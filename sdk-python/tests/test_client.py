import os
from pathlib import Path

from dotenv import load_dotenv
from agentrpc import AgentRPC
from agentrpc.openai import OpenAIIntegration

# Load environment variables from .env file
dotenv_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Validate required environment variables
required_env_vars = ["AGENTRPC_API_SECRET"]
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    raise EnvironmentError(
        f"Missing required environment variables: {', '.join(missing_vars)}. "
        "Please set these variables in your .env file."
    )

api_secret = os.environ.get("AGENTRPC_API_SECRET")
api_endpoint = os.environ.get("AGENTRPC_API_ENDPOINT", "https://api.agentrpc.com")


def test_client_init():
    """Test client initialization."""
    rpc = AgentRPC(api_secret, api_endpoint)

    # Check that properties are set correctly
    assert rpc._AgentRPC__api_secret == api_secret
    assert rpc._AgentRPC__endpoint == api_endpoint
    assert rpc._AgentRPC__http_client is not None
    assert isinstance(rpc.openai, OpenAIIntegration)


def test_client_openai_completions_get_tools():
    """Test client initialization."""
    rpc = AgentRPC(api_secret, api_endpoint)
    tools = rpc.openai.completions.get_tools()
    print(tools)


# def test_client_openai_execute_tool():
#     """Test executing ."""
#     rpc = AgentRPC(api_secret, api_endpoint)
#     function_call = FunctionCall(name="hello", arguments='{"name": "agent"}')
#     result = rpc.openai.execute_tool(function_call)
#     print(result)
