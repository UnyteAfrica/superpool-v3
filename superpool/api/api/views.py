"""
This module will contain the shared views (endpoints) for the application.
"""

import logging
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

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
