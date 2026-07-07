"""Serializers."""
from os import environ
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from . import models


class Evaluation(serializers.ModelSerializer):
    """Evaluation."""
    name = serializers.CharField(
        required=True,
        min_length=3,
        max_length=128,
    )

    url = serializers.URLField(required=False, allow_blank=True)
    online_model_name = serializers.CharField(required=False, allow_blank=True)
    online_api_key = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(max_length=256, allow_blank=True)
    datasets = serializers.ListField(child=serializers.IntegerField(), required=False, default=[])
    owner = serializers.CharField(allow_blank=True, required=False)
    model = serializers.CharField(required=False, allow_blank=True)
    paper_url = serializers.URLField(required=False, allow_blank=True)
    model_url = serializers.URLField(required=False, allow_blank=True)

    base_model_token_size = serializers.CharField(allow_blank=True, required=False)
    base_model_name = serializers.CharField(allow_blank=True, required=False)
    sft_data_size = serializers.CharField(allow_blank=True, required=False)

    tokenizer = serializers.DictField(required=False, default=None)
    model_id = serializers.IntegerField(required=False)
    model_revision = serializers.IntegerField(required=False)
    model_token = serializers.CharField(required=False)

    datasets_config = serializers.ListField(required=False)
    include_robustness = serializers.BooleanField(required=False)

    environ_vars = serializers.DictField(required=False, default=dict)
    model_gen_kwargs = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        """Speicify model."""

        model = models.Evaluation
        fields = (
            'id',
            'user_id', 'url', 'online_model_name', 'online_api_key',
            'name', 'description', 'sence', 'domain', 'model',
            'llm_parameters', 'paper_url', 'model_url',
            'created_at',
            'datasets',
            'owner',
            'accelerator_model',
            'model_type',
            'base_model_token_size',
            'base_model_name',
            'sft_data_size',
            'tokenizer',
            'pretrained_tokenizer_id',
            'model_id',
            'model_revision',
            'model_token',
            'sub_batchid',
            "master_count",
            "master_resource",
            "master_type",
            "worker_count",
            "worker_resource",
            "worker_type",
            "datasets_config",
            "include_robustness",
            "environ_vars",
            "model_gen_kwargs",
        )

    def validate_pretrained_tokenizer_id(self, value):
        request = self.context.get('request')
        if request is None:
            return value
        tokenizer = models.PretrainedTokenizer.objects.filter(
            pk=value,
            user_id=request.user.pk,
        ).first()
        if tokenizer is None:
            raise serializers.ValidationError(_('No such custom tokenizer'))
        if tokenizer.files_count == 0:
            raise serializers.ValidationError(_('Custom tokenizer has NO file been uploaded'))
        return value


class Dataset(serializers.ModelSerializer):
    """Dataset."""

    class Meta:
        """Speicify model."""

        model = models.Dataset
        fields = (
            'id', 'task', 'subject', 'label', 'domain', 'scenario',
            'language', 'tags', 'key', 'name', "is_objective",
            'package',
            'disturbances', 'available', "leaderboard", 'description',

        )


class PretrainedTokenizer(serializers.ModelSerializer):
    ks3_key = serializers.CharField(required=False, allow_blank=True)
    uuid = serializers.UUIDField(required=False)

    class Meta:
        model = models.PretrainedTokenizer
        fields = (
            "id", "ks3_key", "uuid",
        )

class PretrainedTokenizerFile(serializers.ModelSerializer):
    class Meta:
        model = models.PretrainedTokenizerFile
        fields = (
            "id", "tokenizer_id", "filename", "created_at",
        )
