"""
Tests for REST API endpoints.
"""
import pytest
from decimal import Decimal
from datetime import date
from rest_framework.test import APIClient

from MyCurrency.models import Currency, CurrencyExchangeRate, Provider


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def currencies(db):
    """Fixture que crea monedas de prueba."""
    eur = Currency.objects.create(code='EUR', name='Euro', symbol='€')
    usd = Currency.objects.create(code='USD', name='US Dollar', symbol='$')
    return {'EUR': eur, 'USD': usd}


@pytest.fixture
def exchange_rate(currencies):
    """Fixture que crea una tasa de cambio de prueba."""
    return CurrencyExchangeRate.objects.create(
        source_currency=currencies['EUR'],
        exchanged_currency=currencies['USD'],
        valuation_date=date.today(),
        rate_value=Decimal('1.085'),
        provider='mock'
    )


@pytest.fixture
def provider(db):
    """Fixture que crea un proveedor activo."""
    return Provider.objects.create(name='mock', priority=1, is_active=True)


class TestCurrencyAPI:
    """Tests para el endpoint /api/v1/currencies/"""
    
    def test_list_currencies_empty(self, api_client, db):
        """Verifica que se pueden listar monedas (vacío)."""
        response = api_client.get('/api/v1/currencies/')
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_currencies_with_data(self, api_client, currencies):
        """Verifica que se listan las monedas existentes."""
        response = api_client.get('/api/v1/currencies/')
        
        assert response.status_code == 200
        assert len(response.json()) == 2
    
    def test_create_currency(self, api_client, db):
        """Verifica que se puede crear una moneda vía POST."""
        data = {'code': 'GBP', 'name': 'British Pound', 'symbol': '£'}
        response = api_client.post('/api/v1/currencies/', data, format='json')
        
        assert response.status_code == 201
        assert Currency.objects.filter(code='GBP').exists()
    
    def test_retrieve_currency(self, api_client, currencies):
        """Verifica que se puede obtener una moneda por ID."""
        currency_id = currencies['EUR'].id
        response = api_client.get(f'/api/v1/currencies/{currency_id}/')
        
        assert response.status_code == 200
        assert response.json()['code'] == 'EUR'


class TestExchangeRateAPI:
    """Tests para el endpoint /api/v1/rates/"""
    
    def test_rates_requires_parameters(self, api_client, db):
        """Verifica que el endpoint requiere parámetros."""
        response = api_client.get('/api/v1/rates/')
        
        assert response.status_code == 400
    
    def test_rates_with_valid_params(self, api_client, currencies, exchange_rate):
        """Verifica que devuelve tasas con parámetros válidos."""
        today = date.today().isoformat()
        response = api_client.get(
            f'/api/v1/rates/?source_currency=EUR&date_from={today}&date_to={today}'
        )
        
        assert response.status_code == 200
        assert len(response.json()) >= 1


class TestConvertAPI:
    """Tests para el endpoint /api/v1/convert/"""
    
    def test_convert_requires_body(self, api_client, db):
        """Verifica que el endpoint requiere un body."""
        response = api_client.post('/api/v1/convert/', {}, format='json')
        
        assert response.status_code == 400
    
    def test_convert_with_existing_rate(self, api_client, currencies, exchange_rate, provider):
        """Verifica la conversión con una tasa existente en DB."""
        data = {
            'source_currency': 'EUR',
            'exchanged_currency': 'USD',
            'amount': 100
        }
        response = api_client.post('/api/v1/convert/', data, format='json')
        
        assert response.status_code == 200
        assert 'converted_amount' in response.json()
