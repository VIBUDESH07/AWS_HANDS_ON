from django.urls import path

from . import views

urlpatterns = [
    path("health", views.health),
    path("ready", views.ready),
    path("tasks", views.task_list),
    path("tasks/<int:pk>", views.task_detail),
]
