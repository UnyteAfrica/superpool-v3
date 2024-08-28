"""
This module will contain the shared views (endpoints) for the application.
"""

import logging
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdminUser
from core.providers.models import Provider
from api.serializers import ProviderSerializer
from drf_spectacular.utils import OpenApiParameter, OpenApiRequest, extend_schema
from drf_spectacular.utils import OpenApiResponse
from rest_framework import generics
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.exceptions import NotFound
from django.db.models import Q

from core.emails import OnboardingEmail
from core.merchants.models import Merchant
from django.utils import timezone
from .openapi import insurance_provider_search_example, insurance_provider_list_example

logger = logging.getLogger(__name__)


class VerificationAPIView(APIView):
    """
    API view for email verification
    """

    @extend_schema(
        summary="Verify merchant email",
        operation_id="verify-merchant-email",
        tags=["Merchant"],
        parameters=[
            OpenApiParameter(
                name="token",
                type=str,
                location=OpenApiParameter.QUERY,
                description="The verification token sent to the merchant's email",
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Merchant email successfully verified",
            ),
            400: OpenApiResponse(description="Invalid verification token"),
        },
    )
    def get(self, request, short_code, *args, **kwargs):
        """
        Verify the email address of the merchant
        """
        token = request.GET.get("token")

        if not token:
            return Response(
                {"error": _("Invalid verification token")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        merchant = get_object_or_404(Merchant, token=token, short_code=short_code)

        # upgrade merchant status to verified
        if merchant.token == token and merchant.token_expires_at >= timezone.now():
            merchant.verified = True
            merchant.is_active = True

            merchant.clear_token()
            merchant.save()

            # send onboarding email
            try:
                onboarding_email = OnboardingEmail(
                    to=merchant.business_email,
                    tenant_id=str(merchant.tenant_id),
                    merchant_short_code=merchant.short_code,
                )
                onboarding_email.send()
            except Exception as e:
                logger.error(
                    f"Failed to send onboarding email to {merchant.business_email}: {str(e)}"
                )
                pass

            return Response(
                {
                    "message": (
                        "Email verified successfully. Please check your email for onboarding instructions. "
                        "If you do not receive an email, please check your spam folder. If you still do not receive an email, "
                        "please contact support with error code: ONBOARDING_MSG_NOT_RECEIVED."
                    )
                },
                status=status.HTTP_200_OK,
            )
        # token expired
        else:
            return Response(
                {"error": _("Invalid verification token")},
                status=status.HTTP_400_BAD_REQUEST,
            )


class InsurerAPIView(APIView):
    # permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        return Provider.objects.all()

    @extend_schema(
        summary="List all insurance providers",
        operation_id="list-insurance-providers",
        tags=["Insurance Providers"],
        responses={
            200: OpenApiResponse(
                ProviderSerializer,
                "List of insurance providers",
                examples=[
                    insurance_provider_list_example,
                ],
            ),
            404: OpenApiResponse(description="No insurance providers found"),
            500: OpenApiResponse(
                description="An error occurred while fetching the insurance providers"
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        """
        List all insurance providers registered on the platform
        """

        try:
            providers_qs = self.get_queryset()

            # if there are no insurance providers
            if not providers_qs.exists():
                return Response(
                    {"error": _("No insurance providers found")},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = ProviderSerializer(providers_qs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Failed to fetch insurance providers: {str(e)}")
            return Response(
                {
                    "error": _(
                        "An error occurred while fetching the insurance providers"
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    summary="View details about a specific insurance provider",
    operation_id="get-insurance-provider",
    description="Returns a detailed object containing information about the specified insurance provider.",
    responses={
        200: OpenApiResponse(ProviderSerializer, "Details of the insurance provider"),
        404: OpenApiResponse(
            description="The specified insurance provider does not exist"
        ),
        500: OpenApiResponse(
            description="An error occurred while fetching the insurance provider"
        ),
    },
    tags=["Insurance Providers"],
)
class InsuranceProviderDetailView(generics.RetrieveAPIView):
    """
    Retrieve a specific insurance provider
    """

    # permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Provider.objects.all()
    serializer_class = ProviderSerializer
    lookup_field = "name"
    lookup_url_kwarg = "name"

    def get(self, request, *args, **kwargs):
        """
        Retrieve the details of a specific insurance provider
        """

        provider_name = kwargs.get(self.lookup_url_kwarg)

        if not provider_name:
            return Response(
                {"error": _("No insurance name specified in the request.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            provider = self.queryset.filter(name__iexact=provider_name).first()

            if not provider:
                return Response(
                    {"error": _("The specified insurance provider does not exist.")},
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = self.get_serializer(provider)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Failed to fetch insurance provider: {str(e)}")
            ERR_CODE = "INSURANCE_PROVIDER_FETCH_ERROR"
            return Response(
                {
                    "error": _(
                        f"An error occurred while fetching the insurance provider. "
                        f"Please contact support. Error code: {ERR_CODE}"
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InsuranceProviderSearchView(APIView):
    """
    Search for insurance providers
    """

    # permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Provider.objects.all()
    serializer_class = ProviderSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self) -> Provider:
        """
        Filter the queryset based on the search query

        Filters providers by name using an exact or partial match.
        Returns all providers if no search term is provided.
        """

        provider_name = self.request.query_params.get("name", "").strip()
        if provider_name:
            return self.queryset.filter(
                Q(name__icontains=provider_name) | Q(name__iexact=provider_name)
            )
        return self.queryset

    @extend_schema(
        summary="Search for insurance providers",
        operation_id="search-insurance-providers",
        description="Search for insurance providers by name.",
        parameters=[
            OpenApiParameter(
                name="name",
                type=str,
                location=OpenApiParameter.QUERY,
                description="The name of the insurance provider",
            ),
            OpenApiParameter(
                name="limit",
                type=int,
                location=OpenApiParameter.QUERY,
                description="The number of results to return per page",
            ),
            OpenApiParameter(
                name="offset",
                type=int,
                location=OpenApiParameter.QUERY,
                description="The starting position of results to return",
            ),
        ],
        tags=["Insurance Providers"],
        responses={
            200: OpenApiResponse(
                ProviderSerializer,
                "List of insurance providers",
                examples=[insurance_provider_search_example],
            ),
            400: OpenApiResponse(description="Invalid input"),
            404: OpenApiResponse(
                description="No insurance providers matching the search term"
            ),
            500: OpenApiResponse(
                description="An error occurred while fetching the insurance providers"
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        """
        List insurance providers based on the search query

        Exact match returns a single result, otherwise paginated partial matches are returned.
        """

        provider_name = request.query_params.get("name", "").strip()

        if provider_name == "":
            return Response(
                {"error": _("Search query cannot be empty.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        providers_qs = self.get_queryset()

        if not providers_qs.exists():
            return Response(
                {"error": _("No insurance providers matching the search term.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(providers_qs, request)

        if page is not None:
            serializer = ProviderSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # fallback to returning all providers if pagination fails
        serializer = ProviderSerializer(providers_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
