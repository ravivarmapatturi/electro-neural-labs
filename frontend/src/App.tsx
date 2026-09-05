import { useEffect, useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

function App() {
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking')

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((r) => (r.ok ? setBackendStatus('online') : setBackendStatus('offline')))
      .catch(() => setBackendStatus('offline'))
  }, [])

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
          Early build. The natural-language-to-netlist pipeline is in active development —
          nothing generates a real board yet. This page exists to prove the deployment
          pipeline (frontend + backend) works end to end before the real AI logic lands.
        </p>
        <p className="backend-status">
          Backend: <span className={`badge badge-${backendStatus}`}>{backendStatus}</span>
        </p>
      </section>
    </main>
  )
}

export default App
