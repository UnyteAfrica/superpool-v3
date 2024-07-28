from .base import NotificationService


class PolicyNotificationService(NotificationService):
    """
    Policy Notification Service

    """

    def notify_merchant(cls, action: str, data) -> None:
        """Send a notification to the merchant about the action that took place on the policy"""
        pass

    def notify_customer(cls, action: str, data) -> None:
        """Send a notification to the customer about the action that took place on the policy"""
        pass
