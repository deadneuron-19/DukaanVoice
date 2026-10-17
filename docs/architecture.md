# Architecture

This project is designed around clean separation of concerns and a deterministic domain layer. The long-term intent is to support JSON persistence first and swap to relational storage later without changing business logic.

## Core organization

- `core/`: configuration, settings validation, structured logging, exceptions, and security defaults.
- `domain/`: value objects and enums that represent order and product state.
- `repositories/`: JSON-backed persistence interfaces and implementations.
- `services/`: deterministic logic for matching, pricing, inventory, session flow, and order lifecycle.
- `integrations/`: external provider boundaries for LLM and speech models.
- `chains/`: LangChain-based typed prompts used only for LLM-dependent tasks.
- `api/`: FastAPI routes, dependency injection, and exception handling.

## Design principles

- Provider SDK code stays inside integration modules.
- Business logic never trusts LLM-generated IDs.
- Money is calculated with `Decimal` and not via LLM output.
- Mock mode is explicit and clearly separated from real providers.
