#!/usr/bin/env python3
"""
API Test Script - Test toàn bộ các endpoint của Lexi-BE
Sử dụng: python scripts/test_api.py <api_url> <auth_token>
"""

import sys
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import argparse

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class APITester:
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        self.results = []
        self.test_data = {}

    def log(self, message: str, level: str = 'INFO'):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if level == 'SUCCESS':
            print(f"{Colors.GREEN}[{timestamp}] ✓ {message}{Colors.RESET}")
        elif level == 'ERROR':
            print(f"{Colors.RED}[{timestamp}] ✗ {message}{Colors.RESET}")
        elif level == 'WARNING':
            print(f"{Colors.YELLOW}[{timestamp}] ⚠ {message}{Colors.RESET}")
        elif level == 'INFO':
            print(f"{Colors.BLUE}[{timestamp}] ℹ {message}{Colors.RESET}")
        else:
            print(f"[{timestamp}] {message}")

    def test_endpoint(self, method: str, path: str, name: str, 
                     data: Optional[Dict] = None, 
                     expected_status: int = 200,
                     headers: Optional[Dict] = None) -> bool:
        """Test a single endpoint"""
        url = f"{self.base_url}{path}"
        test_headers = self.headers.copy()
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)
            else:
                self.log(f"{name}: Unknown method {method}", 'ERROR')
                return False

            success = response.status_code == expected_status
            status_text = f"{response.status_code}"
            
            if success:
                self.log(f"{name} ({method} {path}) - {status_text}", 'SUCCESS')
                self.results.append({'test': name, 'status': 'PASS', 'code': response.status_code})
                return True
            else:
                error_msg = response.text[:200] if response.text else 'No response body'
                self.log(f"{name} ({method} {path}) - Expected {expected_status}, got {status_text}. Error: {error_msg}", 'ERROR')
                self.results.append({'test': name, 'status': 'FAIL', 'code': response.status_code, 'error': error_msg})
                return False

        except requests.exceptions.Timeout:
            self.log(f"{name}: Request timeout", 'ERROR')
            self.results.append({'test': name, 'status': 'TIMEOUT'})
            return False
        except requests.exceptions.ConnectionError:
            self.log(f"{name}: Connection error", 'ERROR')
            self.results.append({'test': name, 'status': 'CONNECTION_ERROR'})
            return False
        except Exception as e:
            self.log(f"{name}: {str(e)}", 'ERROR')
            self.results.append({'test': name, 'status': 'ERROR', 'error': str(e)})
            return False

    def test_public_endpoint(self, method: str, path: str, name: str,
                            data: Optional[Dict] = None,
                            expected_status: int = 200) -> bool:
        """Test endpoint without authentication"""
        url = f"{self.base_url}{path}"
        headers = {'Content-Type': 'application/json'}

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                return False

            success = response.status_code == expected_status
            if success:
                self.log(f"{name} ({method} {path}) - {response.status_code}", 'SUCCESS')
                self.results.append({'test': name, 'status': 'PASS', 'code': response.status_code})
                return True
            else:
                self.log(f"{name} ({method} {path}) - Expected {expected_status}, got {response.status_code}", 'ERROR')
                self.results.append({'test': name, 'status': 'FAIL', 'code': response.status_code})
                return False

        except Exception as e:
            self.log(f"{name}: {str(e)}", 'ERROR')
            self.results.append({'test': name, 'status': 'ERROR'})
            return False

    def run_all_tests(self):
        """Run all API tests"""
        print(f"\n{Colors.BOLD}{'='*60}")
        print(f"Starting API Tests - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}{Colors.RESET}\n")

        # 1. Public Endpoints (No Auth)
        print(f"{Colors.BOLD}[1] Testing Public Endpoints{Colors.RESET}")
        self.test_public_endpoint('GET', '/scenarios', 'List Scenarios')

        # 2. Profile Endpoints
        print(f"\n{Colors.BOLD}[2] Testing Profile Endpoints{Colors.RESET}")
        self.test_endpoint('GET', '/profile', 'Get Profile')
        self.test_endpoint('PATCH', '/profile', 'Update Profile', 
                          data={'name': 'Test User', 'level': 'BEGINNER'})

        # 3. Vocabulary Endpoints
        print(f"\n{Colors.BOLD}[3] Testing Vocabulary Endpoints{Colors.RESET}")
        self.test_endpoint('POST', '/vocabulary/translate', 'Translate Vocabulary',
                          data={'word': 'hello', 'source_lang': 'en', 'target_lang': 'vi'})
        self.test_endpoint('POST', '/vocabulary/translate-sentence', 'Translate Sentence',
                          data={'sentence': 'Hello world', 'source_lang': 'en', 'target_lang': 'vi'})

        # 4. Flashcard Endpoints
        print(f"\n{Colors.BOLD}[4] Testing Flashcard Endpoints{Colors.RESET}")
        self.test_endpoint('POST', '/flashcards', 'Create Flashcard',
                          data={'word': 'test', 'definition': 'a procedure', 'example': 'This is a test'})
        self.test_endpoint('GET', '/flashcards', 'List Flashcards')
        self.test_endpoint('GET', '/flashcards/due', 'List Due Cards')
        # Note: These require valid flashcard_id
        self.test_endpoint('GET', '/flashcards/test-id', 'Get Flashcard', expected_status=404)
        self.test_endpoint('POST', '/flashcards/test-id/review', 'Review Flashcard',
                          data={'quality': 4}, expected_status=404)

        # 5. Session Endpoints
        print(f"\n{Colors.BOLD}[5] Testing Session Endpoints{Colors.RESET}")
        self.test_endpoint('GET', '/sessions', 'List Sessions')
        self.test_endpoint('POST', '/sessions', 'Create Session',
                          data={
                              'scenario_id': 'test-scenario',
                              'ai_gender': 'female',
                              'level': 'BEGINNER',
                              'prompt_snapshot': 'Test prompt'
                          })
        # Note: These require valid session_id
        self.test_endpoint('GET', '/sessions/test-id', 'Get Session', expected_status=404)
        self.test_endpoint('POST', '/sessions/test-id/turns', 'Submit Turn',
                          data={'text': 'Hello'}, expected_status=404)
        self.test_endpoint('POST', '/sessions/test-id/complete', 'Complete Session', expected_status=404)

        # 6. Admin Endpoints
        print(f"\n{Colors.BOLD}[6] Testing Admin Endpoints{Colors.RESET}")
        self.test_endpoint('GET', '/admin/users', 'List Admin Users')
        self.test_endpoint('GET', '/admin/scenarios', 'List Admin Scenarios')
        self.test_endpoint('POST', '/admin/scenarios', 'Create Admin Scenario',
                          data={
                              'title': 'Test Scenario',
                              'description': 'Test',
                              'learner_role': 'customer',
                              'ai_role': 'waiter'
                          })
        # Note: These require valid IDs
        self.test_endpoint('PATCH', '/admin/users/test-id', 'Update Admin User',
                          data={'status': 'ACTIVE'}, expected_status=404)
        self.test_endpoint('PATCH', '/admin/scenarios/test-id', 'Update Admin Scenario',
                          data={'title': 'Updated'}, expected_status=404)

        # 7. Onboarding Endpoints
        print(f"\n{Colors.BOLD}[7] Testing Onboarding Endpoints{Colors.RESET}")
        self.test_endpoint('POST', '/onboarding/complete', 'Complete Onboarding',
                          data={'name': 'Test', 'level': 'BEGINNER', 'goals': []})

        # Print Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print(f"\n{Colors.BOLD}{'='*60}")
        print(f"Test Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}{Colors.RESET}\n")

        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        errors = sum(1 for r in self.results if r['status'] in ['ERROR', 'TIMEOUT', 'CONNECTION_ERROR'])
        total = len(self.results)

        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
        print(f"{Colors.YELLOW}Errors: {errors}{Colors.RESET}")

        if failed > 0 or errors > 0:
            print(f"\n{Colors.BOLD}Failed/Error Tests:{Colors.RESET}")
            for result in self.results:
                if result['status'] != 'PASS':
                    print(f"  - {result['test']}: {result['status']}")
                    if 'error' in result:
                        print(f"    Error: {result['error']}")

        print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}\n")

        return passed, failed, errors

def main():
    parser = argparse.ArgumentParser(description='Test Lexi-BE API endpoints')
    parser.add_argument('api_url', help='Base URL of the API (e.g., https://xxx.execute-api.region.amazonaws.com/Prod)')
    parser.add_argument('auth_token', help='JWT authentication token')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if not args.api_url.startswith('http'):
        print(f"{Colors.RED}Error: API URL must start with http:// or https://{Colors.RESET}")
        sys.exit(1)

    tester = APITester(args.api_url, args.auth_token)
    tester.run_all_tests()

    # Exit with error code if any tests failed
    passed, failed, errors = tester.print_summary()
    if failed > 0 or errors > 0:
        sys.exit(1)

if __name__ == '__main__':
    main()
