from datetime import datetime
from rest_framework import viewsets, views, status, response
from django.shortcuts import get_object_or_404
from .models import Currency, CurrencyExchangeRate
from .serializers import CurrencySerializer, CurrencyExchangeRateSerializer, ConvertAmountSerializer
from .services.exchange_rates import get_exchange_rate_data

class CurrencyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Currencies to be viewed or edited.
    """
    queryset = Currency.objects.all().order_by('code')
    serializer_class = CurrencySerializer

class ExchangeRateListView(views.APIView):
    """
    API endpoint to retrieve a list of currency rates for a specific time period.
    """
    def get(self, request):
        source_code = request.query_params.get('source_currency')
        date_from_str = request.query_params.get('date_from')
        date_to_str = request.query_params.get('date_to')

        if not all([source_code, date_from_str, date_to_str]):
            return response.Response(
                {"error": "Missing parameters: source_currency, date_from, and date_to are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            return response.Response(
                {"error": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        source_currency = get_object_or_404(Currency, code=source_code)
        
        # Pre-fetch could be optimized here, but standard filtering is sufficient for now
        rates = CurrencyExchangeRate.objects.filter(
            source_currency=source_currency,
            valuation_date__range=[date_from, date_to]
        ).select_related('exchanged_currency').order_by('valuation_date', 'exchanged_currency__code')
        
        serializer = CurrencyExchangeRateSerializer(rates, many=True)
        return response.Response(serializer.data)

class ConvertAmountView(views.APIView):
    """
    API endpoint that calculates the amount in a currency exchanged into a different currency.
    """
    def post(self, request):
        serializer = ConvertAmountSerializer(data=request.data)
        if not serializer.is_valid():
            return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        source_code = serializer.validated_data['source_currency']
        target_code = serializer.validated_data['exchanged_currency']
        amount = serializer.validated_data['amount']

        today = datetime.now().date()
        
        rate_obj = CurrencyExchangeRate.objects.filter(
            source_currency__code=source_code,
            exchanged_currency__code=target_code,
            valuation_date=today
        ).first()

        if rate_obj:
            rate_value = rate_obj.rate_value
        else:
            # Not in DB, fetch from resilient providers
            rate_value = get_exchange_rate_data(source_code, target_code, today)

        if rate_value is None:
            return response.Response(
                {"error": "Could not retrieve exchange rate for the requested pair."},
                status=status.HTTP_404_NOT_FOUND
            )

        converted_amount = amount * rate_value

        return response.Response({
            "source_currency": source_code,
            "exchanged_currency": target_code,
            "amount": float(amount),
            "rate": float(rate_value),
            "converted_amount": float(converted_amount),
            "valuation_date": today.isoformat()
        })
