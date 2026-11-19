# AI-Powered Website Link Analysis API

FastAPI service that analyzes a submitted website URL and returns structured AI insights.

## Features
- URL validation with SSRF protections
- Website extraction (HTTPX + BeautifulSoup)
- OpenAI structured analysis (5 sections)
- Pydantic validation
- Comprehensive tests

## Technologies
Python 3.x, FastAPI, Uvicorn, OpenAI, HTTPX, BeautifulSoup4, Pydantic, python-dotenv, Pytest

## Architecture
See project tree in task spec.

## Installation
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Environment
Copy `.env.example` to `.env` and set `OPENAI_API_KEY`, `OPENAI_MODEL`.

## Run
```
uvicorn app.main:app --host 0.0.0.0 --port 4000
```
Swagger: http://localhost:4000/docs

## Endpoint
POST /link-analysis
Request: {"url":"https://example.com"}

## Tests
```
pytest
```

## LLM Provider Comparison (research date: 2026-11-19)
| Provider | Model | Input $/1M | Output $/1M | Context | Structured JSON | Speed | Notes |
|---|---|---|---|---|---|---|---|
| OpenAI | gpt-4.1-mini | see official | see official | large | yes | fast | primary |
| Google Gemini | gemini-2.5-flash | see official | see official | large | yes | fast | alternative |
| Anthropic Claude | claude-sonnet-4 | see official | see official | large | yes | medium | alternative |

Sources:
- https://openai.com/api/pricing
- https://ai.google.dev/pricing
- https://www.anthropic.com/pricing

Cost estimate: assuming 4,000 input tokens and 2,000 output tokens per analysis, cost depends on model pricing; with gpt-4.1-mini approximate a few cents per analysis. Caching, cleaning, token limits and prompt optimization reduce costs.

## Security
.env ignored, no secrets committed, SSRF protections.

## Deployment
Set env vars, run uvicorn behind reverse proxy.

## Security Hardening Notes
- DNS rebinding: URL validation resolves DNS and validates public IPs, and redirect destinations are revalidated. However, the HTTP client may resolve DNS again at connection time, so DNS rebinding is not fully eliminated. For full protection, use an SSRF-safe HTTP client/proxy or network egress controls that pin resolved IPs.
- Streaming size enforcement stops downloads over 2 MB.
- TLS verification remains enabled.
