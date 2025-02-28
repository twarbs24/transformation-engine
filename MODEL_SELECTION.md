# AI Model Selection Strategy for Code Transformations

The Autogenic AI Codebase Enhancer uses a tiered approach to model selection for code transformations, leveraging the strengths of different AI models for different types of transformations.

## Model Hierarchy

### 1. Primary Model: DeepSeek-Coder-V2 (16B)

**Default:** `deepseek-coder-v2:16b`

The DeepSeek-Coder-V2 model is our preferred choice for most code transformations due to its:

- Performance comparable to GPT4-Turbo
- Excellent reasoning capabilities
- Strong understanding of code patterns and best practices
- Ability to handle a wide range of programming languages

This model is used by default for most transformation operations.

### 2. Fallback Model: Qwen2.5-Coder (7B)

**Default:** `qwen2.5-coder:7b`

The Qwen2.5-Coder model serves as our fallback option when:

- The primary model fails to produce a valid transformation
- System resources are constrained
- Faster processing is needed for simpler transformations

This model is more resource-efficient while still providing good quality code transformations.

### 3. Specialized Model: CodeLlama (34B)

**Default:** `codellama:34b`

The CodeLlama model is specifically used for:

- Complex refactoring operations
- Security vulnerability fixes
- Large file transformations (>1000 lines)

This model excels at understanding complex code relationships and can handle more sophisticated transformations that require deeper code comprehension.

## Dynamic Model Selection

The transformation engine automatically selects the appropriate model based on:

1. **Transformation Type**: Security fixes and refactoring operations may use the specialized model
2. **Code Complexity**: Larger files (>1000 lines) are processed with the specialized model
3. **Failure Recovery**: If the preferred model fails, the system automatically falls back to the fallback model

## Configuration

Models can be configured through:

1. **Environment Variables**:
   ```
   PREFERRED_MODEL=deepseek-coder-v2:16b
   FALLBACK_MODEL=qwen2.5-coder:7b
   SPECIALIZED_MODEL=codellama:34b
   ```

2. **Kubernetes ConfigMap**:
   ```yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: transformation-engine-config
     namespace: code-analysis
   data:
     preferred_model: "deepseek-coder-v2:16b"
     fallback_model: "qwen2.5-coder:7b"
     specialized_model: "codellama:34b"
   ```

3. **API Parameters**:
   Models can be specified when calling the transformation API:
   ```json
   {
     "repo_url": "https://github.com/example/repo.git",
     "branch": "main",
     "transformation_type": "REFACTOR",
     "preferred_model": "deepseek-coder-v2:16b",
     "fallback_model": "qwen2.5-coder:7b",
     "specialized_model": "codellama:34b"
   }
   ```

4. **Command Line**:
   When using the trigger script:
   ```bash
   python trigger-transformation.py \
     --repo-url https://github.com/example/repo.git \
     --transformation-type REFACTOR \
     --preferred-model deepseek-coder-v2:16b \
     --fallback-model qwen2.5-coder:7b \
     --specialized-model codellama:34b
   ```

## Performance Considerations

- The specialized model (34B) requires more GPU memory and may process code more slowly
- The fallback model (7B) is the most resource-efficient but may produce simpler transformations
- The preferred model (16B) offers the best balance of quality and performance

## Future Improvements

Future versions of the transformation engine will include:

1. Automatic benchmarking to evaluate model performance on different transformation types
2. More granular model selection based on specific code patterns
3. Dynamic resource allocation based on available GPU capacity
4. Support for custom fine-tuned models for organization-specific codebases
