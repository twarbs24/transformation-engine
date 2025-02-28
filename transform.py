import os
import sys
import json
import subprocess
from pathlib import Path

# Import transformation engine modules
sys.path.append('.')
from models import TransformationType, VerificationLevel
from codebase_transformer import CodebaseTransformer

def main():
    # Get environment variables
    transformation_type = os.environ.get('TRANSFORMATION_TYPE', 'REFACTOR')
    verification_level = os.environ.get('VERIFICATION_LEVEL', 'STANDARD')
    safe_mode = os.environ.get('SAFE_MODE', 'true').lower() == 'true'
    preferred_model = os.environ.get('PREFERRED_MODEL', 'deepseek-coder:latest')
    fallback_model = os.environ.get('FALLBACK_MODEL', 'qwen:7b')
    specialized_model = os.environ.get('SPECIALIZED_MODEL', 'codellama:latest')
    
    # Get list of files to transform
    files_str = os.environ.get('FILES', '')
    files = [f for f in files_str.split() if f]
    
    if not files:
        print("No files to transform")
        return
    
    print(f"Transforming {len(files)} files with {transformation_type} transformation")
    
    # Initialize transformer
    transformer = CodebaseTransformer(
        workspace_path='.',
        verification_level=verification_level,
        safe_mode=safe_mode,
        preferred_model=preferred_model or None,
        fallback_model=fallback_model or None,
        specialized_model=specialized_model or None
    )
    
    # Group files by language
    file_groups = {}
    for file_path in files:
        ext = Path(file_path).suffix.lower()
        language = None
        
        if ext == '.py':
            language = 'python'
        elif ext in ['.js', '.ts']:
            language = 'javascript'
        elif ext == '.java':
            language = 'java'
        
        if language:
            if language not in file_groups:
                file_groups[language] = []
            file_groups[language].append(file_path)
    
    # Transform files by language group
    results = []
    for language, group_files in file_groups.items():
        print(f"Processing {len(group_files)} {language} files")
        
        for file_path in group_files:
            try:
                with open(file_path, 'r') as f:
                    original_code = f.read()
                
                # Apply transformation
                transformed_code, summary = transformer.transform_code(
                    original_code,
                    file_path,
                    language,
                    transformation_type
                )
                
                # Check if code was actually transformed
                if transformed_code != original_code:
                    with open(file_path, 'w') as f:
                        f.write(transformed_code)
                    
                    print(f"✅ Transformed {file_path}")
                    print(f"   Summary: {summary}")
                    
                    results.append({
                        "file": file_path,
                        "status": "success",
                        "summary": summary
                    })
                else:
                    print(f"ℹ️ No changes for {file_path}")
                    
                    results.append({
                        "file": file_path,
                        "status": "unchanged",
                        "summary": "No changes required"
                    })
            
            except Exception as e:
                print(f"❌ Error transforming {file_path}: {str(e)}")
                
                results.append({
                    "file": file_path,
                    "status": "error",
                    "error": str(e)
                })
    
    # Write results to file
    with open('transformation_results.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
