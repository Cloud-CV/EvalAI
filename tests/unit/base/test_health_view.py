from django.test import TestCase
from django.urls import reverse


class TestHealthCheckView(TestCase):
    """
    The load balancer target group health check calls this endpoint, so it
    must answer unauthenticated requests and must not depend on the database.
    """

    def test_health_check_returns_ok_for_anonymous_requests(self):
        # The literal path is part of the contract: it is configured on the
        # target group, so renaming the route silently breaks health checks.
        self.assertEqual(reverse("health_check"), "/api/health/")

        response = self.client.get(reverse("health_check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_health_check_does_not_query_the_database(self):
        # A database blip must not fail the health check, otherwise the load
        # balancer would drain every healthy target at the same time. Assert
        # the status inside the block too, so an error response that happens
        # to make no query cannot pass this test.
        with self.assertNumQueries(0):
            response = self.client.get(reverse("health_check"))
            self.assertEqual(response.status_code, 200)
