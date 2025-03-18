from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, Type
import inspect
import uuid
import os

from .openai import OpenAIIntegration
from .http_client import HTTPClient
from .errors import AgentRPCError
from .polling import PollingAgent, Tool
from .schema import generate_schema_from_function, generate_schema_from_type_annotations

try:
    from pydantic import BaseModel
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


class AgentRPC:
    """AgentRPC client for connecting to AgentRPC API."""

    def __init__(
        self,
        api_secret: str,
        endpoint: str = "https://api.agentrpc.com",
        machine_id: Optional[str] = None,
    ):
        """Initialize the AgentRPC client.

        Args:
            api_secret: The API secret key.
            endpoint: Custom API endpoint. Defaults to 'https://api.agentrpc.com'.
            machine_id: Custom machine ID. Defaults to a generated UUID.
        """

        self.__api_secret = api_secret
        self.__endpoint = endpoint
        self.__machine_id = machine_id or str(uuid.uuid4())
        self.__http_client = HTTPClient(endpoint, api_secret)
        self.openai = OpenAIIntegration(self)
        self.__polling_agent = None

        parts = api_secret.split("_")
        if len(parts) != 3 or parts[0] != "sk":
            raise ValueError("Invalid API Secret.")
        else:
            _, cluster_id, rand = parts
            self.cluster_id = cluster_id

    def list_tools(self, params):
        """List tools from the HTTP client."""
        return self.__http_client.list_tools(params)

    def create_and_poll_job(self, cluster_id: str, tool_name: str, input_data: dict):
        """Create and poll a job using the HTTP client."""
        return self.__http_client.create_and_poll_job(cluster_id, tool_name, input_data)

    def register(
        self,
        func: Optional[Callable] = None,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        schema: Dict[str, Any],
    ) -> Callable:
        """Register a function as a tool.
        
        Can be used as a decorator or as a function.
        
        Args:
            func: The function to register (when used directly).
            name: Custom name for the tool (defaults to function name).
            description: Description of what the tool does.
            schema: JSON schema for the tool's input (required).
            
        Returns:
            The registered function, allowing use as a decorator.
            
        Examples:
            >>> # As a decorator
            >>> @rpc.register(name="greet", description="Greet someone", schema={"type": "object", "properties": {"name": {"type": "string"}}})
            >>> def say_hello(name: str) -> str:
            >>>     return f"Hello, {name}!"
            >>>
            >>> # Direct usage
            >>> def calculate_sum(a: int, b: int) -> int:
            >>>     return a + b
            >>> rpc.register(calculate_sum, name="sum", description="Add two numbers", schema={"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}})
        """
        # Initialize the polling agent if not already done
        if self.__polling_agent is None:
            self.__polling_agent = PollingAgent(
                client=self,
                machine_id=self.__machine_id,
                cluster_id=self.cluster_id,
                api_secret=self.__api_secret,
                endpoint=self.__endpoint,
            )
        
        # When used as a decorator without args: @rpc.register(schema=...)
        if func is not None and callable(func):
            if schema is None:
                raise AgentRPCError("Schema parameter is required when registering a tool")
            return self._register_function(func, name=name, description=description, schema=schema)
            
        # When used as decorator with args: @rpc.register(name="xyz", schema=...)
        # or when called directly with just config: rpc.register(name="xyz", schema=...)(func)
        if func is None or not callable(func):
            if schema is None:
                raise AgentRPCError("Schema parameter is required when registering a tool")
            def decorator(fn):
                return self._register_function(fn, name=name, description=description, schema=schema)
            return decorator
            
        # When called directly with function: rpc.register(func, name="xyz", schema=...)
        return self._register_function(func, name=name, description=description, schema=schema)
        
    def _register_function(
        self, 
        func: Callable, 
        name: Optional[str] = None, 
        description: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Callable:
        """Internal method to register a function."""
        if not callable(func):
            raise AgentRPCError("Cannot register a non-callable object")
            
        # Check that schema is provided
        if schema is None:
            raise AgentRPCError("Schema parameter is required when registering a tool")
            
        # Use function name if no custom name provided
        tool_name = name or func.__name__
        
        # Use docstring as description if none provided
        tool_description = description
        if tool_description is None and func.__doc__:
            tool_description = inspect.cleandoc(func.__doc__).split("\n")[0]
            
        # Validate that the schema represents an object (dictionary)
        if not (isinstance(schema, dict) and schema.get("type") == "object"):
            schema = {
                "type": "object",
                "properties": {},
                **schema
            }
            
        # Register the tool with the polling agent
        tool = Tool(
            name=tool_name,
            handler=func,
            schema=schema,
            description=tool_description,
        )
        
        self.__polling_agent.register(tool)
        
        # Return the original function to allow chaining decorators
        return func
        
    def listen(self) -> None:
        """Start listening for tool invocations.
        
        This is a blocking call that will register the machine and start polling for jobs.
        """
        if self.__polling_agent is None or not self.__polling_agent.tools:
            raise AgentRPCError("Cannot listen with no registered tools")
            
        self.__polling_agent.start()
        
    def unlisten(self) -> None:
        """Stop listening for tool invocations."""
        if self.__polling_agent is not None:
            self.__polling_agent.stop()
            
    def call_tool(
        self, 
        tool_name: str, 
        input_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Call a tool registered on the cluster.
        
        This method creates a job for the specified tool and waits for its result.
        
        Args:
            tool_name: The name of the tool to call.
            input_data: A dictionary containing the input data for the tool.
            **kwargs: If input_data is not provided, keyword arguments will be used.
            
        Returns:
            The result of the tool execution.
            
        Raises:
            AgentRPCError: If the job fails or times out.
            ValueError: If invalid arguments are provided.
        """
        # Determine the input data format
        if input_data is not None and kwargs:
            raise ValueError("Cannot provide both input_data and keyword arguments")
            
        # If input_data is provided, ensure it's a dictionary
        if input_data is not None:
            if not isinstance(input_data, dict):
                raise ValueError("input_data must be a dictionary")
        else:
            # Use kwargs as input data if no dictionary was provided
            input_data = kwargs
            
        # Call the tool and wait for result
        response = self.__http_client.create_and_poll_job(
            cluster_id=self.cluster_id,
            tool_name=tool_name,
            input_data=input_data,
            wait_time=20,  # Maximum wait time allowed
        )
        
        # Return just the result
        return response.get("result")
