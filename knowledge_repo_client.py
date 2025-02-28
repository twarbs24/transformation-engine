"""
Knowledge Repository Client for the Transformation Engine

This module provides client functionality to interact with the Knowledge Repository Service,
allowing the transformation engine to store and retrieve successful transformation patterns.
"""

import os
import json
import httpx
import logging
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeRepoClient:
    """Client for interacting with the Knowledge Repository Service."""
    
    def __init__(self):
        """Initialize the Knowledge Repository client."""
        self.base_url = os.getenv("KNOWLEDGE_REPO_URL", "http://localhost:8080")
        self.default_timeout = 30.0  # 30 seconds
        self.batch_size = int(os.getenv("BATCH_SIZE", "100"))
    
    async def store_transformation_pattern(self, 
                                          pattern: Dict[str, Any],
                                          metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store a successful transformation pattern in the knowledge repository.
        
        Args:
            pattern: The transformation pattern to store
            metadata: Metadata about the transformation
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            async with httpx.AsyncClient(timeout=self.default_timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/patterns/transformation",
                    json={
                        "pattern": pattern,
                        "metadata": metadata
                    }
                )
                
                if response.status_code != 201:
                    logger.error(f"Failed to store transformation pattern: {response.text}")
                    return {"success": False, "error": response.text}
                
                return {"success": True, "data": response.json()}
        except Exception as e:
            logger.error(f"Error storing transformation pattern: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def retrieve_transformation_patterns(self, 
                                              language: str,
                                              transformation_type: str,
                                              file_path: Optional[str] = None,
                                              limit: int = 10) -> Dict[str, Any]:
        """
        Retrieve transformation patterns from the knowledge repository.
        
        Args:
            language: Programming language (python, javascript, etc.)
            transformation_type: Type of transformation (REFACTOR, OPTIMIZE, etc.)
            file_path: Optional file path pattern to match
            limit: Maximum number of patterns to retrieve
            
        Returns:
            Dict containing the patterns or error information
        """
        try:
            params = {
                "language": language,
                "transformation_type": transformation_type,
                "limit": min(limit, self.batch_size)  # Respect batch size limits
            }
            
            if file_path:
                params["file_path"] = file_path
                
            async with httpx.AsyncClient(timeout=self.default_timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/patterns/transformation",
                    params=params
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to retrieve transformation patterns: {response.text}")
                    return {"success": False, "error": response.text}
                
                return {"success": True, "data": response.json()}
        except Exception as e:
            logger.error(f"Error retrieving transformation patterns: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def record_transformation_success(self,
                                           job_id: str,
                                           file_path: str,
                                           transformation_type: str,
                                           language: str,
                                           before_code: str,
                                           after_code: str,
                                           metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record a successful transformation to help improve future transformations.
        
        Args:
            job_id: The transformation job ID
            file_path: Path to the transformed file
            transformation_type: Type of transformation applied
            language: Programming language of the file
            before_code: Code before transformation
            after_code: Code after transformation
            metrics: Metrics about the transformation (e.g., complexity reduction)
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            async with httpx.AsyncClient(timeout=self.default_timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/transformations/success",
                    json={
                        "job_id": job_id,
                        "file_path": file_path,
                        "transformation_type": transformation_type,
                        "language": language,
                        "before_code": before_code,
                        "after_code": after_code,
                        "metrics": metrics
                    }
                )
                
                if response.status_code != 201:
                    logger.error(f"Failed to record transformation success: {response.text}")
                    return {"success": False, "error": response.text}
                
                return {"success": True, "data": response.json()}
        except Exception as e:
            logger.error(f"Error recording transformation success: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_language_specific_patterns(self,
                                            language: str,
                                            pattern_type: str,
                                            limit: int = 20) -> Dict[str, Any]:
        """
        Get language-specific patterns for a particular pattern type.
        
        Args:
            language: Programming language (python, javascript, etc.)
            pattern_type: Type of pattern (antipattern, bestpractice, etc.)
            limit: Maximum number of patterns to retrieve
            
        Returns:
            Dict containing the patterns or error information
        """
        try:
            params = {
                "language": language,
                "pattern_type": pattern_type,
                "limit": min(limit, self.batch_size)  # Respect batch size limits
            }
                
            async with httpx.AsyncClient(timeout=self.default_timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/patterns/language",
                    params=params
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to retrieve language patterns: {response.text}")
                    return {"success": False, "error": response.text}
                
                return {"success": True, "data": response.json()}
        except Exception as e:
            logger.error(f"Error retrieving language patterns: {str(e)}")
            return {"success": False, "error": str(e)}
