import logging
from typing import Any

from api.merchants.exceptions import (MerchantDeactivationError,
                                      MerchantNotFound,
                                      MerchantRegistrationError)
from api.merchants.serializers import (CreateMerchantSerializer,
                                       MerchantLimitedSerializer,
                                       MerchantSerializer)
from api.merchants.services import MerchantService
from core.merchants.errors import (MerchantAlreadyExists,
                                   MerchantObjectDoesNotExist,
                                   MerchantUpdateError)
from core.merchants.models import Merchant
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

logger = logging.getLogger(__name__)


class MerchantViewList(ReadOnlyModelViewSet):
    """
    Retrieve list of all merchants on the platform
    """

    queryset = Merchant.objects.all()
    serializer_class = MerchantSerializer


class MerchantViewSet(ViewSet):
    """
    Viewset for Merchant model
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.service_class = MerchantService()

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Register a new merchant",
        description="Register a new merchant on the platform",
        request=CreateMerchantSerializer,
        responses={
            status.HTTP_201_CREATED: {"message": "Merchant registered successfully."},
            status.HTTP_400_BAD_REQUEST: {"error": "Validation error."},
            status.HTTP_409_CONFLICT: {"error": "Merchant already exists."},
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "message": "Internal server error. Please try again later or contact support."
            },
        },
    )
    def create(self, request: Request) -> Response:
        """
        Register a new merchant
        """
        try:
            merchant = self.service_class.register_merchant(request.data)
            return Response(
                {"message": "Merchant registered successfully"},
                status=status.HTTP_201_CREATED,
            )
        except MerchantAlreadyExists as err:
            return Response(
                {"error": str(err)},
                status=status.HTTP_409_CONFLICT,
            )
        except ValidationError as err:
            return Response(
                {"error": err.detail},
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
        summary="Update merchant profile",
        description="Update a merchant's profile",
        request=CreateMerchantSerializer,
        responses={
            status.HTTP_200_OK: MerchantSerializer,
            status.HTTP_404_NOT_FOUND: {"error": "Merchant not found."},
            status.HTTP_400_BAD_REQUEST: {"error": "Validation error."},
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "message": "Internal server error. Please try again later or contact support."
            },
        },
    )
    def update(self, request: Request, pk: Any = None) -> Response:
        """
        Update a merchant's profile
        """
        try:
            merchant = self.service_class.update_merchant(pk, request.data)
            return Response(
                MerchantSerializer(merchant).data, status=status.HTTP_200_OK
            )
        except MerchantObjectDoesNotExist:
            return Response(
                {"error": "Merchant not found."}, status=status.HTTP_404_NOT_FOUND
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
        summary="Retrieve a single merchant",
        description="Retrieve a single merchant",
        responses={
            status.HTTP_200_OK: MerchantSerializer,
            status.HTTP_404_NOT_FOUND: {"error": "Merchant not found."},
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "message": "Internal server error. Please try again later or contact support."
            },
        },
    )
    def retrieve(self, request: Request, pk: Any = None) -> Response:
        """
        Retrieve a single merchant
        """
        try:
            merchant = self.service_class.retrieve_merchant(pk)
            return Response(
                MerchantSerializer(merchant).data, status=status.HTTP_200_OK
            )
        except MerchantObjectDoesNotExist:
            return Response(
                {"error": "Merchant not found."}, status=status.HTTP_404_NOT_FOUND
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
            status.HTTP_204_NO_CONTENT: {
                "message": "Merchant deactivated successfully."
            },
            status.HTTP_404_NOT_FOUND: {"error": "Merchant not found."},
            status.HTTP_400_BAD_REQUEST: {"error": "Deactivation error."},
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "message": "Internal server error. Please try again later or contact support."
            },
        },
    )
    def destroy(self, request: Request, pk: Any = None) -> Response:
        """
        Deactivate a merchant
        """
        try:
            self.service_class.deactivate(pk)
            return Response(
                {"message": "Merchant deactivated successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except MerchantObjectDoesNotExist:
            return Response(
                {"error": "Merchant not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except MerchantDeactivationError as err:
            return Response({"error": str(err)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
            logger.error(f"Unexpected error: {err}")
            return Response(
                {
                    "message": "Internal server error. Please try again later or contact support."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
