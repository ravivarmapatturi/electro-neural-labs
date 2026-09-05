# Electro Neural Labs

AI for PCB design, EDA, and CAD.

Starting pipeline: **natural-language description → netlist → schematic → layout** — describe a circuit in plain language, get a real, manufacturable board out the other end.

## Status

Early build. This repo currently contains a minimal, working full-stack scaffold (frontend + backend, deployed and talking to each other) to prove the deployment pipeline before the real AI logic lands — no natural-language-to-netlist generation exists yet.

## Architecture direction (not yet built)

The likely architecture is **one new AI system, not three**: [atopile](https://github.com/atopile/atopile) — an existing, open-source, MIT-licensed declarative PCB compiler — already turns a structured circuit description into a real, manufacturable board (it handles netlist → schematic → layout today). The genuinely new work is generating valid `.ato` source from a natural-language description; atopile's own compiler can plausibly handle everything after that. This needs to be verified against a real atopile build before committing to it, not assumed.

## Structure

- `frontend/` — Vite + React + TypeScript, deployed on Vercel
- `backend/` — FastAPI, deployed on Render (free tier)

## Local development

```bash
# frontend
cd frontend && npm install && npm run dev

# backend
cd backend && python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
./venv/bin/uvicorn main:app --reload
```
