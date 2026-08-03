# Ops API Inventory — Clean My Car (Internal / Admin)

| Field | Detail |
|-------|--------|
| **Document type** | API inventory (module → endpoints) for **ops / platform admin**, not the consumer iOS app |
| **Version** | 0.1 |
| **Status** | Draft — for review (not an OpenAPI contract yet) |
| **Source of truth** | [PRD.md](./PRD.md) v1.3; companion to [API_INVENTORY.md](./API_INVENTORY.md) (consumer) |
| **Primary consumer** | Ops UI, internal tools, or scripts (no full ops suite in v1 — PRD O7/O8 Won’t) |
| **Base path (proposed)** | `/api/v1/ops` (separate from consumer `/api/v1` surface) |
| **Swagger UI (local)** | http://localhost:8000/ops/docs — OpenAPI JSON: `/ops/openapi.json` (consumer remains at `/docs`) |
| **Auth model (proposed)** | Ops credentials only (admin JWT, API key, VPN + service account — **not** end-user phone OTP). Exact scheme is a technical design choice. Until auth is implemented, ops routes may be open in local/dev only. |

---

## 1. Purpose & how to read this doc

Consumer APIs assume **master data already exists** in the database (cities, societies, vehicle catalog, city pricing, etc.). Today that data is loaded via **seeds / SQL / migrations**. Ideally it is maintained through an **Ops UI** calling the endpoints listed here.

This document lists **ops-facing APIs** grouped by the **same module numbers** as [API_INVENTORY.md](./API_INVENTORY.md). Where a module has **no ops surface**, that is stated explicitly.

| Column | Meaning |
|--------|---------|
| **ID** | Stable reference (`OPS-LOC-01`, …) — distinct from consumer IDs |
| **Method / path** | Proposed REST under `/api/v1/ops` (names can change in technical design) |
| **Purpose** | What ops needs |
| **Priority** | **M** = Must (needed to run product without ad-hoc DB edits), **S** = Should, **C** = Could, **W** = Won’t (v1) |
| **Master data** | Tables / fields primarily maintained |
| **PRD** | Related PRD requirement IDs |
| **Consumer dependency** | Consumer APIs that break or degrade without this data |

**Not in scope of this doc:** full request/response schemas, error codes, ops auth middleware, full workforce/routing product (PRD Won’t).

**Sibling doc:** [API_INVENTORY.md](./API_INVENTORY.md) — mobile consumer + payment webhooks.

---

## 2. Module map (overview)

Same module grid as the consumer inventory; ops only implements the **catalog, configuration, and field-execution** side.

```text
┌─────────────────────────────────────────────────────────────┐
│              Ops UI / internal tools / scripts              │
├──────────────┬──────────────┬──────────────┬────────────────┤
│ 1. Auth      │ 2. Profile   │ 3. Location  │ 4. Waitlist    │
│ 5. Vehicle   │ 6. Pricing   │ 7. Subscr.   │ 8. Payments    │
│ 9. Dashboard │ 10. Washes   │ 11. Notifs   │ 12. Support    │
│ 13. App meta │ 14. (n/a)    │ 15. Ops core │                │
└──────────────┴──────────────┴──────────────┴────────────────┘
         │ seeds master data + field actions
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Consumer app (read catalogs / user-owned resources only)   │
└─────────────────────────────────────────────────────────────┘
```

| # | Module | Ops owns? | Master data / action summary |
|---|--------|-----------|------------------------------|
| 1 | **Auth & session** | Minimal | Ops operator login (not phone OTP) |
| 2 | **Profile & account** | Support only | Look up / deactivate users (optional) |
| 3 | **Location & eligibility** | **Yes — master** | Cities, societies, service weekdays, active/live flags |
| 4 | **Waitlist** | **Yes — triage** | Read/update waitlist demand status |
| 5 | **Vehicle** | **Yes — master** | Makes, models, size_tier mapping |
| 6 | **Pricing & plans** | **Yes — master** | City pricing, size base, interior add-ons, GST flags |
| 7 | **Subscription** | Light | View / admin override (Should later) |
| 8 | **Payments & billing** | Light | View / reconcile (Should later) |
| 9 | **Dashboard / home** | No consumer BFF | Optional ops overview (Could) |
| 10 | **Washes & schedule** | **Yes — field** | Complete / miss / roster / list washes |
| 11 | **Notifications** | Config / broadcast | Templates, send ops alerts (Could) |
| 12 | **Support & content** | Content + tickets | FAQ, legal, ticket queue (Should/Could) |
| 13 | **App metadata** | Config | Force-update, feature flags, support channels |
| 14 | **Payment webhooks** | Server-only | Not ops UI; gateway → API |
| 15 | **Ops (cross-cutting)** | Meta | Health of ops auth, audit log (Could) |

---

## 3. Master data map (built consumer modules 1–6)

What must exist before consumer APIs work end-to-end. **Seed today → Ops APIs tomorrow.**

| Master data | Tables (current) | Consumed by (examples) | Ops module |
|-------------|------------------|------------------------|------------|
| Active cities | `cities` | LOC-01, waitlist city, pricing city | **3** |
| Live societies + schedule | `societies` | LOC-02/03/05, quote entitlements | **3** |
| Vehicle brands | `vehicle_makes` | VEH-06 | **5** |
| Vehicle models + size | `vehicle_models` | VEH-07, VEH-02 size derivation | **5** |
| City pricing config | `city_pricing` | PRICE-01/02 GST flags | **6** |
| Size base tariffs | `city_size_prices` | PRICE-01/02 | **6** |
| Interior tariffs | `city_interior_prices` | PRICE-01/02 | **6** |
| Waitlist entries | `waitlist_entries` | WAIT-01/02 (user-created; ops triage) | **4** |
| Users / sessions | `users`, `refresh_tokens`, `otp_*` | Auth/profile — **user-owned**, not catalog | **1–2** (support only) |
| User vehicle instance | `vehicles` | VEH-01–04 — **user-owned** | **5** (read/correct only if needed) |

**Implementation status (codebase):** Ops Modules **1** (auth), **2** (users), and **3** (cities/societies) are implemented under `/api/v1/ops/*`. Vehicle catalog (5) and pricing (6) are still seed/SQL until those ops routes land. Consumer error e.g. `pricing_not_found` means Module **6** master data is missing for that city.

---

## 4. Module 1 — Auth & session (ops)

**Goal:** Authenticate **ops operators**, not end customers.

| ID | Method / path | Purpose | Priority | Master data | PRD |
|----|---------------|---------|----------|-------------|-----|
| OPS-AUTH-01 | `POST /ops/auth/login` | Operator login (email/password or SSO TBD) | M | ops principals (future table) | O* |
| OPS-AUTH-02 | `POST /ops/auth/logout` | Invalidate ops session | M | — | — |
| OPS-AUTH-03 | `POST /ops/auth/token/refresh` | Refresh ops access token | S | — | — |
| OPS-AUTH-04 | `GET /ops/auth/me` | Current operator identity + roles | S | — | — |

**Notes**

- **Do not** reuse consumer phone OTP for ops.
- Roles (e.g. `catalog_admin`, `field_ops`, `support`) can gate modules 3–6 vs 10.

**vs consumer Module 1:** Consumer OTP/JWT remains under `/api/v1/auth/*` with no ops CRUD of OTP challenges.

---

## 5. Module 2 — Profile & account (ops)

**Goal:** Support tooling over user accounts (not self-service profile).

| ID | Method / path | Purpose | Priority | Master data | PRD |
|----|---------------|---------|----------|-------------|-----|
| OPS-PROF-01 | `GET /ops/users` | Search users by phone / id | S | `users` (read) | A2, H2 |
| OPS-PROF-02 | `GET /ops/users/{user_id}` | User detail + location flags | S | `users` | A2 |
| OPS-PROF-03 | `POST /ops/users/{user_id}/deactivate` | Force deactivate | C | `users.is_active` | A3 |
| OPS-PROF-04 | `POST /ops/users/{user_id}/reactivate` | Undo soft deactivate | C | `users` | A3 |

**No ops APIs required for MVP catalog seeding.** User rows are created by consumer AUTH-02.

**vs consumer Module 2:** `GET/PATCH /me` stay user-scoped only.

---

## 6. Module 3 — Location & eligibility (ops) — **master data**

**Goal:** Maintain cities and societies so consumer LOC-* works without app releases (PRD L6).

| ID | Method / path | Purpose | Priority | Master data | PRD |
|----|---------------|---------|----------|-------------|-----|
| OPS-LOC-01 | `GET /ops/cities` | List all cities (incl. inactive) | M | `cities` | L1, L6 |
| OPS-LOC-02 | `POST /ops/cities` | Create city | M | `cities` | L1, L6 |
| OPS-LOC-03 | `PATCH /ops/cities/{city_id}` | Update name/state/order/`is_active` | M | `cities` | L6, BR4 |
| OPS-LOC-04 | `GET /ops/cities/{city_id}/societies` | List societies (incl. non-live) | M | `societies` | L2, Q9 |
| OPS-LOC-05 | `POST /ops/cities/{city_id}/societies` | Create society (weekdays, address, serviceable) | M | `societies` | L2, W1, W11 |
| OPS-LOC-06 | `PATCH /ops/societies/{society_id}` | Update society; toggle `is_serviceable`; set 3 weekdays | M | `societies` | L6, BR2 |
| OPS-LOC-07 | `GET /ops/societies/{society_id}` | Society detail (ops view) | S | `societies` | — |

**Notes**

- Consumer **never** sees inactive cities or non-serviceable societies (LOC-02 Option A).
- Exactly **3** `service_weekdays` (0=Mon…6=Sun) for v1.
- Turning a society live is the bridge from waitlist → conversion.

**Consumer dependency:** LOC-01–05 empty or broken without OPS-LOC-*.

---

## 7. Module 4 — Waitlist (ops)

**Goal:** Triage demand when societies are not live (user-created rows).

| ID | Method / path | Purpose | Priority | Master data | PRD |
|----|---------------|---------|----------|-------------|-----|
| OPS-WAIT-01 | `GET /ops/waitlist` | List/filter by city, status, phone, society_name | M | `waitlist_entries` | L4 |
| OPS-WAIT-02 | `GET /ops/waitlist/{entry_id}` | Entry detail | S | `waitlist_entries` | L4 |
| OPS-WAIT-03 | `PATCH /ops/waitlist/{entry_id}` | Update status (`pending`→`contacted`→`converted`/`closed`), notes | M | `waitlist_entries.status` | L4 |
| OPS-WAIT-04 | `GET /ops/waitlist/summary` | Counts by city / status (demand signal) | S | aggregate | L4 |

**Notes**

- Users create entries via consumer WAIT-01; ops does **not** invent demand.
- No master catalog table beyond status workflow.

**Consumer dependency:** WAIT-* work without ops; ops needed to **act** on demand.

---

## 8. Module 5 — Vehicle (ops) — **master data**

**Goal:** Maintain make/model catalog and **ops-defined** `size_tier` (users never pick Small/Medium/Large free-form).

| ID | Method / path | Purpose | Priority | Master data | PRD |
|----|---------------|---------|----------|-------------|-----|
| OPS-VEH-01 | `GET /ops/vehicle-makes` | List makes (incl. inactive) | M | `vehicle_makes` | V1 |
| OPS-VEH-02 | `POST /ops/vehicle-makes` | Create make/brand | M | `vehicle_makes` | V1 |
| OPS-VEH-03 | `PATCH /ops/vehicle-makes/{make_id}` | Rename, reorder, deactivate | M | `vehicle_makes` | V1 |
| OPS-VEH-04 | `GET /ops/vehicle-makes/{make_id}/models` | List models (incl. inactive) | M | `vehicle_models` | V1 |
| OPS-VEH-05 | `POST /ops/vehicle-makes/{make_id}/models` | Create model + **size_tier** | M | `vehicle_models` | V1, V4 |
| OPS-VEH-06 | `PATCH /ops/vehicle-models/{model_id}` | Update name, size_tier, active | M | `vehicle_models` | V1 |
| OPS-VEH-07 | `GET /ops/users/{user_id}/vehicle` | Inspect user’s registered vehicle | S | `vehicles` (read) | V1 |
| OPS-VEH-08 | `PATCH /ops/users/{user_id}/vehicle` | Correct model/plate if mis-registered | C | `vehicles` | V2 |

**Notes**

- Changing a model’s `size_tier` affects **new** vehicle assignments; existing `vehicles.size_tier` is a snapshot (document reprice policy with Module 7).
- Size tier labels (PRICE/VEH-05 consumer) stay static enums: small/medium/large.

**Consumer dependency:** VEH-06/07 empty without catalog; VEH-02 fails if no active models.

---

## 9. Module 6 — Pricing & plans (ops) — **master data**

**Goal:** Maintain city tariffs so PRICE-01/02 do not return `pricing_not_found`.

| ID | Method / path | Purpose | Priority | Master data | PRD |
|----|---------------|---------|----------|-------------|-----|
| OPS-PRICE-01 | `GET /ops/cities/{city_id}/pricing` | Full ops view of city pricing (incl. inactive) | M | `city_pricing`, size/interior rows | S1, S8, BR3 |
| OPS-PRICE-02 | `PUT /ops/cities/{city_id}/pricing` | Upsert city pricing config (currency, GST flags, rate, active) | M | `city_pricing` | S8, S9 |
| OPS-PRICE-03 | `PUT /ops/cities/{city_id}/pricing/size-prices` | Replace/upsert base prices by size_tier (paise) | M | `city_size_prices` | S1, BR3 |
| OPS-PRICE-04 | `PUT /ops/cities/{city_id}/pricing/interior-prices` | Replace/upsert add-ons for freq 0/1/2/4 (paise) | M | `city_interior_prices` | S1 |
| OPS-PRICE-05 | `POST /ops/pricing/quote` | Same quote engine as consumer, for ops preview | S | read-only compute | S2, S10 |
| OPS-PRICE-06 | `GET /ops/pricing/missing` | Cities active but without pricing (ops checklist) | S | join cities × pricing | L6 |

**Notes**

- Amounts in **paise**; interior frequencies **0, 1, 2, 4** only.
- Consumer `POST /pricing/quote` can stay public/read; ops PUT is the **write** path that “fixes” `pricing_not_found`.
- Prefer atomic PUT of full matrix to avoid partial incomplete cities.

**Consumer dependency:** PRICE-01/02 require OPS-PRICE-02–04 for each sellable city.

---

## 10. Module 7 — Subscription (ops)

**Goal:** Support and exception handling once Module 7 exists on the consumer side.

| ID | Method / path | Purpose | Priority | Master data | PRD |
|----|---------------|---------|----------|-------------|-----|
| OPS-SUB-01 | `GET /ops/subscriptions` | Search by user/phone/status/society | S | subscriptions (future) | S4 |
| OPS-SUB-02 | `GET /ops/subscriptions/{id}` | Detail | S | — | S4 |
| OPS-SUB-03 | `POST /ops/subscriptions/{id}/cancel` | Admin cancel (policy) | C | — | S7 |
| OPS-SUB-04 | `POST /ops/subscriptions/{id}/extend` | Rare goodwill extension | W | — | — |

**v1 note:** No ops APIs until consumer subscription tables exist. **None required for modules 1–6 master data.**

---

## 11. Module 8 — Payments & billing (ops)

| ID | Method / path | Purpose | Priority | Master data | PRD |
|----|---------------|---------|----------|-------------|-----|
| OPS-PAY-01 | `GET /ops/payments` | Search payments / intents | S | payments (future) | P3 |
| OPS-PAY-02 | `GET /ops/payments/{id}` | Detail + gateway refs | S | — | P3 |
| OPS-PAY-03 | `POST /ops/payments/{id}/reconcile` | Manual mark captured (exceptions) | C | — | P4 |

**v1 note:** No ops APIs for modules 1–6. Webhooks (consumer inventory Module 14) are server-to-server, not ops UI.

---

## 12. Module 9 — Dashboard / home (ops)

**No dedicated ops BFF required for consumer DASH-01.**

| ID | Method / path | Purpose | Priority | Master data | PRD |
|----|---------------|---------|----------|-------------|-----|
| OPS-DASH-01 | `GET /ops/overview` | Counts: cities, live societies, open waitlist, active subs | C | aggregates | O6 |

Optional later; not master data.

---

## 13. Module 10 — Washes & schedule (ops) — **field actions**

**Goal:** Keep consumer completed/pending truthful (PRD W7, W9). Carried from consumer inventory Module 15 into this ops-first doc.

| ID | Method / path | Purpose | Priority | Master data | PRD |
|----|---------------|---------|----------|-------------|-----|
| OPS-WASH-01 | `POST /ops/washes/{wash_id}/complete` | Mark exterior (± interior) complete | M | washes (future) | W7, O4, BR10 |
| OPS-WASH-02 | `POST /ops/washes/{wash_id}/miss` | Mark missed + next-day retry | M | washes | W9, O5, BR11 |
| OPS-WASH-03 | `GET /ops/societies/{society_id}/roster` | Subscribers/vehicles due on a date | S | roster query | O6 |
| OPS-WASH-04 | `GET /ops/washes` | Filter by society/date/status | S | washes | O4–O6 |
| OPS-WASH-05 | `POST /ops/washes/generate` | Materialise schedule for a month/society | C | washes | W1, BR2 |

**Notes**

- Not master catalog; **transactional** field data once subscription/washes exist.
- No consumer write APIs for complete/miss.

**vs modules 1–6:** Not needed to exercise location/vehicle/pricing APIs; **required** before dashboard wash counts move.

---

## 14. Module 11 — Notifications (ops)

| ID | Method / path | Purpose | Priority | Master data | PRD |
|----|---------------|---------|----------|-------------|-----|
| OPS-NOTIF-01 | `GET /ops/notification-templates` | List templates | C | config | N1–N5 |
| OPS-NOTIF-02 | `PUT /ops/notification-templates/{key}` | Edit copy | C | config | — |
| OPS-NOTIF-03 | `POST /ops/notifications/send` | Manual send (support) | C | — | — |

**No ops APIs for modules 1–6 master data.** Consumer device token APIs remain user-scoped.

---

## 15. Module 12 — Support & content (ops)

| ID | Method / path | Purpose | Priority | Master data | PRD |
|----|---------------|---------|----------|-------------|-----|
| OPS-SUP-01 | `PUT /ops/content/faq` | Publish FAQ entries | S | content store | H1 |
| OPS-SUP-02 | `PUT /ops/content/legal/{doc_type}` | Publish terms/privacy/cancellation | S | legal versions | H3 |
| OPS-SUP-03 | `GET /ops/support/tickets` | Ticket queue | S | tickets (future) | H2 |
| OPS-SUP-04 | `PATCH /ops/support/tickets/{id}` | Update status / reply | S | tickets | H2 |

**Not required for modules 1–6 pricing/location/vehicle catalogs.**

---

## 16. Module 13 — App metadata (ops)

| ID | Method / path | Purpose | Priority | Master data | PRD |
|----|---------------|---------|----------|-------------|-----|
| OPS-APP-01 | `GET /ops/app/config` | Read remote config | S | app config | — |
| OPS-APP-02 | `PUT /ops/app/config` | Min iOS version, force-update, feature flags, support WhatsApp | S | app config | — |

**Not required for modules 1–6 master data.**

---

## 17. Module 14 — Payment webhooks

**No ops UI APIs.** Gateway → `POST /api/v1/webhooks/payments/{provider}` (consumer inventory WH-01). Ops may **read** payment state via Module 8 ops list when built.

| Status | Detail |
|--------|--------|
| Ops endpoints | **None** |
| Related | Consumer inventory §16 |

---

## 18. Module 15 — Ops platform (cross-cutting)

| ID | Method / path | Purpose | Priority | Master data | PRD |
|----|---------------|---------|----------|-------------|-----|
| OPS-PLAT-01 | `GET /ops/health` | Ops API health | C | — | — |
| OPS-PLAT-02 | `GET /ops/audit` | Audit log of catalog changes | C | audit (future) | — |
| OPS-PLAT-03 | `POST /ops/seed/preview` | Dry-run bulk import (cities/models/prices) | C | bulk | L6 |

Thin platform helpers only; not a full ops suite (O7/O8 Won’t).

---

## 19. Cross-cutting concerns (ops)

| Concern | Expectation |
|---------|-------------|
| **Auth** | Separate from consumer JWT; role-based access recommended |
| **Base path** | `/api/v1/ops/...` so consumer clients never call catalog writes |
| **Idempotency** | `Idempotency-Key` on bulk PUT matrix / wash complete |
| **Pagination** | Required on all list endpoints |
| **Errors** | Same JSON shape as consumer (`code`, `message`, `details`) |
| **Currency** | Paise integers, INR |
| **Soft flags** | Prefer `is_active` / `is_serviceable` over hard deletes |
| **Audit** | Catalog mutations should be attributable to an operator (Should) |
| **Versioning** | Same `/api/v1` major as consumer |

---

## 20. Priority summary (ops)

Focus for **unlocking modules 1–6 without seed scripts**:

| Priority | Focus | Modules |
|----------|--------|---------|
| **M (Must) first** | Location + vehicle catalog + city pricing + ops auth | 1, 3, 5, 6 |
| **M (Must) with service** | Waitlist triage + wash complete/miss | 4, 10 |
| **S** | User support lookup, content, app config, payment search | 2, 8, 12, 13 |
| **C / W** | Deep admin overrides, full suite | 7, 9, 11, 15 |

### Suggested ops MVP slice (replace seeds)

1. OPS-AUTH-01–02
2. OPS-LOC-01–06 (cities + societies)
3. OPS-VEH-01–06 (makes + models + size_tier)
4. OPS-PRICE-02–04 (city pricing matrix)
5. OPS-WAIT-01, OPS-WAIT-03 (triage)
6. Later: OPS-WASH-01–02 when washes exist

---

## 21. Seed → Ops migration checklist (modules 1–6)

| Seeded today (approx.) | Ops API that replaces it | Consumer failure if missing |
|------------------------|--------------------------|-----------------------------|
| Insert `cities` | OPS-LOC-02/03 | Empty LOC-01 |
| Insert `societies` | OPS-LOC-05/06 | Empty LOC-02; location set fails |
| Insert `vehicle_makes` / `vehicle_models` | OPS-VEH-02/05 | Empty VEH-06/07; register vehicle fails |
| Insert `city_pricing` + size/interior rows | OPS-PRICE-02–04 | `pricing_not_found` on PRICE-01/02 |
| Waitlist rows | User WAIT-01; ops only triages | N/A for create |
| Users / vehicles instances | Consumer auth + VEH-* | N/A (not catalog) |

---

## 22. Explicitly out of ops inventory (v1)

Aligned with PRD Won’t / thin ops:

- Full workforce management, routing, cleaner GPS
- RWA / society admin portal
- Cleaner-facing field app (optional later)
- Multi-tenant white-label ops
- Replacing consumer auth with ops login for end users

---

## 23. Open questions

| Topic | Impact |
|-------|--------|
| Ops auth mechanism (password vs SSO vs API key) | OPS-AUTH-* shape |
| Who may edit pricing (finance role?) | RBAC on OPS-PRICE-* |
| Model size_tier change → existing vehicles / subs | Snapshot vs reprice |
| Bulk CSV import vs pure REST | OPS-PLAT-03 priority |
| Soft-delete city with active subscribers | OPS-LOC-03 rules |

---

## 24. Review checklist

- [ ] Module split consumer vs ops clear?
- [ ] Any master table for modules 1–6 missing an ops write path?
- [ ] Waitlist: ops read/status enough, or need merge-to-society action?
- [ ] Pricing: single PUT matrix vs granular PATCH rows?
- [ ] Keep wash complete/miss under `/ops` only (no consumer)?

---

## 25. Next steps (after approval)

1. Freeze **ops MVP Must** set (LOC + VEH + PRICE + AUTH).
2. Implement ops auth + catalog modules (branch per module or one “ops catalog” epic).
3. Retire ad-hoc seeds for local/staging once Ops UI or scripts call these APIs.
4. Keep [API_INVENTORY.md](./API_INVENTORY.md) for consumer-only contracts.

---

*End of Ops API Inventory v0.1 — Clean My Car*
