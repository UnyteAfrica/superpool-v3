from typing import Any, Union

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.utils.html import strip_tags

from core.merchants.models import Merchant

_EmailType = Union[str, list[str]]


class BaseEmailMessage(EmailMultiAlternatives):
    """
    Base class that can be used to create reusable email message classes.

    This class is not meant to be used directly, but to be subclassed by
    more specific email message classes in respective applications.

    - Provides the `template` attribute that can be used to specify the
      template to be used for rendering the email message.
    - Provides the `subject` attribute that can be used to specify the title of the email message.

     Example:
        class TestEmail(BaseEmailMessage):
            subject = 'Example subject'
            template_name = 'superpool/backend/example.html'

        email = TestEmail(['test@localhost'])
        email.send()

    """

    subject: str | None = None
    template: str | None = None

    def __init__(
        self, to: _EmailType, from_email: _EmailType, **extra_kwargs: dict[str, Any]
    ) -> None:
        """
        Initializes the email message instance.

        Args:
            to: A list of email addresses to send the email to.
            from_email: The email address to send the email from.
            extra_kwargs: Additional keyword arguments to pass to the parent class.
        """

        self.from_email = from_email or self.get_from_email()
        subject = self.get_subject()
        to = self._ensure_list(to)
        super().__init__(subject=subject, from_email=from_email, to=to)

        if "headers" not in extra_kwargs:
            extra_kwargs["headers"] = {}
        extra_kwargs["headers"]["Reply-To"] = self.from_email

        context = extra_kwargs.pop("context", {})
        html_content = self.render_template(context)

        self.attach_alternative(html_content, "text/html")
        self.body = strip_tags(html_content)

        # Set any other additional attributes
        if extra_kwargs:
            for key, val in extra_kwargs.items():
                setattr(self, key, val)

    def _ensure_list(self, emails: _EmailType) -> list[str]:
        if isinstance(emails, str):
            return [emails]
        return emails

    def get_subject(self) -> str:
        if not self.subject:
            raise NotImplementedError("The email subject attribute must be implemented")
        return self.subject

    def get_template(self) -> str:
        if not self.template:
            raise NotImplementedError("Template attribute must be implemented")
        return self.template

    def render_template(self, context: dict) -> str:
        return render_to_string(self.get_template(), context)

    def get_from_email(self) -> str:
        """
        Retrieves the system's email mailbox
        """
        return settings.DEFAULT_FROM_EMAIL

    def send(self, silent: bool = True) -> None:
        """
        Send email message to the user
        """
        super().send(fail_silently=False)


class PendingVerificationEmail(BaseEmailMessage):
    """
    Email message class for sending an email to a merchant who has not yet verified their email address.
    """

    template = "superpool/emails/verification_emailV2.html"

    def __init__(
        self,
        confirm_url: str,
        token: str,
        to: str,
        from_: str | None = None,
        merchant_name: str | None = None,
        **kwargs: dict,
    ) -> None:
        """
        Initializes the email message instance.

        Argments:
            confirm_url: The URL to the email verification page.
            *args: Additional positional arguments to pass to the parent class.
            **kwargs: Additional keyword arguments to pass to the parent class.

        """
        self.confirm_url = confirm_url
        self.token = token

        context = {
            "confirm_url": self.confirm_url,
            "token": self.token,
            "merchant_name": merchant_name,
        }

        super().__init__(to, from_email=from_, context=context, **kwargs)

    def get_subject(self) -> str:
        return _("Unyte - Verify your email address")


class OnboardingEmail(BaseEmailMessage):
    """
    Email message class for welcoming a newly verified merchant on he platform.
    """

    template = "superpool/emails/superpool-merchant-onboarding.html"

    def __init__(
        self,
        to: str | list[str],
        tenant_id: str,
        merchant_short_code: str,
        from_: str | None = None,
        merchant_name: str | None = None,
        **kwargs: dict,
    ) -> None:
        context = {
            "tenant_id": tenant_id,
            "merchant_short_code": merchant_short_code,
            "merchant_name": merchant_name,
        }
        super().__init__(to, from_email=from_, context=context)

    def get_subject(self) -> str:
        return _("Unyte - Welcome to the best insure-tech infrastructure!")


def send_password_reset_email(
    merchant: Merchant, reset_link: str | None = None
) -> None:
    """
    Sends an email to a merchant with a reset URL and a generated token
    """

    subject = "Action Required - Reset Your Password!"
    merchant_email = merchant.business_email
    merchant_name = merchant.name

    context = {"merchant_name": merchant_name, "reset_link": reset_link}
    html_content = render_to_string(
        "superpool/emails/superpool-reset-password.html", context
    )

    reset_email = EmailMultiAlternatives(
        subject=subject,
        body="Please use the following link to reset your password.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[merchant_email],
    )
    reset_email.attach_alternative(html_content, "text/html")
    reset_email.send()


def send_password_reset_confirm_email(merchant: Merchant) -> None:
    merchant_name = merchant.name
    merchant_email = merchant.business_email
    subject = "Password changed"

    context = {"merchant_name": merchant_name, "merchant_email": merchant_email}
    html_content = render_to_string(
        "superpool/emails/superpool-reset-password-confirmation-notification.html",
        context,
    )
    reset_confirmation_email = EmailMultiAlternatives(
        subject=subject,
        body="our password has been successfully updated.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[merchant_email],
    )
    reset_confirmation_email.attach_alternative(html_content, "text/html")
    reset_confirmation_email.send()
