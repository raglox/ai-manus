#!/usr/bin/env python3
"""
Integration Test Suite for AI-Manus Phase 1
Tests all critical fixes: Security, Health, Rate Limiting, Billing
"""

import sys
import time
import json
import subprocess
from typing import Dict, List, Tuple
from datetime import datetime

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class TestResult:
    """Test result container"""
    def __init__(self, name: str, status: str, duration: float, notes: str = ""):
        self.name = name
        self.status = status  # PASS, FAIL, SKIP, ERROR
        self.duration = duration
        self.notes = notes


class IntegrationTestSuite:
    """Main test suite runner"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()
        
    def run_command(self, cmd: List[str], timeout: int = 30) -> Tuple[int, str, str]:
        """Run shell command and return exit code, stdout, stderr"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd="/home/user/webapp"
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return -1, "", str(e)
    
    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{BLUE}{'='*80}{RESET}")
        print(f"{BLUE}{text:^80}{RESET}")
        print(f"{BLUE}{'='*80}{RESET}\n")
    
    def print_test(self, name: str):
        """Print test name"""
        print(f"{YELLOW}▶ Running: {name}{RESET}")
    
    def print_result(self, result: TestResult):
        """Print test result"""
        status_color = GREEN if result.status == "PASS" else RED if result.status == "FAIL" else YELLOW
        status_symbol = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "⏭️"
        
        print(f"{status_color}{status_symbol} {result.status}: {result.name} ({result.duration:.2f}s){RESET}")
        if result.notes:
            print(f"   Notes: {result.notes}")
    
    def test_jwt_secret_validation(self):
        """Test 1.1: JWT Secret must be set"""
        self.print_test("Test 1.1: JWT Secret Validation")
        start = time.time()
        
        # Check if JWT_SECRET_KEY is set in .env
        returncode, stdout, stderr = self.run_command([
            "bash", "-c",
            "grep -E '^JWT_SECRET_KEY=.+' /home/user/webapp/.env"
        ])
        
        duration = time.time() - start
        
        if returncode == 0 and "JWT_SECRET_KEY=" in stdout and len(stdout.strip().split('=')[1]) >= 32:
            result = TestResult(
                "JWT Secret Validation",
                "PASS",
                duration,
                f"JWT_SECRET_KEY is set and >= 32 chars"
            )
        else:
            result = TestResult(
                "JWT Secret Validation",
                "FAIL",
                duration,
                "JWT_SECRET_KEY is missing or too short"
            )
        
        self.results.append(result)
        self.print_result(result)
        return result.status == "PASS"
    
    def test_backend_syntax(self):
        """Test 1.2: Backend Python syntax check"""
        self.print_test("Test 1.2: Backend Syntax Check")
        start = time.time()
        
        # Check Python syntax for main files
        files_to_check = [
            "backend/app/main.py",
            "backend/app/core/config.py",
            "backend/app/interfaces/api/health_routes.py",
            "backend/app/interfaces/api/auth_routes.py",
            "backend/app/interfaces/api/billing_routes.py"
        ]
        
        all_valid = True
        failed_files = []
        
        for file_path in files_to_check:
            returncode, stdout, stderr = self.run_command([
                "python3", "-m", "py_compile", file_path
            ])
            if returncode != 0:
                all_valid = False
                failed_files.append(file_path)
        
        duration = time.time() - start
        
        if all_valid:
            result = TestResult(
                "Backend Syntax Check",
                "PASS",
                duration,
                f"All {len(files_to_check)} files have valid Python syntax"
            )
        else:
            result = TestResult(
                "Backend Syntax Check",
                "FAIL",
                duration,
                f"Syntax errors in: {', '.join(failed_files)}"
            )
        
        self.results.append(result)
        self.print_result(result)
        return result.status == "PASS"
    
    def test_sentry_imports(self):
        """Test 2.1: Sentry SDK imports"""
        self.print_test("Test 2.1: Sentry SDK Imports")
        start = time.time()
        
        # Check if sentry_sdk is importable
        returncode, stdout, stderr = self.run_command([
            "python3", "-c",
            "import sentry_sdk; from sentry_sdk.integrations.fastapi import FastApiIntegration; print('OK')"
        ])
        
        duration = time.time() - start
        
        if returncode == 0 and "OK" in stdout:
            result = TestResult(
                "Sentry SDK Imports",
                "PASS",
                duration,
                "sentry_sdk and FastAPI integration available"
            )
        else:
            result = TestResult(
                "Sentry SDK Imports",
                "FAIL",
                duration,
                f"Import failed: {stderr}"
            )
        
        self.results.append(result)
        self.print_result(result)
        return result.status == "PASS"
    
    def test_slowapi_imports(self):
        """Test 2.2: SlowAPI imports"""
        self.print_test("Test 2.2: SlowAPI Imports")
        start = time.time()
        
        # Check if slowapi is importable
        returncode, stdout, stderr = self.run_command([
            "python3", "-c",
            "from slowapi import Limiter; from slowapi.util import get_remote_address; print('OK')"
        ])
        
        duration = time.time() - start
        
        if returncode == 0 and "OK" in stdout:
            result = TestResult(
                "SlowAPI Imports",
                "PASS",
                duration,
                "slowapi rate limiter available"
            )
        else:
            result = TestResult(
                "SlowAPI Imports",
                "FAIL",
                duration,
                f"Import failed: {stderr}"
            )
        
        self.results.append(result)
        self.print_result(result)
        return result.status == "PASS"
    
    def test_config_validation(self):
        """Test 2.3: Config validation logic"""
        self.print_test("Test 2.3: Config Validation")
        start = time.time()
        
        # Test config validation with missing JWT_SECRET_KEY
        test_script = """
import sys
sys.path.insert(0, '/home/user/webapp/backend')
try:
    import os
    os.environ['API_KEY'] = 'test-api-key'
    os.environ['JWT_SECRET_KEY'] = 'short'  # Too short
    from app.core.config import Settings
    settings = Settings()
    settings.validate()
    print('SHOULD_HAVE_FAILED')
except ValueError as e:
    if '32 characters' in str(e):
        print('VALIDATION_WORKS')
    else:
        print(f'UNEXPECTED_ERROR: {e}')
except Exception as e:
    print(f'ERROR: {e}')
"""
        
        returncode, stdout, stderr = self.run_command([
            "python3", "-c", test_script
        ])
        
        duration = time.time() - start
        
        if "VALIDATION_WORKS" in stdout:
            result = TestResult(
                "Config Validation",
                "PASS",
                duration,
                "JWT_SECRET_KEY validation works correctly"
            )
        elif "SHOULD_HAVE_FAILED" in stdout:
            result = TestResult(
                "Config Validation",
                "FAIL",
                duration,
                "Validation did not catch short JWT_SECRET_KEY"
            )
        else:
            result = TestResult(
                "Config Validation",
                "FAIL",
                duration,
                f"Unexpected result: {stdout} {stderr}"
            )
        
        self.results.append(result)
        self.print_result(result)
        return result.status == "PASS"
    
    def test_subscription_model_limits(self):
        """Test 3.1: Subscription model plan limits"""
        self.print_test("Test 3.1: Subscription Model Plan Limits")
        start = time.time()
        
        # Test subscription model limits
        test_script = """
import sys
sys.path.insert(0, '/home/user/webapp/backend')
from app.domain.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus

# Test BASIC plan
sub = Subscription(
    id='test-id',
    user_id='user-123',
    plan=SubscriptionPlan.FREE,
    status=SubscriptionStatus.ACTIVE
)

# Upgrade to BASIC
sub.upgrade_to_basic()
print(f'BASIC_LIMIT={sub.monthly_agent_runs_limit}')
print(f'BASIC_RUNS={sub.monthly_agent_runs}')  # Should be reset to 0

# Upgrade to PRO
sub.upgrade_to_pro()
print(f'PRO_LIMIT={sub.monthly_agent_runs_limit}')
print(f'PRO_RUNS={sub.monthly_agent_runs}')  # Should be reset to 0

# Test trial
sub2 = Subscription(id='test-2', user_id='user-456')
sub2.activate_trial(days=14)
print(f'TRIAL_LIMIT={sub2.monthly_agent_runs_limit}')
print(f'TRIAL_STATUS={sub2.status.value}')
"""
        
        returncode, stdout, stderr = self.run_command([
            "python3", "-c", test_script
        ], timeout=10)
        
        duration = time.time() - start
        
        checks = {
            'BASIC_LIMIT=1000': 'BASIC plan limit is 1000',
            'BASIC_RUNS=0': 'BASIC upgrade resets counter',
            'PRO_LIMIT=5000': 'PRO plan limit is 5000',
            'PRO_RUNS=0': 'PRO upgrade resets counter',
            'TRIAL_LIMIT=50': 'Trial limit is 50',
            'TRIAL_STATUS=trialing': 'Trial status is TRIALING'  # Lowercase because of .value
        }
        
        passed_checks = []
        failed_checks = []
        
        for check, description in checks.items():
            if check in stdout:
                passed_checks.append(description)
            else:
                failed_checks.append(description)
        
        if not failed_checks:
            result = TestResult(
                "Subscription Model Plan Limits",
                "PASS",
                duration,
                f"All {len(checks)} checks passed"
            )
        else:
            result = TestResult(
                "Subscription Model Plan Limits",
                "FAIL",
                duration,
                f"Failed: {', '.join(failed_checks)}"
            )
        
        self.results.append(result)
        self.print_result(result)
        return result.status == "PASS"
    
    def test_health_routes_exist(self):
        """Test 3.2: Health routes exist"""
        self.print_test("Test 3.2: Health Routes Exist")
        start = time.time()
        
        # Check if health routes are defined
        returncode, stdout, stderr = self.run_command([
            "bash", "-c",
            "grep -E '@router\\.(get|post).*/(health|ready|live|version|sentry)' backend/app/interfaces/api/health_routes.py"
        ])
        
        duration = time.time() - start
        
        expected_routes = ['/health', '/ready', '/live', '/version', '/sentry-debug', '/sentry-test']
        found_routes = []
        
        for route in expected_routes:
            if route in stdout:
                found_routes.append(route)
        
        if len(found_routes) == len(expected_routes):
            result = TestResult(
                "Health Routes Exist",
                "PASS",
                duration,
                f"All {len(expected_routes)} health routes defined"
            )
        else:
            missing = set(expected_routes) - set(found_routes)
            result = TestResult(
                "Health Routes Exist",
                "FAIL",
                duration,
                f"Missing routes: {', '.join(missing)}"
            )
        
        self.results.append(result)
        self.print_result(result)
        return result.status == "PASS"
    
    def test_rate_limits_defined(self):
        """Test 3.3: Rate limits are defined"""
        self.print_test("Test 3.3: Rate Limits Defined")
        start = time.time()
        
        # Check auth routes
        returncode1, stdout1, stderr1 = self.run_command([
            "bash", "-c",
            "grep -E '@limiter\\.limit' backend/app/interfaces/api/auth_routes.py | wc -l"
        ])
        
        # Check billing routes
        returncode2, stdout2, stderr2 = self.run_command([
            "bash", "-c",
            "grep -E '@limiter\\.limit' backend/app/interfaces/api/billing_routes.py | wc -l"
        ])
        
        duration = time.time() - start
        
        auth_limits = int(stdout1.strip()) if stdout1.strip().isdigit() else 0
        billing_limits = int(stdout2.strip()) if stdout2.strip().isdigit() else 0
        
        # Expected: login, register in auth (2+)
        # Expected: webhook, checkout, portal, subscription, trial in billing (5+)
        
        if auth_limits >= 2 and billing_limits >= 5:
            result = TestResult(
                "Rate Limits Defined",
                "PASS",
                duration,
                f"Auth: {auth_limits} limits, Billing: {billing_limits} limits"
            )
        else:
            result = TestResult(
                "Rate Limits Defined",
                "FAIL",
                duration,
                f"Auth: {auth_limits}/2+, Billing: {billing_limits}/5+"
            )
        
        self.results.append(result)
        self.print_result(result)
        return result.status == "PASS"
    
    def test_backup_script_exists(self):
        """Test 3.4: Backup script exists and is executable"""
        self.print_test("Test 3.4: Backup Script Exists")
        start = time.time()
        
        # Check if backup script exists
        returncode, stdout, stderr = self.run_command([
            "bash", "-c",
            "test -f scripts/backup-mongodb.sh && test -x scripts/backup-mongodb.sh && echo 'EXISTS_AND_EXECUTABLE' || echo 'NOT_FOUND_OR_NOT_EXECUTABLE'"
        ])
        
        duration = time.time() - start
        
        if "EXISTS_AND_EXECUTABLE" in stdout:
            result = TestResult(
                "Backup Script Exists",
                "PASS",
                duration,
                "scripts/backup-mongodb.sh exists and is executable"
            )
        else:
            result = TestResult(
                "Backup Script Exists",
                "FAIL",
                duration,
                "Backup script missing or not executable"
            )
        
        self.results.append(result)
        self.print_result(result)
        return result.status == "PASS"
    
    def test_documentation_exists(self):
        """Test 3.5: All documentation exists"""
        self.print_test("Test 3.5: Documentation Exists")
        start = time.time()
        
        expected_docs = [
            "SENTRY_SETUP_GUIDE.md",
            "UPTIMEROBOT_SETUP_GUIDE.md",
            "FIX_IMPLEMENTATION_PROGRESS.md",
            "INTEGRATION_TEST_PLAN.md",
            "CRITICAL_SAAS_REVIEW.md"
        ]
        
        found_docs = []
        missing_docs = []
        
        for doc in expected_docs:
            returncode, stdout, stderr = self.run_command([
                "bash", "-c",
                f"test -f {doc} && echo 'EXISTS' || echo 'MISSING'"
            ])
            
            if "EXISTS" in stdout:
                found_docs.append(doc)
            else:
                missing_docs.append(doc)
        
        duration = time.time() - start
        
        if not missing_docs:
            result = TestResult(
                "Documentation Exists",
                "PASS",
                duration,
                f"All {len(expected_docs)} documentation files exist"
            )
        else:
            result = TestResult(
                "Documentation Exists",
                "FAIL",
                duration,
                f"Missing: {', '.join(missing_docs)}"
            )
        
        self.results.append(result)
        self.print_result(result)
        return result.status == "PASS"
    
    def generate_report(self):
        """Generate final test report"""
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        skipped = sum(1 for r in self.results if r.status == "SKIP")
        
        total_duration = time.time() - self.start_time
        
        # Print summary
        self.print_header("INTEGRATION TEST RESULTS - SUMMARY")
        
        print(f"Total Tests: {total_tests}")
        print(f"{GREEN}✅ Passed: {passed}{RESET}")
        print(f"{RED}❌ Failed: {failed}{RESET}")
        print(f"{YELLOW}⏭️  Skipped: {skipped}{RESET}")
        print(f"Total Duration: {total_duration:.2f}s")
        print(f"\nSuccess Rate: {(passed/total_tests*100):.1f}%")
        
        # Detailed results
        print(f"\n{BLUE}Detailed Results:{RESET}\n")
        for i, result in enumerate(self.results, 1):
            status_color = GREEN if result.status == "PASS" else RED if result.status == "FAIL" else YELLOW
            status_symbol = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "⏭️"
            print(f"{i}. {status_color}{status_symbol} {result.name} - {result.status} ({result.duration:.2f}s){RESET}")
            if result.notes:
                print(f"   └─ {result.notes}")
        
        # Overall verdict
        print(f"\n{BLUE}{'='*80}{RESET}")
        if failed == 0:
            print(f"{GREEN}🎉 ALL TESTS PASSED! Phase 1 validation successful.{RESET}")
            verdict = "PASS"
        elif passed >= total_tests * 0.9:  # 90% pass rate
            print(f"{YELLOW}⚠️  MOSTLY PASSED ({passed}/{total_tests}). Review failures before production.{RESET}")
            verdict = "MOSTLY_PASS"
        else:
            print(f"{RED}❌ TESTS FAILED ({failed}/{total_tests}). Fix issues before proceeding.{RESET}")
            verdict = "FAIL"
        print(f"{BLUE}{'='*80}{RESET}\n")
        
        return verdict, passed, failed, skipped, total_duration
    
    def run_all_tests(self):
        """Run all integration tests"""
        self.print_header("AI-MANUS PHASE 1 - INTEGRATION TEST SUITE")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Environment: Development (Local)")
        print(f"Test Plan: INTEGRATION_TEST_PLAN.md\n")
        
        # Test Suite 1: Security & Configuration
        self.print_header("TEST SUITE 1: SECURITY & CONFIGURATION")
        self.test_jwt_secret_validation()
        self.test_backend_syntax()
        self.test_config_validation()
        
        # Test Suite 2: Dependencies & Imports
        self.print_header("TEST SUITE 2: DEPENDENCIES & IMPORTS")
        self.test_sentry_imports()
        self.test_slowapi_imports()
        
        # Test Suite 3: Domain Logic
        self.print_header("TEST SUITE 3: DOMAIN LOGIC")
        self.test_subscription_model_limits()
        self.test_health_routes_exist()
        self.test_rate_limits_defined()
        self.test_backup_script_exists()
        self.test_documentation_exists()
        
        # Generate report
        verdict, passed, failed, skipped, duration = self.generate_report()
        
        # Write results to file
        self.write_results_file(verdict, passed, failed, skipped, duration)
        
        # Exit with appropriate code
        sys.exit(0 if failed == 0 else 1)
    
    def write_results_file(self, verdict: str, passed: int, failed: int, skipped: int, duration: float):
        """Write results to TEST_RESULTS.md"""
        with open("/home/user/webapp/TEST_RESULTS.md", "w") as f:
            f.write("# Integration Test Results - Phase 1\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
            f.write(f"**Environment:** Development (Local)  \n")
            f.write(f"**Test Plan:** INTEGRATION_TEST_PLAN.md  \n")
            f.write(f"**Duration:** {duration:.2f}s  \n\n")
            
            f.write("## Summary\n\n")
            f.write(f"| Metric | Value |\n")
            f.write(f"|--------|-------|\n")
            f.write(f"| Total Tests | {len(self.results)} |\n")
            f.write(f"| ✅ Passed | {passed} |\n")
            f.write(f"| ❌ Failed | {failed} |\n")
            f.write(f"| ⏭️ Skipped | {skipped} |\n")
            f.write(f"| Success Rate | {(passed/len(self.results)*100):.1f}% |\n")
            f.write(f"| **Verdict** | **{verdict}** |\n\n")
            
            f.write("## Detailed Results\n\n")
            for i, result in enumerate(self.results, 1):
                status_symbol = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "⏭️"
                f.write(f"### {i}. {status_symbol} {result.name}\n\n")
                f.write(f"- **Status:** {result.status}\n")
                f.write(f"- **Duration:** {result.duration:.2f}s\n")
                if result.notes:
                    f.write(f"- **Notes:** {result.notes}\n")
                f.write("\n")
            
            f.write("## Recommendations\n\n")
            if failed == 0:
                f.write("✅ **All tests passed!** Phase 1 is ready for deployment.\n\n")
                f.write("**Next Steps:**\n")
                f.write("1. Deploy to staging environment\n")
                f.write("2. Create Sentry account and set SENTRY_DSN\n")
                f.write("3. Create UptimeRobot account and add monitors\n")
                f.write("4. Run production smoke tests\n")
                f.write("5. Launch Private Beta\n")
            elif passed >= len(self.results) * 0.9:
                f.write("⚠️ **Most tests passed**, but some issues need attention.\n\n")
                f.write("**Action Required:**\n")
                f.write("1. Review and fix failed tests\n")
                f.write("2. Re-run integration tests\n")
                f.write("3. Verify fixes in staging\n")
            else:
                f.write("❌ **Multiple test failures detected.** Do not deploy to production.\n\n")
                f.write("**Critical Actions:**\n")
                f.write("1. Fix all failed tests immediately\n")
                f.write("2. Re-run full test suite\n")
                f.write("3. Consider code review\n")
            
            f.write("\n---\n\n")
            f.write("**Generated by:** Integration Test Suite  \n")
            f.write(f"**Timestamp:** {datetime.now().isoformat()}  \n")


if __name__ == "__main__":
    suite = IntegrationTestSuite()
    suite.run_all_tests()
