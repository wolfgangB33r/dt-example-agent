import json
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_community.callbacks.manager import get_openai_callback
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from http.server import BaseHTTPRequestHandler, HTTPServer

AGENT_NAME = "Helsinki"

AGENT_INSTRUCTIONS = f"""
You are **{AGENT_NAME}**, a helpful agent. You don't ask for confirmation, you always execute the necessary tools and DQL queries.


"""

def get_current_time() -> dict:
    """Returns the current date and time.

    Args:
        None

    Returns:
        dict: status and result or error msg.
    """
    now = datetime.now()
    
    report = (
        f'The current date and time is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
    )
    return {"status": "success", "report": report}

def chat_response(prompt: str) -> str:
    """Fallback: Generate a natural language response to any prompt.
    
    Args:
        prompt (str): The input prompt to generate a response for.
    Returns:
        str: The generated response.
    """
    # Google models
    if os.getenv("LLM_MODEL") == "google":
        model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
    else:
        # OpenAI models
        model = init_chat_model("gpt-4o", model_provider="openai")
    return model.invoke(prompt)

def load_dynatrace_config(dt_settings_object_id: str) -> dict:
    """
    Loads the Dynatrace configuration from a settings object by its ID.

    Args:
        dt_settings_object_id (str): The ID of the Dynatrace settings object.

    Returns:
        dict: status and result or error msg.
    """
    
    response = requests.get(os.getenv("DT_SETTINGS_API_URL") + dt_settings_object_id, headers={
        'Authorization': f'Api-Token {os.getenv("DT_SETTINGS_API_KEY")}'
    })

    print(response.text)

    if response.status_code != 200:
        return {"status": "error", "error_msg": response.text}
    
    return {"status": "success", "result": response.json()}

def query_dynatrace_dql(dql_query: str) -> dict:
    """Executes a Dynatrace DQL query and returns the resulting records as a JSON string.

    Args:
        dql_query (str): The DQL query to execute.

    Returns:
        dict: status and result or error msg.
    """
    
    # Data to be sent in the JSON payload
    data = {
        "query": dql_query,
        "timezone": "UTC",
        "locale": "en_US",
        "maxResultRecords": 100,
        "maxResultBytes": 1000000,
        "fetchTimeoutSeconds": 60,
        "requestTimeoutMilliseconds": 5000,
        "enablePreview": True,
        "defaultSamplingRatio": 1,
        "defaultScanLimitGbytes": -1,
        "queryOptions": None,
        "filterSegments": None
    }

    # Convert the data to a JSON string
    json_data = json.dumps(data)

    # Send the POST request
    response = requests.post(os.getenv("DT_DQL_API_URL"), data=json_data, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.getenv("DT_DQL_API_KEY")}'
        })

    if response.status_code != 200:
        # Print the response from the server
        print(response.status_code)
        print(response.text)
        return {"status": "error", "error_msg": response.text}
    
    if response.json()["state"] == "SUCCEEDED":
        report = (
            response.json()["result"]["records"]
        )
        return {"status": "success", "report": report}

def answer(msg):
    try:
        # Google models
        if os.getenv("LLM_MODEL") == "google":
            model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
        else:
            # OpenAI models
            model = init_chat_model("gpt-4o", model_provider="openai")
        tools=[
            get_current_time, chat_response, load_dynatrace_config, query_dynatrace_dql
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

        # load the text in the README.md file
        readme_path = os.path.join(os.path.dirname(__file__), "instructions.md")
        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                instructions_text = f.read()
        except UnicodeDecodeError:
            # try again if there's a BOM or different utf-8 variant
            with open(readme_path, "r", encoding="utf-8-sig") as f:
                instructions_text = f.read()
        except Exception as e:
            instructions_text = f"<unable to load README.md: {e}>"
        input_messages = [
            { "role": "system", "content": AGENT_INSTRUCTIONS},
            { "role": "system", "content": instructions_text},
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
            
            return {"status": "success", "tokens_used": cb.total_tokens, "response": final_message.content}
    except Exception as e:
        return {"status": "error", "tokens_used": cb.total_tokens, "response": e}

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
    #run()
    print(answer("Is there a significant difference between alert spam last week and today?"))
