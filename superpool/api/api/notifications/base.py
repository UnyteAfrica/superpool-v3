"""
Drop-in notification module for the Superpool platform

This module provides a drop-in notification service for the Policy model.
It provides a notify method that can be used to send notifications to
stakeholders about actions that took place on a policy.

Date created: 2024-07-28 12:32

"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Union

import logging

from core.catalog.models import Policy

logger = logging.getLogger(__name__)


class INotification(ABC):
    """
    Interface for the Notification service

    Defines the methods that must be implemented by the Notification service
    """

    @abstractmethod
    def prepare_message(self, action: str, recipient: str) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def send(self, recipient: str, subject: str, message: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def stream_through(self, channel: str) -> None:
        raise NotImplementedError


class NotificationService(INotification):
    """
    Generic Notification Service
    """

    from .channels import EmailNotification, SMSNotification, WhatsAppNotification

    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"

    NOTIFICATION_CHANNEL_REGISTRY = {
        # Unyte might go B2C, or offer self-care portal for merchant's customer WhatsApp notification channel
        # There-fore, push and whatsapp notification channels might be added in the future
        EMAIL: EmailNotification,
        SMS: SMSNotification,
        WHATSAPP: WhatsAppNotification,
    }
    """ Registry of notification types and their corresponding classes"""

    def __init__(self):
        # Initialize the channel instance to None
        self.channel = None

    def prepare_message(self, action: str, recipient: str) -> Dict[str, Any]:
        """
        Prepare the message to be sent to the recipient
        """
        if not self.channel:
            raise Exception("Notification channel not set. Cannot prepare message \n")
        return self.channel.prepare_message(action, recipient)

    def stream_through(self, channel: str) -> None:
        """
        Stream the message through the specified channel
        """
        if not channel:
            logger.error("No notification channel specified")
            return
        channel_class = self.NOTIFICATION_CHANNEL_REGISTRY.get(channel)
        if not channel_class:
            logger.error(f"Notification channel {channel} is not supported")
            raise ValueError(f"Notification channel {channel} is not supported")

        self.channel = channel_class()

    def send(self, recipient: str, subject: str, message: str) -> None:
        """
        Send the message to the recipient
        """
        if not self.channel:
            logger.error(
                "Notification channel not set. Cannot send message \n"
                "Call stream_through method to set the notification channel first"
            )
            raise Exception("Notification channel not set. Cannot send message")
        self.channel.send(recipient, subject, message)
        print(
            f"Sending message to {recipient} with subject: {subject} and message: {message}"
        )
        logger.info(
            f"Message sent to {recipient} through {self.channel.__class__.__name__}"
        )
