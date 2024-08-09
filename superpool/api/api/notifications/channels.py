from abc import abstractmethod, ABC
from api.notifications.base import INotification
from django.conf import settings
from django.core.mail import send_mail
from typing import Any, Dict
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

    def prepare_message(self, action: str, recipient: str) -> Dict[str, Any]:
        message = ACTION_REGISTRY.get(action, {}).get(recipient, {})
        if not message:
            logger.error(f"Action {action} is not supported")
            return {}
        return message

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
