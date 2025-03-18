import os
from pathlib import Path

from dotenv import load_dotenv
from agentrpc import AgentRPC
from agentrpc.openai import OpenAIIntegration

# Load environment variables from .env file
dotenv_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Use real API credentials from the .env file
api_secret = os.environ.get("AGENTRPC_API_SECRET")
api_endpoint = os.environ.get("AGENTRPC_API_ENDPOINT")


def test_client_init():
    """Test client initialization."""
    client = AgentRPC(api_secret, api_endpoint)

    # Check that properties are set correctly
    assert client._AgentRPC__api_secret == api_secret
    assert client._AgentRPC__endpoint == api_endpoint
    assert client._AgentRPC__http_client is not None
    assert isinstance(client.openai, OpenAIIntegration)


def test_client_openai_completions_get_tools():
    """Test OpenAI integration for completions."""
    # Use real client with actual API credentials
    client = AgentRPC(api_secret, api_endpoint)
    
    # Test the get_tools method - this will make a real API call
    tools = client.openai.completions.get_tools()
    
    # Verify the result
    assert tools is not None


# def test_client_openai_execute_tool():
#     """Test executing ."""
#     client = AgentRPC(api_secret, api_endpoint)
#     function_call = FunctionCall(name="hello", arguments='{"name": "agent"}')
#     result = client.openai.execute_tool(function_call)
#     print(result)
