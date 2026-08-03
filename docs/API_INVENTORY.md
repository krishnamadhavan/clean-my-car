# API Inventory — Clean My Car (Mobile Consumer + Supporting)

| Field | Detail |
|-------|--------|
| **Document type** | API inventory (module → endpoints) for product/engineering review |
| **Version** | 0.1 |
| **Status** | Draft — for review (not an OpenAPI contract yet) |
| **Source of truth** | [PRD.md](./PRD.md) v1.3 |
| **Primary consumer** | Native iOS app |
| **Base path (proposed)** | `/api/v1` |
| **Auth model (proposed)** | Bearer access token after phone OTP (refresh token optional/TBD) |
| **Ops companion** | [OPS_API_INVENTORY.md](./OPS_API_INVENTORY.md) — internal/admin APIs & master data (same module map) |

---

## 1. Purpose & how to read this doc

This document lists **all APIs the mobile app is expected to call** for v1, grouped by **module**. It also lists a small set of **supporting APIs** (payments webhooks, minimal ops) that the app does not call but the product needs so mobile features work.

| Column | Meaning |
|--------|---------|
| **ID** | Stable reference (`AUTH-01`, …) |
| **Method / path** | Proposed REST shape (names can change in technical design) |
| **Purpose** | What the client needs |
| **Priority** | **M** = Must (MVP), **S** = Should, **C** = Could, **W** = Won’t (v1 mobile) |
| **PRD** | Related PRD requirement IDs |

**Not in scope of this doc:** full request/response schemas, error codes, auth middleware design, database tables. Those belong in a later technical design / OpenAPI spec.

---

## 2. Module map (overview)

```text
┌─────────────────────────────────────────────────────────────┐
│                     iOS Consumer App                        │
├──────────────┬──────────────┬──────────────┬────────────────┤
│ 1. Auth      │ 2. Profile   │ 3. Location  │ 4. Waitlist    │
│ 5. Vehicle   │ 6. Pricing   │ 7. Subscr.   │ 8. Payments    │
│ 9. Dashboard │ 10. Washes   │ 11. Notifs   │ 12. Support    │
│ 13. App meta │              │              │                │
└──────────────┴──────────────┴──────────────┴────────────────┘
         │ webhooks / server-side only
         ▼
┌──────────────────┐  ┌──────────────────────────┐
│ 14. Payments WH  │  │ 15. Ops (minimal, not iOS)│
└──────────────────┘  └──────────────────────────┘
```

| # | Module | Owns |
|---|--------|------|
| 1 | **Auth & session** | OTP login, tokens, logout |
| 2 | **Profile & account** | Name/email, account delete/deactivate |
| 3 | **Location & eligibility** | Active cities, live societies, society detail/schedule |
| 4 | **Waitlist** | Interest when society not listed |
| 5 | **Vehicle** | Single vehicle CRUD (v1: one car) |
| 6 | **Pricing & plans** | City tariffs, quote (full + pro-rated) |
| 7 | **Subscription** | Start, view, change plan, cancel, pause |
| 8 | **Payments & billing** | Initiate pay, status, history, invoices |
| 9 | **Dashboard / home** | Aggregate “this month” snapshot for home screen |
| 10 | **Washes & schedule** | Progress, history, upcoming visits |
| 11 | **Notifications** | Device token registration, preferences |
| 12 | **Support & content** | FAQ, legal docs, contact/ticket |
| 13 | **App metadata** | Force-update / config (lightweight) |
| 14 | **Payment webhooks** | Gateway callbacks (server-only) |
| 15 | **Ops (minimal)** | Mark wash complete/missed; not consumer iOS |

---

## 3. Module 1 — Auth & session

**Goal:** Phone number + OTP sign-up/login for India; secure session for subsequent calls.

| ID | Method / path | Purpose | Priority | PRD |
|----|---------------|---------|----------|-----|
| AUTH-01 | `POST /auth/otp/request` | Send OTP to mobile number | M | A1 |
| AUTH-02 | `POST /auth/otp/verify` | Verify OTP; create/login user; return tokens + user summary | M | A1, A4 |
| AUTH-03 | `POST /auth/token/refresh` | Exchange refresh token for new access token | M | A4 |
| AUTH-04 | `POST /auth/logout` | Invalidate current session / refresh token | M | A4 |
| AUTH-05 | `GET /auth/session` | Validate session; return current principal (optional if profile covers it) | C | A4 |

**Notes**

- First successful verify may create the user if new.
- Rate-limit OTP request/verify aggressively.
- Device binding is optional (Could).

---

## 4. Module 2 — Profile & account

**Goal:** Basic profile maintenance and account lifecycle.

| ID | Method / path | Purpose | Priority | PRD |
|----|---------------|---------|----------|-----|
| PROF-01 | `GET /me` | Current user profile + high-level status (has vehicle? has sub?) | M | A2 |
| PROF-02 | `PATCH /me` | Update name, email (optional fields) | M | A2 |
| PROF-03 | `POST /me/deactivate` | Soft-deactivate account | S | A3 |
| PROF-04 | `DELETE /me` | Request account deletion (policy / retention) | S | A3 |

**Notes**

- Phone change is sensitive; treat as separate flow later (Won’t unless required for App Store/compliance).

---

## 5. Module 3 — Location & eligibility

**Goal:** Only **active cities** and **live/serviceable societies**; expose society schedule for UX.

| ID | Method / path | Purpose | Priority | PRD |
|----|---------------|---------|----------|-----|
| LOC-01 | `GET /cities` | List active cities (id, name, state, display order) | M | L1, L6, BR4 |
| LOC-02 | `GET /cities/{city_id}/societies` | List **live** societies in city (search `q`, pagination) | M | L2, L3, L6, Q9-A |
| LOC-03 | `GET /societies/{society_id}` | Society detail: address blurb, **3 service weekdays**, timezone/city ref | M | W1, W2, W11 |
| LOC-04 | `GET /me/location` | User’s saved city + society (if set) | M | L5 |
| LOC-05 | `PUT /me/location` | Set/update user’s city + society (must be live society) | M | L5, BR4 |

**Notes**

- `LOC-02` must **never** return non-serviceable societies (PRD Option A).
- Empty search → client shows “not available” + waitlist CTA.
- Moving house (`LOC-05`) may invalidate pricing/subscription eligibility — business rules in technical design.

---

## 6. Module 4 — Waitlist

**Goal:** Capture demand when the user’s society is not live.

| ID | Method / path | Purpose | Priority | PRD |
|----|---------------|---------|----------|-----|
| WAIT-01 | `POST /waitlist` | Join waitlist (city, free-text society name, phone/user id, notes) | S | L4 |
| WAIT-02 | `GET /me/waitlist` | User’s waitlist entries / status | C | L4 |

---

## 7. Module 5 — Vehicle

**Goal:** Exactly **one** vehicle per account in v1. **Size tier is not user-declared** — the user picks **make + model** from an ops-maintained catalog; the server derives Small / Medium / Large from the model.

| ID | Method / path | Purpose | Priority | PRD |
|----|---------------|---------|----------|-----|
| VEH-01 | `GET /me/vehicle` | Get current vehicle (404 if none); includes make, model, derived size_tier | M | V1 |
| VEH-02 | `PUT /me/vehicle` | Create or replace vehicle with `model_id` (+ optional nickname/plate/colour/parking) | M | V1, V4 |
| VEH-03 | `PATCH /me/vehicle` | Partial update; changing `model_id` re-derives size_tier | M | V2, V4 |
| VEH-04 | `DELETE /me/vehicle` | Remove vehicle (blocked if active paid sub — rule TBD) | S | V1 |
| VEH-05 | `GET /vehicle-size-tiers` | Informational labels for Small / Medium / Large (not a picker for pricing) | S | V1 |
| VEH-06 | `GET /vehicle-makes` | List active brands / makes for the picker | M | V1 |
| VEH-07 | `GET /vehicle-makes/{make_id}/models` | List active models for a make (each includes catalog `size_tier`) | M | V1 |

**Notes**

- No multi-vehicle list endpoints in v1 (PRD W: multi-car).
- Clients **must not** send `size_tier` on create/update; it is set only from `vehicle_models.size_tier`.
- Catalog is ops data (seed/admin later); inactive makes/models are hidden from consumers.
- Model change may require subscription plan recalculation (tie to Module 7).

---

## 8. Module 6 — Pricing & plans

**Goal:** Transparent **city-specific** pricing and a **quote** for checkout (full month + pro-rated amount due now).

| ID | Method / path | Purpose | Priority | PRD |
|----|---------------|---------|----------|-----|
| PRICE-01 | `GET /cities/{city_id}/pricing` | Full price matrix for city (size × interior frequency), GST presentation flags | M | S1, S8, S9, BR3 |
| PRICE-02 | `POST /pricing/quote` | Compute quote for inputs: city, size, interior freq, optional start date / society | M | S2, S10, BR8 |
| PRICE-03 | `GET /interior-options` | Reference: None / 1 / 2 / 4 per month | S | S1, interior options |

**Suggested `PRICE-02` response (conceptual)**

- Full monthly amount (base + interior)
- Amount due **now** (pro-rated if mid-month)
- Tax breakdown (if shown)
- Entitlement preview (exterior entitled this month, interior entitled)
- Next full-month amount + next billing month label
- Society service days (if society provided)

**Notes**

- Client should not compute pro-rate; server is source of truth.
- Amounts are **INR paise** (integer minor units).
- v1 pro-rate (technical default for Q15):
  `amount_due_now = round(full_monthly × remaining_days / days_in_month)`
  where remaining days are inclusive of start date through month end (`Asia/Kolkata`).
  Exterior entitlement uses society service weekdays in that window when `society_id` is provided.
- GST presentation: `amounts_include_gst` + `gst_rate_bps` on the city pricing config.

---

## 9. Module 7 — Subscription

**Goal:** Calendar-month subscription lifecycle: start, view, change, cancel (service until month end), optional pause.

| ID | Method / path | Purpose | Priority | PRD |
|----|---------------|---------|----------|-----|
| SUB-01 | `GET /me/subscription` | Current subscription (status, plan, city/society refs, cancel-at, period) | M | S4, BR7 |
| SUB-02 | `POST /me/subscription` | Start subscription (after quote); may return payment intent to complete | M | S3, S10 |
| SUB-03 | `POST /me/subscription/cancel` | Schedule cancel at **end of current calendar month**; no refund | M | S7, S11, BR9 |
| SUB-04 | `POST /me/subscription/cancel/undo` | Undo cancel if still within paid month (optional UX) | C | S7 |
| SUB-05 | `PATCH /me/subscription` | Change plan (size via vehicle and/or interior frequency); effective date per policy | S | S5, Q17 |
| SUB-06 | `POST /me/subscription/pause` | Pause for a date range | S | S6 |
| SUB-07 | `POST /me/subscription/resume` | Resume from pause | S | S6 |
| SUB-08 | `GET /me/subscription/history` | Past subscription periods / status changes | C | S4 |

**Subscription statuses (proposed)**

| Status | Meaning |
|--------|---------|
| `none` | No subscription |
| `pending_payment` | Created, waiting first/renewal payment |
| `active` | Paid for current month; service running |
| `cancel_scheduled` | Active until month end, then ends |
| `paused` | Paused (Should) |
| `expired` / `inactive` | Ended or unpaid |

**Notes**

- Start + pay may be one client flow using SUB-02 → PAY-01 → PAY-02.
- Unpaid month → no service (BR13); status should reflect that clearly.

---

## 10. Module 8 — Payments & billing

**Goal:** Manual monthly pay (UPI/cards/etc.), payment status, history, simple receipts. **No mandatory auto-pay in v1.**

| ID | Method / path | Purpose | Priority | PRD |
|----|---------------|---------|----------|-----|
| PAY-01 | `POST /me/payments/intents` | Create payment intent for current period (first pro-rate or full month renewal) | M | P1, P2, P6 |
| PAY-02 | `GET /me/payments/intents/{intent_id}` | Poll payment intent status (pending/success/failed) | M | P4 |
| PAY-03 | `POST /me/payments/intents/{intent_id}/confirm` | Client-side confirm after SDK success (if gateway requires) | M | P1 |
| PAY-04 | `GET /me/payments` | Payment history list (paginated) | S | P3 |
| PAY-05 | `GET /me/payments/{payment_id}` | Payment detail | S | P3 |
| PAY-06 | `GET /me/payments/{payment_id}/invoice` | Invoice/receipt metadata or PDF URL | S | P3, S9 |
| PAY-07 | `GET /me/billing/summary` | What is due now, period covered, grace/overdue flags | M | P2, P4, BR13 |

**Notes**

- Gateway-specific fields (Razorpay/Stripe/etc.) stay behind this module; client gets `client_secret` / order id as needed.
- Refunds mid-month cancel: not expected (P5); no consumer “request refund” API required for v1.

---

## 11. Module 9 — Dashboard / home

**Goal:** One call (or thin composition) for the home screen hero data.

| ID | Method / path | Purpose | Priority | PRD |
|----|---------------|---------|----------|-----|
| DASH-01 | `GET /me/dashboard` | Aggregate: vehicle blurb, plan, exterior completed/entitled/pending, interior A/B, next service/retry, society weekdays, subscription status, amount due | M | W3, W4, §8.2 |

**Notes**

- Can be implemented as a BFF-style aggregate over subscription + washes + billing.
- Prefer this over forcing the client to join 5 endpoints on every launch (client may still deep-link to modules).

---

## 12. Module 10 — Washes & schedule

**Goal:** Completed vs pending, history, upcoming service days / retries. Interior is **count-only** (days offline).

| ID | Method / path | Purpose | Priority | PRD |
|----|---------------|---------|----------|-----|
| WASH-01 | `GET /me/washes/summary` | Current calendar month: exterior entitled/completed/pending; interior included/completed | M | W3, W4, W8, W10, BR7 |
| WASH-02 | `GET /me/washes` | Wash history list (filters: month, status; pagination) | S | W5 |
| WASH-03 | `GET /me/washes/{wash_id}` | Single wash detail (date, exterior/interior flags, status, miss reason) | S | W5 |
| WASH-04 | `GET /me/schedule` | Upcoming service occurrences (society days + scheduled retries) for N days / rest of month | M | W1, W2, W9, BR2 |
| WASH-05 | `GET /me/washes/calendar` | Month grid view data (optional richer UI) | C | W5 |

**Wash statuses (proposed)**

| Status | Meaning |
|--------|---------|
| `scheduled` | Expected on a service day |
| `completed` | Marked done by ops |
| `missed` | Not done; retry planned |
| `retry_scheduled` | Next-day (or follow-up) attempt |
| `skipped` | Closed without completion (rare; ops/end of month policy) |

**Notes**

- Consumer app is **read-only** for wash completion.
- No API for user to “pick interior day” (PRD: offline coordination).

---

## 13. Module 11 — Notifications

**Goal:** Enable push for payment and service events.

| ID | Method / path | Purpose | Priority | PRD |
|----|---------------|---------|----------|-----|
| NOTIF-01 | `PUT /me/devices` | Register/update APNs device token + app version | S | N1–N5 |
| NOTIF-02 | `DELETE /me/devices/{device_id}` | Unregister device | S | — |
| NOTIF-03 | `GET /me/notification-preferences` | Read prefs (wash done, payment, reminders) | C | N1–N5 |
| NOTIF-04 | `PUT /me/notification-preferences` | Update prefs | C | N1–N5 |
| NOTIF-05 | `GET /me/notifications` | In-app notification inbox | C | — |

**Server-originated events (not client APIs)**

| Event | Priority | PRD |
|-------|----------|-----|
| Payment success / failure | M | N3 |
| Month renewal / amount due reminder | M | N3 |
| Wash completed | S | N1 |
| Missed + next-day retry | S | N5 |
| Cancel confirmation (service until date) | S | N4 |
| Upcoming service day reminder | C | N2 |

---

## 14. Module 12 — Support & content

**Goal:** Trust, help, and a support channel with context.

| ID | Method / path | Purpose | Priority | PRD |
|----|---------------|---------|----------|-----|
| SUP-01 | `GET /content/faq` | FAQ entries (or CMS-backed) | S | H1 |
| SUP-02 | `GET /content/legal/{doc_type}` | `terms` / `privacy` / `cancellation` (versioned text or URL) | M | H3 |
| SUP-03 | `POST /me/support/tickets` | Create support ticket (category, message, optional wash/payment ids) | M | H2 |
| SUP-04 | `GET /me/support/tickets` | List my tickets | C | H2 |
| SUP-05 | `GET /me/support/tickets/{ticket_id}` | Ticket detail / thread | C | H2 |
| SUP-06 | `GET /support/contact` | Static contact channels (WhatsApp link, email, phone) | S | H2 |

**Notes**

- v1 can implement SUP-03 as “create ticket + email ops” without a full ticketing product.
- Legal docs may be static URLs hosted outside the API; endpoint still helps versioning.

---

## 15. Module 13 — App metadata

**Goal:** Lightweight remote config for the iOS client.

| ID | Method / path | Purpose | Priority | PRD |
|----|---------------|---------|----------|-----|
| APP-01 | `GET /app/config` | Min supported iOS version, force-update flag, feature flags, support WhatsApp number | S | — |
| APP-02 | `GET /app/bootstrap` | Optional combined bootstrap: config + session summary for cold start | C | — |

---

## 16. Module 14 — Payment webhooks (server-only)

**Not called by the mobile app.** Required for PAY module reliability.

| ID | Method / path | Purpose | Priority | PRD |
|----|---------------|---------|----------|-----|
| WH-01 | `POST /webhooks/payments/{provider}` | Gateway webhook (payment captured/failed) | M | P1, P4 |
| WH-02 | `POST /webhooks/payments/{provider}/refunds` | Refund events if used later | C | P5 |

---

## 17. Module 15 — Ops (minimal, not consumer iOS)

**Not part of the customer mobile app.** Listed so the inventory is complete for “completed vs pending” to work.

| ID | Method / path | Purpose | Priority | PRD |
|----|---------------|---------|----------|-----|
| OPS-01 | `POST /ops/washes/{wash_id}/complete` | Mark exterior (± interior) complete | M | W7, O4, BR10 |
| OPS-02 | `POST /ops/washes/{wash_id}/miss` | Mark missed + schedule next-day retry | M | W9, O5, BR11 |
| OPS-03 | `GET /ops/societies/{society_id}/roster` | Subscribers/vehicles due on a date | S | O6 |
| OPS-04 | `GET /ops/washes` | Filter washes by society/date/status | S | O4–O6 |

**Auth:** separate ops credentials / VPN / admin token — not end-user JWT.
**Form factor:** thin internal client or scripts; **not** a full ops suite (O7/O8 Won’t).

Catalog/pricing seeding and city/society/vehicle/pricing admin APIs live in the **ops inventory**: [OPS_API_INVENTORY.md](./OPS_API_INVENTORY.md). Wash complete/miss (OPS-01–04 below) are also specified there as OPS-WASH-*. Until those are implemented, use seeds/SQL for master data.

---

## 18. Cross-cutting concerns (all modules)

| Concern | Expectation |
|---------|-------------|
| **Auth** | Bearer token on `/me/*` and mutating routes; public: OTP, cities, societies list, pricing matrix, legal, app config |
| **Idempotency** | `Idempotency-Key` on payment intents and subscription start |
| **Idempotent OTP** | Safe resend behaviour |
| **Pagination** | `cursor` or `page`/`page_size` on lists |
| **Errors** | Consistent JSON error body (`code`, `message`, `details`) |
| **Currency** | INR; amounts in minor units (paise) **or** decimal string — pick one in tech design |
| **Time** | Calendar month in society/city timezone (document TZ policy) |
| **Versioning** | `/api/v1` prefix |

---

## 19. Priority summary (consumer-facing counts)

Approximate counts for planning (IDs above; webhooks/ops excluded from mobile effort).

| Priority | Rough count | Role |
|----------|-------------|------|
| **M (Must)** | ~35 | MVP iOS can onboard, pay, see progress, cancel |
| **S (Should)** | ~20 | History, waitlist, pause, richer support, devices |
| **C (Could)** | ~12 | Inbox, undo cancel, calendar grid, bootstrap |
| **W** | — | Multi-car, auto-pay mandates, interior day picker, full ops app |

### Suggested MVP slice (implement first)

1. Auth (AUTH-01–04)
2. Profile (PROF-01–02)
3. Location (LOC-01–05)
4. Vehicle (VEH-01–03)
5. Pricing (PRICE-01–02)
6. Subscription (SUB-01–03)
7. Payments (PAY-01–03, PAY-07) + WH-01
8. Dashboard (DASH-01)
9. Washes (WASH-01, WASH-04)
10. Legal (SUP-02) + Support create (SUP-03)
11. Ops complete/miss (OPS-01–02) so dashboard numbers move

---

## 20. End-to-end flows → APIs

### 20.1 First-time subscribe

```text
AUTH-01 → AUTH-02
  → LOC-01 → LOC-02 → LOC-03 → LOC-05
  → VEH-02
  → PRICE-02 → SUB-02 → PAY-01 → (gateway) → PAY-02/03 / WH-01
  → DASH-01
```

### 20.2 Monthly renewal (manual pay)

```text
DASH-01 / PAY-07 (see amount due)
  → PAY-01 → gateway → PAY-02/03 / WH-01
  → WASH-01 / DASH-01
```

### 20.3 Cancel

```text
SUB-01 → SUB-03 → DASH-01  (status: cancel_scheduled, service until month end)
```

### 20.4 Home / progress

```text
DASH-01  (or WASH-01 + SUB-01 + PAY-07 + WASH-04)
```

---

## 21. Explicitly out of inventory (v1)

Aligned with PRD Won’t / non-goals:

- Multi-car subscription APIs
- Auto-pay mandate create/revoke
- Interior day scheduling / cleaner chat
- One-off “book a wash now” marketplace
- Consumer cleaner tracking / live GPS
- Full ops workforce suite
- Society RWA admin portal APIs
- Android-specific endpoints (same API; client differs later)

---

## 22. Open questions affecting API shape

| Topic | Impact |
|-------|--------|
| Pro-rate formula (Q15) | Fields inside `PRICE-02` / entitlements, not module boundaries |
| Plan change effective date (Q17) | `SUB-05` body (`effective: immediate \| next_month`) |
| Refresh token vs short-lived access only | AUTH-03 presence |
| Payment provider choice | Shape of PAY-01 client payload |
| Pause rules | SUB-06/07 required fields |
| Vehicle delete while subscribed | VEH-04 rules |
| Ticket system vs WhatsApp-only | SUP-03 depth |

---

## 23. Review checklist

Please mark feedback on:

- [ ] Module boundaries (merge/split any modules?)
- [ ] Any **missing** consumer API for a PRD Must?
- [ ] Any API to **drop** from MVP Must list?
- [ ] Prefer **DASH-01 aggregate** vs client composition only?
- [ ] Waitlist / pause / plan-change: keep as Should for v1.1?
- [ ] Ops APIs: OK as separate non-mobile surface?

---

## 24. Next steps (after approval)

1. Freeze MVP Must set.
2. Produce OpenAPI (or technical design) for Must endpoints only.
3. Implement module-by-module on feature branches (no commit until you review).
4. iOS can generate client stubs from OpenAPI later.

---

*End of API Inventory v0.1 — Clean My Car*
