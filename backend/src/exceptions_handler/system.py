from .base import APIException
from typing import Optional, Union
from sentry_sdk import capture_exception

class InternalServerErrorException(APIException):
    """
    Exception for unexpected internal server errors.
    """

    def __init__(self, error: Optional[Union[str, Exception]] = None):
        super().__init__()
        self.error = error

    def get_status_code(self) -> int:
        return 500

    def get_message(self) -> str:
        return "An unexpected server error occurred internally. Please try again later."

    def handle(self):
        if self.error:
            capture_exception(self)