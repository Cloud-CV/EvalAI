"""Tests for the Cilium rollout gate used by the code-upload worker bootstrap.

install_dependencies.sh runs as the container CMD, so it re-runs in full on
every worker restart. The autoscaler scales this nodegroup to desiredSize 0
whenever no submissions are pending, and on a zero-node cluster a 1-replica
cilium-operator Deployment can never become available. Waiting on that rollout
therefore fails on a timeout and exits the script, restarting the container and
re-running the whole bootstrap -- including another `helm upgrade cilium` --
every few minutes for as long as the challenge is idle.

These tests drive the gate with a fake kubectl on PATH so the real behaviour is
exercised, rather than asserting on the text of the script.
"""

import os
import stat
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKER_UTILS = REPO_ROOT / "scripts" / "workers" / "code_upload_worker_utils"
GATE_SCRIPT = WORKER_UTILS / "wait_for_cilium_rollout.sh"
INSTALL_SCRIPT = WORKER_UTILS / "install_dependencies.sh"

FAKE_KUBECTL = """#!/bin/bash
echo "$*" >> "$KUBECTL_LOG"
case "$*" in
  *"get nodes"*)
    exit_code="${FAKE_NODES_EXIT:-0}"
    if [ "$exit_code" != "0" ]; then
      echo "the server could not find the requested resource" >&2
      exit "$exit_code"
    fi
    if [ -n "$FAKE_NODE_LINES" ]; then
      printf '%s\\n' "$FAKE_NODE_LINES"
    fi
    exit 0
    ;;
  *"rollout status daemonset/cilium"*)
    exit "${FAKE_DAEMONSET_EXIT:-0}"
    ;;
  *"rollout status deployment/cilium-operator"*)
    exit "${FAKE_DEPLOYMENT_EXIT:-0}"
    ;;
esac
exit 0
"""


@pytest.fixture
def run_gate(tmp_path):
    """Run the gate script with a fake kubectl, returning (result, calls)."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    kubectl = bin_dir / "kubectl"
    kubectl.write_text(FAKE_KUBECTL)
    kubectl.chmod(kubectl.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP)

    log = tmp_path / "kubectl.log"
    log.touch()

    def _run(**fake_env):
        env = dict(os.environ)
        env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
        env["KUBECTL_LOG"] = str(log)
        env.update({k: str(v) for k, v in fake_env.items()})
        result = subprocess.run(
            ["bash", str(GATE_SCRIPT)],
            env=env,
            capture_output=True,
            text=True,
        )
        return result, log.read_text().splitlines()

    return _run


def test_skips_rollout_wait_when_cluster_has_no_nodes(run_gate):
    """Zero nodes is the autoscaler's idle state, not a failure."""
    result, calls = run_gate(FAKE_NODE_LINES="")

    assert result.returncode == 0, result.stderr
    assert not any("rollout status" in call for call in calls), (
        "waited on a rollout that cannot complete without a node"
    )


def test_waits_for_both_rollouts_when_a_node_exists(run_gate):
    """With a node present the gate must still prove Cilium is up."""
    result, calls = run_gate(
        FAKE_NODE_LINES="ip-10-0-0-1.ec2.internal Ready <none> 1d v1.36.0"
    )

    assert result.returncode == 0, result.stderr
    assert any("rollout status daemonset/cilium" in c for c in calls)
    assert any("rollout status deployment/cilium-operator" in c for c in calls)


def test_fails_when_node_lookup_fails(run_gate):
    """A failed lookup must not be read as "zero nodes".

    Counting lines from a command that errored would silently skip the gate
    whenever the API server was unreachable or RBAC was misconfigured, which
    is the opposite of what the gate is for.
    """
    result, calls = run_gate(FAKE_NODES_EXIT=1)

    assert result.returncode == 1
    assert not any("rollout status" in call for call in calls)


def test_fails_when_operator_rollout_fails_on_a_live_node(run_gate):
    """A broken Cilium on a real node must still fail the bootstrap."""
    result, _ = run_gate(
        FAKE_NODE_LINES="ip-10-0-0-1.ec2.internal Ready <none> 1d v1.36.0",
        FAKE_DEPLOYMENT_EXIT=1,
    )

    assert result.returncode == 1


def test_bootstrap_delegates_the_cilium_wait_to_the_gate():
    """The gate is only worth anything if the bootstrap actually calls it.

    Without this, every test above would still pass after someone dropped the
    call from install_dependencies.sh and restored the unguarded waits.
    """
    content = INSTALL_SCRIPT.read_text()

    assert "wait_for_cilium_rollout.sh" in content, (
        "install_dependencies.sh must delegate the Cilium wait to the gate"
    )
    for ungated in (
        "rollout status daemonset/cilium",
        "rollout status deployment/cilium-operator",
    ):
        assert ungated not in content, (
            f"install_dependencies.sh still waits on '{ungated}' directly, "
            "which cannot succeed when the nodegroup is scaled to zero"
        )
