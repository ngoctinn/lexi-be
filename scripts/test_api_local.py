#!/usr/bin/env python3
"""
Local API Test Script - Test các endpoint mà không cần auth token
Dùng để test khi chạy SAM local
"""

import sys
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import argparse

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class LocalAPITester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {'Content-Type': 'application/json'}
        self.results = []

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
            else:
                return False

            success = response.status_code == expected_status
            
            if success:
                self.log(f"{name} ({method} {path}) - {response.status_code}", 'SUCCESS')
                self.results.append({'test': name, 'status': 'PASS'})
                
                # Print response for debugging
                try:
                    resp_json = response.json()
                    print(f"  Response: {json.dumps(resp_json, indent=2)[:200]}...")
                except:
                    pass
                
                return True
            else:
                error_msg = response.text[:200] if response.text else 'No response'
                self.log(f"{name} - Expected {expected_status}, got {response.status_code}", 'ERROR')
                print(f"  Response: {error_msg}")
                self.results.append({'test': name, 'status': 'FAIL', 'code': response.status_code})
                return False

        except requests.exceptions.ConnectionError:
            self.log(f"{name}: Cannot connect to {url}", 'ERROR')
            self.results.append({'test': name, 'status': 'CONNECTION_ERROR'})
            return False
        except Exception as e:
            self.log(f"{name}: {str(e)}", 'ERROR')
            self.results.append({'test': name, 'status': 'ERROR'})
            return False

    def run_all_tests(self):
        """Run all local API tests"""
        print(f"\n{Colors.BOLD}{'='*60}")
        print(f"Local API Tests - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Base URL: {self.base_url}")
        print(f"{'='*60}{Colors.RESET}\n")

        # 1. Public Endpoints
        print(f"{Colors.BOLD}[1] Testing Public Endpoints{Colors.RESET}")
        self.test_endpoint('GET', '/scenarios', 'List Scenarios', expected_status=200)

        # 2. Profile Endpoints (may fail without auth, but we test the route exists)
        print(f"\n{Colors.BOLD}[2] Testing Profile Endpoints{Colors.RESET}")
        self.test_endpoint('GET', '/profile', 'Get Profile', expected_status=401)
        self.test_endpoint('PATCH', '/profile', 'Update Profile',
                          data={'name': 'Test'}, expected_status=401)

        # 3. Vocabulary Endpoints
        print(f"\n{Colors.BOLD}[3] Testing Vocabulary Endpoints{Colors.RESET}")
        self.test_endpoint('POST', '/vocabulary/translate', 'Translate Vocabulary',
                          data={'word': 'hello', 'source_lang': 'en', 'target_lang': 'vi'},
                          expected_status=401)
        self.test_endpoint('POST', '/vocabulary/translate-sentence', 'Translate Sentence',
                          data={'sentence': 'Hello', 'source_lang': 'en', 'target_lang': 'vi'},
                          expected_status=401)

        # 4. Flashcard Endpoints
        print(f"\n{Colors.BOLD}[4] Testing Flashcard Endpoints{Colors.RESET}")
        self.test_endpoint('GET', '/flashcards', 'List Flashcards', expected_status=401)
        self.test_endpoint('GET', '/flashcards/due', 'List Due Cards', expected_status=401)
        self.test_endpoint('POST', '/flashcards', 'Create Flashcard',
                          data={'word': 'test'}, expected_status=401)

        # 5. Session Endpoints
        print(f"\n{Colors.BOLD}[5] Testing Session Endpoints{Colors.RESET}")
        self.test_endpoint('GET', '/sessions', 'List Sessions', expected_status=401)
        self.test_endpoint('POST', '/sessions', 'Create Session',
                          data={'scenario_id': 'test'}, expected_status=401)

        # 6. Admin Endpoints
        print(f"\n{Colors.BOLD}[6] Testing Admin Endpoints{Colors.RESET}")
        self.test_endpoint('GET', '/admin/users', 'List Admin Users', expected_status=401)
        self.test_endpoint('GET', '/admin/scenarios', 'List Admin Scenarios', expected_status=401)

        # 7. Onboarding Endpoints
        print(f"\n{Colors.BOLD}[7] Testing Onboarding Endpoints{Colors.RESET}")
        self.test_endpoint('POST', '/onboarding/complete', 'Complete Onboarding',
                          data={'name': 'Test'}, expected_status=401)

        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print(f"\n{Colors.BOLD}{'='*60}")
        print(f"Test Summary")
        print(f"{'='*60}{Colors.RESET}\n")

        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        errors = sum(1 for r in self.results if r['status'] in ['ERROR', 'CONNECTION_ERROR'])
        total = len(self.results)

        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
        print(f"{Colors.YELLOW}Errors: {errors}{Colors.RESET}")

        if failed > 0 or errors > 0:
            print(f"\n{Colors.BOLD}Issues:{Colors.RESET}")
            for result in self.results:
                if result['status'] != 'PASS':
                    print(f"  - {result['test']}: {result['status']}")

        print()

def main():
    parser = argparse.ArgumentParser(description='Test Lexi-BE API locally')
    parser.add_argument('--url', default='http://localhost:3000',
                       help='Base URL (default: http://localhost:3000)')

    args = parser.parse_args()

    tester = LocalAPITester(args.url)
    tester.run_all_tests()

if __name__ == '__main__':
    main()
