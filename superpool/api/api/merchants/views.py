from rest_framework.decorators import action
from rest_framework.response import Response


@action(methods=["POST"], detail=False, url_path="create-application")
def create_application_view() -> Response:
    """
    Create a new application instance for a given merchant
    """

    return Response()

