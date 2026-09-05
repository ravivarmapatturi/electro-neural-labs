"""The real, verified seed parts database this backend's generation logic
picks from -- deliberately tiny and honestly sourced, not a production
parts catalog.

Every entry mirrors a real component definition in ato_lib/own_parts/*.ato
that has been confirmed, by a real `ato build`, to compile correctly with
zero live network calls and zero atopile account. Resistor and capacitor
values were reused from a real prior board's own actual BOM output (they
were genuinely picked by real atopile part-search before that search
infrastructure went dead/account-gated).

The diode used for reverse_polarity_protection (SS34_C8678) is NOT one
of our own own_parts -- it's a real part already vendored in
ato_lib/generics/elec/src, whose footprint is independently confirmed
real because its actual .kicad_mod file exists in
ato_lib/generics/elec/footprints/ and a real `ato build` resolved it
correctly. This replaced an earlier hand-authored small-signal diode
(own_parts/diodes.ato, since removed) whose footprint string was a
real package name but not confirmed against an actual footprint file
the way every other part here is -- resolved by switching to an
already-footprint-verified real part instead of trying to hand-verify
a new one, and a Schottky is also the more correct real-world choice
for power-rail protection than a small-signal diode (lower forward-
voltage drop, real amp-scale current handling).

Honest limits, not glossed over:
  - Coverage is tiny (4 resistor values, 3 capacitor values, 1 button,
    1 diode) -- only what happened to already exist or get looked up
    during verification, not a real production parts catalog.
  - A real v1 needs this sourced properly (LCSC's own API, Octopart, or
    similar) with live stock/price checks -- this static list has no way
    to know if a part goes out of stock or gets discontinued.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Resistor:
    ato_name: str  # the real component name in ato_lib/own_parts/resistors.ato
    ohms: float
    package: str
    mpn: str
    lcsc_id: str


@dataclass(frozen=True)
class Capacitor:
    ato_name: str  # the real component name in ato_lib/own_parts/capacitors.ato
    farads: float
    package: str
    mpn: str
    lcsc_id: str


RESISTORS: list[Resistor] = [
    Resistor("FixedResistor100R_0402", 100, "0402", "0402WGF1000TCE", "C25076"),
    Resistor("FixedResistor2k_0402", 2_000, "0402", "0402WGF2001TCE", "C4109"),
    Resistor("FixedResistor5k1_0402", 5_100, "0402", "0402WGF5101TCE", "C25905"),
    Resistor("FixedResistor10k_0402", 10_000, "0402", "0402WGF1002TCE", "C25744"),
]

CAPACITORS: list[Capacitor] = [
    Capacitor("FixedCapacitor100nF_0402", 100e-9, "0402", "CL05B104KB54PNC", "C307331"),
    Capacitor("FixedCapacitor1uF_0402", 1e-6, "0402", "CL05A105KP5NNNC", "C14445"),
    Capacitor("FixedCapacitor22uF_0805", 22e-6, "0805", "CL21A226MAQNNNE", "C45783"),
]

# Real LED specs (from ato_lib/generics/leds.ato's _KT_0603R -- a real,
# already-existing part, not authored by this generation logic).
LED_KT_0603R_VF = 2.0  # volts
LED_KT_0603R_IMAX = 0.020  # amps (20mA)

BUTTON_SKRPACE010_ATO_NAME = "TactileButtonSKRPACE010"  # ato_lib/own_parts/buttons.ato
DIODE_SS34_ATO_NAME = "SS34_C8678"  # ato_lib/generics/elec/src/SS34_C8678.ato -- a real,
# already-vendored, footprint-verified Schottky diode (see this file's
# own module docstring for why this replaced a hand-authored diode).


def best_resistor_for_led_current(
    v_in: float, v_f: float = LED_KT_0603R_VF, i_max: float = LED_KT_0603R_IMAX
) -> Resistor:
    """Pick the seed resistor giving the highest *safe* current for an LED
    at v_in, real Ohm's-law reasoning (I = (v_in - v_f) / R), rejecting any
    resistor whose resulting current would exceed i_max -- the same
    real reasoning manually verified for the LED indicator target."""
    safe = [r for r in RESISTORS if (v_in - v_f) / r.ohms <= i_max]
    if not safe:
        raise ValueError(
            f"No seed resistor keeps current under {i_max * 1000:.1f}mA at v_in={v_in}V, v_f={v_f}V"
        )
    # Brightest safe choice = lowest resistance among the safe ones.
    return min(safe, key=lambda r: r.ohms)


def best_divider_pair(v_in: float, v_out_target: float) -> tuple[Resistor, Resistor]:
    """Combinatorial best-fit search over every (top, bottom) pair of seed
    resistors for the ratio closest to v_out_target / v_in -- the same
    real reasoning manually verified for the voltage-divider target."""
    target_ratio = v_out_target / v_in
    best: tuple[Resistor, Resistor] | None = None
    best_diff = float("inf")
    for top in RESISTORS:
        for bottom in RESISTORS:
            ratio = bottom.ohms / (top.ohms + bottom.ohms)
            diff = abs(ratio - target_ratio)
            if diff < best_diff:
                best_diff = diff
                best = (top, bottom)
    assert best is not None
    return best
