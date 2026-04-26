import os
import sys
import logging
import pytest
import json
import jwt
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Load test environment variables
env_path = Path(__file__).parent.parent / ".env.test"
load_dotenv(env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Environment Variables
# ============================================================================

BASE_URL = os.getenv("BASE_URL", "https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod")
WS_URL = os.getenv("WS_URL", "wss://no8fa2u3qg.execute-api.ap-southeast-1.amazonaws.com/Prod")
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "test@example.com")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "placeholder_password")
TEST_ADMIN_EMAIL = os.getenv("TEST_ADMIN_EMAIL", "admin@example.com")
TEST_ADMIN_PASSWORD = os.getenv("TEST_ADMIN_PASSWORD", "placeholder_password")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "ap-southeast-1_VhFl3NxNy")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "4krhiauplon0iei1f5r4cgpq7i")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")


# ============================================================================
# Token Management
# ============================================================================

class TokenManager:
    """Manage JWT tokens for testing with caching and expiry tracking."""

    # Mock secret for test token generation
    SECRET = "test-secret-key-do-not-use-in-production"

    # Token cache: {role: (token, expiry_time)}
    _token_cache = {}

    # Refresh threshold: refresh token if expiry is within this many seconds
    REFRESH_THRESHOLD = 300  # 5 minutes

    @staticmethod
    def generate_test_token(
        user_id: str = "test-user-123",
        email: str = TEST_USER_EMAIL,
        role: str = "user",
        ttl_hours: int = 1,
    ) -> str:
        """
        Generate a mock JWT token for testing.

        Args:
            user_id: User ID to include in token
            email: Email to include in token
            role: User role (user or admin)
            ttl_hours: Token time-to-live in hours

        Returns:
            JWT token string
        """
        expiry = datetime.utcnow() + timedelta(hours=ttl_hours)
        payload = {
            "sub": user_id,
            "email": email,
            "cognito:username": email,
            "cognito:groups": [role],
            "iat": datetime.utcnow(),
            "exp": expiry,
        }
        token = jwt.encode(payload, TokenManager.SECRET, algorithm="HS256")
        logger.debug(f"Generated test token for {email} (role={role}, expires in {ttl_hours}h)")
        return token

    @staticmethod
    def get_user_token() -> str:
        """
        Get user token with caching and refresh logic.

        Returns:
            Valid JWT token for test user

        Raises:
            RuntimeError: Token generation failed
        """
        # Try to get real token from Cognito first
        try:
            import subprocess
            result = subprocess.run([
                "aws", "cognito-idp", "admin-initiate-auth",
                "--user-pool-id", COGNITO_USER_POOL_ID,
                "--client-id", COGNITO_CLIENT_ID,
                "--auth-flow", "ADMIN_NO_SRP_AUTH",
                "--auth-parameters", f"USERNAME={TEST_USER_EMAIL},PASSWORD={TEST_USER_PASSWORD}",
                "--region", AWS_REGION
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                import json
                auth_result = json.loads(result.stdout)
                # Use IdToken instead of AccessToken - API Gateway Cognito Authorizer validates IdToken
                token = auth_result["AuthenticationResult"]["IdToken"]
                logger.info(f"Got real JWT IdToken from Cognito for {TEST_USER_EMAIL}")
                return token
        except Exception as e:
            logger.warning(f"Failed to get real token from Cognito: {e}, falling back to mock token")
        
        # Fallback to mock token
        return TokenManager._get_cached_token("user", TEST_USER_EMAIL, "test-user-123")

    @staticmethod
    def get_admin_token() -> str:
        """
        Get admin token with caching and refresh logic.

        Returns:
            Valid JWT token for admin user

        Raises:
            RuntimeError: Token generation failed
        """
        return TokenManager._get_cached_token("admin", TEST_ADMIN_EMAIL, "admin-user-123")

    @staticmethod
    def _get_cached_token(role: str, email: str, user_id: str) -> str:
        """
        Get token from cache or generate new one if expired.

        Args:
            role: User role (user or admin)
            email: User email
            user_id: User ID

        Returns:
            Valid JWT token

        Raises:
            RuntimeError: Token generation failed
        """
        try:
            # Check if token exists in cache
            if role in TokenManager._token_cache:
                token, expiry_time = TokenManager._token_cache[role]

                # Check if token is still valid (with refresh threshold)
                time_until_expiry = (expiry_time - datetime.utcnow()).total_seconds()

                if time_until_expiry > TokenManager.REFRESH_THRESHOLD:
                    logger.debug(f"Using cached {role} token (expires in {time_until_expiry:.0f}s)")
                    return token

                logger.debug(f"Cached {role} token expired or close to expiry, refreshing...")

            # Generate new token
            token = TokenManager.generate_test_token(user_id, email, role)
            expiry_time = datetime.utcnow() + timedelta(hours=1)

            # Cache token
            TokenManager._token_cache[role] = (token, expiry_time)
            logger.info(f"Generated and cached {role} token")

            return token

        except Exception as e:
            logger.error(f"Failed to get {role} token: {e}")
            raise RuntimeError(f"Token generation failed for role '{role}': {e}") from e

    @staticmethod
    def refresh_token_if_needed(token: str, role: str = "user") -> str:
        """
        Refresh token if close to expiry.

        Args:
            token: Current JWT token
            role: User role (user or admin)

        Returns:
            Valid JWT token (refreshed or original)
        """
        try:
            # Decode token to check expiry
            decoded = jwt.decode(token, TokenManager.SECRET, algorithms=["HS256"])
            exp_timestamp = decoded.get("exp")

            if not exp_timestamp:
                logger.warning("Token missing 'exp' claim, generating new token")
                return TokenManager.get_user_token() if role == "user" else TokenManager.get_admin_token()

            expiry_time = datetime.utcfromtimestamp(exp_timestamp)
            time_until_expiry = (expiry_time - datetime.utcnow()).total_seconds()

            if time_until_expiry > TokenManager.REFRESH_THRESHOLD:
                logger.debug(f"Token still valid (expires in {time_until_expiry:.0f}s)")
                return token

            logger.info(f"Token close to expiry ({time_until_expiry:.0f}s), refreshing...")
            return TokenManager.get_user_token() if role == "user" else TokenManager.get_admin_token()

        except jwt.DecodeError as e:
            logger.error(f"Failed to decode token: {e}")
            raise RuntimeError(f"Invalid token: {e}") from e

    @staticmethod
    def generate_expired_token() -> str:
        """Generate an expired JWT token for testing."""
        payload = {
            "sub": "expired-user",
            "email": "expired@example.com",
            "iat": datetime.utcnow() - timedelta(hours=2),
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
        }
        token = jwt.encode(payload, TokenManager.SECRET, algorithm="HS256")
        logger.debug("Generated expired test token")
        return token

    @staticmethod
    def clear_cache() -> None:
        """Clear token cache (useful for testing)."""
        TokenManager._token_cache.clear()
        logger.debug("Token cache cleared")


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def api_client():
    """
    Fixture: Authenticated API client for regular users.
    Scope: function (new client per test)
    """
    from tests.test_api_client import APIClient

    token = TokenManager.get_user_token()
    client = APIClient(base_url=BASE_URL, token=token)
    logger.info(f"Created authenticated API client for {TEST_USER_EMAIL}")
    return client


@pytest.fixture(scope="function")
def admin_client():
    """
    Fixture: Authenticated API client for admin users.
    Scope: function (new client per test)
    """
    from tests.test_api_client import APIClient

    token = TokenManager.get_admin_token()
    client = APIClient(base_url=BASE_URL, token=token)
    logger.info(f"Created admin API client for {TEST_ADMIN_EMAIL}")
    return client


@pytest.fixture(scope="function")
def public_client():
    """
    Fixture: Unauthenticated API client for public endpoints.
    Scope: function (new client per test)
    """
    from tests.test_api_client import APIClient

    client = APIClient(base_url=BASE_URL, token=None)
    logger.info("Created public API client (no authentication)")
    return client


@pytest.fixture
async def ws_client():
    """
    Fixture: WebSocket client with connection.
    Automatically connects and closes.
    Scope: function (new connection per test)
    """
    from tests.test_websocket_client import WebSocketClient

    token = TokenManager.get_user_token()
    client = WebSocketClient(timeout=5)

    try:
        await client.connect(WS_URL, token)
        logger.info("WebSocket client connected")
        yield client
    except Exception as e:
        logger.error(f"Failed to connect WebSocket: {e}")
        raise RuntimeError(f"WebSocket connection failed: {e}") from e
    finally:
        await client.close()
        logger.info("WebSocket client closed")


@pytest.fixture
def test_scenario(api_client):
    """
    Fixture: Create a test scenario via API.
    Cleans up after test.
    Scope: function (new scenario per test)
    """
    from tests.fixtures.test_data import TestDataFactory

    try:
        # Create scenario
        scenario_data = TestDataFactory.valid_scenario_data()
        response = api_client.post("/admin/scenarios", scenario_data)
        assert response.status_code == 201, f"Failed to create test scenario: {response.text}"

        scenario = response.json()["data"]
        logger.info(f"Created test scenario: {scenario['scenario_id']}")

        yield scenario

    except Exception as e:
        logger.error(f"Failed to create test scenario: {e}")
        raise RuntimeError(f"Test scenario creation failed: {e}") from e
    finally:
        # Cleanup: Delete scenario (if delete endpoint exists)
        logger.info(f"Test scenario cleanup: {scenario.get('scenario_id', 'unknown')}")


@pytest.fixture
def test_session(api_client, test_scenario):
    """
    Fixture: Create a test session via API.
    Cleans up after test.
    Scope: function (new session per test)
    """
    from tests.fixtures.test_data import TestDataFactory

    try:
        # Create session
        session_data = TestDataFactory.valid_session_data(scenario_id=test_scenario["scenario_id"])
        response = api_client.post("/sessions", session_data)
        assert response.status_code == 201, f"Failed to create test session: {response.text}"

        session = response.json()["data"]
        logger.info(f"Created test session: {session['session_id']}")

        yield session

    except Exception as e:
        logger.error(f"Failed to create test session: {e}")
        raise RuntimeError(f"Test session creation failed: {e}") from e
    finally:
        # Cleanup: Delete session (if delete endpoint exists)
        logger.info(f"Test session cleanup: {session.get('session_id', 'unknown')}")


# ============================================================================
# Pytest Hooks
# ============================================================================

def pytest_configure(config):
    """
    Hook: Called after command line options have been parsed.
    Used for test session setup and logging configuration.
    """
    logger.info("=" * 80)
    logger.info("API Validation Test Suite - Starting")
    logger.info("=" * 80)
    logger.info(f"Base URL: {BASE_URL}")
    logger.info(f"WebSocket URL: {WS_URL}")
    logger.info(f"AWS Region: {AWS_REGION}")
    logger.info("=" * 80)

    # Clear token cache at start of test session
    TokenManager.clear_cache()
    logger.info("Token cache cleared at session start")


def pytest_collection_modifyitems(config, items):
    """
    Hook: Called after test collection.
    Used to add markers to tests based on naming conventions.
    """
    for item in items:
        # Add asyncio marker to async tests
        if "async" in item.nodeid:
            item.add_marker(pytest.mark.asyncio)


def pytest_runtest_logreport(report):
    """
    Hook: Called after each test phase (setup, call, teardown).
    Used for test reporting and logging.
    """
    if report.when == "call":
        if report.outcome == "passed":
            logger.info(f"✓ {report.nodeid}")
        elif report.outcome == "failed":
            logger.error(f"✗ {report.nodeid}")
        elif report.outcome == "skipped":
            logger.warning(f"⊘ {report.nodeid}")


def pytest_sessionfinish(session, exitstatus):
    """
    Hook: Called after the whole test run finished.
    Used for final cleanup and reporting.
    """
    print("=" * 80)
    print("API Validation Test Suite - Finished")
    print("=" * 80)
