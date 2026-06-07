# Yutori Outreach Email Pipeline — Design

**Date:** 2026-06-06
**Status:** Approved for implementation planning
**Depends on:** `2026-06-06-yutori-scouting-design.md` (consumes the `challenges.json` it produces)
**Scope:** Daily Celery task that emails benchmark organizers discovered by the Yutori scout, via EvalAI's existing `send_email()` helper, from a dedicated `outreach@eval.ai` SES identity.

## Goal

Once per day, send a personalized outreach email to each benchmark/challenge
organizer who first appeared in `challenges.json` during the previous 24h,
inviting them to host their benchmark on EvalAI. Delivery uses EvalAI's
existing SES + SendGrid template infrastructure with a dedicated sender
identity (`outreach@eval.ai`) to isolate reputation from transactional mail.

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
apps/web/yutori_scout/tasks.py :: send_daily_outreach
        │
        ├─ Read watermark from data/last_outreach_run.iso
        │     (default if missing: now - 24h)
        │
        ├─ Load apps/web/yutori_scout/data/challenges.json
        │
        ├─ For each challenge where _first_seen > watermark:
        │     For each organizer with a non-empty email:
        │        send_email(
        │           sender=settings.YUTORI_OUTREACH_FROM_EMAIL,
        │           recipient=organizer.email,
        │           template_id=SENDGRID_SETTINGS["TEMPLATES"]
        │                       ["OUTREACH_BENCHMARK_HOSTING"],
        │           template_data=build_template_data(challenge, organizer),
        │        )
        │
        ├─ Write new watermark = run_started_at (atomic temp+rename)
        └─ Log: sent_count, skipped_count, attempted_count
```

## Files to add

```
apps/web/yutori_scout/
├── tasks.py                       # @shared_task send_daily_outreach()
├── outreach.py                    # iter_new_targets(), build_template_data()
├── data/
│   └── last_outreach_run.iso      # watermark; gitignored; atomic write
└── tests/
    ├── test_outreach.py
    └── test_tasks.py
```

The `apps/web/yutori_scout/` package already exists from the Yutori spec.
`tasks.py`, `outreach.py`, and the watermark file are new additions to it;
they share the same data directory as the webhook receiver.

## Settings & env

Add to `settings/common.py`:

```python
YUTORI_OUTREACH_FROM_EMAIL = os.environ.get(
    "YUTORI_OUTREACH_FROM_EMAIL",
    "EvalAI Team <outreach@eval.ai>",
)
```

Add inside the existing `SENDGRID_SETTINGS["TEMPLATES"]` dict:

```python
"OUTREACH_BENCHMARK_HOSTING": os.environ.get(
    "SENDGRID_OUTREACH_BENCHMARK_HOSTING_TEMPLATE_ID"
),
```

Add to `CELERY_BEAT_SCHEDULE` (or equivalent — confirm the existing
location in EvalAI's settings during implementation):

```python
"yutori-outreach-daily": {
    "task": "web.yutori_scout.tasks.send_daily_outreach",
    "schedule": crontab(hour=10, minute=0),    # 10:00 UTC daily
},
```

`.env.example` updated with placeholder entries for both new env vars.

## Prerequisites (one-time, before first run)

1. **Verify `outreach@eval.ai` as an identity in AWS SES.**
   AWS Console → SES → Verified identities → Create identity → Email address.
   Wait for the verification email, click the link, confirm status = Verified.
2. **(Recommended)** Create a separate SES configuration set for outreach so
   bounce/complaint metrics for this sender are visible independently of
   `team@eval.ai`. Wire it via the existing `AWS_SES_CONFIGURATION_SET`
   pattern if you want to keep one global set, or introduce
   `AWS_SES_OUTREACH_CONFIGURATION_SET` for fully separate tracking.
3. **Create the SendGrid dynamic template `OUTREACH_BENCHMARK_HOSTING`** in
   the SendGrid dashboard with the variable contract below, copy its
   template ID into `SENDGRID_OUTREACH_BENCHMARK_HOSTING_TEMPLATE_ID`.
4. **Confirm the Yutori scout has produced at least one `challenges.json`
   entry.** Without that, the task is a no-op (which is fine — it will log
   `sent=0` and update the watermark).

## SendGrid template contract

The Celery task passes exactly these variables in `template_data`. The
SendGrid template must render with this schema; subject line lives in the
template and may reference any of these variables (e.g. `{{benchmark_name}}`):

| Variable          | Type   | Source                                   | Example                                   |
|-------------------|--------|------------------------------------------|-------------------------------------------|
| `organizer_name`  | string | `organizer.name`                         | `"Dr. Jane Doe"`                          |
| `benchmark_name`  | string | `challenge.benchmark_name`               | `"ImageNet-21K-P"`                        |
| `conference`      | string | `challenge.conference`                   | `"NeurIPS"`                               |
| `year`            | int    | `challenge.year`                         | `2025`                                    |
| `official_url`    | string | `challenge.official_url`                 | `"https://imagenet21k.org/challenge"`     |
| `evalai_pitch`    | string | `challenge.evalai_reasoning`             | `"Standardized leaderboard hosting…"`     |

`build_template_data(challenge, organizer)` is a small helper in
`outreach.py` that produces this dict. It does no I/O.

## Watermark logic

- File: `apps/web/yutori_scout/data/last_outreach_run.iso`
  (single line, ISO-8601 UTC timestamp, e.g. `2026-06-05T10:00:00Z`)
- On task start:
  - Capture `run_started_at = now(UTC)`.
  - Read watermark. If missing or unparseable, default watermark to
    `run_started_at - 24h` and log a warning.
- Filter: a challenge is in-scope iff `_first_seen > watermark`. Challenges
  with malformed or missing `_first_seen` are skipped and logged.
- On task end (after the send loop completes, regardless of how many
  individual `send_email()` calls succeeded — that helper swallows its own
  exceptions):
  - Write `run_started_at` to the watermark file atomically
    (`tempfile + os.replace`).
- Rationale: using a watermark instead of a fixed 24h window means a missed
  run (worker down, deploy, etc.) does not silently drop a day of new
  challenges. Using `run_started_at` (captured at the start of the run) and
  not `now()` at the end avoids a race where a challenge whose `_first_seen`
  falls between start and end gets skipped on the next run.

## Selection semantics

- One email per (organizer, challenge) pair. If the same organizer appears
  on two newly-discovered challenges in the same day, they get two emails
  (different subjects, different bodies).
- Organizers with empty-string or missing `email` are skipped silently
  (logged at DEBUG, not WARNING — missing emails are normal output from the
  Yutori scout when no public email exists).
- The pipeline does not deduplicate across days. If a challenge somehow
  appears in `challenges.json` twice with different `_first_seen` values,
  organizers get re-emailed. (This should not happen given the Yutori
  spec's dedup, but the outreach side does not guard against it.)

## Failure modes

| Scenario                                           | Behavior                                                            |
|----------------------------------------------------|---------------------------------------------------------------------|
| `challenges.json` missing or empty                 | Log `sent=0`, update watermark, return                              |
| `challenges.json` malformed                        | Log exception via Sentry, **do not** update watermark, re-raise     |
| Watermark file missing / corrupt                   | Default to `now - 24h`, log warning, continue                       |
| Single challenge missing required fields           | Log warning with what's available, skip that challenge              |
| Organizer with empty email                         | Skip silently (DEBUG log only)                                      |
| `send_email()` internal failure                    | Already handled inside `send_email()` (Sentry + log); loop continues |
| SES identity not yet verified                      | `send_email()` raises internally, logs via Sentry, loop continues   |
| Two task runs overlap (shouldn't, but)             | Both read the same watermark; both update watermark to their start time — last write wins. Duplicate sends possible. Acceptable per Risks. |
| Celery worker crashes mid-loop                     | Watermark not updated; next run re-processes the same window. Duplicate sends possible. Acceptable per Risks. |

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

### Unit (`pytest`, no network)

`test_outreach.py`:
- `iter_new_targets` returns only `(challenge, organizer)` pairs from
  challenges with `_first_seen > watermark`.
- Skips organizers with empty/missing `email`.
- Skips challenges with missing or malformed `_first_seen`.
- Handles challenges missing the `organizers` key.
- `build_template_data` produces the exact key set required by the SendGrid
  template contract above.

`test_tasks.py` (with `send_email` patched):
- End-to-end on a synthetic `challenges.json`:
  - Correct number of `send_email` calls.
  - Each call has correct `sender`, `recipient`, `template_id`,
    `template_data` shape.
  - Watermark is updated to `run_started_at` after the loop.
- Watermark is **not** updated when `challenges.json` is malformed (parse
  error raised before the loop).
- When `send_email` raises (simulated), loop continues to subsequent
  organizers and watermark still updates (matches real `send_email`
  behavior, which swallows exceptions internally).
- Run with empty `challenges.json` → zero calls, watermark still updated.

### Manual end-to-end (before declaring done)

1. Verify SES identity `outreach@eval.ai` is `Verified` in AWS Console.
2. Set `SENDGRID_OUTREACH_BENCHMARK_HOSTING_TEMPLATE_ID` to a real test
   template ID in the SendGrid dashboard.
3. Seed `apps/web/yutori_scout/data/challenges.json` with one entry whose
   single organizer's `email` is a test inbox you control, and whose
   `_first_seen` is the current time.
4. Delete `apps/web/yutori_scout/data/last_outreach_run.iso`.
5. Run the task directly:
   `python -c "from web.yutori_scout.tasks import send_daily_outreach; send_daily_outreach()"`
6. Confirm:
   - Email arrives at the test inbox, From = `outreach@eval.ai`.
   - Subject and body render with the seeded variables.
   - `last_outreach_run.iso` exists and contains the run start time.
7. Re-run the task → confirm no second email is sent (watermark filter
   excludes the now-older challenge).

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
