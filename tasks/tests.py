from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Task


class HealthCheckTestCase(TestCase):
    def test_health_check(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

class TaskAPITests(APITestCase):
    def setUp(self):
        self.task = Task.objects.create(title="First task", description="Details")
        self.list_url = reverse("task-list")
        self.detail_url = reverse("task-detail", args=[self.task.pk])

    def test_list_tasks(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.task.pk)

    def test_create_task(self):
        response = self.client.post(self.list_url, {"title": "New task"}, format="json")
        self.assertEqual(response.status_code, 201)
        task = Task.objects.get(pk=response.data["id"])
        self.assertEqual(task.title, "New task")
        self.assertEqual(task.description, "")
        self.assertFalse(task.completed)
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)

    def test_retrieve_task(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], self.task.title)
        self.assertEqual(response.data["description"], "Details")

    def test_replace_task(self):
        response = self.client.put(self.detail_url, {
            "title": "Replaced", "description": "Updated", "completed": True,
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Replaced")
        self.assertEqual(self.task.description, "Updated")
        self.assertTrue(self.task.completed)

    def test_partial_update_task(self):
        response = self.client.patch(self.detail_url, {"completed": True}, format="json")
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertTrue(self.task.completed)
        self.assertEqual(self.task.title, "First task")

    def test_delete_task(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())

    def test_invalid_titles(self):
        for payload in ({}, {"title": ""}, {"title": "   "}, {"title": "x" * 201}):
            with self.subTest(payload=payload):
                response = self.client.post(self.list_url, payload, format="json")
                self.assertEqual(response.status_code, 400)
                self.assertIn("title", response.data)
        self.assertEqual(Task.objects.count(), 1)

    def test_invalid_completed(self):
        response = self.client.patch(self.detail_url, {"completed": "invalid"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.task.refresh_from_db()
        self.assertFalse(self.task.completed)

    def test_server_managed_fields_are_read_only(self):
        created_at = self.task.created_at
        response = self.client.patch(self.detail_url, {
            "id": self.task.pk + 10,
            "created_at": "2000-01-01T00:00:00Z",
            "updated_at": "2000-01-01T00:00:00Z",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(response.data["id"], self.task.pk)
        self.assertEqual(self.task.created_at, created_at)
        self.assertGreater(self.task.updated_at, created_at)

    def test_missing_task(self):
        url = reverse("task-detail", args=[self.task.pk + 1])
        for method, payload in (("get", None), ("patch", {"title": "Missing"}),
                                ("put", {"title": "Missing"}), ("delete", None)):
            with self.subTest(method=method):
                response = getattr(self.client, method)(url, payload, format="json")
                self.assertEqual(response.status_code, 404)
