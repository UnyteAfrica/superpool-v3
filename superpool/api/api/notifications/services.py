import logging
from typing import Any, Dict, Union

from core.catalog.models import Policy

from .base import NotificationService

logger = logging.getLogger(__name__)


class PolicyNotificationService(NotificationService):
    """
    Policy Notification Service

    """

    @staticmethod
    def notify_merchant(
        action: str, policy: "Policy", customer: dict, transaction_date: str
    ) -> None:
        """Send a notification to the merchant about the action that took place on the policy"""

        print(f"Sending notification to merchant for action: {action}")
        service = NotificationService()
        service.stream_through(NotificationService.EMAIL)

        # prepare context for the email template
        context = {
            "policy": policy,
            "customer_name": f'{customer["first_name"]} {customer["last_name"]}',
            "transaction_date": transaction_date,
        }

        message_data = service.prepare_message(action, "merchant", context=context)
        service.send(
            recipient=policy.merchant.business_email,
            subject=message_data["subject"],
            message=message_data["body"],
        )
        logger.info(f"Notification sent to {policy.merchant.business_email}")

    @staticmethod
    def notify_customer(
        action: str,
        policy: "Policy",
        customer_email: Union[str, None] = None,
        **extra_kwargs: Dict[str, Any],
    ) -> None:
        """Send a notification to the customer about the action that took place on the policy"""

        print(f"Sending notification to customer for action: {action}")
        service = NotificationService()
        # We would assume the policy holder is to be notified if the user information
        # is not passed to this function
        recipient = customer_email or policy.policy_holder.email
        _channel = extra_kwargs.get("notification_channel", NotificationService.EMAIL)
        print(f"Selected notification channel:  {_channel}")
        service.stream_through(_channel)
        message_data = service.prepare_message(action, "customer")
        print(f"Message data: {message_data}")

        service.send(
            recipient=recipient,
            subject=message_data["subject"],
            message=message_data["body"],
        )
        logger.info(f"Notification sent to {recipient} via {_channel}")
