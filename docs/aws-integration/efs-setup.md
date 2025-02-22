Sure! Here's the documentation for integrating AWS Elastic File System (EFS) for static code upload in CloudCV, formatted as a markdown file named `efs-setup.md`:

```markdown
# Documentation: AWS Elastic File System (EFS) Integration for Static Code Upload in CloudCV

## **Overview**
This documentation provides a comprehensive guide to integrating AWS Elastic File System (EFS) for the static code upload feature in CloudCV. EFS enables scalable and persistent storage to handle large-scale data uploads seamlessly. Follow the steps below to configure, mount, and use EFS within your environment.

---

## **Prerequisites**
Ensure the following requirements are met before starting:
- An active AWS account.
- IAM permissions to create and manage EFS, EC2 instances, and security groups.
- Installed AWS CLI (v2 or higher).
- SSH access to the EC2 instance used for the upload pipeline.

---

## **Step 1: Create an EFS File System**
1. **Log in** to the AWS Management Console and navigate to **Elastic File System (EFS)**.
2. Click **Create File System** and configure:
   - **VPC**: Select the same VPC as your EC2 instance.
   - **Performance Mode**: General Purpose is recommended for most use cases.
   - **Throughput Mode**: Choose between Bursting or Provisioned based on workload.
3. Click **Create** to provision the EFS and note down its ID for later use.

---

## **Step 2: Configure Security Groups**
1. **Update EFS Security Group**:
   - Add an inbound rule to allow NFS traffic (port 2049) from the EC2 instance's security group.
2. **Update EC2 Security Group**:
   - Add an outbound rule to allow NFS traffic to the EFS security group.

---

## **Step 3: Mount EFS on EC2 Instance**
1. **Install the NFS client**:
   ```bash
   sudo apt update && sudo apt install -y nfs-common   # For Ubuntu/Debian
   sudo yum install -y nfs-utils                      # For Amazon Linux/CentOS
   ```
2. **Create a mount directory**:
   ```bash
   sudo mkdir -p /mnt/efs
   ```
3. **Mount the EFS file system**:
   ```bash
   sudo mount -t nfs4 -o nfsvers=4.1 fs-<EFS-ID>.efs.<region>.amazonaws.com:/ /mnt/efs
   ```
4. **Verify the mount**:
   ```bash
   df -h | grep efs
   ```

---

## **Step 4: Automate Mounting**
To make the EFS mount persistent across reboots:
1. Edit the `/etc/fstab` file:
   ```plaintext
   fs-<EFS-ID>.efs.<region>.amazonaws.com:/ /mnt/efs nfs4 defaults,_netdev 0 0
   ```
2. Test the configuration:
   ```bash
   sudo umount /mnt/efs
   sudo mount -a
   ```

---

## **Step 5: Upload Data to EFS**
Transfer files to the mounted EFS directory:
```bash
scp -i <key.pem> <local-file-path> ec2-user@<EC2-IP>:/mnt/efs/
```

---

## **Step 6: Integrate with CloudCV**
1. **Update Configuration**:
   - Modify the `code-upload` pipeline’s configuration to use the mounted EFS directory as the upload target.
   - Example: Set the upload path to `/mnt/efs` in `settings.py` or `config.yaml`.
2. **Test Integration**:
   - Run a sample upload to confirm the integration is working correctly.

---

## **Troubleshooting**
- **Permission Denied**: Verify the IAM roles, security group rules, and mount permissions.
- **Mount Failure**: Ensure the EC2 instance and EFS are in the same VPC.
- **Slow Transfers**: Optimize the throughput mode or consider enabling encryption.