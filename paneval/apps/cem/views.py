"""Views of CEM."""
import logging
from typing import Dict, List, Any, Optional

from django.db import transaction
from django.db.models import Q, F
from django.http import HttpResponse, JsonResponse as DJsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response as JsonResponse

from . import models
from . import serializers
from .tasks import run_on_executor

from ..evaluation.models import Evaluation, CvTaskResult
from ..evaluation import executor
from ..evaluation.utils import filter_user
from .utils import merge_lbx, merge_lbx_config

logger = logging.getLogger(__name__)

class BatchList(generics.ListCreateAPIView):
    """Batches."""

    permission_classes = [IsAuthenticated]
    serializer_class = serializers.Batch

    def get_queryset(self):
        """Queryset."""
        kwargs = dict(
            deleted_at__isnull=True,
        )
        eva_queryset = filter_user(self.request, Evaluation.objects.filter(**kwargs))
        eva = get_object_or_404(eva_queryset, pk=self.kwargs['eval_id'])

        return models.Batch.objects.filter(evaluation_id=eva.pk).order_by("-id")

    def create(self, request, eval_id=None):
        """Create DAG."""

        eva_queryset = Evaluation.objects.filter(
            user_id=request.user.pk,
            deleted_at__isnull=True,
        )
        eva = get_object_or_404(eva_queryset, pk=eval_id)
        if self.has_incomplete_batch(eva.pk):
            return JsonResponse(
                {
                    "detail": _("A job is still running"),
                },
                status=400,
            )

        ser = serializers.BatchCreation(data=request.data)
        if not ser.is_valid():
            return JsonResponse(ser.errors, status=400)

        if not ser.data['dry_run'] and self._is_exceed(request):
            return JsonResponse(
                {
                    "detail": _("Started job number is exceed the quota of this month.")
                },
                status=400,
            )
        return self._create_api_batch(request, eva, ser.data['dry_run'])

    def _is_exceed(self, request) -> bool:
        return False

    def _create_api_batch(self, request, eva: Evaluation, dry_run: bool) -> JsonResponse:  # noqa
        priority = 'high'
        return self._create_job(
            request, eva, dry_run, priority=priority,
        )

    def _create_job(self, request, eva: Evaluation, dry_run: bool, priority: str) -> JsonResponse:  # noqa
        run_batch = self._create_run_batch(request, eva, dry_run, priority=priority)  # noqa
        result = run_on_executor.delay(run_batch.pk, run_batch.try_sequence)
        run_batch.celery_task_id = result.id
        run_batch.save()
        return JsonResponse({"id": result.id}, status=201)

    def _create_run_batch(
            self, request, eva: Evaluation, dry_run: bool, *,
            resource: Optional[Dict[str, Any]] = None,
            priority: str = 'high',
    ) -> models.Batch:  # noqa
        with transaction.atomic():
            run_batch = models.Batch(
                evaluation_id=eva.pk,
                user_id=request.user.pk,
                sequence=models.Batch.objects.filter(evaluation_id=eva.pk, dry_run=dry_run).count() + 1,  # noqa
                status=models.Batch.Status.PENDING,
                dry_run=dry_run,
                resource=resource or {},
                priority=priority,
                dags_ready=True,
                updated_at=timezone.now(),
                created_at=timezone.now(),
                datasets_config = eva.datasets_config,
                include_robustness=eva.include_robustness,
            )

            run_batch.save()
            if not dry_run:
                request.user.eva_used += 1
                request.user.save()
            if eva.domain == Evaluation.Domain.MULTI:
                data = merge_lbx(eva)
                for i in range(len(data)):
                    if dry_run and "lbx" in data[i] and data[i]["lbx"] == 1:
                        continue
                    cur_data = {"name": data[i]["name"], "dataset": data[i]["dataset_show"], "subjective": data[i].get("subjective", 0)}
                    if "lbx" in data[i] and data[i]["lbx"] == 1:
                        cur_data["lbx"] = 1
                        cur_data["parent"] = data[i]["parent"]
                    else:
                        cur_data["lbx"] = 0
                    CvTaskResult.objects.create(
                        batch_id=run_batch.pk,
                        cv_id=data[i]["cv_id"],
                        idx=i,
                        mid=data[i]["pk"],
                        result_json=cur_data)
            else:
                from .tasks import create_nlp_dags
                run_batch.dags_ready = False
                create_nlp_dags(run_batch, include_robustness=eva.include_robustness)

            return run_batch

    @staticmethod
    def has_incomplete_batch(eval_id: int) -> bool:
        pending_or_running = models.Batch.objects.filter(
            status__in=models.Batch.RUNNING_STATUSES,
            evaluation_id=eval_id,
        ).first()
        if pending_or_running is not None:
            return True
        return False


class BatchResult(viewsets.ViewSet):
    """Retrieve result of batch."""
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *, eval_id=None, batch_id=None, pk=None):
        """retrieve result of batch."""
        eva = Evaluation.objects.get(id=self.kwargs['eval_id'])
        if eva.domain == Evaluation.Domain.MULTI:
            gjz = {"accuracy", "meanRecall", "IS", "FID"}
            res = []
            lbx0 = {}
            # lbx的任务一定在最后面运行
            parent = {}
            lbx = {}
            a = CvTaskResult.objects.filter(
                batch_id=self.kwargs['batch_id'],
                deleted_at=None,
            )
            hassubject = 0
            bat = models.Batch.objects.get(pk=self.kwargs['batch_id'])
            cuowu = 0
            for item in a:
                data = item.result_json
                data["pk"] = item.pk
                data["status"] = item.status
                res.append(data)
                if bat.dry_run == False and bat.status != models.Batch.Status.HUMAN_EVALUATING and request.user.available_mark_count > 0:
                    if item.status == 1:
                        if data.get("subjective", 0) == 1:
                            hassubject = request.user.available_mark_count
                    else:
                        cuowu = 1
                    if cuowu == 1:
                        hassubject = 0
                if data["status"] == 1:
                    parent[item.mid] = data["data"]["data"]
                    if data.get("lbx", 0) == 1 and "parent" in data["data"]:
                        if data["parent"] not in lbx0:
                            lbx0[data["parent"]] = {data["dataset"]: data["data"]["data"]}
                        else:
                            lbx0[data["parent"]][data["dataset"]] = data["data"]["data"]
            for k, v in lbx0.items():
                p = parent[k]
                for item in gjz:
                    if item in p:
                        flag = 1
                        cur_len = 0
                        cur_value = 0
                        for k1, v1 in v.items():
                            cur_len += 1
                            cur_value += p[item] - v1[item]
                        if k not in lbx:
                            lbx[k] = {}
                        lbx[k]["RB-" + item] = cur_value / (cur_len * p[item])

            dict1 = {
                "science_qa": "ScienceQA(test)",
                "mmmu": "MMMU(val)",
                "seed_bench": "SEED-Bench(test)",
                "cmmu": "CMMU(test)",
                "cmmmu": "CMMMU(val)",
                "math_vista": "MathVista(testmini)",
                "mm_bench_cn": "MMBench-CN(val)",
                "mm_bench_en": "MMBench(val)",
                "hallusion_bench": "HallusionBench(img)",
                "coco_t2i": "COCO_val2014",
                "cub": "CUB-200-2011",
                "flowers": "Flowers102",
                "mg18_zh": "MG-18_zh",
                "mg18_en": "MG-18_en",
                "Subjective_all": "Subjective_all",
                "Subjective_zh": "Subjective_zh",
                "Subjective_en": "Subjective_en",
            }
            for item in res:
                if "dataset" in item and item["dataset"] in dict1:
                    item["dataset"] = dict1[item["dataset"]]
            return JsonResponse({'results': res, "lbx": lbx, "hassubject": hassubject})
        elif eva.domain == Evaluation.Domain.NLP:
            results = summarize_batch(
                self.request.user.pk, self.kwargs['eval_id'], self.kwargs['batch_id'],
                self.request.user.is_staff,  # type: ignore
            )
            return JsonResponse({'results': results})


def summarize_batch(user_id: int, eval_id: int, batch_id: int, is_admin: bool = False) -> List[Dict[str, Any]]:
    kwargs: Dict[str, Any] = dict(
        deleted_at__isnull=True,
    )
    if not is_admin:
        kwargs.update(user_id=user_id)
    eva_queryset = Evaluation.objects.filter(**kwargs)
    eva = get_object_or_404(eva_queryset, pk=eval_id)

    # check batch.
    batch = get_object_or_404(
        models.Batch.objects.filter(evaluation_id=eva.pk),
        pk=batch_id,
    )

    from .utils import summarize_robustness
    return summarize_robustness(batch)



class Batch(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, eval_id=None, pk=None):
        from .tasks import cancel_batch
        queryset = filter_user(request, models.Batch.objects.all())
        batch = get_object_or_404(queryset, pk=pk)

        cancel_batch(batch_id=batch.pk, status=models.Batch.Status.CANCEL)
        return HttpResponse(status=204)


class DAG(generics.ListAPIView):
    """DAGs in batch."""

    permission_classes = [IsAuthenticated]
    serializer_class = serializers.DAG
    pagination_class = None

    def get_queryset(self):
        """Queryset."""
        kwargs = dict(
            deleted_at__isnull=True,
        )
        eva_queryset = filter_user(self.request, Evaluation.objects.filter(**kwargs))
        eva = get_object_or_404(eva_queryset, pk=self.kwargs['eval_id'])

        # check batch.
        batch = get_object_or_404(
            models.Batch.objects.filter(evaluation_id=eva.pk),
            pk=self.kwargs['batch_id'],
        )


        filters = dict(
            batch_id=batch.pk,
            deleted_at=None,
        )

        dataset_ids = self.request.GET.getlist('datasetIds')
        if dataset_ids:
            filters.update(dataset_id__in=dataset_ids)
        return models.DAG.objects.defer("result").filter(**filters).order_by("id")


class DAGResult(generics.RetrieveAPIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *, eval_id: int, batch_id: int, pk: int):
        dag = get_object_or_404(models.DAG.objects.defer("result").all(), pk=pk)
        return DJsonResponse(dag.result)


class BatchLog(viewsets.ViewSet):
    """Retrieve logs of batch."""

    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *, eval_id=None, batch_id=None, kind=None):
        """retrieve result of batch."""
        page: int = int(request.GET.get("page", "1")) or 1
        eva = get_object_or_404(
            Evaluation.objects.all(),
            pk=eval_id
        )

        batch = get_object_or_404(
            models.Batch.objects.all(),
            pk=batch_id, evaluation_id=eva.pk,
        )

        try_seq = batch.try_sequence
        if request.GET.get("try_sequence") is not None:
            try_seq = int(request.GET["try_sequence"])

        page_size = 80960
        total = executor.service.count_log_page(batch.pk, kind, try_seq, page_size)
        content = executor.service.load_log(batch.pk, kind, try_seq, page=page, page_size=page_size)
        if content == "":
            content = batch.failure_details
        return JsonResponse({
            'results': content,
            'page': {
                'current': page,
                'total': total,
            }
        })


class BatchResumption(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request, *, eval_id: int, batch_id: int):
        eva = get_object_or_404(
            Evaluation.objects.all(),
            pk=eval_id, user_id=request.user.pk,
        )
        if BatchList.has_incomplete_batch(eva.pk):
            return JsonResponse(
                {
                    "detail": _("A job is still running"),
                },
                status=400,
            )

        batch = get_object_or_404(
            models.Batch.objects.all(),
            pk=batch_id, evaluation_id=eva.pk,
        )
        if batch.status not in [models.Batch.Status.FAILURE, models.Batch.Status.CANCEL, models.Batch.Status.MODIFIED]:  # noqa
            return JsonResponse(
                {'detail': _('According to its status, We DONOT support to resume this run.')},  # noqa
                status=400,
            )
        if eva.sence == Evaluation.Sence.MODEL and batch.model_id == 0:
            return JsonResponse(
                {'detail': _('We DONOT support to resume this run.')},
                status=400,
            )

        try:
            celery_task_id = self.resume_failed_batch(eva, batch)
        except RuntimeError as e:
            return e.args[0]
        return JsonResponse(
            {'id': celery_task_id},
            status=201,
        )

    @staticmethod
    def resume_failed_batch(eva: Evaluation, batch: models.Batch) -> str:
        with transaction.atomic():
            models.Batch.objects.filter(
                pk=batch.pk,
            ).update(
                status=models.Batch.Status.PENDING,
                updated_at=timezone.now(),
                try_sequence=F('try_sequence') + 1,
            )
            if eva.domain == Evaluation.Domain.MULTI:
                items = CvTaskResult.objects.filter(
                    ~Q(status=1),
                    batch_id = batch.pk,
                    deleted_at=None,
                )
                for item in items:
                    item.status = 0
                    a1 = item.result_json
                    if "data" in a1:
                        if "starttime" in a1["data"]:
                            del a1["data"]["starttime"]
                        if "endtime" in a1["data"]:
                            del a1["data"]["endtime"]
                    item.result_json = a1
                    item.save()
            elif eva.domain == Evaluation.Domain.NLP:
                models.DAG.objects.filter(
                    ~Q(status__in=models.Batch.SUCCESS_STATUSES),
                    batch_id=batch.pk,
                    deleted_at=None,
                ).update(
                    status=models.Batch.Status.PENDING,
                    updated_at=timezone.now(),
                )
        batch.refresh_from_db() # read thew new value of try_sequence
        result = run_on_executor.delay(batch.pk, batch.try_sequence)
        return result.id


class BatchDagsUpdateViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def update(self, request, *, eval_id: int, batch_id: int):
        eva = get_object_or_404(
            Evaluation.objects.all(),
            pk=eval_id, user_id=request.user.pk,
        )
        batch = get_object_or_404(
            models.Batch.objects.all(),
            pk=batch_id, evaluation_id=eva.pk,
        )
        if batch.status in models.Batch.RUNNING_STATUSES:
            return JsonResponse(
                {
                    "detail": _("You may not change the datasets while the job is running."),
                },
                status=400,
            )
        ser = serializers.BatchDags(data=request.data)
        if not ser.is_valid():
            return JsonResponse(ser.errors, status=400)
        datasets: List[int] = ser.data['datasets']
        datasets_config: List[Dict[str, Any]] = ser.data.get('datasets_config') or []
        include_robustness = ser.data.get('include_robustness') or False
        with transaction.atomic():
            batch.include_robustness = include_robustness
            batch.save()
            if eva.domain == Evaluation.Domain.MULTI:
                CvTaskResult.objects.filter(~Q(status=1), batch_id=batch.pk).update(
                    deleted_at=timezone.now()
                )
                new_dataset_created = False
                data = merge_lbx_config(datasets_config, include_robustness)
                for i in range(len(data)):
                    if batch.dry_run and "lbx" in data[i] and data[i]["lbx"] == 1:
                        continue
                    cur_data = {"name": data[i]["name"], "dataset": data[i]["dataset_show"], "subjective": data[i].get("subjective", 0)}
                    if "lbx" in data[i] and data[i]["lbx"] == 1:
                        cur_data["lbx"] = 1
                        cur_data["parent"] = data[i]["parent"]
                    else:
                        cur_data["lbx"] = 0
                    try:
                        ctr = CvTaskResult.objects.filter(
                            ~Q(deleted_at=None),
                            batch_id=batch.pk,
                            cv_id=data[i]["cv_id"],
                        ).get()
                        if ctr.status != 1:
                            ctr.status = 99
                            ctr.result_json = cur_data
                        ctr.idx = i
                        ctr.deleted_at = None
                        ctr.save()
                    except CvTaskResult.DoesNotExist:
                        CvTaskResult.objects.create(
                            batch_id=batch.pk,
                            cv_id=data[i]["cv_id"],
                            idx=i,
                            result_json=cur_data,
                            status=99
                        )
                        new_dataset_created = True
                batch.datasets_config = datasets_config
                if new_dataset_created:
                    batch.status = models.Batch.Status.MODIFIED
                batch.save()
            elif eva.domain == Evaluation.Domain.NLP:
                from .tasks import create_nlp_dags
                batch.dags_ready = False
                create_nlp_dags(batch, datasets, include_robustness)
        return HttpResponse(status=204)
