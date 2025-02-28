"""
Transformation Engine Server

FastAPI server that provides API endpoints for code transformation operations.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Path, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import make_asgi_app

from models import TransformationRequest, TransformationType, VerificationLevel, JobStatus
from tasks import TransformationTaskManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Transformation Engine API",
    description="API for the Autogenic AI Codebase Enhancer Transformation Engine",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a metrics endpoint for Prometheus
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Initialize task manager
task_manager = TransformationTaskManager()


@app.get("/")
async def root():
    """Root endpoint that confirms the API is running."""
    return {
        "name": "Transformation Engine API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/transformations/start")
async def start_transformation(request: TransformationRequest):
    """
    Start a new transformation job.
    
    Args:
        request: Transformation request details
        
    Returns:
        Dictionary with job ID and status
    """
    try:
        result = await task_manager.start_transformation_job(request.dict())
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
            
        return {
            "job_id": result["job_id"],
            "message": result["message"]
        }
        
    except Exception as e:
        logger.error(f"Error starting transformation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/transformations/{job_id}")
async def get_transformation_status(job_id: str = Path(..., description="ID of the transformation job")):
    """
    Get the status of a transformation job.
    
    Args:
        job_id: ID of the transformation job
        
    Returns:
        Dictionary with job status information
    """
    try:
        result = await task_manager.get_job_status(job_id)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])
            
        return result["job"]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transformation status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/transformations/{job_id}/results")
async def get_transformation_results(
    job_id: str = Path(..., description="ID of the transformation job"),
    limit: int = Query(100, description="Maximum number of results to return"),
    skip: int = Query(0, description="Number of results to skip")
):
    """
    Get the results of a transformation job.
    
    Args:
        job_id: ID of the transformation job
        limit: Maximum number of results to return
        skip: Number of results to skip
        
    Returns:
        Dictionary with job results
    """
    try:
        result = await task_manager.get_job_results(job_id, limit, skip)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])
            
        return {
            "job": result["job"],
            "results": result["results"],
            "pagination": result["pagination"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transformation results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.delete("/transformations/{job_id}")
async def cancel_transformation_job(job_id: str = Path(..., description="ID of the transformation job")):
    """
    Cancel a running transformation job.
    
    Args:
        job_id: ID of the transformation job
        
    Returns:
        Dictionary with cancellation status
    """
    try:
        result = await task_manager.cancel_job(job_id)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
            
        return {"message": result["message"]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling transformation job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/transformations/types")
async def get_transformation_types():
    """
    Get available transformation types.
    
    Returns:
        List of available transformation types
    """
    return {
        "types": [t.value for t in TransformationType],
        "descriptions": {
            "REFACTOR": "Improve code readability and maintainability",
            "OPTIMIZE": "Enhance performance of the code",
            "PRUNE": "Remove unused code",
            "MERGE": "Consolidate related functionality",
            "MODERNIZE": "Update to newer language patterns",
            "FIX_SECURITY": "Address potential security vulnerabilities"
        }
    }


@app.get("/transformations/verification-levels")
async def get_verification_levels():
    """
    Get available verification levels.
    
    Returns:
        List of available verification levels
    """
    return {
        "levels": [l.value for l in VerificationLevel],
        "descriptions": {
            "none": "No verification performed",
            "basic": "Basic syntax check only",
            "standard": "Syntax check and run tests if available",
            "strict": "Comprehensive verification including tests"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
