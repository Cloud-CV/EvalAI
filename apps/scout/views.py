import json
import logging

from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.utils.crypto import constant_time_compare
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from scout.dedup import canonical_key
from scout.models import Scout, ScoutChallenge, ScoutRun
from scout.serializers import ScoutChallengePayloadSerializer

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def webhook_receiver(request, name, token):
    scout = Scout.objects.filter(name=name).first()
    if scout is None:
        return HttpResponse(status=404)
    if not constant_time_compare(token, scout.webhook_token):
        return HttpResponse(status=403)

    try:
        body = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return HttpResponse(status=400)

    with transaction.atomic():
        run = ScoutRun.objects.create(scout=scout, raw_payload=body)

        warnings = []
        new_count = 0
        received = 0

        challenges = body.get("challenges")
        if not isinstance(challenges, list):
            warnings.append(
                "Payload is missing 'challenges' list (got {!r})".format(
                    type(body.get("challenges")).__name__
                )
            )
        else:
            for c in challenges:
                received += 1
                serializer = ScoutChallengePayloadSerializer(data=c)
                if not serializer.is_valid():
                    warnings.append(
                        "Skipped entry name={!r}: {}".format(
                            (
                                c.get("benchmark_name", "?")
                                if isinstance(c, dict)
                                else "?"
                            ),
                            serializer.errors,
                        )
                    )
                    continue
                data = serializer.validated_data
                try:
                    key = canonical_key(data)
                except (KeyError, AttributeError, ValueError) as err:
                    warnings.append(
                        "Could not compute key for entry name={!r}: {}".format(
                            data.get("benchmark_name", "?"), err
                        )
                    )
                    continue
                _, created = ScoutChallenge.objects.get_or_create(
                    canonical_key=key,
                    defaults={**data, "source_run": run},
                )
                if created:
                    new_count += 1

        run.new_challenge_count = new_count
        run.parse_warnings = warnings
        run.save(update_fields=["new_challenge_count", "parse_warnings"])

    return JsonResponse(
        {
            "received": received,
            "new": new_count,
            "run_id": run.id,
            "scout": scout.name,
        }
    )
