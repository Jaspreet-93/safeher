# SafeHer — Architecture Decision Records (ADR)

**Document Version:** 1.0.0  
**Status:** Living Document  

---

## ADR 001: Monorepo Architecture

- **Status:** ACCEPTED
- **Date:** 2026-11-19
- **Context:** SafeHer comprises a React web application (PWA), a FastAPI backend, background workers, an eventual React Native mobile app, and shared ML/data models. We need unified versioning, atomic commits, seamless type sharing, and single-command local development.
- **Alternatives Considered:**
  1. *Multi-repo (separate repos for frontend, backend, mobile, docs):* Increases synchronization friction, makes cross-boundary breaking changes difficult to manage, and complicates CI orchestration in early stages.
  2. *Monorepo with Turborepo / Nx:* Great for JS-only repos, but introduces overhead when orchestrating heterogeneous stacks (Python + TypeScript).
- **Decision:** Standard structured monorepo (`backend/`, `frontend/`, `mobile/`, `docs/`, `infra/`, `ml/`) managed at the root with standard scripts, Docker Compose, and GitHub Actions.
- **Consequences:** Simplified end-to-end testing, centralized documentation, atomic feature branches, streamlined CI matrix.

---

## ADR 002: Backend Framework — FastAPI + SQLAlchemy 2.0 (Async) + Pydantic v2

- **Status:** ACCEPTED
- **Date:** 2026-11-19
- **Context:** The backend must handle high-concurrency real-time location bursts and emergency triggers while enforcing strict data validation and generating accurate OpenAPI schemas.
- **Alternatives Considered:**
  1. *Django + Django REST Framework:* Heavyweight, synchronous ORM by default, higher memory footprint, less ergonomic WebSocket/async support.
  2. *Node.js / Express or NestJS:* Strong concurrency, but weaker ecosystem for GIS/geospatial computations and Python-based ML/data processing.
  3. *Go:* Ultra-fast, but slower iteration velocity and fewer out-of-the-box libraries for complex multilingual Indic NLP and rapid GIS transformations.
- **Decision:** Python 3.10+ / 3.12 with FastAPI, Pydantic v2, and async SQLAlchemy 2.0 with Alembic.
- **Consequences:** Asynchronous I/O for database and Redis operations, automated OpenAPI documentation for frontend client generation, zero-friction integration with scientific Python libraries in future phases.

---

## ADR 003: Frontend Technology — React 18+ (Vite) + TypeScript + Tailwind CSS

- **Status:** ACCEPTED
- **Date:** 2026-11-19
- **Context:** The initial web client must be mobile-first, performant on 3G/4G connections, WCAG AA accessible, installable as a PWA, and easily maintainable.
- **Alternatives Considered:**
  1. *Next.js (App Router):* Strong SSR, but higher deployment complexity for containerized setups and unnecessary server rendering overhead for an authenticated, interactive single-page app.
  2. *Vue / Nuxt:* Strong framework, but React allows direct component architecture and logic sharing with the upcoming React Native mobile app.
- **Decision:** React with Vite, TypeScript, Tailwind CSS, TanStack Query, React Hook Form, and Zod.
- **Consequences:** Sub-second hot-module reloading in dev, tiny optimized production bundles, strong compile-time type safety matching backend schemas.

---

## ADR 004: Mapping & Spatial Engine — PostgreSQL + PostGIS & Leaflet

- **Status:** ACCEPTED
- **Date:** 2026-11-19
- **Context:** SafeHer requires high-performance spatial indexing (ST_DWithin, GiST indexes) for finding nearby emergency facilities, calculating journey proximity, and fuzzing incident coordinates.
- **Alternatives Considered:**
  1. *MongoDB Geospatial:* Flexible documents, but lacks the robust relational constraints, ACID compliance, and advanced spatial SQL functions of PostGIS.
  2. *Google Maps Platform:* High cost at scale ($7 per 1,000 requests for Places/Directions), proprietary locks, restrictive terms on caching.
- **Decision:** PostgreSQL with PostGIS extension for backend spatial queries; Leaflet + OpenStreetMap tiles for client-side rendering; abstract `GeocodingProvider` and `RoutingProvider` interfaces to enable swappable providers.
- **Consequences:** Free, high-speed spatial calculations natively in the database, predictable zero-cost baseline for dev and early deployment, complete data sovereignty.

---

## ADR 005: Emergency Reliability — Transactional Outbox & Client-Side Offline Outbox

- **Status:** ACCEPTED
- **Date:** 2026-11-19
- **Context:** In emergency scenarios (SOS trigger), network drops, worker crashes, or external SMS gateway hiccups must never lead to lost incidents or phantom "sent" confirmations.
- **Alternatives Considered:**
  1. *Direct API Call to Twilio/SMS Provider within HTTP Request:* Fragile. If the provider takes 4 seconds to respond, the client hangs. If the client disconnects before receiving HTTP 200, it cannot know if the SOS fired.
  2. *Redis Pub/Sub without persistence:* Ephemeral; crashes lead to dropped emergency events.
- **Decision:**
  - Client-side Offline Outbox in IndexedDB: caches pending SOS if offline, continuously retries, and immediately surfaces the native 112 dialer and pre-composed SMS fallback.
  - Server-side Transactional Outbox: records incident and notifications in an atomic PostgreSQL transaction before background workers dispatch to gateways with idempotency keys.
- **Consequences:** Zero lost alerts, truthful UI status reflecting actual gateway delivery receipts, rock-solid failure tolerance.
