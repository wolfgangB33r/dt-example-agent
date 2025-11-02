import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_community.callbacks.manager import get_openai_callback
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

AGENT_NAME = "Santa"

AGENT_INSTRUCTIONS = f"""
You are **{AGENT_NAME}**, a helpful agent.
**Instructions:**
1. **Do not ask follow-up questions**—handle the request based on the loaded context.
"""

def get_current_time() -> dict:
    """Returns the current date and time.

    Args:
        None

    Returns:
        dict: status and result or error msg.
    """
    print("test")
    now = datetime.now()
    
    report = (
        f'The current date and time is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
    )
    return {"status": "success", "report": report}

def request(msg):
    try:
        # Google models
        if os.getenv("LLM_MODEL") == "google":
            model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
        else:
            # OpenAI models
            model = init_chat_model("gpt-4o", model_provider="openai")
        
        tools=[
            get_current_time,
        ]
        agent_executor = create_react_agent(
            model, 
            tools, 
            debug=False)
        
        config = {
            "configurable": {
                "thread_id": "wolfgang", 
                "agent_name": AGENT_NAME, 
                "agent_description": f"{AGENT_NAME}, a helpful assistant."
            }
        }

        input_messages = [
            { "role": "system", "content": AGENT_INSTRUCTIONS},
            { "role": "user", "content": msg }
        ]
        
        with get_openai_callback() as cb:
            response = agent_executor.invoke({"messages": input_messages}, config=config)
            for msg in response["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for call in msg.tool_calls:
                        print("Tool call:", call)

            final_message = response["messages"][-1]
            print(final_message.content)
            print("Total tokens used:", cb.total_tokens)
            
            return {"status": "success", "response": final_message.content}
    except Exception as e:
        return {"status": "error", "response": e.message}

## main routine
if __name__ == "__main__":
    print(request("What is the current date and time?"))