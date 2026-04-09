# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1.api import api_router
import app.db.base_class 
from app.data_pipeline.producer import EmailKafkaProducer

# Global producer instance
kafka_producer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to Kafka
    global kafka_producer
    print("Connecting to Kafka...")
    kafka_producer = EmailKafkaProducer(bootstrap_servers='localhost:9092')
    yield
    # Shutdown: Close Kafka cleanly
    print("Disconnecting from Kafka...")
    if kafka_producer:
        kafka_producer.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan, # Attach the lifespan manager
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the AetherMail API", "status": "Running"}

# --- Route Registration ---
# We apply the global "/api/v1" prefix here. 
# So the email route becomes: /api/v1/emails
app.include_router(api_router, prefix="/api/v1")