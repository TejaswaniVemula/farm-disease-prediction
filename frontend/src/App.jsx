import { useEffect, useMemo, useState } from "react";
import { getSymptoms, predict } from "./services/api";


function RiskBadge({ label }) {
  // label example: "High Risk / అధిక ప్రమాదం"
  const isHigh = label.toLowerCase().includes("high risk");
  const isMed = label.toLowerCase().includes("medium risk");
  const cls = isHigh
    ? "badge badge-high"
    : isMed
    ? "badge badge-med"
    : "badge badge-low";

  return <span className={cls}>{label}</span>;
}

function Pill({ text, onRemove }) {
  return (
    <span className="pill">
      {text}
      <button className="pill-x" onClick={onRemove} title="Remove">
        ×
      </button>
    </span>
  );
}

export default function App() {
  const [animal, setAnimal] = useState("Cow");
  const [allSymptoms, setAllSymptoms] = useState([]); // array of {en, te, display}
  const [selected, setSelected] = useState([]); // array of symptom en strings
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getSymptoms()
      .then(setAllSymptoms)
      .catch(() => setError("Failed to load symptoms. Please start backend (FastAPI)."));
  }, []);

  const selectedDisplay = useMemo(() => {
    const map = new Map(allSymptoms.map((s) => [s.en, s.display]));
    return selected.map((en) => map.get(en) || en);
  }, [selected, allSymptoms]);

  const filteredSymptoms = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return allSymptoms;
    return allSymptoms.filter((s) => s.display.toLowerCase().includes(q));
  }, [query, allSymptoms]);

  const toggle = (en) => {
    setSelected((prev) => {
      if (prev.includes(en)) return prev.filter((x) => x !== en);
      if (prev.length >= 8) {
        setError("You can select maximum 8 symptoms.");
        return prev;
      }
      return [...prev, en];
    });
  };

  const clearAll = () => {
    setSelected([]);
    setQuery("");
    setResult(null);
    setError("");
  };

  const onPredict = async () => {
    setError("");
    setResult(null);

    if (selected.length < 3) {
      setError("Select at least 3 symptoms.");
      return;
    }

    setLoading(true);
    try {
      const data = await predict({ animal, symptoms: selected, top_k: 3 });
      setResult(data);
    } catch {
      setError("Prediction failed. Check backend is running on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="topbar">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold text-white">
              Farm Animal Disease Prediction System
            </h1>
            <p className="text-emerald-50 text-sm md:text-base mt-1">
              పశువుల వ్యాధి అంచనా వ్యవస్థ
            </p>
        </div>

        
      </div>

      <div className="layout">
        {/* LEFT: INPUT */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Input</div>
              <div className="card-hint">Select animal and symptoms (min 3, max 8)</div>
            </div>
            <button className="btn btn-ghost" onClick={clearAll}>
              Clear
            </button>
          </div>

          <div className="field">
            <label className="label">Animal</label>
            <select className="select" value={animal} onChange={(e) => setAnimal(e.target.value)}>
              <option value="Cow">Cow / ఆవు</option>
              <option value="Buffalo">Buffalo / గేదె</option>
              <option value="Goat">Goat / మేక</option>
              <option value="Sheep">Sheep / గొర్రె</option>
            </select>
          </div>

          <div className="field">
            <label className="label">Search Symptoms</label>
            <input
              className="input"
              placeholder="Type fever / జ్వరం ..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>

          <div className="field">
            <label className="label">
              Selected Symptoms <span className="muted">({selected.length}/8)</span>
            </label>
            {selected.length === 0 ? (
              <div className="empty">No symptoms selected yet.</div>
            ) : (
              <div className="pill-wrap">
                {selected.map((en, idx) => (
                  <Pill
                    key={en}
                    text={selectedDisplay[idx]}
                    onRemove={() => setSelected((prev) => prev.filter((x) => x !== en))}
                  />
                ))}
              </div>
            )}
          </div>

          <div className="field">
            <label className="label">Choose Symptoms</label>
            <div className="symptom-grid">
              {filteredSymptoms.map((s) => (
                <button
                  type="button"
                  key={s.en}
                  className={`symptom-item ${selected.includes(s.en) ? "active" : ""}`}
                  onClick={() => toggle(s.en)}
                >
                  <span className="symptom-check">{selected.includes(s.en) ? "✓" : "+"}</span>
                  <span className="symptom-text">{s.display}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="actions">
            <button className="btn btn-primary" onClick={onPredict} disabled={loading}>
              {loading ? "Predicting..." : "Predict"}
            </button>
            <div className="helper">
              Tip: Choose the most noticeable symptoms first for better confidence.
            </div>
          </div>

          {error && <div className="alert alert-error">{error}</div>}
        </div>

        {/* RIGHT: OUTPUT */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Output</div>
              <div className="card-hint">Predicted disease, risk level and guidance</div>
            </div>
          </div>

          {!result ? (
            <div className="empty big">
              <div className="empty-title">No prediction yet</div>
              <div className="empty-sub">Select symptoms and click Predict to view results.</div>
            </div>
          ) : (
            <>
              <div className="summary">
                <div className="summary-box">
                  <div className="summary-label">Animal</div>
                  <div className="summary-value">{result.animal.display}</div>
                </div>

                <div className="summary-box">
                  <div className="summary-label">Risk</div>
                  <div className="summary-value">
                    <RiskBadge label={result.risk.overall.display} />
                  </div>
                </div>
              </div>

              <div className="section">
                <div className="section-title">Selected Symptoms</div>
                <div className="section-body">
                  {result.symptoms.map((x) => x.display).join(", ")}
                </div>
              </div>

              <div className="section">
                <div className="section-title">Top Predictions</div>
                <div className="table-wrap">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Disease</th>
                        <th style={{ width: 130 }}>Probability</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.predictions.map((p, i) => (
                        <tr key={i} className={i === 0 ? "row-highlight" : ""}>
                          <td>
                            <div className="disease-name">{p.disease.display}</div>
                            {i === 0 && <div className="muted">Most likely</div>}
                          </td>
                          <td>
                            <div className="prob">
                              <div className="bar">
                                <div className="bar-fill" style={{ width: `${p.probability_percent}%` }} />
                              </div>
                              <div className="prob-text">{p.probability_percent}%</div>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="alert alert-info">
                  <b>Risk Explanation:</b> {result.risk.explanation}
                </div>
              </div>

              <div className="two-col">
                <div className="panel">
                  <div className="panel-title">Prevention</div>
                  <div className="panel-body">
                    {result.prevention ? result.prevention.display : "—"}
                  </div>
                </div>
                <div className="panel">
                  <div className="panel-title">Precautions</div>
                  <div className="panel-body">
                    {result.precautions ? result.precautions.display : "—"}
                  </div>
                </div>
              </div>

              <div className="footer-note">
                ⚠️ This system provides decision support only. Consult a veterinary doctor for confirmation.
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
