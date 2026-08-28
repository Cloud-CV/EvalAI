from django.test import TestCase
from django.urls import reverse


class TestHealthCheckView(TestCase):
    """
    The load balancer target group health check calls this endpoint, so it
    must answer unauthenticated requests and must not depend on the database.
    """

    def test_health_check_returns_ok_for_anonymous_requests(self):
        response = self.client.get(reverse("health_check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_health_check_does_not_query_the_database(self):
        # A database blip must not fail the health check, otherwise the load
        # balancer would drain every healthy target at the same time.
        with self.assertNumQueries(0):
            self.client.get(reverse("health_check"))
