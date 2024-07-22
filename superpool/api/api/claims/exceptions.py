from rest_framework.exceptions import APIException


class NotFound(APIException):
    status_code = 404

    def __init__(self, detail: str, code: str | None) -> None:
        super().__init__(detail, code)
