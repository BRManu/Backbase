import logging
from datetime import date
from decimal import Decimal
from django.db import transaction
from ..models import Currency, CurrencyExchangeRate, Provider
from .adapters import PROVIDERS as ADAPTER_CLASSES

logger = logging.getLogger(__name__)

def get_exchange_rate_data(source_currency_code, exchanged_currency_code, valuation_date, provider_name=None):
    """
    Retrieves exchange rate data with resilience and priority.
    
    1. If a specific provider is requested, use only that one.
    2. Otherwise, fetch all active providers from DB, ordered by priority.
    3. Try each provider until one succeeds.
    4. Save the successful rate to the database (caching).
    """
    
    # Validation of currencies (optional but good practice)
    try:
        source_currency = Currency.objects.get(code=source_currency_code)
        exchanged_currency = Currency.objects.get(code=exchanged_currency_code)
    except Currency.DoesNotExist:
        logger.error(f"Currency not found: {source_currency_code} or {exchanged_currency_code}")
        return None

    # Determine which providers to try
    if provider_name:
        providers = Provider.objects.filter(name=provider_name, is_active=True)
    else:
        providers = Provider.objects.filter(is_active=True).order_by('priority')

    if not providers.exists():
        logger.warning("No active providers configured.")
        return None

    # Try each provider in order
    for provider_model in providers:
        adapter_class = ADAPTER_CLASSES.get(provider_model.name)
        if not adapter_class:
            logger.error(f"Adapter class not found for provider: {provider_model.name}")
            continue

        try:
            adapter = adapter_class()
            rate_value = adapter.get_rate(source_currency_code, exchanged_currency_code, valuation_date)
            
            if rate_value is not None:
                # Success! Save to database for future use (cache)
                # using update_or_create to avoid duplicate records for the same day/provider
                with transaction.atomic():
                    rate_obj, created = CurrencyExchangeRate.objects.update_or_create(
                        source_currency=source_currency,
                        exchanged_currency=exchanged_currency,
                        valuation_date=valuation_date,
                        provider=provider_model.name,
                        defaults={'rate_value': rate_value}
                    )
                return rate_value
        except Exception as e:
            logger.exception(f"Error fetching rate from {provider_model.name}: {str(e)}")
            continue # Try the next one

    return None
