from django.db import models


class AccountingEntry(models.Model):
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="USD")
    entry_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-entry_date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.description}: {self.amount} {self.currency}"
