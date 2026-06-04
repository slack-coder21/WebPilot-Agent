from pydantic import ValidationError
import pytest

from webpilot.models import BrowserAction


def test_browser_action_accepts_known_action() -> None:
    action = BrowserAction(action="goto", url="https://arxiv.org")
    assert action.action == "goto"


def test_browser_action_rejects_unknown_action() -> None:
    with pytest.raises(ValidationError):
        BrowserAction(action="run_javascript")

