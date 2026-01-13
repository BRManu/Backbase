from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import CurrencyViewSet, ExchangeRateListView, ConvertAmountView

router = DefaultRouter()
router.register(r'currencies', CurrencyViewSet)

# Namespace for API versioning. This allows:
# - /api/v1/currencies/
# - /api/v1/rates/
# - /api/v1/convert/
app_name = 'v1'

urlpatterns = [
    path('', include(router.urls)),
    path('rates/', ExchangeRateListView.as_view(), name='exchange-rate-list'),
    path('convert/', ConvertAmountView.as_view(), name='convert-amount'),
]
