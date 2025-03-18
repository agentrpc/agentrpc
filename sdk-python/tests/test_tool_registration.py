import os
import time
import unittest
import uuid
from unittest import mock
from pathlib import Path

import pytest
from dotenv import load_dotenv

from agentrpc import AgentRPC
from agentrpc.polling import Tool
from agentrpc.errors import AgentRPCError


# Load environment variables from .env file if it exists
dotenv_path = Path(__file__).parent.parent / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)

# Use a test API secret, or a real one if available for integration tests
API_SECRET = os.environ.get("AGENTRPC_API_SECRET")
API_ENDPOINT = os.environ.get("AGENTRPC_API_ENDPOINT")

# Set this to True to run integration tests against the real API
RUN_INTEGRATION_TESTS = True


class TestToolRegistration(unittest.TestCase):
    """Test the tool registration functionality."""

    def test_tool_registration_decorator(self):
        """Test registering a tool using the decorator syntax."""
        # Create a client with a mocked HTTP client
        client = AgentRPC(API_SECRET, API_ENDPOINT)
        client._AgentRPC__http_client.post = mock.MagicMock(return_value={"clusterId": "test"})
        
        # Test decorator usage
        @client.register(name="greet", description="Greet someone")
        def say_hello(name: str) -> str:
            return f"Hello, {name}!"
            
        # Verify tool was registered
        self.assertIsNotNone(client._AgentRPC__polling_agent)
        self.assertIn("greet", client._AgentRPC__polling_agent.tools)
        
        # Verify tool properties
        tool = client._AgentRPC__polling_agent.tools["greet"]
        self.assertEqual(tool.name, "greet")
        self.assertEqual(tool.description, "Greet someone")
        self.assertEqual(tool.handler, say_hello)
        
        # Verify schema generation
        self.assertEqual(tool.schema["type"], "object")
        
    def test_direct_tool_registration(self):
        """Test registering a tool by direct function call."""
        # Create a client with a mocked HTTP client
        client = AgentRPC(API_SECRET, API_ENDPOINT)
        client._AgentRPC__http_client.post = mock.MagicMock(return_value={"clusterId": "test"})
        
        # Define a function
        def calculate_sum(a: int, b: int) -> int:
            """Add two numbers together."""
            return a + b
            
        # Register it directly
        client.register(calculate_sum, name="sum", description="Add two numbers")
        
        # Verify tool was registered
        self.assertIsNotNone(client._AgentRPC__polling_agent)
        self.assertIn("sum", client._AgentRPC__polling_agent.tools)
        
        # Verify tool properties
        tool = client._AgentRPC__polling_agent.tools["sum"]
        self.assertEqual(tool.name, "sum")
        self.assertEqual(tool.description, "Add two numbers")
        self.assertEqual(tool.handler, calculate_sum)
        
    def test_cannot_register_after_listen(self):
        """Test that tools cannot be registered after listen() is called."""
        # Create a client with mocked methods
        client = AgentRPC(API_SECRET, API_ENDPOINT)
        client._AgentRPC__http_client.post = mock.MagicMock(return_value={"clusterId": "test"})
        
        # Create a real polling agent instead of a mock
        from agentrpc.polling import PollingAgent
        client._AgentRPC__polling_agent = PollingAgent(
            client=client,
            machine_id="test",
            cluster_id="test",
            api_secret=API_SECRET,
            endpoint=API_ENDPOINT
        )
        
        # Add a test tool
        client._AgentRPC__polling_agent.tools = {"test": mock.MagicMock()}
        
        # Mock the is_polling method to return True
        client._AgentRPC__polling_agent.is_polling = mock.MagicMock(return_value=True)
        
        # Try to register a tool after polling has started
        with self.assertRaises(Exception):
            client.register(lambda x: x, name="too_late")
        
    def test_tool_execution(self):
        """Test executing a registered tool."""
        # Create a client with a mocked HTTP client
        client = AgentRPC(API_SECRET, API_ENDPOINT)
        client._AgentRPC__http_client.post = mock.MagicMock(return_value={"clusterId": "test"})
        
        # Register a test tool
        @client.register
        def multiply(a: int, b: int) -> int:
            return a * b
            
        # Create a mock call message
        call_message = {
            "id": "job_123",
            "function": "multiply",
            "input": {"a": 5, "b": 7}
        }
        
        # Execute the tool directly
        result = client._AgentRPC__polling_agent._execute_tool(call_message)
        
        # Verify result
        self.assertEqual(result["result"], 35)
        self.assertEqual(result["resultType"], "number")
        
    def test_call_tool(self):
        """Test calling a tool using the call_tool method."""
        # Create a client with a mocked HTTP client
        client = AgentRPC(API_SECRET, API_ENDPOINT)
        client._AgentRPC__http_client.post = mock.MagicMock(return_value={"clusterId": "test"})
        
        # Mock the create_and_poll_job method
        client._AgentRPC__http_client.create_and_poll_job = mock.MagicMock(
            return_value={"result": 42, "status": "done"}
        )
        
        # Call the tool with keyword arguments
        result = client.call_tool("multiply", a=6, b=7)
        self.assertEqual(result, 42)
        
        # Verify create_and_poll_job was called with correct arguments
        client._AgentRPC__http_client.create_and_poll_job.assert_called_with(
            cluster_id=client.cluster_id,
            tool_name="multiply",
            input_data={"a": 6, "b": 7},
            wait_time=20,
        )
        
        # Call with a dictionary argument
        result = client.call_tool("multiply", input_data={"a": 6, "b": 7})
        self.assertEqual(result, 42)
        
        # Verify create_and_poll_job was called with correct arguments
        client._AgentRPC__http_client.create_and_poll_job.assert_called_with(
            cluster_id=client.cluster_id,
            tool_name="multiply",
            input_data={"a": 6, "b": 7},
            wait_time=20,
        )
        
        # Test validation error when providing non-dictionary input
        with self.assertRaises(ValueError):
            client.call_tool("multiply", "invalid input")
        
        # Test validation error when providing both input_data and kwargs
        with self.assertRaises(ValueError):
            client.call_tool("multiply", input_data={"a": 1}, b=2)

    def test_execute_tool_input_validation(self):
        """Test that tool execution validates input data is a dictionary."""
        # Create a client with a mocked HTTP client
        client = AgentRPC(API_SECRET, API_ENDPOINT)
        client._AgentRPC__http_client.post = mock.MagicMock(return_value={"clusterId": "test"})
        
        # Register a test tool
        @client.register
        def test_tool(data: dict) -> str:
            return "Success"
            
        # Test with valid dictionary input
        valid_call = {
            "id": "job_123",
            "function": "test_tool",
            "input": {"key": "value"}
        }
        result = client._AgentRPC__polling_agent._execute_tool(valid_call)
        self.assertEqual(result["result"], "Success")
        
        # Test with non-dictionary input
        invalid_call = {
            "id": "job_456",
            "function": "test_tool",
            "input": "not a dictionary"
        }
        with self.assertRaises(AgentRPCError) as context:
            client._AgentRPC__polling_agent._execute_tool(invalid_call)
        
        self.assertIn("Input data must be a dictionary", str(context.exception))


@pytest.mark.skipif(not RUN_INTEGRATION_TESTS, reason="Integration tests disabled")
class TestToolRegistrationIntegration(unittest.TestCase):
    """Integration tests for tool registration that use the real API.
    
    These tests are skipped by default. To run them, set RUN_INTEGRATION_TESTS to True.
    """
    
    def setUp(self):
        """Set up the test environment."""
        # Skip if integration tests are disabled
        if not RUN_INTEGRATION_TESTS:
            self.skipTest("Integration tests disabled")

        # Check if the API endpoint is available        
        try:
            import requests
            endpoint = API_ENDPOINT or "https://api.agentrpc.com"
            requests.get(endpoint, timeout=2)
        except (requests.RequestException, ImportError):
            self.skipTest("API endpoint not available")
            
        # Create a client with a unique machine ID to avoid conflicts
        self.client = AgentRPC(
            API_SECRET, 
            API_ENDPOINT,
            machine_id=f"test-{uuid.uuid4()}"
        )
    
    def test_register_and_listen(self):
        """Test registering a tool and starting/stopping the poller."""
        # Register a simple test tool
        @self.client.register(name="echo", description="Echo back the input")
        def echo(input_data):
            # Handle both dictionary input and direct parameter
            if isinstance(input_data, dict) and "message" in input_data:
                return input_data["message"]
            return input_data
            
        # Start listening in a non-blocking way
        self.client.listen()
        
        # Verify we're polling
        self.assertTrue(self.client._AgentRPC__polling_agent.is_polling())
        
        # Wait a bit to allow registration to complete
        time.sleep(2)

        # Call the tool
        result = self.client.call_tool("echo", input_data={"message": "Hello, world!"})
        self.assertEqual(result, "Hello, world!")
        
        # Try with keyword arguments
        result = self.client.call_tool("echo", message="Hello, again!")
        self.assertEqual(result, "Hello, again!")
        
        # Stop listening
        self.client.unlisten()
        
        # Verify we've stopped polling
        time.sleep(1)  # Give it time to stop
        self.assertFalse(self.client._AgentRPC__polling_agent.is_polling()) 