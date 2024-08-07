from api.notifications.base import INotification
from django.conf import settings
from django.core.mail import send_mail
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class EmailNotification(INotification):
    """
    Email Notification service
    """

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


class SMSNotification(INotification):
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


class WhatsAppNotification(INotification):
    """
    WhatsApp Notification service
    """
