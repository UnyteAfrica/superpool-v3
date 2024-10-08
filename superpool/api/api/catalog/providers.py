from api.catalog.interfaces import BaseQuoteProvider, HeirsQuoteProvider


class QuoteProviderFactory:
    providers = {
        "Heirs": HeirsQuoteProvider,
    }

    @staticmethod
    def get_provider(provider_name: str) -> BaseQuoteProvider:
        provider_class = QuoteProviderFactory.providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Provider {provider_name} is not supported.")
        return provider_class()
