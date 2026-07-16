# Changelog

All notable changes to this project are documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning follows [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-07-16

Initial public release.

### Added
- Hybrid Sentinel detection layer (DeBERTa classifier + regex pattern library) with multi-pass semantic neutralization (`SentinelDetector`, `SentinelNeutralizer`, `SentinelPipeline`).
- RAG pipeline with document loading/chunking, ChromaDB vector storage, and Ollama LLM integration (`SentinelRAG`, `RAGPipeline`, `OllamaLLM`).
- FastAPI web demo (`src/web/new_app.py`) with PDF upload, detection/neutralization, and side-by-side protected-vs-unprotected LLM comparison.
- Experimental "V5" detection modules: multi-language keyword detection, statistical zero-shot anomaly detection, a simpler context-aware neutralizer, a detection explainer, and an adversarial-example generator (not yet wired into the production pipeline — see `docs/architecture.md`).
- Evaluation tooling: attack-success-rate comparison, latency benchmarking, evaluation against the public `deepset/prompt-injections` benchmark, and a spotlighting-defense comparison.
- Full documentation set (`docs/`): installation, usage, architecture with diagrams, API reference, and benchmarks.
- Project governance/OSS files: license, contributing guide, security policy, code of conduct, citation metadata, issue/PR templates.

### Fixed
- `src/sentinel/__init__.py` was missing `SentinelDetector`, `SentinelNeutralizer`, and `ProcessedChunk` from its exports — the last of these broke the entire `src` package (`import src`, `from src import SentinelRAG`, and anything importing `src.sentinel`/`src.rag` transitively) with an `ImportError` at module load time. All three are now exported correctly.
- `run_sentinel_v5.py`: fixed a broken V4-detector call (was passing a file path where text was expected, and calling `.get()` on a dataclass), switched from the unmaintained `PyPDF2` to `pypdf` (already a dependency), and fixed the `--web` flag to launch the actual FastAPI app via `uvicorn` instead of assuming a Flask `.run()` method.
- Most scripts under `scripts/` resolved paths relative to the current working directory rather than their own location, only working when invoked as `cd scripts && python foo.py`; they're now cwd-independent and runnable from the repository root as documented.
- `scripts/evaluate_deepset.py`: a local re-import of `load_dataset` inside an `except` block made Python treat the name as local for the *entire* function, so the first `load_dataset()` call always raised `UnboundLocalError` (silently caught, then masked by an unnecessary `pip install` retry on every run). Removed the redundant re-import.
- `run_sentinel_v5.py --web` bound the demo server to `0.0.0.0` (all network interfaces) instead of `127.0.0.1`; unnecessary exposure for a local-only demo tool.

### Changed
- Repository restructured: the project root now matches the git repository root (previously nested one directory deeper); a stray, out-of-date `requirements.txt`/`architecture.md`/tracked `venv/` at the outer level were removed.
- `requirements.txt` split into runtime (`requirements.txt`) and development/evaluation (`requirements-dev.txt`) dependency sets; missing runtime dependencies (`PyMuPDF`, `python-multipart`) added, unused dependency (`python-docx`) removed.
- Both files now pin exact versions (verified working end-to-end) instead of open-ended lower bounds, and upgrade `pypdf`, `python-multipart`, `python-dotenv`, `pydantic-settings`, and `pytest` to patched releases addressing known CVEs.
- Tests converted from print-driven manual-inspection scripts to real `pytest` tests with assertions; consolidated from two locations (project root + `tests/`) into `tests/` only.
- `.gitignore` hardened to cover model/data artifacts, vector store directories, and common cache directories.
- Entire codebase formatted with `black`/`isort`/`ruff` (whitespace and import-order only — verified via full test-suite and evaluation re-runs that behavior is byte-for-byte unchanged); removed ~20 dead imports/unused variables across `src/` and `scripts/`.
- Added `.github/workflows/{ci,lint,security}.yml` for automated testing, linting, and security scanning on every push/PR.

### Removed
- `src/web/app1.py`, an earlier draft of `src/web/app.py` with no unique functionality.
