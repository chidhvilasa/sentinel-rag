# Security Policy

Sentinel-RAG is a research project studying defenses against prompt injection. We take reports of both traditional security vulnerabilities and detection-bypass techniques seriously.

## Reporting a vulnerability

**Do not open a public GitHub issue for security reports.** Instead, use [GitHub's private vulnerability reporting](https://github.com/chidhvilasa/sentinel-rag/security/advisories/new) for this repository, or email the maintainer directly (see the GitHub profile for contact info).

Please include:
- A description of the issue and its potential impact
- Steps to reproduce (a minimal example is ideal)
- If applicable: which component is affected (detector, neutralizer, RAG pipeline, web demo)

## Scope

In scope:
- Traditional vulnerabilities (e.g. injection, path traversal, unsafe deserialization) in the web demo or supporting scripts
- Reliable detector/neutralizer bypasses — i.e. an injection payload that consistently evades detection and successfully manipulates LLM output through the full pipeline

Out of scope / expected limitations (see the README's Limitations section for the full list):
- The DeBERTa classifier and regex patterns are tuned for the resume-screening use case demonstrated in this repo and are not claimed to generalize to arbitrary domains — reduced recall on out-of-domain injection styles is a known, documented limitation, not a vulnerability report.
- The experimental "V5" modules (`multilang_detector`, `zeroshot_detector`, etc.) are not wired into the production pipeline; issues specific to them are lower priority.

## Response

This is a research project maintained outside of full-time work, so response times may vary. We'll acknowledge reports as soon as possible and aim to provide a timeline for a fix or public disclosure.
