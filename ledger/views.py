# package: ledger.views
from django.db import transaction as db_tx
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Account, Transaction, Posting
from .serializers import (
    AccountSerializer,
    TransactionSerializer,
    TransactionCreateSerializer,
)


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all().order_by("code")
    serializer_class = AccountSerializer
    lookup_field = "code"

    @action(detail=True, methods=["get"])
    def balance(self, request, *args, **kwargs):
        account = self.get_object()
        total = (Posting.objects
                 .filter(account=account)
                 .aggregate(total=Sum("amount"))["total"] or 0)
        return Response(data={"code": account.code, "balance": total}, status=200)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read transactions and initiate a new one via a custom action.
    """
    queryset = Transaction.objects.all().order_by("-created_at")
    serializer_class = TransactionSerializer

    @action(detail=False, methods=["post"])
    def initiate(self, request):
        # validate input
        payload = TransactionCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data

        # idempotency: if key already exists, return existing tx
        existing = Transaction.objects.filter(idempotency_key=data["idempotency_key"]).first()
        if existing:
            ser = TransactionSerializer(existing)
            return Response(ser.data, status=status.HTTP_200_OK)

        # resolve accounts
        debit_acc = get_object_or_404(Account, code=data["debit_account"])
        credit_acc = get_object_or_404(Account, code=data["credit_account"])

        # atomic write of parent + postings
        with db_tx.atomic():
            tx = Transaction.objects.create(
                external_id=data["external_id"],
                idempotency_key=data["idempotency_key"],
                amount=data["amount"],
                currency=data["currency"].upper(),
                description=data.get("description", ""),
                status="SETTLED",
            )
            Posting.objects.create(transaction=tx, account=debit_acc, amount=+data["amount"])
            Posting.objects.create(transaction=tx, account=credit_acc, amount=-data["amount"])

            # Extra safety check
            if sum(p.amount for p in tx.postings.all()) != 0:
                raise ValueError("Unbalanced postings for transaction")

        ser = TransactionSerializer(tx)
        return Response(ser.data, status=status.HTTP_201_CREATED)
