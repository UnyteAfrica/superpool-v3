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

from core.emails import OnboardingEmail
from core.merchants.models import Merchant
from django.utils import timezone

logger = logging.getLogger(__name__)


class VerificationAPIView(APIView):
    """
    API view for email verification
    """

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
                    "message": _(
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
        responses={
            200: OpenApiResponse(ProviderSerializer, "List of insurance providers"),
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
)
class InsuranceProviderDetailView(generics.RetrieveAPIView):
    """
    Retrieve a specific insurance provider
    """

    # permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Provider.objects.all()
    serializer_class = ProviderSerializer
    lookup_field = "id"
    lookup_url_kwarg = "provider_id"

    def get(self, request, *args, **kwargs):
        """
        Retrieve the details of a specific insurance provider
        """
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return self.queryset


@extend_schema(
    summary="Search for insurance providers",
    description="Search for insurance providers by name.",
    parameters=[
        OpenApiParameter(
            name="name",
            type=str,
            location=OpenApiParameter.QUERY,
            description="The name of the insurance provider",
        )
    ],
    responses={
        200: OpenApiResponse(ProviderSerializer, "List of insurance providers"),
        400: OpenApiResponse(description="Invalid input"),
        404: OpenApiResponse(description="No insurance providers found"),
        500: OpenApiResponse(
            description="An error occurred while fetching the insurance providers"
        ),
    },
)
class InsuranceProviderSearchView(generics.ListAPIView):
    """
    Search for insurance providers
    """

    # permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Provider.objects.all()
    serializer_class = ProviderSerializer

    def get_queryset(self):
        provider_name = self.request.query_params.get("name", "").strip()

        # if no provider name is provided, return all providers
        if not provider_name:
            return self.queryset

        # we want to handle input sensitization to prevent SQL injection
        # and other issues
        if not self.validate_search_query(provider_name):
            return ValidationError("Invalid search query")
        return Provider.objects.filter(name__icontains=provider_name)

    def validate_search_query(self, query: str) -> bool:
        """
        Validate the search query for invalid characters and invalid types
        """
        return all(char.isalnum() or char.isspace() for char in query)
