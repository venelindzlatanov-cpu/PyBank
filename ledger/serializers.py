from rest_framework import serializers
from .models import Account, Transaction, Posting


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["id", "code", "name", "type", "created_at"]


class TransactionCreateSerializer(serializers.Serializer):
    external_id = serializers.CharField(max_length=64)
    idempotency_key = serializers.CharField(max_length=64)
    amount = serializers.IntegerField(min_value=1)  # minor units; must be positive
    currency = serializers.CharField(max_length=3)
    debit_account = serializers.CharField(max_length=32)
    credit_account = serializers.CharField(max_length=32)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["debit_account"] == attrs["credit_account"]:
            raise serializers.ValidationError("Debit and credit accounts must be different.")
        return attrs


class PostingSerializer(serializers.ModelSerializer):
    account_code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Posting
        fields = ["id", "account", "account_code", "amount", "created_at"]
        read_only_fields = ["account", "amount", "created_at"]


class TransactionSerializer(serializers.ModelSerializer):
    postings = PostingSerializer(many=True, read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id", "external_id", "idempotency_key", "amount", "currency",
            "description", "status", "created_at", "updated_at", "postings"
        ]
