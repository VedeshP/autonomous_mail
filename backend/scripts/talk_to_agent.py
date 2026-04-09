# backend/scripts/talk_to_agent.py
import sys
import os

# Add backend directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agent.graph import build_agent
from langchain_core.messages import HumanMessage

def main():
    print("Initializing AetherMail Agent...")
    agent = build_agent()
    
    print("\n Agent is online! Type 'exit' to quit.\n")
    
    # Create a simple interactive chat loop
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        print("AetherMail is thinking...")
        
        # Prepare the state (the message history)
        inputs = {"messages": [HumanMessage(content=user_input)]}
        
        # Stream the graph execution so we can see what it's doing
        try:
            for event in agent.stream(inputs, stream_mode="values"):
                # The event contains the current list of messages. We just want the last one.
                last_message = event["messages"][-1]
                
                # If it's an AI message, print it
                if last_message.type == "ai" and last_message.content:
                    print(f"\nAetherMail: {last_message.content}\n")
                
                # If the AI decided to use a tool, print a notification
                if last_message.type == "ai" and hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    print(f"[Agent is using tool: {last_message.tool_calls[0]['name']}]")
                    
        except Exception as e:
            print(f"\n An error occurred: {e}\n")

if __name__ == "__main__":
    main()