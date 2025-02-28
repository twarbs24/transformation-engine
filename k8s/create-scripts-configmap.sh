#!/bin/bash
# Script to create a ConfigMap containing transformation scripts

set -e

# Directory containing this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
SCRIPTS_DIR="$REPO_ROOT/transformation-engine/scripts"

# Create temporary directory for scripts
TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

# Copy scripts to temporary directory
cp "$SCRIPTS_DIR/trigger-transformation.py" "$TMP_DIR/"

# Create ConfigMap
kubectl create configmap transformation-scripts \
  --namespace code-analysis \
  --from-file="$TMP_DIR/trigger-transformation.py" \
  --dry-run=client -o yaml > "$SCRIPT_DIR/scripts-configmap.yaml"

echo "ConfigMap YAML created at $SCRIPT_DIR/scripts-configmap.yaml"
echo "To apply, run: kubectl apply -f $SCRIPT_DIR/scripts-configmap.yaml"
