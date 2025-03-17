import os
from pathlib import Path

from dotenv import load_dotenv
from agentrpc import AgentRPC
from agentrpc.openai import OpenAIIntegration

# Load environment variables from .env file
dotenv_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)
api_secret = os.environ.get("INFERABLE_TEST_API_SECRET", "test_secret")
api_endpoint = os.environ.get("INFERABLE_TEST_API_ENDPOINT", "https://api.agentrpc.com")


def test_client_init():
    """Test client initialization."""
    client = AgentRPC(api_secret, api_endpoint)

    # Check that properties are set correctly
    assert client._AgentRPC__api_secret == api_secret
    assert client._AgentRPC__endpoint == api_endpoint
    assert client._AgentRPC__http_client is not None
    assert isinstance(client.openai, OpenAIIntegration)


def test_client_openai_completions_get_tools():
    """Test client initialization."""
    client = AgentRPC(api_secret, api_endpoint)
    tools = client.openai.completions.get_tools()
    print(tools)


# def test_client_openai_execute_tool():
#     """Test executing ."""
#     client = AgentRPC(api_secret, api_endpoint)
#     function_call = FunctionCall(name="hello", arguments='{"name": "agent"}')
#     result = client.openai.execute_tool(function_call)
#     print(result)
