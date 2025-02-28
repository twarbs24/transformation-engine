#!/bin/bash

# Set default values
ADMIN_USER=${GRAFANA_ADMIN_USER:-admin}
ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-$(openssl rand -base64 12)}

# Create the secret
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic grafana-admin-credentials \
  --namespace monitoring \
  --from-literal=admin-user=$ADMIN_USER \
  --from-literal=admin-password=$ADMIN_PASSWORD \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Grafana admin credentials created:"
echo "Username: $ADMIN_USER"
echo "Password: $ADMIN_PASSWORD"
echo
echo "Save these credentials in a secure location."
