from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Prefetch
from django.utils import timezone
from scout.client import YutoriAPIError, YutoriClient
from scout.models import Scout, ScoutRun


class Command(BaseCommand):
    help = (
        "Show, pause, or resume registered Yutori scouts. "
        "With no arguments, lists all scouts. "
        "Use --name <name> to act on one specific scout."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            default=None,
            help=(
                "Operate on the scout with this name. Required when using "
                "--pause or --resume. Without it, all scouts are listed."
            ),
        )
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "--pause",
            action="store_true",
            help="Pause the scout selected by --name.",
        )
        group.add_argument(
            "--resume",
            action="store_true",
            help="Resume the scout selected by --name.",
        )

    def handle(self, *args, **options):
        name = options.get("name")

        if options["pause"] or options["resume"]:
            if not name:
                raise CommandError(
                    "--pause and --resume require --name <name>."
                )
            api_key = getattr(settings, "YUTORI_API_KEY", "")
            if not api_key:
                raise CommandError("YUTORI_API_KEY env var is not set.")
            try:
                scout = Scout.objects.get(name=name)
            except Scout.DoesNotExist:
                raise CommandError(
                    "No Scout found with name={!r}.".format(name)
                )
            client = YutoriClient(api_key=api_key)
            try:
                if options["pause"]:
                    client.pause_scout(scout.scout_id)
                    scout.paused_at = timezone.now()
                    scout.save(update_fields=["paused_at"])
                    self.stdout.write(
                        "Paused Scout(name={}).".format(scout.name)
                    )
                else:
                    client.resume_scout(scout.scout_id)
                    scout.paused_at = None
                    scout.save(update_fields=["paused_at"])
                    self.stdout.write(
                        "Resumed Scout(name={}).".format(scout.name)
                    )
            except YutoriAPIError as err:
                raise CommandError("Yutori API call failed: {}".format(err))
            return

        if name:
            try:
                scout = Scout.objects.get(name=name)
            except Scout.DoesNotExist:
                raise CommandError(
                    "No Scout found with name={!r}.".format(name)
                )
            self._print_scout(scout, recent_runs=5)
            return

        run_qs = ScoutRun.objects.order_by("-received_at")
        scouts = list(
            Scout.objects.order_by("name").prefetch_related(
                Prefetch("runs", queryset=run_qs, to_attr="prefetched_runs")
            )
        )
        if not scouts:
            self.stdout.write(
                "No scouts registered. Run scout_create to register one."
            )
            return
        self.stdout.write("Registered scouts ({}):".format(len(scouts)))
        for scout in scouts:
            self._print_scout(scout, recent_runs=3)
            self.stdout.write("")

    def _print_scout(self, scout, recent_runs):
        self.stdout.write(
            "  name={} scout_id={} created_at={} paused={}".format(
                scout.name,
                scout.scout_id,
                scout.created_at.isoformat(),
                scout.paused_at.isoformat() if scout.paused_at else "no",
            )
        )
        self.stdout.write(
            "  view_url: {}".format(scout.yutori_view_url or "-")
        )
        runs = getattr(scout, "prefetched_runs", None)
        if runs is None:
            runs = list(scout.runs.order_by("-received_at"))
        recent = list(runs[:recent_runs])
        self.stdout.write("  last {} runs:".format(recent_runs))
        if not recent:
            self.stdout.write("    (none)")
        for run in recent:
            self.stdout.write(
                "    {}  new={} warnings={}".format(
                    run.received_at.isoformat(),
                    run.new_challenge_count,
                    len(run.parse_warnings or []),
                )
            )
