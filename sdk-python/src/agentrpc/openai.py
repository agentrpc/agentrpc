import json
from typing import List
from openai.types.chat import ChatCompletionToolParam
from openai.types.chat.chat_completion_message import ChatCompletionMessageToolCall
from .errors import AgentRPCError


class OpenAIIntegration:
    def __init__(self, client):
        self.__client = client
        self.__cluster_id = None

    def __get_cluster_id(self) -> str:
        """Get or initialize the cluster ID.

        Returns:
            The cluster ID.
        """
        if not self.__cluster_id:
            self.__cluster_id = self.__client.get_cluster_id()
        return self.__cluster_id

    def get_tools(self) -> List[ChatCompletionToolParam]:
        """Get tools in OpenAI format.

        Returns:
            List of tools formatted for OpenAI.

        Raises:
            AgentRPCError: If the request fails.
        """
        # Ensure we have a cluster ID
        cluster_id = self.__get_cluster_id()

        # Make the API call to list tools
        tool_response = self.__client.list_tools({"params": {"clusterId": cluster_id}})

        # Check the response status
        if tool_response.get("status") != 200:
            raise AgentRPCError(
                f"Failed to list AgentRPC tools: {tool_response.get('status')}",
                status_code=tool_response.get("status"),
                response=tool_response,
            )

        # Transform the tools to OpenAI format
        tools = []
        for tool in tool_response.get("body", []):
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.get("name"),
                        "description": tool.get("description") or "",
                        "parameters": json.loads(tool.get("schema") or "{}"),
                    },
                }
            )

        return tools

    def execute_tool(self, tool_call: ChatCompletionMessageToolCall) -> str:
        """Execute a tool call from OpenAI.

        Args:
            tool_call: The tool call from OpenAI.

        Returns:
            The tool execution result.

        Raises:
            AgentRPCError: If the tool execution fails.
        """
        try:
            # Ensure we have a cluster ID
            cluster_id = self.__get_cluster_id()

            # Get function name and arguments
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            # Create job and poll for completion
            job_result = self.__client.create_and_poll_job(
                cluster_id=cluster_id, tool_name=function_name, input_data=arguments
            )

            status = job_result.get("status")
            if status != "done":
                if status == "failure":
                    raise AgentRPCError(
                        f"Tool execution failed: {job_result.get('result')}"
                    )
                else:
                    raise AgentRPCError(f"Unexpected job status: {status}")

            result_type = job_result.get("resultType")

            result_str = job_result.get("result", "")
            if not result_str:
                return "Function executed successfully but returned no result."

            return f"{result_type}: {result_str}"

        except Exception as e:
            raise AgentRPCError(f"Error executing function: {str(e)}")
