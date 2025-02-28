#!/bin/bash
# Script to create Kubernetes secrets for the Transformation Engine

# Set your actual values here
MONGO_URI="mongodb://username:password@host:port/database"

# Create namespace if it doesn't exist
kubectl create namespace code-analysis --dry-run=client -o yaml | kubectl apply -f -

# Create the secret
kubectl create secret generic transformation-engine-secrets \
  --namespace=code-analysis \
  --from-literal=mongo_uri="$MONGO_URI" \
  --dry-run=client -o yaml > secret.yaml

echo "Secret manifest generated as secret.yaml"
echo "Review the file and then apply with: kubectl apply -f secret.yaml"

# Note: For production, consider using a secrets management solution like:
# - Hashicorp Vault
# - AWS Secrets Manager
# - Azure Key Vault
# - Google Secret Manager
