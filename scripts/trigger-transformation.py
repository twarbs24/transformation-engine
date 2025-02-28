#!/usr/bin/env python3
"""
Script to trigger code transformations via the Transformation Engine API.
This script can be used in CI/CD pipelines to initiate transformations.
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
import requests
from typing import Dict, List, Any, Optional

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Trigger code transformations')
    
    parser.add_argument('--repo-url', required=True,
                        help='URL of the repository to transform')
    
    parser.add_argument('--branch', default='main',
                        help='Branch to transform (default: main)')
    
    parser.add_argument('--transformation-type', 
                        choices=['REFACTOR', 'OPTIMIZE', 'PRUNE', 'MERGE', 'MODERNIZE', 'FIX_SECURITY'],
                        default='REFACTOR',
                        help='Type of transformation to apply (default: REFACTOR)')
    
    parser.add_argument('--verification-level',
                        choices=['NONE', 'BASIC', 'STANDARD', 'STRICT'],
                        default='STANDARD',
                        help='Level of verification to perform (default: STANDARD)')
    
    parser.add_argument('--safe-mode', action='store_true', default=True,
                        help='Only apply verified transformations (default: True)')
    
    parser.add_argument('--api-url', default='http://localhost:8081',
                        help='URL of the Transformation Engine API (default: http://localhost:8081)')
    
    parser.add_argument('--files', nargs='+',
                        help='Specific files to transform (optional)')
    
    parser.add_argument('--wait', action='store_true',
                        help='Wait for transformation to complete')
    
    parser.add_argument('--timeout', type=int, default=600,
                        help='Timeout in seconds when waiting (default: 600)')
    
    parser.add_argument('--preferred-model',
                        default=os.environ.get('PREFERRED_MODEL', 'deepseek-coder:latest'),
                        help='Preferred model to use for transformations (overrides environment variable)')
    
    parser.add_argument('--fallback-model',
                        default=os.environ.get('FALLBACK_MODEL', 'qwen:7b'),
                        help='Fallback model to use for transformations (overrides environment variable)')
    
    parser.add_argument('--specialized-model',
                        default=os.environ.get('SPECIALIZED_MODEL', 'codellama:latest'),
                        help='Specialized model to use for complex transformations (overrides environment variable)')
    
    return parser.parse_args()

def trigger_transformation(args) -> Dict[str, Any]:
    """Trigger a transformation job via the API."""
    url = f"{args.api_url}/api/v1/transform"
    
    payload = {
        "repository_url": args.repo_url,
        "branch": args.branch,
        "transformation_type": args.transformation_type,
        "verification_level": args.verification_level,
        "safe_mode": args.safe_mode
    }
    
    if args.files:
        payload["files"] = args.files
    
    # Add model configuration if provided
    if args.preferred_model:
        payload["preferred_model"] = args.preferred_model
    
    if args.fallback_model:
        payload["fallback_model"] = args.fallback_model
    
    if args.specialized_model:
        payload["specialized_model"] = args.specialized_model
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error triggering transformation: {e}")
        sys.exit(1)

def check_job_status(api_url: str, job_id: str) -> Dict[str, Any]:
    """Check the status of a transformation job."""
    url = f"{api_url}/api/v1/transform/{job_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error checking job status: {e}")
        sys.exit(1)

def wait_for_completion(api_url: str, job_id: str, timeout: int) -> Dict[str, Any]:
    """Wait for a transformation job to complete."""
    start_time = time.time()
    poll_interval = 5  # seconds
    
    while time.time() - start_time < timeout:
        status = check_job_status(api_url, job_id)
        
        if status.get("status") in ["completed", "failed"]:
            return status
        
        print(f"Job status: {status.get('status', 'unknown')} - waiting...")
        time.sleep(poll_interval)
    
    print(f"Timeout waiting for job {job_id} to complete")
    return {"status": "timeout", "job_id": job_id}

def get_job_result(api_url: str, job_id: str) -> Dict[str, Any]:
    """Get the results of a completed transformation job."""
    url = f"{api_url}/api/v1/transform/{job_id}/result"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting job results: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    args = parse_args()
    
    print(f"Triggering {args.transformation_type} transformation for {args.repo_url}")
    result = trigger_transformation(args)
    
    job_id = result.get("job_id")
    if not job_id:
        print("Error: No job ID returned")
        sys.exit(1)
    
    print(f"Transformation job started with ID: {job_id}")
    
    if args.wait:
        print(f"Waiting for job to complete (timeout: {args.timeout}s)...")
        status = wait_for_completion(args.api_url, job_id, args.timeout)
        
        if status.get("status") == "completed":
            print("Transformation completed successfully!")
            
            # Get detailed results
            results = get_job_result(args.api_url, job_id)
            
            # Print summary
            files_transformed = results.get("files_transformed", 0)
            files_failed = results.get("files_failed", 0)
            total_files = files_transformed + files_failed
            
            print(f"Transformed {files_transformed}/{total_files} files successfully")
            
            # Print details of transformed files
            transformations = results.get("transformations", [])
            for t in transformations:
                file_path = t.get("file_path", "unknown")
                if t.get("success", False):
                    print(f" {file_path}")
                else:
                    print(f" {file_path}: {t.get('error', 'Unknown error')}")
            
            if files_failed > 0:
                sys.exit(1)
        else:
            print(f"Job did not complete successfully: {status.get('status', 'unknown')}")
            sys.exit(1)
    else:
        print("Job triggered successfully. Use the following command to check status:")
        print(f"curl {args.api_url}/api/v1/transform/{job_id}")

if __name__ == "__main__":
    main()
