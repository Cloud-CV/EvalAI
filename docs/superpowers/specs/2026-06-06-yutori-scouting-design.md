# Yutori Scouting Integration — Design

**Date:** 2026-06-06
**Status:** Approved for implementation planning
**Scope:** Yutori → JSON file pipeline only. Email/outreach pipeline is a separate spec.

## Goal

Automatically run a daily research scout against Yutori's Scouting API to discover
new / trending AI benchmark challenges from top-tier conferences, and persist the
results as a clean, deduped, machine-parseable JSON file under
`apps/web/yutori_scout/data/`. A future email-outreach subsystem will consume that
file; it is out of scope here.

## Non-goals

- Sending outreach emails (separate spec).
- A web UI for editing the prompt.
- Managing multiple prompts / multiple scouts.
- Implementing webhook delivery retries (Yutori handles retries on its side).

## Background — what the Yutori Scouting API gives us

- `POST https://api.yutori.com/v1/scouting/tasks` with header `X-API-Key: <key>`.
- Body includes `query` (the prompt), `output_interval` (seconds; default 86400),
  `output_schema` (JSON Schema enforced on each run's output), `webhook_url`,
  `webhook_format` (we use `scout`), `skip_email: true`.
- Yutori runs the scout on its own schedule. Results are **not** returned
  synchronously. Each run POSTs results to our `webhook_url`. There is no
  documented polling endpoint.
- The Scouting API does **not** retain memory across runs, so de-duplication
  ("don't repeat previously seen challenges") must happen on our side.

## High-level architecture

```
   Yutori scout (runs every 24h)
            │
            ▼
   POST <public_base>/web/yutori/webhook/<token>/
            │
            ▼
   apps/web/yutori_scout/views.py: webhook_receiver
            │
   ┌────────┼─────────────────────────────────────────┐
   │        │                                         │
   ▼        ▼                                         ▼
 verify  write raw payload                  for each challenge:
 token   → data/runs/<ts>.json                key = canonical_key(...)
                                              if key not in seen.json:
                                                append to challenges.json
                                                seen.json[key] = today
```

A downstream email-outreach subsystem (separate spec) reads `challenges.json`
and `seen.json` only. It never talks to Yutori. Likely sender: a marketing
platform (e.g. Customer.io / Lemlist / Instantly) — chosen later.

## File / module layout

New self-contained sub-package inside the existing `apps/web` Django app
(not registered as a separate Django app — its URL include is added to
`apps/web/urls.py`):

```
apps/web/yutori_scout/
├── __init__.py
├── prompt.py                      # Research prompt as a module constant
├── schema.py                      # output_schema (JSON Schema) sent to Yutori
├── client.py                      # YutoriClient: create_scout, get_scout, pause_scout
├── storage.py                     # Atomic JSON read/write
├── dedup.py                       # canonical_key(); merge_new()
├── views.py                       # webhook_receiver
├── urls.py                        # POST yutori/webhook/<token>/
├── management/commands/
│   ├── yutori_scout_create.py     # one-time: register the scout
│   └── yutori_scout_status.py     # show / pause / resume
├── data/                          # gitignored
│   ├── runs/YYYY-MM-DDTHH-MM-SSZ.json
│   ├── challenges.json
│   ├── seen.json
│   └── scout_meta.json            # {scout_id, created_at, webhook_url}
└── tests/
    ├── test_dedup.py
    ├── test_storage.py
    ├── test_schema.py
    ├── test_client.py
    └── test_webhook_view.py
```

`apps/web/urls.py` will gain:
```python
url(r"^yutori/", include("web.yutori_scout.urls")),
```

The resulting webhook path depends on where `apps/web` is mounted by the
project's root URLconf (existing routes like `contact/`, `subscribe/` follow
the same prefix). The `yutori_scout_create` command derives the full URL
from `YUTORI_PUBLIC_BASE_URL` plus this relative path at runtime, so the
spec does not hardcode the prefix.

## Settings & secrets

Read from environment (matches EvalAI's existing convention):

| Setting                   | Purpose                                                   |
|---------------------------|-----------------------------------------------------------|
| `YUTORI_API_KEY`          | Sent as `X-API-Key` header to Yutori                      |
| `YUTORI_WEBHOOK_TOKEN`    | Random opaque token embedded in the webhook URL path      |
| `YUTORI_PUBLIC_BASE_URL`  | Public base URL (e.g. `https://eval.ai` or ngrok URL)     |

Added to `settings/common.py` (or wherever EvalAI loads env-backed settings).
`.env.example` updated with placeholder values.

## Security model

The webhook URL is `/<public_base>/web/yutori/webhook/<token>/`. The `<token>`
path segment carries an unguessable secret. The view does
`django.utils.crypto.constant_time_compare(token, settings.YUTORI_WEBHOOK_TOKEN)`
before doing any work. Mismatched token → 403, nothing written, nothing logged
beyond a counter. Token never appears in logs.

We do not implement HMAC signature verification because Yutori's documentation
does not describe a signing scheme. If Yutori later publishes one, swap in
HMAC and remove the token-in-path.

CSRF: the view is decorated with `@csrf_exempt` (it's an external webhook).

## Data flow — detail

### One-time setup

```
$ python manage.py yutori_scout_create
```

1. Read `YUTORI_API_KEY`, `YUTORI_WEBHOOK_TOKEN`, `YUTORI_PUBLIC_BASE_URL`.
2. Build webhook URL: `{YUTORI_PUBLIC_BASE_URL}/web/yutori/webhook/{token}/`.
3. POST to `https://api.yutori.com/v1/scouting/tasks` with:
   - `query`         = `prompt.RESEARCH_PROMPT`
   - `output_schema` = `schema.OUTPUT_SCHEMA`
   - `output_interval` = 86400
   - `webhook_url`   = built URL
   - `webhook_format` = `"scout"`
   - `skip_email`    = `true`
4. Persist response to `data/scout_meta.json`:
   `{scout_id, query, created_at, webhook_url, next_run_timestamp}`.
5. Print `scout_id` and `view_url` to stdout.

Re-running the command when `scout_meta.json` already exists: abort with a
message telling the user to delete `scout_meta.json` or use
`yutori_scout_status --pause` first. (Prevents accidentally creating
duplicate scouts.)

### Status / pause

```
$ python manage.py yutori_scout_status              # show current scout + last 5 runs
$ python manage.py yutori_scout_status --pause      # pause the scout via Yutori API
$ python manage.py yutori_scout_status --resume     # resume
```

### Daily webhook delivery

For each POST to `/web/yutori/webhook/<token>/`:

1. **Token check** — constant-time compare. Mismatch → 403, return.
2. **Body parse** — JSON decode. Malformed → 400, return.
3. **Persist raw** — write the entire request body verbatim to
   `data/runs/<UTC timestamp>.json`. This is the audit trail; it happens
   before any parsing so a buggy parser can never lose data.
4. **Extract challenges** — payload is expected to contain
   `{"challenges": [...]}` per our `output_schema`. If the key is missing or
   not a list, log a warning and return 200 (Yutori shouldn't retry — the
   raw file is on disk for forensic review).
5. **Merge** — for each challenge dict:
   - Validate it has the schema's required fields. If not, log a warning
     including the dedup key and skip it.
   - Compute `key = canonical_key(c)`.
   - If `key` already in `seen.json`, skip.
   - Otherwise: append to `challenges.json`, set `seen.json[key] = today_iso`.
6. **Respond** — 200 OK with `{"received": N, "new": M}`.

**Idempotency policy:** the view **always** returns 200 if the token is valid,
even if some entries are malformed. This prevents Yutori from retry-storming
on partial parse failures. Bad entries are logged, not surfaced as HTTP errors.

**Concurrency:** `storage.py` uses write-to-temp-then-rename for `challenges.json`
and `seen.json`. A `fcntl.flock` on a sidecar lockfile guards the
read-modify-write cycle so two near-simultaneous webhook deliveries can't
clobber each other.

## `output_schema` (the JSON shape Yutori is forced to return)

Sent as `output_schema` in the scout creation request:

```json
{
  "type": "object",
  "required": ["challenges"],
  "properties": {
    "challenges": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["benchmark_name", "task_area", "conference", "year",
                     "official_url", "organizers", "evalai_suitable",
                     "evalai_reasoning"],
        "properties": {
          "benchmark_name": {"type": "string"},
          "task_area":      {"type": "string",
                             "description": "vision | NLP | multimodal | RL | robustness | medical imaging | speech | other"},
          "conference":     {"type": "string",
                             "description": "CVPR | NeurIPS | ICCV | ECCV | ICLR | AAAI | IJCAI | EMNLP | ACL | other"},
          "year":           {"type": "integer"},
          "official_url":   {"type": "string", "format": "uri"},
          "dataset_url":    {"type": "string",
                             "description": "Dataset page or official repo. Empty string if none."},
          "organizers": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["name"],
              "properties": {
                "name":        {"type": "string"},
                "role":        {"type": "string"},
                "email":       {"type": "string",
                                "description": "Official public email only. Empty string if not found."},
                "affiliation": {"type": "string"}
              }
            }
          },
          "evalai_suitable":  {"type": "boolean"},
          "evalai_reasoning": {"type": "string", "description": "1-2 lines"}
        }
      }
    }
  }
}
```

## Dedup key

```python
def canonical_key(c: dict) -> str:
    return f"{c['benchmark_name'].strip().lower()}|{c['conference'].strip().lower()}|{c['year']}"
```

Reasoning: name+conference+year survives URL changes and is robust to whitespace/case
drift. Different challenges at the same venue/year share the conference + year but
differ in name, so collisions are unlikely.

## The research prompt

Lives in `prompt.py` as a module-level constant `RESEARCH_PROMPT`. Verbatim from
the user, with one modification: the "don't repeat the challenge which you gave
me previously" clause is **removed**, because Yutori has no memory across runs
and we enforce dedup locally via `seen.json`. Leaving it in would mislead the
model and contaminate every result.

Changing the prompt = edit `prompt.py`, then:
1. `yutori_scout_status --pause` (pauses the existing scout via Yutori)
2. Delete `data/scout_meta.json`
3. `yutori_scout_create` (registers a new scout with the new prompt)

No live prompt-editing UI.

## File formats

### `data/challenges.json`
```json
{
  "schema_version": 1,
  "challenges": [
    { ...challenge as returned by Yutori, plus...
      "_first_seen": "2026-06-06T10:30:00Z",
      "_source_run": "2026-06-06T10-30-00Z.json"
    }
  ]
}
```

### `data/seen.json`
```json
{
  "schema_version": 1,
  "keys": {
    "imagenet-21k-p|neurips|2025": "2026-06-06T10:30:00Z"
  }
}
```

### `data/runs/<UTC timestamp>.json`
The verbatim webhook request body as received. Never mutated.

### `data/scout_meta.json`
```json
{
  "schema_version": 1,
  "scout_id": "uuid-from-yutori",
  "query_hash": "sha256 of prompt at time of creation",
  "created_at": "2026-06-06T10:00:00Z",
  "webhook_url": "...",
  "yutori_view_url": "..."
}
```

## Failure modes (handled)

| Scenario                                  | Behavior                                             |
|-------------------------------------------|------------------------------------------------------|
| Bad token in webhook URL                  | 403, nothing written                                 |
| Malformed JSON body                       | 400, nothing written                                 |
| `challenges` key missing/not a list       | 200, raw file kept, warning logged                   |
| Single challenge missing required field   | 200, valid entries persisted, bad one logged+skipped |
| Duplicate delivery of identical payload   | 200, no changes to `challenges.json` (dedup absorbs) |
| Yutori API down at `scout_create` time    | Command exits non-zero, no `scout_meta.json` written |
| Two webhooks arrive simultaneously        | flock on storage write serializes them               |
| Existing `scout_meta.json` at create time | Command aborts with explanatory error                |

## Testing strategy

### Unit (`pytest`, fast, no network)
- `test_dedup.py` — `canonical_key` normalization (whitespace, case, year as int); `merge_new` with duplicate / new / partial entries.
- `test_storage.py` — atomic write (tempfile + rename); concurrent-write safety under flock; recovery from corrupted existing file (renames to `.corrupt.<ts>` and starts fresh).
- `test_schema.py` — `OUTPUT_SCHEMA` validates against a known-good fixture payload using the `jsonschema` library.
- `test_client.py` — `YutoriClient` against a mocked `requests` session: correct URL, headers (`X-API-Key`), body shape; surfaces non-2xx as a typed exception.

### Webhook view (`pytest-django`)
- Valid token + valid payload → 200, files written, response body has correct counts.
- Invalid token → 403, no files written.
- Valid token + malformed JSON → 400, no files written.
- Valid token + valid payload with one challenge missing a required field → 200, valid entries persisted, bad entry logged.
- Duplicate delivery (same payload twice) → `challenges.json` unchanged on the second call.

### Manual end-to-end (before declaring done)
1. Start ngrok against local Django: `ngrok http 8000`.
2. Set `YUTORI_PUBLIC_BASE_URL` to the ngrok URL.
3. `python manage.py yutori_scout_create` against a real Yutori key, with `output_interval=1800` (the documented minimum) for the test scout.
4. Wait one cycle; confirm a file appears in `data/runs/`, `challenges.json` grows, and `seen.json` has new keys.
5. `python manage.py yutori_scout_status --pause`.
6. Delete the test scout via the Yutori dashboard; bump `output_interval` back to 86400 and re-create for production use.

## Dependencies

- `requests` (likely already in EvalAI) — Yutori HTTP calls.
- `jsonschema` (likely already in EvalAI; if not, add) — schema tests.
- No new runtime deps beyond those.

## Open questions for the user to confirm at review

- Is `apps/web/yutori_scout/data/` an acceptable on-disk location, or should
  the data live outside the source tree (e.g. `/var/lib/evalai/yutori_scout/`)
  for production deployments? Default in this spec: in-repo, gitignored.
- Should the webhook view emit a Slack notification on first-seen-today
  challenges? Out of scope unless requested.
