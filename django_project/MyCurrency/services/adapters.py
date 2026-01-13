import random
import requests
from abc import ABC, abstractmethod
from decimal import Decimal
from django.conf import settings

class BaseCurrencyProvider(ABC):
    """
    Abstract base class for all currency exchange rate providers.
    """
    @abstractmethod
    def get_rate(self, source_currency, exchanged_currency, valuation_date):
        pass

class MockProvider(BaseCurrencyProvider):
    """
    A mock provider that returns random exchange rates for testing.
    """
    def get_rate(self, source_currency, exchanged_currency, valuation_date):
        # Generate a random rate between 0.5 and 2.0
        return Decimal(str(round(random.uniform(0.5, 2.0), 6)))

class CurrencyBeaconProvider(BaseCurrencyProvider):
    """
    Provider that integrates with the CurrencyBeacon API.
    """
    BASE_URL = "https://api.currencybeacon.com/v1/historical"

    def get_rate(self, source_currency, exchanged_currency, valuation_date):
        api_key = getattr(settings, 'CURRENCY_BEACON_API_KEY', None)
        if not api_key:
            return None

        params = {
            'api_key': api_key,
            'base': source_currency,
            'symbols': exchanged_currency,
            'date': valuation_date.strftime('%Y-%m-%d')
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # CurrencyBeacon structure: data['response']['rates'][symbol]
            response_data = data.get('response', {})
            rate = response_data.get('rates', {}).get(exchanged_currency)
            if rate is not None:
                return Decimal(str(rate))
        except (requests.RequestException, ValueError, KeyError):
            pass
        
        return None

PROVIDERS = {
    'mock': MockProvider,
    'currency_beacon': CurrencyBeaconProvider,
}
