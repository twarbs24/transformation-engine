# Model Configuration for Transformation Engine

This document explains the model configuration for the Transformation Engine and how to use different AI models for code transformations.

## Available Models

The Transformation Engine supports the following AI models:

1. **Preferred Model**: `deepseek-coder:latest`
   - Primary model for most transformations
   - Best for general-purpose code transformations
   - Optimized for readability and maintainability

2. **Fallback Model**: `qwen:7b`
   - Used when the preferred model fails or is unavailable
   - Smaller and faster, but potentially less capable
   - Good for simpler transformations

3. **Specialized Model**: `codellama:latest`
   - Used for complex transformations
   - Particularly good for security fixes and optimization
   - May be slower but more thorough

## Configuration Options

You can configure which models to use in several ways:

### 1. Environment Variables

Set these environment variables to configure the models:

```bash
export PREFERRED_MODEL="deepseek-coder:latest"
export FALLBACK_MODEL="qwen:7b"
export SPECIALIZED_MODEL="codellama:latest"
```

### 2. Kubernetes ConfigMap

The models are configured in the `transformation-engine-config` ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: transformation-engine-config
  namespace: code-analysis
data:
  preferred_model: "deepseek-coder:latest"
  fallback_model: "qwen:7b"
  specialized_model: "codellama:latest"
  # Other configuration...
```

### 3. Command Line Arguments

When using the `trigger-transformation.py` script, you can specify models directly:

```bash
python trigger-transformation.py \
  --repo-url https://github.com/your-org/your-repo.git \
  --preferred-model "deepseek-coder:latest" \
  --fallback-model "qwen:7b" \
  --specialized-model "codellama:latest"
```

### 4. GitHub Actions Workflow

When triggering the transformation via GitHub Actions, you can specify models in the workflow dispatch:

```yaml
on:
  workflow_dispatch:
    inputs:
      preferred_model:
        description: 'Preferred model to use for transformations'
        default: 'deepseek-coder:latest'
      fallback_model:
        description: 'Fallback model to use for transformations'
        default: 'qwen:7b'
      specialized_model:
        description: 'Specialized model for complex transformations'
        default: 'codellama:latest'
```

## Model Selection Strategy

The Transformation Engine uses a tiered approach to model selection:

1. For each transformation, it first selects the appropriate model based on:
   - Transformation type (REFACTOR, OPTIMIZE, etc.)
   - Code complexity
   - Language-specific requirements

2. It attempts the transformation with the selected model.

3. If the transformation fails or produces no changes, it falls back to the next model in the hierarchy.

4. For complex transformations (like security fixes), it may directly use the specialized model.

## Adding New Models

To add new models to the system:

1. Pull the model using Ollama:
   ```bash
   ollama pull new-model:tag
   ```

2. Update the ConfigMap and other configuration files to use the new model.

3. Test the model with the `test_models.py` script to ensure it works correctly.
