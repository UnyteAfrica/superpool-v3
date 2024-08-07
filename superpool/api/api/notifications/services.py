from typing import Any, Dict, Union

from core.catalog.models import Policy

from .base import NotificationService


class PolicyNotificationService(NotificationService):
    """
    Policy Notification Service

    """

    @staticmethod
    def notify_merchant(action: str, policy: "Policy") -> Dict[str, Any]:
        """Send a notification to the merchant about the action that took place on the policy"""
        print(f"Sending notification to merchant for action: {action}")

    @staticmethod
    def notify_customer(
        action: str, policy: "Policy", **extra_kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send a notification to the customer about the action that took place on the policy"""

        print(f"Sending notification to customer for action: {action}")
