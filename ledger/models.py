from django.db import models
from django.utils import timezone
from django.core.validators import MinLengthValidator

class Account(models.Model):
    ACCOUNT_TYPES = [
        ("ASSET", "Asset"),
        ("LIAB", "Liability"),
        ("INCOME", "Income"),
        ("EXP", "Expense"),
        ("EQUITY", "Equity"),
    ]
    code = models.CharField(max_length=32, unique=True, validators=[MinLengthValidator(2)])
    name = models.CharField(max_length=128)
    type = models.CharField(max_length=8, choices=ACCOUNT_TYPES)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.code} - {self.name}"

class Transaction(models.Model):
    external_id = models.CharField(max_length=64, unique=True)
    idempotency_key = models.CharField(max_length=64, unique=True)
    amount = models.BigIntegerField(help_text="minor units, e.g., cents")
    currency = models.CharField(max_length=3, default="EUR")
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=16, default="REQUESTED")  # REQUESTED|SETTLED|FAILED
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

class Posting(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="postings")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="postings")
    amount = models.BigIntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [models.Index(fields=["account", "created_at"])]
        constraints = [
            models.CheckConstraint(condition=~models.Q(amount=0), name="posting_amount_nonzero"),
        ]
