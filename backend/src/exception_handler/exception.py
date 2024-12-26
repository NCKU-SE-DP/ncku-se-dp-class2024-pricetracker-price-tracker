from .base import APIException

class NoResourceFoundException(APIException):
    def get_status_code(self) -> int:
        return 404
    
    def get_message(self) -> str:
        return "No data found"
    
class ArticleNotFoundException(APIException):
    def get_status_code(self) -> int:
        return 404

    def get_message(self) -> str:
        return "Invalid article id, article not found"
    
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
    
class InvalidCredentialsException(APIException):
    def get_status_code(self) -> int:
        return 401

    def get_message(self) -> str:
        return "Invalid credentials"
    
class UserNotFoundException(APIException):
    def get_status_code(self) -> int:
        return 404

    def get_message(self) -> str:
        return "User not found"
    
class UserRegistrationFailedException(APIException):
    def get_status_code(self) -> int:
        return 500

    def get_message(self) -> str:
        return "User registration failed"
    
class UserUpdateFailedException(APIException):
    def get_status_code(self) -> int:
        return 500

    def get_message(self) -> str:
        return "User update failed"
    
class UserDeleteFailedException(APIException):
    def get_status_code(self) -> int:
        return 500

    def get_message(self) -> str:
        return "User delete failed"
    
class UserPasswordChangeFailedException(APIException):
    def get_status_code(self) -> int:
        return 500

    def get_message(self) -> str:
        return "User password change failed"
    
class UserPasswordChangeInvalidException(APIException):
    def get_status_code(self) -> int:
        return 400

    def get_message(self) -> str:
        return "Invalid password change request"
    
class UserPasswordChangeMismatchException(APIException):
    def get_status_code(self) -> int:
        return 400

    def get_message(self) -> str:
        return "Passwords do not match"
    