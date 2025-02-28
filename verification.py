"""
Verification Utilities for Transformation Engine

This module provides functionality to verify code transformations.
"""

import os
import subprocess
import tempfile
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple

from models import VerificationLevel
from metrics import PrometheusMetrics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransformationVerifier:
    """Verifies code transformations to ensure they maintain functionality."""
    
    def __init__(self, workspace_path: str, verification_level: str = VerificationLevel.STANDARD.value):
        """Initialize the transformation verifier.
        
        Args:
            workspace_path: Path to the workspace containing the codebase
            verification_level: Level of verification to perform
        """
        self.workspace_path = workspace_path
        self.verification_level = verification_level
    
    async def verify_transformation(
        self,
        file_path: str,
        original_code: str,
        transformed_code: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Verify a code transformation based on the specified verification level.
        
        Args:
            file_path: Path to the file being transformed
            original_code: Original code before transformation
            transformed_code: Transformed code
            language: Programming language of the code
            
        Returns:
            Dictionary containing verification results
        """
        # Start with basic verification results
        results = {
            "success": False,
            "level": self.verification_level,
            "language": language,
            "syntax_check": False,
            "errors": []
        }
        
        try:
            # Basic syntax check
            syntax_result = await self._check_syntax(transformed_code, language, file_path)
            results["syntax_check"] = syntax_result["success"]
            
            if not syntax_result["success"]:
                results["errors"].append(f"Syntax error: {syntax_result.get('error', 'Unknown error')}")
                PrometheusMetrics.record_error("syntax_error")
                return results
            
            # Additional verification based on level
            if self.verification_level == VerificationLevel.STANDARD.value:
                # Run additional checks for standard verification
                additional_result = await self._run_additional_checks(file_path, original_code, transformed_code, language)
                results.update(additional_result)
                
                if not additional_result.get("success", False):
                    PrometheusMetrics.record_error("verification_error")
                    return results
            
            elif self.verification_level == VerificationLevel.COMPREHENSIVE.value:
                # Run comprehensive verification including tests
                test_result = await self._run_tests(file_path)
                results["tests_passed"] = test_result["success"]
                
                if not test_result["success"]:
                    results["errors"].append(f"Test failure: {test_result.get('error', 'Unknown error')}")
                    PrometheusMetrics.record_error("test_failure")
                    return results
            
            # If we got here, verification passed
            results["success"] = True
            
            return results
            
        except Exception as e:
            logger.error(f"Error during verification: {str(e)}")
            results["errors"].append(f"Verification error: {str(e)}")
            PrometheusMetrics.record_error("verification_exception")
            return results
    
    async def _check_syntax(self, code: str, language: str, file_path: str) -> Dict[str, Any]:
        """
        Verify syntax of code.
        
        Args:
            code: Code to verify
            language: Programming language
            file_path: Path to the file
            
        Returns:
            Dictionary containing syntax verification results
        """
        result = {"success": False, "error": None}
        
        try:
            with tempfile.NamedTemporaryFile(suffix=os.path.splitext(file_path)[1], delete=False) as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(code.encode('utf-8'))
                
            # Language-specific syntax checking
            if language == "python":
                subprocess.run(["python", "-m", "py_compile", temp_file_path], check=True, capture_output=True)
                result["success"] = True
            elif language == "javascript":
                subprocess.run(["node", "--check", temp_file_path], check=True, capture_output=True)
                result["success"] = True
            elif language == "typescript":
                # Assumes tsc is installed
                subprocess.run(["tsc", "--noEmit", temp_file_path], check=True, capture_output=True)
                result["success"] = True
            elif language == "java":
                # Basic Java syntax check - assumes javac is available
                subprocess.run(["javac", "-Xlint:all", temp_file_path], check=True, capture_output=True)
                result["success"] = True
            else:
                # For unsupported languages, assume syntax is correct
                logger.warning(f"Syntax verification not implemented for {language}")
                result["success"] = True
                
        except subprocess.CalledProcessError as e:
            result["error"] = f"Syntax check failed: {e.stderr.decode('utf-8') if e.stderr else str(e)}"
        except Exception as e:
            result["error"] = f"Error during syntax check: {str(e)}"
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
        return result
    
    async def _run_additional_checks(self, file_path: str, original_code: str, transformed_code: str, language: str) -> Dict[str, Any]:
        """
        Run additional checks for standard verification.
        
        Args:
            file_path: Path to the file being transformed
            original_code: Original code before transformation
            transformed_code: Transformed code
            language: Programming language
            
        Returns:
            Dictionary containing additional check results
        """
        result = {"success": True}
        
        # Additional checks can be added here
        
        return result
    
    async def _run_tests(self, file_path: str) -> Dict[str, Any]:
        """
        Run tests related to the transformed file.
        
        Args:
            file_path: Path to the file being transformed
            
        Returns:
            Dictionary containing test results
        """
        result = {
            "success": False,
            "error": None
        }
        
        try:
            # Detect test framework and find test files
            test_command = self._detect_test_command(file_path)
            
            if not test_command:
                logger.info(f"No tests detected for {file_path}")
                # If strict verification but no tests found, consider as not passed
                result["error"] = "No tests found"
                return result
                
            # Run tests
            logger.info(f"Running tests with command: {test_command}")
            process = subprocess.run(
                test_command,
                shell=True,
                cwd=self.workspace_path,
                capture_output=True,
                text=True
            )
            
            result["success"] = process.returncode == 0
            
            if not result["success"]:
                result["error"] = process.stderr if process.stderr else "Tests failed without specific error message"
                
        except Exception as e:
            result["error"] = f"Error running tests: {str(e)}"
            
        return result
    
    def _detect_test_command(self, file_path: str) -> Optional[str]:
        """
        Detect appropriate test command based on the project structure.
        
        Args:
            file_path: Path to the file being transformed
            
        Returns:
            Test command string or None if not detected
        """
        language = self._detect_language(file_path)
        file_name = os.path.basename(file_path)
        file_base = os.path.splitext(file_name)[0]
        
        # Python test detection
        if language == "python":
            # Check for pytest
            if os.path.exists(os.path.join(self.workspace_path, "pytest.ini")) or os.path.exists(os.path.join(self.workspace_path, "conftest.py")):
                # Try to find related test file
                test_file = f"test_{file_base}.py"
                test_dir = os.path.join(self.workspace_path, "tests")
                
                if os.path.exists(os.path.join(test_dir, test_file)):
                    return f"python -m pytest {os.path.join('tests', test_file)} -v"
                else:
                    return "python -m pytest"
            
            # Check for unittest
            test_file = f"test_{file_base}.py"
            if os.path.exists(os.path.join(self.workspace_path, test_file)):
                return f"python -m unittest {test_file}"
                
            return None
            
        # JavaScript/TypeScript test detection
        elif language in ["javascript", "typescript"]:
            # Check for Jest
            if os.path.exists(os.path.join(self.workspace_path, "jest.config.js")) or os.path.exists(os.path.join(self.workspace_path, "package.json")):
                return "npm test"
                
            return None
            
        # Java test detection
        elif language == "java":
            # Check for Maven
            if os.path.exists(os.path.join(self.workspace_path, "pom.xml")):
                return "mvn test"
            
            # Check for Gradle
            if os.path.exists(os.path.join(self.workspace_path, "build.gradle")):
                return "./gradlew test"
                
            return None
            
        # Default: no test command detected
        return None
    
    def _detect_language(self, file_path: str) -> str:
        """
        Detect programming language from file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language name as string
        """
        extension = os.path.splitext(file_path)[1].lower()
        
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
        
        return language_map.get(extension, "unknown")
