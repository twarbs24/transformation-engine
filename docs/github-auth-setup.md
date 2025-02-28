# GitHub Authentication Setup

This document provides instructions for setting up GitHub authentication for the Transformation Engine and API Service.

## Prerequisites

1. A GitHub account
2. A GitHub Personal Access Token (PAT) with appropriate permissions

## Creating a GitHub Personal Access Token

1. Log in to your GitHub account
2. Go to Settings > Developer settings > Personal access tokens > Tokens (classic)
3. Click "Generate new token" and select "Generate new token (classic)"
4. Give your token a descriptive name
5. Select the following scopes:
   - `repo` (Full control of private repositories)
   - `read:org` (Read organization membership)
   - `workflow` (if you need to trigger GitHub Actions workflows)
6. Click "Generate token"
7. Copy the token immediately (you won't be able to see it again)

## Setting Up Authentication

### Option 1: Using the Setup Script (Recommended)

The setup script will configure GitHub authentication for both local development and Kubernetes deployment.

```bash
./setup-github-auth.sh --token YOUR_GITHUB_TOKEN --username YOUR_GITHUB_USERNAME
```

### Option 2: Manual Setup

#### For Local Development

1. Set environment variables:

```bash
export GITHUB_TOKEN=your_github_token
export GIT_USERNAME=your_github_username
```

2. Add these variables to your `.env` file:

```
GITHUB_TOKEN=your_github_token
GIT_USERNAME=your_github_username
```

#### For Kubernetes Deployment

1. Create a Kubernetes secret:

```bash
cd mcp-server-implementation/transformation-engine/k8s
./create-github-secret.sh --token YOUR_GITHUB_TOKEN --username YOUR_GITHUB_USERNAME
```

2. Ensure the deployment is configured to use these secrets (check `deployment.yaml`)

## Verifying Authentication

To verify that GitHub authentication is working correctly:

1. Check the API service status:

```bash
curl http://localhost:8082/api/v1/status
```

The response should include `"github_auth": true` if authentication is configured.

2. Try cloning a private repository:

```bash
cd /tmp
git clone https://github.com/your-org/your-private-repo.git
```

If authentication is working correctly, the repository should clone without prompting for credentials.

## Troubleshooting

If you encounter authentication issues:

1. Verify that your GitHub token has the correct permissions
2. Check that the environment variables are set correctly
3. Ensure the Kubernetes secrets are created and mounted properly
4. Check the logs for any authentication errors:

```bash
kubectl logs -n code-analysis deployment/transformation-engine
```
