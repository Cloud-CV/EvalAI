#!/bin/bash

#installing AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
echo "### AWS CLI Installed"

aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
aws configure set aws_secret_access $AWS_SECRET_ACCESS_KEY
aws configure set default.region $AWS_DEFAULT_REGION
echo "### AWS CLI Configured"

#install iam-authenticator
curl -o aws-iam-authenticator https://amazon-eks.s3.us-west-2.amazonaws.com/1.17.7/2020-07-08/bin/linux/amd64/aws-iam-authenticator
chmod +x ./aws-iam-authenticator
mkdir -p $HOME/bin && cp ./aws-iam-authenticator $HOME/bin/aws-iam-authenticator && export PATH=$PATH:$HOME/bin
echo 'export PATH=$PATH:$HOME/bin' >> ~/.bashrc
echo "### iam-authenticator Installed"

#configure kubeconfig
mkdir ~/.kube
echo "### Kube config Configured"

#install kubectl
curl -LO "https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x ./kubectl
sudo mv ./kubectl /usr/local/bin/kubectl
echo "### Kubectl Installed"

# install aws-container-insights
curl https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluentd-quickstart.yaml | sed "s/{{$CLUSTER_NAME}}/cluster-name/;s/{{$AWS_DEFAULT_REGION}}/cluster-region/" | kubectl apply -f -
echo "### Container Insights Installed"

# install calico
# Calico is being used to provide networking and network policy, in either overlay or non-overlay networking modes. 
kubectl apply -f https://raw.githubusercontent.com/aws/amazon-vpc-cni-k8s/release-1.6/config/v1.6/calico.yaml
echo "### Calico Installed"
