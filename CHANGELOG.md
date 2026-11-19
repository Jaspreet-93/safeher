# Changelog

All notable changes to the SafeHer platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Phase 2 Backend (Contacts, Smart SOS Core, Outbox & Chaos Verification)
- Emergency Contacts engine (`emergency_contacts`) with priority ordering, verification tokens, and scoped location permissions.
- Public Contact Verification endpoint (`/contacts/verify/{token}`) allowing contacts to accept or decline being an emergency responder.
- Smart SOS incident state machine: `created → active → (cancelled | resolved | escalated)` with 5-second grace window cancellation.
- Strict client-driven idempotency (`X-Idempotency-Key`): prevents duplicate incidents and SMS floods during panic multi-taps.
- Transactional Outbox pattern: atomic database persistence of incidents and outbox notification items (`emergency_notifications`).
- `MockSmsProvider` with honest `[MOCK]` logging (Rule 5 compliance) and controllable fault-injection levers for chaos resilience tests.
- Contact emergency acknowledgement endpoint (`/incidents/ack/{token}`) with 112 emergency fallback and location links.
- Comprehensive automated test suite: 17/17 tests passing including unit and chaos/reliability tests.

### Added - Phase 1 (Auth, Consent Records & RBAC)
- Argon2id password hashing implementation (`argon2-cffi`) with `t=3, m=65536, p=4`.
- Short-lived JWT access tokens and opaque rotating refresh tokens with SHA-256 hash persistence.
- Automatic refresh token reuse & theft detection: revoking all active sessions if an already-rotated token is presented.
- Brute-force & credential stuffing defense: 10 consecutive failed attempts triggers 15-minute account lockout (`HTTP 423 Locked`).
- Generic authentication error messages to prevent user enumeration.
- DPDPA 2023 consent records engine (`consent_records`) storing timestamp, IP, and user agent for auditability.
- Role-Based Access Control (RBAC) dependency (`require_role`) supporting `user`, `coordinator`, `org_admin`, and `admin`.
- User and profile endpoints (`/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/users/me`, `/consent/history`).
- Unit and security test suite in `tests/unit/test_auth.py` verifying lockout, rotation, theft detection, and RBAC (11/11 passing).
- React frontend components: `AuthContext`, `LoginForm`, `RegisterForm` with password strength meter, `ConsentNoticeModal`, `AuthPage`, and `ProfilePage`.

### Added - Phase 0 (Foundations)
- Comprehensive system architecture documentation with Mermaid diagrams (`docs/ARCHITECTURE.md`).
- STRIDE threat model and anti-coercion/abuse analysis (`docs/THREAT_MODEL.md`).
- Architecture Decision Records ADR 001 through ADR 005 (`docs/DECISIONS.md`).
- Known limitations and operational realities documentation (`docs/KNOWN_LIMITATIONS.md`).
- Future enhancements and post-MVP backlog (`docs/BACKLOG.md`).
- Monorepo directory structure for backend, frontend, docs, and infra.
- Multi-container Docker Compose configuration (`docker-compose.yml`) orchestrating FastAPI, React, PostgreSQL/PostGIS, and Redis.
- Automated CI pipeline workflow (`.github/workflows/ci.yml`).
- Centralized environment configuration template (`.env.example`).
