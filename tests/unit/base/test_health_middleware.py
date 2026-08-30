from django.test import TestCase, override_settings


@override_settings(ALLOWED_HOSTS=["eval.ai"])
class TestHealthCheckMiddleware(TestCase):
    """
    A load balancer health-checks targets by private IP and cannot send a
    custom Host header, so the request never matches ALLOWED_HOSTS. Without a
    bypass every target is marked unhealthy and the service is taken out of
    rotation.
    """

    def test_health_check_answers_a_host_outside_allowed_hosts(self):
        response = self.client.get("/api/health/", HTTP_HOST="10.0.1.42")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_other_paths_still_reject_a_host_outside_allowed_hosts(self):
        # The bypass must be scoped to the health path. If host validation
        # stopped applying everywhere, this would return something other
        # than 400 and the protection would be gone site-wide.
        response = self.client.get("/api/challenges/", HTTP_HOST="10.0.1.42")

        self.assertEqual(response.status_code, 400)

    def test_health_check_still_answers_a_permitted_host(self):
        response = self.client.get("/api/health/", HTTP_HOST="eval.ai")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
