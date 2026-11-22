from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from .models import Task
from .serializers import TaskSerializer


def health_check(request):
    return JsonResponse({"status": "ok"})


class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = (AllowAny,)
