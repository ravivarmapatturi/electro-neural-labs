"""Generates real, buildable `.ato` source for a small set of circuit
patterns, using only parts from parts_db.py -- the same real reasoning
manually verified end-to-end (real `ato build`, real pass/fail) during
this feature's research phase, now turned into real, re-runnable code
instead of one-off manual tests.

Each function returns the full text of a `circuit.ato` file. Every
generated file imports from ato_lib/generics and ato_lib/own_parts,
which builder.py vendors into the actual build directory alongside it
(atopile's own build tool requires all imported source to live inside
the project directory it's building -- a real constraint discovered
during verification, not a style choice).
"""

from parts_db import (
    BUTTON_SKRPACE010_ATO_NAME,
    DIODE_1N4148_ATO_NAME,
    best_divider_pair,
    best_resistor_for_led_current,
)


def led_indicator(v_supply: float) -> str:
    """A red LED status indicator on a v_supply rail, current-limited to
    stay under the LED's real rated maximum."""
    r = best_resistor_for_led_current(v_supply)
    return f'''# Generated: red LED status indicator on a {v_supply}V rail.
# Resistor chosen: {r.ohms:g} ohm ({r.ato_name}) -- the brightest available
# seed value that still keeps current under the LED's real 20mA max.

from "ato_lib/generics/interfaces.ato" import Power
from "ato_lib/generics/leds.ato" import _KT_0603R
from "ato_lib/own_parts/resistors.ato" import {r.ato_name}

module Circuit:
    power = new Power
    led = new _KT_0603R
    r_limit = new {r.ato_name}

    power.vcc ~ led.anode
    led.cathode ~ r_limit.p1
    r_limit.p2 ~ power.gnd

    power.voltage = {v_supply}V +/- 5%
'''


def voltage_divider(v_in: float, v_out_target: float) -> str:
    """A resistive voltage divider producing roughly v_out_target from
    v_in, using the best-fitting pair of seed resistor values."""
    top, bottom = best_divider_pair(v_in, v_out_target)
    actual_ratio = bottom.ohms / (top.ohms + bottom.ohms)
    actual_vout = v_in * actual_ratio
    return f'''# Generated: voltage divider from {v_in}V targeting ~{v_out_target}V.
# Best-fit pair from the seed set: top={top.ohms:g} ohm ({top.ato_name}),
# bottom={bottom.ohms:g} ohm ({bottom.ato_name}) -> actual ratio
# {actual_ratio:.4f}, actual Vout ~= {actual_vout:.3f}V.

from "ato_lib/generics/interfaces.ato" import Power
from "ato_lib/own_parts/resistors.ato" import {top.ato_name}, {bottom.ato_name}

module Circuit:
    power = new Power
    r_top = new {top.ato_name}
    r_bottom = new {bottom.ato_name}

    power.vcc ~ r_top.p1
    r_top.p2 ~ r_bottom.p1
    r_bottom.p2 ~ power.gnd

    power.voltage = {v_in}V +/- 5%
'''


def pullup_button(v_supply: float) -> str:
    """A momentary push button with a pull-up resistor -- output reads
    low when pressed."""
    return f'''# Generated: momentary push button with pull-up on a {v_supply}V rail,
# output reads low when pressed. 10k is the standard safe pull-up value,
# also one of the available seed resistor values.

from "ato_lib/generics/interfaces.ato" import Power
from "ato_lib/own_parts/resistors.ato" import FixedResistor10k_0402
from "ato_lib/own_parts/buttons.ato" import {BUTTON_SKRPACE010_ATO_NAME}

module Circuit:
    power = new Power
    pullup = new FixedResistor10k_0402
    btn = new {BUTTON_SKRPACE010_ATO_NAME}
    signal out

    power.vcc ~ pullup.p1
    pullup.p2 ~ btn.in
    btn.out ~ power.gnd
    out ~ pullup.p2

    power.voltage = {v_supply}V +/- 5%
'''


def reverse_polarity_protection(v_supply: float) -> str:
    """Series reverse-polarity protection using a small-signal diode,
    plus a decoupling capacitor on the protected side."""
    return f'''# Generated: series reverse-polarity protection on a {v_supply}V input,
# plus a decoupling capacitor on the protected side. Current only flows
# anode -> cathode in the correct-polarity direction, so a reversed input
# can't forward-bias the diode and no current reaches the protected rail.

from "ato_lib/generics/interfaces.ato" import Power
from "ato_lib/own_parts/diodes.ato" import {DIODE_1N4148_ATO_NAME}
from "ato_lib/own_parts/capacitors.ato" import FixedCapacitor100nF_0402

module Circuit:
    power_in = new Power
    power_protected = new Power
    protect = new {DIODE_1N4148_ATO_NAME}
    decouple = new FixedCapacitor100nF_0402

    power_in.vcc ~ protect.A
    protect.K ~ power_protected.vcc
    power_in.gnd ~ power_protected.gnd

    power_protected.vcc ~ decouple.p1
    decouple.p2 ~ power_protected.gnd

    power_in.voltage = {v_supply}V +/- 5%
'''
