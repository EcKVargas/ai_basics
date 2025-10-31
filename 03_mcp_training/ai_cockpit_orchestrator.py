import json
import asyncio
import urllib3
from gen_ai_hub.proxy import get_proxy_client
from gen_ai_hub.proxy.native.openai.clients import OpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from mcp_tool_schema import get_all_schemas

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxy_client = get_proxy_client()
chat_client = OpenAI(proxy_client=proxy_client)

SYSTEM_PROMPT = """
You are a routing-capable assistant for SAP landscape queries.

TOOL-CHOICE POLICY:
- If the user asks for an OVERVIEW or DETAILS of a SINGLE system identified by SID
  (e.g., “show ERX overview”, “status of ADL”, “availability for SID CC3”),
  CALL: cockpit_get_view_by_sid with {"sid": "<SID>"}.
  Return the normalized sections in your final answer.

- If the user asks to LIST or SEARCH systems by FILTERS/ATTRIBUTES (e.g., cluster, status,
  landscape, system type) or asks for multiple systems, CALL: search_system_flexi
  with proper fields + filters.

Never call both tools for the same request unless explicitly necessary. Prefer exactly one tool.
"""

async def mcp_invoke(session: ClientSession, tool_name: str, args: dict):
    """Invoke an MCP tool and return the first json/text result as a Python object."""
    result = await session.call_tool(tool_name, args)

    # 🔍 DEBUG: show what the MCP actually returned
    print("↩ MCP raw result:", result)
    print("↩ MCP parts:", [(getattr(p, "type", None),
                             hasattr(p, "json"),
                             hasattr(p, "text")) for p in result.content])

    for part in result.content:
        # FastMCP content parts are usually 'json' or 'text'
        if getattr(part, "type", "") == "json":
            return getattr(part, "json", {})
        if getattr(part, "type", "") == "text":
            txt = getattr(part, "text", "")
            try:
                return json.loads(txt)  # sometimes JSON is serialized as text
            except Exception:
                return {"text": txt}

    return {"warning": "No json/text content in MCP result"}

async def run_once(user_prompt: str):
    # 1) Connect to MCP server
    async with streamablehttp_client("http://localhost:8050/mcp") as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools_list = await session.list_tools()
            available = [t.name for t in tools_list.tools]
            print("MCP tools available:", available)

            # 2) Provide both tool schemas to the LLM
            tools = get_all_schemas()

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]

            # 3) First LLM turn -> choose a tool
            first = chat_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
            )

            msg = first.choices[0].message
            tool_calls = getattr(msg, "tool_calls", None)

            if not tool_calls:
                # No tool was chosen -> just return LLM text
                print("Assistant:", msg.content)
                return msg.content

            # ✅ Append the assistant message that *contains* the tool_calls
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ],
            })

            # 4) Execute each tool call via MCP and feed results back
            for tc in tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments or "{}")
                print(f"Calling MCP tool: {name} with {args}")
                result_obj = await mcp_invoke(session, name, args)
                
                # Append as a 'tool' message using tool_call_id (newer format)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": name,
                    "content": json.dumps(result_obj)
                })

            # 5) Second LLM turn -> produce final answer
            second = chat_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
            )
            final = second.choices[0].message.content
            print("Final:", final)
            return final

if __name__ == "__main__":
    # Interactive console loop: enter a query to run, empty input or 'quit' to exit
    print("Interactive console. Type your question and press Enter. Empty input or 'quit' to exit.")
    try:
        while True:
            try:
                user_input = input("User> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break

            if not user_input:
                print("No input — exiting.")
                break
            if user_input.lower() in ("q", "quit", "exit"):
                print("Exiting.")
                break

            print("\n=== USER:", user_input)
            # run the request (each call creates its own MCP session)
            try:
                asyncio.run(run_once(user_input))
            except Exception as e:
                # Keep the console alive on errors so the user can try again
                print("Error while processing the request:", repr(e))
    except KeyboardInterrupt:
        print("\nInterrupted — exiting.")
