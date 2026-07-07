"""Define endpoints."""

from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.Evaluation.as_view()),
    path(
        "<int:pk>",
        views.EvaluationViewSet.as_view(
            actions={
                'get': "retrieve",
                'patch': "update",
                'delete': "destroy",
            },
        ),
    ),
    path("<int:eval_id>/batches/", include('paneval.apps.cem.urls')),
    path("datasets", views.Dataset.as_view()),
    path(
        'tokenizers',
        views.Tokenizer.as_view(
            actions={
                "get": "retrieve",
                "post": "create",
            },
        ),
    ),
    path('tokenizers/<int:pk>', views.TokenizerUploadView.as_view()),
    path("mmdata", views.list_mmdata),


    path("img", views.GetImg.as_view(
        actions={
            "get": "get",
        },
    )),

    path(
        '<int:eval_id>/tokenizer/files',
        views.TokenizerListFilesView.as_view(),
    ),
    path(
        '<int:eval_id>/tokenizer/files/<int:pk>/content',
        views.TokenizerFileContentView.as_view(),
    ),
    path(
        "mm/progress",
        views.BatchProgress.as_view(actions={
            "get": "get",
        }),
    ),
]
