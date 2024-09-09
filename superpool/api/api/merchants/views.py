import logging
from typing import Any

from rest_framework.views import APIView

from api.app_auth.authentication import APIKeyAuthentication
from api.merchants.exceptions import MerchantDeactivationError
from api.merchants.serializers import (
    CreateMerchantSerializer,
    MerchantSerializer,
    MerchantSerializerV2,
    MerchantWriteSerializerV2,
    CustomerInformationSerializer,
)
from api.merchants.services import MerchantService
from core.merchants.errors import (
    MerchantAlreadyExists,
    MerchantObjectDoesNotExist,
    MerchantUpdateError,
)
from core.merchants.models import Merchant
from django.http.response import Http404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from core.user.models import Customer

logger = logging.getLogger(__name__)


class MerchantAPIViewsetV2(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Updated vieewsets for handling with merchant data
    """

    queryset = Merchant.objects.all()
    authentication_classes = [APIKeyAuthentication]

    def get_serializer_class(self):
        if self.action in ["create", "update"]:
            return MerchantWriteSerializerV2
        return MerchantSerializerV2

    @extend_schema(
        operation_id="create-new-merchant",
        summary="Register a new merchant on Unyte",
        description="Register a new merchant on the platform",
        tags=["Merchant"],
        responses={
            200: MerchantSerializer,
        },
    )
    def create(self, request, *args, **kwargs):
        """
        This action allows you to register a new merchant
        """
        from core.utils import generate_verification_token, send_verification_email

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as err:
            logger.error(f"Validation error: {err}")
            return Response(err.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Unexpected error: {exc}")
            return Response(
                {"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        self.perform_create(serializer)

        # generate and send a verification email to the merchant
        merchant = serializer.instance

        verification_token = generate_verification_token()
        merchant.verification_token = verification_token

        # import pdb
        #
        # pdb.set_trace()
        try:
            send_verification_email(
                email=merchant.business_email,
                token=verification_token,
                merchant_id=merchant.short_code,
                merchant_name=merchant.name,
            )
        except Exception as email_exc:
            logger.error(
                f"Error sending verification email to this merchant email: {email_exc}"
            )
            return Response(
                {
                    "error": "Merchant created, but sending email verification failed.",
                    "data": serializer.data,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "message": "Merchant successfully created.",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @extend_schema(
        operation_id="retrieve-a-single-merchant",
        tags=["Merchant"],
        summary="Retrieve a merchant instance by its unique short code",
        description="Retrieve a single merchant using its short code",
        responses={
            status.HTTP_200_OK: MerchantSerializer,
            status.HTTP_404_NOT_FOUND: {
                "error": "Merchant with the provided short code not found."
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "error": "An unexpected error occured. Please contact support"
            },
        },
    )
    @action(detail=False, methods=["get"], url_path="(?P<short_code>[^/.]+)")
    def retrieve_by_short_code(self, request, short_code=None):
        """
        This action allows you to retrieve a single merchant by its unique
        short code

        e.g AXA-5G36, WEM-GLE2, etc
        """
        try:
            merchant = get_object_or_404(Merchant, short_code=short_code)
        except Http404:
            logger.error(f"Merchant:{short_code} not found.")
            return Response(
                {"error": "Merchant with the provided short code not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as exc:
            logger.error(
                f"An unexpected error occured while retrieving merchant: {exc}"
            )
            return Response(
                {
                    "error": "An unexpected error occured. Please contact support",
                    "detail": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = self.get_serializer(merchant)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="List all merchants",
    description="Retrieve a list of all merchants on the platform",
    tags=["Merchant"],
    responses={
        status.HTTP_200_OK: OpenApiResponse(MerchantSerializer, "List of merchants"),
        status.HTTP_404_NOT_FOUND: {"error": "No merchants found."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "error": "An unexpected error occured. Please contact support"
        },
    },
)
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

    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    service_class = MerchantService()

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
    def create(self, request: Request, *args: dict, **kwargs: dict) -> Response:
        """
        Register a new merchant
        """
        try:
            merchant = self.service_class.register_merchant(request.data)
            if merchant:
                return Response(
                    {"message": "Merchant registered successfully", "data": merchant},
                    status=status.HTTP_201_CREATED,
                )
        except MerchantAlreadyExists as err:
            return Response(
                {"error": str(err.message)},
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
                    "message": "Internal server error. Please try again later or contact support.",
                    "detail": err,
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
