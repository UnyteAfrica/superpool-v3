"""
Drop-in notification module for the Superpool platform

This module provides a drop-in notification service for the Policy model.
It provides a notify method that can be used to send notifications to
stakeholders about actions that took place on a policy.

Date created: 2024-07-28 12:32

"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Union

from core.catalog.models import Policy


class INotification(ABC):
    """
    Interface for the Notification service

    Defines the methods that must be implemented by the Notification service
    """

    @classmethod
    @abstractmethod
    def notify(cls, who: str, action: str, policy: "Policy") -> Dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def send(subject: str, message: str, recipient: str) -> None:
        raise NotImplementedError


class NotificationService(INotification):
    ACTION_REGISTRY = {
        "purchase_policy": {
            "merchant": "Policy Purchase Notification - A new policy has been purchased.",
            "customer": "Policy Purchase Successful - We've got your back!. Your policy has been purchased.",
        },
        "accept_policy": {
            "merchant": "Policy Confirmation - A new policy has been accepted.",
            "customer": "Your policy has been accepted.",
        },
        "cancel_policy": {
            "merchant": "Policy Cancellation Notification",
            "customer": "Policy Cancellation Confirmation - Your policy has been cancelled.",
        },
        "status_update": {
            "merchant": "Policy Status Update - A policy status has been updated.",
            "customer": "Policy Status Update - Your policy status has been updated.",
        },
        "renew_policy": {
            "merchant": "Policy Renewal Notification - A policy has been renewed",
            "customer": "Policy Renewal Notification - Your policy has been renewed",
        },
        "claim_policy": {
            "merchant": "Policy Claim Notification - A policy has been claimed",
            "customer": "Policy Claim Notification - Your policy has been claimed",
        },
    }
    """ Registry of actions and their corresponding messages"""

    NOTIFICATION_CHANNEL_REGISTRY = {
        "email": "EmailNotification",
        "sms": "SMSNotification",
        # Unyte might go B2C, or offer self-care portal for merchant's customer WhatsApp notification channel
        # There-fore, push and whatsapp notification channels might be added in the future
        "push": "PushNotification",
        "whatsapp": "WhatsAppNotification",
    }
    """ Registry of notification types and their corresponding classes"""

    @classmethod
    def notify(cls, who: str, action: str, policy: "Policy") -> Dict[str, Any]:
        """
        Notify a stakeholder about an action that took place on this policy

        Arguments:
            who: The stakeholder to notify, either a 'merchant' or a 'customer'
            action: The action that took place on the policy
            policy: The policy instance on which the action took place

        Returns:
            A dictionary with a status message
        """
        pass

    @staticmethod
    def send(subject: str, message: str, recipient: str) -> None:
        """
        Send a notification to the recipient

        Arguments:
            subject: The subject of the notification
            message: The message to send
            recipient: The recipient of the notification
        """
        pass
