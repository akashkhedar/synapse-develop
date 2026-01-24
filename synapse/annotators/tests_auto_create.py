
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from annotators.models import AnnotatorProfile

User = get_user_model()

class AnnotatorAutoCreateTests(APITestCase):
    """Tests for annotator profile auto-creation on test submission"""

    @classmethod
    def setUpTestData(cls):
        from organizations.models import Organization
        cls.org = Organization.objects.create(title="Test Org")
        
        # Create user WITHOUT annotator profile
        cls.user = User.objects.create_user(
            username="newannotator", 
            email="newannotator@test.com", 
            password="testpass123"
        )
        cls.user.active_organization = cls.org
        cls.user.save()

    def test_auto_create_on_pass(self):
        """Test that passing the test auto-creates and approves the annotator"""
        self.client.force_authenticate(user=self.user)
        
        # Verify no profile exists initially
        self.assertFalse(AnnotatorProfile.objects.filter(user=self.user).exists())

        # Simulate passing result
        results = {
            "passed": True,
            "score": 95,
            "details": {}
        }

        response = self.client.post(
            "/api/annotators/test/submit",
            {"results": results},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if profile was created
        profile = AnnotatorProfile.objects.get(user=self.user)
        self.assertEqual(profile.status, "approved")
        self.assertIsNotNone(profile.approved_at)
        self.assertTrue(profile.email_verified)
