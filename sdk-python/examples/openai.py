from agentrpc import AgentRPC
from openai import OpenAI

openai = OpenAI(api_key="")
agentrpc = AgentRPC(api_secret="")

tools = agentrpc.openai.get_tools()

completion = openai.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": "What is the weather in Melbourne?"
    }],
    tools=tools,
)

if completion.choices[0].message.tool_calls:
    for tool_call in completion.choices[0].message.tool_calls:
        print("Agent is calling Tool", tool_call.function.name)
        result = agentrpc.openai.execute_tool(tool_call)
        print(result)
