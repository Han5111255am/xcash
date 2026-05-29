from internal_api.authentication import InternalTokenAuthentication
from internal_api.serializers.operations import WithdrawalReviewLogSerializer
from rest_framework.mixins import ListModelMixin
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from withdrawals.models import WithdrawalReviewLog


class WithdrawalReviewLogViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    authentication_classes = [InternalTokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = WithdrawalReviewLogSerializer

    def get_queryset(self):
        return WithdrawalReviewLog.objects.filter(
            project__appid=self.kwargs["project_appid"]
        ).select_related("withdrawal", "actor").order_by("-created_at")
