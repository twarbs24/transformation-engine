#!/bin/bash
# Script to create Kubernetes secret with GitHub credentials

# Exit on error
set -e

# Default namespace
NAMESPACE="code-analysis"

# Help message
function show_help {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -t, --token TOKEN       GitHub Personal Access Token"
    echo "  -u, --username USERNAME GitHub Username"
    echo "  -n, --namespace NS      Kubernetes namespace (default: code-analysis)"
    echo "  -h, --help              Show this help message"
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -t|--token)
            GITHUB_TOKEN="$2"
            shift 2
            ;;
        -u|--username)
            GIT_USERNAME="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            ;;
    esac
done

# Check if required parameters are provided
if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GitHub token is required"
    show_help
fi

if [ -z "$GIT_USERNAME" ]; then
    echo "Error: GitHub username is required"
    show_help
fi

# Encode secrets in base64
ENCODED_TOKEN=$(echo -n "$GITHUB_TOKEN" | base64)
ENCODED_USERNAME=$(echo -n "$GIT_USERNAME" | base64)

# Check if secret already exists
if kubectl get secret transformation-engine-secrets -n "$NAMESPACE" &> /dev/null; then
    echo "Secret already exists, updating..."
    kubectl patch secret transformation-engine-secrets -n "$NAMESPACE" -p "{\"data\":{\"github_token\":\"$ENCODED_TOKEN\",\"git_username\":\"$ENCODED_USERNAME\"}}"
else
    echo "Creating new secret..."
    # Create the secret
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: transformation-engine-secrets
  namespace: $NAMESPACE
type: Opaque
data:
  github_token: $ENCODED_TOKEN
  git_username: $ENCODED_USERNAME
EOF
fi

echo "Secret created/updated successfully!"
