
class AnnotatorAutoApprovalTests(APITestCase):
    """Tests for annotator auto-approval on test submission"""

    @classmethod
    def setUpTestData(cls):
        from organizations.models import Organization
        from annotators.models import AnnotatorProfile

        cls.org = Organization.objects.create(title="Test Org")
        
        # Create user with annotator profile pending test
        cls.user = User.objects.create_user(
            username="candidate", 
            email="candidate@test.com", 
            password="testpass123"
        )
        cls.user.active_organization = cls.org
        cls.user.save()

        cls.annotator = AnnotatorProfile.objects.create(
            user=cls.user, 
            status="pending_test",
            email_verified=True
        )

    def test_auto_approve_on_pass(self):
        """Test that passing the test auto-approves the annotator"""
        self.client.force_authenticate(user=self.user)
        
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
        
        # Check if status was updated in DB
        self.annotator.refresh_from_db()
        self.assertEqual(self.annotator.status, "approved")
        self.assertIsNotNone(self.annotator.approved_at)
        
    def test_no_approve_on_fail(self):
        """Test that failing the test does not approve"""
        self.client.force_authenticate(user=self.user)
        
        # Simulate failing result
        results = {
            "passed": False,
            "score": 40,
            "details": {}
        }

        response = self.client.post(
            "/api/annotators/test/submit",
            {"results": results},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if status is correct
        self.annotator.refresh_from_db()
        self.assertEqual(self.annotator.status, "pending_test")
        self.assertIsNone(self.annotator.approved_at)
