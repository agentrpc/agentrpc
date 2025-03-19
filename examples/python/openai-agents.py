import asyncio
import os

from agentrpc import AgentRPC
from agents import Agent, Runner


async def main():
    rpc = AgentRPC(
        api_secret=os.environ.get("AGENTRPC_API_SECRET", ""),
    )

    agent = Agent(name="AgentRPC Agent", tools=rpc.openai.agents.get_tools())

    result = await Runner.run(
        agent,
        input="What is the weather in Melbourne?",
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
