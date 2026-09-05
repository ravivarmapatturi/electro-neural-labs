import { useEffect, useState, type FormEvent } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

type Pattern = 'led_indicator' | 'voltage_divider' | 'pullup_button' | 'reverse_polarity_protection'

const PATTERNS: { value: Pattern; label: string; needsVOut: boolean }[] = [
  { value: 'led_indicator', label: 'LED status indicator', needsVOut: false },
  { value: 'voltage_divider', label: 'Voltage divider', needsVOut: true },
  { value: 'pullup_button', label: 'Push button with pull-up', needsVOut: false },
  { value: 'reverse_polarity_protection', label: 'Reverse-polarity protection', needsVOut: false },
]

interface GenerateResponse {
  pattern: Pattern
  ato_source: string
  build_success: boolean
  bom_csv: string | null
  build_stdout: string
  build_warnings: string[]
}

function parseBom(csv: string | null): string[][] {
  if (!csv) return []
  return csv
    .trim()
    .split('\n')
    .map((row) => row.split(','))
}

function App() {
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking')

  const [pattern, setPattern] = useState<Pattern>('led_indicator')
  const [vSupply, setVSupply] = useState('5')
  const [vOutTarget, setVOutTarget] = useState('3')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<GenerateResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((r) => (r.ok ? setBackendStatus('online') : setBackendStatus('offline')))
      .catch(() => setBackendStatus('offline'))
  }, [])

  const selected = PATTERNS.find((p) => p.value === pattern)!

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const body: Record<string, unknown> = { pattern, v_supply: Number(vSupply) }
      if (selected.needsVOut) body.v_out_target = Number(vOutTarget)

      const res = await fetch(`${API_URL}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => null)
        throw new Error(detail?.detail ?? `Request failed (${res.status})`)
      }
      setResult(await res.json())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const bomRows = parseBom(result?.bom_csv ?? null)

  return (
    <main className="page">
      <section className="hero">
        <h1>Electro Neural Labs</h1>
        <p className="tagline">AI for PCB design, EDA, and CAD.</p>
        <p className="pitch">
          Starting with a real pipeline: describe a circuit in plain language, get a working,
          manufacturable PCB out the other end — natural-language description&nbsp;&rarr;&nbsp;netlist&nbsp;&rarr;&nbsp;schematic&nbsp;&rarr;&nbsp;layout.
        </p>
      </section>

      <section className="status">
        <h2>Status</h2>
        <p>
          Early build. Generation currently covers 4 real circuit patterns, each backed by a
          small, honestly-sourced seed parts database and validated against a real compiler build
          below — not a general natural-language-to-netlist system yet.
        </p>
        <p className="backend-status">
          Backend: <span className={`badge badge-${backendStatus}`}>{backendStatus}</span>
        </p>
      </section>

      <section className="generator">
        <h2>Try it</h2>
        <form onSubmit={handleSubmit}>
          <label>
            Pattern
            <select value={pattern} onChange={(e) => setPattern(e.target.value as Pattern)}>
              {PATTERNS.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            Supply voltage (V)
            <input
              type="number"
              step="0.1"
              value={vSupply}
              onChange={(e) => setVSupply(e.target.value)}
              required
            />
          </label>

          {selected.needsVOut && (
            <label>
              Target output voltage (V)
              <input
                type="number"
                step="0.1"
                value={vOutTarget}
                onChange={(e) => setVOutTarget(e.target.value)}
                required
              />
            </label>
          )}

          <button type="submit" disabled={loading || backendStatus !== 'online'}>
            {loading ? 'Generating…' : 'Generate & build'}
          </button>
          {backendStatus !== 'online' && (
            <p className="hint">Backend is {backendStatus} — generation needs it online.</p>
          )}
        </form>

        {error && <p className="error">{error}</p>}

        {result && (
          <div className="result">
            <p className="build-result">
              Build:{' '}
              <span className={`badge badge-${result.build_success ? 'online' : 'offline'}`}>
                {result.build_success ? 'success' : 'failed'}
              </span>
            </p>

            {result.build_warnings.length > 0 && (
              <ul className="warnings">
                {result.build_warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            )}

            <h3>Generated .ato source</h3>
            <pre className="code-block">{result.ato_source}</pre>

            {bomRows.length > 1 && (
              <>
                <h3>Bill of materials</h3>
                <table className="bom">
                  <thead>
                    <tr>
                      {bomRows[0].map((h, i) => (
                        <th key={i}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {bomRows.slice(1).map((row, i) => (
                      <tr key={i}>
                        {row.map((cell, j) => (
                          <td key={j}>{cell}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}

            {!result.build_success && (
              <>
                <h3>Build output</h3>
                <pre className="code-block build-log">{result.build_stdout}</pre>
              </>
            )}
          </div>
        )}
      </section>
    </main>
  )
}

export default App
