from rest_framework import serializers

from ..models import Alert, Channel, Program, ProgramInstance, Schedule


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ("id", "name", "code", "program_type", "latitude", "longitude", "timezone")


class ProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
        fields = (
            "id",
            "title",
            "subtitle",
            "description",
            "channel",
            "genres",
            "target_audiences",
            "default_duration",
            "broadcast_type",
            "program_origin",
            "media_source",
            "is_live",
            "is_repeatable",
            "is_active",
            "evaluation_required",
            "evaluation_status",
            "fixed_on_clock",
        )


class ProgramInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramInstance
        fields = (
            "id",
            "program",
            "episode_number",
            "episode_title",
            "episode_description",
            "scheduled_start",
            "scheduled_end",
            "status",
            "submitted_at",
            "approved_at",
        )


class ScheduleSerializer(serializers.ModelSerializer):
    program_instance = ProgramInstanceSerializer()

    class Meta:
        model = Schedule
        fields = ("id", "channel", "schedule_date", "order", "program_instance", "locked")


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = ("id", "trigger", "schedule", "message", "method", "sent", "created_at")
