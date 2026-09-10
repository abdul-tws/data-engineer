#!/usr/bin/env python3
"""
Test Runner - Executes all test suites with detailed reporting
"""

import sys
import unittest
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root / 'tests'))


def run_all_tests(verbosity=2):
    """Run all test suites"""
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = str(project_root / 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run with detailed reporting
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    return result


def run_specific_test(test_module, test_class=None, test_method=None):
    """Run specific test or test class"""
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Build test name
    if test_class and test_method:
        test_name = f"{test_module}.{test_class}.{test_method}"
    elif test_class:
        test_name = f"{test_module}.{test_class}"
    else:
        test_name = test_module
    
    try:
        suite.addTests(loader.loadTestsFromName(test_name))
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result
    except Exception as e:
        print(f"Error running test: {e}")
        return None


def print_test_summary(result):
    """Print test execution summary"""
    
    print("\n" + "="*70)
    print("TEST EXECUTION SUMMARY")
    print("="*70)
    
    tests_run = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    success = tests_run - failures - errors - skipped
    
    print(f"\nTotal Tests Run: {tests_run}")
    print(f"  ✓ Success:  {success}")
    print(f"  ✗ Failures: {failures}")
    print(f"  ✗ Errors:   {errors}")
    print(f"  ⊘ Skipped:  {skipped}")
    
    if failures > 0:
        print("\nFailed Tests:")
        for test, traceback in result.failures:
            print(f"  - {test}")
            print(f"    {traceback.split(chr(10))[0]}")
    
    if errors > 0:
        print("\nTests with Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}")
            print(f"    {traceback.split(chr(10))[0]}")
    
    print("\n" + "="*70)
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        return 1


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run tests for Fund Position Reconciliation'
    )
    parser.add_argument(
        '--module',
        help='Specific test module (e.g., test_database)',
        default=None
    )
    parser.add_argument(
        '--class',
        dest='test_class',
        help='Specific test class',
        default=None
    )
    parser.add_argument(
        '--method',
        help='Specific test method',
        default=None
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    print("Fund Position Reconciliation - Test Suite")
    print("=" * 70)
    
    if args.module:
        print(f"\nRunning: {args.module}", end="")
        if args.test_class:
            print(f".{args.test_class}", end="")
            if args.method:
                print(f".{args.method}", end="")
        print()
        result = run_specific_test(args.module, args.test_class, args.method)
    else:
        print("\nRunning all tests...\n")
        result = run_all_tests(verbosity=2)
    
    exit_code = print_test_summary(result)
    sys.exit(exit_code)
