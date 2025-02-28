#!/usr/bin/env python3
"""
Test script to verify GitHub authentication is working correctly.
This script will:
1. Check if GitHub credentials are set
2. Attempt to clone a private repository
3. Report success or failure
"""

import os
import sys
import tempfile
import shutil
import subprocess
import argparse
from pathlib import Path

def check_credentials():
    """Check if GitHub credentials are set."""
    github_token = os.environ.get("GITHUB_TOKEN")
    git_username = os.environ.get("GIT_USERNAME")
    
    if not github_token:
        print("❌ GITHUB_TOKEN environment variable is not set")
        return False
    
    if not git_username:
        print("❌ GIT_USERNAME environment variable is not set")
        return False
    
    print(f"✅ GitHub credentials found for user: {git_username}")
    return True

def test_clone_repository(repo_url):
    """Test cloning a repository with GitHub authentication."""
    temp_dir = tempfile.mkdtemp()
    try:
        print(f"🔄 Attempting to clone repository: {repo_url}")
        print(f"🔄 Using temporary directory: {temp_dir}")
        
        result = subprocess.run(
            ["git", "clone", repo_url, temp_dir],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ Repository cloned successfully!")
            # Count files to verify clone worked
            file_count = sum(1 for _ in Path(temp_dir).rglob('*') if _.is_file())
            print(f"✅ Repository contains {file_count} files")
            return True
        else:
            print("❌ Failed to clone repository")
            print(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Clone operation timed out")
        return False
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
        return False
    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    parser = argparse.ArgumentParser(description="Test GitHub authentication")
    parser.add_argument(
        "--repo", 
        default="https://github.com/autogenic-ai/transformation-engine.git",
        help="Repository URL to test cloning (default: https://github.com/autogenic-ai/transformation-engine.git)"
    )
    args = parser.parse_args()
    
    print("🔍 Testing GitHub Authentication")
    print("===============================")
    
    if not check_credentials():
        print("\n❌ GitHub authentication test failed: Missing credentials")
        print("Please set the GITHUB_TOKEN and GIT_USERNAME environment variables.")
        print("You can use the setup-github-auth.sh script to set these variables.")
        sys.exit(1)
    
    if test_clone_repository(args.repo):
        print("\n✅ GitHub authentication test passed!")
        print("The system is correctly configured to access GitHub repositories.")
        sys.exit(0)
    else:
        print("\n❌ GitHub authentication test failed: Could not clone repository")
        print("Please check your GitHub token permissions and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
