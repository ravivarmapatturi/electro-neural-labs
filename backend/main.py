from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import codegen
from builder import build_circuit

app = FastAPI(title="Electro Neural Labs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the real frontend origin once one exists
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


Pattern = Literal["led_indicator", "voltage_divider", "pullup_button", "reverse_polarity_protection"]


class GenerateRequest(BaseModel):
    pattern: Pattern
    v_supply: float = 5.0
    # Only used by voltage_divider; ignored otherwise.
    v_out_target: float | None = None


class GenerateResponse(BaseModel):
    pattern: Pattern
    ato_source: str
    build_success: bool
    bom_csv: str | None
    build_stdout: str
    build_warnings: list[str]


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> GenerateResponse:
    """Generates real `.ato` source for one of a small set of proven
    circuit patterns (see codegen.py), then validates it against a real
    `ato build` (see builder.py) -- the same real generate-then-verify
    loop proven manually during this feature's research phase. Only
    covers what parts_db.py's tiny, honestly-sourced seed database
    actually has real parts for -- see parts_db.py's own docstring for
    exactly what that does and doesn't include."""
    try:
        if req.pattern == "led_indicator":
            source = codegen.led_indicator(req.v_supply)
        elif req.pattern == "voltage_divider":
            if req.v_out_target is None:
                raise HTTPException(422, "voltage_divider requires v_out_target")
            source = codegen.voltage_divider(req.v_supply, req.v_out_target)
        elif req.pattern == "pullup_button":
            source = codegen.pullup_button(req.v_supply)
        elif req.pattern == "reverse_polarity_protection":
            source = codegen.reverse_polarity_protection(req.v_supply)
        else:
            raise HTTPException(422, f"Unknown pattern: {req.pattern}")
    except ValueError as e:
        # E.g. no seed part in parts_db.py can satisfy the request (no
        # resistor keeps LED current safe at this voltage) -- a real,
        # anticipatable rejection, not a server error.
        raise HTTPException(422, str(e)) from e

    try:
        result = build_circuit(source)
    except RuntimeError as e:
        raise HTTPException(500, str(e)) from e

    return GenerateResponse(
        pattern=req.pattern,
        ato_source=source,
        build_success=result.success,
        bom_csv=result.bom_csv,
        build_stdout=result.stdout,
        build_warnings=result.warnings,
    )
