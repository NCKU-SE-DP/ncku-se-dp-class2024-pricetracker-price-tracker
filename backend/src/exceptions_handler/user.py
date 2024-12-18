from .base import APIException
from abc import abstractmethod

class UserExceptionBase(APIException):
    """
    Base class for user-related exceptions.
    Attributes:
        username (str): The username associated with the exception.
    """
    def __init__(self, username: str):
        self.username = username
        super().__init__()

    def get_status_code(self) -> int:
        return 400 

class UserNotFoundException(UserExceptionBase):
    """
    Exception for a user not being found.
    """
    def get_message(self) -> str:
        return f"User '{self.username}' not found"

class UserAlreadyExistsException(UserExceptionBase):
    """
    Exception for a user already existing.
    """
    def get_message(self) -> str:
        return f"User '{self.username}' already exists"

class IncorrectPasswordException(UserExceptionBase):
    """
    Exception for an incorrect password.
    """
    def get_message(self) -> str:
        return f"Incorrect password for user '{self.username}'"

class InputValidationExceptionBase(APIException):
    """
    Base class for input validation-related exceptions.
    """

    @abstractmethod
    def get_field(self) -> str:
        """
        Get the name of the field that failed validation.
        Returns:
            str: The name of the invalid field.
        Note:
            This method must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def get_reason(self) -> str:
        """
        Get the reason for validation failure.
        Returns:
            str: The reason for the validation failure.
        Note:
            This method must be implemented by subclasses.
        """
        pass

    def get_message(self) -> str:
        return f"Invalid input for field '{self.get_field()}': {self.get_reason()}"

    def get_status_code(self) -> int:
        return 400

class InvalidUsernameSizeException(InputValidationExceptionBase):
    """
    Exception for invalid username length.
    """

    def __init__(self, maximum_username_size: int):
        self.maximum_username_size = maximum_username_size
        super().__init__()

    def get_field(self) -> str:
        return "username"

    def get_reason(self) -> str:
        return f"Username too long (maximum {self.maximum_username_size} characters)"

class InvalidPasswordSizeException(InputValidationExceptionBase):
    """
    Exception for invalid password length.
    """

    def __init__(self, maximum_password_size: int):
        self.maximum_password_size = maximum_password_size
        super().__init__()

    def get_field(self) -> str:
        return "password"

    def get_reason(self) -> str:
        return f"Password too long (maximum {self.maximum_password_size} characters)"