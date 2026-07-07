"""Serializers."""

from rest_framework import serializers

from . import models


class Batch(serializers.ModelSerializer):
    """Batch."""

    class Meta:
        """Meta."""

        model = models.Batch
        fields = (
            "id", "evaluation_id", "user_id", "celery_task_id",
            "joint_job_id", "status", "joint_job_id", "sequence",
            "dry_run", "failure_kind", "failure_details",
            "submitted", "created_at", "updated_at",
            "owner", "resource", "priority", "model_revision", "model_id",
            "include_robustness", "try_sequence", "nlp_trending",
        )


class DAG(serializers.ModelSerializer):
    """DAG."""

    class Meta:
        """Meta."""

        model = models.DAG
        fields = (
            "id", "run_entry", "celery_task_id", "dataset_id",
            "disturbance", "status", "created_at", "updated_at",
            "started_at",
            "stopped_at",
        )


class BatchCreation(serializers.Serializer):
    dry_run = serializers.BooleanField(required=False)
    priority = serializers.ChoiceField(
        choices=[
            "high", "medium", "low",
        ],
        required=False
    )


class BatchDags(serializers.Serializer):
    datasets = serializers.ListField(child=serializers.IntegerField(), required=True)
    include_robustness = serializers.BooleanField(required=False)
    datasets_config = serializers.ListField(child=serializers.DictField(), required=False)
