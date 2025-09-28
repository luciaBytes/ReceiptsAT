#!/usr/bin/env python3
"""
Security Audit: Check for any files that might make real API calls

This script scans all Python files to ensure no real API calls can be made
to the Portuguese Tax Authority platform during testing.
"""

import os
import re

def scan_for_security_issues():
    """Scan all Python files for potential security issues."""
    print("=" * 70)
    print("SECURITY AUDIT: Checking for Real API Call Risks")
    print("=" * 70)
    
    issues_found = []
    files_checked = 0
    
    # Patterns that indicate potential real API calls
    dangerous_patterns = [
        (r'WebClient\([^)]*testing_mode\s*=\s*False', 'WebClient with testing_mode=False'),
        (r'requests\.(get|post|put|delete)\s*\(', 'Direct requests calls (should be mocked)'),
        (r'autenticacao\.gov\.pt', 'Direct reference to Autenticacao.Gov domain'),
        (r'portal\.financas\.gov\.pt', 'Direct reference to Portal das Financas domain'),
        (r'\.login\([^)]*\).*#.*real|#.*production', 'Login call marked as real/production'),
    ]
    
    # Scan all Python files
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        skip_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', 'dist', 'build'}
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.endswith('.py'):
                files_checked += 1
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    for pattern, description in dangerous_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                        for match in matches:
                            # Get line number
                            line_num = content[:match.start()].count('\n') + 1
                            line_content = content.split('\n')[line_num - 1].strip()
                            
                            # Check if it's in a test file with proper mocking
                            is_test_file = 'test' in file_path.lower() or 'tests' in file_path.lower()
                            has_mock = 'mock' in content.lower() or 'patch' in content.lower()
                            
                            if not (is_test_file and has_mock):
                                issues_found.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'content': line_content,
                                    'issue': description,
                                    'severity': 'HIGH' if 'testing_mode=False' in line_content else 'MEDIUM'
                                })
                
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}")
    
    # Report results
    print(f"Files checked: {files_checked}")
    print(f"Security issues found: {len(issues_found)}")
    print()
    
    if issues_found:
        print("SECURITY ISSUES DETECTED:")
        print("-" * 50)
        
        for issue in sorted(issues_found, key=lambda x: x['severity'], reverse=True):
            severity_icon = "🚨" if issue['severity'] == 'HIGH' else "⚠️"
            print(f"{severity_icon} {issue['severity']}: {issue['file']}:{issue['line']}")
            print(f"   Issue: {issue['issue']}")
            print(f"   Code: {issue['content']}")
            print()
        
        print("RECOMMENDATIONS:")
        print("1. Change all WebClient(testing_mode=False) to WebClient(testing_mode=True)")
        print("2. Ensure all tests use proper mocking (patch requests.Session)")
        print("3. Never commit files with real credentials or testing_mode=False")
        print("4. Use environment variables or config files for production settings")
        
        return False
    else:
        print("✅ NO SECURITY ISSUES FOUND!")
        print("All files appear to be properly configured for testing.")
        return True

if __name__ == "__main__":
    secure = scan_for_security_issues()
    exit(0 if secure else 1)