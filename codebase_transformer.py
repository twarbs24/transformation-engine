"""
Codebase Transformer for Autogenic AI Codebase Enhancer

This module provides functionality to transform codebases using AI models,
applying various transformation types like refactoring, optimization, etc.
"""

import os
import logging
import json
import asyncio
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Tuple
import httpx
from pathlib import Path
import subprocess
import tempfile
import time
from datetime import datetime

# Import from local modules
from models import TransformationType, VerificationLevel
from verification import TransformationVerifier
from metrics import MetricsCollector, PrometheusMetrics
from repo_utils import RepositoryManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransformationResult:
    """Result of a codebase transformation operation."""
    
    def __init__(self):
        """Initialize transformation result."""
        self.total_transformations = 0
        self.transformed_files = []
        self.transformation_details = {}
        self.errors = []
        self.start_time = datetime.utcnow()
        self.end_time = None
        self.verification_status = None
    
    def add_transformation(self, file_path: str, transformation_type: TransformationType, details: Dict[str, Any]):
        """Add a transformation to the result."""
        if file_path not in self.transformation_details:
            self.transformation_details[file_path] = []
            self.transformed_files.append(file_path)
        
        self.transformation_details[file_path].append({
            "type": transformation_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            **details
        })
        
        self.total_transformations += 1
    
    def add_error(self, file_path: str, error: str):
        """Add an error to the result."""
        self.errors.append({
            "file_path": file_path,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def complete(self, verification_status: Optional[Dict[str, Any]] = None):
        """Mark the transformation as complete."""
        self.end_time = datetime.utcnow()
        self.verification_status = verification_status
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "total_transformations": self.total_transformations,
            "transformed_files": self.transformed_files,
            "transformation_details": self.transformation_details,
            "errors": self.errors,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "verification_status": self.verification_status
        }


class CodebaseTransformer:
    """Transformer for applying AI-driven transformations to codebases."""
    
    def __init__(
        self,
        workspace_path: str,
        verification_level: str = VerificationLevel.STANDARD.value,
        safe_mode: bool = True,
        code_analyzer_client = None,
        knowledge_repo_client = None,
        ollama_url: str = None,
        preferred_model: str = None,
        fallback_model: str = None,
        specialized_model: str = None
    ):
        """Initialize the codebase transformer.
        
        Args:
            workspace_path: Path to the workspace containing the codebase
            verification_level: Level of verification to perform
            safe_mode: If True, only apply verified transformations
            code_analyzer_client: Client for Code Analyzer service
            knowledge_repo_client: Client for Knowledge Repository service
            ollama_url: URL of the Ollama API (optional if set via env var)
            preferred_model: Name of the preferred Ollama model to use (optional if set via env var)
            fallback_model: Name of the fallback Ollama model to use (optional if set via env var)
            specialized_model: Name of the specialized Ollama model for complex transformations (optional if set via env var)
        """
        self.workspace_path = workspace_path
        self.verification_level = verification_level
        self.safe_mode = safe_mode
        self.code_analyzer = code_analyzer_client
        self.knowledge_repo = knowledge_repo_client
        
        # Initialize Ollama settings from environment if not provided
        self.ollama_url = ollama_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.preferred_model = preferred_model or os.getenv("PREFERRED_MODEL", "deepseek-coder-v2:16b")
        self.fallback_model = fallback_model or os.getenv("FALLBACK_MODEL", "qwen2.5-coder:7b")
        self.specialized_model = specialized_model or os.getenv("SPECIALIZED_MODEL", "codellama:34b")
        
        # Initialize HTTP client with longer timeout for AI model calls
        self.http_client = httpx.AsyncClient(timeout=120.0)
        
        # Initialize metrics collector
        self.metrics_collector = PrometheusMetrics()
    
    async def close(self):
        """Close resources."""
        await self.http_client.aclose()
    
    async def transform_files(
        self,
        files: List[Dict[str, Any]],
        transformation_type: str,
        job_id: str
    ) -> List[Dict[str, Any]]:
        """
        Transform a batch of files.
        
        Args:
            files: List of file information dictionaries
            transformation_type: Type of transformation to apply
            job_id: ID of the transformation job
            
        Returns:
            List of transformation results
        """
        results = []
        
        # Process files concurrently with a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent transformations
        
        async def process_file(file_info):
            async with semaphore:
                file_path = file_info["path"]
                language = file_info.get("language")
                
                try:
                    # Read file content
                    full_path = os.path.join(self.workspace_path, file_path)
                    
                    with open(full_path, 'r', encoding='utf-8') as f:
                        original_code = f.read()
                    
                    # Get transformation patterns from knowledge repo if available
                    patterns = []
                    if self.knowledge_repo:
                        patterns_result = await self.knowledge_repo.retrieve_transformation_patterns(
                            language=language,
                            transformation_type=transformation_type,
                            file_path=file_path,
                            limit=5
                        )
                        
                        if patterns_result["success"]:
                            patterns = patterns_result["data"].get("patterns", [])
                    
                    # Apply transformation using AI model
                    start_time = time.time()
                    transformed_code, transformation_summary = await self._apply_transformation(
                        original_code=original_code,
                        file_path=file_path,
                        language=language,
                        transformation_type=transformation_type,
                        patterns=patterns
                    )
                    transformation_duration = time.time() - start_time
                    
                    # Record transformation duration
                    PrometheusMetrics.transformation_duration.observe(transformation_duration)
                    
                    # Verify the transformation
                    verifier = TransformationVerifier(
                        workspace_path=self.workspace_path,
                        verification_level=self.verification_level
                    )
                    
                    verification_result = await verifier.verify_transformation(
                        file_path=file_path,
                        original_code=original_code,
                        transformed_code=transformed_code,
                        language=language
                    )
                    
                    # Record verification result
                    PrometheusMetrics.record_verification(verification_result["success"])
                    
                    # Apply the transformation if verification passed or safe mode is disabled
                    if verification_result["success"] or not self.safe_mode:
                        # Write the transformed code back to the file
                        with open(full_path, 'w', encoding='utf-8') as f:
                            f.write(transformed_code)
                            
                        # Record successful transformation
                        PrometheusMetrics.record_transformation(transformation_type)
                        
                        # Record complexity reduction metrics
                        PrometheusMetrics.record_complexity_reduction(
                            transformation_type, 
                            original_code, 
                            transformed_code
                        )
                        
                        # Store successful transformation pattern in knowledge repo if available
                        if self.knowledge_repo and verification_result["success"]:
                            await self.knowledge_repo.store_transformation_pattern(
                                language=language,
                                transformation_type=transformation_type,
                                file_path=file_path,
                                pattern={
                                    "before": original_code,
                                    "after": transformed_code,
                                    "summary": transformation_summary,
                                    "metrics": MetricsCollector.calculate_complexity_reduction(
                                        original_code, transformed_code
                                    )
                                }
                            )
                    
                    # Create result
                    result = {
                        "file_path": file_path,
                        "language": language,
                        "transformation_type": transformation_type,
                        "verification": verification_result,
                        "summary": transformation_summary,
                        "applied": verification_result["success"] or not self.safe_mode,
                        "metrics": MetricsCollector.calculate_complexity_reduction(
                            original_code, transformed_code
                        ),
                        "job_id": job_id
                    }
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Error transforming file {file_path}: {str(e)}")
                    # Record error
                    PrometheusMetrics.record_error("transformation_error")
                    
                    return {
                        "file_path": file_path,
                        "language": language,
                        "transformation_type": transformation_type,
                        "error": str(e),
                        "applied": False,
                        "job_id": job_id
                    }
        
        # Process all files concurrently
        tasks = [process_file(file_info) for file_info in files]
        results = await asyncio.gather(*tasks)
        
        return results
    
    async def _apply_transformation(
        self,
        original_code: str,
        file_path: str,
        language: str,
        transformation_type: str,
        patterns: List[Dict[str, Any]] = None
    ) -> Tuple[str, str]:
        """
        Apply transformation to code using AI model.
        
        Args:
            original_code: Original code to transform
            file_path: Path to the file
            language: Programming language
            transformation_type: Type of transformation to apply
            patterns: Optional list of transformation patterns
            
        Returns:
            Tuple of (transformed_code, transformation_summary)
        """
        # Select the appropriate model based on transformation type and complexity
        selected_model = self._select_model_for_transformation(transformation_type, original_code)
        
        # Prepare prompt for the AI model
        prompt = self._create_transformation_prompt(
            code=original_code,
            file_path=file_path,
            language=language,
            transformation_type=transformation_type,
            patterns=patterns
        )
        
        try:
            # Call Ollama API
            response = await self.http_client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": selected_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,  # Low temperature for more deterministic output
                        "top_p": 0.95,
                        "max_tokens": 4096
                    }
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract transformed code and summary from response
            transformed_code, transformation_summary = self._parse_transformation_response(
                result["response"],
                original_code
            )
            
            # If transformation failed with preferred model, try fallback model
            if transformed_code == original_code and selected_model == self.preferred_model:
                logger.info(f"Transformation with preferred model failed, trying fallback model for {file_path}")
                
                # Call Ollama API with fallback model
                response = await self.http_client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.fallback_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.2,
                            "top_p": 0.95,
                            "max_tokens": 4096
                        }
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Extract transformed code and summary from response
                transformed_code, transformation_summary = self._parse_transformation_response(
                    result["response"],
                    original_code
                )
            
            return transformed_code, transformation_summary
            
        except Exception as e:
            logger.error(f"Error calling Ollama API: {str(e)}")
            # Return original code if transformation fails
            return original_code, f"Transformation failed: {str(e)}"
    
    def _select_model_for_transformation(self, transformation_type: str, code: str) -> str:
        """
        Select the appropriate model based on transformation type and code complexity.
        
        Args:
            transformation_type: Type of transformation to apply
            code: The code to transform
            
        Returns:
            Name of the model to use
        """
        # Use specialized model for complex transformations
        if transformation_type in ["FIX_SECURITY", "REFACTOR"] and len(code) > 1000:
            logger.info(f"Using specialized model for complex {transformation_type}")
            return self.specialized_model
            
        # Use preferred model for most transformations
        return self.preferred_model
    
    def _create_transformation_prompt(
        self,
        code: str,
        file_path: str,
        language: str,
        transformation_type: str,
        patterns: List[Dict[str, Any]] = None
    ) -> str:
        """
        Create a prompt for the AI model.
        
        Args:
            code: Code to transform
            file_path: Path to the file
            language: Programming language
            transformation_type: Type of transformation to apply
            patterns: Optional list of transformation patterns
            
        Returns:
            Prompt string for the AI model
        """
        # Base instructions based on transformation type
        transformation_instructions = {
            "REFACTOR": "Refactor this code to improve readability and maintainability. Follow clean code principles.",
            "OPTIMIZE": "Optimize this code for better performance. Focus on algorithmic improvements and efficiency.",
            "PRUNE": "Remove any unused or redundant code. Eliminate dead code, unused imports, and unnecessary comments.",
            "MERGE": "Consolidate related functionality. Combine similar functions and reduce duplication.",
            "MODERNIZE": "Update this code to use modern language features and patterns.",
            "FIX_SECURITY": "Fix potential security vulnerabilities in this code. Focus on common security issues."
        }
        
        # Get instructions for the specified transformation type
        instruction = transformation_instructions.get(
            transformation_type,
            "Improve this code following best practices."
        )
        
        # Build the prompt
        prompt = f"""You are an expert {language} developer tasked with improving code quality.

TASK: {instruction}

FILE PATH: {file_path}

ORIGINAL CODE:
```{language}
{code}
```

INSTRUCTIONS:
1. Analyze the code carefully
2. Apply the requested transformation: {transformation_type}
3. Preserve the functionality of the code
4. Do not change the overall structure unless necessary
5. Return the transformed code in the format specified below

"""

        # Add patterns if available
        if patterns and len(patterns) > 0:
            prompt += "\nRELEVANT PATTERNS TO CONSIDER:\n"
            for i, pattern in enumerate(patterns[:3]):  # Limit to 3 patterns
                prompt += f"{i+1}. {pattern.get('description', 'No description')}\n"
                if "example" in pattern:
                    prompt += f"   Example: {pattern['example']}\n"
        
        # Add output format instructions
        prompt += """
OUTPUT FORMAT:
First provide a brief summary of the changes you made, starting with "SUMMARY:"
Then provide the complete transformed code, enclosed in triple backticks with the language specified.

Example:
SUMMARY: Refactored the function to use list comprehension instead of for loops, removed redundant variable assignments, and added type hints.

```python
# Your transformed code here
```
"""
        
        return prompt
    
    def _parse_transformation_response(self, response: str, original_code: str) -> Tuple[str, str]:
        """
        Parse the response from the AI model.
        
        Args:
            response: Response from the AI model
            original_code: Original code (used as fallback)
            
        Returns:
            Tuple of (transformed_code, transformation_summary)
        """
        # Extract summary
        summary = ""
        if "SUMMARY:" in response:
            summary_parts = response.split("SUMMARY:", 1)
            if len(summary_parts) > 1:
                summary_text = summary_parts[1].split("```", 1)[0].strip()
                summary = summary_text
        
        # Extract code
        code_blocks = response.split("```")
        if len(code_blocks) >= 3:
            # Find the first code block after a language specifier
            for i in range(1, len(code_blocks), 2):
                language_line = code_blocks[i].strip().lower()
                if language_line and not language_line.startswith("output") and i+1 < len(code_blocks):
                    transformed_code = code_blocks[i+1].strip()
                    return transformed_code, summary
        
        # Fallback: try to find any code block
        if "```" in response:
            try:
                transformed_code = response.split("```")[1].split("```")[0]
                if transformed_code.strip():
                    # Remove language identifier if present
                    first_line = transformed_code.split("\n")[0].strip()
                    if first_line and not first_line.startswith("#") and not first_line.startswith("//"):
                        transformed_code = "\n".join(transformed_code.split("\n")[1:])
                    return transformed_code.strip(), summary
            except:
                pass
        
        # If no valid code block found, return original code
        logger.warning("Could not parse transformed code from AI response")
        return original_code, "No changes made (could not parse AI response)"
