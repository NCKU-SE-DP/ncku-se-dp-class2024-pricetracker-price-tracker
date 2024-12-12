class DomainMismatchException(Exception):
    """Exception raised for URLs whose domain does not match the news website's domain."""

    def __init__(
        self,
        url: str,
        message: str = "URL's domain does not match the news website's domain",
    ):
        self.url = url
        self.message = message
        super().__init__(self.message)

class LLMClientInitializeException(Exception):
    """
    Exception raised for errors during the initialization of the LLM client.
    """

    def __init__(
        self,
        message: str = "Failed to initialize the LLM client due to an error",
    ):
        self.message = message
        super().__init__(self.message)