import logging
from typing import Any

from api.merchants.exceptions import (
    MerchantDeactivationError,
    MerchantNotFound,
    MerchantRegistrationError,
)
from api.merchants.serializers import (
    CreateMerchantSerializer,
    MerchantLimitedSerializer,
)
from api.merchants.services import MerchantService
from core.merchants.errors import MerchantAlreadyExists, MerchantUpdateError
from core.merchants.models import Merchant
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

logger = logging.getLogger(__name__)


class MerchantViewList(ReadOnlyModelViewSet):
    """
    Retrieve list of all merchants on the platform
    """

    queryset = Merchant.objects.all()
    serializer_class = MerchantLimitedSerializer
    permission_classes = [IsAuthenticated]


class MerchantViewset(ViewSet):
    """
    Viewset for Merchant model
    """

    service = MerchantService()

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Register a new merchant",
        description="Register a new merchant on the platform",
        request=CreateMerchantSerializer,
        responses={
            status.HTTP_201_CREATED: {"message": "Merchant registered successfully."},
            status.HTTP_400_BAD_REQUEST: {"error": "It seems you fucked up!"},
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "message": "Internal server error. It appears, we are experiencing an outage. Please try again later or reach out to support team."
            },
        },
    )
    @action(detail=False, methods=["POST"], permission_classes=[AllowAny])
    def register_merchant(self, request: Request) -> Response:
        """
        Register a new merchant
        """
        try:
            merchant, response_data = self.service.register(request.data)
            if merchant:
                return Response(
                    {
                        "message": "Merchant registered successfully",
                        "data": response_data,
                    },
                    status=status.HTTP_201_CREATED,
                )
        except MerchantRegistrationError as err:
            logger.error(err.message)
            return Response(
                {
                    "error": err.message,
                    "details": err.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except MerchantAlreadyExists as err:
            return Response(
                {
                    "error": err.message,
                },
                status=status.HTTP_409_CONFLICT,
            )
        # Catch all exceptions
        return Response(
            {
                "message": f"Internal server error. It appears, we are experiencing an outage. \n"
                "Please try again later or reach out to support team."
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @extend_schema(
        summary="Update merchant profile",
        description="Update a merchant's profile",
        request=CreateMerchantSerializer,
    )
    @action(detail=True, methods=["PUT"])
    def update_merchant(self, request: Request, pk: Any = None):
        """
        Update a merchant's profile
        """
        try:
            merchant = self.service.update_profile(pk, request.data)
            return Response({"message": "Merchant details updated successfully"})
        except MerchantNotFound:
            return Response(
                {"error": MerchantNotFound.message}, status=status.HTTP_404_NOT_FOUND
            )
        except MerchantUpdateError as err:
            return Response(
                {"error": err.message, "details": err.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as err:
            logger.error(f"Unexpected error: {err}")
            return Response(
                {
                    "message": "Internal server error. Please try again later or contact support."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="Deactivate a merchant",
        description="Deactivate a merchant",
        responses={
            status.HTTP_200_OK: {"message": "Merchant deactivated successfully"},
            status.HTTP_404_NOT_FOUND: {"error": "Merchant not found"},
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "message": "Internal server error. Please try again later or contact support."
            },
        },
    )
    @action(detail=False, methods=["POST"])
    def deactivate_merchant(self, request: Request, pk: Any = None) -> Response:
        """
        Deactivate a merchant
        """
        try:
            self.service.deactivate(pk)
            return Response({"message": "Merchant deactivated successfully"})
        except MerchantNotFound:
            return Response(
                {"error": MerchantNotFound.message}, status=status.HTTP_404_NOT_FOUND
            )
        except MerchantDeactivationError as err:
            return Response({"error": err.message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
            logger.error(f"Unexpected error: {err}")
            return Response(
                {
                    "message": "Internal server error. Please try again later or contact support."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
