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
        """
        Prepare the message to be sent to the recipient
        """
        raise NotImplementedError


class NotificationService(INotification):
    """
    Generic Notification Service
    """

    from .channels import EmailNotification, SMSNotification, WhatsAppNotification

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
        # Unyte might go B2C, or offer self-care portal for merchant's customer WhatsApp notification channel
        # There-fore, push and whatsapp notification channels might be added in the future
        "email": EmailNotification,
        "sms": SMSNotification,
        "whatsapp": WhatsAppNotification,
    }
    """ Registry of notification types and their corresponding classes"""

    @classmethod
    def notify(
        cls, who: str, action: str, policy: "Policy", customer_email=None
    ) -> Dict[str, Any]:
        """
        Notify a stakeholder about an action that took place on this policy

        Arguments:
            who: The stakeholder to notify, either a 'merchant' or a 'customer'
            action: The action that took place on the policy
            policy: The policy instance on which the action took place

        Returns:
            A dictionary with a status message
        """
        message_template = cls.ACTION_REGISTRY.get(action, {}).get(who)
        print(f"Mssage template: {message_template}")
        if not message_template:
            raise ValueError("Invalid action or recipent type")

        # Build the notification information based on the passed parameters
        # we want to get recipent email  address based on who's being notified
        # and construct the message subject based on specific action.
        if customer_email and who == "customer":
            recipient = customer_email
        else:
            recipient = (
                policy.merchant.business_email
                if who == "merchant"
                else policy.policy_holder.email
            )

        subject = f"Policy Notification - {action}"

        # We want to send  the notification to the recipient using the appropriate channel
        notification_channel_class = cls.NOTIFICATION_CHANNEL_REGISTRY.get("email")

        if notification_channel_class:
            notification_channel = notification_channel_class()
            notification_channel.send_message(subject, message_template, recipient)
        else:
            raise ValueError("Invalid notification channel")

        logger.info(f"Notification sent to {recipient} successfully")

        return {"message": "Notification sent successfully", "status": "success"}
