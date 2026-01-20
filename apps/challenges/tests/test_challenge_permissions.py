from rest_framework.test import APITestCase


class ChallengePermissionTests(APITestCase):
    def test_unauthenticated_user_cannot_create_challenge(self):
        """
        Ensure that an unauthenticated user cannot create a challenge.
        """
        response = self.client.post("/api/challenges/", data={})

        # 401 = Unauthorized, 403 = Forbidden
        self.assertIn(response.status_code, [401, 403])
