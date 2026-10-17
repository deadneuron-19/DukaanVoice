# DukaanVoice

DukaanVoice is a backend-first voice-ordering MVP for Indian neighbourhood grocery stores. The project follows a workflow-driven design: customer audio/text order -> transcript -> validated extraction -> catalogue matching -> confirmation -> persisted order.

## Implemented status

The foundation, deterministic text-order workflow, FastAPI API, and LLM integration boundary are implemented. `LLMClient` supports LangChain with the OpenAI provider and validates structured output. Gnani request wiring remains intentionally blocked until the official Prisma/Timbre API contract can be verified.

## Architecture

- `src/dukaanvoice/` contains the application package.
- `core/` holds configuration, settings, logging, and exceptions.
- `schemas/` defines validated contracts for API, order, and LLM outputs.
- `domain/` defines enums and domain entities.
- `repositories/` provide catalogue and order persistence abstractions using JSON as the initial storage mechanism.
- `integrations/` isolates provider SDKs for LLM and Gnani calls.
- `chains/` handles LLM tasks with typed inputs and outputs.
- `services/` contains deterministic pricing, matching, inventory, and workflow logic.
- `api/` contains FastAPI routes and dependency wiring.

## Prerequisites

- Python 3.12+
- Pip or venv
- Optional Docker Desktop for local container runs
- Optional real Gnani credentials for provider-backed voice features

## Virtual environment setup (PowerShell)

```powershell
cd C:\Users\mukes\OneDrive\Desktop\DukaanVoice
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Environment configuration

Copy `.env.example` to `.env` and update the values for your environment.

```powershell
Copy-Item .env.example .env
```

The app loads environment variables through `pydantic-settings`. Missing required values fail at startup with explicit configuration errors.

## Seed data

```powershell
python scripts\seed_data.py
```

## Run the FastAPI server

```powershell
$env:PYTHONPATH = "src"
python -m uvicorn dukaanvoice.main:app --host 0.0.0.0 --port 8000 --reload
```

In VS Code, use **Terminal → Run Task → Start DukaanVoice** to start the API and web app together. The frontend development server proxies `/api` requests to `http://127.0.0.1:8000`, so the browser does not need a separately exposed API URL.

## Run the frontend (second PowerShell window)

The React + TypeScript frontend lives in `frontend/`. The Vite dev server listens on `http://127.0.0.1:3000`; its `/api` proxy forwards requests to the local backend at `http://127.0.0.1:8000`. Set `VITE_API_PROXY_TARGET` to change the backend target during development.

```powershell
cd C:\Users\mukes\OneDrive\Desktop\DukaanVoice\frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Build and test the frontend:

```powershell
npm run test
npm run build
```

For a deployed frontend, set `VITE_API_BASE_URL` to the API origin or relative API path before building. Do not put provider credentials in frontend environment variables; Vite variables are public in the browser bundle.

## Run tests

```powershell
pytest
```

## Text-order workflow

In the default `LLM_PROVIDER=mock` development mode, text orders use deterministic matching against active catalogue names and aliases. Unknown or ambiguous product names request clarification rather than inventing a product. For model-based extraction, set `LLM_PROVIDER=openai` and `LLM_API_KEY`. Start the server with the command above, then submit an order:

```powershell
$headers = @{ "Idempotency-Key" = "order-create-demo-001" }
$body = @{
  session_id = "customer-session-001"
  transcript = "2 packets of Amul milk"
  language = "en"
} | ConvertTo-Json
$order = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/orders/text -Headers $headers -ContentType "application/json" -Body $body
$order
```

If the response is `needs_clarification`, choose one of the returned catalogue candidates through `POST /orders/clarify`. Review the generated totals, then confirm explicitly:

```powershell
$confirmHeaders = @{ "Idempotency-Key" = "order-confirm-demo-001" }
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/orders/$($order.order.order_id)/confirm" -Headers $confirmHeaders
```

Confirmation checks stock and price again. JSON writes are safe for this single-process MVP only; do not run multiple workers against the JSON data directory.

## Mock mode

For local development without real API credentials, keep `DEVELOPMENT_MOCK_MODE=true` in `.env` and set `LLM_PROVIDER=mock`. Text order entry uses deterministic catalogue matching; it does not fabricate an LLM answer or claim real model inference. Speech transcription and synthesis remain unavailable unless a verified speech integration is configured. Tests inject fake clients/models and make no paid provider calls.

## Real Gnani configuration

The real Gnani adapter is not enabled yet. The public material reviewed did not document Prisma/Timbre API endpoints, authentication, request formats, SDK/API versions, or audio constraints. Do not set credentials expecting a provider call: the client fails explicitly rather than guessing a wire contract. Once Gnani provides official integration documentation, wire it through the `GnaniTransport` boundary and add credential-gated integration tests.

## Current limitations

- JSON persistence is intentionally MVP-friendly and is not a multi-worker transactional database.
- Real LLM inference requires `LLM_PROVIDER=openai` and `LLM_API_KEY`.
- Real Gnani speech inference is blocked pending the official API request contract.
- Voice routes report 501 until Gnani's official API request contract is verified.
- JSON files do not provide cross-process transactions. Use a single application process for this MVP.
- The frontend is available as an MVP; accounts/access control and production database persistence are not implemented.
- Browser recordings are captured locally but cannot be uploaded because the backend voice endpoint has no verified audio-upload contract.
- Local browser recording is capped at 20 MiB as a client-side safety limit; this is not a promise about the backend's configurable upload limit.

## Next recommended tasks

1. Complete and test the real Gnani adapter after obtaining official API documentation.
2. Add automated evaluation metrics and improve workflow coverage with real-provider evaluation data.
3. Add account/access controls before exposing order history or shopkeeper data publicly.
