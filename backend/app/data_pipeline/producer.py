# backend/app/data_pipeline/producer.py
import json
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailKafkaProducer:
    def __init__(self, bootstrap_servers: str = 'localhost:9092'):
        """
        Initializes the Kafka Producer.
        bootstrap_servers: The address of your Kafka broker.
        """
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=[bootstrap_servers],
                # Kafka expects data as bytes. This lambda automatically 
                # converts our Python dictionaries to JSON byte strings.
                value_serializer=lambda m: json.dumps(m).encode('utf-8'),
                # Retries are crucial in distributed systems
                retries=3 
            )
            logger.info(f"Successfully connected to Kafka at {bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise

    def send_raw_email(self, topic: str, email_data: dict):
        """
        Sends a raw email JSON object to the specified Kafka topic.
        """
        try:
            # Send the message (this is asynchronous)
            future = self.producer.send(topic, email_data)
            
            # Block until a single message is sent (or timeout)
            # This returns metadata about exactly where the message was stored
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Delivered message to topic '{record_metadata.topic}' "
                f"partition {record_metadata.partition} "
                f"offset {record_metadata.offset}"
            )
        except KafkaError as e:
            logger.error(f"Failed to send message to Kafka: {e}")
        except Exception as e:
             logger.error(f"An unexpected error occurred: {e}")

    def close(self):
        """Flushes the queue and closes the connection cleanly."""
        self.producer.flush()
        self.producer.close()
        logger.info("Kafka producer closed.")