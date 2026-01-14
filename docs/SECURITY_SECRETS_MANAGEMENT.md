# Security: Secrets Management Best Practices

## Overview

This document outlines best practices for managing secrets in the EvalAI application to prevent credential leakage and unauthorized access.

## Current Issues

### 1. Secrets Passed to Worker Containers

The application currently passes sensitive credentials to ECS/EKS worker containers through environment variables:
- Database passwords (RDS_PASSWORD)
- AWS credentials
- Email host passwords
- ~~Django SECRET_KEY~~ (removed in this PR)

### 2. Default AWS Credentials

The codebase contains default values of "x" for AWS credentials, which should never have defaults.

## Recommended Solutions

### For Production: Use AWS Secrets Manager

#### Step 1: Store Secrets in AWS Secrets Manager

```bash
# Store database password
aws secretsmanager create-secret \
    --name evalai/prod/db-password \
    --secret-string "your-secure-password"

# Store email credentials
aws secretsmanager create-secret \
    --name evalai/prod/email-password \
    --secret-string "your-email-password"
```

#### Step 2: Update IAM Roles

Grant ECS task execution role permission to read secrets:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:region:account-id:secret:evalai/*"
      ]
    }
  ]
}
```

#### Step 3: Reference Secrets in Task Definitions

Instead of passing values directly, reference secrets:

```python
# In task_definitions.py
{
    "name": "RDS_PASSWORD",
    "valueFrom": "arn:aws:secretsmanager:region:account-id:secret:evalai/prod/db-password"
}
```

### For Development: Use Environment-Specific Secrets

Development secrets should:
1. Never be committed to version control
2. Be stored in `.env` files that are `.gitignore`d
3. Use clearly marked test/dev values

Example `.env.example`:
```bash
SECRET_KEY=your-secret-key-here
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
RDS_PASSWORD=your-db-password
```

## Changes Made in This PR

### 1. Removed SECRET_KEY from Worker Environment

- **Before**: Django SECRET_KEY passed to all worker containers
- **After**: Removed from COMMON_SETTINGS_DICT
- **Impact**: Workers should use their own authentication mechanism or retrieve from Secrets Manager

### 2. Added Security Warnings

Added documentation warnings in `aws_utils.py` for remaining secrets that should be migrated to AWS Secrets Manager.

### 3. Created This Documentation

Provides clear guidance for implementing proper secrets management.

## Migration Checklist

### Immediate Actions (Required)
- [ ] Remove hardcoded AWS credentials defaults
- [ ] Audit all locations where secrets are passed to containers
- [ ] Add `.env` to `.gitignore` if not already present

### Short-term (Recommended)
- [ ] Implement AWS Secrets Manager for production
- [ ] Rotate all existing credentials
- [ ] Update task definitions to use `valueFrom` for secrets
- [ ] Remove database passwords from environment variables

### Long-term (Best Practice)
- [ ] Implement automated secret rotation
- [ ] Use AWS IAM roles for AWS SDK authentication instead of keys
- [ ] Consider using AWS Systems Manager Parameter Store for non-sensitive configuration
- [ ] Implement secret scanning in CI/CD pipeline (e.g., git-secrets, truffleHog)

## Security Checklist

### Never Do This ❌
- Store secrets in code
- Commit secrets to version control
- Use default or weak secrets
- Share secrets via email or chat
- Log secrets in application logs
- Pass secrets as command-line arguments

### Always Do This ✅
- Use secrets management services (AWS Secrets Manager, HashiCorp Vault)
- Rotate secrets regularly
- Use environment-specific secrets
- Implement least-privilege access
- Audit secret access
- Use encrypted connections for secret transmission

## Additional Resources

- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)

## Questions?

For security concerns or questions about secrets management, please:
1. Contact the security team
2. Do NOT post secrets in issue trackers or chat
3. Follow responsible disclosure practices
