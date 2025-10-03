import pytest
from django.urls import reverse
from ledger.models import Account

@pytest.mark.django_db
def test_balance_on_empty_account(api):
    cash = Account.objects.create(code="1001", name="Cash", type="ASSET")

    url = reverse("account-balance", kwargs={"code": cash.code})
    res = api.get(url)

    assert res.status_code == 200
    assert res.data["balance"] == 0

@pytest.mark.django_db
def test_balances_reflect_after_transaction(api):
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
    api.post(url, payload, format="json")

    url1 = reverse("account-balance", kwargs={"code": cash.code})
    url2 = reverse("account-balance", kwargs={"code": payable.code})
    res1 = api.get(url1)
    res2 = api.get(url2)

    assert res1.status_code == 200
    assert res2.status_code == 200

    assert res1.data["balance"] == 1500
    assert res2.data["balance"] == -1500
