#!/bin/bash

# Check if SLACK_WEBHOOK_URL is provided
if [ -z "$SLACK_WEBHOOK_URL" ]; then
  echo "Please provide your Slack webhook URL:"
  read -s SLACK_WEBHOOK_URL
  echo
fi

# Create the secret
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic alertmanager-secrets \
  --namespace monitoring \
  --from-literal=SLACK_WEBHOOK_URL=$SLACK_WEBHOOK_URL \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Alertmanager secrets created successfully."
echo "To use a different Slack webhook URL, run this script again with the new URL."
