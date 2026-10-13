import json
import socket

from django.db import DatabaseError
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from .models import Task

TITLE_MAX_LENGTH = Task._meta.get_field("title").max_length


def parse_json_body(request):
    try:
        body = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return None
    return body if isinstance(body, dict) else None


@require_GET
def health(request):
    # Liveness probe — process uyiroda irukka nu mattum. DB check inga panna koodadhu,
    # illana DB down aana ellam pods-um restart aagidum.
    return JsonResponse({"status": "ok", "backend": "django", "hostname": socket.gethostname()})


@require_GET
def ready(request):
    # Readiness probe — DB reachable + migration mudinjirukka nu check. Fail aana
    # Service indha pod-ku traffic anuppadhu, aana pod-a restart pannadhu.
    try:
        Task.objects.exists()
    except DatabaseError as error:
        return JsonResponse({"status": "not-ready", "error": str(error)}, status=503)
    return JsonResponse({"status": "ready"})


# JSON API mattum — session/cookie auth illa, adhanala CSRF exempt
@csrf_exempt
@require_http_methods(["GET", "POST"])
def task_list(request):
    if request.method == "GET":
        return JsonResponse([task.to_dict() for task in Task.objects.all()], safe=False)

    body = parse_json_body(request)
    if body is None:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    title = str(body.get("title", "")).strip()
    if not title:
        return JsonResponse({"error": "title is required"}, status=400)

    task = Task.objects.create(title=title[:TITLE_MAX_LENGTH])
    return JsonResponse(task.to_dict(), status=201)


@csrf_exempt
@require_http_methods(["PATCH", "DELETE"])
def task_detail(request, pk):
    try:
        task = Task.objects.get(pk=pk)
    except Task.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)

    if request.method == "DELETE":
        task.delete()
        return HttpResponse(status=204)

    body = parse_json_body(request)
    if body is None:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    if "title" in body:
        title = str(body["title"]).strip()
        if not title:
            return JsonResponse({"error": "title cannot be empty"}, status=400)
        task.title = title[:TITLE_MAX_LENGTH]
    if "done" in body:
        task.done = bool(body["done"])

    task.save()
    return JsonResponse(task.to_dict())
