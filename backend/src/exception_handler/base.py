from abc import ABC, abstractmethod
from fastapi.responses import JSONResponse
from sentry_sdk import capture_exception
from typing import Optional, Union

class APIException(Exception, ABC):
    """
    Base class for all API exceptions.
    """
    
    
    def __init__(self, detail: Optional[str] = None, status_code: Optional[int] = None):
        """
        Initialize the API exception.

        Args:
            detail (Optional[str], optional): The error message to display in the response or logs. Defaults to None.
            status_code (Optional[int], optional): The HTTP status code representing the error (e.g., 400, 404, 500). Defaults to None.
        """
        self.detail = detail
        self.status_code = status_code
        capture_exception()

    def __str__(self) -> str:
        """
        Get the string representation of the exception.

        Returns:
            str: The string representation of the exception.
        """
        return self.get_message()
    
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

    def capture_exception(self):
        """
        Capture the exception using Sentry.
        """
        capture_exception(self)
    
    def get_response(self) -> JSONResponse:
        """
        Get the JSON response for this exception.

        Returns:
            JSONResponse: The JSON response containing the error message and status code.
        """
        return JSONResponse(content={"detail": self.get_message()}, status_code=self.get_status_code())
