"""Real, re-runnable tests for the generate-then-build pipeline -- these
run the exact same 4 targets that were manually verified against a real
`ato build` during this feature's research phase, now as automated tests
instead of one-off manual runs. Requires the real `ato` CLI installed and
on PATH (skips with a clear reason if it isn't, rather than failing for
an unrelated reason)."""

import shutil

import pytest

import codegen
from builder import build_circuit
from parts_db import best_divider_pair, best_resistor_for_led_current

pytestmark = pytest.mark.skipif(
    shutil.which("ato") is None,
    reason="the atopile 'ato' CLI is not installed -- see README for setup",
)


def test_led_indicator_picks_safe_resistor_and_builds():
    source = codegen.led_indicator(v_supply=5.0)
    result = build_circuit(source)
    assert result.success, result.stdout + result.stderr
    assert result.bom_csv is not None
    # The real, verified-safe choice: 2k, not 100R (which would exceed
    # the LED's real 20mA max at 5V).
    assert "0402WGF2001TCE" in result.bom_csv
    assert "0402WGF1000TCE" not in result.bom_csv


def test_led_indicator_rejects_unreachable_safe_current():
    # Even the largest seed resistor (10k) gives (12V - 2V) / 10k = 1mA,
    # which exceeds a 0.1mA cap -- no seed resistor can satisfy this, so
    # this should raise before ever attempting a build, not silently
    # pick an unsafe part.
    with pytest.raises(ValueError):
        best_resistor_for_led_current(v_in=12.0, i_max=0.0001)


def test_voltage_divider_best_fit_and_builds():
    # Same real target manually verified: 12V -> ~1/4 (3V), best real
    # fit from the seed set is top=5.1k/bottom=2k (ratio 0.2817).
    top, bottom = best_divider_pair(v_in=12.0, v_out_target=3.0)
    assert top.ohms == 5_100
    assert bottom.ohms == 2_000

    source = codegen.voltage_divider(v_in=12.0, v_out_target=3.0)
    result = build_circuit(source)
    assert result.success, result.stdout + result.stderr
    assert "0402WGF5101TCE" in result.bom_csv
    assert "0402WGF2001TCE" in result.bom_csv


def test_pullup_button_builds():
    source = codegen.pullup_button(v_supply=3.3)
    result = build_circuit(source)
    assert result.success, result.stdout + result.stderr
    assert "SKRPACE010" in result.bom_csv


def test_reverse_polarity_protection_builds():
    source = codegen.reverse_polarity_protection(v_supply=5.0)
    result = build_circuit(source)
    assert result.success, result.stdout + result.stderr
    assert "1N4148SOD-123" in result.bom_csv
    assert "CL05B104KB54PNC" in result.bom_csv


def test_generated_source_has_no_dead_search_dependency():
    """Every pattern must generate source that builds with zero live
    network calls / zero atopile account -- the whole point of routing
    everything through parts_db.py's pinned seed parts instead of
    atopile's tolerance-constrained, search-triggering built-in types."""
    for source in (
        codegen.led_indicator(5.0),
        codegen.voltage_divider(12.0, 3.0),
        codegen.pullup_button(3.3),
        codegen.reverse_polarity_protection(5.0),
    ):
        assert "resistors.ato\" import Resistor" not in source
        assert "capacitors.ato\" import Capacitor" not in source
