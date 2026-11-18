# SafeHer — Known Limitations & Honest Operating Boundaries

**Document Version:** 1.0.0  
**Status:** Living Document  

---

## 1. Safety & System Realities

SafeHer is an emergency assistance and personal safety tool, not a bulletproof guarantee of physical protection or immediate law-enforcement intervention. The following limitations are documented transparently for users, developers, and institutional stakeholders:

1. **Connectivity Dependency:**
   - Real-time location streaming and server-side notifications require an active cellular data or Wi-Fi connection.
   - When network connectivity is unavailable, the application cannot transmit location updates to remote servers or contacts; it can only activate on-device native fallbacks (direct 112 hardware dialing and native SMS composing).
2. **Emergency Services (112) Integration:**
   - SafeHer does not currently have a direct programmatic API integration with the Indian ERSS 112 emergency dispatch system.
   - The app provides a direct-dial 112 link that opens the device's native dialer with one tap. Users must confirm the call via their phone interface.
3. **Web Browser Background Constraints:**
   - In the PWA (web browser) environment, browsers enforce strict battery-saving restrictions on background geolocation and persistent WebSockets. Background tracking in web browsers will suspend if the tab is inactive or screen locked. Continuous background tracking requires the upcoming native mobile application (Phase 10).
4. **Accuracy of OpenStreetMap Data:**
   - OpenStreetMap facility listings (police stations, hospitals, pharmacies) are community-curated and may be outdated or incomplete in rural or developing localities.
   - Every facility displayed in the UI includes its verification status and data source timestamp. Unverified facilities are explicitly labeled as `Unverified`.
5. **SMS Delivery SLA:**
   - SMS delivery times depend on telecom operator gateways, DLT scrubbing, and signal strength. SafeHer tracks delivery status truthfully and reports when an SMS is pending or unacknowledged.
