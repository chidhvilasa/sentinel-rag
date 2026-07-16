# Installation

## Prerequisites

- Python 3.10+
- 16 GB RAM minimum (the DeBERTa detection model + embedding model + LLM all load into memory)
- An NVIDIA GPU is optional but speeds up detection and embedding
- [Ollama](https://ollama.com) for local LLM inference

## 1. Install Ollama

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

**Windows:**
Download the installer from [ollama.com/download](https://ollama.com/download).

Pull a model (the default config expects `llama3:8b`; use a smaller one if you're RAM-constrained):
```bash
ollama pull llama3:8b
# or, for lower memory:
ollama pull phi3:mini
```

## 2. Clone and set up a virtual environment

**Linux / macOS:**
```bash
git clone https://github.com/chidhvilasa/sentinel-rag.git
cd sentinel-rag
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/chidhvilasa/sentinel-rag.git
cd sentinel-rag
python -m venv venv
venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

For running tests, evaluation scripts, or the dataset-generation scripts, also install dev dependencies:
```bash
pip install -r requirements-dev.txt
```

## 4. Configure environment

```bash
cp .env.example .env
```

The defaults work out of the box for a local Ollama setup. See [`usage.md`](usage.md#configuration) for what each variable does.

## 5. Start Ollama

In a separate terminal:
```bash
ollama serve
```

## 6. Run something

```bash
# Rich-console CLI demo
python scripts/demo.py

# FastAPI web demo
uvicorn src.web.new_app:app --reload
# then open http://localhost:8000
```

See [`usage.md`](usage.md) for the full command reference.

## Troubleshooting

**`ConnectionError` / detector or LLM calls hang or fail**
Ollama isn't running, or isn't reachable at `LLM_BASE_URL` (default `http://localhost:11434`). Start it with `ollama serve` and confirm the model is pulled (`ollama list`).

**First run is slow / downloads several GB**
The DeBERTa detection model (`protectai/deberta-v3-base-prompt-injection-v2`) and the sentence-transformer embedding model (`all-MiniLM-L6-v2`) are downloaded from Hugging Face on first use and cached locally (`~/.cache/huggingface` by default). Subsequent runs are fast.

**`ModuleNotFoundError` for `PyMuPDF`/`fitz`, `reportlab`, or `datasets`**
Make sure you installed from the right file — `PyMuPDF` is in `requirements.txt` (needed by the web demo's PDF upload), while `reportlab` and `datasets` are dev/eval-only and live in `requirements-dev.txt`.

**Torch install issues on Windows / no GPU**
The pinned `torch>=2.2.0` installs a CPU build by default via PyPI on most platforms. If you need CUDA acceleration, install the matching `torch` build from [pytorch.org](https://pytorch.org/get-started/locally/) *before* running `pip install -r requirements.txt`, so pip doesn't overwrite it.

**Port 8000 already in use**
`uvicorn src.web.new_app:app --reload --port 8001`

**`UnicodeEncodeError: 'charmap' codec can't encode character '✅'` (Windows only)**
Several scripts print emoji (✅/🚨/⚠️) directly to stdout, which fails on a legacy `cp1252` Windows console. Fix by forcing UTF-8 output before running:
```powershell
$env:PYTHONIOENCODING = "utf-8"
python scripts/demo.py
```
or run `chcp 65001` once in the terminal session first. Windows Terminal with a recent PowerShell defaults to UTF-8 and typically isn't affected.
