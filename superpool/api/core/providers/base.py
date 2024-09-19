from __future__ import annotations

from abc import ABC, abstractmethod

from core.providers.exceptions import ProviderNotFound


class Provider(ABC):
    """
    Interface for Insurance Providers/Partners

    """

    @abstractmethod
    def get_all_products(self) -> list[Product]:
        """
        Retrieve all products and policies offered by the provider

        Returns:
            list[Product]: List of all products offered by the provider
        """
        ...

    @abstractmethod
    def validate_provider(self) -> None:
        """
        Validate the provider instance by its short code

        Raises:
            ValidationError: If the provider instance is invalid
        """
        pass

    @abstractmethod
    def has_policy(self, policy: str) -> bool:
        """
        Check if the provider has a policy by its unique identifier or name

        Args:
            policy_id (str): Unique identifier of the policy

        Returns:
            bool: True if the policy exists, False otherwise
        """
        pass


class BaseProvider(Provider):
    """
    Extensible base class for Insurance Providers/Partners

    Implementations must provide concrete implement of the BaseProvider API
    """

    @abstractmethod
    def get_provider(self, provider_id: str) -> Provider | None:
        """
        Retrieve a provider by its unique identifier

        Args:
            provider_id (str): Unique identifier of the provider

        Returns:
            Optional[Provider]: Provider instance if found, None otherwise
        """
        pass

    @abstractmethod
    def get_provider_by_short_code(self, short_code: str) -> Provider | None:
        """
        Retrieve a provider by its short code

        Args:
            short_code (str): Short code of the provider

        Returns:
            Optional[Provider]: Provider instance if found, None otherwise
        """
        pass

    @abstractmethod
    def get_provider_by_name(self, name: str) -> Provider | None | ProviderNotFound:
        """
        Retrieve a provider by its name

        Args:
            name (str): Name of the provider

        Returns:
            Optional[Provider]: Provider instance if found, None otherwise
        """
        pass

    @abstractmethod
    def get_all_providers(self) -> list[Provider]:
        """
        Retrieve all providers in the system

        Returns:
            list[Provider]: List of all providers in the system
        """
        pass

    @abstractmethod
    def create_provider(self, provider: Provider) -> Provider:
        """
        Create a new provider in the system

        Args:
            provider (Provider): Provider instance to create

        Returns:
            Provider: Created provider instance
        """
        pass

    @abstractmethod
    def update_provider(
        self, provider_instance: Provider, **kwargs: dict[str, object]
    ) -> Provider:
        """
        Update an existing provider in the system

        Args:
            provider (Provider): Provider instance to update

        Returns:
            Provider: Updated provider instance
        """
        pass
