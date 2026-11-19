# Changelog

All notable changes to the SafeHer platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Phase 3 (Real Notification Providers, Multi-Tier Failover & Carrier DLR Webhooks)
- Indian DLT-compliant SMS adapter (`DLTSmsProvider`) adhering to TRAI regulations with mandatory Sender ID (`SAFEHR`) and pre-registered template validation (`SOS_ALERT`, `CONTACT_VERIFY`).
- Robust Indian mobile number sanitizer and validator accepting `+91`, `91`, and standard 10-digit formats with prefix sanity checking.
- Multi-tier emergency failover engine (`NotificationRouter`):
  - **Tier 1:** Primary SMS Gateway (Fast2SMS / Telecom DLT).
  - **Tier 2:** Secondary SMS Gateway (Twilio / Alternate Route) with automatic trigger upon Tier 1 failure.
  - **Tier 3:** High-priority Email & Push fallback if carrier gateways fail.
- Delivery Receipt (DLR) Webhook (`POST /api/v1/webhooks/sms/dlr`) secured with HMAC-SHA256 signature verification (`X-Webhook-Signature`) to prevent message status forgery or spoofing.
- Transactional Outbox integration: `OutboxService` automatically routes notifications through `NotificationRouter` and persists carrier message identifiers.
- Frontend Carrier Delivery Audit Trail Modal (`DeliveryReceiptsModal`) allowing users and responders to inspect carrier transaction IDs, DLR timestamps, and failover diagnostics.
- Rule 5 adherence: All mock providers and dev UI components are prominently tagged `[MOCK]` to never mislead users.
- Automated test suites: `test_notification_providers.py` and `test_failover_engine.py` verifying phone validation, failover ladders, and HMAC webhook security (24/24 tests passing).

### Added - Phase 2 Frontend (UI, Offline Outbox & Contact Ack Viewer)
- `useGeolocation` hook for high-accuracy GPS coordinates, horizontal accuracy, and fresh location timestamps.
- `useOfflineOutbox` hook detecting connectivity loss, queuing SOS incidents locally, displaying fail-loudly warnings ("NOT SENT — NO CONNECTION"), and launching native 112 dialer and pre-formatted emergency SMS.
- `ContactManager` & `AddContactModal` supporting contact creation, priority ranking, and instant copy of consent links.
- `SOSControl` featuring accessible one-thumb trigger, 5-second cancel countdown, and live per-contact delivery receipts feed.
- `EmergencyAckPage` public viewer allowing emergency contacts to review sender coordinates and tap "I Am Responding".
- `ContactVerifyPage` allowing designated contacts to review and consent to being an emergency responder.

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
