"""Custom exceptions for the FIWARE Actuators Setup package."""


class IoTAgentError(Exception):
    """Base exception for IoT Agent errors."""

    pass


class IoTAgentClientError(IoTAgentError):
    """Exception for HTTP 4xx client errors."""

    def __init__(
        self, status_code: int, message: str, response_body: str | None = None
    ):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(f"Client error {status_code}: {message}")


class IoTAgentServerError(IoTAgentError):
    """Exception for HTTP 5xx server errors."""

    def __init__(
        self, status_code: int, message: str, response_body: str | None = None
    ):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(f"Server error {status_code}: {message}")


class IoTAgentNotFoundError(IoTAgentClientError):
    """Exception for HTTP 404 Not Found errors."""

    def __init__(self, resource: str, response_body: str | None = None):
        super().__init__(
            status_code=404,
            message=f"Resource not found: {resource}",
            response_body=response_body,
        )
        self.resource = resource
