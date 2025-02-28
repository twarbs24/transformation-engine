import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from codebase_transformer import CodebaseTransformer
from models import TransformationType, VerificationLevel


@pytest.fixture
def mock_http_client():
    """Mock for httpx AsyncClient."""
    mock = AsyncMock()
    mock.post.return_value = AsyncMock()
    mock.post.return_value.status_code = 200
    mock.post.return_value.json.return_value = {
        "response": """SUMMARY: Refactored the code to improve readability.

```python
def hello_world():
    \"\"\"Print hello world message.\"\"\"
    print("Hello, World!")
```"""
    }
    return mock


@pytest.fixture
def mock_metrics_collector():
    """Mock for MetricsCollector."""
    mock = MagicMock()
    mock.calculate_complexity_reduction.return_value = {
        "complexity_before": 5,
        "complexity_after": 3,
        "reduction_percentage": 40.0,
    }
    return mock


@pytest.fixture
def mock_knowledge_repo():
    """Mock for KnowledgeRepoClient."""
    mock = AsyncMock()
    mock.retrieve_transformation_patterns.return_value = {
        "success": True,
        "data": {
            "patterns": [
                {
                    "description": "Replace for loops with list comprehensions",
                    "example": "Use [x for x in items] instead of for loops"
                }
            ]
        }
    }
    mock.record_transformation_success.return_value = {"success": True}
    return mock


@pytest.fixture
def mock_code_analyzer():
    """Mock for CodeAnalyzerClient."""
    mock = AsyncMock()
    mock.update_file_metrics_after_transformation.return_value = {"success": True}
    return mock


@pytest.fixture
def transformer(mock_http_client, mock_metrics_collector, mock_knowledge_repo, mock_code_analyzer):
    """Create a CodebaseTransformer with mocked dependencies."""
    with patch("codebase_transformer.httpx.AsyncClient", return_value=mock_http_client), \
         patch("codebase_transformer.MetricsCollector", return_value=mock_metrics_collector):
        transformer = CodebaseTransformer(
            workspace_path="/tmp/test_workspace",
            verification_level=VerificationLevel.BASIC.value,
            safe_mode=True,
            code_analyzer_client=mock_code_analyzer,
            knowledge_repo_client=mock_knowledge_repo,
            ollama_url="http://test-ollama:11434",
            ollama_model="test-model"
        )
        yield transformer


@pytest.mark.asyncio
async def test_apply_transformation(transformer, mock_http_client, tmp_path):
    """Test applying a transformation to code."""
    # Setup
    original_code = """def hello():
    print('hello')
"""
    file_path = "test.py"
    language = "python"
    transformation_type = TransformationType.REFACTOR.value
    
    # Execute
    transformed_code, summary = await transformer._apply_transformation(
        original_code=original_code,
        file_path=file_path,
        language=language,
        transformation_type=transformation_type
    )
    
    # Verify
    assert "Hello, World!" in transformed_code
    assert "Refactored" in summary
    mock_http_client.post.assert_called_once()
    

@pytest.mark.asyncio
async def test_transform_files(transformer, mock_http_client, tmp_path):
    """Test transforming multiple files."""
    # Setup
    workspace_path = str(tmp_path)
    transformer.workspace_path = workspace_path
    
    # Create test files
    test_file_path = os.path.join(workspace_path, "test.py")
    with open(test_file_path, 'w') as f:
        f.write("def hello(): print('hello')")
    
    files = [
        {
            "path": "test.py",
            "language": "python"
        }
    ]
    
    # Mock verification
    with patch("codebase_transformer.TransformationVerifier.verify_transformation", 
               return_value={"verified": True, "errors": []}):
        
        # Execute
        results = await transformer.transform_files(
            files=files,
            transformation_type=TransformationType.REFACTOR.value,
            job_id="test_job_123"
        )
    
    # Verify
    assert len(results) == 1
    assert results[0]["status"] == "success"
    assert results[0]["job_id"] == "test_job_123"
    assert results[0]["file_path"] == "test.py"
    
    # Verify file was transformed
    with open(test_file_path, 'r') as f:
        content = f.read()
        assert "Hello, World!" in content


@pytest.mark.asyncio
async def test_transform_files_verification_failure(transformer, mock_http_client, tmp_path):
    """Test handling verification failure in safe mode."""
    # Setup
    workspace_path = str(tmp_path)
    transformer.workspace_path = workspace_path
    transformer.safe_mode = True
    
    # Create test files
    test_file_path = os.path.join(workspace_path, "test.py")
    with open(test_file_path, 'w') as f:
        f.write("def hello(): print('hello')")
    
    files = [
        {
            "path": "test.py",
            "language": "python"
        }
    ]
    
    # Mock verification failure
    with patch("codebase_transformer.TransformationVerifier.verify_transformation", 
               return_value={"verified": False, "errors": ["Syntax error"]}):
        
        # Execute
        results = await transformer.transform_files(
            files=files,
            transformation_type=TransformationType.REFACTOR.value,
            job_id="test_job_123"
        )
    
    # Verify
    assert len(results) == 1
    assert results[0]["status"] == "failed"
    assert "Verification failed" in results[0]["error"]
    
    # Verify file was not transformed
    with open(test_file_path, 'r') as f:
        content = f.read()
        assert "def hello(): print('hello')" == content
