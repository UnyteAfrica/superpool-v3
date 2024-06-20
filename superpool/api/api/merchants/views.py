from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from .serializers import CreateApplicationSerializer
from .services import ApplicationService


@extend_schema(
    operation_id="create_application",
    description="Create a new application instance for a given merchant. Application allows a sandboxed environment when using the API.",
    request=CreateApplicationSerializer,
    responses={201: CreateApplicationSerializer},
)
@api_view(["POST"])
def create_application_view(request: Request) -> Response:
    """
    Create a new application instance for a given merchant
    """
    serializer = CreateApplicationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payload = ApplicationService.create_application(serializer.validated_data)
    return Response(
        data=payload,
        status=status.HTTP_201_CREATED,
    )
