from abc import abstractmethod, ABC
from api.notifications.base import INotification
from django.conf import settings
from django.core.mail import send_mail
from typing import Any, Dict
from django.template.loader import render_to_string
import logging
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
        print(
            f"Sending email to {recipient} with subject: {subject} and message: {message}"
        )
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [recipient],
                fail_silently=False,
            )
            logger.info(f"Email sent to {recipient} with subject: {subject}")
        except Exception as e:
            print(f"Failed to send email to {recipient}")
            logger.error(f"An error occurred while sending message: \n{e}")


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
