# backend/scripts/ingest_to_kafka.py
import sys
import os
import json
import time

# Add backend directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.data_pipeline.producer import EmailKafkaProducer

def main():
    topic_name = "raw_emails"
    
    # 1. Initialize our producer
    producer = EmailKafkaProducer(bootstrap_servers='localhost:9092')
    
    # 2. Load the raw, messy Google JSON
    # In a production system, this would be a real-time webhook from Gmail
    email_file_path = "sample_email.json"
    
    if not os.path.exists(email_file_path):
        print(f"Error: {email_file_path} not found.")
        return

    with open(email_file_path, "r") as f:
        raw_email_data = json.load(f)

    print("--- Starting Ingestion Pipeline ---")
    
    # 3. Push to Kafka (Let's send it 3 times to simulate a burst of emails)
    for i in range(3):
        print(f"Pushing email {i+1}/3 to Kafka...")
        
        # We append a fake ID just to make them look unique in the queue
        raw_email_data["_internal_job_id"] = f"batch_1_email_{i}"
        
        producer.send_raw_email(topic=topic_name, email_data=raw_email_data)
        time.sleep(1) # Small pause for readability
        
    # 4. Clean up
    producer.close()
    print("--- Ingestion Complete ---")

if __name__ == "__main__":
    main()