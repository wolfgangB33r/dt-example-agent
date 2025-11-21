import json
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient  

from http.server import BaseHTTPRequestHandler, HTTPServer

AGENT_NAME = "Helsinki"

# Load environment variables
DT_TENANT = os.getenv('DT_TENANT')
DT_API_TOKEN = os.getenv('DT_API_TOKEN')

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

def chat_response(prompt: str) -> str:
    """Fallback: Generate a natural language response to any prompt.
    
    Args:
        prompt (str): The input prompt to generate a response for.
    Returns:
        str: The generated response.
    """
    model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
    return model.invoke(prompt)

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

async def answer(msg, thread_id):
    total_input_tokens = 0
    total_output_tokens = 0
    try:
        # Initiate the agent model and tools
        model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
        # 
        mcp_tools = await client.get_tools() 
    
        tools=[
            get_current_time, 
            chat_response
        ]
        agent_executor = create_react_agent(model, mcp_tools, debug=False)
        
        config = {
            "configurable": {
                "thread_id": thread_id, 
                "agent_name": AGENT_NAME, 
                "agent_description": f"{AGENT_NAME}, a helpful assistant.",
            }
        }

        input_messages = [
            { "role": "system", "content": load_instructions() },
            { "role": "user", "content": msg }
        ]

        # invoke the agent and pass callbacks
        response = agent_executor.invoke({"messages": input_messages}, config=config)
       
        for msg in response["messages"]:
            if hasattr(msg, "usage_metadata"):
                total_input_tokens += msg.usage_metadata.get("input_tokens", 0)
                total_output_tokens += msg.usage_metadata.get("output_tokens", 0)
            
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for call in msg.tool_calls:
                    print("Tool call:", call)

        final_message = response["messages"][-1]
       
        return {"status": "success", "total_input_tokens_used": total_input_tokens, "total_output_tokens": total_output_tokens, "response": final_message.content}
    except Exception as e:
        return {"status": "error", "total_input_tokens_used": total_input_tokens, "total_output_tokens": total_output_tokens, "response": e}

class SimpleTextHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Get content length
        content_length = int(self.headers.get('Content-Length', 0))
        # Read the posted data
        post_data = self.rfile.read(content_length)

        text = post_data.decode('utf-8')
        
        result_json = answer(text)

        response = json.dumps({"result": result_json}).encode('utf-8')

        # Send response headers
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()

        # Send the response body
        self.wfile.write(response)

def run(server_class=HTTPServer, handler_class=SimpleTextHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Serving on port {port}...")
    httpd.serve_forever()

## main routine
if __name__ == "__main__":
    import asyncio
    #run()
    print(asyncio.run(answer("List all your tools", thread_id="test-thread-001")))
