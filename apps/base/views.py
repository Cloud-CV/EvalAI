from django.http import JsonResponse


def health_check(request):
    """
    Liveness probe for the load balancer target group.

    Deliberately does not touch the database, cache or any other dependency.
    A load balancer health check answers one question -- "is this process
    still serving?" -- and folding dependency checks into it means an RDS or
    ElastiCache blip drains every application target at once instead of
    raising the alarm that actually owns that dependency.
    """
    return JsonResponse({"status": "ok"})
