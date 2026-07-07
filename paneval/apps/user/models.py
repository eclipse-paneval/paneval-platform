"""Model for users."""
from django.db import models
from django.db.models import F
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property


class User(AbstractUser):
    """User model."""

    class Status(models.TextChoices):
        """Status."""

        INCOMPLETE = 'I', _('INCOMPLETE')
        PENDING = 'P', _('Pending')
        APPROVED = 'A', _('Approved')
        DENIED = 'D', _('Denied')

    country_code = models.CharField(max_length=5, default='+86')
    phone = models.CharField(max_length=20)
    name = models.CharField(max_length=40, default='')
    organization = models.CharField(max_length=128, default='')
    organization_en = models.CharField(max_length=128, default='')
    team_id = models.BigIntegerField(default=0)

    feishu_id = models.CharField(max_length=200, default='')

    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default='I',
    )
    user_center = models.JSONField(default=dict)
    is_private_model = models.BooleanField(default=False)
    created_at = models.DateTimeField(db_index=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, db_index=True)
    deleted_at = models.DateTimeField(null=True, db_index=True)
    eva_count = models.IntegerField(default=5)
    eva_used = models.IntegerField(default=0)

    mark_count = models.IntegerField(default=2)
    mark_used = models.IntegerField(default=0)

    is_researcher = models.BooleanField(default=False)


    class Meta:
        """Make multiple fields unique."""

        unique_together = ('country_code', 'phone')

    @cached_property
    def tasks(self):
        return [x.task for x in UserTask.objects.filter(user_id=self.pk, deleted_at=None)]

    @cached_property
    def eva_length(self):
        return self.eva_count - self.eva_used

    @cached_property
    def available_mark_count(self) -> int:
        return self.mark_count - self.mark_used

    def incr_mark_used(self) -> bool:
        return User.objects.filter(
            pk=self.pk,
            mark_used__lt=F('mark_count'),
        ).update(
            mark_used=F('mark_used') + 1,
        ) == 1

    @cached_property
    def huggingface(self):
        item = UserSocialAccount.objects.filter(
            user_id=self.pk,
            social_platform=UserSocialAccount.SocialPlat.HUGGINGFACE,
        ).first()
        if item is None:
            return None
        return f'https://huggingface.co/{item.social_open_id}'

    @cached_property
    def sa_email(self):
        item = UserSocialAccount.objects.filter(
            user_id=self.pk,
            social_platform=UserSocialAccount.SocialPlat.EMAIL,
        ).first()

        if item is None:
            return None

        return item.social_open_id

    @cached_property
    def sa_username(self):
        item = UserSocialAccount.objects.filter(
            user_id=self.pk,
            social_platform=UserSocialAccount.SocialPlat.USERNAME,
        ).first()

        if item is None:
            return None

        return item.social_open_id


class UserSocialAccount(models.Model):
    """Bind WeChat openid to a user."""

    class SocialPlat(models.TextChoices):
        """Social Platforms."""

        WECHAT = 'WX', _('WeChat')
        EMAIL = 'EM', _('Email')
        USERNAME = 'UN', _('Username')
        HUGGINGFACE = 'HF', _("HuggingFace")
        OPENID_CONNECT = 'OC', _("OpenID Connect")

    user_id = models.BigIntegerField(db_index=True)
    social_platform = models.CharField(
        max_length=2,
        choices=SocialPlat.choices,
    )

    # WeChat OpenID, Email address, etc.
    social_open_id = models.CharField(max_length=100)

    password = models.CharField(max_length=64, default='')
    password_salt = models.CharField(max_length=16, default='')
    extras = models.JSONField(default=dict)

    updated_at = models.DateTimeField(null=True, default=None)
    created_at = models.DateTimeField()

    class Meta:
        """Make multiple fields unique."""

        unique_together = (
            ('user_id', 'social_platform'),
            ('social_platform', 'social_open_id')
        )

    def to_field(self) -> str:
        """Convert to fields in user."""
        if self.social_platform == self.SocialPlat.WECHAT:
            return "wechat"
        if self.social_platform == self.SocialPlat.USERNAME:
            return "username"
        if self.social_platform == self.SocialPlat.EMAIL:
            return "email"
        if self.social_platform == self.SocialPlat.OPENID_CONNECT:
            return "openid_connect"


class UserTask(models.Model):
    """User tasks."""

    class Sence(models.TextChoices):
        """Types of task."""

        API = "EA", _("API Evaluate")
        MODEL = "EM", _("Model Evaluate")
        TRAIN = "TM", _("Model Train")

    user_id = models.BigIntegerField()
    task = models.CharField(
        max_length=2,
        choices=Sence.choices,
    )

    deleted_at = models.DateTimeField(null=True)


    class Meta:
        """Make multiple fields unique."""

        index_together = ('user_id', 'deleted_at')
