from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from ..models import Alert, Channel, Program, ProgramInstance, Schedule
from .serializers import (
    AlertSerializer,
    ChannelSerializer,
    ProgramInstanceSerializer,
    ProgramSerializer,
    ScheduleSerializer,
)


class ChannelViewSet(viewsets.ModelViewSet):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer


class ProgramViewSet(viewsets.ModelViewSet):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer


class ProgramInstanceViewSet(viewsets.ModelViewSet):
    queryset = ProgramInstance.objects.all()
    serializer_class = ProgramInstanceSerializer


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer

    @action(detail=True, methods=["post"])
    def reorder(self, request, pk=None):
        """Endpoint to receive drag&drop reorder updates for a daily schedule item.
        Expected payload: {'order': 2, 'scheduled_start': '2025-11-25T14:00:00Z'}
        """
        schedule = self.get_object()
        data = request.data
        order = data.get("order")
        start = data.get("scheduled_start")
        if order is not None:
            schedule.order = int(order)
        if start:
            schedule.program_instance.scheduled_start = start
            # if end not provided compute using default_duration
            if not data.get("scheduled_end"):
                schedule.program_instance.scheduled_end = (
                    schedule.program_instance.scheduled_start + schedule.program_instance.program.default_duration
                )
            else:
                schedule.program_instance.scheduled_end = data.get("scheduled_end")
            schedule.program_instance.save()
        schedule.save()
        return Response({"ok": True})


class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all().order_by("-created_at")
    serializer_class = AlertSerializer

    @action(detail=False, methods=["post"], permission_classes=[IsAdminUser])
    def run_scan(self, request):
        """Trigger the alert scan task (enqueued via Celery).
        Returns the Celery task id when enqueued.
        """
        try:
            from ..tasks import check_alerts_task

            task = check_alerts_task.apply_async()
            return Response(
                {"ok": True, "task_id": task.id},
                status=status.HTTP_202_ACCEPTED,
            )
        except Exception as e:
            return Response(
                {"ok": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def send_email(self, request, pk=None):
        """Enqueue sending this alert via email (admin only)."""
        alert = self.get_object()
        try:
            from ..tasks import send_alert_email

            task = send_alert_email.apply_async(args=[alert.id])
            return Response({"ok": True, "task_id": task.id}, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({"ok": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
