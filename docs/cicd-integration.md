# CI/CD Integration for Transformation Engine

This document describes how to integrate the Transformation Engine with CI/CD pipelines and GitHub repositories.

## Overview

The Transformation Engine can be integrated with CI/CD pipelines in several ways:

1. **GitHub Actions Workflow**: Automatically run transformations on push or pull request events
2. **Kubernetes CronJob**: Schedule periodic transformations on repositories
3. **GitHub Webhook Receiver**: Receive GitHub webhook events and trigger transformations
4. **Command Line Script**: Trigger transformations from any CI/CD pipeline

## GitHub Actions Integration

### Setup Instructions

1. Copy the `.github/workflows/auto-transform.yml` file to your repository
2. Customize the workflow as needed:
   - Adjust the transformation type
   - Configure verification levels
   - Set safe mode options

### Configuration Options

The GitHub Actions workflow supports the following configuration options:

- **Transformation Type**: REFACTOR, OPTIMIZE, PRUNE, MERGE, MODERNIZE, FIX_SECURITY
- **Verification Level**: NONE, BASIC, STANDARD, STRICT
- **Safe Mode**: true/false

### Manual Triggering

You can manually trigger the workflow from the GitHub Actions tab with custom parameters.

## Kubernetes CronJob

### Setup Instructions

1. Create the scripts ConfigMap:
   ```bash
   ./k8s/create-scripts-configmap.sh
   ```

2. Customize the CronJob configuration in `k8s/cronjob.yaml`:
   - Set the repository URL
   - Configure the schedule
   - Adjust transformation parameters

3. Apply the CronJob:
   ```bash
   kubectl apply -f k8s/cronjob.yaml
   ```

## GitHub Webhook Receiver

The webhook receiver is a service that listens for GitHub webhook events and triggers transformations.

### Setup Instructions

1. Build and deploy the webhook receiver:
   ```bash
   cd webhook-receiver
   docker build -t webhook-receiver:latest .
   # Push to your registry
   ```

2. Create the webhook secret:
   ```bash
   ./k8s/create-webhook-secret.sh <your-webhook-secret>
   ```

3. Deploy the webhook receiver:
   ```bash
   kubectl apply -f k8s/webhook-receiver-deployment.yaml
   ```

4. Configure GitHub webhooks:
   - Go to your repository settings
   - Add a webhook with the URL of your webhook receiver
   - Set the secret to match your webhook secret
   - Select events: push, pull request

## Command Line Integration

The `trigger-transformation.py` script can be used to trigger transformations from any CI/CD pipeline.

### Usage

```bash
python scripts/trigger-transformation.py \
  --repo-url https://github.com/your-org/your-repo.git \
  --branch main \
  --transformation-type REFACTOR \
  --verification-level STANDARD \
  --api-url http://transformation-engine-api-url \
  --wait
```

### Jenkins Integration Example

```groovy
pipeline {
    agent any
    
    stages {
        stage('Transform Code') {
            steps {
                sh '''
                python /path/to/trigger-transformation.py \
                  --repo-url ${GIT_URL} \
                  --branch ${BRANCH_NAME} \
                  --transformation-type REFACTOR \
                  --verification-level STANDARD \
                  --api-url http://transformation-engine-api-url \
                  --wait
                '''
            }
        }
    }
}
```

## Security Considerations

- Store GitHub tokens securely in Kubernetes secrets
- Use webhook secrets to verify GitHub webhook payloads
- Limit access to the transformation API
- Review transformations before merging to production branches

## Monitoring

The transformation engine exposes metrics that can be monitored:

- Transformation success rate
- Transformation duration
- Error rates

Configure alerts for:
- High error rates
- Low verification success rates
- Slow transformations

## Troubleshooting

### Common Issues

1. **Authentication Failures**:
   - Verify GitHub token has correct permissions
   - Check token expiration

2. **Webhook Not Triggering**:
   - Verify webhook secret
   - Check webhook receiver logs
   - Ensure correct events are configured

3. **Transformation Failures**:
   - Check transformation engine logs
   - Verify repository access
   - Check for syntax errors in code

### Logs

Access logs for troubleshooting:

```bash
# Transformation Engine logs
kubectl logs -n code-analysis deployment/transformation-engine

# Webhook Receiver logs
kubectl logs -n code-analysis deployment/webhook-receiver
```
