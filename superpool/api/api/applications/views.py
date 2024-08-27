from api.exceptions import ApplicationCreationError
from api.services import ApplicationService
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ApplicationSerializer, CreateApplicationSerializer


def create_application_view(request: Request, *args: dict, **kwargs: dict) -> Response:
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


class ApplicationView(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        operation_id="get_application",
        tags=["Application"],
        description="Retrieve the application instance for the authenticated merchant",
        responses={200: ApplicationSerializer},
    )
    def get(self, request: Request) -> Response:
        """
        Retrieves the instance of the application for the authenticated merchant
        """
        queryset = ApplicationService.get_application()
        try:
            application = ApplicationSerializer(queryset)
        except Exception as err:
            raise err
        return Response(
            data=application.serialized_data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="create_application",
        tags=["Application"],
        description="Create a new application instance for the authenticated merchant",
        request=CreateApplicationSerializer,
        responses={201: CreateApplicationSerializer, 400: ApplicationCreationError},
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Creates a new application instance for the authenticated merchant
        """
        return create_application_view(request, *args, **kwargs)
