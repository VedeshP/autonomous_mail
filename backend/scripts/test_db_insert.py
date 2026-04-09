# backend/scripts/test_db_insert.py
import sys
import os
import json

# Add backend directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app.db.base_class

from app.db.session import SessionLocal
from app.core.parsing import parse_gmail_payload
from app.crud.email import create_email, get_email_by_gmail_id
from app.models.user import User

def main():
    # 1. Open a database session
    db = SessionLocal()

    try:
        # 2. We need a dummy user first, because emails require an owner_id!
        # Let's check if our test user exists, if not, create one.
        test_user = db.query(User).filter(User.email == "test@aethermail.com").first()
        if not test_user:
            print("Creating dummy user...")
            test_user = User(
                google_sub="dummy_google_sub_123",
                email="test@aethermail.com",
                full_name="Test User"
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print(f"Created User with ID: {test_user.id}")

        # 3. Load and parse the raw JSON
        with open("sample_email.json", "r") as f:
            raw_data = json.load(f)
        
        parsed_email = parse_gmail_payload(raw_data)
        
        # 4. Check if we already inserted this email
        existing_email = get_email_by_gmail_id(db, parsed_email.gmail_id)
        if existing_email:
            print(f"Email {parsed_email.gmail_id} already exists in database!")
            return

        # 5. Insert the email into the database!
        print("Inserting email into PostgreSQL...")
        saved_email = create_email(db=db, email_in=parsed_email, owner_id=test_user.id)
        
        print("\n✅ Success! Email saved to database.")
        print(f"Database UUID: {saved_email.id}")
        print(f"Subject: {saved_email.subject}")

    finally:
        db.close()

if __name__ == "__main__":
    main()