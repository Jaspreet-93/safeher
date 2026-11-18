# Changelog

All notable changes to the SafeHer platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
