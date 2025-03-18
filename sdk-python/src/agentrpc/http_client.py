import time
import json
from importlib.metadata import version, PackageNotFoundError
from typing import Dict, Any, Optional, List, Tuple, Union
import requests
import logging
from .errors import AgentRPCError

# Setup logging
logger = logging.getLogger("agentrpc")

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

    def get(self, path: str, params: Optional[Dict[str, str]] = None) -> Any:
        """Make a GET request to the API.
        
        Args:
            path: The API path.
            params: Optional query parameters.
            
        Returns:
            The parsed response.
            
        Raises:
            AgentRPCError: If the request fails.
        """
        url = f"{self.endpoint}{path}"
        logger.debug(f"GET {url}")
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get("error", {}).get("message", str(e))
                    raise AgentRPCError(error_message, status_code=e.response.status_code)
                except (ValueError, KeyError):
                    # If response is not JSON or doesn't have expected structure
                    raise AgentRPCError(f"Request failed: {str(e)}", status_code=e.response.status_code if hasattr(e, "response") else None)
            raise AgentRPCError(f"Request failed: {str(e)}")
            
    def post(self, path: str, data: Any, params: Optional[Dict[str, str]] = None, headers: Optional[Dict[str, str]] = None) -> Any:
        """Make a POST request to the API.
        
        Args:
            path: The API path.
            data: The request payload.
            params: Optional query parameters.
            headers: Optional additional headers.
            
        Returns:
            The parsed response.
            
        Raises:
            AgentRPCError: If the request fails.
        """
        url = f"{self.endpoint}{path}"
        logger.debug(f"POST {url}")
        
        # Merge headers
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)
            
        try:
            response = requests.post(
                url,
                headers=request_headers,
                json=data,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get("error", {}).get("message", str(e))
                    raise AgentRPCError(error_message, status_code=e.response.status_code)
                except (ValueError, KeyError):
                    # If response is not JSON or doesn't have expected structure
                    raise AgentRPCError(f"Request failed: {str(e)}", status_code=e.response.status_code if hasattr(e, "response") else None)
            raise AgentRPCError(f"Request failed: {str(e)}")

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
        wait_time: int = 0,
    ) -> Dict[str, Any]:
        """Create a job with the AgentRPC API.

        Args:
            cluster_id: The cluster ID.
            function_name: The function name.
            tool_name: The tool name.
            input_data: The input data.
            wait_time: How long to wait for job completion (0-20 seconds).

        Returns:
            The API response.

        Raises:
            AgentRPCError: If the request fails.
        """
        if not function_name and not tool_name:
            raise AgentRPCError("Either function or tool must be provided")

        payload = {"input": input_data or {}}

        if function_name:
            payload["function"] = function_name
        if tool_name:
            payload["tool"] = tool_name

        query_params = {}
        if wait_time > 0:
            query_params["waitTime"] = str(min(wait_time, 20))  # Max 20 seconds

        try:
            return self.post(
                f"/clusters/{cluster_id}/jobs", 
                payload, 
                params=query_params
            )
        except Exception as e:
            raise AgentRPCError(f"Failed to create job: {str(e)}")

    def get_job(self, job_id: str) -> Dict[str, Any]:
        """Get job status from the AgentRPC API.

        Args:
            job_id: The job ID.

        Returns:
            The API response.

        Raises:
            AgentRPCError: If the request fails.
        """
        try:
            return self.get(f"/jobs/{job_id}")
        except Exception as e:
            raise AgentRPCError(f"Failed to get job: {str(e)}")

    def create_and_poll_job(
        self,
        cluster_id: str,
        tool_name: str,
        input_data: Dict[str, Any],
        wait_time: int = 0,
        max_retries: int = 100,
        retry_interval: int = 1,
    ) -> Dict[str, Any]:
        """Create a job and poll for its completion.

        Args:
            cluster_id: The cluster ID.
            tool_name: The tool name.
            input_data: The input data.
            wait_time: How long to wait for job completion in the initial request.
            max_retries: Maximum number of polling retries.
            retry_interval: Time between polling in seconds.

        Returns:
            The final job status.

        Raises:
            AgentRPCError: If the job fails or polling times out.
        """
        # Try to create the job with the initial wait time
        job = self.create_job(
            cluster_id=cluster_id,
            tool_name=tool_name,
            input_data=input_data,
            wait_time=wait_time,
        )

        if job.get("status") == "done":
            return job

        job_id = job.get("id")
        if not job_id:
            raise AgentRPCError("No job ID returned from create_job")

        # Poll for completion
        for _ in range(max_retries):
            time.sleep(retry_interval)
            job = self.get_job(job_id)
            status = job.get("status")

            if status == "done":
                return job
            elif status == "failure":
                raise AgentRPCError(f"Job failed: {job.get('error')}")
            elif status not in ["pending", "running"]:
                raise AgentRPCError(f"Unexpected job status: {status}")

        raise AgentRPCError(f"Job polling timed out after {max_retries} retries")
