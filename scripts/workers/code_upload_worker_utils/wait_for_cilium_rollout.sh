#!/bin/bash

# Wait for Cilium to come up, but only when the cluster has a node to run it on.
#
# install_dependencies.sh is the container CMD, so it re-runs in full on every
# worker restart. scripts/monitoring/auto_scale_eks_nodes.py scales this
# nodegroup to desiredSize 0 whenever a challenge has no pending submissions,
# and a 1-replica cilium-operator Deployment can never become available with no
# node to schedule it on. Treating that as a bootstrap failure exits the script,
# restarts the container, and re-runs the whole bootstrap - another AWS CLI
# download, another round of kubectl applies, another `helm upgrade cilium` -
# every few minutes for as long as the challenge stays idle.
#
# Note the asymmetry that makes this easy to misread in the logs: a DaemonSet
# with zero nodes trivially satisfies 0/0 desired and reports success, so
# `daemonset/cilium` rolls out "fine" and only the operator Deployment hangs.
#
# A zero-node cluster is a normal idle state, not a failure. Skip the wait and
# let the worker start and poll SQS; the DaemonSet and the operator roll out on
# their own once the autoscaler brings a node up for a new submission.

CILIUM_ROLLOUT_TIMEOUT="${CILIUM_ROLLOUT_TIMEOUT:-120s}"

# A lookup that failed and a cluster that genuinely has no nodes both leave
# stdout empty - they must not be treated the same way. Counting lines from an
# errored command would silently skip the rollout gate whenever the API server
# was unreachable or RBAC was misconfigured, which is precisely when the gate
# is worth having. Only an empty result from a lookup that *succeeded* means
# "no nodes yet".
node_list="$(mktemp)"
if ! kubectl get nodes --no-headers >"$node_list" 2>/dev/null; then
  echo "### Could not list cluster nodes to decide whether to wait for Cilium" >&2
  rm -f "$node_list"
  exit 1
fi
node_count="$(grep -c '[^[:space:]]' "$node_list")"
rm -f "$node_list"

if [ "$node_count" -eq 0 ]; then
  echo "### Cluster has no nodes (nodegroup scaled to zero for an idle challenge)."
  echo "### Skipping the Cilium rollout wait; it will roll out when a node appears."
  exit 0
fi

if ! kubectl -n kube-system rollout status daemonset/cilium \
    --timeout="$CILIUM_ROLLOUT_TIMEOUT"; then
  echo "### Cilium daemonset failed to roll out" >&2
  exit 1
fi

# ipam.mode=cluster-pool means agent pods wait on cilium-operator to allocate
# their node's PodCIDR, so the DaemonSet rolling out successfully doesn't
# guarantee the cluster is actually functional without this too.
if ! kubectl -n kube-system rollout status deployment/cilium-operator \
    --timeout="$CILIUM_ROLLOUT_TIMEOUT"; then
  echo "### Cilium operator failed to roll out" >&2
  exit 1
fi

echo "### Cilium rolled out"
