# Manual Setup

Docker is the supported local installation path. Manual setup is only recommended for advanced contributors who need to run Django and the frontend outside containers.

## Recommended path

Use [Linux](linux-setup.html), [macOS](macos-setup.html), or [Windows](windows-setup.html) Docker instructions instead.

## High-level manual steps

1. Install Python 3, Node.js, PostgreSQL, and Redis/SQS-compatible queue per current `README.md` in the repository root.
2. Create a virtual environment and install `requirements/dev.txt`.
3. Configure Django settings module for development (`settings/dev.py`).
4. Run migrations: `python manage.py migrate`
5. Seed data: `python manage.py seed` (if available in your branch)
6. Start Django: `python manage.py runserver`
7. Build frontend assets per `frontend/README` or root README instructions.
8. Run `python scripts/workers/submission_worker.py` in a separate terminal for evaluation.

Exact versions and commands change over time — always follow the root [README.md](https://github.com/Cloud-CV/EvalAI/blob/master/README.md) on your checkout.

## Documentation development

To build docs only:

```bash
pip install -r requirements/readthedocs.txt
cd docs && make html
```

See [docs/README.md](https://github.com/Cloud-CV/EvalAI/blob/master/docs/README.md).

## See also

- [Contribution guide](../../04-development/contributing/contribution-guide.html)
- [FAQ](../../07-troubleshooting/support/faq.html)
