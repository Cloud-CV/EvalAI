# Stripe "Pay & Approve" for Challenge Hosts — Implementation Plan

**Goal:** Let a challenge host pay through Stripe and have the challenge
approved automatically once the payment is confirmed, without an EvalAI admin
having to flip `approved_by_admin` by hand.

**Architecture:** Every downstream approval effect already hangs off
`approved_by_admin` changing from `False` to `True` followed by `save()`: the
post-save signals in `apps/challenges/models.py` (`create_eks_cluster_or_ec2_for_challenge`)
and `apps/challenges/aws_utils.py` (`challenge_approval_callback`) start the
Fargate workers, the EKS cluster or the EC2 instance. Payment therefore only
needs to perform that flip, and only after Stripe has confirmed the payment.

A new `apps/payments` Django app creates a Stripe Checkout Session for the
host. Stripe's hosted page collects the card, so card data never touches
EvalAI. A signature-verified webhook records each Stripe event and queues a
Celery task. The task verifies the payment and calls a shared
`approve_challenge()` helper, the same one the admin approval endpoint uses.
Everything ships behind a feature flag.

**Tech Stack:** Django 2.2.20, Python 3.9, DRF 3.10.3, Celery 4.3.0
(`evalai/celery.py`), PostgreSQL (`django.contrib.postgres.fields.JSONField`),
the `stripe` Python SDK (new dependency), AngularJS frontend, `mock` for
tests.

**Line references** are as of commit `8d3a5e8`.

---

## Assumed defaults

The plan assumes these; change any of them and the affected phases adjust.

1. **One payment per challenge** (Checkout `mode="payment"`), not a
   subscription. The end date is frozen at approval, so the price is known up
   front.
2. **Auto-approve only within the plan's limits.** A paid challenge that
   doesn't fit its plan is marked `needs_review` and flagged to admins in
   Slack.
3. **The manual "Send approval request" path stays**, for hosts who pay by
   invoice or purchase order.
4. **Feature flag:** `STRIPE_PAYMENTS_ENABLED`, default `False`.

## Open decisions

- [ ] One payment per challenge (assumed) or a subscription?
- [ ] Which challenge types can auto-approve, and what limits each plan has
      (duration, docker-based, instance types, worker counts).
- [ ] Refund policy, Stripe Tax, currency, and invoicing for universities.

---

## File Structure

**Created:**

```text
apps/payments/
├── __init__.py
├── apps.py
├── models.py          # ChallengeHostingPlan, ChallengePayment, StripeEvent
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py
├── admin.py
├── serializers.py
├── urls.py            # mounted at api/payments/
├── views.py           # plans, checkout, stripe webhook
├── tasks.py           # approve_paid_challenge (Celery)
└── utils.py           # check_plan_eligibility, Stripe client helpers

tests/unit/payments/
├── __init__.py
├── test_models.py
├── test_views.py
├── test_tasks.py
└── test_utils.py
```

**Modified:**

| File | Change |
|---|---|
| `apps/challenges/utils.py` | Add `get_unfinished_phases()` and `approve_challenge()` |
| `apps/challenges/views.py` | Use the new helpers; add the paid-plan guard to the host PATCH |
| `settings/common.py` | Add `payments` to `OUR_APPS`; add Stripe settings |
| `settings/test.py` | Dummy Stripe values |
| `docker/dev/docker.env` | Test-mode placeholders |
| `evalai/urls.py` | Mount `api/payments/` |
| `requirements/common.txt` | Pin `stripe` |
| `frontend/src/views/web/challenge/challenge-page.html` | "Pay & approve" button |
| `frontend/src/js/controllers/challengeCtrl.js` | Plan picker, checkout redirect, return polling |
| `frontend/tests/controllers-test/challengeCtrl.test.js` | Frontend tests |
| `docs/source/02-for-challenge-hosts/` | Host-facing docs |

**Suggested PR split:**
1. Refactor, models and settings (Phases 1–2)
2. Endpoints, webhook, task and PATCH guard (Phases 3–4)
3. Frontend (Phase 5)

---

## Phase 0: Stripe setup (no code)

- [ ] In Stripe test mode, create one Product/Price for each plan in the
      current subscription email (`SENDGRID_SUBSCRIPTION_PLANS_TEMPLATE_ID`).
- [ ] Register the webhook endpoint at
      `https://<api-host>/api/payments/stripe/webhook/` for these events:
      - `checkout.session.completed`
      - `checkout.session.async_payment_succeeded`
      - `checkout.session.async_payment_failed`
      - `checkout.session.expired`
      - `charge.refunded`
      - `charge.dispute.created`
- [ ] Add `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` to the staging and
      prod environments.

## Phase 1: Refactor (no behaviour change)

- [ ] Move the "every phase has a finished submission" check out of
      `request_challenge_approval_by_pk` (`apps/challenges/views.py:5367`)
      into `get_unfinished_phases(challenge)` in `apps/challenges/utils.py`.
- [ ] Move the approve logic out of `update_challenge_approval`
      (`apps/challenges/views.py:5541`) into `approve_challenge(challenge)` in
      `apps/challenges/utils.py`. It sets `approved_by_admin=True` and
      `is_frozen=True` and calls `save()`. The existing post-save signals
      still do the AWS provisioning.
- [ ] Point both views at the new helpers.
- [ ] Confirm the existing tests in `tests/unit/challenges/test_views.py`
      pass unchanged.

## Phase 2: `apps/payments` app, models and settings

`apps/challenges/views.py` is already 5,800+ lines, so payment code gets its
own app.

- [ ] Create the app and add `"payments"` to `OUR_APPS` in
      `settings/common.py`.
- [ ] Mount `apps/payments/urls.py` at `api/payments/` in `evalai/urls.py`.
- [ ] **`ChallengeHostingPlan`**:
      - Stripe and display: `name`, `stripe_price_id`, `amount` (minor
        units), `currency`, `is_active`, `description`
      - Limits: `max_duration_days`, `allow_docker_based`,
        `allowed_worker_instance_types` (JSONField), `max_worker_instance`
- [ ] **`ChallengePayment`** (`TimeStampedModel`):
      - Links: `challenge`, `host_team`, `created_by`, `plan`
      - Money and status: `amount`, `currency`, `status`, `paid_at`
      - `status` values: `pending`, `paid`, `needs_review`, `failed`,
        `expired`, `refunded`, `disputed`
      - Stripe IDs: `stripe_checkout_session_id` (unique),
        `stripe_payment_intent_id`
      - A conditional `UniqueConstraint` so a challenge can have only one
        `paid` payment.
- [ ] **`StripeEvent`**: `event_id` (unique), `type`, `payload` (JSONField,
      as in `apps/scout/models.py`), `received_at`, `processed_at`. This is
      the audit and deduplication log.
- [ ] Generate `0001_initial.py` with `makemigrations`.
- [ ] Register all three models in the Django admin.
- [ ] Pin a `stripe` release that supports Python 3.9 in
      `requirements/common.txt`.
- [ ] Add `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` and
      `STRIPE_PAYMENTS_ENABLED` (default `False`) to `settings/common.py`,
      read from the environment.
- [ ] Put dummy values in `settings/test.py` and test-mode placeholders in
      `docker/dev/docker.env`.

## Phase 3: Backend endpoints and task

### 3.1 `GET /api/payments/challenges/<challenge_pk>/plans/`

- [ ] Returns the active plans. Each plan has `eligible` (bool) and
      `reasons` (list) for this challenge.
- [ ] Also returns `payments_enabled` so the UI knows whether to show the
      button.
- [ ] Hosts of the challenge only.

### 3.2 `POST /api/payments/challenges/<challenge_pk>/checkout/` with `{plan_id}`

- [ ] Same auth as `request_approval`: `IsAuthenticated`,
      `HasVerifiedEmail`, JWT or expiring token, and
      `is_user_a_host_of_challenge` (`apps/hosts/utils.py:14`).
- [ ] Reject the request if:
      - the flag is off,
      - the challenge is already approved, or already has a `paid` payment,
      - `get_unfinished_phases()` is non-empty,
      - the plan is inactive, or `check_plan_eligibility()` fails.
- [ ] Reuse an unexpired `pending` session for the same challenge and plan if
      there is one.
- [ ] Otherwise create a `ChallengePayment` (`pending`), then a Checkout
      Session:

  ```python
  session = stripe.checkout.Session.create(
      mode="payment",
      line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
      client_reference_id=str(challenge.pk),
      metadata={"challenge_pk": challenge.pk, "payment_pk": payment.pk},
      customer_email=request.user.email,
      success_url=f"{challenge_page_url}?payment=success",
      cancel_url=f"{challenge_page_url}?payment=cancelled",
      idempotency_key=f"challenge-payment-{payment.pk}",
  )
  ```

- [ ] Save `session.id` and `session.amount_total` on the payment.
- [ ] Return `{"checkout_url": session.url}`.

### 3.3 `POST /api/payments/stripe/webhook/`

A plain Django view with `@csrf_exempt` and `@require_POST`, and no EvalAI
auth or throttling. `apps/scout/views.py` has a similar receiver to copy.

- [ ] Verify the request; a bad signature returns 400:

  ```python
  try:
      event = stripe.Webhook.construct_event(
          request.body,
          request.META.get("HTTP_STRIPE_SIGNATURE", ""),
          settings.STRIPE_WEBHOOK_SECRET,
      )
  except (ValueError, stripe.SignatureVerificationError):
      return HttpResponse(status=400)
  ```

- [ ] Record the event in `StripeEvent` (`get_or_create` on `event_id`). If
      it was already processed, return 200 straight away.
- [ ] Act on the event type:
      - **Session paid** (`checkout.session.completed` or
        `checkout.session.async_payment_succeeded`, with
        `payment_status == "paid"`): queue
        `approve_paid_challenge.delay(session_id)`.
      - **Failed or expired** (`checkout.session.async_payment_failed` or
        `checkout.session.expired`): update the payment's status.
      - **Refund or dispute** (`charge.refunded` or
        `charge.dispute.created`): update the status and alert Slack. Don't
        un-approve automatically; an admin decides.
      - **Anything else:** return 200.
- [ ] Always answer quickly; Stripe retries slow or failed deliveries.

### 3.4 Celery task `approve_paid_challenge(session_id)`

In `apps/payments/tasks.py`, using `evalai.celery.app`.

This runs in Celery because approving starts Fargate workers synchronously
inside `save()` (`challenge_approval_callback`). Those AWS calls are too slow
for a webhook response.

- [ ] In `transaction.atomic()`, lock the payment with `select_for_update()`.
      Stop if it is already `paid`.
- [ ] Check that `payment_status` is `"paid"` and that `amount_total` and
      `currency` match the payment row. On a mismatch, set `needs_review` and
      alert Slack.
- [ ] Set the status to `paid` and save `stripe_payment_intent_id` and
      `paid_at`.
- [ ] Re-run `check_plan_eligibility()`:
      - If the challenge still fits and isn't approved, call
        `approve_challenge()` from `transaction.on_commit`.
      - If not, set `needs_review`.
- [ ] Post to Slack with `send_slack_notification`
      (`apps/base/utils.py:467`) and `APPROVAL_WEBHOOK_URL`, e.g.
      "Challenge N auto-approved via payment (plan X, $Y)" or
      "needs review".

## Phase 4: Protect what was paid for

Today `is_frozen` only blocks `start_date` and `end_date`
(`apps/challenges/views.py:267`). After approval a host can still PATCH
`worker_instance_type`, `max_worker_instance`, `cpu_only_jobs` and similar
fields through `ZipChallengeSerializer`. Without a guard, a host could pay for
the CPU plan and then switch to GPU, and the EKS nodegroup sync hook would
apply the change live.

- [ ] Add `check_plan_eligibility(challenge, plan)` in
      `apps/payments/utils.py`. It returns a list of reasons the challenge
      doesn't fit, covering:
      - duration (`end_date - start_date`), `is_docker_based`,
        `remote_evaluation`
      - `worker_instance_type`, `worker_ami_type`, `worker_disk_size`
      - `min_worker_instance`, `max_worker_instance`,
        `desired_worker_instance`
      - `cpu_only_jobs`, `job_cpu_cores`, `job_memory`, `worker_cpu_cores`,
        `worker_memory`
      - `uses_ec2_worker`, `ec2_storage`, `ephemeral_storage`
- [ ] In the host PATCH/PUT branch of `challenge_detail`
      (`apps/challenges/views.py:264`): if the challenge has a `paid`
      payment, check the edited challenge against its plan. Reject with 403
      and the reasons if it no longer fits.
- [ ] Apply the same check to the zip and GitHub config re-upload path.
- [ ] Admins can still override in the Django admin.

## Phase 5: Frontend (AngularJS)

- [ ] `frontend/src/views/web/challenge/challenge-page.html` (around line
      20): add a **Pay & approve** button next to the existing approval
      button. Show it when the user is a host, the challenge isn't approved
      and `payments_enabled` is true.
- [ ] `frontend/src/js/controllers/challengeCtrl.js` (next to
      `vm.sendApprovalRequest`, line 207):
      - `vm.loadHostingPlans()` calls the plans endpoint.
      - A plan-picker dialog shows ineligible plans disabled, with their
        reasons.
      - `vm.payAndApprove(planId)` POSTs to checkout, then sets
        `$window.location.href = response.data.checkout_url`.
- [ ] On return to the challenge page:
      - With `?payment=success`, show "Payment received, approving…" and
        check the challenge every few seconds, for about a minute, until
        `approved_by_admin` is true. **Never approve from this redirect;**
        anyone can type that URL.
      - With `?payment=cancelled`, show a notice.

## Phase 6: Tests

### Backend (`tests/unit/payments/`)

Mock the Stripe SDK calls and the AWS approval signals.

| Area | Cases |
|---|---|
| Checkout | non-host gets 403; unfinished phases; already approved; already paid; ineligible plan; flag off; correct `Session.create` parameters, including the idempotency key and metadata; pending session reused |
| Webhook | bad signature gets 400; duplicate event is skipped; paid session queues the task; expired or failed session updates the status; refund or dispute updates the status and alerts Slack; unknown events get 200 |
| Task | approves and freezes; safe to run twice; amount mismatch → `needs_review`, not approved; ineligible → `needs_review` |
| Eligibility | each limit in `check_plan_eligibility()` |
| PATCH guard | cost-field edit blocked on a paid challenge; allowed on an unpaid one |
| Refactor | existing approval tests in `tests/unit/challenges/test_views.py` pass unchanged |

### Frontend

- [ ] Add `payAndApprove` (redirect on success, notify on error), plan loading
      and return-polling cases to
      `frontend/tests/controllers-test/challengeCtrl.test.js`.

### Commands (from `AGENTS.md`)

```bash
# Backend tests (CI-style one-off container)
docker compose run --rm --no-deps -e DJANGO_SETTINGS_MODULE=settings.test django \
  bash -c 'python manage.py flush --noinput && pytest -q'

# Backend lint
docker exec evalai-django-1 bash -c \
  'cd /code && python -m ruff check --no-fix apps/ && python -m ruff format --check apps/'

# Frontend tests
docker exec evalai-nodejs-1 bash -c \
  'Xvfb :99 -screen 0 1024x768x24 &>/dev/null & sleep 1 && npm test -- --single-run'
```

## Phase 7: Manual end-to-end test (Stripe test mode)

- [ ] Run `stripe listen --forward-to localhost:8000/api/payments/stripe/webhook/`
      and set `STRIPE_WEBHOOK_SECRET` to the `whsec_…` it prints.
- [ ] As `host`, create a challenge and get one finished submission per
      phase.
- [ ] Pay with test card `4242 4242 4242 4242`.
- [ ] Confirm the challenge ends up with `approved_by_admin` and `is_frozen`
      set to true, and that the Slack message fires.
- [ ] Repeat with a Stripe 3-D Secure test card.
- [ ] Use `stripe trigger` to simulate a refund and a dispute, and check the
      statuses and Slack alerts.

## Phase 8: Rollout

- [ ] Merge with `STRIPE_PAYMENTS_ENABLED=False`.
- [ ] Deploy to staging with test keys and repeat Phase 7 there.
- [ ] Turn it on in prod with live keys for one low-risk plan first, such as
      challenges that don't use docker.
- [ ] Watch Slack and the Stripe dashboard, then open up the other plans.
- [ ] Update the host docs in `docs/source/02-for-challenge-hosts/`.
