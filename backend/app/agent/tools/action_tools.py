# backend/app/agent/tools/action_tools.py
from langchain_core.tools import tool
from app.db.session import SessionLocal
from app.core.gmail_service import get_gmail_service, modify_email_labels, create_gmail_label # Ensure create_gmail_label is imported
from cryptography.fernet import Fernet
from pyspark.sql import SparkSession
import os

@tool
def organize_email(user_id: str, gmail_id: str, add_label_ids: list[str] = [], remove_label_ids: list[str] = []) -> str:
    """
    Autonomously apply or remove labels (folders) from an email.
    Use this when the user asks to organize, archive, or categorize specific emails.
    You must provide the exact gmail_id and the internal Google Label IDs (e.g., 'UNREAD', 'INBOX', or custom IDs).
    """
    db = SessionLocal()
    try:
        service = get_gmail_service(db, user_id)
        result = modify_email_labels(
            service=service, 
            gmail_id=gmail_id, 
            add_labels=add_label_ids, 
            remove_labels=remove_label_ids
        )
        return f"Successfully updated email {gmail_id}. Current labels: {result['current_labels']}"
    except Exception as e:
        return f"Failed to organize email: {str(e)}"
    finally:
        db.close()

@tool
def create_new_label(user_id: str, label_name: str) -> str:
    """
    Autonomously creates a new custom label (folder) in the user's Gmail.
    Use this when the user asks you to create a new folder or category that does not exist yet.
    Returns the internal ID of the newly created label.
    """
    db = SessionLocal()
    try:
        service = get_gmail_service(db, user_id)
        result = create_gmail_label(service, label_name)
        return f"Successfully created label '{result['name']}'. The Label ID is: {result['id']}"
    except Exception as e:
        return f"Failed to create label: {str(e)}"
    finally:
        db.close()
        
@tool
def create_draft_reply(user_id: str, gmail_id: str, to_email: str, subject: str, body_text: str) -> str:
    """
    Autonomously creates a draft reply to an email.
    Use this when the user asks you to reply, respond, or draft an email.
    """
    db = SessionLocal()
    try:
        service = get_gmail_service(db, user_id)
        message_str = f"To: {to_email}\nSubject: {subject}\n\n{body_text}"
        import base64
        b64_string = base64.urlsafe_b64encode(message_str.encode("utf-8")).decode("utf-8")
        
        draft_body = {
            "message": {
                "raw": b64_string,
                "threadId": gmail_id 
            }
        }
        draft = service.users().drafts().create(userId='me', body=draft_body).execute()
        return f"Successfully created draft. Draft ID: {draft['id']}"
    except Exception as e:
        return f"Failed to create draft: {str(e)}"
    finally:
        db.close()
        
        
@tool
def trigger_bulk_action_job(user_id: str, action_type: str, query_filter: dict, action_payload: dict) -> str:
    """
    Delegates massive bulk actions (like deleting or labeling >50 emails) to the Spark Big Data cluster.
    Use this immediately when the user asks to modify hundreds or thousands of emails.
    Do NOT attempt to process them individually in the chat.
    
    action_type: e.g., 'apply_label', 'delete', 'archive'
    query_filter: e.g., {"sender": "marketing@spam.com", "date_before": "2023-01-01"}
    action_payload: e.g., {"label_id": "Label_123"}
    """
    try:
        from app.main import kafka_producer # Import our running producer
        
        # Package the job instructions
        job_message = {
            "user_id": user_id,
            "action_type": action_type,
            "filter": query_filter,
            "payload": action_payload,
            "status": "queued"
        }
        
        # Drop it into the Kafka speed layer!
        kafka_producer.send_raw_email("bulk_actions", job_message)
        
        print(f" AGENT DELEGATING TO KAFKA: Dropped bulk {action_type} job into queue.")
        return "Bulk action successfully queued to the Apache Spark cluster. The user will be notified upon completion."
        
    except Exception as e:
        return f"Failed to queue bulk action to Kafka: {str(e)}"
    
    
    
@tool
def fetch_raw_email_from_hdfs(gmail_id: str) -> str:
    """
    Fetches the FULL, raw, original text of an email from the HDFS Data Lake.
    Use this ONLY when you need to read the exact, word-for-word content of a specific email, 
    or if the user asks you to forward or quote a massive email.
    You must provide the exact gmail_id.
    """
    try:
        # 1. Initialize the decryption key
        ENCRYPTION_KEY = os.getenv("HDFS_ENCRYPTION_KEY")
        if not ENCRYPTION_KEY:
             return "System Error: Missing HDFS decryption key."
             
        cipher_suite = Fernet(ENCRYPTION_KEY.encode())

        # 2. Start a lightweight, local Spark session just for reading
        # (In production, we would use a dedicated API for this, not spin up Spark every time)
        print(f"🚀 AGENT DELEGATING TO HDFS: Fetching heavy payload for {gmail_id}")
        spark = SparkSession.builder.appName("HDFS_Reader").master("local[2]").getOrCreate()
        spark.sparkContext.setLogLevel("ERROR")

        # 3. Read the Parquet files and filter for our specific email
        df = spark.read.parquet("hdfs://localhost:9000/aethermail/raw_emails")
        email_row = df.filter(df.gmail_id == gmail_id).first()

        spark.stop() # Clean up

        if not email_row:
            return f"Error: Email {gmail_id} not found in the HDFS Data Lake."

        encrypted_text = email_row["body_text"]
        if not encrypted_text:
             return "Error: Email body is empty."

        # 4. Decrypt the data in memory!
        try:
            # Fernet requires bytes, so we encode the string to bytes, decrypt, and decode back to string
            decrypted_bytes = cipher_suite.decrypt(encrypted_text.encode('utf-8'))
            plain_text = decrypted_bytes.decode('utf-8')
            return f"--- FULL EMAIL TEXT FROM ARCHIVE ---\n{plain_text}"
            
        except Exception as decrypt_error:
             return f"SECURITY FATAL: Failed to decrypt email. Data may be corrupted or tampered with. Error: {str(decrypt_error)}"

    except Exception as e:
        return f"Failed to retrieve from HDFS: {str(e)}"

# Update export list
action_tools_list = [organize_email, create_new_label, create_draft_reply, trigger_bulk_action_job, fetch_raw_email_from_hdfs]