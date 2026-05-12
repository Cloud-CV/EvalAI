# Submission Workflow Invariants

The submission API in EvalAI enforces a set of invariants to ensure challenge integrity and prevent invalid submissions.
These rules are enforced at the API layer and are fundamental to how submissions are handled across challenges.

This document describes those invariants and the reasoning behind them.

---

## Core Invariants

The submission workflow must satisfy the following rules:

- Submissions must be rejected if the challenge or challenge phase is inactive.
- Only participant teams that are registered for a challenge are allowed to submit.
- Submission requests must be authenticated before workflow invariants are evaluated.

These represent a subset of the fundamental invariants enforced by the submission workflow and apply regardless of client behavior.

---

## Why These Invariants Matter

These rules ensure that only valid submissions enter the system.
By enforcing them early in the request lifecycle, EvalAI prevents inconsistent state and avoids downstream issues in scoring, evaluation, and leaderboards.

Making these constraints explicit also helps contributors reason about expected behavior and avoid introducing regressions.

---

## Testing Approach

These invariants are intended to be validated using API-level workflow tests rather than unit tests of internal functions.

Each workflow test:
- Satisfies only the required preconditions
- Violates exactly one invariant
- Asserts both the API response and the absence of side effects (for example, ensuring that no `Submission` object is created)

This approach helps keep tests stable while clearly documenting the guarantees provided by the submission workflow.
