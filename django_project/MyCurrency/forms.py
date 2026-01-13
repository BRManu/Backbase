from django import forms
from .models import Currency

class AdminCurrencyConverterForm(forms.Form):
    source_currency = forms.ModelChoiceField(
        queryset=Currency.objects.filter(is_active=True),
        label="Source Currency",
        empty_label=None
    )
    amount = forms.DecimalField(
        max_digits=18, 
        decimal_places=2, 
        initial=1.00,
        min_value=0.01
    )
    target_currencies = forms.ModelMultipleChoiceField(
        queryset=Currency.objects.filter(is_active=True),
        label="Target Currencies",
        widget=forms.CheckboxSelectMultiple
    )
