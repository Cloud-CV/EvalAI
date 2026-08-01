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
helm repo add --force-update cilium https://helm.cilium.io/
helm repo update cilium

# One-time migration: clusters bootstrapped before this change installed
# Cilium via `kubectl create` against a raw quick-install.yaml, so those
# resources carry no Helm ownership metadata. Helm refuses to adopt them
# ("invalid ownership metadata") and errors out instead of upgrading. If no
# Helm release named "cilium" is tracked yet but the legacy ConfigMap is
# still present, this is one of those clusters - remove the legacy install
# first so the Helm install below starts clean.
if ! helm status cilium --namespace kube-system >/dev/null 2>&1 && \
   kubectl get configmap cilium-config -n kube-system >/dev/null 2>&1; then
  echo "### Migrating legacy (non-Helm) Cilium install"
  kubectl delete -f https://raw.githubusercontent.com/cilium/cilium/v1.9/install/kubernetes/quick-install.yaml --ignore-not-found
fi

if ! helm upgrade --install cilium cilium/cilium --version 1.19.6 \
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

