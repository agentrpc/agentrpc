from agents import FunctionTool, Tool
import json
from typing import List
from openai.types.chat import ChatCompletionToolParam
from openai.types.chat.chat_completion_message import ChatCompletionMessageToolCall
from .errors import AgentRPCError


class ToolInvoker:
    def __init__(self, client):
        self.__client = client

    def get_tools(self) -> List[dict]:
        """Fetch tools from the API."""
        tool_response = self.__client.list_tools(
            {"params": {"clusterId": self.__client.cluster_id}}
        )

        if tool_response.get("status") != 200:
            raise AgentRPCError(
                f"Failed to list AgentRPC tools: {tool_response.get('status')}",
                status_code=tool_response.get("status"),
                response=tool_response,
            )

        return tool_response.get("body", [])

    def execute_tool(self, function_name: str, arguments: dict) -> str:
        """Execute a tool by function name and arguments."""
        try:
            job_result = self.__client.create_and_poll_job(
                cluster_id=self.__client.cluster_id,
                tool_name=function_name,
                input_data=arguments,
            )

            status = job_result.get("status")
            if status != "done":
                if status == "failure":
                    raise AgentRPCError(
                        f"Tool execution failed: {job_result.get('result')}"
                    )
                    raise AgentRPCError(f"Unexpected job status: {status}")

            return f"{job_result.get('resultType')}: {job_result.get('result', 'Function executed successfully but returned no result.')}"
        except Exception as e:
            raise AgentRPCError(f"Error executing function: {str(e)}")


class OpenAIIntegration:
    def __init__(self, client):
        self.completions = OpenAICompletionsIntegration(client)
        self.agents = OpenAIAgentsIntegration(client)


class OpenAICompletionsIntegration:
    def __init__(self, client):
        self.__tool_invoker = ToolInvoker(client)

    def get_tools(self) -> List[ChatCompletionToolParam]:
        tools = self.__tool_invoker.get_tools()
        return [
            ChatCompletionToolParam(
                type="function",
                function={
                    "name": str(tool.get("name", "")),
                    "description": str(tool.get("description", "")),
                    "parameters": json.loads(tool.get("schema", "{}")),
                },
            )
            for tool in tools
        ]

    def execute_tool(self, tool_call: ChatCompletionMessageToolCall) -> str:
        return self.__tool_invoker.execute_tool(
            tool_call.function.name, json.loads(tool_call.function.arguments)
        )


class OpenAIAgentsIntegration:
    def __init__(self, client):
        self.__client = client
        self.__cluster_id = None
        self.__tool_invoker = ToolInvoker(client)

    def get_tools(self) -> List[Tool]:
        tools = self.__tool_invoker.get_tools()

        async def invoke_tool(tool_name: str, tool_args: dict) -> str:
            return self.__tool_invoker.execute_tool(tool_name, tool_args)

        return [
            FunctionTool(
                name=str(tool.get("name", "")),
                description=str(tool.get("description", "")),
                params_json_schema=json.loads(tool.get("schema", "{}")),
                on_invoke_tool=lambda ctx,
                args,
                tool_name=tool.get("name", ""): invoke_tool(
                    tool_name, json.loads(args)
                ),
            )
            for tool in tools
        ]
