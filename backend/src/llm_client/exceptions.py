class LLMClientInitializeException(Exception):
    """
    Raised when the LLM client fails to initialize.
    """
    def __init__(self, message: str):
        super().__init__(message)


class EvaluationFailure(Exception):
    """
    Raised when the evaluation process fails.
    """
    def __init__(self, message: str):
        super().__init__(message)
