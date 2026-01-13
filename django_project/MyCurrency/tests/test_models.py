"""
Tests for MyCurrency models.
"""
import pytest
from decimal import Decimal
from datetime import date

from MyCurrency.models import Currency, CurrencyExchangeRate, Provider


@pytest.fixture
def currency_eur(db):
    """Fixture que crea una moneda EUR para los tests."""
    return Currency.objects.create(code='EUR', name='Euro', symbol='€')


@pytest.fixture
def currency_usd(db):
    """Fixture que crea una moneda USD para los tests."""
    return Currency.objects.create(code='USD', name='US Dollar', symbol='$')


@pytest.fixture
def provider_mock(db):
    """Fixture que crea un proveedor mock."""
    return Provider.objects.create(name='mock', priority=1, is_active=True)


class TestCurrencyModel:
    
    def test_currency_creation(self, currency_eur):
        """Verifica que se puede crear una moneda correctamente."""
        assert currency_eur.code == 'EUR'
        assert currency_eur.name == 'Euro'
        assert currency_eur.symbol == '€'
        assert currency_eur.is_active is True
    
    def test_currency_str_representation(self, currency_eur):
        """Verifica la representación string del modelo."""
        assert str(currency_eur) == 'EUR - Euro'
    
    def test_currency_soft_delete(self, currency_eur):
        """Verifica que el soft-delete funciona (poniendo is_active=False)."""
        currency_eur.is_active = False
        currency_eur.save()
        
        # El objeto sigue existiendo en la DB
        assert Currency.objects.filter(code='EUR').exists()
        # Pero está marcado como inactivo
        assert Currency.objects.get(code='EUR').is_active is False


class TestCurrencyExchangeRateModel:
    """Tests para el modelo CurrencyExchangeRate."""
    
    def test_exchange_rate_creation(self, currency_eur, currency_usd):
        """Verifica que se puede crear una tasa de cambio."""
        rate = CurrencyExchangeRate.objects.create(
            source_currency=currency_eur,
            exchanged_currency=currency_usd,
            valuation_date=date(2024, 1, 15),
            rate_value=Decimal('1.085'),
            provider='mock'
        )
        
        assert rate.source_currency == currency_eur
        assert rate.exchanged_currency == currency_usd
        assert rate.rate_value == Decimal('1.085')
    
    def test_exchange_rate_str_includes_provider(self, currency_eur, currency_usd):
        """Verifica que la representación string incluye el proveedor."""
        rate = CurrencyExchangeRate.objects.create(
            source_currency=currency_eur,
            exchanged_currency=currency_usd,
            valuation_date=date(2024, 1, 15),
            rate_value=Decimal('1.085'),
            provider='currency_beacon'
        )
        
        assert 'currency_beacon' in str(rate)


class TestProviderModel:
    """Tests para el modelo Provider."""
    
    def test_provider_creation(self, provider_mock):
        """Verifica la creación de un proveedor."""
        assert provider_mock.name == 'mock'
        assert provider_mock.priority == 1
        assert provider_mock.is_active is True
    
    def test_provider_ordering_by_priority(self, db):
        """Verifica que los proveedores se ordenan por prioridad."""
        Provider.objects.create(name='low_priority', priority=10, is_active=True)
        Provider.objects.create(name='high_priority', priority=1, is_active=True)
        Provider.objects.create(name='medium_priority', priority=5, is_active=True)
        
        providers = list(Provider.objects.all())
        
        assert providers[0].name == 'high_priority'
        assert providers[1].name == 'medium_priority'
        assert providers[2].name == 'low_priority'
