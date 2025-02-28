"""
Metrics Collection Utilities for Transformation Engine

This module provides functionality to collect and analyze metrics about code transformations.
"""

import re
import os
import json
import subprocess
from typing import Dict, List, Optional, Any
from prometheus_client import Counter, Gauge, Histogram, Summary

# Prometheus metrics for the transformation engine
class PrometheusMetrics:
    """Prometheus metrics for the Transformation Engine."""
    
    # Initialize metrics as class variables
    transformations_total = Counter(
        'transformation_engine_transformations_total',
        'Total number of transformations performed'
    )
    
    transformations_by_type = Counter(
        'transformation_engine_transformations_by_type_total',
        'Total number of transformations by type',
        ['type']
    )
    
    errors_total = Counter(
        'transformation_engine_errors_total',
        'Total number of errors encountered',
        ['error_type']
    )
    
    verification_attempts = Counter(
        'transformation_engine_verification_attempts_total',
        'Total number of verification attempts'
    )
    
    verification_successes = Counter(
        'transformation_engine_verification_successes_total',
        'Total number of successful verifications'
    )
    
    verification_success_ratio = Gauge(
        'transformation_engine_verification_success_ratio',
        'Ratio of successful verifications to total attempts'
    )
    
    transformation_duration = Histogram(
        'transformation_engine_transformation_duration_seconds',
        'Time taken to perform a transformation',
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
    )
    
    complexity_reduction = Gauge(
        'transformation_engine_complexity_reduction_percentage',
        'Percentage reduction in complexity after transformation',
        ['transformation_type']
    )
    
    file_size_reduction = Gauge(
        'transformation_engine_file_size_reduction_percentage',
        'Percentage reduction in file size after transformation'
    )
    
    @classmethod
    def record_transformation(cls, transformation_type: str):
        """Record a transformation event."""
        cls.transformations_total.inc()
        cls.transformations_by_type.labels(type=transformation_type).inc()
    
    @classmethod
    def record_error(cls, error_type: str):
        """Record an error event."""
        cls.errors_total.labels(error_type=error_type).inc()
    
    @classmethod
    def record_verification(cls, success: bool):
        """Record a verification attempt and update success ratio."""
        cls.verification_attempts.inc()
        if success:
            cls.verification_successes.inc()
        
        # Update the success ratio
        if cls.verification_attempts._value.get() > 0:
            success_ratio = cls.verification_successes._value.get() / cls.verification_attempts._value.get()
            cls.verification_success_ratio.set(success_ratio)
    
    @classmethod
    def record_complexity_reduction(cls, transformation_type: str, before_code: str, after_code: str):
        """Record complexity reduction metrics."""
        metrics = MetricsCollector.calculate_complexity_reduction(before_code, after_code)
        if metrics["line_count_change_percentage"] < 0:  # Negative percentage means reduction
            cls.complexity_reduction.labels(transformation_type=transformation_type).set(
                abs(metrics["line_count_change_percentage"])
            )
        
        if metrics["character_count_change_percentage"] < 0:  # Negative percentage means reduction
            cls.file_size_reduction.set(abs(metrics["character_count_change_percentage"]))


class MetricsCollector:
    """Collects and analyzes metrics about code transformations."""
    
    @staticmethod
    def collect_basic_metrics(code: str) -> Dict[str, Any]:
        """
        Collect basic metrics about a code snippet.
        
        Args:
            code: The code snippet to analyze
            
        Returns:
            Dictionary containing basic metrics
        """
        lines = code.splitlines()
        non_empty_lines = [line for line in lines if line.strip()]
        
        return {
            "total_lines": len(lines),
            "non_empty_lines": len(non_empty_lines),
            "characters": len(code),
            "average_line_length": len(code) / len(lines) if lines else 0,
        }
    
    @staticmethod
    def calculate_complexity_reduction(before_code: str, after_code: str) -> Dict[str, Any]:
        """
        Calculate complexity reduction metrics between original and transformed code.
        
        Args:
            before_code: Original code before transformation
            after_code: Transformed code
            
        Returns:
            Dictionary containing complexity reduction metrics
        """
        before_metrics = MetricsCollector.collect_basic_metrics(before_code)
        after_metrics = MetricsCollector.collect_basic_metrics(after_code)
        
        # Calculate percentage changes
        line_change_pct = ((after_metrics["total_lines"] - before_metrics["total_lines"]) / 
                          before_metrics["total_lines"]) * 100 if before_metrics["total_lines"] else 0
                          
        char_change_pct = ((after_metrics["characters"] - before_metrics["characters"]) / 
                          before_metrics["characters"]) * 100 if before_metrics["characters"] else 0
        
        return {
            "before": before_metrics,
            "after": after_metrics,
            "line_count_change_percentage": line_change_pct,
            "character_count_change_percentage": char_change_pct,
            "is_smaller": after_metrics["characters"] < before_metrics["characters"]
        }
    
    @staticmethod
    def extract_python_complexity(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract complexity metrics for Python code using radon.
        Requires radon to be installed.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Dictionary containing complexity metrics or None if failed
        """
        try:
            # Use radon to measure cyclomatic complexity
            result = subprocess.run(
                ["radon", "cc", "-j", file_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                # Extract average complexity
                if file_path in data and data[file_path]:
                    complexities = [item.get("complexity", 0) for item in data[file_path]]
                    return {
                        "average_complexity": sum(complexities) / len(complexities) if complexities else 0,
                        "max_complexity": max(complexities) if complexities else 0,
                        "functions_analyzed": len(complexities)
                    }
            
            return None
        except (subprocess.SubprocessError, json.JSONDecodeError, KeyError) as e:
            print(f"Error analyzing Python complexity: {str(e)}")
            return None
    
    @staticmethod
    def extract_js_complexity(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract complexity metrics for JavaScript code using complexity-report.
        Requires complexity-report to be installed.
        
        Args:
            file_path: Path to the JavaScript file
            
        Returns:
            Dictionary containing complexity metrics or None if failed
        """
        try:
            # Use complexity-report to measure complexity
            result = subprocess.run(
                ["cr", "-f", "json", file_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                return {
                    "maintainability_index": data.get("maintainability", 0),
                    "average_complexity": data.get("averageComplexityPerFunction", 0),
                    "functions_analyzed": data.get("functionCount", 0)
                }
            
            return None
        except (subprocess.SubprocessError, json.JSONDecodeError) as e:
            print(f"Error analyzing JavaScript complexity: {str(e)}")
            return None
    
    @staticmethod
    def detect_language_from_file(file_path: str) -> Optional[str]:
        """
        Detect programming language from file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language name or None if unknown
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
        
        return language_map.get(extension)
