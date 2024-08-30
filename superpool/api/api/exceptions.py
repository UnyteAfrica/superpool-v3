class ApplicationCreationError(Exception):
    """
    An error occurred while creating the application
    """

    message = "An error occurred while creating the application"

    def __init__(self, message: str, error: Exception) -> None:
        self.message = message
        self.error = error
        super().__init__(self.message)
