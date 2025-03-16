from agentrpc import AgentRPC

from openai import OpenAI

openaiClient = OpenAI(api_key="")

agentRPC = AgentRPC(api_secret="")

# Tools must be registered in a different SDK. This expects a tool `hello` that takes `name` arg.
tools = agentRPC.openai.get_tools()

completion = openaiClient.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Say hello to John"}],
    tools=tools,
)

if completion.choices[0].message.tool_calls:
    for tool_call in completion.choices[0].message.tool_calls:
        print("Is Calling Tool", tool_call.function.name)
        result = agentRPC.openai.execute_tool(tool_call.function)
        print(result)
