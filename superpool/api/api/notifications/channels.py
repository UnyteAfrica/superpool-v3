from api.notifications.base import INotification
from django.conf import settings
from django.core.mail import send_mail
from typing import Any, Dict


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
        pass


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
