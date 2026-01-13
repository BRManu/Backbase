from django.db import models


class ProtectedModel(models.Model):
    """
    Abstract base model with audit fields and soft-delete capability.
    All models should inherit from this for consistent behavior.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Currency(ProtectedModel):
    """
    Currency model representing available currencies in the system.
    """
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=20, db_index=True)
    symbol = models.CharField(max_length=10)

    class Meta:
        verbose_name_plural = "Currencies"

    def __str__(self):
        return f"{self.code} - {self.name}"


class CurrencyExchangeRate(ProtectedModel):
    """
    Exchange rate between two currencies on a specific date.
    """
    source_currency = models.ForeignKey(
        Currency,
        related_name='exchanges',
        on_delete=models.CASCADE
    )
    exchanged_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE
    )
    valuation_date = models.DateField(db_index=True)
    rate_value = models.DecimalField(
        db_index=True,
        decimal_places=6,
        max_digits=18
    )
    provider = models.CharField(max_length=50, db_index=True, default='unknown')

    class Meta:
        unique_together = ['source_currency', 'exchanged_currency', 'valuation_date', 'provider']

    def __str__(self):
        return f"{self.source_currency.code} -> {self.exchanged_currency.code}: {self.rate_value} ({self.valuation_date}) via {self.provider}"


class Provider(ProtectedModel):
    """
    Registry of currency exchange rate providers with priority and active status.
    """
    name = models.CharField(max_length=50, unique=True)
    priority = models.IntegerField(default=1, help_text="Lower value means higher priority.")
    
    class Meta:
        ordering = ['priority', 'created_at']

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.name} (Priority: {self.priority}, {status})"
