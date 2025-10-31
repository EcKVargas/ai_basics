import json
import requests
from pydantic import BaseModel, Field
from gen_ai_hub.proxy.native.openai import chat
from gen_ai_hub.proxy.native.openai import completions
from gen_ai_hub.proxy import get_proxy_client
from gen_ai_hub.proxy.native.openai.clients import OpenAI
from mcp_tool_schema import  get_search_system_flexi_schema
from server import search_system_flexi
import urllib3
from mcp import ClientSession
# from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
import requests

# Disable SSL verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxy_client = get_proxy_client()
chat_client = OpenAI(proxy_client=proxy_client)

    # COCKPIT_BASE_API = "https://dlm.wdf.sap.corp/slim/API/UI5CockpitDataProvider"
    # SLIM_ENTITY_API = "https://dlm.wdf.sap.corp/slim"




import asyncio

async def initialize_session():
    # Connect to a streamable HTTP server
    async with streamablehttp_client("http://localhost:8050/mcp") as (
        read_stream,
        write_stream,
        _,
    ):
        # Create a session using the client streams
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")


# Run the async initialization
asyncio.run(initialize_session())


tools =  []

tools = [get_search_system_flexi_schema()] 

print("Tools schema:", tools)

user_prompt = "show me all systems with cluster Core 1"
system_prompt = """
You are a helpful assistant that retrieves SAP system information 
from the SLIM Flexi Report API. 
You have access to a tool called `search_system_flexi` that allows you to 
search systems, filter by attributes (e.g. SID, status), and return details.

When you need system information, call the tool with the right query 
string (fields + filters). Always include the tool result in your final answer.
"""

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user",
    "content": user_prompt
    }
]
response = chat_client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
)
print(response)
event = response.choices[0].message.tool_calls  # Fully typed Person
print("tool call format is", event)

def call_function(name, args):
    if name == "search_system_flexi":
        return search_system_flexi(**args)
    
tool_calls = getattr(response.choices[0].message, "tool_calls", None)
if not tool_calls:
    # No tool was called by the model — print assistant content and skip function invocation
    assistant_content = getattr(response.choices[0].message, "content", None)
    print("No tool calls. Assistant response:", assistant_content)
else:   
    for tool_call in response.choices[0].message.tool_calls :
        arguments = json.loads(tool_call.function.arguments)
        print("Function arguments:", arguments)
        function_response = call_function(tool_call.function.name, arguments)
        messages.append({
            "role": "function",
            "name": tool_call.function.name,
            "content": str(function_response)
        })


    # class WeatherResponse(BaseModel):
    #     temperature: float = Field(
    #         description ="the current temperature in celsius for the given location"
    #         )
    #     response: str = Field(
    #         description="a natural language response to the user question"
    #         )


    # print("Message for the second LLM call", messages)
    second_response = chat_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools
        # response_format=WeatherResponse,
    )
    print(second_response)
    final_response = second_response.choices[0].message.content
    print("Final response:", final_response)
