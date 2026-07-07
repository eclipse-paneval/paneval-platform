from typing import List, Dict, Any

import jwt
from django.db.models import QuerySet
from django.http import HttpRequest

from . import models
from ..user.models import User


def get_subjective_tasks(eva: models.Evaluation) -> List[models.Dataset]:
    results: List[models.Dataset] = []
    queryset = models.Dataset.objects.filter(pk__in=eva.datasets)
    for item in queryset:
        if not item.is_objective:
            results.append(item)

    return results


def load_datasets(user: User, include_deleted=False) -> QuerySet[models.Dataset]:
    from django.contrib.auth.models import AnonymousUser

    kwargs: Dict[str, Any] = {}
    if not include_deleted:
        kwargs.update(deleted_at=None)
    if isinstance(user, AnonymousUser) or not user.is_researcher:
        kwargs.update(only_researcher=False)

    return models.Dataset.objects.filter(**kwargs).all()


def filter_user(request: HttpRequest, queryset: QuerySet) -> QuerySet:
    if not request.user.is_staff:  # type: ignore
        return queryset.filter(user_id=request.user.pk)
    return queryset
