import pytest
from django.urls import reverse
from ledger.models import Account, Transaction, Posting

@pytest.mark.django_db
def test_initiate_transaction_creates_balanced_postings(api):
    cash = Account.objects.create(code="1001", name="Cash", type="ASSET")
    payable = Account.objects.create(code="2001", name="Payable", type="LIAB")

    url = reverse("transaction-initiate")
    payload = {
        "external_id": "ext-001",
        "idempotency_key": "idem-001",
        "amount": 1500,
        "currency": "EUR",
        "debit_account": "1001",
        "credit_account": "2001",
        "description": "Test",
    }
    res = api.post(url, payload, format="json")

    assert res.status_code in (201, 200)
    tx = Transaction.objects.get(external_id="ext-001")
    amounts = list(Posting.objects.filter(transaction=tx).values_list("amount", flat=True))
    assert len(amounts) == 2
    assert sum(amounts) == 0

@pytest.mark.django_db
def test_initiate_is_idempotent(api):
    Account.objects.create(code="1001", name="Cash", type="ASSET")
    Account.objects.create(code="2001", name="Payable", type="LIAB")

    url = reverse("transaction-initiate")
    payload = {
        "external_id": "ext-002",
        "idempotency_key": "same-key",
        "amount": 999,
        "currency": "EUR",
        "debit_account": "1001",
        "credit_account": "2001",
    }

    r1 = api.post(url, payload, format="json")
    r2 = api.post(url, payload, format="json")

    assert r1.status_code in (201, 200)
    assert r2.status_code in (201, 200)
    # still exactly one transaction in DB
    assert Transaction.objects.filter(idempotency_key="same-key").count() == 1
