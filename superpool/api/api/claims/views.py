import uuid
from django.http import Http404
from core.claims.models import Claim
from django.core.exceptions import ValidationError
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiRequest,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from .exceptions import NotFound
from .serializers import (
    ClaimRequestSerializer,
    ClaimSerializer,
    ClaimResponseSerializer,
    ClaimUpdateSerializer,
)
from .services import ClaimService
import logging
from .openapi import (
    full_claim_request_payload_example,
    minimal_request_payload_example,
    claim_request_payload_example,
    single_claim_response_example,
)
from core.permissions import IsMerchant, IsMerchantOrSupport
from api.app_auth.authentication import APIKeyAuthentication

logger = logging.getLogger(__name__)


class ClaimsViewSet(viewsets.ViewSet):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsMerchantOrSupport, IsMerchant]

    def get_service(self):
        """
        Returns the instance of our Claims Service
        """
        return ClaimService()

    def get_serializer_class(self):
        if self.action == "create":
            return ClaimRequestSerializer
        elif self.action == "update":
            return ClaimUpdateSerializer
        else:
            return ClaimSerializer

    @extend_schema(
        summary="View all claims made by your customers",
        parameters=[
            OpenApiParameter(
                name="customer_email",
                required=False,
                type=OpenApiTypes.EMAIL,
            ),
            OpenApiParameter(
                name="first_name",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="last_name",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="phone_number",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="claim_type",
                description="",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="claim_owner",
                description="",
                required=False,
                type=OpenApiTypes.STR,
            ),
        ],
    )
    def list(self, request):
        """
        Retrieve a list of claims based on query parameters.
        """
        query_params = request.query_params.dict()
        service = self.get_service()
        try:
            claims = service.get_claims(query_params)

            # we want to, paginate the resulting queryset
            paginator = LimitOffsetPagination()
            page = paginator.paginate_queryset(claims, request)

            if page is not None:
                serializer = ClaimSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = ClaimSerializer(claims, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Retrieve a claim by its ID or Reference Number",
        responses={
            200: OpenApiResponse(
                response=ClaimSerializer,
                examples=[single_claim_response_example],
            ),
            400: OpenApiResponse(
                response={"error": "ERR_MESSAGE"},
                description="Bad Request",
            ),
            500: OpenApiResponse(
                description="Internal Server Error",
            ),
        },
    )
    def retrieve(self, request, pk=None):
        """
        Retrieve a single claim by its unique ID or claim reference number
        """

        # validate claim id is always present
        if not pk:
            return Response(
                {"error": "Claim ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # We don't want malicious uuid sent in here
        try:
            uuid.UUID(pk)
        except ValueError:
            return Response(
                {"error": "Invalid UUID format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = self.get_service()
        try:
            claim = service.get_claim(claim_id=pk)
        except Claim.DoesNotExist:
            return Response(
                {"error": "Claim not found"}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = ClaimSerializer(claim)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="submit_claim",
        summary="Submit a claim",
        description="Submits a new claim entry on behalf of a customer",
        request=OpenApiRequest(
            request=ClaimRequestSerializer,
            examples=[
                claim_request_payload_example,
                minimal_request_payload_example,
                full_claim_request_payload_example,
            ],
        ),
        responses={
            200: OpenApiResponse(
                description="Claim submitted successfully",
                response=ClaimResponseSerializer,
            )
        },
    )
    def create(self, request, *args, **kwargs):
        """
        Endpoint to submit a new claim
        """
        service = self.get_service()
        serializer = ClaimRequestSerializer(data=request.data)

        if serializer.is_valid():
            try:
                claim = service.submit_claim(serializer.validated_data)
                response_serializer = ClaimResponseSerializer(claim)

                response_data = {
                    "status": "success",
                    "message": "Claim submitted successfully. Note: Witness creation and authority report are not implemented yet, but will be available soon.",
                    "data": response_serializer.data,
                }
                return Response(response_data, status=status.HTTP_201_CREATED)
            except ValidationError as err:
                return Response(
                    {"error": str(err)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as exc:
                return Response(
                    {"error": str(exc)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Update the details of a previously filed claim by a cutstomer",
        parameters=[
            OpenApiParameter(
                name="claim_number",
                description="Claim Reference Number issued by the Insurance provider to help manage/track claim object",
            ),
        ],
        responses={200: ClaimSerializer},
    )
    def update(self, request, pk=None):
        """
        Endpoint to update an existing filed claim
        """
        # validate claim id is always present
        if not pk:
            return Response(
                {"error": "Claim ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # We don't want malicious uuid sent in here
        try:
            uuid.UUID(pk)
        except ValueError:
            return Response(
                {"error": "Invalid UUID format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = self.get_service()
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, partial=True)
        try:
            instance = service.get_claim(claim_id=pk)
        except Claim.DoesNotExist:
            return Response(
                {"error": "Claim not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = ClaimUpdateSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            updated_claim = serializer.save()
            response_serializer = ClaimSerializer(updated_claim)
            return Response(
                {
                    "status": "success",
                    "message": "Claim updated successfully.",
                    "data": response_serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
