import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from infrastructure.handlers.scenarios_handler import handler


def test_scenarios_handler_returns_active_scenarios():
    response = handler({}, None)
    payload = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert payload["success"] is True
    assert payload["scenarios"]
