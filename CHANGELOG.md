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

### Changed
- Repository restructured: the project root now matches the git repository root (previously nested one directory deeper); a stray, out-of-date `requirements.txt`/`architecture.md`/tracked `venv/` at the outer level were removed.
- `requirements.txt` split into runtime (`requirements.txt`) and development/evaluation (`requirements-dev.txt`) dependency sets; missing runtime dependencies (`PyMuPDF`, `python-multipart`) added, unused dependency (`python-docx`) removed.
- Tests converted from print-driven manual-inspection scripts to real `pytest` tests with assertions; consolidated from two locations (project root + `tests/`) into `tests/` only.
- `.gitignore` hardened to cover model/data artifacts, vector store directories, and common cache directories.

### Removed
- `src/web/app1.py`, an earlier draft of `src/web/app.py` with no unique functionality.
