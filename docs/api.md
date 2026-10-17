# API Overview

Interactive OpenAPI documentation is available at `/docs`.

## Implemented endpoints

| Method | Path | Behavior |
|---|---|---|
| `GET` | `/health` | Application liveness status |
| `GET` | `/products` | Active catalogue |
| `GET` | `/products/{product_id}` | One product, or 404 |
| `GET` | `/orders` | Persisted orders |
| `GET` | `/orders/{order_id}` | One order, or 404 |
| `POST` | `/orders/text` | Extract and validate text order; requires `Idempotency-Key`; returns clarification or an awaiting-confirmation summary |
| `POST` | `/orders/clarify` | Resolve a pending product/quantity clarification |
| `POST` | `/orders/{order_id}/confirm` | Recheck stock and price, persist confirmation, and decrement inventory; requires `Idempotency-Key` |
| `POST` | `/orders/{order_id}/cancel` | Cancel an order before confirmation |
| `PATCH` | `/orders/{order_id}/items/{product_id}` | Correct a draft item quantity |
| `DELETE` | `/orders/{order_id}/items/{product_id}` | Remove a draft item |
| `GET` | `/sessions/{session_id}` | Persisted conversation state, or 404 |
| `POST` | `/voice/transcribe` | Explicit 501 until Gnani Prisma's official API contract is verified |
| `POST` | `/voice/synthesize` | Explicit 501 until Gnani Timbre's official API contract is verified |

All responses include an `X-Correlation-ID`. Clients may supply this header to preserve a request ID across services. CORS origins are configured using `ALLOWED_ORIGINS`.

## PowerShell examples

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/products
Invoke-RestMethod http://127.0.0.1:8000/orders

$headers = @{ "Idempotency-Key" = "order-create-demo-001" }
$body = @{
  session_id = "customer-session-001"
  transcript = "2 packets of Amul milk"
  language = "en"
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/orders/text -Headers $headers -ContentType "application/json" -Body $body
```

When `LLM_PROVIDER=mock` (the local-development default), text orders use deterministic, catalogue-constrained extraction: only active catalogue names and aliases are recognized, and unknown or ambiguous items require clarification. This path does not call an LLM or claim language-model inference. To use model-based extraction, configure a supported real provider and its credentials. A returned order remains `awaiting_confirmation` until the customer calls the confirm endpoint. Confirmation rechecks current catalogue price and stock before persisting inventory changes.

JSON writes are atomic per file, while order and inventory updates span separate files. The application serializes updates within one process and rolls back inventory if the order write fails. A process crash between the two writes or multiple worker processes is not transactionally safe; run the JSON MVP as a single process and migrate to a transactional database before multi-worker production use.
