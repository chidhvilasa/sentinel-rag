# Screenshots

None of the images below exist yet — this is a checklist of what to capture and where each one is referenced from. Add the file, then update the corresponding link (all currently point here as a placeholder).

| # | File to add | What to capture | Referenced from |
|---|---|---|---|
| 1 | `banner.png` | A wide GitHub social-preview-style banner (project name + one-line tagline) | GitHub repo "social preview" setting (Settings → General), not embedded in README |
| 2 | `demo-home.png` | The web UI homepage (`GET /`) on first load, empty state | `README.md` Screenshots section |
| 3 | `demo-threat-detected.png` | The UI after analyzing a poisoned document — showing `threat_level`, the highlighted malicious excerpt, and the neutralized text side by side | `README.md`, `docs/usage.md` |
| 4 | `demo-safe-document.png` | The UI after analyzing a clean document — showing `is_threat: false` and the unmodified pass-through | `README.md` |
| 5 | `architecture-diagram.png` (optional) | A rendered export of the Mermaid system-overview diagram, for viewers whose Markdown renderer doesn't support Mermaid | `docs/architecture.md` (optional fallback) |
| 6 | `directory-structure.png` (optional) | A terminal screenshot of `tree` or similar showing the top-level layout | `docs/development.md` (optional, the Mermaid diagram there already covers this) |
| 7 | `api-response-example.png` | A terminal/Postman/browser screenshot of a real `POST /api/analyze` response | `docs/api.md` |
| 8 | `benchmark-results.png` (optional) | Terminal output of `scripts/evaluate_large.py` or `scripts/benchmark_latency.py` running | `docs/benchmarks.md` (optional — the numbers are already tabulated there from real runs) |

## How to capture these

1. Start the web demo: `python src/web/new_app.py`
2. Open `http://localhost:8000` and use the sample files in `data/samples/` to drive #2–#4.
3. For #7, run `curl -X POST http://localhost:8000/api/analyze -H "Content-Type: application/json" -d '{"content": "..."}'` against a real attack payload (see `data/samples/sample_attack_naive.txt`).
4. Save PNGs into this directory, then replace the placeholder link/text in the referencing doc with a real `![alt text](docs/screenshots/filename.png)`.

Nothing here is fabricated or implied to exist — every image above is a to-do, not a claim.
