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

    @abstractmethod
    def send(subject: str, message: str, recipient: str) -> None:
        raise NotImplementedError


class NotificationService(INotification):
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

        return {}

    def send(subject: str, message: str, recipient: str) -> None:
        """
        Send a notification to the recipient

        Arguments:
            subject: The subject of the notification
            message: The message to send
            recipient: The recipient of the notification
        """

        pass
