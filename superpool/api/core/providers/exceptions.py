class ProviderNotFound(Exception):
    """Raised when a provider is not found in the registry."""


class ProviderAlreadyExists(Exception):
    """Raised when a provider already exists in the registry"""


class InvalidProviderCredentials(Exception):
    """Raised when a request is made with invalid credentials for a given provider"""


class InvalidProvider(Exception):
    """Raised when a provider instance is invalid"""
