# Architecture Decisions

## JSON-first persistence

JSON was selected as the initial persistence layer for simplicity and testability. Repository interfaces are designed to make future replacement with PostgreSQL straightforward.

## Decimal-based pricing

All monetary calculations use `Decimal` to avoid floating-point drift in pricing and total calculations.

## Strict provider boundaries

LLM and speech-provider SDK imports are isolated to dedicated integration modules. No route or service should call providers directly.

## Explicit mock mode

Mock mode is opt-in and clearly flagged in the configuration model so the application does not claim real inference without credentials.

## Gnani integration documentation gap

The official [Gnani website](https://gnani.ai/) reviewed during Phase 3 describes multilingual speech capabilities but did not provide the Prisma/Timbre API request contract, authentication scheme, SDK version, or audio constraints. No provider endpoint, header, model identifier, or payload has been guessed. `GnaniClient` validates local audio and exposes a normalized transport boundary for tests, but it refuses real inference until an official API contract is available. Explicit mock mode reports inference as unavailable and does not generate fake transcripts or audio.

## LLM provider scope

Phase 3 wires LangChain's OpenAI chat integration behind `LLMClient`. Provider-specific construction and invocation remain inside this module. Tests inject fake LangChain-compatible models. Local mock mode reports inference unavailable rather than returning success-shaped fabricated results.
