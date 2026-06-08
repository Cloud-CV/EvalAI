import hashlib
import secrets

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from scout.client import YutoriAPIError, YutoriClient
from scout.models import Scout
from scout.prompt import RESEARCH_PROMPT
from scout.schema import OUTPUT_SCHEMA


class Command(BaseCommand):
    help = (
        "Register a recurring Yutori scout with the current prompt. "
        "Use --name to register multiple independent scouts."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            default="default",
            help=(
                "Friendly identifier for this scout (used in the webhook "
                "URL path). Must be unique across all registered scouts. "
                "Default: 'default'."
            ),
        )

    def handle(self, *args, **options):
        name = options["name"]
        api_key = getattr(settings, "YUTORI_API_KEY", "")
        public_base = getattr(settings, "SCOUT_PUBLIC_BASE_URL", "")

        if not api_key:
            raise CommandError("YUTORI_API_KEY env var is not set.")
        if not public_base:
            raise CommandError(
                "SCOUT_PUBLIC_BASE_URL env var is not set "
                "(e.g. https://eval.ai or your ngrok URL)."
            )

        if Scout.objects.filter(name=name).exists():
            raise CommandError(
                "A Scout with name={!r} already exists. Pick a different "
                "--name, or delete the existing row first.".format(name)
            )

        webhook_token = secrets.token_urlsafe(32)
        webhook_url = "{}/api/scout/webhook/{}/{}/".format(
            public_base.rstrip("/"), name, webhook_token
        )

        client = YutoriClient(api_key=api_key)
        try:
            resp = client.create_scout(
                query=RESEARCH_PROMPT,
                output_schema=OUTPUT_SCHEMA,
                webhook_url=webhook_url,
                output_interval=86400,
            )
        except YutoriAPIError as err:
            raise CommandError("Yutori API call failed: {}".format(err))

        scout_id = resp.get("id")
        if not scout_id:
            raise CommandError(
                "Yutori response missing 'id' field: {!r}".format(resp)
            )

        query_hash = hashlib.sha256(
            RESEARCH_PROMPT.encode("utf-8")
        ).hexdigest()

        scout = Scout.objects.create(
            name=name,
            webhook_token=webhook_token,
            scout_id=scout_id,
            query_hash=query_hash,
            webhook_url=webhook_url,
            yutori_view_url=resp.get("view_url", "") or "",
        )

        self.stdout.write(
            "Created Scout(name={}, scout_id={}).".format(
                scout.name, scout.scout_id
            )
        )
        self.stdout.write("Webhook URL: {}".format(scout.webhook_url))
        self.stdout.write(
            "View at: {}".format(scout.yutori_view_url or "(no view_url)")
        )
