"""
Repository Utilities for Transformation Engine

This module provides functionality to work with Git repositories and manage code files.
"""

import os
import shutil
import tempfile
import logging
import subprocess
from typing import Dict, List, Optional, Any
from git import Repo
from git.exc import GitError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RepositoryManager:
    """Manages Git repositories for code transformations."""
    
    def __init__(self, workspace_dir: str):
        """
        Initialize the Repository Manager.
        
        Args:
            workspace_dir: Base directory for workspace repositories
        """
        self.workspace_dir = workspace_dir
        os.makedirs(workspace_dir, exist_ok=True)
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.git_username = os.getenv("GIT_USERNAME")
    
    def set_credentials(self, github_token: str = None, git_username: str = None):
        """
        Set Git credentials for authentication.
        
        Args:
            github_token: GitHub Personal Access Token
            git_username: Git username for authentication
        """
        if github_token:
            self.github_token = github_token
        if git_username:
            self.git_username = git_username
    
    def clone_repository(self, repo_url: str, repo_id: str, branch: str = "main") -> Dict[str, Any]:
        """
        Clone a Git repository to the workspace.
        
        Args:
            repo_url: URL of the Git repository
            repo_id: Unique identifier for the repository
            branch: Branch to checkout
            
        Returns:
            Dictionary containing the result of the operation
        """
        result = {"success": False, "repo_path": None, "error": None}
        repo_path = os.path.join(self.workspace_dir, repo_id)
        
        try:
            # Check if repository already exists
            if os.path.exists(repo_path):
                logger.info(f"Repository {repo_id} already exists, updating instead of cloning")
                result = self.update_repository(repo_id, branch)
                return result
            
            # Add GitHub token to URL if available and it's a GitHub repository
            authenticated_url = repo_url
            if self.github_token and "github.com" in repo_url:
                # Handle different URL formats
                if repo_url.startswith("https://"):
                    # For HTTPS URLs, add token to the URL
                    authenticated_url = repo_url.replace(
                        "https://", 
                        f"https://{self.github_token}@"
                    )
                elif repo_url.startswith("git@"):
                    # For SSH URLs, we don't modify them as they use SSH keys
                    pass
            
            # Clone the repository
            logger.info(f"Cloning repository {repo_id} to {repo_path}")
            # Don't log the authenticated URL as it contains credentials
            repo = Repo.clone_from(authenticated_url, repo_path, branch=branch)
            result["success"] = True
            result["repo_path"] = repo_path
            
        except GitError as e:
            error_msg = f"Git error when cloning repository: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
        except Exception as e:
            error_msg = f"Error cloning repository: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
            
        return result
    
    def update_repository(self, repo_id: str, branch: str = "main") -> Dict[str, Any]:
        """
        Update a previously cloned repository.
        
        Args:
            repo_id: Unique identifier for the repository
            branch: Branch to checkout
            
        Returns:
            Dictionary containing the result of the operation
        """
        result = {"success": False, "repo_path": None, "error": None}
        repo_path = os.path.join(self.workspace_dir, repo_id)
        
        try:
            # Check if repository exists
            if not os.path.exists(repo_path):
                error_msg = f"Repository {repo_id} does not exist in {repo_path}"
                logger.error(error_msg)
                result["error"] = error_msg
                return result
            
            # Open the repository and update it
            repo = Repo(repo_path)
            
            # Fetch all remotes
            for remote in repo.remotes:
                remote.fetch()
            
            # Checkout the specified branch
            repo.git.checkout(branch)
            
            # Pull the latest changes
            repo.remotes.origin.pull()
            
            result["success"] = True
            result["repo_path"] = repo_path
            
        except GitError as e:
            error_msg = f"Git error when updating repository: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
        except Exception as e:
            error_msg = f"Error updating repository: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
            
        return result
    
    def create_working_copy(self, repo_id: str, job_id: str) -> Dict[str, Any]:
        """
        Create a working copy of a repository for transformations.
        
        Args:
            repo_id: Unique identifier for the repository
            job_id: Job identifier for the transformation
            
        Returns:
            Dictionary containing the result of the operation
        """
        result = {"success": False, "working_path": None, "error": None}
        repo_path = os.path.join(self.workspace_dir, repo_id)
        working_path = os.path.join(self.workspace_dir, f"{repo_id}_{job_id}")
        
        try:
            # Check if repository exists
            if not os.path.exists(repo_path):
                error_msg = f"Repository {repo_id} does not exist in {repo_path}"
                logger.error(error_msg)
                result["error"] = error_msg
                return result
            
            # Check if working copy already exists
            if os.path.exists(working_path):
                logger.info(f"Working copy already exists at {working_path}, removing it")
                shutil.rmtree(working_path)
            
            # Create working copy by copying the repository
            logger.info(f"Creating working copy from {repo_path} to {working_path}")
            shutil.copytree(repo_path, working_path, symlinks=True)
            
            # Remove .git directory from working copy to avoid accidental commits
            git_dir = os.path.join(working_path, ".git")
            if os.path.exists(git_dir):
                shutil.rmtree(git_dir)
                
            result["success"] = True
            result["working_path"] = working_path
            
        except Exception as e:
            error_msg = f"Error creating working copy: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
            
        return result
    
    def list_files(self, path: str, languages: Optional[List[str]] = None, 
                   max_size_kb: int = 50) -> List[Dict[str, Any]]:
        """
        List files in a directory with optional filtering.
        
        Args:
            path: Path to the directory
            languages: Optional list of language extensions to include
            max_size_kb: Maximum file size in KB
            
        Returns:
            List of dictionaries containing file information
        """
        files_list = []
        
        try:
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, path)
                    
                    # Skip hidden files and directories
                    if file.startswith('.') or '/.git/' in file_path:
                        continue
                    
                    # Get file stats
                    file_stats = os.stat(file_path)
                    file_size_kb = file_stats.st_size / 1024
                    
                    # Skip files larger than max_size_kb
                    if file_size_kb > max_size_kb:
                        continue
                    
                    # Get file extension
                    _, extension = os.path.splitext(file)
                    extension = extension.lower()
                    
                    # Detect language from extension
                    language = self._detect_language_from_extension(extension)
                    
                    # Filter by language if specified
                    if languages and language and language not in languages:
                        continue
                    
                    # Add file to the list
                    files_list.append({
                        "path": relative_path,
                        "size_kb": file_size_kb,
                        "language": language,
                        "extension": extension
                    })
                    
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            
        return files_list
    
    @staticmethod
    def _detect_language_from_extension(extension: str) -> Optional[str]:
        """
        Detect programming language from file extension.
        
        Args:
            extension: File extension
            
        Returns:
            Language name or None if unknown
        """
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".rb": "ruby",
            ".go": "go",
            ".php": "php",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".c": "c",
            ".html": "html",
            ".css": "css"
        }
        
        return language_map.get(extension)
    
    @staticmethod
    def read_file(file_path: str) -> Dict[str, Any]:
        """
        Read a file and return its contents.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing the result of the operation
        """
        result = {"success": False, "content": None, "error": None}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                result["content"] = f.read()
                result["success"] = True
                
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    result["content"] = f.read()
                    result["success"] = True
            except Exception as e:
                result["error"] = f"Error reading file with alternate encoding: {str(e)}"
        except Exception as e:
            result["error"] = f"Error reading file: {str(e)}"
            
        return result
    
    @staticmethod
    def write_file(file_path: str, content: str) -> Dict[str, Any]:
        """
        Write content to a file.
        
        Args:
            file_path: Path to the file
            content: Content to write
            
        Returns:
            Dictionary containing the result of the operation
        """
        result = {"success": False, "error": None}
        
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                result["success"] = True
                
        except Exception as e:
            result["error"] = f"Error writing file: {str(e)}"
            
        return result
