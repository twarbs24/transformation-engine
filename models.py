"""
Data models for the Transformation Engine

Defines the data structures used throughout the transformation engine.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class TransformationType(str, Enum):
    """Types of code transformations supported by the engine."""
    REFACTOR = "REFACTOR"
    OPTIMIZE = "OPTIMIZE"
    PRUNE = "PRUNE"
    MERGE = "MERGE"
    MODERNIZE = "MODERNIZE"
    FIX_SECURITY = "FIX_SECURITY"


class VerificationLevel(str, Enum):
    """Verification levels for code transformations."""
    NONE = "none"
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"


class JobStatus(str, Enum):
    """Status of a transformation job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TransformationRequest(BaseModel):
    """Request model for starting a transformation job."""
    repo_id: str
    repo_url: str
    branch: str = "main"
    transformation_type: TransformationType
    file_paths: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    verification_level: VerificationLevel = VerificationLevel.STANDARD
    safe_mode: bool = True
    batch_size: int = Field(default=10, ge=1, le=100)
    max_file_size_kb: int = Field(default=50, ge=1, le=500)
    preferred_model: Optional[str] = None
    fallback_model: Optional[str] = None
    specialized_model: Optional[str] = None
    
    class Config:
        use_enum_values = True


class TransformationJobInfo(BaseModel):
    """Information about a transformation job."""
    job_id: str
    status: JobStatus
    repo_id: str
    transformation_type: str
    created_at: str
    updated_at: str
    total_files: int = 0
    processed_files: int = 0
    successful_transformations: int = 0
    failed_transformations: int = 0
    
    class Config:
        use_enum_values = True


class FileTransformationResult(BaseModel):
    """Result of a file transformation."""
    file_path: str
    language: str
    status: str
    error: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    changes_summary: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
