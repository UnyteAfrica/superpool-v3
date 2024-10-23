from abc import ABC, abstractmethod

from django.core.cache import cache
from django.db import Error

from core.models import APIKeyV2


def invariant_check(condition: bool, message: str) -> Exception | Error:
    """
    Check the invariant edge cases
    """
    return


class IAuthService(ABC):
    """
    Interface for authentication service
    """

    @abstractmethod
    def validate(self, key: str) -> "APIKeyV2":
        """
        Validate the key
        """
        raise NotImplementedError


class KeyAuthService(IAuthService):
    """
    Key authentication service
    """

    CACHE_TIMEOUT = 60  # about a minute

    def _recompute_hash(self, key: str) -> str:
        """
        Recompute the hash of the key
        """
        pass

    def verify_checksum(self, key: str) -> bool:
        """
        Verify the checksum of the key
        """
        pass

    def _validate_format(self, provided_key: str) -> None:
        prefix, env_label, client_id, hashed_part, _ = provided_key.split("_")
        invariant_check(not prefix, "Invalid API Key format")
        invariant_check(
            env_label not in ("uk_test", "uk_live"), "Invalid API Key format"
        )
        invariant_check(
            hashed_part != (expected_hash := self._recompute_hash(provided_key)),
            "Checksum validation failed",
        )

    def validate(self, key: str) -> "APIKeyV2":
        """
        Validate the provided key
        """
        try:
            _, _, client_id, hashed_part, _ = key.split("_")
        except ValueError:
            raise ValueError("Invalid API Key format")

        try:
            api_key = self._validate_format(key)
        except (ValueError, Exception):
            raise

        cache_prefix = "key"
        cache_key = f"{cache_prefix}_metadata:{key}"
        cached_metadata = cache.get(cache_key)

        if cached_metadata:
            api_key = APIKeyV2.objects.get(id=cached_metadata["id"])

            if not api_key.is_active:
                raise ValueError("API Key is revoked!")
            return api_key

        # retrieve corresponding api key obj and store metadata
        # in cache
        api_key = APIKeyV2.objects.get(
            key_hash=hashed_part, environment__client_id=client_id, is_active=True
        )

        cache.set(
            cache_key,
            {
                "id": api_key.id,
                "client_id": client_id,
                "environment": api_key.environment.is_test_mode,
                "type": api_key.api_key_type,
            },
            timeout=KeyAuthService.CACHE_TIMEOUT,
        )
        return api_key

    @staticmethod
    def revoke_key(key: str) -> None:
        """
        Revoke the key
        """
        api_key = APIKeyV2.objects.get(key_hash=key)
        api_key.is_active = False
        api_key.save()

        cache_prefix = "key"
        cache_key = f"{cache_prefix}_metadata:{key}"
        cache.delete(cache_key)
