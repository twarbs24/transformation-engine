#!/bin/bash
# Script to create a Kubernetes secret for GitHub webhook

set -e

# Check if webhook secret is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <webhook-secret>"
  echo "Example: $0 my-webhook-secret"
  exit 1
fi

WEBHOOK_SECRET=$1
NAMESPACE="code-analysis"

# Create base64 encoded values
WEBHOOK_SECRET_B64=$(echo -n "$WEBHOOK_SECRET" | base64)

# Create secret YAML
cat > webhook-secret.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: github-webhook-secret
  namespace: ${NAMESPACE}
type: Opaque
data:
  webhook-secret: ${WEBHOOK_SECRET_B64}
EOF

# Apply the secret
kubectl apply -f webhook-secret.yaml

# Clean up
rm webhook-secret.yaml

echo "GitHub webhook secret created in namespace ${NAMESPACE}"
