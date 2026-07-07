"""Views."""
import os
import uuid
from typing import Dict, Any, Optional

from django.core.files import File
from django.db import transaction
from django.http import HttpResponse
from django.http import JsonResponse as DJsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from paneval import storage
from paneval.apps.evaluation import executor
from rest_framework import generics, views, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response as JsonResponse

from .utils import filter_user
from ..user import models as user_model
from ..cem.models import Batch
from . import models, serializers, utils


class Evaluation(generics.ListCreateAPIView):
    """List evalutions."""

    permission_classes = [IsAuthenticated]
    serializer_class = serializers.Evaluation

    def get_queryset(self):
        """Filter queryset."""
        kwargs: Dict[str, Any] = dict(
            deleted_at__isnull=True,
        )
        create_user = self.request.GET.get('create_user', None)
        model_name = self.request.GET.get('model_name', None)
        me = self.request.GET.get('me', "0")
        # 管理员用户，选择了只看自己的
        if me == "1":
            kwargs.update(user_id=self.request.user.pk)
        # 管理员用户，用户名查询
        elif create_user is not None:
            us = user_model.User.objects.filter(name__icontains=create_user)
            ids = []
            for item in us:
                ids.append(item.id)
            kwargs.update(user_id__in=ids)
            pass
        # 管理员用户，模型名称查询
        if model_name is not None:
            kwargs.update(name__icontains=model_name)
        domain = self.request.GET.get('domain', None)
        if domain:
            kwargs.update(domain=domain)
        return filter_user(self.request, models.Evaluation.objects.filter(**kwargs)).order_by("-id")

    def create(self, request):
        """Create a evalution."""
        data = request.data
        data["user_id"] = request.user.pk
        data["created_at"] = timezone.now()
        serializer = serializers.Evaluation(
            data=data,
            context={'request': request},
        )
        if serializer.is_valid():
            valid_data: Dict[str, Any] = serializer.data # type: ignore
            if (
                models.Evaluation.objects.filter(
                    name=valid_data["name"],
                    deleted_at=None,
                ).first()
                is not None
            ):  # noqa
                return JsonResponse(
                    {"detail": _("Model name has been taken.")},
                    status=400,
                )
            datasets = valid_data.pop("datasets")
            with transaction.atomic():
                eva = models.Evaluation.objects.create(
                    **valid_data,
                )

                if eva.domain == models.Evaluation.Domain.MULTI:
                    for dataset_id in datasets:
                        models.CvTask.objects.create(
                            eva_id=eva.pk,
                            cv_id=dataset_id,
                        )
                else:
                    for dataset_id in datasets:
                        models.EvaluationTask.objects.create(
                            eval_id=eva.pk,
                            dataset_id=dataset_id,
                        )
            ser = serializers.Evaluation(eva)
            return JsonResponse(ser.data, status=201)
        return JsonResponse(serializer.errors, status=400)


class EvaluationViewSet(viewsets.ViewSet):
    """ViewSet to retrieve/update/delete evaluation."""

    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None):
        """Retrieve."""
        eva = self._get_obj(request, pk, retrieve=True)
        serializer = serializers.Evaluation(eva)
        return JsonResponse(serializer.data, status=200)

    def _get_obj(self, request, pk=None, retrieve=False) -> models.Evaluation:
        queryset = models.Evaluation.objects.all()
        queryset = filter_user(request, queryset)
        eva = get_object_or_404(queryset, pk=pk)
        return eva

    def update(self, request, pk=None):
        """Update."""
        eva = self._get_obj(request, pk)
        assert eva.user_id == request.user.pk
        data = request.data
        data["user_id"] = request.user.pk
        data["created_at"] = eva.created_at
        serializer = serializers.Evaluation(
            data=request.data,
            context={'request': request},
        )
        if serializer.is_valid():
            eva.pretrained_tokenizer_id = 0    # reset to 0
            eva.revision += 1
            with transaction.atomic():
                for k in (
                    "description",
                    "domain",
                    "url",
                    "model",
                    "paper_url",
                    "model_url",
                    "llm_parameters",
                    "model_type",
                    "base_model_token_size",
                    "base_model_name",
                    "sft_data_size",
                    "tokenizer",
                    "pretrained_tokenizer_id",
                    "datasets_config",
                    'environ_vars',
                    "include_robustness",
                    'online_model_name',
                    'online_api_key',
                ):
                    if k in serializer.data:
                        setattr(eva, k, serializer.data[k])

                eva.updated_at = timezone.now()

                if eva.domain == models.Evaluation.Domain.MULTI:
                    models.CvTask.objects.filter(
                        eva_id=eva.pk,
                        deleted_at=None,
                    ).update(deleted_at=timezone.now())
                    for dataset_id in serializer.data["datasets"]:
                        try:
                            models.MmDataset.objects.get(pk=dataset_id)
                            models.CvTask.objects.create(
                                eva_id=eva.pk,
                                cv_id=dataset_id,
                            )
                        except models.MmDataset.DoesNotExist:
                            return JsonResponse(
                                {
                                    "detail": _("No such dataset"),
                                    "datasetId": dataset_id,
                                },
                                status=400,
                            )
                else:
                    models.EvaluationTask.objects.filter(
                        eval_id=eva.pk,
                        deleted_at=None,
                    ).update(deleted_at=timezone.now())
                    dataset_filter: Dict[str, Any] = dict(deleted_at=None)
                    if not request.user.is_researcher:
                        dataset_filter.update(only_researcher=False)
                    for dataset_id in serializer.data["datasets"]:
                        try:
                            models.Dataset.objects.get(
                                pk=dataset_id, **dataset_filter,
                            )
                        except models.Dataset.DoesNotExist:
                            return JsonResponse(
                                {
                                    "detail": _("No such dataset"),
                                    "datasetId": dataset_id,
                                },
                                status=400,
                            )

                        models.EvaluationTask.objects.create(
                            eval_id=eva.pk,
                            dataset_id=dataset_id,
                        )
                eva.revision += 1
                eva.save()
            eva_ser = serializers.Evaluation(eva)
            return JsonResponse(eva_ser.data, status=200)
        return JsonResponse(serializer.errors, status=400)

    def destroy(self, request, pk=None):
        """Delete."""
        obj = self._get_obj(request, pk)
        assert obj.user_id == request.user.pk
        obj.deleted_at = timezone.now()
        obj.save()
        return HttpResponse(status=204)


class Dataset(generics.ListAPIView):
    """Dataset."""

    permission_classes = [AllowAny]
    serializer_class = serializers.Dataset
    pagination_class = None

    def get_queryset(self):
        return utils.load_datasets(self.request.user, include_deleted=True)


def list_mmdata(request):
    ds = models.CvData.objects.filter(parent_name='')
    a = []
    a0 = {}
    for item in ds:
        a.append(item.pk)
        a0[item.pk] = item.name
    datas = models.MmDataset.objects.filter(cv_id__in=a, lbx=0)
    res0 = {}
    res = []
    for item in a:
        res0[item] = []
    for item in datas:
        if item.data.get("lbx", 0) == 0:
            if "dataset_show" in item.data:
                item.data["datasetShow"] = item.data["dataset_show"]
                del item.data["dataset_show"]
            item.data["datasetShow"] = item.name
        item.data["id"] = item.pk
        if item.data.get("is_admin", 0) == 0 or (item.data.get("is_admin", 0) == 1 and request.user.is_staff):
            is_show = True
        else:
            is_show = False
        if is_show:
            if ("description" not in item.data) or item.data["description"] == "非榜单任务":
                item.data["leaderboard"] = False
            else:
                item.data["leaderboard"] = True
            item.data["description"] = ""
            res0[item.cv_id].append(item.data)
    for k, v in res0.items():
        if len(v) > 0:
            res.append({"id": k, "name": a0[k], "data": v})
    return DJsonResponse(data=res, status=200, json_dumps_params={"ensure_ascii": False}, safe=False)


class Tokenizer(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def retrieve(self, request):
        results = [
            {
                "id": "gpt2",
                "tokenizerName": "gpt2",
                "maxSequenceLength": 2048,
                "endOfTextToken": "</s>",
                "prefixToken": "",
            },
            {
                "id": "tiiuae/falcon-7b",
                "tokenizerName": "tiiuae/falcon-7b",
                "maxSequenceLength": 2048,
                "endOfTextToken": "</s>",
                "prefixToken": "",
            },
            {
                "id": "THUDM/chatglm2-6b",
                "tokenizerName": "THUDM/chatglm2-6b",
                "maxSequenceLength": 2048,
                "endOfTextToken": "</s>",
                "prefixToken": "",
            },
            {
                "id": "TsinghuaKEG/ice",
                "tokenizerName": "TsinghuaKEG/ice",
                "maxSequenceLength": 2048,
                "endOfTextToken": "</s>",
                "prefixToken": "",
            },
        ]
        return JsonResponse({"results": results})

    def create(self, request, format=None):
        ser = serializers.PretrainedTokenizer(data=request.data)
        if not ser.is_valid():
            return JsonResponse(
                ser.errors,
                status=400
            )

        uuid1 = uuid.uuid1()
        t = models.PretrainedTokenizer(
            user_id=request.user.pk,
            uuid=uuid1.hex,
            ks3_key=f'pretrained-tokenizers/{uuid1}',
            updated_at=timezone.now(),
            created_at=timezone.now(),
        )
        t.save()
        ser = serializers.PretrainedTokenizer(t)
        return JsonResponse(ser.data, status=201)


class TokenizerUploadView(views.APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int, format=None):
        queryset = models.PretrainedTokenizer.objects.all()
        t = get_object_or_404(queryset, pk=pk, user_id=request.user.pk)
        fobj: File = request.data['file']
        t.total_size_kb += fobj.size / 1024
        t.files_count += 1
        if t.total_size_kb >= 1024 * 20:
            return JsonResponse(
                {"detail": _("Tokenizer's size is exceeded 20M.")},
                status=400,
            )
        if fobj.file is None:
            raise RuntimeError("none file")

        if fobj.name is None:
            return JsonResponse(
                {"detail": _("Filename is required.")},
                status=400,
            )

        with transaction.atomic():
            models.PretrainedTokenizerFile.objects.filter(
                tokenizer_id=pk,
                filename=fobj.name,
                deleted_at=None,
            ).update(
                deleted_at=None,
            )
            models.PretrainedTokenizerFile.objects.create(
                tokenizer_id=pk,
                user_id=request.user.pk,
                filename=fobj.name,
                created_at=timezone.now(),
            )
            key = os.path.join(t.ks3_key, fobj.name)
            storage.store.upload(key, fobj.file)
            t.updated_at = timezone.now()
            t.save()
        ser = serializers.PretrainedTokenizer(t)
        return JsonResponse(ser.data, status=201)


class TokenizerListFilesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.PretrainedTokenizerFile
    pagination_class = None

    @staticmethod
    def get_tokenizer(request, eval_id: int) -> models.PretrainedTokenizer:
        kwargs = {}
        if not request.user.is_staff:  # type: ignore
            kwargs['user_id'] = request.user.pk
        eva = get_object_or_404(
            models.Evaluation.objects.all(),
            pk=eval_id,
            **kwargs,
        )
        return get_object_or_404(models.PretrainedTokenizer, pk=eva.pretrained_tokenizer_id)

    def get_queryset(self):
        pt = self.get_tokenizer(self.request, self.kwargs['eval_id'])
        return models.PretrainedTokenizerFile.objects.filter(tokenizer_id=pt.pk)


class TokenizerFileContentView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def retrieve(self, request, *, eval_id: int, pk: int):
        pt = TokenizerListFilesView.get_tokenizer(request, eval_id)
        f = get_object_or_404(
            models.PretrainedTokenizerFile.objects.all(),
            tokenizer_id=pt.pk,
            pk=pk,
        )
        ks3_key = os.path.join(pt.ks3_key, f.filename)
        key = storage.store.get_key(ks3_key)
        if key is None:
            return JsonResponse(
                {'detail': _('File DO NOT found on our server')},
                status=500,
            )
        content = key.read()
        is_binary = True
        try:
            content = content.decode('utf-8')
            is_binary = False
        except:  # noqa
            pass

        return JsonResponse({'results': content, 'is_binary': is_binary},)


class GetImg(viewsets.ViewSet):
    def get(self, request):
        md5 = request.GET.get("md5")
        try:
            i = models.ImageData.objects.get(md5=md5)
            response = HttpResponse(content_type='image/jpeg')
            response.write(i.data)
            return response
        except models.ImageData.DoesNotExist:
            return HttpResponse(status=204)


class BatchProgress(viewsets.ViewSet):
    """Retrieve logs of batch."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        batch_id = self.request.GET.get('batch_id', None)
        print("= = ka", batch_id)
        if batch_id is None:
            return JsonResponse(
                {
                    "detail": "batch id is None",
                },
                status=400,
            )
        batch = get_object_or_404(
            Batch.objects.all(),
            pk=batch_id
        )
        if batch.status != Batch.Status.RUNNING:
            return JsonResponse(
                {
                    "detail": f"batch is not running({batch.status})",
                },
                status=400,
            )
        else:
            results: Optional[Dict[str, Any]] = executor.service.load_batch_status(batch_id, batch.try_sequence)
            totald = models.CvTaskResult.objects.filter(batch_id=batch.pk).count()
            curd = 0
            totalc = -1
            curc = 0
            if results is not None:
                for k, v in results["data"].items():
                    if v["ret"] == 1:
                        curd += 1
                    elif v["ret"] == 2 and "total" in v and "curi" in v:
                        totalc = v["total"]
                        curc = v["curi"]
            return DJsonResponse({
                "datasets": totald,
                "datasets_suc": curd,
                "datasets_progress": curd / totald,
                "curdataset": totalc,
                "curdataset_suc": curc,
                "curdataset_progress": curc / totalc
            })
