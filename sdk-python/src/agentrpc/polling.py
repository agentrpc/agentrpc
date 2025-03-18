import json
import time
import threading
import uuid
import inspect
import concurrent.futures
from typing import Any, Callable, Dict, List, Optional, TypeVar, Type, get_type_hints
import logging
from contextlib import contextmanager
import traceback

try:
    from pydantic import BaseModel, create_model, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

from .errors import AgentRPCError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agentrpc")

# Constants
MAX_CONSECUTIVE_POLL_FAILURES = 50
DEFAULT_RETRY_AFTER = 10


class Tool:
    """Representation of a tool that can be registered with AgentRPC."""
    
    def __init__(
        self,
        name: str,
        handler: Callable,
        schema: Dict[str, Any],
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a tool.
        
        Args:
            name: The name of the tool.
            handler: The function that implements the tool.
            schema: The JSON schema for the tool's input.
            description: A description of what the tool does.
            config: Additional configuration for the tool.
        """
        self.name = name
        self.handler = handler
        self.schema = schema
        self.description = description
        self.config = config


class PollingAgent:
    """Agent responsible for polling for tool invocation requests."""
    
    def __init__(self, client, machine_id: str, cluster_id: str, api_secret: str, endpoint: str):
        """Initialize the polling agent.
        
        Args:
            client: The AgentRPC client.
            machine_id: The machine ID.
            cluster_id: The cluster ID.
            api_secret: The API secret.
            endpoint: The API endpoint.
        """
        self.client = client
        self.machine_id = machine_id
        self.cluster_id = cluster_id
        self.api_secret = api_secret
        self.endpoint = endpoint
        self.tools: Dict[str, Tool] = {}
        self.polling_thread: Optional[threading.Thread] = None
        self.should_stop = threading.Event()
        self.retry_after = DEFAULT_RETRY_AFTER
        self.consecutive_failures = 0
        
    def register(self, tool: Tool) -> None:
        """Register a tool with the agent.
        
        Args:
            tool: The tool to register.
            
        Raises:
            AgentRPCError: If a tool with the same name is already registered or if 
                           the polling is already active.
        """
        if self.is_polling():
            raise AgentRPCError("Tools must be registered before starting the polling agent")
            
        if tool.name in self.tools:
            raise AgentRPCError(f"Tool with name '{tool.name}' already registered")
            
        logger.info(f"Registering tool: {tool.name}")
        self.tools[tool.name] = tool
        
    def is_polling(self) -> bool:
        """Check if the agent is currently polling.
        
        Returns:
            True if polling, False otherwise.
        """
        return self.polling_thread is not None and self.polling_thread.is_alive()
    
    def start(self) -> None:
        """Start polling for tool invocations.
        
        Raises:
            AgentRPCError: If no tools are registered or polling is already active.
        """
        if not self.tools:
            raise AgentRPCError("Cannot start polling with no registered tools")
            
        if self.is_polling():
            raise AgentRPCError("Polling is already active")
            
        # Register the machine with tools first
        self._register_machine()
            
        logger.info("Starting polling agent")
        self.should_stop.clear()
        self.polling_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.polling_thread.start()
        
    def stop(self) -> None:
        """Stop polling for tool invocations."""
        if self.is_polling():
            logger.info("Stopping polling agent")
            self.should_stop.set()
            self.polling_thread.join(timeout=5)
            self.polling_thread = None
            
    def _poll_loop(self) -> None:
        """Main polling loop."""
        while not self.should_stop.is_set():
            try:
                self._poll_once()
                # Reset consecutive failures on success
                self.consecutive_failures = 0
                
            except Exception as e:
                self.consecutive_failures += 1
                logger.error(f"Error in polling loop: {str(e)}")
                logger.debug(traceback.format_exc())
                
                if self.consecutive_failures > MAX_CONSECUTIVE_POLL_FAILURES:
                    logger.error(f"Too many consecutive failures ({self.consecutive_failures}), stopping polling")
                    break
                    
            # Sleep between polls
            if not self.should_stop.is_set():
                self.should_stop.wait(self.retry_after)
    
    def _register_machine(self) -> None:
        """Register the machine with the available tools."""
        logger.info("Registering machine with tools")
        
        # Prepare payload for registration
        payload = {
            "service": "agentrpc-python",
            "tools": []
        }
        
        for tool_name, tool in self.tools.items():
            schema_json = json.dumps(tool.schema)
            payload["tools"].append({
                "name": tool.name,
                "description": tool.description or "",
                "schema": schema_json
            })
        
        try:
            # Use the HTTP client to register the machine
            headers = {
                "Authorization": f"Bearer {self.api_secret}",
                "Content-Type": "application/json",
                "X-Machine-ID": self.machine_id,
                "X-Machine-SDK-Version": "python",  # Replace with actual version
                "X-Machine-SDK-Language": "python"
            }
            
            http_client = self.client._AgentRPC__http_client
            response = http_client.post(
                f"/machines",
                payload,
                headers=headers
            )
            
            if "clusterId" not in response:
                raise AgentRPCError(f"Failed to register machine: Invalid response: {response}")
                
            logger.info(f"Machine registered with cluster ID: {response['clusterId']}")
            
        except Exception as e:
            raise AgentRPCError(f"Failed to register machine: {str(e)}")
    
    def _poll_once(self) -> None:
        """Make a single poll request."""
        try:
            http_client = self.client._AgentRPC__http_client
            
            # Prepare polling request
            query_params = {
                "machineId": self.machine_id,
                "status": "pending",
                "limit": 10,
                "acknowledge": True,
                "waitTime": 10  # 10 second long poll
            }
            
            # Add optional tools parameter if we have specific tools
            if self.tools:
                query_params["tools"] = ",".join(self.tools.keys())
            
            # Make the polling request
            response = http_client.get(
                f"/clusters/{self.cluster_id}/jobs",
                params=query_params
            )
            
            # Check if there are any jobs to process
            if response and isinstance(response, list) and len(response) > 0:
                logger.info(f"Received {len(response)} jobs")
                
                # Process jobs in parallel
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # Submit all jobs to the executor
                    futures = []
                    for job in response:
                        futures.append(executor.submit(self._process_job, job, http_client))
                    
                    # Wait for all jobs to complete
                    concurrent.futures.wait(futures)
            
            # Check for retry-after header
            retry_after = None
            if isinstance(response, dict) and "retryAfter" in response:
                retry_after = response.get("retryAfter")
            
            if retry_after and isinstance(retry_after, int):
                self.retry_after = max(1, min(retry_after, 30))  # Between 1 and 30 seconds
                
        except Exception as e:
            logger.error(f"Error in polling: {str(e)}")
            self.retry_after = DEFAULT_RETRY_AFTER
            raise
    
    def _process_job(self, job: Dict[str, Any], http_client) -> None:
        """Process a single job.
        
        Args:
            job: The job to process.
            http_client: The HTTP client to use for reporting results.
        """
        job_id = job.get("id", "unknown")
        tool_name = job.get("function")
        input_data = job.get("input", {})
        
        logger.info(f"Processing job: {job_id}")
        
        # Execute the tool
        start_time = time.time()
        try:
            result = self._execute_tool({
                "id": job_id,
                "function": tool_name,
                "input": input_data
            })
            
            execution_time = int((time.time() - start_time) * 1000)  # ms
            
            # Send the result back
            result_payload = {
                "result": result.get("result"),
                "resultType": "resolution",  # Use "resolution" for successful executions
                "meta": {
                    "functionExecutionTime": execution_time
                }
            }
            
            # Complete the job
            http_client.post(
                f"/clusters/{self.cluster_id}/jobs/{job_id}/result",
                result_payload
            )
            
            logger.info(f"Completed job: {job_id}")
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error executing job {job_id}: {error_message}")
            
            # Report job failure
            http_client.post(
                f"/clusters/{self.cluster_id}/jobs/{job_id}/result",
                {
                    "result": error_message,
                    "resultType": "rejection",  # Use "rejection" for failed executions
                    "meta": {}
                }
            )
    
    def _execute_tool(self, call_message: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool based on the call message.
        
        Args:
            call_message: The message containing the tool name and input.
            
        Returns:
            The result of executing the tool.
            
        Raises:
            AgentRPCError: If the tool is not found or if there's an error executing it.
        """
        job_id = call_message.get("id", "unknown")
        function_name = call_message.get("function")
        input_data = call_message.get("input", {})
        
        if not function_name:
            raise AgentRPCError(f"No function name provided in call message for job {job_id}")
            
        # Find the registered tool
        tool = self.tools.get(function_name)
        if not tool:
            raise AgentRPCError(f"Tool '{function_name}' not found for job {job_id}")
        
        # Validate that input_data is a dictionary
        if not isinstance(input_data, dict):
            raise AgentRPCError(f"Input data must be a dictionary, got {type(input_data).__name__}")
            
        logger.info(f"Executing tool '{function_name}' for job {job_id}")
        
        try:
            # Execute the tool handler
            # We need to handle both direct function calls and functions expecting unpacked arguments
            try:
                # First try calling with the input data dictionary
                result = tool.handler(input_data)
            except TypeError as e:
                # If that fails with a TypeError about missing arguments, try unpacking the input
                if "missing" in str(e) and "argument" in str(e):
                    # Try to unpack the input data as keyword arguments
                    result = tool.handler(**input_data)
                else:
                    # If it's a different TypeError, re-raise it
                    raise
            
            # Determine result type
            result_type = "string"
            if result is None:
                result = "null"
                result_type = "null"
            elif isinstance(result, bool):
                result_type = "boolean"
            elif isinstance(result, (int, float)):
                result_type = "number"
            elif isinstance(result, dict):
                result_type = "object"
                # Ensure result is JSON serializable
                result = json.loads(json.dumps(result))
            elif isinstance(result, list):
                result_type = "array"
                # Ensure result is JSON serializable
                result = json.loads(json.dumps(result))
            else:
                # Convert to string for all other types
                result = str(result)
                
            return {
                "result": result,
                "resultType": result_type
            }
            
        except Exception as e:
            error_message = f"Error executing tool '{function_name}': {str(e)}"
            logger.error(f"{error_message}\n{traceback.format_exc()}")
            raise AgentRPCError(error_message) 