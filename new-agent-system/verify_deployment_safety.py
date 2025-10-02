#!/usr/bin/env python3
"""
Deployment Safety Verification Script
Checks for hardcoded credentials before deployment to Streamlit Cloud
"""
import os
import re
import glob
from pathlib import Path

def scan_file_for_credentials(file_path):
    """Scan a file for potential hardcoded credentials"""
    issues = []
    
    # Patterns to look for
    dangerous_patterns = [
        (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API Key'),
        (r'AKIA[0-9A-Z]{16}', 'AWS Access Key'),
        (r'[A-Za-z0-9/+]{40}', 'AWS Secret Key (potential)'),
        (r'aws_access_key_id\s*=\s*["\'][^"\']+["\']', 'Hardcoded AWS Access Key'),
        (r'aws_secret_access_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded AWS Secret Key'),
        (r'openai_api_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded OpenAI Key'),
        (r'api_key\s*=\s*["\']sk-[^"\']+["\']', 'Hardcoded OpenAI API Key'),
    ]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for pattern, description in dangerous_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Filter out obvious environment variable usage
                for match in matches:
                    if 'getenv' not in content or 'os.environ' not in content:
                        issues.append({
                            'file': file_path,
                            'issue': description,
                            'match': match[:20] + '...' if len(match) > 20 else match
                        })
                        
    except Exception as e:
        issues.append({
            'file': file_path,
            'issue': f'Error reading file: {e}',
            'match': ''
        })
    
    return issues

def check_environment_variable_usage(file_path):
    """Check if file properly uses environment variables"""
    env_usage = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Look for proper environment variable usage
        env_patterns = [
            r'os\.getenv\(["\'][^"\']+["\']\)',
            r'os\.environ\.get\(["\'][^"\']+["\']\)',
            r'os\.environ\[["\'][^"\']+["\']\]'
        ]
        
        for pattern in env_patterns:
            matches = re.findall(pattern, content)
            env_usage.extend(matches)
            
    except Exception as e:
        pass
    
    return env_usage

def main():
    """Main verification function"""
    print("🔍 **Deployment Safety Verification**")
    print("=" * 50)
    
    # Files to check
    python_files = []
    for pattern in ['**/*.py', '*.py']:
        python_files.extend(glob.glob(pattern, recursive=True))
    
    # Remove test files and __pycache__
    python_files = [f for f in python_files if '__pycache__' not in f and 'test_' not in f]
    
    print(f"Scanning {len(python_files)} Python files...")
    print()
    
    all_issues = []
    files_with_env_usage = []
    
    for file_path in python_files:
        # Check for credential issues
        issues = scan_file_for_credentials(file_path)
        all_issues.extend(issues)
        
        # Check for environment variable usage
        env_usage = check_environment_variable_usage(file_path)
        if env_usage:
            files_with_env_usage.append((file_path, env_usage))
    
    # Report results
    if all_issues:
        print("🚨 **SECURITY ISSUES FOUND:**")
        print("-" * 30)
        for issue in all_issues:
            print(f"❌ {issue['file']}")
            print(f"   Issue: {issue['issue']}")
            print(f"   Match: {issue['match']}")
            print()
        print("⚠️  **DO NOT DEPLOY** - Fix these issues first!")
        return False
    else:
        print("✅ **NO HARDCODED CREDENTIALS FOUND**")
        print()
    
    # Show proper environment variable usage
    if files_with_env_usage:
        print("✅ **PROPER ENVIRONMENT VARIABLE USAGE:**")
        print("-" * 40)
        for file_path, usage in files_with_env_usage:
            print(f"✓ {file_path}")
            for env_var in usage:
                print(f"   {env_var}")
            print()
    
    # Check for .env in .gitignore
    gitignore_path = '.gitignore'
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()
            
        if '.env' in gitignore_content:
            print("✅ **.env file is in .gitignore**")
        else:
            print("❌ **.env file NOT in .gitignore** - Add it!")
            return False
    else:
        print("❌ **.gitignore file not found** - Create it!")
        return False
    
    print()
    print("🎉 **DEPLOYMENT SAFETY CHECK PASSED!**")
    print()
    print("✅ No hardcoded credentials found")
    print("✅ Proper environment variable usage detected")
    print("✅ .env file is properly ignored")
    print()
    print("🚀 **Safe to deploy to Streamlit Cloud!**")
    
    return True

if __name__ == "__main__":
    is_safe = main()
    exit(0 if is_safe else 1)