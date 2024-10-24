from abc import ABC, abstractmethod

from django.core.cache import cache

from core.models import APIKeyV2


def invariant_check(condition: bool, message: str) -> Exception | None:
    """
    Check the invariant edge cases
    """
    if not condition:
        raise ValueError(message)


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
        return True

    def _validate_format(self, provided_key: str) -> dict:
        """
        Validates the format of the provided key and extract its components
        """
        try:
            prefix, env_label, client_id, hashed_part, checksum = provided_key.split(
                "_"
            )
        except ValueError:
            raise ValueError("Invalid API Key format: Incorrect number of components")

        invariant_check(not prefix, "Invalid API Key format: Missing prefix")
        invariant_check(prefix != "unyt", "Invalid API Key format: Incorrect prefix")
        invariant_check(
            env_label not in ("uk_test", "uk_live"),
            "Invalid API Key format: Invalid Environment Identifier",
        )
        invariant_check(not client_id, "Invalid API Key format: Missing client ID")
        invariant_check(not hashed_part, "Invalid API Key format: Missing hashed part")
        invariant_check(not checksum, "Invalid API Key format: Checksum not provided")

        return {
            "prefix": prefix,
            "env_label": env_label,
            "client_id": client_id,
            "hashed_part": hashed_part,
            "checksum": checksum,
        }

    def validate(self, key: str) -> "APIKeyV2":
        """
        Validate the provided key
        """
        key_metadata = self._validate_format(key)
        client_id = key_metadata["client_id"]
        hashed_part = key_metadata["hashed_part"]

        if not self.verify_checksum(key):
            raise ValueError("Invalid API Key: Checksum mismatch")

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
        try:
            api_key = APIKeyV2.objects.get(
                key_hash=hashed_part, client_id=client_id, is_active=True
            )
        except APIKeyV2.DoesNotExist:
            raise ValueError("Invalid API Key: Key not found")

        cache.set(
            cache_key,
            {
                "id": str(api_key.id),
                "client_id": client_id,
                "key_type": api_key.api_key_type,
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
