from rest_framework import serializers
from .models import Currency, CurrencyExchangeRate

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ['id', 'code', 'name', 'symbol', 'is_active', 'created_at', 'updated_at']

class CurrencyExchangeRateSerializer(serializers.ModelSerializer):
    source_currency_code = serializers.ReadOnlyField(source='source_currency.code')
    exchanged_currency_code = serializers.ReadOnlyField(source='exchanged_currency.code')

    class Meta:
        model = CurrencyExchangeRate
        fields = [
            'id', 'source_currency_code', 'exchanged_currency_code', 
            'valuation_date', 'rate_value', 'provider', 'created_at'
        ]

class ConvertAmountSerializer(serializers.Serializer):
    source_currency = serializers.CharField(max_length=3)
    exchanged_currency = serializers.CharField(max_length=3)
    amount = serializers.DecimalField(max_digits=18, decimal_places=6)
