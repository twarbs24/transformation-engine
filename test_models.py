#!/usr/bin/env python3
"""
Test script to verify that the models are working correctly with the CodebaseTransformer.
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Import transformation engine modules
from codebase_transformer import CodebaseTransformer
from models import TransformationType, VerificationLevel

async def test_models():
    """Test that the models are working correctly."""
    # Create a simple test file
    test_dir = Path("test_workspace")
    test_dir.mkdir(exist_ok=True)
    
    test_file = test_dir / "test_file.py"
    test_file.write_text("""
def add(a, b):
    return a + b
    
def subtract(a, b):
    return a - b
""")
    
    # Initialize transformer with different models
    models_to_test = [
        {
            "name": "Primary Model (DeepSeek-Coder)",
            "preferred_model": "deepseek-coder:latest",
            "fallback_model": None,
            "specialized_model": None
        },
        {
            "name": "Fallback Model (Qwen)",
            "preferred_model": None,
            "fallback_model": "qwen:7b",
            "specialized_model": None
        },
        {
            "name": "Specialized Model (CodeLlama)",
            "preferred_model": None,
            "fallback_model": None,
            "specialized_model": "codellama:latest"
        },
        {
            "name": "Multi-Model Configuration",
            "preferred_model": "deepseek-coder:latest",
            "fallback_model": "qwen:7b",
            "specialized_model": "codellama:latest"
        }
    ]
    
    for model_config in models_to_test:
        print(f"\nTesting {model_config['name']}...")
        
        transformer = None
        try:
            transformer = CodebaseTransformer(
                workspace_path=str(test_dir),
                verification_level=VerificationLevel.BASIC.value,
                safe_mode=True,
                preferred_model=model_config["preferred_model"],
                fallback_model=model_config["fallback_model"],
                specialized_model=model_config["specialized_model"],
                ollama_url="http://localhost:11434"  # Explicitly set the Ollama URL
            )
            
            # Test model selection
            code = test_file.read_text()
            selected_model = transformer._select_model_for_transformation(
                transformation_type=TransformationType.REFACTOR.value,
                code=code
            )
            
            print(f"Selected model: {selected_model}")
            
            # Test direct API call to Ollama
            prompt = f"Add docstrings to the following Python code:\n\n{code}\n\nReturn the improved code with docstrings."
            
            # Create a synchronous HTTP client for direct testing
            import httpx
            response = httpx.post(
                f"{transformer.ollama_url}/api/generate",
                json={
                    "model": selected_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"API call successful")
                print(f"Response preview: {result.get('response', '')[:100]}...")
            else:
                print(f"API call failed with status code {response.status_code}")
                print(f"Error: {response.text}")
            
        except Exception as e:
            print(f"Error during test: {e}")
        finally:
            # Close the transformer to release resources
            if transformer:
                await transformer.close()
    
    # Clean up
    if test_file.exists():
        test_file.unlink()
    if test_dir.exists():
        test_dir.rmdir()

if __name__ == "__main__":
    asyncio.run(test_models())
