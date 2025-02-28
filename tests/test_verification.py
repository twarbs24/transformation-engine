import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock

from verification import TransformationVerifier
from models import VerificationLevel


@pytest.fixture
def sample_python_code_before():
    return """
def add_numbers(a, b):
    # Add two numbers
    return a + b

def multiply_numbers(a, b):
    # Multiply two numbers
    return a * b
"""


@pytest.fixture
def sample_python_code_after_valid():
    return """
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

def multiply_numbers(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b
"""


@pytest.fixture
def sample_python_code_after_invalid():
    return """
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

def multiply_numbers(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b  # Missing closing parenthesis
"""


@pytest.fixture
def sample_js_code_before():
    return """
function addNumbers(a, b) {
    // Add two numbers
    return a + b;
}

function multiplyNumbers(a, b) {
    // Multiply two numbers
    return a * b;
}
"""


@pytest.fixture
def sample_js_code_after_valid():
    return """
/**
 * Add two numbers together
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} Sum of a and b
 */
function addNumbers(a, b) {
    return a + b;
}

/**
 * Multiply two numbers together
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} Product of a and b
 */
function multiplyNumbers(a, b) {
    return a * b;
}
"""


@pytest.fixture
def sample_js_code_after_invalid():
    return """
/**
 * Add two numbers together
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} Sum of a and b
 */
function addNumbers(a, b) {
    return a + b;
}

/**
 * Multiply two numbers together
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} Product of a and b
 */
function multiplyNumbers(a, b) {
    return a * b  // Missing semicolon
}
"""


def test_verify_python_syntax_valid():
    """Test Python syntax verification with valid code."""
    code = """
def hello():
    print("Hello, world!")
    return True
"""
    result = TransformationVerifier._verify_syntax(code, "python")
    assert result["verified"] is True
    assert len(result["errors"]) == 0


def test_verify_python_syntax_invalid():
    """Test Python syntax verification with invalid code."""
    code = """
def hello():
    print("Hello, world!"
    return True
"""
    result = TransformationVerifier._verify_syntax(code, "python")
    assert result["verified"] is False
    assert len(result["errors"]) > 0


def test_verify_javascript_syntax_valid():
    """Test JavaScript syntax verification with valid code."""
    code = """
function hello() {
    console.log("Hello, world!");
    return true;
}
"""
    result = TransformationVerifier._verify_syntax(code, "javascript")
    assert result["verified"] is True
    assert len(result["errors"]) == 0


def test_verify_javascript_syntax_invalid():
    """Test JavaScript syntax verification with invalid code."""
    code = """
function hello() {
    console.log("Hello, world!"
    return true;
}
"""
    result = TransformationVerifier._verify_syntax(code, "javascript")
    assert result["verified"] is False
    assert len(result["errors"]) > 0


def test_verify_transformation_basic_level(sample_python_code_before, sample_python_code_after_valid):
    """Test transformation verification at BASIC level."""
    with patch('verification.TransformationVerifier._verify_syntax') as mock_verify_syntax:
        mock_verify_syntax.return_value = {"verified": True, "errors": []}
        
        result = TransformationVerifier.verify_transformation(
            before_code=sample_python_code_before,
            after_code=sample_python_code_after_valid,
            file_path="test.py",
            verification_level=VerificationLevel.BASIC.value,
            workspace_dir="/tmp"
        )
        
        assert result["verified"] is True
        assert "syntax" in result
        assert result["syntax"]["verified"] is True
        mock_verify_syntax.assert_called_once()


def test_verify_transformation_standard_level(sample_python_code_before, sample_python_code_after_valid):
    """Test transformation verification at STANDARD level."""
    with patch('verification.TransformationVerifier._verify_syntax') as mock_verify_syntax, \
         patch('verification.TransformationVerifier._run_tests') as mock_run_tests:
        
        mock_verify_syntax.return_value = {"verified": True, "errors": []}
        mock_run_tests.return_value = {"verified": True, "errors": [], "test_results": {"passed": 5, "failed": 0}}
        
        result = TransformationVerifier.verify_transformation(
            before_code=sample_python_code_before,
            after_code=sample_python_code_after_valid,
            file_path="test.py",
            verification_level=VerificationLevel.STANDARD.value,
            workspace_dir="/tmp"
        )
        
        assert result["verified"] is True
        assert "syntax" in result
        assert "tests" in result
        assert result["syntax"]["verified"] is True
        assert result["tests"]["verified"] is True
        mock_verify_syntax.assert_called_once()
        mock_run_tests.assert_called_once()


def test_verify_transformation_strict_level(sample_python_code_before, sample_python_code_after_valid):
    """Test transformation verification at STRICT level."""
    with patch('verification.TransformationVerifier._verify_syntax') as mock_verify_syntax, \
         patch('verification.TransformationVerifier._run_tests') as mock_run_tests, \
         patch('verification.TransformationVerifier._verify_functionality') as mock_verify_functionality:
        
        mock_verify_syntax.return_value = {"verified": True, "errors": []}
        mock_run_tests.return_value = {"verified": True, "errors": [], "test_results": {"passed": 5, "failed": 0}}
        mock_verify_functionality.return_value = {"verified": True, "errors": []}
        
        result = TransformationVerifier.verify_transformation(
            before_code=sample_python_code_before,
            after_code=sample_python_code_after_valid,
            file_path="test.py",
            verification_level=VerificationLevel.STRICT.value,
            workspace_dir="/tmp"
        )
        
        assert result["verified"] is True
        assert "syntax" in result
        assert "tests" in result
        assert "functionality" in result
        assert result["syntax"]["verified"] is True
        assert result["tests"]["verified"] is True
        assert result["functionality"]["verified"] is True
        mock_verify_syntax.assert_called_once()
        mock_run_tests.assert_called_once()
        mock_verify_functionality.assert_called_once()


def test_verify_transformation_failure(sample_python_code_before, sample_python_code_after_invalid):
    """Test transformation verification with invalid code."""
    result = TransformationVerifier.verify_transformation(
        before_code=sample_python_code_before,
        after_code=sample_python_code_after_invalid,
        file_path="test.py",
        verification_level=VerificationLevel.BASIC.value,
        workspace_dir="/tmp"
    )
    
    assert result["verified"] is False
    assert "syntax" in result
    assert result["syntax"]["verified"] is False
    assert len(result["syntax"]["errors"]) > 0


def test_detect_test_framework():
    """Test detection of test frameworks."""
    # Create a temporary directory with test files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create pytest file
        with open(os.path.join(temp_dir, "test_something.py"), "w") as f:
            f.write("def test_function(): assert True")
        
        # Create a requirements.txt with pytest
        with open(os.path.join(temp_dir, "requirements.txt"), "w") as f:
            f.write("pytest==7.0.0\nrequests==2.28.1")
        
        framework = TransformationVerifier._detect_test_framework(temp_dir)
        assert framework == "pytest"


def test_run_tests():
    """Test running tests."""
    with patch('subprocess.run') as mock_run:
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = b"Ran 5 tests, all passed"
        mock_run.return_value = mock_process
        
        with patch('verification.TransformationVerifier._detect_test_framework') as mock_detect:
            mock_detect.return_value = "pytest"
            
            result = TransformationVerifier._run_tests("/tmp", "test.py")
            
            assert result["verified"] is True
            assert len(result["errors"]) == 0
            mock_run.assert_called_once()
            mock_detect.assert_called_once()
