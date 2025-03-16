from .openai import OpenAIIntegration
from .http_client import HTTPClient


class AgentRPC:
    """AgentRPC client for connecting to AgentRPC API."""

    def __init__(
        self,
        api_secret: str,
        endpoint: str = "https://api.agentrpc.com",
    ):
        """Initialize the AgentRPC client.

        Args:
            api_secret: The API secret key.
            endpoint: Custom API endpoint. Defaults to 'https://api.agentrpc.com'.
        """
        self.__api_secret = api_secret
        self.__endpoint = endpoint
        self.__http_client = HTTPClient(endpoint, api_secret)
        self.openai = OpenAIIntegration(self)

    def get_cluster_id(self) -> str:
        """Get the cluster ID from the HTTP client."""
        return self.__http_client.get_cluster_id()

    def list_tools(self, params):
        """List tools from the HTTP client."""
        return self.__http_client.list_tools(params)

    def create_and_poll_job(self, cluster_id: str, tool_name: str, input_data: dict):
        """Create and poll a job using the HTTP client."""
        return self.__http_client.create_and_poll_job(cluster_id, tool_name, input_data)
