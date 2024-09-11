"""
This module will contain the shared views (endpoints) for the application.
"""

import logging
from os import stat
import uuid
from django.core.exceptions import MultipleObjectsReturned, ValidationError
from django.core.mail import EmailMessage, EmailMultiAlternatives, send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdminUser
from core.providers.models import Provider
from api.serializers import ProviderSerializer
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiRequest,
    extend_schema,
)
from drf_spectacular.utils import OpenApiResponse
from rest_framework import generics
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.exceptions import NotFound
from django.conf import settings
from django.db.models import Q

from core.emails import (
    OnboardingEmail,
    send_password_reset_email,
    send_password_reset_confirm_email,
)
from core.merchants.models import Merchant
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str, force_str
from .openapi import (
    BASE_URL,
    insurance_provider_search_example,
    insurance_provider_list_example,
)
from .serializers import (
    CompleteRegistrationSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    MerchantForgotCredentialSerializer,
)

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
    def get(self, request, merchant_id, *args, **kwargs):
        """

        Verify the email address of a merchant based on their verification token.

        This endpoint allows merchants to verify their email addresses after account creation.
        It is triggered when the merchant clicks on the verification link sent to their email.

        Args:
            request (HttpRequest): The incoming HTTP request. The request must include a valid
                `token` as a query parameter.
            merchant_id (str): This parameter represents the merchant's unique identifier,
                also referred to as the "short_code" internally. Though renamed to `merchant_id`,
                the underlying functionality remains unchanged. It helps map merchants in the system.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response (JSON): Returns a JSON response indicating success or failure of the email
            verification process.

            Success Response (HTTP 200):
            {
                "message": (
                    "Email verified successfully. Please check your email for onboarding instructions. "
                    "If you do not receive an email, please check your spam folder. If you still do not receive an email, "
                    "please contact support with error code: ONBOARDING_MSG_NOT_RECEIVED."
                )
            }

            Failure Response (HTTP 400):
            {
                "error": "Invalid verification token"
            }

        Key Details for Non-Technical Stakeholders:
        - This API is part of the merchant onboarding process, ensuring that the merchant's
          email is verified before they can fully access the platform.
        - The `merchant_id` in the URL is a placeholder that simplifies the naming convention
          for external users but internally still maps to the original "short_code".
        - The email verification token must be provided by the merchant via the verification link.
        - If the email is successfully verified, the merchant receives onboarding instructions via email.

        Key Details for Developers:
        - The `merchant_id` parameter is simply an alias for `short_code`, preserving
          backward compatibility with existing logic.
        - The token is checked for validity, and if it has expired or is incorrect,
          the request is rejected with a 400 response.
        - Upon successful verification, the merchant's status is updated to verified, and
          the onboarding email is sent. Errors during email dispatch are logged but do not block verification.
        - Ensure the token expiration logic works properly to prevent expired tokens from being reused.

        """
        token = request.GET.get("token")
        short_code = merchant_id  # a place holder to map short code to understandable term: merchant_id

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
                    merchant_name=merchant.name,
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


class MerchantSetPasswordView(APIView):
    """
    API view for completing merchant registration for the Superpool
    dashboard.

    You can use this endpoint to set a new password for a merchant account.
    """

    permission_classes = []

    @extend_schema(
        summary="Complete merchant registration for the Superpool dashboard",
        operation_id="complete-merchant-registration",
        tags=["Auth"],
        request=OpenApiRequest(request=CompleteRegistrationSerializer),
        responses={
            200: OpenApiResponse(description="Password set successfully"),
            400: OpenApiResponse(description="Invalid input"),
            404: OpenApiResponse(description="Merchant not found"),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = CompleteRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                serializer.save()
                return Response(
                    {
                        "status": "success",
                        "message": "Registration completed successfully.",
                    },
                    status=status.HTTP_200_OK,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Auth"],
    summary="Initiate a password reset request",
    request=OpenApiRequest(request=PasswordResetSerializer),
    responses={
        200: OpenApiResponse(
            response={"message": "Password reset email sent successfully"},
            description="Password reset email has been sent to the merchant's email address.",
        ),
        400: OpenApiResponse(
            response={
                "message": "Email cannot be empty. Please provide your email address."
            },
            description="Returned when the request does not contain an email.",
        ),
        404: OpenApiResponse(
            response={"message": "Email not found!"},
            description="Returned when the email does not correspond to any merchant account.",
        ),
    },
)
class PasswordResetView(APIView):
    """
    Handles password reset initiation for merchants.

    Merchants submit their email, and if the email is valid and associated with a merchant,
    the system generates a password reset link with the merchant's `tenant_id` (UUID4) and a reset token.
    """

    permission_classes = []
    serializer_class = PasswordResetSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get("email", None)

        if not email:
            return Response(
                {
                    "message": "Email cannot be empty. Please provide your email address."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            merchant = Merchant.objects.get(business_email__iexact=email)
            # logger.info(f"Merchant information: {merchant}")
            logger.info(f"Merchant Name: {merchant.name}")
            logger.info(f"Merchant Email: {merchant.business_email}")

            token = default_token_generator.make_token(merchant.user)
            encoded_tenant_id = urlsafe_base64_encode(force_bytes(merchant.tenant_id))

            reset_link = (
                f"{BASE_URL}/auth/merchant/reset-password/{encoded_tenant_id}/{token}/"
            )

            try:
                send_password_reset_email(merchant, reset_link)
            except Exception as mail_exc:
                logger.error({"error_type": "MAILER_EXCEPTION", "error": str(mail_exc)})
                return Response(
                    {"message": "Failed to send password reset email"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {"message": "Password reset email sent successfully"},
                status=status.HTTP_200_OK,
            )
        except Merchant.DoesNotExist:
            logger.error(
                "Merchant does not exist - Unable to send password reset email"
            )
            return Response(
                {"message": "Email not found!"}, status=status.HTTP_404_NOT_FOUND
            )


@extend_schema(
    tags=["Auth"],
    summary="Finalize a password reset process",
    request=OpenApiRequest(request=PasswordResetConfirmSerializer),
    responses={},
)
class PasswordResetConfirmView(APIView):
    """
    Handles password reset confirmation for merchants.

    Merchants submit their new password along with the `tenant_id` and reset token.
    The system ensures that the new password is different from the old one and updates the password.
    A confirmation email is sent to the merchant upon successful reset.
    """

    permission_classes = []
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request: Request, tenant_id_b64: str, token: str):
        try:
            # first we decode the incoming encoded tenant id
            tenant_id = uuid.UUID(force_str(urlsafe_base64_decode(tenant_id_b64)))
            merchant = Merchant.objects.get(tenant_id=tenant_id)

            if not default_token_generator.check_token(merchant.user, token):
                return Response(
                    {"message": "Token expired! Please resend reset request"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = PasswordResetConfirmSerializer(data=request.data)

            if serializer.is_valid():
                new_password = serializer.validated_data["new_password"]

                # this new password should never be the same with the current password
                if merchant.user.check_password(new_password):
                    return Response(
                        {
                            "message": "New password cannot be the same as the old password"
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                merchant.user.set_password(new_password)
                merchant.user.save()

                # send email back to the merchant
                send_password_reset_confirm_email(merchant)

                return Response(
                    {"message": "Your password has been successfully updated"},
                    status=status.HTTP_200_OK,
                )
        except Exception as e:
            raise e


@extend_schema(
    summary="Recover Tenant ID for merchant",
    description=(
        "This endpoint allows merchants to recover their Tenant ID by submitting their "
        "registered business email address. If the email is valid and associated with "
        "a merchant, the Tenant ID is sent to the email address. \n"
        "NOTE: At the moment, only customer suport agents, can perform this action on behalf of merchants"
    ),
    tags=["Auth", "Unyte Admin"],
    request=OpenApiRequest(
        {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "Registered business email address of the merchant.",
                }
            },
            "required": ["email"],
        }
    ),
    responses={
        200: OpenApiResponse(
            description="Tenant ID has been sent to the provided email address."
        ),
        400: OpenApiResponse(description="Bad Request: Email is missing or invalid."),
        404: OpenApiResponse(
            description="Not Found: No merchant found with the provided email address."
        ),
        500: OpenApiResponse(
            description="Internal Server Error: Multiple records returned for the email address."
        ),
    },
)
class MerchantForgotTenantIDView(APIView):
    """
    Handles the 'Forget Tenant ID' functionality for merchants.

    This endpoint allows merchants to recover their tenant ID by submitting their
    registered business email. Upon successful validation of the provided email,
    the tenant ID associated with the merchant's account will be emailed to them.

    - Merchants submit a POST request with their email in the request body.
    - If the email exists, an email with the tenant ID is sent to the merchant.
    - If the email is not found or invalid, an appropriate error response is returned.

    ```json
        {
            "email": "<merchant_business_email>"
        }
    ```

    Possible Responses:
    - 200 OK: Tenant ID has been sent to the provided email address.
    - 404 Not Found: No merchant found with the provided email address.
    - 400 Bad Request: Email is missing or invalid.


    IMPORTANT NOTE: Due to security reasons, this action can only be performed on behalf of mechants by user with customer support permissons
    """

    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = MerchantForgotCredentialSerializer(data=request.data)

        if serializer.is_valid():
            merchant_email = serializer.validated_data["email"]
            try:
                merchant = Merchant.objects.get(business_email=merchant_email)

                # we are extracting the messages into variables to enable for change
                email_subject = "Unyte - Tenant ID Recovery!"
                email_body = f"""
                    Dear {merchant.name},

                    We have received your request to recover your Tenant ID associated with your Unyte account.

                    Your Tenant ID is: **{merchant.tenant_id}**

                    Please keep this information safe for future reference. If you have any questions or require further assistance, feel free to reach out to our support team.

                    Best regards,
                    The Unyte Team

                    ---
                    This is an automated message. Please do not reply to this email.
                    """
                send_mail(
                    subject=email_subject,
                    message=email_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[merchant.business_email],
                    fail_silently=True,
                )
                return Response(
                    {"message": "Tenant ID sent successfully to merchant"},
                    status=status.HTTP_200_OK,
                )

            except Merchant.DoesNotExist:
                return Response(
                    {"message": "No merchant found for the provided email address"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            except MultipleObjectsReturned:
                return Response(
                    {
                        "error": "We are experiencing some downtime with this service. Please contact support with error code, MERCHANT_RECOVERY_MULTI_OBJ"
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
