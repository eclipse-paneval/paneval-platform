"""Define endpoints."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.BatchList.as_view()),
    path("<int:pk>", views.Batch.as_view()),
    path("<int:batch_id>/dags", views.DAG.as_view()),
    path("<int:batch_id>/dags/<int:pk>/result", views.DAGResult.as_view()),
    path(
        "<int:batch_id>/results",
        views.BatchResult.as_view(actions={
            "get": "retrieve",
        }),
    ),
    path(
        "<int:batch_id>/logs/<str:kind>",
        views.BatchLog.as_view(actions={
            "get": "retrieve",
        }),
    ),
    path(
        "<int:batch_id>/datasets",
        views.BatchDagsUpdateViewSet.as_view(actions={
            "put": "update",
        }),
    ),
    path(
        "<int:batch_id>/resumption",
        views.BatchResumption.as_view(actions={
            "put": "create",
        }),
    ),
    
]
