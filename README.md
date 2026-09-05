# Electro Neural Labs

AI for PCB design, EDA, and CAD.

Starting pipeline: **natural-language description → netlist → schematic → layout** — describe a circuit in plain language, get a real, manufacturable board out the other end.

## Status

Early build. A real (if narrow) first slice of the generation pipeline now exists and is covered by real, passing tests: given one of a small set of circuit patterns (LED indicator, voltage divider, pull-up button, reverse-polarity protection), the backend generates real `.ato` source and validates it against a real `ato build` — no heuristics, no simulated results. This is genuinely limited in scope (see "What actually works" below) — it is not yet a general natural-language-to-netlist system.

## Architecture findings (real, verified — not assumed)

[atopile](https://github.com/atopile/atopile) — an existing, open-source, MIT-licensed declarative PCB compiler — turns a structured `.ato` description into a real netlist/BOM (confirmed by actually running it, repeatedly, against real generated circuits — see `backend/tests/test_generation.py`). This means the genuinely new work for this product is mostly **stage 1: generating valid `.ato` source from a natural-language description** — verified real, not assumed.

Two real caveats worth knowing before building further on this:

1. **Automatic part search is not currently free-and-open.** The public `atopile` PyPI release (0.2.69) has a dead live part-search endpoint (`components.atopileapi.com` — confirmed `NXDOMAIN`, not a local network issue). The newer version that matches atopile's own current documented syntax (0.15.8, bundled with the VS Code extension) is officially in "maintenance mode" — the vendor's current product is a hosted app (`app.atopile.io`, 0.16+) — and its automatic part-picking requires signing in to an atopile account. **Workaround used here**: route every generated circuit through a small, honestly-sourced local seed parts database (`backend/parts_db.py` + `backend/ato_lib/own_parts/`) of fully pre-pinned components (real footprint + real LCSC id, no live search needed), rather than atopile's tolerance-constrained built-in `Resistor`/`Capacitor` types. This works today with zero account and zero network dependency, for the parts the seed database actually covers.
2. **Autonomous physical PCB layout is not solved by atopile.** It syncs a declarative source against an *existing, human-placed* KiCad layout — it does not generate component placement from nothing. Real layout-reuse for previously-placed sub-modules does work (confirmed via a local, no-registry-needed test), so a real product could plausibly compose boards from a library of once-placed reference modules — but this repo doesn't implement that yet.

## What actually works right now

`POST /generate` on the backend, given `{"pattern": "led_indicator" | "voltage_divider" | "pullup_button" | "reverse_polarity_protection", "v_supply": <volts>, "v_out_target": <volts, voltage_divider only>}`, will:

1. Pick the best available part(s) for the request from `backend/parts_db.py`'s seed database (e.g. the LED-indicator pattern rejects any seed resistor whose current would exceed the LED's real rated max; the voltage-divider pattern does a real combinatorial best-fit search over every seed resistor pair).
2. Generate real `.ato` source (`backend/codegen.py`).
3. Actually run `ato build` against it (`backend/builder.py`) and return the real pass/fail, the real generated source, and the real BOM.

The seed parts database is intentionally tiny (4 resistor values, 3 capacitor values, 1 button, 1 diode) and honestly sourced — see `parts_db.py`'s own docstring for exactly where each part number came from and what a real production version would still need (proper LCSC/Octopart sourcing with live stock checks, not a static hand-copied list). Anything needing a part outside this seed set — a specific IC, an uncommon passive value — is not covered yet.

## Structure

- `frontend/` — Vite + React + TypeScript, deployed on Vercel
- `backend/` — FastAPI, deployed on Render (free tier)
  - `parts_db.py` — the real, honestly-sourced seed parts database and part-selection logic
  - `codegen.py` — generates real `.ato` source for each supported circuit pattern
  - `builder.py` — runs a real `ato build` against generated source, in a throwaway temp directory
  - `ato_lib/` — vendored real `.ato` library source (`generics/` + `own_parts/`) that generated circuits import from
  - `tests/test_generation.py` — real tests: generate, build for real, assert on the real result

## Local development

```bash
# frontend
cd frontend && npm install && npm run dev

# backend
cd backend && python3 -m venv venv && ./venv/bin/pip install -r requirements-dev.txt
./venv/bin/uvicorn main:app --reload
```

### Setting up atopile (needed for `/generate` and for running the tests)

atopile has its own, separate dependency set that can conflict with a system-wide Python install — install it in its own venv:

```bash
cd backend
python3 -m venv .ato-venv && .ato-venv/bin/pip install atopile
export PATH="$(pwd)/.ato-venv/bin:$PATH"   # needs to be on PATH when running uvicorn or pytest
```

`tests/test_generation.py`'s real build tests auto-skip (not fail) if `ato` isn't found on PATH.
