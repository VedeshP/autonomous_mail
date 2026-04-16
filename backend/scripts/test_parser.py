#backend/scripts/test_parser.py
import json


import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.parsing import parse_gmail_payload

if __name__ == "__main__":
    # Load the raw, untruncated sample email
    with open("sample_email.json", "r") as f:
        raw_data = json.load(f)

    print("--- Parsing raw Google JSON ---")
    
    # Call our new parsing function
    clean_email = parse_gmail_payload(raw_data)
    
    print("\n✅ Success! Parsed into Pydantic Schema:\n")
    
    # Pydantic gives us a beautiful, readable representation
    print(clean_email.model_dump_json(indent=4))
    
    print("\n--- Decoded Plain Text Body (first 300 chars) ---")
    if clean_email.raw_text_body:
        print(clean_email.raw_text_body[:300] + "...")
        # print(clean_email.raw_text_body)
    else:
        print("No plain text body found.")
