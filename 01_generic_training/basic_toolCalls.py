
import json
import requests
from pydantic import BaseModel, Field
from gen_ai_hub.proxy.native.openai import chat
from gen_ai_hub.proxy.native.openai import completions
from gen_ai_hub.proxy import get_proxy_client
from gen_ai_hub.proxy.native.openai.clients import OpenAI

proxy_client = get_proxy_client()
chat_client = OpenAI(proxy_client=proxy_client)



def get_weather(latitude,longitude):
    print("Fetching weather for:", latitude, longitude)
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
    print("with API ->", url)
    response = requests.get(url, timeout=10)
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        raise RuntimeError(f"HTTP error when calling weather API: {e}, status={response.status_code}, text={response.text}") from e

    data = response.json()
    print("API response:", data)

    # support both possible keys and provide a clear error if missing
    if "current" in data:
        return data["current"]
    if "current_weather" in data:
        return data["current_weather"]

    # helpful debug error
    raise KeyError(f"Expected 'current' or 'current_weather' in API response. Response keys: {list(data.keys())}. Full response: {data}")


tools =  [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a given latitude and longitude.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number",
                            "description": "The latitude of the location to get the weather for.",
                        },
                        "longitude": {
                            "type": "number",
                            "description": "The longitude of the location to get the weather for.",
                        },
                    },
                    "required": ["latitude", "longitude"],
                    "additionalProperties": False,
                },
                "strict": True,
            },

        }
    ]


# from tool_schema import get_weather_schema
# tools.extend(get_weather_schema())

user_prompt = "what is the current weather in berlin germany?"
system_prompt = "You are a helpful assistant that helps people find information about the current weather in a given location. You have access to a tool that can get the current weather for a given latitude and longitude. Use this tool to get the current weather when needed. If you use the tool, be sure to include the result in your final answer."
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

# completions.model_dump()

def call_function(name, args):
    if name == "get_weather":
        return get_weather(**args)
    
tool_calls = getattr(response.choices[0].message, "tool_calls", None)
if not tool_calls:
    # No tool was called by the model — print assistant content and skip function invocation
    assistant_content = getattr(response.choices[0].message, "content", None)
    print("No tool calls. Assistant response:", assistant_content)
else:   
    for tool_call in response.choices[0].message.tool_calls :
        arguments = json.loads(tool_call.function.arguments)
        function_response = call_function(tool_call.function.name, arguments)
        messages.append({
            "role": "function",
            "name": tool_call.function.name,
            "content": str(function_response)
        })


    class WeatherResponse(BaseModel):
        temperature: float = Field(
            description ="the current temperature in celsius for the given location"
            )
        response: str = Field(
            description="a natural language response to the user question"
            )


    print("Message for the second call", messages)
    second_response = chat_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        response_format=WeatherResponse,
    )
    print(second_response)
    final_response = second_response.choices[0].message.parsed  # Fully typed Person
    print("Final response is", final_response)
    print(final_response.temperature)
    print(final_response.response)