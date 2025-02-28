# Transformation Engine for Autogenic AI Codebase Enhancer

The Transformation Engine is a core component of the Autogenic AI Codebase Enhancer ecosystem, responsible for intelligently transforming code using AI-driven techniques. It analyzes, refactors, and improves software codebases across multiple programming languages.

## Features

- **AI-Driven Transformations**: Leverages Ollama AI models to intelligently transform code
- **Multiple Transformation Types**:
  - `REFACTOR`: Improve code readability and maintainability
  - `OPTIMIZE`: Enhance performance
  - `PRUNE`: Remove unused code
  - `MERGE`: Consolidate related functionality
  - `MODERNIZE`: Update to newer language patterns
  - `FIX_SECURITY`: Address potential vulnerabilities
- **Multi-Language Support**: Handles Python, JavaScript, TypeScript, Java, and more
- **Verification System**: Ensures transformations maintain code functionality
  - Syntax checking
  - Test execution
  - Verification levels (none, basic, standard, strict)
- **Safe Mode**: Option to only apply verified transformations
- **Batch Processing**: Process files in manageable chunks for optimal performance
- **API-First Design**: RESTful API for integration with other services
- **GitHub Authentication**: Secure access to private repositories using GitHub tokens

## Architecture

The Transformation Engine consists of two primary components:

1. **Server (server.py)**: FastAPI-based service that handles transformation requests
2. **Codebase Transformer (codebase_transformer.py)**: Core transformation logic

### API Endpoints

- `POST /transformations/start`: Start a new transformation job
- `GET /transformations/{job_id}`: Check status of a transformation job
- `GET /transformations/{job_id}/results`: Get results of a completed job
- `DELETE /transformations/{job_id}`: Cancel a running job

## Configuration

The service is configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017/mcp` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `CODE_ANALYZER_URL` | Code Analyzer service URL | `http://localhost:8080` |
| `KNOWLEDGE_REPO_URL` | Knowledge Repository service URL | `http://localhost:8080` |
| `OLLAMA_URL` | Ollama API URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model to use | `codellama:13b` |
| `WORKSPACE_DIR` | Directory for transformation workspaces | `/tmp/workspaces` |
| `SAFE_MODE` | Only apply verified transformations | `true` |

## Deployment

The service is designed to be deployed as a Docker container and integrates with the MCP server implementation. See `Dockerfile` and `docker-compose.yml` for deployment details.

## Dependencies

- FastAPI
- Uvicorn
- Motor (MongoDB)
- Redis
- httpx
- GitPython
- Language-specific tools (pylint, eslint, etc.)

## Development

To run the service locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn server:app --reload
```

## Integration

The Transformation Engine integrates with:

1. **Code Analyzer Service**: Gets analysis results to prioritize transformations
2. **Knowledge Repository**: Stores and retrieves successful transformation patterns
3. **Ollama AI Service**: Performs AI-driven code transformations

## Safety Considerations

- Creates working copies before transformation
- Verifies syntax and correctness
- Runs tests when available
- Supports safe mode for production use

## GitHub Authentication

The Transformation Engine supports secure authentication for accessing private GitHub repositories:

- **Token-based Authentication**: Uses GitHub Personal Access Tokens
- **Environment Variables**: Configure via `GITHUB_TOKEN` and `GIT_USERNAME`
- **Kubernetes Secrets**: Securely stored in the Kubernetes cluster
- **Multiple URL Formats**: Supports both HTTPS and SSH repository URLs

For detailed setup instructions, see [GitHub Authentication Setup](./docs/github-auth-setup.md).

## CI/CD Integration

The Transformation Engine can be integrated with CI/CD pipelines in several ways:

### GitHub Actions

A GitHub Actions workflow is provided to automatically run transformations on push or pull request events. See `.github/workflows/auto-transform.yml` for details.

### Kubernetes CronJob

A Kubernetes CronJob can be configured to run transformations on a schedule. See `k8s/cronjob.yaml` for details.

### GitHub Webhook Receiver

A webhook receiver service is available to trigger transformations in response to GitHub events. See `webhook-receiver/` for implementation details.

### Command Line Integration

The `scripts/trigger-transformation.py` script can be used to trigger transformations from any CI/CD pipeline.

For detailed instructions, see [CI/CD Integration Documentation](docs/cicd-integration.md).

## Installation

To install the Transformation Engine, follow these steps:

```bash
# Clone the repository
git clone https://github.com/autogenic-ai/transformation-engine.git

# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn server:app --reload
```

Note: This installation guide assumes you have Python 3.8 or later installed on your system.
