class BaseException(Exception):
    """
    Base class for platform-specific exceptions
    """

    def __init__(
        self, message: str | None = None, code: str | int | None = None
    ) -> None:
        if code:
            self.code = code
        self.message = message

    def __new__(cls) -> BaseException:
        return super().__new__(self.message, self.code)
