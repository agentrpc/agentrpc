import os

from agentrpc import AgentRPC
from openai import OpenAI


def main():
    rpc = AgentRPC(
        api_secret=os.environ.get("AGENTRPC_API_SECRET", ""),
    )
    openai = OpenAI(
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        base_url="https://api.anthropic.com/v1/",
    )

    tools = rpc.openai.completions.get_tools()

    completion = openai.chat.completions.create(
        model="claude-3-sonnet-20240229",
        messages=[{"role": "user", "content": "What is the weather in Melbourne?"}],
        tools=tools,
    )

    if completion.choices[0].message.tool_calls:
        for tool_call in completion.choices[0].message.tool_calls:
            print("Agent is calling Tool", tool_call.function.name)
            result = rpc.openai.completions.execute_tool(tool_call)
            print(result)


if __name__ == "__main__":
    main()
