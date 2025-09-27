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
            "command": "python -m pytest tests/ -v --tb=short",
            "description": "Main unit tests for core functionality"
        },
        {
            "name": "Authentication Tests",
            "command": "python -m pytest tests/test_2fa_authentication.py tests/test_2fa_translations.py -v",
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
            "name": "Multilingual Localization Tests",
            "command": "python -m pytest tests/test_multilingual_localization.py -v",
            "description": "Multilingual interface and localization system tests"
        }
    ]
    
    # Results tracking
    results = []
    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_suites_passed = 0
    total_suites_failed = 0
    total_duration = 0
    
    # Run each test suite
    for suite in test_suites:
        success, stdout, stderr, duration = run_command(
            suite["command"], 
            f"{suite['name']}: {suite['description']}"
        )
        
        # Track suite-level success/failure
        if success:
            total_suites_passed += 1
        else:
            total_suites_failed += 1
        
        # Parse pytest output to get individual test counts
        suite_passed = 0
        suite_failed = 0
        
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
                        suite_passed = int(passed_match.group(1))
                        total_passed += suite_passed
                    
                    if failed_match:
                        suite_failed = int(failed_match.group(1))
                        total_failed += suite_failed
                    
                    break  # Only process the first summary line we find
        
        total_duration += duration
        
        results.append({
            "name": suite["name"],
            "success": success,
            "duration": duration,
            "tests_passed": suite_passed,
            "tests_failed": suite_failed,
            "stdout": stdout,
            "stderr": stderr
        })
    
    # Calculate totals
    total_tests = total_passed + total_failed
    
    # Calculate success rates
    if total_tests > 0:
        individual_test_success_rate = f"{(total_passed/total_tests*100):.1f}%"
    else:
        individual_test_success_rate = "N/A"
    
    if len(test_suites) > 0:
        suite_success_rate = f"{(total_suites_passed/len(test_suites)*100):.1f}%"
    else:
        suite_success_rate = "N/A"
    
    # Print summary
    print(f"""

TEST EXECUTION COMPLETE
{"="*60}
SUMMARY:
   - Total Test Suites: {len(test_suites)} (Passed: {total_suites_passed}, Failed: {total_suites_failed})
   - Suite Success Rate: {suite_success_rate}
   - Individual Tests: {total_tests} (Passed: {total_passed}, Failed: {total_failed})
   - Individual Test Success Rate: {individual_test_success_rate}
   - Total Duration: {total_duration:.2f}s

DETAILED RESULTS:
""")
    
    for result in results:
        status = "PASSED" if result["success"] else "FAILED"
        test_info = ""
        if result["tests_passed"] > 0 or result["tests_failed"] > 0:
            test_info = f" - {result['tests_passed']} passed, {result['tests_failed']} failed"
        print(f"   {status} {result['name']} ({result['duration']:.2f}s){test_info}")
    
    # Overall assessment - both suites AND individual tests must pass
    overall_success = (total_suites_failed == 0 and total_failed == 0)
    
    if overall_success:
        print(f"\n[PASS] ALL TESTS PASSED! Your application is ready for deployment.")
    else:
        print(f"\n[FAIL] TESTS FAILED!")
        if total_suites_failed > 0:
            print(f"   - {total_suites_failed} test suite(s) failed to run")
        if total_failed > 0:
            print(f"   - {total_failed} individual test(s) failed")
        print(f"   Please review and fix issues before deployment.")
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
