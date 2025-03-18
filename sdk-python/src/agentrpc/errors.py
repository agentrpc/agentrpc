"""Error classes for the AgentRPC client."""

class AgentRPCError(Exception):
    """Base error class for all AgentRPC errors."""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        """Initialize the error.
        
        Args:
            message: The error message.
            status_code: The HTTP status code, if applicable.
            response: The API response, if applicable.
        """
        super().__init__(message)
        self.status_code = status_code
        self.response = response
