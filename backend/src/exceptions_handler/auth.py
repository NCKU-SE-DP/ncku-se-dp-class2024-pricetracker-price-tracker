from .base import APIException

class AuthenticationExceptionBase(APIException):
    """
    Base class for authentication-related exceptions.
    """
    def get_status_code(self) -> int:
        return 401

class UnauthorizedException(AuthenticationExceptionBase):
    def get_message(self) -> str:
        return "Authorization Bearer Token not provided"


class TokenExpiredException(AuthenticationExceptionBase):
    def get_message(self) -> str:
        return "Authentication token has expired"


class InvalidTokenException(AuthenticationExceptionBase):
    def get_message(self) -> str:
        return "Invalid authentication token"


class MissingSubTokenException(AuthenticationExceptionBase):
    def get_message(self) -> str:
        return "Missing 'sub' field in token"