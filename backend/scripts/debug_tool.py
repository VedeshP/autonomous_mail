#backend/scripts/debug_tool.py

import sys
import os

# Add backend directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agent.tools.email_tools import search_emails_semantic

def main():
    print("Testing the Semantic Search Tool directly...")
    
    # We will pass a test query directly to the Python function
    query = "Career Brew"
    print(f"Querying for: '{query}'")
    
    try:
        # Call the tool function natively (bypassing LangGraph)
        result = search_emails_semantic.invoke({"query": query})
        
        print("\n--- TOOL RESULT ---")
        print(result)
        print("-------------------\n")
        
    except Exception as e:
        import traceback
        print("\n CRITICAL ERROR IN TOOL:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
