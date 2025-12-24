import json
import os
import sys

# Ensure current directory is in path (standard in FC, but good for safety)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from liangent import Liangent

def handler(event, context):
    """
    Aliyun Function Compute Entry Point.
    """
    print(f"FC Handler Triggered. Event: {event}")
    
    # 1. Parsing Event (Simple text or JSON)
    try:
        if isinstance(event, bytes):
            evt_str = event.decode("utf-8")
        else:
            evt_str = str(event)
        print("receive event info: ", event)
        
        # Try to parse JSON input
        try:
            evt_json = json.loads(evt_str)
            query = evt_json.get("query", "Hello from FC")
        except json.JSONDecodeError:
            query = evt_str or "Hello from FC"
            
    except Exception as e:
        return f"Error parsing event: {e}"

    # 2. Initialize Agent
    # FC Environment Variables should be set in the console:
    # OPENAI_API_KEY, OPENAI_BASE_URL, MODEL_NAME
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "Error: OPENAI_API_KEY not set in FC environment variables."
        
    try:
        print("Initializing Liangent...")
        # Use in-memory DB or ephemeral file (FC /tmp is writable)
        # Note: /tmp is wiped after execution context recycling
        db_url = "sqlite:////tmp/liangent.db"
        
        bot = Liangent(
            api_key=api_key, 
            db_url=db_url
        )
        
        print(f"Agent initialized. Query: {query}")
        
        # Use stream() instead of chat() to capture intermediate events
        final_response = ""
        for event in bot.stream(query):
            evt_type = event.get("event")
            
            # Print intermediate steps for debugging
            if evt_type == "thought":
                print(f"[Thinking] {event.get('content')}")
            elif evt_type == "item.started":
                item = event.get("data", {}).get("item", {})
                print(f"[Tool Call] {item.get('tool')}({item.get('args')})")
            elif evt_type == "item.completed":
                item = event.get("data", {}).get("item", {})
                print(f"[Tool Output] {item.get('aggregated_output')}")
            elif evt_type == "final_answer":
                final_response = event.get("content")
                print(f"[Final Answer] {final_response}")
            elif evt_type == "error":
                print(f"[Error] {event.get('content')}")
            elif evt_type == "debug":
                # Only if DEBUG is enabled, but good to have if user wants deep traces
                print(f"[Debug] {event.get('data')}")

        return {
            "status": "success",
            "query": query,
            "response": final_response
        }
        
    except Exception as e:
        print(f"Agent Execution Error: {e}")
        return f"Agent Execution Error: {e}"
