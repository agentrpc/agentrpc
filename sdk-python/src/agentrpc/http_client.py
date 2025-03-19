import time
from importlib.metadata import version, PackageNotFoundError
from typing import Dict, Any, Optional
import requests
from .errors import AgentRPCError


class HTTPClient:
    """HTTP client for making requests to the AgentRPC API."""

    def __init__(self, endpoint: str, api_secret: str):
        """Initialize the HTTP client.

        Args:
            endpoint: The API endpoint.
            api_secret: The API secret key.
        """
        self.endpoint = endpoint.rstrip("/")
        self.api_secret = api_secret
        self.cluster_id = None
        self.machine_id = None

        # Get SDK version from package metadata
        try:
            sdk_version = version("agentrpc")
        except PackageNotFoundError:
            sdk_version = "unknown"

        # Set standard headers
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_secret}",
            "x-machine-sdk-version": sdk_version,
            "x-machine-sdk-language": "python",
            "x-machine-id": "python",
        }

    def list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List tools from the AgentRPC API.

        Args:
            params: Parameters including clusterId.

        Returns:
            The API response.

        Raises:
            AgentRPCError: If the request fails.
        """
        cluster_id = params.get("params", {}).get("clusterId")
        if not cluster_id:
            raise AgentRPCError("clusterId is required")

        try:
            response = self.get(f"/clusters/{cluster_id}/tools")
            return {"status": 200, "body": response}
        except Exception as e:
            raise AgentRPCError(f"Failed to list tools: {str(e)}")

    def create_job(
        self,
        cluster_id: str,
        function_name: Optional[str] = None,
        tool_name: Optional[str] = None,
        input_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        if not function_name and not tool_name:
            raise AgentRPCError("Either function or tool must be provided")

        payload = {"input": input_data or {}}

        if function_name:
            payload["function"] = function_name
        if tool_name:
            payload["tool"] = tool_name

        query_params = {
            "waitTime": "20",
        }

        try:
            return self.post(
                f"/clusters/{cluster_id}/jobs", payload, params=query_params
            )
        except Exception as e:
            raise AgentRPCError(f"Failed to create job: {str(e)}")

    def get_job(self, cluster_id: str, job_id: str) -> Dict[str, Any]:
        try:
            query_params = {
                "waitTime": "20",
            }
            response = self.get(
                f"/clusters/{cluster_id}/jobs/{job_id}", params=query_params
            )
            return {"status": 200, "body": response}
        except Exception as e:
            raise AgentRPCError(f"Failed to get job details: {str(e)}")

    def poll_for_job_completion(
        self,
        cluster_id: str,
        job_id: str,
        initial_status: Optional[str] = None,
        initial_result: str = "",
        initial_result_type: str = "rejection",
        poll_interval: float = 1.0,
    ) -> Dict[str, str]:
        status = initial_status
        result = initial_result
        result_type = initial_result_type

        while not status or status not in ["failure", "done"]:
            time.sleep(poll_interval)

            details = self.get_job(cluster_id, job_id)

            if details.get("status") != 200:
                raise AgentRPCError(
                    f"Failed to fetch job details: {details.get('status')}"
                )

            body = details.get("body", {})
            status = body.get("status")
            result = body.get("result") or ""
            result_type = body.get("resultType") or "rejection"

        return {"status": status, "result": result, "resultType": result_type}

    def create_and_poll_job(
        self, cluster_id: str, tool_name: str, input_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Create a job and poll for completion.

        Args:
            cluster_id: The cluster ID.
            tool_name: The tool name.
            input_data: The input data.

        Returns:
            The final job status, result, and result type.

        Raises:
            AgentRPCError: If the request fails.
        """
        # Create the job with maximum server-side wait time
        create_result = self.create_job(
            cluster_id=cluster_id,
            tool_name=tool_name,
            input_data=input_data,
        )

        # Poll for completion
        return self.poll_for_job_completion(
            cluster_id=cluster_id,
            job_id=create_result.get("id"),
            initial_status=create_result.get("status"),
            initial_result=create_result.get("result") or "",
            initial_result_type=create_result.get("resultType") or "rejection",
        )

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make a GET request to the API.

        Args:
            path: The API path.
            params: Query parameters.

        Returns:
            The API response.

        Raises:
            AgentRPCError: If the request fails for any reason.
        """
        url = f"{self.endpoint}{path}"

        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            raise AgentRPCError(
                f"HTTP error: {e.response.status_code} - {e.response.text}",
                status_code=e.response.status_code,
                response=e.response.text,
            )
        except requests.RequestException as e:
            raise AgentRPCError(f"Request error: {str(e)}")
        except Exception as e:
            raise AgentRPCError(f"Unexpected error: {str(e)}")

    def post(
        self, path: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Make a POST request to the API.

        Args:
            path: The API path.
            data: The request body.
            params: Optional query parameters.

        Returns:
            The API response.

        Raises:
            AgentRPCError: If the request fails for any reason.
        """
        url = f"{self.endpoint}{path}"

        try:
            response = requests.post(
                url, json=data, params=params, headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            raise AgentRPCError(
                f"HTTP error: {e.response.status_code} - {e.response.text}",
                status_code=e.response.status_code,
                response=e.response.text,
            )
        except requests.RequestException as e:
            raise AgentRPCError(f"Request error: {str(e)}")
        except Exception as e:
            raise AgentRPCError(f"Unexpected error: {str(e)}")
