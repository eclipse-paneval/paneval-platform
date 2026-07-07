"""Models of Evaluations."""
import json
from typing import Dict, Any

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property


class Batch(models.Model):
    """Each run contains multiple scenarios."""

    class Status(models.TextChoices):
        """Status of Batch."""

        MODIFIED = 'M', _('MODIFIED')
        PENDING = 'P', _('Pending')
        PREPARING = 'PPR', _("Platform Preparing")
        ENQUEUED = 'PPE', _('Platform Pending')
        STARTING = 'PST', _("Platform Starting")
        SCHEDULING = 'PSC', _("Platform Scheduling")
        RUNNING = 'R', _('Running')
        DONE_INFERENCE = 'DI', _('Done Inference')   # 推理完成
        HUMAN_EVALUATING = 'HE', _('Human Evaluating') # 人工评测
        SUCCESS = 'S', _('Success')
        FAILURE = 'F', _('Failure')
        CANCEL = 'C', _("Cancel")

    SUCCESS_STATUSES = [
        Status.DONE_INFERENCE,
        Status.SUCCESS,
    ]

    RUNNING_STATUSES = [
        Status.PENDING,
        Status.PREPARING,
        Status.ENQUEUED,
        Status.STARTING,
        Status.SCHEDULING,
        Status.RUNNING,
    ]


    class FailureKind(models.TextChoices):
        SYSTEM = "SYS", _('System')
        MODEL = "MOD", _("Model")

    evaluation_id = models.BigIntegerField(db_index=True)
    sequence = models.BigIntegerField(default=0)
    try_sequence = models.IntegerField(default=0)
    user_id = models.BigIntegerField()
    celery_task_id = models.CharField(max_length=40, db_index=True)
    joint_job_id = models.CharField(max_length=40, default='')
    resource = models.JSONField()
    priority = models.CharField(max_length=20, default='high')
    submitted = models.BooleanField(default=False)
    results = models.JSONField(default=list)
    dry_run = models.BooleanField(default=False)

    model_storage_url = models.CharField(max_length=512, default='')
    model_id = models.BigIntegerField(default=0)
    model_revision = models.BigIntegerField(default=0)
    dags_ready = models.BooleanField(default=True)
    dags_delayed_tasks = models.JSONField(default=dict)

    status = models.CharField(
        max_length=3,
        choices=Status.choices,
        default=Status.FAILURE,
    )

    failure_kind = models.CharField(
        max_length=3,
        choices=FailureKind.choices,
        null=True,
    )
    failure_details = models.TextField(null=True)

    include_robustness = models.BooleanField(default=True)

    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(null=True)

    datasets_config = models.JSONField(default=dict)

    nlp_trending = models.JSONField(default=dict)


    class Meta:
        """Meta."""

        index_together = (
            ('user_id', 'created_at'),
        )

    @cached_property
    def owner(self):
        """Wraps to return owner."""
        from paneval.apps.user.models import User
        return User.objects.get(pk=self.user_id).name


class DAG(models.Model):
    """DAG model."""

    evaluation_id = models.BigIntegerField(default=0)
    batch_id = models.BigIntegerField()
    scenario_entry_point = models.CharField(max_length=40, default='')
    dataset_id = models.BigIntegerField(default=0)
    run_entry = models.CharField(max_length=512)
    disturbance = models.CharField(max_length=200, default='')  # empty is accuracy
    disturbance_opts = models.JSONField(default=dict)
    celery_task_id = models.CharField(max_length=40, db_index=True)
    result = models.JSONField()
    status = models.CharField(
        max_length=3,
        choices=Batch.Status.choices,
    )
    delayed_uuid = models.UUIDField(null=True, editable=False)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(null=True)

    started_at = models.BigIntegerField(null=True)
    stopped_at = models.BigIntegerField(null=True)
    metrics = models.JSONField(default=dict)

    deleted_at = models.DateTimeField(null=True, db_index=True)

    class Meta:
        """Meta."""

        unique_together = (
            ('batch_id', 'run_entry', 'disturbance'),
        )
        index_together = (
            ('batch_id', 'scenario_entry_point', 'dataset_id'),
        )

    @cached_property
    def dag_id(self) -> str:
        if self.delayed_uuid is not None:
            return str(self.delayed_uuid)
        return str(self.pk)


class DatasetResult(models.Model):
    """Result of dataset in a batch."""

    batch_id = models.BigIntegerField()
    dataset_id = models.BigIntegerField()
    disturbance = models.CharField(max_length=200, default='')  # empty is accuracy
    scenario_entry_point = models.CharField(max_length=40, default='')
    result = models.JSONField(default=list)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(null=True)

    started_at = models.BigIntegerField(null=True)
    stopped_at = models.BigIntegerField(null=True)
    total_instances = models.BigIntegerField(null=True)
    avg_elapsed = models.BigIntegerField(null=True)
    max_elapsed = models.BigIntegerField(null=True)

    class Meta:
        """Options of model."""

        index_together = (
            ("batch_id", "dataset_id", "disturbance"),
        )
