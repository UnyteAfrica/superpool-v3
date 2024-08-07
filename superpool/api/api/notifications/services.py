from typing import Any

from core.catalog.models import Policy

from .base import NotificationService


class PolicyNotificationService(NotificationService):
    """
    Policy Notification Service

    """

    @classmethod
    def notify_merchant(cls, action: str, policy: "Policy") -> dict[str, Any]:
        """Send a notification to the merchant about the action that took place on the policy"""
        return cls.notify("merchant", action, policy)

    @classmethod
    def notify_customer(
        cls, action: str, policy: "Policy", **extra_kwargs: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a notification to the customer about the action that took place on the policy"""
        customer_email = extra_kwargs.get("customer_email")
        return cls.notify("customer", action, policy, customer_email, **extra_kwargs)
