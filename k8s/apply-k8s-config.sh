#!/bin/bash
# Script to apply Kubernetes configuration for the Transformation Engine

# Exit on error
set -e

# Default namespace
NAMESPACE="code-analysis"

# Help message
function show_help {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -n, --namespace NS      Kubernetes namespace (default: code-analysis)"
    echo "  -t, --token TOKEN       GitHub Personal Access Token (optional)"
    echo "  -u, --username USERNAME GitHub Username (optional)"
    echo "  -h, --help              Show this help message"
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -t|--token)
            GITHUB_TOKEN="$2"
            shift 2
            ;;
        -u|--username)
            GIT_USERNAME="$2"
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

# Check if namespace exists, create if not
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo "Creating namespace: $NAMESPACE"
    kubectl create namespace "$NAMESPACE"
fi

# Create GitHub secret if credentials are provided
if [ -n "$GITHUB_TOKEN" ] && [ -n "$GIT_USERNAME" ]; then
    echo "Creating GitHub secret..."
    ./create-github-secret.sh --token "$GITHUB_TOKEN" --username "$GIT_USERNAME" --namespace "$NAMESPACE"
fi

# Apply ConfigMap
echo "Applying ConfigMap..."
kubectl apply -f configmap.yaml

# Apply Secrets
echo "Applying Secrets..."
kubectl apply -f secret-template.yaml

# Apply Deployment
echo "Applying Deployment..."
kubectl apply -f deployment.yaml

# Apply Service
echo "Applying Service..."
kubectl apply -f service.yaml

# Apply HorizontalPodAutoscaler
echo "Applying HorizontalPodAutoscaler..."
kubectl apply -f hpa.yaml

echo "Kubernetes configuration applied successfully!"
echo "To check the status of the deployment, run:"
echo "kubectl get pods -n $NAMESPACE"
