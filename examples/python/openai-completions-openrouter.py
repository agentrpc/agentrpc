import os

from agentrpc import AgentRPC
from openai import OpenAI


def main():
    agentrpc = AgentRPC(api_secret=os.environ.get("AGENTRPC_API_SECRET", ""))
    openai = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
    )

    tools = agentrpc.openai.completions.get_tools()

    completion = openai.chat.completions.create(
        model="google/gemini-2.0-flash-001",
        messages=[{"role": "user", "content": "What is the weather in Melbourne?"}],
        tools=tools,
    )

    if completion.choices[0].message.tool_calls:
        for tool_call in completion.choices[0].message.tool_calls:
            print("Agent is calling Tool", tool_call.function.name)
            result = agentrpc.openai.completions.execute_tool(tool_call)
            print(result)


if __name__ == "__main__":
    main()
