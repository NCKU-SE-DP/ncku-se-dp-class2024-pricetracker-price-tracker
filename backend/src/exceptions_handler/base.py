from abc import ABC, abstractmethod
from fastapi.responses import JSONResponse
from sentry_sdk import capture_exception, configure_scope
from typing import Optional, Union

class APIException(ABC, Exception):
    """
    Base API Exception class. All custom exceptions should inherit from this class.
    Attributes:
        error (Optional[Union[str, Exception]]): 
            The error message or exception details. This can be a string message explaining 
            the error or an Exception object providing detailed context.
        details (Optional[str]): 
            The string representation of the error or exception, derived from `error`.
    """

    def __init__(self, error: Optional[Union[str, Exception]] = None):
        """
        Initialize the exception with an optional error message or Exception.
        Args:
            error (Optional[Union[str, Exception]]): 
                A string representing the error message, or an Exception object for detailed context.
        """
        super().__init__(self.get_message())    
        if isinstance(error, str):
            self.details = error
        elif isinstance(error, Exception):
            self.details = str(error)
        else:
            self.details = None

    @abstractmethod
    def get_message(self) -> str:
        """
        Get the error message for this exception.
        Returns:
            str: The error message to display in the response or logs.
        Note:
            This method must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def get_status_code(self) -> int:
        """
        Get the HTTP status code for this exception.
        Returns:
            int: The HTTP status code representing the error (e.g., 400, 404, 500).
        Note:
            This method must be implemented by subclasses.
        """
        pass

    def handle(self):
        """
        Capture the exception for logging or reporting (e.g., Sentry).
        
        Action:
            Sends the exception details to the configured monitoring tool.
        """
        capture_exception(self)

    def to_response(self) -> JSONResponse:
        """
        Convert the exception into a FastAPI JSONResponse.
        Returns:
            JSONResponse: 
                A JSON response containing the error message and additional details 
                (if available), with the appropriate HTTP status code.
        """
        response_content = {"error": self.get_message()}
        if self.details:
            response_content["details"] = self.details

        return JSONResponse(
            status_code=self.get_status_code(),
            content=response_content,
        )