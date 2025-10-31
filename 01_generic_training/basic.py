from pydantic import BaseModel
from gen_ai_hub.proxy.native.openai import chat

class calendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

user_prompt = "alice and bob are going to a science fair on saturday 01/05/2024"
system_prompt = "extract the event information "
messages = [
{"role": "system", "content": system_prompt},
{"role": "user",
  "content": user_prompt
}
]


response = chat.completions.parse(
    model="gpt-4o",
    messages=messages,
    response_format=calendarEvent
)
event = response.choices[0].message.parsed  # Fully typed Person
print(event)