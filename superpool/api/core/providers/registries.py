from .exceptions import ProviderNotFound

PARTNERS_REGISTRY = {
    "AXA": "AXA INSURANCE",
    "HEIR": "HEIRS INSURANCE",
    "LEAD": "LEADWAY",
    "UNYT": "UNYTE",
}


def get_provider_instance(provider_name: str) -> Provider:
    """
    Retrieves a specfic insurance instance
    """
    ProviderClass = PARTNERS_REGISTRY.get(provider_name)

    if ProviderClass:
        return ProviderClass
    return ProviderNotFound()
