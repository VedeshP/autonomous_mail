# backend/app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create the SQLAlchemy Engine
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI, 
    pool_pre_ping=True # Checks if connection is alive before using it
)

# Create a SessionLocal class. Each instance of this class is a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get a DB session in our FastAPI endpoints later
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()