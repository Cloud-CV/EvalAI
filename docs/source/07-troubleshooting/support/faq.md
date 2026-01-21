# FAQs (Frequently Asked Questions)

This section provides answers to common questions developers have while working with or contributing to EvalAI. It is organized by category to help you find answers quickly.

## Table of Contents

- [Setup & Installation](#setup--installation)
- [Docker & Frontend Issues](#docker--frontend-issues)
- [Python & Backend Errors](#python--backend-errors)
- [Development & Contribution](#development--contribution)
- [PostgreSQL Errors](#postgresql-errors)
- [Learning Resources](#learning-resources)
- [Recommended Next Steps](#recommended-next-steps)

---

## Setup & Installation

### Q. How to start contributing?

EvalAI's issue tracker is good place to start. If you find something that interests you, comment on the thread and we'll help get you started. Alternatively, if you come across a new bug on the site, please file a new issue and comment if you would like to be assigned. Existing issues are tagged with one or more labels, based on the part of the website it touches, its importance etc., which can help you select one.

### Q. What are the technologies that EvalAI uses?

Please refer to [Technologies Used](../../02-architecture/technologies.md)

### Q. Why was virtualenv setup deprecated?

Due to evolving dependencies and environment complexity, we now recommend using Docker-based setup for reliability and consistency across systems.

---

## Docker & Frontend Issues

### Q. I see `Cannot GET \` on http://localhost:8888/ when using Docker.

This may happen if the container is not built properly. Run:

```bash
docker compose down
docker compose up --build
```

### Q. I get this error: `ERROR: Version in "./docker-compose.yml" is unsupported.`

Upgrade your Docker engine to the latest version compatible with Compose file version 3.

### Q. Nothing happens after clicking Login on EvalAI dashboard

This usually happens due to cache. Clean your browser cache & cookies completely and try accessing the website again, if still doesn't work, then try on a new browser profile.

### Q. While building EvalAI via Docker, I get:

```
ERROR: Service 'celery' failed to build: pull access denied for evalai_django, repository does not exist or may require 'docker login': denied: requested access to the resource is denied
```

**Solution:**

Ensure that your directory is named `evalai` (all lowercase). Docker image naming depends on the folder name. For instance, the image `evalai_django` gets renamed to `evalai_dev_django` if your directory is renamed to `EvalAI_dev`.

---

## Python & Backend Errors

### Q. I get this error while running tests inside Docker:

```
import file mismatch...
```

**Solution:**

Clean `__pycache__` and `.pyc` files:

```bash
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
```

---

## Development & Contribution

### Q. How do I fix coverage decrease warnings?

This means your new code isn't covered by tests. Click on the coverage report to view uncovered lines and add test cases accordingly.

---

## PostgreSQL Errors

### Q. ERROR: Port 5432 already in use

**Solution:**

Check and kill the process:

```bash
sudo netstat -lpn | grep :5432
sudo kill <PID>
```

---

## Learning Resources

- [Git and GitHub Learning Resources](https://help.github.com/articles/git-and-github-learning-resources/)
- [Markdown Guide](https://guides.github.com/features/mastering-markdown/)

---

## Recommended Next Steps

- Refer to the [EvalAI Docs](https://evalai.readthedocs.io/)
- Join our [Slack](https://evalai.cloudcv.org/web/slack) to ask for help if you're stuck