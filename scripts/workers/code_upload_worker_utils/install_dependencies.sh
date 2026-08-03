#!/bin/bash

# installing AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install
echo "### AWS CLI Installed"

aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
aws configure set aws_secret_access $AWS_SECRET_ACCESS_KEY
aws configure set default.region $AWS_DEFAULT_REGION
echo "### AWS CLI Configured"

# Install iam-authenticator
curl -o aws-iam-authenticator https://amazon-eks.s3.us-west-2.amazonaws.com/1.17.7/2020-07-08/bin/linux/amd64/aws-iam-authenticator
chmod +x ./aws-iam-authenticator
mkdir -p $HOME/bin && cp ./aws-iam-authenticator $HOME/bin/aws-iam-authenticator && export PATH=$PATH:$HOME/bin
echo 'export PATH=$PATH:$HOME/bin' >> ~/.bashrc
echo "### iam-authenticator Installed"

# Configure kubeconfig
aws eks --region $AWS_DEFAULT_REGION update-kubeconfig --name $CLUSTER_NAME

# Install kubectl
curl -LO "https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x ./kubectl
mv ./kubectl /usr/local/bin/kubectl
echo "### Kubectl Installed"

# Install helm
# Pinned to a fixed release rather than the mutable `main` branch script
# default (which installs whatever the latest v3 patch happens to be at
# run time) so this step is reproducible across worker restarts.
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod +x get_helm.sh
./get_helm.sh --version v3.21.3
echo "### Helm Installed"

# Install aws-container-insights
# Create amazon-cloudwatch namespace
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/cloudwatch-namespace.yaml
# Create configmap for fluent bit
kubectl create configmap fluent-bit-cluster-info \
--from-literal=cluster.name=$CLUSTER_NAME \
--from-literal=http.server='On' \
--from-literal=http.port='2020' \
--from-literal=read.head='On' \
--from-literal=read.tail='Off' \
--from-literal=logs.region=$AWS_DEFAULT_REGION -n amazon-cloudwatch
# Use FluentD compatible FluentBit insights
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/fluent-bit/fluent-bit-compatible.yaml
echo "### Container Insights Installed"

# Setup EFS as persistent volume
kubectl apply -k "github.com/kubernetes-sigs/aws-efs-csi-driver/deploy/kubernetes/overlays/stable/ecr/?ref=release-1.7"
kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=release-1.25"
cat /code/scripts/workers/code_upload_worker_utils/persistent_volume.yaml | sed "s/{{EFS_ID}}/$EFS_ID/" | kubectl apply -f -
kubectl apply -f /code/scripts/workers/code_upload_worker_utils/persistent_volume_claim.yaml
kubectl apply -f /code/scripts/workers/code_upload_worker_utils/persistent_volume_storage_class.yaml

# Install cilium
# Cilium is being used to provide networking and network policy.
# Installed via `helm upgrade --install`, which is idempotent across worker
# restarts (this script re-runs on every restart) and actually applies a
# version bump. The old `kubectl create` against a hardcoded v1.9
# quick-install.yaml silently no-op'd on already-existing resources and
# never advanced, which is how this cluster ended up permanently pinned to
# a 2021-era Cilium build incompatible with current EKS AMI kernels.
CILIUM_TARGET_VERSION="1.19.6"

helm repo add --force-update cilium https://helm.cilium.io/
helm repo update cilium

# One-time migration: clusters bootstrapped before this change installed
# Cilium via `kubectl create` against a raw quick-install.yaml, so those
# resources carry no Helm ownership metadata and Helm refuses to adopt them
# ("invalid ownership metadata") instead of upgrading them.
#
# Check the actual ownership annotation on the DaemonSet directly rather
# than inferring "no release" from `helm status` failing - that command can
# also fail for reasons that have nothing to do with a legacy install (Helm
# storage, RBAC, API connectivity), and treating that failure as "legacy" is
# how a real, working Helm-managed install would get deleted by mistake.
if kubectl get daemonset cilium -n kube-system >/dev/null 2>&1; then
  owner_release="$(kubectl get daemonset cilium -n kube-system \
    -o jsonpath='{.metadata.annotations.meta\.helm\.sh/release-name}' 2>/dev/null)"
  owner_namespace="$(kubectl get daemonset cilium -n kube-system \
    -o jsonpath='{.metadata.annotations.meta\.helm\.sh/release-namespace}' 2>/dev/null)"
  if [ "$owner_release" != "cilium" ] || [ "$owner_namespace" != "kube-system" ]; then
    echo "### Migrating legacy (non-Helm) Cilium install"
    kubectl delete -f https://raw.githubusercontent.com/cilium/cilium/v1.9/install/kubernetes/quick-install.yaml --ignore-not-found
  fi
fi

# Cilium's supported upgrade path only covers one minor version at a time;
# jumping several minors in a single unattended `helm upgrade` isn't
# supported and can leave the datapath broken with nobody watching. This
# script has only ever installed CILIUM_TARGET_VERSION via Helm (everything
# older was the unmanaged quick-install.yaml handled above), so this is not
# expected to trigger today - it exists to stop a future version bump here
# from silently attempting an unsupported jump. Upgrade Cilium manually,
# one minor version at a time, before advancing this pin.
#
# `helm list` failing (API unreachable, RBAC, corrupted Helm storage) and
# "no release found" both leave the command substitution empty - they must
# not be treated the same way. An empty result from a *failed* lookup would
# silently skip this guard and fall through to an unattended install with no
# idea whether an incompatible version is already there, defeating the point
# of the check. Only an empty result from a lookup that *succeeded* means
# "no release yet, safe to proceed."
helm_list_output="$(helm list --namespace kube-system --filter '^cilium$' --output json 2>&1)"
if [ $? -ne 0 ]; then
  echo "### Could not check for an existing Cilium Helm release:" >&2
  echo "$helm_list_output" >&2
  exit 1
fi

current_release_version="$(printf '%s' "$helm_list_output" | python3 -c 'import json, sys
releases = json.load(sys.stdin)
print(releases[0]["app_version"] if releases else "")')"
if [ $? -ne 0 ]; then
  echo "### Could not parse Cilium release version from helm list output" >&2
  exit 1
fi

if [ -n "$current_release_version" ] && [ "$current_release_version" != "$CILIUM_TARGET_VERSION" ]; then
  echo "### Cilium is Helm-managed at version ${current_release_version}, not ${CILIUM_TARGET_VERSION}." >&2
  echo "### Refusing to jump versions automatically - Cilium only supports upgrading" >&2
  echo "### one minor version at a time. Upgrade it manually first:" >&2
  echo "### https://docs.cilium.io/en/stable/operations/upgrade/" >&2
  exit 1
fi

if ! helm upgrade --install cilium cilium/cilium --version "$CILIUM_TARGET_VERSION" \
  --namespace kube-system \
  --set ipam.mode=cluster-pool \
  --set kubeProxyReplacement=false; then
  echo "### Cilium Helm install failed" >&2
  exit 1
fi

if ! kubectl -n kube-system rollout status daemonset/cilium --timeout=120s; then
  echo "### Cilium daemonset failed to roll out" >&2
  exit 1
fi

# ipam.mode=cluster-pool means agent pods wait on cilium-operator to
# allocate their node's PodCIDR, so the DaemonSet rolling out successfully
# doesn't guarantee the cluster is actually functional without this too.
if ! kubectl -n kube-system rollout status deployment/cilium-operator --timeout=120s; then
  echo "### Cilium operator failed to roll out" >&2
  exit 1
fi

echo "### Cilium Installed"

# Apply cilium network policy
# echo "### Setting up Cilium Network Policy..."
# cat /code/scripts/workers/code_upload_worker_utils/network_policies.yaml | sed "s/{{EVALAI_DNS}}/$EVALAI_DNS/" | kubectl apply -f -
# echo "### Cilium EvalAI Network Policy Installed"

# Set ssl-certificate
echo $CERTIFICATE | base64 --decode > scripts/workers/certificate.crt

# Running Code Upload Worker
python -m scripts.workers.code_upload_submission_worker
echo "### Worker Started"

