# SafeHer — Threat Model & Security Architecture

**Document Version:** 1.0.0  
**Status:** DRAFT (Phase 0 Foundation)  
**Standard:** STRIDE Methodology + Abuse/Coercion Analysis  

---

## 1. Context & Adversary Profiles

Women's safety platforms operate under a threat landscape fundamentally distinct from standard enterprise SaaS. In addition to conventional cybercriminals, adversaries frequently include **intimate partners, family members, acquaintances, stalkers, and rogue workplace/campus authorities**.

### Adversary Personas

| Adversary | Motivation | Capabilities & Access |
| :--- | :--- | :--- |
| **Coercive Partner / Stalker** | Covert surveillance, psychological control, physical intimidation. | Physical access to unlocked device, knowledge of user's personal details (DOB, phone, schedule), social pressure to share location. |
| **Malicious Contact** | Intercepting real-time movements, harassing user or contacts. | Designated as a trusted contact initially, or brute-forcing emergency token links. |
| **Rogue Org Coordinator** | Spying on students/employees, stalking individuals across campus. | Institutional admin privileges, ability to view departmental roster. |
| **Credential Stuffer / Botnet** | Account takeover, extortion, SMS gateway exhaustion (telephony denial of service). | Automated HTTP tools, leaked password databases, proxy networks. |
| **Vandal / Spammer** | Degrade trust in community safety reports, flood map with false hazards. | Scripted account generation, bulk submission of fabricated incidents. |

---

## 2. STRIDE Threat Analysis

### 2.1. Spoofing Identity
- **Threat 1.1:** Attacker spoofing SMS OTP during registration or login to hijack account.  
  *Mitigation:* Strict rate-limiting (3 OTPs / 10 minutes per IP/number), Argon2id password hash, constant-time token comparison, progressive lockouts, secure session binding.
- **Threat 1.2:** Attacker falsifying emergency coordinate updates (GPS spoofing).  
  *Mitigation:* Server validation of speed/teleportation anomalies, logging sensor metadata (horizontal accuracy, altitude, timestamp coherence), flagging impossible transitions.

### 2.2. Tampering with Data
- **Threat 2.1:** Modifying emergency incident state or suppressing notifications in transit.  
  *Mitigation:* TLS 1.3 in transit; transactional outbox pattern on Postgres ensures persistent, un-suppressible alert logging; cryptographic message signatures on outbound webhooks.
- **Threat 2.2:** Tampering with audit logs or moderation decisions.  
  *Mitigation:* Write-only / append-only audit log tables in PostgreSQL; restricted database role permissions preventing `UPDATE` or `DELETE` on audit traces.

### 2.3. Repudiation
- **Threat 3.1:** Organization admin denying unauthorized access to an emergency report.  
  *Mitigation:* Comprehensive audit logging recording timestamp, admin user ID, client IP, user agent, target user ID, and justification reason for every record view.
- **Threat 3.2:** User denying initiation of an SOS alert.  
  *Mitigation:* Immutable incident records with signed device session tokens and network timestamps.

### 2.4. Information Disclosure (Highest Risk)
- **Threat 4.1:** Eavesdropping on live location sharing links.  
  *Mitigation:* Ephemeral URLs with 256-bit cryptographically secure tokens; tokens stored exclusively as SHA-256 hashes at rest; strict expiration (TTL 1–24 hours max); instant one-tap revocation.
- **Threat 4.2:** Leakage of harassment victims' home or commute locations via community reports.  
  *Mitigation:* Automatic spatial perturbation/fuzzing ($100-300\text{m}$) on public maps; reporter UUIDs permanently excluded from public serialization schemas.
- **Threat 4.3:** Multi-tenant data leakage (College A viewing College B's incident feed).  
  *Mitigation:* Strict tenant scoping by `org_id` in repository layer + PostgreSQL Row Level Security (RLS).

### 2.5. Denial of Service (DoS)
- **Threat 5.1:** Exhausting SMS credits or bombarding emergency contacts with fake triggers.  
  *Mitigation:* Rate limiting on incident creation (per-user and per-device), client-side cancellation countdown (5–10 seconds), DLT-registered transactional SMS templates, circuit breaker on third-party SMS gateways.
- **Threat 5.2:** Flooding WebSocket live location endpoints.  
  *Mitigation:* Maximum connection limits per user session, token verification before WebSocket handshake, message rate limiting.

### 2.6. Elevation of Privilege
- **Threat 6.1:** BOLA / IDOR attack (changing incident ID in `/api/v1/incidents/{id}` to access another user's emergency telemetry).  
  *Mitigation:* Centralized object-level permission enforcement in service layer; automatic authorization check verifying `incident.user_id == current_user.id` or caller is verified contact of this incident.

---

## 3. Dedicated Abuse & Anti-Coercion Defenses

1. **Persistent Visual Sharing Indicator:** Whenever location sharing or journey monitoring is active, an unambiguous, high-visibility status bar persists across the entire UI.
2. **Periodic Sharer Reminders:** When active location sessions exceed 1 hour, automatic local reminders notify the user that their location is currently accessible.
3. **Safety Check Screen ("Who Can See Me?"):** A dedicated dashboard view showing all active sharing links, verified contacts with access permissions, and connected devices, with a single-tap **"Kill All Active Shares"** nuclear button.
4. **Targeted Invitation Throttling:** Anti-stalking heuristic flags and throttles accounts that attempt to add dozens of non-reciprocated contacts or repeatedly spam a single target phone number.
5. **No Stealth Surveillance by Organizations:** SafeHer Organization explicitly prohibits background tracking. Institutional coordinators can only view location when an active SOS has been initiated with the organization selected as an escalation partner.

---

## 4. Regulatory & Compliance Baseline (India)

### 4.1. Digital Personal Data Protection Act, 2023 (DPDPA)
- **Consent Architecture:** Granular, unambiguous, revocable consent recorded in `consent_records` with versioned privacy notices.
- **Purpose Limitation:** Location telemetry collected during SOS or journeys is never reused for marketing, advertising, or cross-tenant analytics.
- **Right to Erasure:** Complete account erasure workflow removes all personal credentials and cascades to anonymize historical incident reports after mandatory legal hold periods.

### 4.2. CERT-In Direction & IT Act
- System and security logs retained in structured, synchronized format with NTP time stamps.
- Security incident response plan documented in `docs/RUNBOOK.md` with explicit 6-hour reporting criteria for critical cybersecurity incidents.
