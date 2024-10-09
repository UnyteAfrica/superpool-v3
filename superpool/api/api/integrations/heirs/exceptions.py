from dataclasses import dataclass
from typing import Optional


@dataclass
class HeirsAPIException(Exception):
    # Models the error response of heirs
    # meant to be thrown within heirs service
    # See: core/integrations/providers/heirs/registry.py
    type: Optional[str] = None
    title: Optional[str] = None
    detail: Optional[str] = None
    status: Optional[str] = None

    def __str__(self):
        return f"HeirsAPIException(type={self.type}, title={self.title}, detail={self.detail}, status={self.status})"
