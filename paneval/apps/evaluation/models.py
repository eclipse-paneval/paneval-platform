"""Models for evaluation."""
from typing import List

from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _



class Evaluation(models.Model):
    """Evalution db model."""
    class Sence(models.TextChoices):
        """Types of task."""

        API = "EA", _("API Evaluate")
        MODEL = "EM", _("Model Evaluate")
        TRAIN = "TM", _("Model Train")

    class Domain(models.TextChoices):
        """Domains."""
        NLP = "N", _("NLP")
        MULTI = "M", _("Multimodel")

    class ModelType(models.TextChoices):
        """Model Types."""
        NONE = "", _("None")
        BASE = "Base", _("Base")
        SFT = "SFT", _("SFT")
        BACKBONE = "Backbone", _("Backbone")
        FINE_TUNING = "Fine-tuning", _("Fine-tuning")
        DIRECT_MODEL = "direct-model", _("direct-model")
        CHAT = "Chat", _("Chat")

    class ImageType(models.TextChoices):
        BUILTIN = "B", _("Builtin")
        USER = "U", _("User")

    user_id = models.BigIntegerField(db_index=True)
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(default='')
    model = models.CharField(max_length=100, default='BAAI/chat-glm-130b')
    sence = models.CharField(
        max_length=2,
        choices=Sence.choices,
    )
    domain = models.CharField(
        max_length=2,
        choices=Domain.choices,
    )
    llm_parameters = models.FloatField(default=0)  # Billion
    paper_url = models.CharField(max_length=200, default='')
    model_url = models.CharField(max_length=200, default='')
    url = models.CharField(max_length=256, default='')
    online_model_name = models.CharField(max_length=256, default='')
    online_api_key = models.CharField(max_length=256, default='')
    online_property = models.JSONField(default=dict)
    accelerator_model = models.CharField(max_length=40, default='')
    model_type = models.CharField(
        max_length=30, default=ModelType.NONE,
        choices=ModelType.choices,

    )

    base_model_token_size = models.CharField(max_length=100, default='')
    base_model_name = models.CharField(max_length=200, default='')
    sft_data_size = models.CharField(max_length=100, default='')

    tokenizer = models.JSONField(default=None, null=True)
    pretrained_tokenizer_id = models.BigIntegerField(default=0)
    revision = models.BigIntegerField(default=0)


    master_count = models.BigIntegerField(default=0)
    master_type = models.BigIntegerField(default=0)
    worker_count = models.BigIntegerField(default=0)
    worker_type = models.BigIntegerField(default=0)
    master_resource = models.JSONField(default=dict)
    worker_resource = models.JSONField(default=dict)

    anonymous = models.BooleanField(default=False)

    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(null=True)
    deleted_at = models.DateTimeField(null=True, db_index=True)

    sub_batchid = models.BigIntegerField(default=0)
    sub_admin_batchid = models.BigIntegerField(default=0)
    sub_at = models.DateTimeField(null=True)
    sub_updated_at = models.DateTimeField(null=True)
    organization = models.CharField(max_length=200, default='')
    datasets_config = models.JSONField(default=dict)
    include_robustness = models.BooleanField(default=True)
    environ_vars = models.JSONField(default=dict)
    leaderboard_lite = models.BooleanField(default=False)
    leaderboard_meta = models.JSONField(default=dict)
    model_gen_kwargs = models.CharField(max_length=200, default='')

    @cached_property
    def datasets(self) -> List[int]:
        """Wraps datasets."""
        if self.domain == self.Domain.MULTI:
            return [
            x.cv_id
            for x in CvTask.objects.filter(
                    eva_id=self.pk,
                    deleted_at=None,
            )
        ]
        elif self.domain == self.Domain.NLP:
            return [
                x.dataset_id
                for x in EvaluationTask.objects.filter(
                        eval_id=self.pk,
                        deleted_at=None,
                )
            ]
        return []

    @cached_property
    def owner(self):
        """Wraps to return owner."""
        from paneval.apps.user.models import User
        return User.objects.get(pk=self.user_id).name


class MmDataset(models.Model):
    cv_id = models.BigIntegerField(default=0)
    name = models.CharField(max_length=100)
    data = models.JSONField(default=dict)
    # 是否是鲁棒性数据集
    lbx = models.BigIntegerField(default=0)

class EvaluationTask(models.Model):
    """Evalution Tasks."""

    eval_id = models.BigIntegerField()
    dataset_id = models.BigIntegerField(default=0)
    deleted_at = models.DateTimeField(null=True)

    class Meta:
        """Options"""

        index_together = (
            ("eval_id", "deleted_at"),
        )


class Dataset(models.Model):
    """Evaluation Datasets."""

    class Scenario(models.TextChoices):
        """Scenario."""

        QA = "QA", _("QA")
        Classification = "C", _("Classification")
        Generation = "G", _("Generation")
        IR = "IR", _("IR")
        GQ = "GQ", _("Generation QA")
        Other = "O", _("Other")


    class Language(models.TextChoices):
        """Language."""

        EN = "en", _("English")
        ZH = "zh", _("Chinese")
        MU = "mu", _("Multiple")

    # Scenario of feam
    # Example: GenerationQA
    task = models.CharField(max_length=100)
    # Example: CLCC-H
    subject = models.CharField(max_length=100)
    # Example: Gaokao2023v2
    label = models.CharField(max_length=100, default='')
    # Example: 高考题目QA
    description = models.CharField(max_length=256)
    # Example: N
    domain = models.CharField(choices=Evaluation.Domain.choices, max_length=2)
    # Example: QA
    scenario = models.CharField(max_length=2, choices=Scenario.choices)
    # Example: zh
    language = models.CharField(max_length=2, choices=Language.choices)
    # Example: feam.scenario.nlp
    feam_group = models.CharField(max_length=20, default='feam.scenario.nlp')
    # Example: builtin.qa.zh
    feam_scenario = models.CharField(max_length=100, db_index=True, default='')
    # Example: gaokao
    feam_task_id = models.CharField(max_length=100, db_index=True, default='')
    is_objective = models.BooleanField(default=True)
    package = models.CharField(max_length=100, default='helm')
    only_researcher = models.BooleanField(default=False)
    leaderboard = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, db_index=True)


    @cached_property
    def tags(self):
        """Wraps tags."""
        return [
            x.tag
            for x in DatasetTag.objects.filter(dataset_id=self.pk)
        ]

    @cached_property
    def disturbances(self):
        return [
            {
                'name': x.name,
                'label': x.label,
                'description': x.description,
                'group': x.group,
                'opts': {
                    'method': x.method,
                    'reference_prefix': x.reference_prefix,
                },
            }
            for x in DatasetDisturbance.objects.filter(
                    deleted_at=None, dataset_id=self.pk,
            )
        ]

    @cached_property
    def key(self):
        return self.feam_scenario

    @cached_property
    def name(self):
        if self.label != '':
            return self.label

        if self.subject != '':
            return self.subject.upper()
        return self.task

    @cached_property
    def available(self) -> bool:
        return self.deleted_at is None


class ImageData(models.Model):
    md5 = models.CharField(max_length=50, db_index=True)
    data = models.BinaryField()


class DatasetDisturbance(models.Model):
    """Disturbance for robust."""

    class Method(models.TextChoices):
        Dataset = 'D', _('Dataset')
        ReferencePrefix = 'RefPre', _('Reference Prefix')

    class Group(models.TextChoices):
        Content = 'C', _('Content')
        Format = 'F', _('Format')

    dataset_id = models.BigIntegerField()
    name = models.CharField(max_length=200)
    method = models.CharField(
        max_length=20,
        default=Method.Dataset,
        choices=Method.choices,
    )
    reference_prefix = models.CharField(max_length=20, default='')
    label = models.CharField(max_length=200, default='')
    description = models.TextField(default='')
    group = models.CharField(max_length=1, choices=Group.choices, default=Group.Content)
    deleted_at = models.DateTimeField(null=True)

    class Meta:
        index_together = (
            ('deleted_at', 'dataset_id'),
        )

        unique_together = (
            ('dataset_id', 'name'),
        )


class DatasetTag(models.Model):
    """Tags of dataset."""

    class Tag(models.TextChoices):
        """Tags."""

        #: 常识
        commonsence = "CS", _("commonsence")

        #: 事实检测
        truthfulness = "TF", _("truthfulness")

        #: 匹配
        matching = "M", _("matching")

        #: 推理
        reasoning = "R", _("reasoning")

        #: 生成
        generation = "G", _("generation")

    dataset_id = models.BigIntegerField(db_index=True)
    tag = models.CharField(max_length=2, choices=Tag.choices)


class PretrainedTokenizer(models.Model):
    user_id = models.BigIntegerField(default=0, db_index=True)
    uuid = models.UUIDField(unique=True)
    ks3_key = models.CharField(max_length=200, unique=True)
    files_count = models.IntegerField(default=0)
    total_size_kb = models.BigIntegerField(default=0)
    updated_at = models.DateTimeField()
    created_at = models.DateTimeField()

class EvaShow(models.Model):
    name = models.CharField(max_length=200, unique=True)
    show = models.BooleanField(default=True)

class PretrainedTokenizerFile(models.Model):
    tokenizer_id = models.BigIntegerField(db_index=True)
    user_id = models.BigIntegerField(db_index=True)
    filename = models.CharField(max_length=200)
    created_at = models.DateTimeField()
    deleted_at = models.DateTimeField(null=True)

    class Meta:
        index_together = (
            ("tokenizer_id", "filename", "deleted_at"),
        )

class CvData(models.Model):
    # 前端显示的名称
    name = models.CharField(max_length=100)
    # 父节点名称
    parent_name = models.CharField(max_length=100)
    # json串，里面信息有数据信息。
    meta_data = models.CharField(max_length=3000)
    deleted_at = models.DateTimeField(null=True)



class CvTask(models.Model):
    # evaluation的id
    eva_id = models.BigIntegerField(db_index=True)
    # CvData的id, 或者是多模态的idx(0: 图问答, 1: 图像-文本匹配, 2: 文本生成图)
    cv_id = models.BigIntegerField()
    deleted_at = models.DateTimeField(null=True)


class CvTaskResult(models.Model):
    batch_id = models.BigIntegerField()
    # 通过cv_id 找到cvData. cv_id是-1时，代表鲁棒性
    cv_id = models.BigIntegerField(db_index=True)
    # status 状态。0: 启动，1 成功，-1 失败，2 运行中，3 取消, 99 待推理
    status = models.BigIntegerField(default=0)
    # 第几个数据集
    idx = models.BigIntegerField(default=0)

    result = models.CharField(max_length=9000, default="")
    result_json = models.JSONField(default=dict)

    # MmDataset的id
    mid = models.BigIntegerField(default=0)

    deleted_at = models.DateTimeField(null=True, db_index=True)


class SfTaskResult(models.Model):
    batch_id = models.BigIntegerField()
    # status 状态。0: 启动，1 成功，-1 失败，2 运行中
    status = models.BigIntegerField(default=0)
    # 第几个task
    idx = models.BigIntegerField(default=0)
    result = models.JSONField(default=dict)
