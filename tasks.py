"""
Background Task Manager for Transformation Engine

This module provides functionality to run transformation jobs in the background.
"""

import os
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from motor.motor_asyncio import AsyncIOMotorClient
import redis

from models import TransformationType, VerificationLevel, JobStatus
from codebase_transformer import CodebaseTransformer
from repo_utils import RepositoryManager
from code_analyzer_client import CodeAnalyzerClient
from knowledge_repo_client import KnowledgeRepoClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransformationTaskManager:
    """Manages background transformation tasks."""
    
    def __init__(self):
        """Initialize the Transformation Task Manager."""
        # Initialize MongoDB connection
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/mcp")
        self.mongo_client = AsyncIOMotorClient(mongo_uri)
        self.db = self.mongo_client.get_database()
        self.jobs_collection = self.db.transformation_jobs
        self.results_collection = self.db.transformation_results
        
        # Initialize Redis connection
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
        # Initialize workspace directory
        self.workspace_dir = os.getenv("WORKSPACE_DIR", "/tmp/workspaces")
        
        # Initialize repository manager
        self.repo_manager = RepositoryManager(self.workspace_dir)
        
        # Initialize clients
        self.code_analyzer = CodeAnalyzerClient()
        self.knowledge_repo = KnowledgeRepoClient()
        
        # Initialize active jobs tracking
        self.active_jobs = {}
    
    async def start_transformation_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start a new transformation job.
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            Dictionary containing the result of the operation
        """
        try:
            # Generate job ID
            job_id = str(uuid.uuid4())
            
            # Prepare job document
            now = datetime.utcnow().isoformat()
            job_doc = {
                "job_id": job_id,
                "status": JobStatus.PENDING.value,
                "repo_id": job_data["repo_id"],
                "repo_url": job_data["repo_url"],
                "branch": job_data.get("branch", "main"),
                "transformation_type": job_data["transformation_type"],
                "file_paths": job_data.get("file_paths", []),
                "languages": job_data.get("languages", []),
                "verification_level": job_data.get("verification_level", VerificationLevel.STANDARD.value),
                "safe_mode": job_data.get("safe_mode", True),
                "batch_size": job_data.get("batch_size", 10),
                "max_file_size_kb": job_data.get("max_file_size_kb", 50),
                "created_at": now,
                "updated_at": now,
                "total_files": 0,
                "processed_files": 0,
                "successful_transformations": 0,
                "failed_transformations": 0
            }
            
            # Save job to database
            await self.jobs_collection.insert_one(job_doc)
            
            # Start background task
            asyncio.create_task(self._run_transformation_job(job_id, job_doc))
            
            return {
                "success": True,
                "job_id": job_id,
                "message": "Transformation job started successfully"
            }
            
        except Exception as e:
            logger.error(f"Error starting transformation job: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to start transformation job: {str(e)}"
            }
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a transformation job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            Dictionary containing job status information
        """
        try:
            job = await self.jobs_collection.find_one({"job_id": job_id})
            
            if not job:
                return {
                    "success": False,
                    "error": f"Job with ID {job_id} not found"
                }
            
            # Remove MongoDB _id field
            if "_id" in job:
                del job["_id"]
                
            return {
                "success": True,
                "job": job
            }
            
        except Exception as e:
            logger.error(f"Error getting job status: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to get job status: {str(e)}"
            }
    
    async def get_job_results(self, job_id: str, limit: int = 100, skip: int = 0) -> Dict[str, Any]:
        """
        Get the results of a transformation job.
        
        Args:
            job_id: ID of the job
            limit: Maximum number of results to return
            skip: Number of results to skip
            
        Returns:
            Dictionary containing job results
        """
        try:
            job = await self.jobs_collection.find_one({"job_id": job_id})
            
            if not job:
                return {
                    "success": False,
                    "error": f"Job with ID {job_id} not found"
                }
            
            # Get job results with pagination
            cursor = self.results_collection.find({"job_id": job_id})
            cursor.skip(skip).limit(limit)
            
            results = await cursor.to_list(length=limit)
            
            # Remove MongoDB _id field from results
            for result in results:
                if "_id" in result:
                    del result["_id"]
                    
            # Get total count for pagination
            total_count = await self.results_collection.count_documents({"job_id": job_id})
                
            return {
                "success": True,
                "job": job,
                "results": results,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "skip": skip
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting job results: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to get job results: {str(e)}"
            }
    
    async def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel a running transformation job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            Dictionary containing the result of the operation
        """
        try:
            job = await self.jobs_collection.find_one({"job_id": job_id})
            
            if not job:
                return {
                    "success": False,
                    "error": f"Job with ID {job_id} not found"
                }
            
            if job["status"] in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
                return {
                    "success": False,
                    "error": f"Job with ID {job_id} is already in terminal state: {job['status']}"
                }
            
            # Update job status to cancelled
            await self.jobs_collection.update_one(
                {"job_id": job_id},
                {"$set": {
                    "status": JobStatus.CANCELLED.value,
                    "updated_at": datetime.utcnow().isoformat()
                }}
            )
            
            # Add to Redis cancellation list
            self.redis_client.set(f"cancel_job:{job_id}", "true", ex=3600)  # Expire after 1 hour
            
            return {
                "success": True,
                "message": f"Job with ID {job_id} has been cancelled"
            }
            
        except Exception as e:
            logger.error(f"Error cancelling job: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to cancel job: {str(e)}"
            }
    
    async def _run_transformation_job(self, job_id: str, job_data: Dict[str, Any]) -> None:
        """
        Run a transformation job in the background.
        
        Args:
            job_id: ID of the job
            job_data: Dictionary containing job information
        """
        logger.info(f"Starting transformation job {job_id}")
        
        try:
            # Track job as active
            self.active_jobs[job_id] = True
            
            # Update job status to running
            await self.jobs_collection.update_one(
                {"job_id": job_id},
                {"$set": {
                    "status": JobStatus.RUNNING.value,
                    "updated_at": datetime.utcnow().isoformat()
                }}
            )
            
            # Clone repository
            clone_result = self.repo_manager.clone_repository(
                job_data["repo_url"],
                job_data["repo_id"],
                job_data["branch"]
            )
            
            if not clone_result["success"]:
                await self._fail_job(job_id, f"Failed to clone repository: {clone_result['error']}")
                return
                
            # Create working copy
            working_copy = self.repo_manager.create_working_copy(job_data["repo_id"], job_id)
            
            if not working_copy["success"]:
                await self._fail_job(job_id, f"Failed to create working copy: {working_copy['error']}")
                return
                
            working_path = working_copy["working_path"]
            
            # Get files to transform
            files_to_transform = await self._get_files_to_transform(
                job_id,
                job_data["repo_id"],
                working_path,
                job_data.get("file_paths", []),
                job_data.get("languages", []),
                job_data["transformation_type"],
                job_data["max_file_size_kb"]
            )
            
            if not files_to_transform:
                await self._fail_job(job_id, "No files found for transformation")
                return
                
            # Update total files count
            await self.jobs_collection.update_one(
                {"job_id": job_id},
                {"$set": {
                    "total_files": len(files_to_transform),
                    "updated_at": datetime.utcnow().isoformat()
                }}
            )
            
            # Initialize transformer
            transformer = CodebaseTransformer(
                working_path,
                job_data["verification_level"],
                job_data["safe_mode"],
                self.code_analyzer,
                self.knowledge_repo,
                preferred_model=job_data.get("preferred_model"),
                fallback_model=job_data.get("fallback_model"),
                specialized_model=job_data.get("specialized_model")
            )
            
            # Process files in batches
            batch_size = job_data["batch_size"]
            total_processed = 0
            successful = 0
            failed = 0
            
            for i in range(0, len(files_to_transform), batch_size):
                # Check if job has been cancelled
                if self.redis_client.get(f"cancel_job:{job_id}"):
                    logger.info(f"Job {job_id} has been cancelled")
                    
                    # Update job status to cancelled
                    await self.jobs_collection.update_one(
                        {"job_id": job_id},
                        {"$set": {
                            "status": JobStatus.CANCELLED.value,
                            "updated_at": datetime.utcnow().isoformat()
                        }}
                    )
                    
                    return
                
                # Get batch of files
                batch = files_to_transform[i:i+batch_size]
                
                # Process batch
                batch_results = await transformer.transform_files(
                    batch,
                    job_data["transformation_type"],
                    job_id
                )
                
                # Save results to database
                if batch_results:
                    await self.results_collection.insert_many(batch_results)
                    
                    # Update counts
                    batch_successful = sum(1 for r in batch_results if r.get("status") == "success")
                    batch_failed = len(batch_results) - batch_successful
                    
                    total_processed += len(batch_results)
                    successful += batch_successful
                    failed += batch_failed
                    
                    # Update job progress
                    await self.jobs_collection.update_one(
                        {"job_id": job_id},
                        {"$set": {
                            "processed_files": total_processed,
                            "successful_transformations": successful,
                            "failed_transformations": failed,
                            "updated_at": datetime.utcnow().isoformat()
                        }}
                    )
            
            # Complete job
            await self.jobs_collection.update_one(
                {"job_id": job_id},
                {"$set": {
                    "status": JobStatus.COMPLETED.value,
                    "updated_at": datetime.utcnow().isoformat()
                }}
            )
            
            logger.info(f"Transformation job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error running transformation job {job_id}: {str(e)}")
            await self._fail_job(job_id, f"Transformation job failed: {str(e)}")
        finally:
            # Remove from active jobs
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
            
            # Clean up Redis cancellation key
            self.redis_client.delete(f"cancel_job:{job_id}")
    
    async def _fail_job(self, job_id: str, error_message: str) -> None:
        """
        Mark a job as failed.
        
        Args:
            job_id: ID of the job
            error_message: Error message to record
        """
        logger.error(f"Job {job_id} failed: {error_message}")
        
        await self.jobs_collection.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": JobStatus.FAILED.value,
                "error": error_message,
                "updated_at": datetime.utcnow().isoformat()
            }}
        )
    
    async def _get_files_to_transform(self,
                                     job_id: str,
                                     repo_id: str,
                                     working_path: str,
                                     file_paths: List[str],
                                     languages: List[str],
                                     transformation_type: str,
                                     max_file_size_kb: int) -> List[Dict[str, Any]]:
        """
        Get files to transform based on job parameters.
        
        Args:
            job_id: ID of the job
            repo_id: Repository ID
            working_path: Path to the working copy
            file_paths: List of specific file paths to transform
            languages: List of languages to include
            transformation_type: Type of transformation
            max_file_size_kb: Maximum file size in KB
            
        Returns:
            List of files to transform
        """
        # If specific file paths are provided, use those
        if file_paths:
            files = []
            for path in file_paths:
                full_path = os.path.join(working_path, path)
                if os.path.isfile(full_path):
                    lang = self.repo_manager._detect_language_from_extension(
                        os.path.splitext(path)[1].lower()
                    )
                    
                    # Skip if language doesn't match filter
                    if languages and lang and lang not in languages:
                        continue
                        
                    # Skip if file is too large
                    file_size_kb = os.path.getsize(full_path) / 1024
                    if file_size_kb > max_file_size_kb:
                        continue
                        
                    files.append({
                        "path": path,
                        "language": lang,
                        "size_kb": file_size_kb
                    })
            
            return files
        
        # Otherwise, try to get prioritized files from Code Analyzer
        analyzer_result = await self.code_analyzer.get_files_for_transformation(
            repo_id,
            transformation_type,
            None if not languages else languages[0],
            100  # Get a larger batch to filter
        )
        
        if analyzer_result["success"] and analyzer_result["data"]:
            files = []
            for file_info in analyzer_result["data"]:
                path = file_info["file_path"]
                full_path = os.path.join(working_path, path)
                
                # Skip if file doesn't exist
                if not os.path.isfile(full_path):
                    continue
                    
                # Skip if file is too large
                file_size_kb = os.path.getsize(full_path) / 1024
                if file_size_kb > max_file_size_kb:
                    continue
                    
                files.append({
                    "path": path,
                    "language": file_info.get("language"),
                    "size_kb": file_size_kb,
                    "priority": file_info.get("priority", 0),
                    "metrics": file_info.get("metrics", {})
                })
            
            # Sort by priority
            files.sort(key=lambda x: x.get("priority", 0), reverse=True)
            return files
        
        # Fall back to listing all files
        return self.repo_manager.list_files(working_path, languages, max_file_size_kb)
