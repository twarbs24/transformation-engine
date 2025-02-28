# Setting Up GitHub Secrets for CI/CD

This document explains how to set up the necessary secrets in your GitHub repository for the CI/CD pipeline.

## Required Secrets

The following secrets need to be configured in your GitHub repository:

1. `SONAR_TOKEN` - SonarQube/SonarCloud authentication token
2. `KUBE_CONFIG` - Base64-encoded Kubernetes configuration file
3. `DOCKER_USERNAME` (optional) - Docker Hub username if using Docker Hub instead of GitHub Container Registry
4. `DOCKER_PASSWORD` (optional) - Docker Hub password if using Docker Hub instead of GitHub Container Registry

## Setting Up Secrets in GitHub

1. Navigate to your GitHub repository
2. Click on "Settings" tab
3. In the left sidebar, click on "Secrets and variables" → "Actions"
4. Click on "New repository secret"
5. Add each secret with its name and value

## Obtaining Secret Values

### SONAR_TOKEN

1. Log in to your SonarCloud account at https://sonarcloud.io/
2. Go to "My Account" → "Security"
3. Generate a new token with a meaningful name (e.g., "github-transformation-engine")
4. Copy the token value immediately (it will only be shown once)

### KUBE_CONFIG

1. Locate your Kubernetes config file (typically at `~/.kube/config`)
2. Encode it as Base64:
   ```bash
   cat ~/.kube/config | base64
   ```
3. Copy the entire output string

> **IMPORTANT**: Make sure your kubeconfig doesn't contain any sensitive information that shouldn't be exposed to CI/CD systems. Consider creating a service account with limited permissions specifically for CI/CD.

## Creating a Service Account for CI/CD

For better security, create a dedicated Kubernetes service account for your CI/CD pipeline:

```bash
# Create a service account
kubectl create serviceaccount github-actions -n code-analysis

# Create a role with limited permissions
kubectl create role deployment-manager \
  --verb=get,list,watch,create,update,patch,delete \
  --resource=deployments,services,configmaps,pods \
  -n code-analysis

# Bind the role to the service account
kubectl create rolebinding github-actions-deployment-manager \
  --role=deployment-manager \
  --serviceaccount=code-analysis:github-actions \
  -n code-analysis

# Get the token for the service account (Kubernetes 1.24+)
kubectl create token github-actions -n code-analysis
```

Use this token in a kubeconfig file specifically for CI/CD.
