import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
import asyncio

from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient


AGENT_NAME = "Helsinki"

# Load environment variables
DT_TENANT = os.getenv('DT_TENANT')
DT_API_TOKEN = os.getenv('DT_API_TOKEN')

# Initialize the MultiServerMCPClient with Dynatrace MCP server configuration
client = MultiServerMCPClient(  
    {
        "dynatrace-mcp": {
            "transport": "streamable_http",  
            "url": 'https://{tenant}/platform-reserved/mcp-gateway/v0.1/servers/dynatrace-mcp/mcp'.format(tenant=DT_TENANT),
            "headers": {
                "Authorization": "Bearer {token}".format(token=DT_API_TOKEN)
            }
        }
    }
)

# Load the agents instructions from the markdown file
def load_instructions():
    readme_path = os.path.join(os.path.dirname(__file__), "instructions.md")
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            instructions_text = f.read()
    except UnicodeDecodeError:
        # try again if there's a BOM or different utf-8 variant
        with open(readme_path, "r", encoding="utf-8-sig") as f:
            instructions_text = f.read()
    except Exception as e:
        instructions_text = f"<unable to load instructions.md: {e}>"
    return instructions_text

# Session memory
input_messages = [
    { "role": "system", "content": load_instructions() },
] 

# A tool to get the current date and time
def get_current_time() -> dict:
    """Returns the current date and time.

    Args:
        None

    Returns:
        dict: status and result or error msg.
    """
    now = datetime.now()
    report = ( f'The current date and time is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}' )
    return { "status": "success", "report": report }

# A fallback tool to generate a natural language response for simple questions
def chat_response(prompt: str) -> str:
    """Fallback: Generate a natural language response to any prompt.
    
    Args:
        prompt (str): The input prompt to generate a response for.
    Returns:
        str: The generated response.
    """
    model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
    return model.invoke(prompt)


async def run_agent(msg, thread_id):
    total_input_tokens = 0
    total_output_tokens = 0
    try:
        # Initiate the agent model and tools
        #model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
        #model = init_chat_model("gemini-3-pro-preview", model_provider="google_genai")
        model = init_chat_model("gpt-4o", model_provider="openai")
        # 
        mcp_tools = await client.get_tools()
    
        tools=[
            get_current_time, 
            chat_response
        ]
        tools.extend(mcp_tools)
        agent_executor = create_agent(model, tools)
        
        config = {
            "configurable": {
                "thread_id": thread_id, 
                "agent_name": AGENT_NAME, 
                "agent_description": f"{AGENT_NAME}, a helpful assistant.",
            }
        }

        # Append newest user message
        input_messages.append({ "role": "user", "content": msg })

        # invoke the agent and pass callbacks
        response = await agent_executor.ainvoke({"messages": input_messages}, config=config)

        
        for msg in response["messages"]:
            if hasattr(msg, "usage_metadata") and msg.usage_metadata:
                total_input_tokens += msg.usage_metadata.get("input_tokens", 0)
                total_output_tokens += msg.usage_metadata.get("output_tokens", 0)
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for call in msg.tool_calls:
                    #print("Tool call:", call)
                    break
        final_message = response["messages"][-1]
        # Remember conversation
        input_messages.append({"role": "assistant", "content": final_message.content})
       
        return {"status": "success", "total_input_tokens_used": total_input_tokens, "total_output_tokens": total_output_tokens, "response": final_message.content}
    except Exception as e:
        return {"status": "error", "total_input_tokens_used": total_input_tokens, "total_output_tokens": total_output_tokens, "response": e}

# main routine
if __name__ == "__main__":
    # Generate a random thread id for this session
    print("Helsinki Agent is running. Type 'exit' to quit.")
    session_id = "local-session-00" + str(os.getpid())
    # Loop for asking the user for input
    while True:
        user_input = input("?: ")
        if user_input.lower() == 'exit':
            break
        
        result = asyncio.run(run_agent(user_input, thread_id=session_id))
        print("Response:", result['response'])
