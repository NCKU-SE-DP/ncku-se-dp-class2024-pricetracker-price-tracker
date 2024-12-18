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
        return "Invalid article id, please try another one"

class UnsupportedFeatureException(APIException):
    """
    Generic exception for unsupported features.
    Attributes:
        feature_name (str): The name of the unsupported feature causing the exception.
    """

    def __init__(self, feature_name: str):
        self.feature_name = feature_name
        super().__init__()

    def get_status_code(self) -> int:
        return 400

    def get_message(self) -> str:
        return f"Unsupported feature: {self.feature_name}"

class InvalidAiInputParamException(APIException):
    def get_status_code(self) -> int:
        return 400

    def get_message(self) -> str:
        return "AI summary failed. Please provide a longer or different content"