# backend/app/data_pipeline/spark_stream.py

import os
import sys
import json
import requests

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, udf
from pyspark.sql.types import StringType, StructType, StructField
from cryptography.fernet import Fernet

# Add backend directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.append(backend_dir)

from app.core.parsing import parse_gmail_payload
from app.core.config import settings

# --- 1. Define the UDFs ---

ENCRYPTION_KEY = os.getenv("HDFS_ENCRYPTION_KEY")
cipher_suite = Fernet(ENCRYPTION_KEY.encode()) if ENCRYPTION_KEY else None

def encrypt_text(text: str) -> str:
    """
    Encrypts a plain text string using AES (Fernet).
    Returns the ciphertext as a base64 string.
    """
    if not text or not cipher_suite:
        return text # Return original if empty or key is missing
    try:
        # Fernet requires bytes, so we encode the string to bytes, encrypt it, 
        # and then decode the resulting ciphertext back to a safe string for Parquet.
        cipher_bytes = cipher_suite.encrypt(text.encode('utf-8'))
        return cipher_bytes.decode('utf-8')
    except Exception as e:
        print(f"Encryption failed: {e}")
        return "ENCRYPTION_ERROR"

# Register the Python function as a Spark UDF
encrypt_udf = udf(encrypt_text, StringType())

def parse_and_clean_email(raw_json_str):
    try:
        raw_dict = json.loads(raw_json_str)
        clean_email = parse_gmail_payload(raw_dict)
        
        result = {
            "owner_id": raw_dict.get("_aethermail_owner_id", "unknown"),
            "gmail_id": clean_email.gmail_id,
            "thread_id": clean_email.thread_id,
            "sender": clean_email.sender,
            "recipient": clean_email.recipient,
            "subject": clean_email.subject,
            "date_received": clean_email.date_received.isoformat(), 
            "snippet": clean_email.snippet,
            "body_text": clean_email.raw_text_body or clean_email.snippet
        }
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})

parse_udf = udf(parse_and_clean_email, StringType())

# ADD THIS NEW FUNCTION
def get_embedding(text_chunk):
    """Calls local Ollama server to get vector embedding for a string of text."""
    if not text_chunk:
        return None
    try:
        url = "http://localhost:11434/api/embeddings"
        payload = {
            "model": "nomic-embed-text",
            "prompt": text_chunk
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        # Returns a list of 768 floats
        return response.json().get("embedding")
    except Exception as e:
        print(f"Embedding failed: {e}")
        return None


# We use ArrayType(FloatType()) because it returns a list of numbers
from pyspark.sql.types import ArrayType, FloatType
embed_udf = udf(get_embedding, ArrayType(FloatType()))


# --- 2. The Main Spark Job ---
def start_streaming():
    print("Initializing Apache Spark Session via spark-submit...")
    
    # We no longer hardcode the JARs here. We will pass them in the spark-submit command!
    spark = SparkSession.builder \
        .appName("AetherMail_Streaming_Processor") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    print("Spark Session created. Connecting to Kafka...")

    # --- 3. INGESTION (Read from Kafka) ---
    raw_kafka_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", "raw_emails") \
        .option("startingOffsets", "earliest") \
        .load()

    json_df = raw_kafka_df.selectExpr("CAST(value AS STRING) as raw_json")

    # --- 4. TRANSFORMATION ---
    cleaned_df = json_df.withColumn("clean_json", parse_udf(col("raw_json")))

    clean_schema = StructType([
        StructField("owner_id", StringType(), True),
        StructField("gmail_id", StringType(), True),
        StructField("thread_id", StringType(), True),
        StructField("sender", StringType(), True),
        StructField("recipient", StringType(), True),
        StructField("subject", StringType(), True),
        StructField("date_received", StringType(), True),
        StructField("snippet", StringType(), True),
        StructField("body_text", StringType(), True),
        StructField("error", StringType(), True)
    ])

    final_df = cleaned_df.withColumn("parsed", from_json(col("clean_json"), clean_schema)) \
                         .select("parsed.*") \
                         .filter(col("error").isNull())

    # --- 5. ACTION (Write the Data) ---
    def process_batch(df, batch_id):
        print(f"\n--- Processing Batch {batch_id} ---")
        row_count = df.count()
        print(f"Emails in this batch: {row_count}")
        
        if row_count > 0:
            df.show(truncate=50)
            
            # --- ACTION A: PostgreSQL ---
            db_df = df.select("owner_id", "gmail_id", "thread_id", "sender", "recipient", "subject", "date_received", "snippet")
            try:
                from pyspark.sql.functions import lit
                # db_df = db_df.withColumn("owner_id", lit("3c1a96ad-d823-481d-846c-03be83909f3a")) # <-- REPLACE THIS AGAIN!

                db_url = f"jdbc:postgresql://{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
                
                db_df.write \
                    .format("jdbc") \
                    .option("url", db_url) \
                    .option("dbtable", "emails") \
                    .option("user", settings.POSTGRES_USER) \
                    .option("password", settings.POSTGRES_PASSWORD) \
                    .option("driver", "org.postgresql.Driver") \
                    .mode("append") \
                    .save()
                print(" Batch metadata written to PostgreSQL.")
            except Exception as e:
                print(f" Failed to write to Postgres: {e}")

            # --- ACTION B: Write Raw Data to REAL HDFS! ---
            try:
                # This now points to your local Hadoop cluster!
                encrypted_df = df.withColumn("encrypted_body", encrypt_udf(col("body_text")))
                
                # 2. Select the ID and the NEW encrypted column, and write to HDFS
                encrypted_df.select(
                    "gmail_id", 
                    col("encrypted_body").alias("body_text") # Rename it back so the schema stays consistent
                ).write.mode("append").parquet("hdfs://localhost:9000/aethermail/raw_emails")
                
                print(" Batch encrypted and written to HDFS!")
            except Exception as e:
                 print(f" Failed to write to HDFS: {e}")
                
            # --- ACTION C: Generate Embeddings and write to Qdrant --- 
            try:
                from qdrant_client import QdrantClient
                from qdrant_client.models import PointStruct, VectorParams, Distance
                
                # 1. Connect to Qdrant
                q_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
                collection_name = "emails"

                # Ensure collection exists
                if not q_client.collection_exists(collection_name):
                    q_client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(size=768, distance=Distance.COSINE) # nomic-embed uses 768 dimensions
                    )

                # 2. Get the embeddings! 
                # We apply the embed_udf to the body_text column.
                # In production with long emails, we would CHUNK the text first. 
                # For this test, we embed the snippet to save time.
                embedded_df = df.withColumn("vector", embed_udf(col("snippet")))

                # 3. Collect the data to the master node to insert into Qdrant
                # (Note: In a huge cluster, you'd use df.foreachPartition to distribute the writes)
                records = embedded_df.select("gmail_id", "vector", "sender", "subject", "date_received").collect()
                
                points = []
                import uuid
                
                for row in records:
                    if row["vector"] is not None:
                        points.append(
                            PointStruct(
                                id=str(uuid.uuid4()), # Qdrant requires a UUID for the point
                                vector=row["vector"],
                                payload={
                                    "gmail_id": row["gmail_id"],
                                    "sender": row["sender"],
                                    "subject": row["subject"],
                                    "date_received": row["date_received"]
                                }
                            )
                        )
                
                if points:
                    q_client.upsert(collection_name=collection_name, points=points)
                    print(f" Batch vectors written to Qdrant collection '{collection_name}'!")
                    
            except Exception as e:
                print(f" Failed to write to Qdrant: {e}")

    query = final_df.writeStream \
        .foreachBatch(process_batch) \
        .trigger(processingTime='5 seconds') \
        .start()

    print(" Spark Streaming is live and waiting for emails...")
    query.awaitTermination()

if __name__ == "__main__":
    start_streaming()