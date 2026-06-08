# Yutori Outreach Email Pipeline — Design

**Date:** 2026-06-06 (revised 2026-06-06 to move package to top-level `apps/scout/` and read challenges from DB models instead of JSON files)
**Status:** Approved for implementation planning
**Depends on:** `2026-06-06-yutori-scouting-design.md` (consumes the `ScoutChallenge` model defined there, and the `outreach_sent_at` column on it)
**Scope:** Daily Celery task that emails benchmark organizers discovered by the Yutori scout, via EvalAI's existing `send_email()` helper, from a dedicated `outreach@eval.ai` SES identity.

## Goal

Once per day, send a personalized outreach email to each benchmark/challenge
organizer whose `ScoutChallenge` row has not yet been emailed about
(i.e. `outreach_sent_at IS NULL`), inviting them to host their benchmark
on EvalAI. After successfully attempting sends for a row, the task sets
`outreach_sent_at = timezone.now()`. Delivery uses EvalAI's existing
SES + SendGrid template infrastructure with a dedicated sender identity
(`outreach@eval.ai`) to isolate reputation from transactional mail.

## Non-goals

- Suppression list for organizer emails (explicit user decision — see Risks).
- Unsubscribe view, List-Unsubscribe header, or footer opt-out link.
- Per-day send cap.
- Extending `apps/accounts/bounce_handler.py` to capture non-User bounces.
- Reply / inbound-mail handling for `outreach@eval.ai`.
- Multiple templates or campaign sequencing.
- Any UI for inspecting or managing outreach.

## Background — what EvalAI already provides

`apps/base/utils.py::send_email(sender, recipient, template_id, template_data)`:

- Fetches a SendGrid dynamic template by ID, renders Handlebars placeholders,
  and sends via the configured Django email backend.
- In production the backend is `django_ses.SESBackend` (AWS SES).
- Built-in protections: rate-limit (per-recipient per-minute via Django cache,
  default 10/min), Profile-based bounce suppression for recipients that have
  a registered EvalAI User, Sentry capture on failure.
- Returns silently on failure — `send_email()` never raises to callers.

The `Profile.email_bounced` suppression only catches recipients that exist as
EvalAI Users. Cold organizer emails do not, so that check is effectively a
no-op for this pipeline. This is acknowledged and accepted (see Risks).

## High-level architecture

```text
Celery beat (10:00 UTC daily)
        │
        ▼
scout/tasks.py :: send_daily_outreach
        │
        ├─ Query: ScoutChallenge.objects.filter(outreach_sent_at__isnull=True)
        │
        ├─ For each ScoutChallenge in the queryset:
        │     For each organizer dict in challenge.organizers
        │           (JSONField — list of {name, role, email, affiliation}):
        │        if organizer.get("email"):
        │           send_email(
        │             sender=settings.OUTREACH_FROM_EMAIL,
        │             recipient=organizer["email"],
        │             template_id=SENDGRID_SETTINGS["TEMPLATES"]
        │                         ["OUTREACH_BENCHMARK_HOSTING"],
        │             template_data=build_template_data(challenge, organizer),
        │           )
        │     # After attempting sends for the row:
        │     challenge.outreach_sent_at = timezone.now()
        │     challenge.save(update_fields=["outreach_sent_at"])
        │
        └─ Log: sent_count, skipped_count, attempted_count
```

Per-row marking means a partially-completed run (worker crash, deploy
mid-loop) does not need to be replayed from a watermark. Rows whose
emails went out are marked; the rest will be picked up next run.

## Files to add

```text
apps/scout/
├── tasks.py                       # @shared_task send_daily_outreach()
└── outreach.py                    # iter_new_targets(), build_template_data()
```

Tests live at the project root under `tests/unit/scout/`, matching the
existing EvalAI convention:

```text
tests/unit/scout/
├── test_outreach.py
└── test_tasks.py
```

The `apps/scout/` package and its `models.py` (containing `Scout`,
`ScoutRun`, `ScoutChallenge`) are created by the Yutori scouting spec,
including the `ScoutChallenge.outreach_sent_at` column this pipeline
reads and writes. This spec adds only `tasks.py`, `outreach.py`, and
their tests in `tests/unit/scout/` inside that same Django app — no new
app, no new migration.

## Settings & env

Add to `settings/common.py`:

```python
OUTREACH_FROM_EMAIL = os.environ.get(
    "OUTREACH_FROM_EMAIL",
    "EvalAI Team <outreach@eval.ai>",
)
```

Add inside the existing `SENDGRID_SETTINGS["TEMPLATES"]` dict:

```python
"OUTREACH_BENCHMARK_HOSTING": os.environ.get(
    "SENDGRID_OUTREACH_BENCHMARK_HOSTING_TEMPLATE_ID"
),
```

Add to `CELERY_BEAT_SCHEDULE` (locate the existing schedule in EvalAI's
settings during implementation — `deactivate_stale_bounced_accounts` is
one existing entry to grep for):

```python
"scout-outreach-daily": {
    "task": "scout.tasks.send_daily_outreach",
    "schedule": crontab(hour=10, minute=0),    # 10:00 UTC daily
},
```

`.env.example` updated with placeholder entries for both new env vars.

## Prerequisites (one-time, before first run)

1. **Yutori scouting spec is deployed.** That spec's migration creates the
   `ScoutChallenge` table (including the `outreach_sent_at` column this
   pipeline writes).
2. **Verify `outreach@eval.ai` as an identity in AWS SES.**
   AWS Console → SES → Verified identities → Create identity → Email address.
   Wait for the verification email, click the link, confirm status = Verified.
3. **(Recommended)** Create a separate SES configuration set for outreach so
   bounce/complaint metrics for this sender are visible independently of
   `team@eval.ai`. Wire it via the existing `AWS_SES_CONFIGURATION_SET`
   pattern if you want to keep one global set, or introduce
   `AWS_SES_OUTREACH_CONFIGURATION_SET` for fully separate tracking.
4. **Create the SendGrid dynamic template `OUTREACH_BENCHMARK_HOSTING`** in
   the SendGrid dashboard with the variable contract below, copy its
   template ID into `SENDGRID_OUTREACH_BENCHMARK_HOSTING_TEMPLATE_ID`.
5. **Confirm at least one `ScoutChallenge` row exists** (i.e. the Yutori scout
   has produced at least one webhook delivery). Without that, the task is
   a no-op (which is fine — it will log `sent=0`).

## SendGrid template contract

The Celery task passes exactly these variables in `template_data`. The
SendGrid template must render with this schema; subject line lives in the
template and may reference any of these variables (e.g. `{{benchmark_name}}`):

| Variable          | Type   | Source                                   | Example                                   |
|-------------------|--------|------------------------------------------|-------------------------------------------|
| `organizer_name`  | string | `organizer["name"]`                      | `"Dr. Jane Doe"`                          |
| `benchmark_name`  | string | `challenge.benchmark_name`               | `"ImageNet-21K-P"`                        |
| `conference`      | string | `challenge.conference`                   | `"NeurIPS"`                               |
| `year`            | int    | `challenge.year`                         | `2025`                                    |
| `official_url`    | string | `challenge.official_url`                 | `"https://imagenet21k.org/challenge"`     |
| `evalai_pitch`    | string | `challenge.evalai_reasoning`             | `"Standardized leaderboard hosting…"`     |

`build_template_data(challenge, organizer)` is a small helper in
`outreach.py` that produces this dict. It does no I/O.

## Per-row tracking (replaces "watermark")

There is no standalone watermark table. The `outreach_sent_at` column on
`ScoutChallenge` is the durable per-row state.

- **Filter:** `ScoutChallenge.objects.filter(outreach_sent_at__isnull=True)`.
  The column is indexed at the DB level for cheap filtering.
- **Mark sent:** after iterating organizers for one row, set
  `challenge.outreach_sent_at = timezone.now()` and
  `challenge.save(update_fields=["outreach_sent_at"])`. This commits the
  row's "I've been processed" flag independently of every other row.
- **Crash mid-loop semantics:** if the Celery worker dies after marking
  rows 1–3 but before row 4, the next run picks up at row 4 — no
  duplicate sends to rows 1–3, no missed sends to row 4 onwards.
- **First run** has no special seeding step: every row is `null`, so
  every row is eligible. Subsequent runs only pick up newly-inserted
  rows (which start `null`) plus any rows the previous run did not get
  to. This is correct behavior — no missed day, no manual catch-up.

## Selection semantics

- One email per (organizer, challenge) pair. If the same organizer appears
  on two `ScoutChallenge` rows (different benchmarks), they get two
  emails — different subjects, different bodies — on the days those rows
  are first processed.
- Organizers with empty-string or missing `email` in the JSONField are
  skipped silently (logged at DEBUG, not WARNING — missing emails are
  normal output from the Yutori scout when no public email exists).
- Per-organizer deduplication across challenges is **not** done here.
  Because dedup at the `ScoutChallenge` level is enforced by a unique
  constraint on `canonical_key` in the scouting spec, the same challenge
  cannot appear twice as separate rows; therefore an organizer attached
  to a given challenge is emailed exactly once for that challenge.

## Failure modes

| Scenario                                           | Behavior                                                            |
|----------------------------------------------------|---------------------------------------------------------------------|
| Zero matching `ScoutChallenge` rows                | Log `sent=0`, return                                                |
| DB unreachable                                     | Celery surfaces the exception; the row currently being processed is not marked sent; task retried per Celery defaults |
| `ScoutChallenge.organizers` JSONField is empty or missing key | Skip the loop body but still mark `outreach_sent_at` (no organizers means nothing to send; we don't keep retrying empties) |
| Organizer dict missing `email` or with empty string | Skip silently (DEBUG log only)                                     |
| `send_email()` internal failure                    | Already handled inside `send_email()` (Sentry + log); loop continues; row still marked sent at the end |
| SES identity not yet verified                      | `send_email()` raises internally, logs via Sentry, loop continues   |
| `ScoutChallenge.outreach_sent_at` column missing   | Scouting-spec migration not applied; task raises on first query — fix by running `migrate scout` |
| Two task runs overlap (shouldn't, but)             | Both query the same `outreach_sent_at IS NULL` set, both iterate, both send. Possible double-send for rows queried before either run marked them. Acceptable per Risks. |
| Celery worker crashes mid-loop                     | Rows fully processed are marked sent and not retried; the row mid-flight may have had some organizers emailed without the row marked — those organizers get re-emailed once on the next run. Acceptable per Risks. |

## Risks accepted (explicit user decision, 2026-06-06)

The user was presented twice during brainstorming with the option of adding
guardrails (suppression list, unsubscribe view, daily cap, non-User bounce
capture) and explicitly chose to omit all of them in favor of fastest
implementation. The user acknowledged the SES suspension risk on the
second prompt.

**Risk inventory:**

1. **AWS SES suspension of `outreach@eval.ai`** if bounce rate exceeds 5%
   or complaint rate exceeds 0.5%. Likely with LLM-scraped academic emails
   (stale addresses, role aliases). Blast radius is limited to outreach;
   `team@eval.ai` transactional mail (password resets, challenge invites,
   etc.) keeps working because SES suspends per-identity. This is the
   primary reason the dedicated sender identity was chosen.
2. **CAN-SPAM / GDPR exposure** for unsolicited commercial email without an
   unsubscribe mechanism or physical postal address. Accepted by user.
3. **No suppression** — a person can be emailed repeatedly across days if
   they appear on multiple newly-discovered challenges. Accepted.
4. **Duplicate sends** on Celery retry, overlapping runs, or worker crash
   mid-loop. Accepted.
5. **No reply handling** for `outreach@eval.ai`. Replies (including "STOP"
   and bounce notifications outside SES's webhook path) land in an inbox
   nobody is committed to reading. User should designate a human to monitor
   this mailbox if responses are expected.

**Mitigations baked into this spec despite the no-guardrails decision:**

- Dedicated SES identity isolates reputation damage to outreach only.
- Existing `send_email()` per-recipient per-minute rate limit (10/min) is
  inherited automatically — a tiny floor against accidental loops.
- Sentry captures `send_email()` failures, so a sudden spike in bounces is
  observable even without our own suppression list.

## Testing strategy

### Unit (`pytest`, no DB)

`test_outreach.py`:
- `build_template_data` produces the exact key set required by the
  SendGrid template contract above, given a `ScoutChallenge` instance and an
  organizer dict.
- Handles `organizer["email"]` missing, empty string, and whitespace-only.

### Integration (`pytest-django`, `@pytest.mark.django_db`)

`test_tasks.py` (with `send_email` patched at the module boundary):
- End-to-end on a fixture set of `ScoutChallenge` rows with mixed
  `outreach_sent_at` values:
  - Correct number of `send_email` calls (one per organizer with a
    non-empty email on a row whose `outreach_sent_at` is null).
  - Each call has correct `sender`, `recipient`, `template_id`,
    `template_data` shape.
  - After the task: every previously-null row now has
    `outreach_sent_at` set to a recent timestamp; previously-set rows
    are unchanged.
- Re-running the task immediately performs zero sends and changes no
  rows (idempotency).
- When `send_email` raises (simulated), loop continues to subsequent
  organizers and the row's `outreach_sent_at` is still set at the end
  (matches real `send_email` behavior, which swallows exceptions
  internally).
- A `ScoutChallenge` whose `organizers` is an empty list or missing the
  `email` key produces zero calls but is still marked
  `outreach_sent_at` (we don't want to re-query empty rows every run).

### Manual end-to-end (before declaring done)

1. Verify SES identity `outreach@eval.ai` is `Verified` in AWS Console.
2. Set `SENDGRID_OUTREACH_BENCHMARK_HOSTING_TEMPLATE_ID` to a real test
   template ID in the SendGrid dashboard.
3. Insert a `ScoutChallenge` row via Django shell whose single organizer's
   `email` is a test inbox you control and whose `outreach_sent_at` is
   null (the default on insert):
   `ScoutChallenge.objects.create(..., organizers=[{"name": "...", "email": "you@example.com"}])`.
4. Run the task directly:
   `python -c "from scout.tasks import send_daily_outreach; send_daily_outreach()"`
5. Confirm:
   - Email arrives at the test inbox, From = `outreach@eval.ai`.
   - Subject and body render with the variables from the ScoutChallenge row.
   - The row's `outreach_sent_at` is now set (check via Django shell or admin).
6. Re-run the task → confirm no second email is sent (the row's
   `outreach_sent_at` is no longer null).

## Dependencies

- `celery` — already a runtime dependency of EvalAI.
- No new runtime dependencies.

## Open questions for review

- Confirm the time-of-day for the daily Celery schedule (spec defaults to
  10:00 UTC). Should it align with a specific timezone (e.g. 09:00 ET to
  hit US mornings, ~13:00 UTC)?
- Confirm whether `AWS_SES_OUTREACH_CONFIGURATION_SET` should be a
  separate setting (recommended for separate metric tracking) or whether
  outreach should share the existing `AWS_SES_CONFIGURATION_SET`.
