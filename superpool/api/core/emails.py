from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.translation import gettext as _

_EmailType = str | list[str]


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

        subject = self.get_subject()
        from_email = self.get_from_email()
        to = to
        super().__init__(subject=subject, from_email=from_email, to=to)
        extra_kwargs["headers"]["Reply-To"] = from_email

        self.attach_alternative(self.get_template(), "text/html")

    def get_subject(self) -> str:
        if not self.subject:
            raise NotImplementedError("The email subject attribute must be implemented")
        return self.subject

    def get_template(self) -> str:
        if not self.template:
            raise NotImplementedError("Template attribute must be implemented")
        return self.template

    def get_from_email(self) -> str:
        """
        Retrieves the system's email mailbox
        """
        return settings.FROM_EMAIL

    def send(self, silent: bool = True) -> None:
        """
        Send email message to the user
        """
        from django.db import transaction

        Super = super()
        transaction.on_commit(lambda: Super.send(fail_silently=silent))


class PendingVerificationEmail(BaseEmailMessage):
    """
    Email message class for sending an email to a merchant who has not yet verified their email address.
    """

    template = "superpool/emails/verification.html"

    def __init__(
        self,
        confirm_url: str,
        to: str,
        from_: str,
        *args: dict,
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
        super().__init__(to, from_, **kwargs)

    def get_subject(self) -> str:
        return _("Unyte - Verify your email address")


class OnboardingEmail(BaseEmailMessage):
    """
    Email message class for welcoming a newly verified merchant on he platform.
    """

    template = "superpool/emails/welcome.html"

    def __init__(
        self,
        to: str | None = None,
        from_: str | None = None,
        *args: dict,
        **kwargs: dict,
    ) -> None:
        super().__init__(to, from_, **kwargs)

    def get_subject(self) -> str:
        return _("Unyte - Welcome to the best insure-tech infrastructure!")
