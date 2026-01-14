"""
Tests for the Honeypot Quality Control System

Tests cover:
- HoneypotService injection logic
- Honeypot task selection
- Annotation evaluation
- Accuracy updates
- Trust level updates
- API endpoints
"""

import json
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class HoneypotServiceTests(TestCase):
    """Tests for HoneypotService logic"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data for all test methods"""
        from organizations.models import Organization
        from projects.models import Project
        from tasks.models import Task
        from annotators.models import (
            AnnotatorProfile,
            TaskAssignment,
            HoneypotTask,
            TrustLevel,
        )

        # Create organization
        cls.org = Organization.objects.create(title="Test Org")

        # Create user with annotator profile
        cls.user = User.objects.create_user(
            username="annotator1", email="annotator1@test.com", password="testpass123"
        )
        cls.user.active_organization = cls.org
        cls.user.save()

        cls.annotator = AnnotatorProfile.objects.create(
            user=cls.user, status="approved"
        )

        # Create trust level
        cls.trust_level = TrustLevel.objects.create(
            annotator=cls.annotator, level="new"
        )

        # Create project with honeypot enabled
        cls.project = Project.objects.create(
            title="Test Project",
            organization=cls.org,
            honeypot_enabled=True,
            honeypot_injection_rate=Decimal("0.10"),
            honeypot_min_interval=5,
        )

        # Create regular tasks
        cls.tasks = []
        for i in range(10):
            task = Task.objects.create(
                project=cls.project, data={"text": f"Sample task {i}"}
            )
            cls.tasks.append(task)

        # Create honeypot task
        cls.honeypot_task = Task.objects.create(
            project=cls.project, data={"text": "Honeypot task - classify this"}
        )
        cls.honeypot = HoneypotTask.objects.create(
            task=cls.honeypot_task,
            ground_truth=[{"value": {"choices": ["positive"]}}],
            tolerance=Decimal("0.80"),
            is_active=True,
        )

    def test_should_inject_honeypot_enabled(self):
        """Test honeypot injection when enabled"""
        from annotators.honeypot_service import HoneypotService

        # With 10% rate and random, it might or might not inject
        # Just check it doesn't crash
        result = HoneypotService.should_inject_honeypot(self.annotator, self.project)
        self.assertIsInstance(result, bool)

    def test_should_inject_honeypot_disabled(self):
        """Test honeypot not injected when disabled"""
        from annotators.honeypot_service import HoneypotService

        self.project.honeypot_enabled = False
        self.project.save()

        result = HoneypotService.should_inject_honeypot(self.annotator, self.project)
        self.assertFalse(result)

        # Re-enable for other tests
        self.project.honeypot_enabled = True
        self.project.save()

    def test_should_inject_honeypot_no_honeypots(self):
        """Test no injection when no honeypots exist"""
        from annotators.honeypot_service import HoneypotService

        # Deactivate honeypot
        self.honeypot.is_active = False
        self.honeypot.save()

        result = HoneypotService.should_inject_honeypot(self.annotator, self.project)
        self.assertFalse(result)

        # Reactivate
        self.honeypot.is_active = True
        self.honeypot.save()

    def test_get_honeypot_task(self):
        """Test getting an unseen honeypot task"""
        from annotators.honeypot_service import HoneypotService

        task = HoneypotService.get_honeypot_task(self.annotator, self.project)

        self.assertIsNotNone(task)
        self.assertEqual(task.id, self.honeypot_task.id)

    def test_get_honeypot_task_already_seen(self):
        """Test no honeypot returned when all seen"""
        from annotators.honeypot_service import HoneypotService
        from annotators.models import TaskAssignment

        # Mark honeypot as seen
        TaskAssignment.objects.create(
            annotator=self.annotator,
            task=self.honeypot_task,
            is_honeypot=True,
            status="completed",
        )

        task = HoneypotService.get_honeypot_task(self.annotator, self.project)

        self.assertIsNone(task)

    def test_process_honeypot_result_pass(self):
        """Test processing a passing honeypot result"""
        from annotators.honeypot_service import HoneypotService
        from annotators.models import TaskAssignment

        # Create assignment
        assignment = TaskAssignment.objects.create(
            annotator=self.annotator, task=self.honeypot_task, status="completed"
        )

        # Matching annotation
        annotation_result = [{"value": {"choices": ["positive"]}}]

        result = HoneypotService.process_honeypot_result(assignment, annotation_result)

        assignment.refresh_from_db()
        self.assertTrue(result["passed"])
        self.assertTrue(assignment.is_honeypot)
        self.assertTrue(assignment.honeypot_passed)

    def test_process_honeypot_result_fail(self):
        """Test processing a failing honeypot result"""
        from annotators.honeypot_service import HoneypotService
        from annotators.models import TaskAssignment

        # Create assignment
        assignment = TaskAssignment.objects.create(
            annotator=self.annotator, task=self.honeypot_task, status="completed"
        )

        # Non-matching annotation
        annotation_result = [{"value": {"choices": ["negative"]}}]

        result = HoneypotService.process_honeypot_result(assignment, annotation_result)

        assignment.refresh_from_db()
        self.assertFalse(result["passed"])
        self.assertTrue(assignment.is_honeypot)
        self.assertFalse(assignment.honeypot_passed)

    def test_update_annotator_accuracy(self):
        """Test accuracy score calculation"""
        from annotators.honeypot_service import HoneypotService
        from annotators.models import TaskAssignment

        # Create honeypot assignments with results
        for i, passed in enumerate([True, True, True, False]):
            task = Task.objects.create(project=self.project, data={"text": f"HP {i}"})
            TaskAssignment.objects.create(
                annotator=self.annotator,
                task=task,
                is_honeypot=True,
                honeypot_passed=passed,
                status="completed",
            )

        HoneypotService.update_annotator_accuracy(self.annotator)

        self.annotator.refresh_from_db()
        # 3 pass, 1 fail = 75%
        self.assertEqual(float(self.annotator.accuracy_score), 75.0)

    def test_create_honeypot(self):
        """Test creating a new honeypot"""
        from annotators.honeypot_service import HoneypotService

        new_task = Task.objects.create(
            project=self.project, data={"text": "New honeypot task"}
        )

        honeypot = HoneypotService.create_honeypot(
            task=new_task,
            ground_truth=[{"value": {"choices": ["neutral"]}}],
            tolerance=0.9,
            created_by=self.user,
        )

        self.assertIsNotNone(honeypot)
        self.assertEqual(honeypot.task, new_task)
        self.assertEqual(float(honeypot.tolerance), 0.9)

    def test_get_honeypot_stats(self):
        """Test getting honeypot statistics"""
        from annotators.honeypot_service import HoneypotService

        stats = HoneypotService.get_honeypot_stats(self.project)

        self.assertIn("total_honeypots", stats)
        self.assertIn("active_honeypots", stats)
        self.assertIn("pass_rate", stats)


class HoneypotTrustLevelTests(TestCase):
    """Tests for trust level updates based on honeypot performance"""

    @classmethod
    def setUpTestData(cls):
        from organizations.models import Organization
        from annotators.models import AnnotatorProfile, TrustLevel

        cls.org = Organization.objects.create(title="Test Org")
        cls.user = User.objects.create_user(
            username="annotator2", email="annotator2@test.com", password="testpass123"
        )
        cls.user.active_organization = cls.org
        cls.user.save()

        cls.annotator = AnnotatorProfile.objects.create(
            user=cls.user, status="approved"
        )
        cls.trust_level = TrustLevel.objects.create(
            annotator=cls.annotator, level="new"
        )

    def test_trust_level_updates_on_honeypot_pass(self):
        """Test trust level metrics update on honeypot pass"""
        from annotators.models import TrustLevel, TaskAssignment
        from annotators.honeypot_service import HoneypotService
        from projects.models import Project
        from tasks.models import Task
        from annotators.models import HoneypotTask

        project = Project.objects.create(
            title="Trust Test Project", organization=self.org, honeypot_enabled=True
        )

        task = Task.objects.create(project=project, data={"text": "test"})

        HoneypotTask.objects.create(
            task=task,
            ground_truth=[{"value": {"choices": ["yes"]}}],
            tolerance=Decimal("0.8"),
        )

        assignment = TaskAssignment.objects.create(
            annotator=self.annotator, task=task, status="completed"
        )

        # Process passing result
        HoneypotService.process_honeypot_result(
            assignment, [{"value": {"choices": ["yes"]}}]
        )

        self.trust_level.refresh_from_db()
        self.assertEqual(self.trust_level.total_honeypots, 1)
        self.assertEqual(self.trust_level.passed_honeypots, 1)
        self.assertEqual(float(self.trust_level.honeypot_pass_rate), 100.0)


class HoneypotAPITests(APITestCase):
    """Tests for honeypot management API endpoints"""

    @classmethod
    def setUpTestData(cls):
        from organizations.models import Organization
        from projects.models import Project
        from tasks.models import Task
        from annotators.models import HoneypotTask

        cls.org = Organization.objects.create(title="Test Org")

        # Create admin user
        cls.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="adminpass123",
            is_staff=True,
        )
        cls.admin.active_organization = cls.org
        cls.admin.save()

        cls.project = Project.objects.create(
            title="API Test Project",
            organization=cls.org,
            created_by=cls.admin,
            honeypot_enabled=True,
        )

        cls.task = Task.objects.create(project=cls.project, data={"text": "Test task"})

        cls.honeypot = HoneypotTask.objects.create(
            task=cls.task,
            ground_truth=[{"label": "positive"}],
            tolerance=Decimal("0.8"),
        )

    def test_list_honeypots(self):
        """Test listing honeypots for a project"""
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(
            f"/api/annotators/honeypots/project/{self.project.id}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("honeypots", response.data)
        self.assertEqual(response.data["count"], 1)

    def test_create_honeypot(self):
        """Test creating a new honeypot"""
        self.client.force_authenticate(user=self.admin)

        new_task = Task.objects.create(
            project=self.project, data={"text": "New task for honeypot"}
        )

        response = self.client.post(
            f"/api/annotators/honeypots/project/{self.project.id}",
            {
                "task_id": new_task.id,
                "ground_truth": [{"label": "negative"}],
                "tolerance": 0.9,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)

    def test_get_honeypot_stats(self):
        """Test getting honeypot statistics"""
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(
            f"/api/annotators/honeypots/project/{self.project.id}/stats"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_honeypots", response.data)
        self.assertIn("active_honeypots", response.data)

    def test_get_honeypot_config(self):
        """Test getting project honeypot configuration"""
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(
            f"/api/annotators/honeypots/project/{self.project.id}/config"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("honeypot_enabled", response.data)
        self.assertIn("honeypot_injection_rate", response.data)

    def test_update_honeypot_config(self):
        """Test updating project honeypot configuration"""
        self.client.force_authenticate(user=self.admin)

        response = self.client.put(
            f"/api/annotators/honeypots/project/{self.project.id}/config",
            {"honeypot_injection_rate": 0.20, "honeypot_min_interval": 10},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["honeypot_injection_rate"], 0.20)
        self.assertEqual(response.data["honeypot_min_interval"], 10)

    def test_delete_honeypot(self):
        """Test deleting a honeypot"""
        self.client.force_authenticate(user=self.admin)

        response = self.client.delete(
            f"/api/annotators/honeypots/project/{self.project.id}/{self.honeypot.id}"
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_honeypot_unauthorized(self):
        """Test unauthorized access is rejected"""
        response = self.client.get(
            f"/api/annotators/honeypots/project/{self.project.id}"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
