from api.notifications.base import INotification
from django.conf import settings
from django.core.mail import send_mail


class EmailNotification(INotification):
    """
    Email Notification service
    """

    @staticmethod
    def send_message(subject: str, message: str, recipient: str) -> None:
        """
        Sends a message to a recipient via Email
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
        )


class SMSNotification(INotification):
    """
    SMS Notification service
    """

    @staticmethod
    def send_message(subject: str, message: str, recipient: str) -> None:
        """
        Sends a message to a recipient via SMS
        """
        # TODO: In future, we can implement the SMS service
        pass


class WhatsAppNotification(INotification):
    """
    WhatsApp Notification service
    """

    @staticmethod
    def send_message(message: str, recipient: str) -> None:
        """
        Sends a message to a recipient via Whatsapp
        """
        # TODO: In future, we can implement the WhatsApp APIs
        pass
