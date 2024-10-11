from dataclasses import dataclass


@dataclass
class HeirsAPIException(Exception):
    # Models the error response of heirs
    # meant to be thrown within heirs service
    # See: core/integrations/providers/heirs/registry.py
    type: str
    title: str
    detail: str
    status: str

    def __str__(self):
        return f"HeirsAPIException(type={self.type}, title={self.title}, detail={self.detail}, status={self.status})"
