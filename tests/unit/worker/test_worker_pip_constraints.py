import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

WORKER_DOCKERFILES = [
    ("docker/prod/worker_py3_7/Dockerfile", "worker_py3_7.txt"),
    ("docker/prod/worker_py3_8/Dockerfile", "worker_py3_8.txt"),
    ("docker/prod/worker_py3_9/Dockerfile", "worker_py3_9.txt"),
    ("docker/dev/worker_py3_7/Dockerfile", "worker_py3_7.txt"),
    ("docker/dev/worker_py3_8/Dockerfile", "worker_py3_8.txt"),
    ("docker/dev/worker_py3_9/Dockerfile", "worker_py3_9.txt"),
]


@pytest.mark.parametrize(
    "dockerfile_path,requirements_name", WORKER_DOCKERFILES
)
def test_worker_dockerfile_sets_pip_constraint(
    dockerfile_path, requirements_name
):
    content = (REPO_ROOT / dockerfile_path).read_text()
    expected = f"/code/requirements/{requirements_name}"
    assert (
        f"PIP_CONSTRAINT={expected}" in content
    ), f"{dockerfile_path} must set PIP_CONSTRAINT to {expected}"
    assert (
        f"PIP_BUILD_CONSTRAINT={expected}" in content
    ), f"{dockerfile_path} must set PIP_BUILD_CONSTRAINT to {expected}"


@pytest.mark.parametrize(
    "dockerfile_path,requirements_name", WORKER_DOCKERFILES
)
def test_pip_constraint_points_at_runtime_stage_requirements(
    dockerfile_path, requirements_name
):
    # The constraints file must be copied into the image (COPY . /code/ or
    # COPY requirements/) so PIP_CONSTRAINT resolves at container runtime.
    content = (REPO_ROOT / dockerfile_path).read_text()
    assert re.search(
        r"COPY\s+\.\s+/code/", content
    ), f"{dockerfile_path} must copy the app (incl. requirements/) into /code"
