#!/usr/bin/env python3
"""
Comprehensive test runner for the Portal das Finanças Receipts application.
"""

import subprocess
import sys
import os
import time
from datetime import datetime

def run_command(cmd, description):
    """Run a command and capture output."""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=os.getcwd()
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Duration: {duration:.2f}s")
        print(f"Exit Code: {result.returncode}")
        
        if result.stdout:
            print(f"\nOutput:\n{result.stdout}")
        
        if result.stderr and result.returncode != 0:
            print(f"\nErrors:\n{result.stderr}")
            
        return result.returncode == 0, result.stdout, result.stderr, duration
        
    except Exception as e:
        print(f"Failed to run command: {e}")
        return False, "", str(e), 0

def main():
    """Run all test suites."""
    
    print(f"""
Portal das Financas Receipts - Test Suite Runner
{"="*60}
Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Python: {sys.version.split()[0]}
Working Directory: {os.getcwd()}
""")
    
    # Test configurations
    test_suites = [
        {
            "name": "Core Test Suite",
            "command": "python -m pytest tests/ -v --tb=short --ignore=tests/test_validation_aesthetic.py --ignore=tests/test_corrected_export.py --ignore=tests/test_2fa_gui.py",
            "description": "Main unit tests for core functionality (excluding GUI tests with mainloop)"
        },
        {
            "name": "Authentication Tests",
            "command": "python -m pytest tests/test_2fa_authentication_fixed.py -v",
            "description": "2FA and authentication flow tests"
        },
        {
            "name": "Data Processing Tests",
            "command": "python -m pytest tests/test_nif_extraction.py tests/test_multiple_tenants.py tests/test_multiple_parties.py -v",
            "description": "NIF extraction and tenant data processing"
        },
        {
            "name": "Receipt Processing Tests",
            "command": "python -m pytest tests/test_receipt_issuing.py tests/test_payload_validation.py tests/test_payment_date.py -v",
            "description": "Receipt creation and validation"
        },
        {
            "name": "CSV & Validation Tests",
            "command": "python -m pytest tests/test_csv_not_in_portal.py tests/test_flexible_columns.py -v",
            "description": "CSV processing and validation exports"
        },
        {
            "name": "Platform Integration Tests",
            "command": "python -m pytest tests/test_mock_platform.py tests/test_step_by_step_fix.py -v",
            "description": "Platform simulation and step-by-step processing"
        },
        {
            "name": "GUI & Dialog Tests",
            "command": "python -m pytest tests/test_dialog_functionality.py -v",
            "description": "GUI components and dialog functionality"
        }
    ]
    
    # Results tracking
    results = []
    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_duration = 0
    
    # Run each test suite
    for suite in test_suites:
        success, stdout, stderr, duration = run_command(
            suite["command"], 
            f"{suite['name']}: {suite['description']}"
        )
        
        # Parse pytest output to get test counts
        if "passed" in stdout or "failed" in stdout:
            lines = stdout.split('\n')
            for line in lines:
                # Look for pytest summary lines
                if "passed" in line and "in" in line and "s" in line:
                    # Parse lines like:
                    # "18 passed in 0.37s"
                    # "1 failed, 17 passed in 0.98s"
                    # "5 passed, 3 warnings in 0.34s"
                    
                    # Extract numbers before "passed" and "failed"
                    import re
                    passed_match = re.search(r'(\d+)\s+passed', line)
                    failed_match = re.search(r'(\d+)\s+failed', line)
                    
                    if passed_match:
                        passed = int(passed_match.group(1))
                        total_passed += passed
                    
                    if failed_match:
                        failed = int(failed_match.group(1))
                        total_failed += failed
                    
                    break  # Only process the first summary line we find
        
        total_duration += duration
        
        results.append({
            "name": suite["name"],
            "success": success,
            "duration": duration,
            "stdout": stdout,
            "stderr": stderr
        })
    
    # Calculate totals
    total_tests = total_passed + total_failed
    
    # Calculate success rate safely
    if total_tests > 0:
        success_rate = f"{(total_passed/total_tests*100):.1f}%"
    else:
        success_rate = "N/A"
    
    # Print summary
    print(f"""

TEST EXECUTION COMPLETE
{"="*60}
SUMMARY:
   • Total Test Suites: {len(test_suites)}
   • Total Tests: {total_tests}
   • Passed: {total_passed}
   • Failed: {total_failed}
   • Total Duration: {total_duration:.2f}s
   • Success Rate: {success_rate}

DETAILED RESULTS:
""")
    
    for result in results:
        status = "PASSED" if result["success"] else "FAILED"
        print(f"   {status} {result['name']} ({result['duration']:.2f}s)")
    
    # Overall assessment
    if total_failed == 0:
        print(f"\nALL TESTS PASSED! Your application is ready for deployment.")
    else:
        print(f"\nWarning: {total_failed} tests failed. Please review and fix before deployment.")
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return total_failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
