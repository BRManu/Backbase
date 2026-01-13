"""
Tests para los servicios (adapters y exchange_rates).
Ejecutar con: pytest MyCurrency/tests/test_services.py -v
"""
import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import patch, MagicMock

from MyCurrency.models import Currency, Provider
from MyCurrency.services.adapters import MockProvider, PROVIDERS
from MyCurrency.services.exchange_rates import get_exchange_rate_data


class TestMockProvider:
    """Tests para el proveedor Mock."""
    
    def test_mock_provider_returns_decimal(self):
        """Verifica que el MockProvider devuelve un Decimal."""
        provider = MockProvider()
        rate = provider.get_rate('EUR', 'USD', date.today())
        
        assert isinstance(rate, Decimal)
    
    def test_mock_provider_returns_valid_range(self):
        """Verifica que la tasa está en un rango razonable."""
        provider = MockProvider()
        rate = provider.get_rate('EUR', 'USD', date.today())
        
        assert Decimal('0.5') <= rate <= Decimal('2.0')


class TestProvidersRegistry:
    """Tests para el registro de proveedores."""
    
    def test_providers_registry_has_mock(self):
        """Verifica que el registro contiene el proveedor mock."""
        assert 'mock' in PROVIDERS
    
    def test_providers_registry_has_currency_beacon(self):
        """Verifica que el registro contiene currency_beacon."""
        assert 'currency_beacon' in PROVIDERS


class TestGetExchangeRateData:
    """Tests para la función principal de obtención de tasas."""
    
    @pytest.fixture
    def setup_currencies_and_provider(self, db):
        """Fixture que prepara el entorno de test."""
        Currency.objects.create(code='EUR', name='Euro', symbol='€')
        Currency.objects.create(code='USD', name='US Dollar', symbol='$')
        Provider.objects.create(name='mock', priority=1, is_active=True)
    
    def test_get_rate_uses_mock_provider(self, setup_currencies_and_provider):
        """Verifica que se puede obtener una tasa usando el mock."""
        rate = get_exchange_rate_data('EUR', 'USD', date.today(), provider_name='mock')
        
        assert rate is not None
        assert isinstance(rate, Decimal)
    
    def test_get_rate_returns_none_for_missing_currency(self, db):
        """Verifica que devuelve None si la moneda no existe."""
        rate = get_exchange_rate_data('XXX', 'YYY', date.today())
        
        assert rate is None
    
    def test_get_rate_returns_none_for_inactive_provider(self, db):
        """Verifica que no usa proveedores inactivos."""
        Currency.objects.create(code='EUR', name='Euro', symbol='€')
        Currency.objects.create(code='USD', name='US Dollar', symbol='$')
        Provider.objects.create(name='mock', priority=1, is_active=False)
        
        rate = get_exchange_rate_data('EUR', 'USD', date.today())
        
        # Sin proveedores activos, debería devolver None
        assert rate is None
