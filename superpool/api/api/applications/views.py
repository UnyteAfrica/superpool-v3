from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.exceptions import NotAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.exceptions import ApplicationCreationError
from api.services import ApplicationService
from core.models import Application

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
    # authentication_classes = [
    #     TokenAuthentication,
    # ]
    # permission_classes = [
    #     IsAuthenticated,
    # ]

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


class ApplicationViewSetV2(viewsets.ModelViewSet):
    """
    V2 of the application viewset

    Allows merchants to create and manage sandbox and production environments.
    """

    serializer_class = ApplicationSerializer
    http_method_names = ["get", "post"]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated or not hasattr(user, "merchant"):
            raise NotAuthenticated("You must be authenticated to view this resource.")
        return Application.objects.filter(merchant=user.merchant)

    @extend_schema(
        summary="Retrieve all applications for the authenticated merchant",
        description="This endpoint retrieves all sandbox or production applications for the merchant, including the hashed API keys.",
        tags=["Application"],
        responses={
            200: OpenApiResponse(ApplicationSerializer(many=True)),
        },
        examples=[
            OpenApiExample(
                "Success Response Example",
                value=[
                    {
                        "application_id": "f0a2e4b6-33e5-451e-b90d-ea3a3d2a8e3e",
                        "name": "Test Application",
                        "test_mode": True,
                        "api_key_hash": "d9a8f82b123fe6e...",
                    },
                    {
                        "application_id": "a0d3e3a2-42b5-451e-b80d-ea3b3d1c9d3e",
                        "name": "Production Application",
                        "test_mode": False,
                        "api_key_hash": "c8a7f83a8912ce7...",
                    },
                ],
                response_only=True,
                status_codes=["200"],
            )
        ],
    )
    def list(self, request, *args, **kwargs):
        """
        Retrieves all applications for the authenticated merchant
        """
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new application",
        description="This endpoint allows the merchant to create a sandbox or production application. The response includes the application ID, name, mode, and hashed API key.",
        tags=["Application"],
        request=ApplicationSerializer,
        responses={
            201: OpenApiResponse(ApplicationSerializer),
            400: OpenApiResponse(description="Validation errors"),
            500: OpenApiResponse(description="Internal server error"),
        },
        examples=[
            OpenApiExample(
                "Create a new application environment",
                value={
                    "name": "Sandbox Environment",
                    "test_mode": "true",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Success Response Example",
                value={
                    "application_id": "f0a2e4b6-33e5-451e-b90d-ea3a3d2a8e3e",
                    "name": "Sandbox Environent",
                    "api_key_hash": "d9a8f82b123fe6e...",
                    "test_mode": "false",
                },
                response_only=True,
                status_codes=["201"],
            ),
        ],
    )
    def create(self, request: Request) -> Response:
        """
        Create a new environment instance for the authenticated merchant
        """
        # if Application.objects.filter(merchant=self.request.user.merchant).count() >= 2:
        #     raise ValidationError("A merchant can only have a maximum of 2 API keys.")
        return super().create(request)
