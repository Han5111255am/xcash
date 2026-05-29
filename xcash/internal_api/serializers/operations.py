from rest_framework import serializers

from withdrawals.models import WithdrawalReviewLog


class WithdrawalReviewLogSerializer(serializers.ModelSerializer):
    withdrawal_sys_no = serializers.CharField(source="withdrawal.sys_no", read_only=True)
    actor = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = WithdrawalReviewLog
        fields = [
            "id",
            "withdrawal_sys_no",
            "actor",
            "action",
            "from_review_status",
            "to_review_status",
            "note",
            "created_at",
        ]
