"""Real tests for the HTTP layer itself -- error handling, validation --
as opposed to test_generation.py's tests of the underlying generate/build
logic directly."""

import shutil

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_generate_voltage_divider_missing_v_out_target_is_422():
    r = client.post("/generate", json={"pattern": "voltage_divider", "v_supply": 12.0})
    assert r.status_code == 422
    assert "v_out_target" in r.json()["detail"]


@pytest.mark.skipif(
    shutil.which("ato") is None,
    reason="the atopile 'ato' CLI is not installed -- see README for setup",
)
def test_generate_led_indicator_unreachable_current_is_a_clean_422_not_a_500():
    # Real bug caught and fixed during manual UI testing: an unreachable
    # safe-current request used to bubble up as an unhandled 500 with no
    # useful message. Must now be a clean 422 with the real reason.
    r = client.post("/generate", json={"pattern": "led_indicator", "v_supply": 300.0})
    assert r.status_code == 422
    assert "No seed resistor keeps current under" in r.json()["detail"]
