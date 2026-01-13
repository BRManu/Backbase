from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from datetime import date
from .models import Currency, CurrencyExchangeRate, Provider
from .forms import AdminCurrencyConverterForm
from .services.exchange_rates import get_exchange_rate_data
from .admin_site import my_currency_admin_site

class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'symbol', 'is_active', 'created_at')
    search_fields = ('code', 'name')
    list_filter = ('is_active',)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_converter_link'] = True
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('converter/', self.admin_site.admin_view(self.converter_view), name='currency-converter'),
        ]
        return custom_urls + urls

    def converter_view(self, request):
        results = []
        form = AdminCurrencyConverterForm(request.POST or None)
        
        if request.method == 'POST' and form.is_valid():
            source = form.cleaned_data['source_currency']
            amount = form.cleaned_data['amount']
            targets = form.cleaned_data['target_currencies']
            
            for target in targets:
                rate = get_exchange_rate_data(source.code, target.code, date.today())
                if rate:
                    results.append({
                        'currency': target,
                        'rate': rate,
                        'converted': amount * rate
                    })
        
        context = {
            **self.admin_site.each_context(request),
            'form': form,
            'results': results,
            'amount': form.cleaned_data.get('amount') if form.is_valid() else None,
            'source': form.cleaned_data.get('source_currency') if form.is_valid() else None,
            'title': 'Currency Converter'
        }
        return render(request, 'admin/currency_converter.html', context)

class CurrencyExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('source_currency', 'exchanged_currency', 'valuation_date', 'rate_value', 'provider', 'created_at')
    list_filter = ('valuation_date', 'source_currency', 'exchanged_currency', 'provider')
    date_hierarchy = 'valuation_date'

class ProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'priority', 'is_active', 'updated_at')
    list_editable = ('priority', 'is_active')
    ordering = ('priority',)

from django.contrib.auth.models import User, Group

# Register everything to the custom site instead of the default admin.site
my_currency_admin_site.register(Currency, CurrencyAdmin)
my_currency_admin_site.register(CurrencyExchangeRate, CurrencyExchangeRateAdmin)
my_currency_admin_site.register(Provider, ProviderAdmin)
my_currency_admin_site.register(User)
my_currency_admin_site.register(Group)
my_currency_admin_site.register(admin.models.LogEntry)
