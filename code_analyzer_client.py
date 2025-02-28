"""
Code Analyzer Client for the Transformation Engine

This module provides client functionality to interact with the Code Analyzer Service,
allowing the transformation engine to prioritize files and get insights for transformations.
"""

import os
import json
import httpx
import logging
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeAnalyzerClient:
    """Client for interacting with the Code Analyzer Service."""
    
    def __init__(self):
        """Initialize the Code Analyzer client."""
        self.base_url = os.getenv("CODE_ANALYZER_URL", "http://localhost:8080")
        self.default_timeout = 30.0  # 30 seconds
        self.batch_size = int(os.getenv("BATCH_SIZE", "100"))
    
    async def get_files_for_transformation(self,
                                          repo_id: str,
                                          transformation_type: str,
                                          language: Optional[str] = None,
                                          limit: int = 50) -> Dict[str, Any]:
        """
        Get prioritized files for a specific transformation type.
        
        Args:
            repo_id: Repository ID
            transformation_type: Type of transformation (REFACTOR, OPTIMIZE, etc.)
            language: Optional filter by programming language
            limit: Maximum number of files to retrieve
            
        Returns:
            Dict containing the prioritized files or error information
        """
        try:
            params = {
                "repo_id": repo_id,
                "transformation_type": transformation_type,
                "limit": min(limit, self.batch_size)  # Respect batch size limits
            }
            
            if language:
                params["language"] = language
                
            async with httpx.AsyncClient(timeout=self.default_timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/analysis/transformation-candidates",
                    params=params
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get files for transformation: {response.text}")
                    return {"success": False, "error": response.text}
                
                return {"success": True, "data": response.json()}
        except Exception as e:
            logger.error(f"Error getting files for transformation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_file_metrics(self,
                              repo_id: str,
                              file_path: str) -> Dict[str, Any]:
        """
        Get detailed metrics for a specific file.
        
        Args:
            repo_id: Repository ID
            file_path: Path to the file
            
        Returns:
            Dict containing the file metrics or error information
        """
        try:
            params = {
                "repo_id": repo_id,
                "file_path": file_path
            }
                
            async with httpx.AsyncClient(timeout=self.default_timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/analysis/file-metrics",
                    params=params
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get file metrics: {response.text}")
                    return {"success": False, "error": response.text}
                
                return {"success": True, "data": response.json()}
        except Exception as e:
            logger.error(f"Error getting file metrics: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_suggested_transformations(self,
                                          repo_id: str,
                                          file_path: str) -> Dict[str, Any]:
        """
        Get suggested transformations for a specific file.
        
        Args:
            repo_id: Repository ID
            file_path: Path to the file
            
        Returns:
            Dict containing suggested transformations or error information
        """
        try:
            params = {
                "repo_id": repo_id,
                "file_path": file_path
            }
                
            async with httpx.AsyncClient(timeout=self.default_timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/analysis/suggested-transformations",
                    params=params
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get suggested transformations: {response.text}")
                    return {"success": False, "error": response.text}
                
                return {"success": True, "data": response.json()}
        except Exception as e:
            logger.error(f"Error getting suggested transformations: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def update_file_metrics_after_transformation(self,
                                                     repo_id: str,
                                                     file_path: str,
                                                     metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update metrics for a file after transformation.
        
        Args:
            repo_id: Repository ID
            file_path: Path to the file
            metrics: Updated metrics for the file
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            async with httpx.AsyncClient(timeout=self.default_timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/analysis/update-metrics",
                    json={
                        "repo_id": repo_id,
                        "file_path": file_path,
                        "metrics": metrics
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to update file metrics: {response.text}")
                    return {"success": False, "error": response.text}
                
                return {"success": True, "data": response.json()}
        except Exception as e:
            logger.error(f"Error updating file metrics: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_repo_insights(self, repo_id: str) -> Dict[str, Any]:
        """
        Get overall insights for a repository.
        
        Args:
            repo_id: Repository ID
            
        Returns:
            Dict containing repository insights or error information
        """
        try:
            params = {"repo_id": repo_id}
                
            async with httpx.AsyncClient(timeout=self.default_timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/analysis/repo-insights",
                    params=params
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get repo insights: {response.text}")
                    return {"success": False, "error": response.text}
                
                return {"success": True, "data": response.json()}
        except Exception as e:
            logger.error(f"Error getting repo insights: {str(e)}")
            return {"success": False, "error": str(e)}
