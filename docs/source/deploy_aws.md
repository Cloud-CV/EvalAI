## Deploying EvalAI on EC2 with AWS

Deploying EvalAI on-prem is now easier using the deployment script. This version of the deployment script spins up a prod version of EvalAI with AWS workers, to use EvalAI dev version, see the previous guide.

### 1. Getting the AWS resources ready

Firstly, create two VPCs. First VPC will contain all the servers (prod instances and worker instances) and second will contain the RDS Database. Set the inbound and outbound rules for the two VPCs accordingly.

Next, create a CloudWatch Logs role for the EC2 instance to log the data.

Next, start up a Postgres RDS database instance and note the **RDS_HOSTNAME**, **RDS_DB_NAME**, **RDS_USERNAME**, **RDS_PASSWORD**.

Next, create an S3 bucket for static and media files. Note the **AWS_STORAGE_BUCKET_NAME**.

Next, Verify your email on AWS SES & request for production access (without prod access you won't be able to send registration verification emails). Along with that, download the SMTP access keys & note your **EMAIL_HOST_USER**, **EMAIL_HOST_PASSWORD** from the creds section.

Next, register your EvalAI project with Sentry and note the **SENTRY_URL** (DSN url).

Next, Create an ECS cluster : Cluster -> Create Cluster -> EC2 Linux + Networking -> (For VPC, SG : Select the same SG & VPC as EC2 instance & choose any 2 subnets) -> Select the default ecsTaskExecutionRole for execution role -> Create. After creation, note the **CLUSTER**, **EXECUTION_ROLE_ARN**, **SUBNET_1**, **SUBNET_2**, **SUBNET_SECURITY_GROUP**. Since, you created the ECS cluster with the default execution role (ecsTaskExecutionRole), attach the cloudwatch logs policy and RDSFullDataAccess policy to ecsTaskExecutionRole

### 2. Getting the VM instance and routing ready

Set up an EC2 Ubuntu VM instance (attach the earlier created CloudWatch Logs role) and set the traffic to route to the IP address of VM instance.

### 3. Clone and checkout the deployment branch

Now that you have got the instance ready, simply SSH into your instance. Then, clone the project and check out the deployment script branch.

```
git clone https://github.com/Cloud-CV/EvalAI.git && cd EvalAI
git fetch origin pull/2978/head:v2_deploy
git checkout v2_deploy
```

### 4. Run the deployment script

To run the deployment script, run the following command : 

```
./scripts/ec2_deployment/deploy-aws.sh
```

Then, input the fields (use the default values in braces when appropriate) and you're done !