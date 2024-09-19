import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .constants import ACTION_REGISTRY

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """
    Interface for notification channels.
    """

    @abstractmethod
    def prepare_message(self, action: str, recipient: str) -> Dict[str, Any]:
        """
        Prepare the message for the recipient.
        """
        pass

    @abstractmethod
    def send(self, recipient: str, subject: str, message: str) -> None:
        """
        Send the message to the recipient.
        """
        pass


class EmailNotification(NotificationChannel):
    """
    Email Notification service
    """

    def prepare_message(
        self, action: str, recipient: str, context: dict = None
    ) -> Dict[str, Any]:
        action_data = ACTION_REGISTRY.get(action, {}).get(recipient, {})
        logger.info(f"Retrieved action_data: {action_data}")

        # no action data?
        if not action_data:
            logger.error(f"Action {action} is not supported")
            return {}

        template_path = action_data.get("template")
        logger.info(f"Template path: {template_path}")

        if context is None:
            context = {}

        if template_path:
            try:
                # render the template with the context if the template path is provided
                subject = action_data.get("subject", "")
                logger.info(f"Retrieved context: {context}")
                body = render_to_string(template_path, context)
            except Exception as e:
                logger.error(f"Template renderng failed: {e}")
                return {}

            # Log after rendering the template
            logger.info("Template rendering was successful")
        else:
            # otherwise, use the default subject and message
            subject = action_data.get("subject", "")
            body = action_data.get("body", "")

            logger.info(f"Using default subject and body: {subject}, {body}")

        if not subject or not body:
            logger.error(
                f"Action {action} is not supported is not supported for {recipient}"
            )
            return {}

        return {
            "subject": subject,
            "body": body,
        }

    def send(self, recipient: str, subject: str, message: str) -> None:
        """
        Send the email message to the recipient
        """
        logger.info(f"Preparing to send email to {recipient} with subject: {subject}")

        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient],
            )
            email.attach_alternative(message, "text/html")
            email.send(fail_silently=False)
            logger.info(f"Email sent to {recipient} with subject: {subject}")
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")


class SMSNotification(NotificationChannel):
    """
    SMS Notification service
    """

    def send(self, recipient: str, subject: str, message: str) -> None:
        """
        Send the SMS message to the recipient
        """
        print(
            f"Sending SMS to {recipient} with subject: {subject} and message: {message}"
        )
        pass


class WhatsAppNotification(NotificationChannel):
    """
    WhatsApp Notification service
    """
