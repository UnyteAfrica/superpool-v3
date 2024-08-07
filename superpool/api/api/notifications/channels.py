from api.notifications.base import INotification
from django.conf import settings
from django.core.mail import send_mail
from typing import Any, Dict


class EmailNotification(INotification):
    """
    Email Notification service
    """


class SMSNotification(INotification):
    """
    SMS Notification service
    """


class WhatsAppNotification(INotification):
    """
    WhatsApp Notification service
    """
