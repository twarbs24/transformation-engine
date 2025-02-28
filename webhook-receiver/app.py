#!/usr/bin/env python3
"""
GitHub Webhook Receiver for Transformation Engine

This service receives GitHub webhook events and triggers appropriate
transformations in the Transformation Engine.
"""

import os
import sys
import json
import hmac
import hashlib
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuration
GITHUB_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET")
TRANSFORMATION_API_URL = os.environ.get("TRANSFORMATION_API_URL", "http://localhost:8081")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

def verify_signature(payload_body, signature_header):
    """Verify that the webhook payload was sent from GitHub by validating the signature."""
    if not GITHUB_SECRET or not signature_header:
        return False
    
    # The signature header starts with 'sha256='
    sha_name, signature = signature_header.split('=')
    if sha_name != 'sha256':
        return False
    
    # Create the expected signature
    mac = hmac.new(GITHUB_SECRET.encode(), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = mac.hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(expected_signature, signature)

def trigger_transformation(repo_url, branch, files=None):
    """Trigger a transformation job via the API."""
    url = f"{TRANSFORMATION_API_URL}/api/v1/transform"
    
    payload = {
        "repository_url": repo_url,
        "branch": branch,
        "transformation_type": "REFACTOR",  # Default transformation type
        "verification_level": "STANDARD",   # Default verification level
        "safe_mode": True
    }
    
    if files:
        payload["files"] = files
    
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error triggering transformation: {e}")
        return {"error": str(e)}

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle GitHub webhook events."""
    # Verify signature
    signature = request.headers.get('X-Hub-Signature-256')
    if GITHUB_SECRET and not verify_signature(request.data, signature):
        app.logger.warning("Invalid signature")
        return jsonify({"error": "Invalid signature"}), 401
    
    # Parse event
    event = request.headers.get('X-GitHub-Event')
    payload = request.json
    
    if not event or not payload:
        return jsonify({"error": "Missing event or payload"}), 400
    
    # Handle push event
    if event == 'push':
        repo_url = payload.get('repository', {}).get('clone_url')
        branch = payload.get('ref', '').replace('refs/heads/', '')
        
        if not repo_url or not branch:
            return jsonify({"error": "Missing repository URL or branch"}), 400
        
        # Get changed files
        commits = payload.get('commits', [])
        files = set()
        for commit in commits:
            files.update(commit.get('added', []))
            files.update(commit.get('modified', []))
        
        # Filter for supported file types
        supported_extensions = ['.py', '.js', '.ts', '.java']
        files = [f for f in files if any(f.endswith(ext) for ext in supported_extensions)]
        
        if not files:
            return jsonify({"message": "No supported files changed"}), 200
        
        # Trigger transformation
        result = trigger_transformation(repo_url, branch, list(files))
        return jsonify(result), 200
    
    # Handle pull request event
    elif event == 'pull_request':
        action = payload.get('action')
        if action not in ['opened', 'synchronize']:
            return jsonify({"message": f"Ignoring pull request action: {action}"}), 200
        
        repo_url = payload.get('repository', {}).get('clone_url')
        branch = payload.get('pull_request', {}).get('head', {}).get('ref')
        
        if not repo_url or not branch:
            return jsonify({"error": "Missing repository URL or branch"}), 400
        
        # Trigger transformation
        result = trigger_transformation(repo_url, branch)
        return jsonify(result), 200
    
    # Ignore other events
    return jsonify({"message": f"Ignoring event: {event}"}), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8082))
    app.run(host='0.0.0.0', port=port)
