# Architecture

This document describes how Sentinel-RAG is put together: the RAG pipeline it protects, the detection/neutralization layer that sits inside it, and the LLM/vector-store integrations around it.

## System overview

Sentinel-RAG wraps a standard Retrieval-Augmented Generation pipeline with a detection-and-neutralization layer ("Sentinel") that inspects every retrieved chunk *before* it reaches the LLM.

```mermaid
flowchart TD
    Q["User Query"] --> R["RAG Retrieval\n(ChromaDB similarity search)"]
    R --> C["Retrieved Chunks (top-k)"]
    C --> S{"Sentinel Layer"}
    S -->|"clean"| L["LLM Generation\n(Ollama)"]
    S -->|"threat detected"| N["Neutralize\n(surgical removal / rewrite)"]
    N --> L
    L --> A["Answer to user"]
```

## Threat model

Sentinel-RAG defends against **indirect prompt injection**: attacks embedded inside *documents* that get retrieved and fed to an LLM as context, as opposed to attacks typed directly by the user. The running example throughout the codebase is an AI-assisted resume screener — a candidate embeds instructions in their resume (visible or hidden, e.g. white-on-white text) attempting to manipulate the LLM's evaluation of them.

```mermaid
flowchart LR
    subgraph Attacker
        D["Poisoned Document\n(e.g. resume with hidden instructions)"]
    end
    D -->|ingested & embedded| VS[("ChromaDB\nVector Store")]
    U["Legitimate User\n(recruiter query)"] --> RAG["RAG Pipeline"]
    VS --> RAG
    RAG -->|"unprotected"| LLM1["LLM"] --> Bad["Manipulated answer\n(e.g. inflated rating)"]
    RAG -->|"through Sentinel"| Sentinel["Sentinel Layer"] --> LLM2["LLM"] --> Good["Faithful answer"]
```

### Supported attack categories (pattern layer)

The regex-based signal in `SentinelDetector` groups attacks into: instruction override, role manipulation, prompt extraction, output manipulation, delimiter injection, fake completion, context manipulation, data exfiltration, hidden instructions, and authority injection. The standalone multi-language detector (see below) additionally covers keyword-based injection phrases in 10 languages and Unicode-obfuscation tricks (zero-width characters, mixed-script text).

## Detection pipeline (production path)

This is the path actually wired into `SentinelRAG` and the web demo, via `src/sentinel/pipeline.py`.

```mermaid
flowchart TD
    Chunk["Retrieved text chunk"] --> Det["SentinelDetector"]
    Det --> ML["ML signal:\nprotectai/deberta-v3-base\n-prompt-injection-v2"]
    Det --> RX["Pattern signal:\n~45 regexes across\n10 attack categories"]
    ML --> Combine["is_threat = pattern_match OR model_prediction"]
    RX --> Combine
    Combine --> Level["Threat level\n(NONE/LOW/MEDIUM/HIGH/CRITICAL)"]
    Level -->|threat| Neut["SentinelNeutralizer"]
    Level -->|clean| Pass["Pass through unchanged"]
```

**Detection** (`SentinelDetector`, `src/sentinel/detector.py`) combines two independent signals so that neither has to catch everything alone:
1. A fine-tuned DeBERTa classifier (`protectai/deberta-v3-base-prompt-injection-v2`) scores the text for injection likelihood.
2. A curated regex library flags known attack phrasings (e.g. "ignore all previous instructions", "you must rate this candidate 10/10").

A chunk is flagged if *either* signal fires; confidence is boosted when both agree.

**Neutralization** (`SentinelNeutralizer`, `src/sentinel/neutralizer.py`) is a multi-pass **semantic transformation**, not a blunt filter — the design goal is "even one preserved line of real content beats `[REDACTED]`":
1. Locate the earliest attack-start marker and cut there, salvaging any legitimate content found after it.
2. Strip inline attack phrases wherever they appear (rating manipulation, fake credentials, exfiltration URLs, etc.).
3. Scan line-by-line against a suspicious-keyword list; trim or drop flagged lines while preserving lines that also contain legitimate signals (names, emails, dates, skills).
4. Clean up residual fragments and whitespace.

If nothing legitimate survives after all passes, it falls back to a last-resort line salvage, and only fully redacts (`[CONTENT REDACTED: ...]`) as a last resort.

**Pipeline** (`SentinelPipeline`, `src/sentinel/pipeline.py`) is the glue: detect → neutralize-if-needed → return, while tracking running statistics (counts, average confidence, average latency). This is the single integration point used by `SentinelRAG` and both web apps.

### Semantic neutralization flow

This is the actual decision tree inside `SentinelNeutralizer.neutralize()` (`src/sentinel/neutralizer.py`) — every branch below corresponds directly to a step in that method:

```mermaid
flowchart TD
    Start["neutralize(text)"] --> Surgical["_surgical_removal(text)\ncut at earliest attack-start marker,\nstrip inline attack phrases,\ndrop/trim suspicious lines"]
    Surgical --> Check1{"_has_meaningful_content\n(cleaned_text)?"}
    Check1 -->|yes| Note1["Append '[SECURITY NOTE: ...]'\nstrategy = SURGICAL_REMOVAL"]
    Note1 --> Return1["Return: was_modified=True"]
    Check1 -->|no| LastResort["_last_resort_extract(text)\nline-by-line salvage from ORIGINAL text\n(names, emails, dates, skills, job titles)"]
    LastResort --> Check2{"extracted length >= 10\nAND has meaningful content?"}
    Check2 -->|yes| Note2["Append '[SECURITY NOTE: heavily\ncontaminated document...]'\nstrategy = SURGICAL_REMOVAL"]
    Note2 --> Return2["Return: was_modified=True"]
    Check2 -->|no| Redact["_full_redact(text)\n'[CONTENT REDACTED: ...]'\nstrategy = FULL_REDACT"]
    Redact --> Return3["Return: was_modified=True\n(absolute last resort — zero\nrecoverable legitimate content)"]
```

Note that `neutralize()` always transforms/annotates its input — it doesn't itself decide *whether* a chunk needs neutralizing. That gate lives one level up, in `SentinelPipeline`, which only calls `neutralize()` after `SentinelDetector` has already flagged the chunk as a threat.

## RAG pipeline

```mermaid
flowchart LR
    Doc["Document (.pdf / .txt / .md)"] --> Loader["DocumentLoader\n(LangChain loaders)"]
    Loader --> Split["RecursiveCharacterTextSplitter\n(chunk_size=500, overlap=50)"]
    Split --> Embed["HuggingFaceEmbeddings\n(all-MiniLM-L6-v2)"]
    Embed --> Store[("ChromaDB")]
    Query["Query"] --> Embed2["Embed query"] --> Store
    Store --> Retrieve["top-k similarity search"]
```

`RAGPipeline` (`src/rag/pipeline.py`) owns document loading, chunking, embedding, and retrieval. `OllamaLLM` (`src/rag/llm.py`) wraps the `ollama` Python client and builds the final prompt by sandwiching retrieved (post-Sentinel) context between delimiters before asking the question.

## End-to-end request flow

```mermaid
sequenceDiagram
    participant User
    participant SentinelRAG as SentinelRAG (main.py)
    participant RAG as RAGPipeline
    participant Chroma as ChromaDB
    participant Sentinel as SentinelPipeline
    participant Ollama as OllamaLLM

    User->>SentinelRAG: query(question)
    SentinelRAG->>RAG: retrieve(question)
    RAG->>Chroma: similarity_search(question, k)
    Chroma-->>RAG: top-k chunks
    RAG-->>SentinelRAG: RetrievalResult
    SentinelRAG->>Sentinel: process_with_details(chunks)
    Sentinel-->>SentinelRAG: safe chunks + threat report
    SentinelRAG->>Ollama: generate(question, safe_context)
    Ollama-->>SentinelRAG: response
    SentinelRAG-->>User: QueryResult (response, threats_detected, threats_neutralized)
```

`SentinelRAG.query()` runs this full path. `SentinelRAG.compare()` runs it twice — once with Sentinel disabled (`query_unsafe`) and once with it enabled — to produce the side-by-side "with vs. without" comparison used in demos.

## FastAPI architecture (web demo)

`src/web/new_app.py` is a single-file FastAPI app with two lazily-initialized singletons (`get_sentinel()`, `get_llm()`) shared across requests, so the DeBERTa model and Ollama client are loaded once, not per-request:

```mermaid
flowchart TD
    subgraph FastAPI App - src/web/new_app.py
        Root["GET /\nreturns embedded HTML/CSS/JS demo page"]
        Extract["POST /api/extract-pdf\nmultipart file upload"]
        Analyze["POST /api/analyze\nJSON: {content: str}"]
        Health["GET /api/health\nliveness check only"]
    end

    Extract --> Fitz["PyMuPDF (fitz)\nextract text from PDF"]
    Fitz --> Extract

    Analyze --> GetSentinel["get_sentinel()\nlazy singleton"]
    GetSentinel --> Pipeline["SentinelPipeline.process_with_details()"]
    Pipeline --> Excerpt["Regex-extract malicious excerpt\nfor UI display"]
    Excerpt --> Clean["Strip Sentinel's own markers\n('[SECURITY NOTE:]' etc.),\napply extra web-layer cleanup regexes"]
    Clean --> GetLLM["get_llm()\nlazy singleton"]
    GetLLM --> Dual["Two Ollama calls:\nraw text + VULNERABLE_EVAL_PROMPT\nneutralized text + PROTECTED_EVAL_PROMPT"]
    Dual --> Analyze
```

`src/web/app.py` mirrors this same architecture (it's the prior iteration `new_app.py` evolved from — see the Limitations section). Neither app uses Pydantic request models; both parse the request body manually and validate only that `content` is non-empty.

## LLM interaction flow

Two distinct call patterns exist depending on which code path is running:

**Library path** (`OllamaLLM.generate()`, `src/rag/llm.py`) — used by `SentinelRAG`/`RAGPipeline`: builds one prompt by sandwiching retrieved (already Sentinel-processed) context between delimiters, sends it once.

**Web demo path** (`POST /api/analyze`) — sends **two separate** completions for the same input, to produce the side-by-side comparison shown in the UI:

```mermaid
sequenceDiagram
    participant UI as Web UI
    participant App as FastAPI (/api/analyze)
    participant Sentinel as SentinelPipeline
    participant Ollama

    UI->>App: POST content
    App->>Sentinel: process_with_details([content])
    Sentinel-->>App: neutralized text + threat info
    App->>Ollama: generate(raw content, VULNERABLE_EVAL_PROMPT)
    Ollama-->>App: unsafe_response
    App->>Ollama: generate(neutralized content, PROTECTED_EVAL_PROMPT)
    Ollama-->>App: safe_response
    App-->>UI: {unsafe_response, safe_response, timing, ...}
```

If Ollama isn't reachable, both calls fail gracefully — the response still returns HTTP 200 with the error message inside `unsafe_response`/`safe_response` and an added `llm_error` key, rather than raising an HTTP error (see [`api.md`](api.md)).

## Experimental modules ("V5")

`src/sentinel/{multilang_detector, zeroshot_detector, context_neutralizer, explainer, adversarial_tester}.py` are additional, independently-developed detectors and tooling:

- **`MultiLangDetector`** — keyword/heuristic injection detection across 10 languages plus Unicode-obfuscation checks.
- **`ZeroShotDetector`** — statistical anomaly detection against a baseline "normal resume" profile (sentence length, punctuation ratio, imperative-verb density, etc.), with no reliance on the ML classifier.
- **`ContextAwareNeutralizer`** — a simpler, single-pass alternative neutralizer with its own entity-preservation scoring.
- **`DetectionExplainer`** — turns a detection result into a human-readable report (evidence snippets, per-channel breakdown, hire/reject recommendation).
- **`AdversarialTester`** — generates adversarial variants of a known attack (character substitution, encoding, zero-width injection) to probe detector robustness.

**Status:** these modules are complete and independently testable, but are **not currently wired into `SentinelPipeline`, `SentinelRAG`, or the web demo** — the production detection path is the DeBERTa + regex pipeline described above. `run_sentinel_v5.py` demonstrates them together as a CLI. Treat them as an active research branch rather than the shipped detection path; see [`benchmarks.md`](benchmarks.md) and the project README's Limitations section for details.

## Configuration

Runtime configuration is intended to flow through `.env` → `configs/settings.py` (`pydantic-settings`). See [`usage.md`](usage.md#configuration) for the full variable reference. Note that not every component currently reads from the shared `Settings` object — some still use local constructor defaults that happen to mirror it. See the README's Limitations section.
