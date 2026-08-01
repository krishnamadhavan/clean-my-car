# Project Requirements Document (PRD)
## Clean My Car — Apartment Car Cleaning Subscription

| Field | Detail |
|-------|--------|
| **Product name** | Clean My Car |
| **Document type** | Project Requirements Document (non-technical) |
| **Version** | 1.3 |
| **Status** | Draft — product decisions locked for v1; optional edge cases (Q15–Q17) can ride with technical design |
| **Date** | 30 July 2026 |
| **Primary platform (v1)** | Native iOS app |
| **Service model** | Monthly subscription for scheduled car cleaning |
| **Initial market** | Select cities in India, apartment communities only |
| **Changelog (v1.1)** | Resolved Q1–Q7: DB-driven cities/societies, calendar-month billing with pro-rated start, cancel-at-month-end, next-day makeup attempts, per-society service days, city-specific pricing |
| **Changelog (v1.2)** | Resolved Q8, Q11–Q14: single vehicle only; manual monthly pay allowed; brand Clean My Car; no XL tier; interior day assignment offline (not automated) |
| **Changelog (v1.3)** | Q9: app lists only live/serviceable societies. Q10: no full ops suite or cleaner field app; wash complete/missed via minimal internal process only |

---

## 1. Executive Summary

Clean My Car is a subscription-based car cleaning service designed for residents of apartment complexes in select Indian cities. Subscribers opt in through a mobile app, choose a plan based on car size and interior-cleaning needs, and receive exterior (and optionally interior) washes on a fixed schedule of **three service days per week** (days configured **per society**).

The product removes the friction of one-off car wash bookings: users pay on a **calendar-month** cycle (pro-rated if they join mid-month), see how many washes they have left, and know when their car will be cleaned—without chasing local washers or visiting a service center.

**v1 goal:** Launch a polished native iOS experience that lets apartment residents in serviceable cities/societies subscribe, manage their plan, and track washes completed vs pending for the current calendar month.

---

## 2. Problem Statement

### 2.1 Customer pain points

| Pain | Description |
|------|-------------|
| **Inconsistent service** | On-demand washers are unreliable; quality and timing vary day to day. |
| **Time cost** | Driving to a wash bay or waiting for someone to arrive interrupts busy apartment living. |
| **Unclear pricing** | Ad-hoc rates for hatchback vs SUV, or exterior vs full clean, are hard to compare. |
| **No visibility** | Residents who pay monthly (or tip regularly) rarely know how many cleans they “got” vs what they expected. |
| **Apartment logistics** | Cars are parked in basements or open lots; access and coordination with security are non-trivial. |

### 2.2 Opportunity

Apartment communities concentrate many cars in one place. A scheduled, subscription model can:

- Deliver predictable service three days a week on-site.
- Price transparently by car size, interior frequency, and **city**.
- Give users a simple monthly progress view (completed vs pending washes).
- Build recurring revenue while optimising cleaner routes by society and city.

---

## 3. Vision & Goals

### 3.1 Product vision

> Every apartment car owner in our cities can open the app, subscribe in minutes, and never wonder when their car will be cleaned next—or how many washes they still have this month.

### 3.2 Business goals (v1)

1. **Validate demand** in apartment communities across cities configured as active in the product.
2. **Establish a clear subscription funnel**: discover eligibility → choose plan → pay (full or pro-rated) → receive service.
3. **Operational clarity**: cleaners and ops know who is due on which **society-specific** service day.
4. **Trust through transparency**: completed vs pending wash counts are always visible and accurate.

### 3.3 User goals (v1)

1. Confirm the service is available for their apartment and city.
2. Subscribe with the right plan for their car and interior needs.
3. Understand schedule (3 days/week for their society) and what is included.
4. Track monthly wash progress without calling support.
5. Manage basic account and subscription actions (pause, cancel, update plan—where offered).

### 3.4 Non-goals (explicitly out of v1)

See **Section 12 — Out of Scope**.

---

## 4. Target Users & Personas

### 4.1 Primary persona: “Apartment Car Owner”

| Attribute | Detail |
|-----------|--------|
| **Who** | Working professional or family living in a gated/apartment complex |
| **Car** | One primary vehicle (hatchback, sedan, SUV/MUV, or luxury—see sizing) |
| **Motivation** | Clean car without weekend trips to a wash centre |
| **Constraints** | Fixed parking slot; limited free time; prefers UPI/cards for recurring pay |
| **Success** | Car cleaned on schedule; fair price; app shows washes done vs left |

### 4.2 Secondary persona: “Decision-maker spouse / co-owner”

May not drive daily but manages household subscriptions and wants clear billing and progress.

### 4.3 Indirect stakeholders (not end-users of the consumer app in v1)

| Stakeholder | Role |
|-------------|------|
| **Cleaners / field staff** | Execute washes on service days (ops tooling may be separate or minimal in v1) |
| **Apartment / society admin** | May approve vendor access; not a product user in v1 unless needed for eligibility |
| **Internal ops** | Onboard cities/societies, set per-society schedules and city pricing, handle exceptions |
| **Support** | Resolve missed washes, access issues, billing questions |

### 4.4 Eligibility (who can use the service)

A user is eligible for v1 when **all** of the following are true:

1. They live in an **apartment / gated community** (not independent house / open street parking as primary model).
2. Their **city** is marked active in the application (list maintained by ops; **served to the app from the product database**, not hard-coded in the client).
3. Their **specific society/apartment** is onboarded and marked serviceable (same source: application database).
4. They have a **vehicle** they can register against the subscription.

**Product implication:** Cities, societies, service schedules, and serviceability flags are **operational data**. Ops add or disable them; the app always reads the current set. Pilot city/society choices do not need to be fixed in this PRD.

**Society discovery (v1):** The app shows **only societies that are live/serviceable**. Users do not browse a wide directory of non-serviceable complexes. If their building is not on the list, they see that service is unavailable and may join a waitlist (Should).

---

## 5. Service Model

### 5.1 Core offering

| Element | Definition |
|---------|------------|
| **Product type** | Monthly recurring subscription |
| **Service days** | **3 days per week**, configured **per society** (e.g., Society A: Mon/Wed/Fri; Society B: Tue/Thu/Sat) |
| **Location** | User’s apartment parking (on-site) |
| **Default clean** | Exterior wash (water/foam/wipe-down as per ops SOP) |
| **Optional add-on** | Interior cleaning, at a chosen frequency per month |
| **Billing cycle** | **Calendar month** (1st through last day of the month) |
| **Wash entitlement** | Derived from the society’s 3 service days per week within the calendar month, adjusted for mid-month start (pro-rated period) and any pauses |

### 5.2 What “3 days a week” means for the user

- Users do **not** pick arbitrary wash dates for each clean in v1.
- Service runs on a **fixed weekly pattern of three days defined for that user’s society**.
- On each service day, eligible subscribed cars at that society are cleaned per the day’s plan (exterior always; interior only on designated interior days if the user opted in).
- Users see:
  - **Their society’s service days** and upcoming visits, and
  - **Completed vs pending** washes for the current calendar month.

### 5.3 Car size categories (pricing input)

Pricing varies by vehicle size. Recommended v1 categories (labels can be refined with ops):

| Size tier | Typical examples |
|-----------|------------------|
| **Small** | Hatchbacks (e.g., Swift, i20, Baleno) |
| **Medium** | Sedans / compact crossovers (e.g., City, Verna, Nexon) |
| **Large** | SUVs / MUVs (e.g., Creta, XUV, Innova) |

**v1 does not include** an XL / luxury / van size tier. Oversized or specialty vehicles are out of scope unless ops later adds a tier.

Users select size during onboarding; ops may correct misclassification if needed.

### 5.4 Interior cleaning options

Users choose whether they need **interior cleaning**, and if yes, **how many times per month**.

| Interior option | Meaning |
|-----------------|--------|
| **None** | Exterior-only subscription |
| **1× / month** | One interior clean per calendar month |
| **2× / month** | Two interior cleans per calendar month |
| **4× / month** | Four interior cleans—aligned with roughly once per week |

**v1:** Support **None / 1 / 2 / 4** times per month as discrete plan add-ons. The app tracks **how many** interior cleans are included and completed; it does **not** auto-schedule *which* service days receive interior. Ops communicates interior visit days to the user **offline** (call, WhatsApp, in-person at the society, etc.). For mid-month starts, interior entitlement is pro-rated along with exterior (see §5.7).

### 5.5 Pricing principles (non-technical)

1. **Base monthly price** depends on **car size**.
2. **Interior add-on** adds a fee based on **frequency per month**.
3. Total full-month price = base (size) + interior package (if any).
4. **Prices are city-specific.** After the user selects a city, the plan builder shows tariffs for that city (size + interior). Different cities may have different amounts for the same size/interior combo.
5. Prices are shown in **INR**, inclusive or exclusive of GST as per legal/finance guidance (must be stated clearly in UI).
6. Mid-month **start** charges a **pro-rated** amount for the remainder of the calendar month (see §5.7).
7. Plan changes mid-cycle: effective date policy still TBD for upgrades/downgrades (remaining open question).

*Exact rupee amounts are commercial inputs maintained as application configuration (by city)—not hard-coded in this PRD or the iOS client.*

### 5.6 Completed vs pending washes

This is a **core product promise**.

For the **current calendar month**, the user must always be able to see:

| Metric | Definition |
|--------|------------|
| **Entitled washes** | Number of exterior washes included for this month (based on society’s 3×/week schedule within the user’s active period that month) |
| **Completed** | Washes marked done by ops/cleaner for this month |
| **Pending** | Entitled − Completed (remaining washes still expected) |
| **Interior progress** *(if applicable)* | Interior cleans done vs included for the month |

**Example (illustrative):**
User entitled to 12 exterior washes this month; 7 done → **7 completed, 5 pending**.
Interior 2×/month; 1 done → **1 of 2 interiors completed**.

### 5.7 Billing: calendar month, pro-rated start, cancel at month-end

| Topic | Policy (decided) |
|-------|------------------|
| **Billing period** | **Calendar month** (e.g., 1 Aug–31 Aug). Wash counts and “this month” on the dashboard align to the same period. |
| **Mid-month signup** | User pays a **pro-rated amount** covering from the **start date through the last day of that month**. Entitlement (exterior and interior) is calculated only for remaining service days / fair share of the month—not a full-month allotment. |
| **Full subsequent months** | From the next calendar month onward, user is charged the **full monthly** city/size/interior price (unless cancelled). |
| **Cancellation** | User may cancel at any time. **Service continues until the end of the current calendar month** because the user has already paid for that period. No further charge for the next month. **No pro-rated refund** on cancel mid-month (service is fulfilled for the paid month). |
| **Renewal** | On the boundary into a new calendar month, collect the full monthly fee if the subscription is still active (not cancelled). |

**Checkout UX implications:**

- Show **“Pay ₹X for remainder of [Month]”** when joining mid-month, with a clear note of the **full monthly price from next month**.
- On cancel, show **“You’ll keep service until [last day of month]. No charge from next month.”**

**Pro-rate calculation (product intent, not engineering formula):**
Charge and entitlement scale with **how much of the month remains** after signup (by days remaining and/or remaining society service days—exact formula to be specified in the technical design and finance review, but must feel fair and explainable in the app).

### 5.8 Missed washes: next-day attempt

When a scheduled wash cannot be completed on the service day, the default policy is **attempt again the next day** (not auto-credit or skip without retry).

| Situation | Policy (decided) |
|-----------|------------------|
| **Car not available** (user away, car out, blocked access to slot) | Mark as missed for that day; **retry the next day**. Remains **pending** until completed or month ends under ops handling. |
| **Weather / access / ops failure** (rain, society access issue, cleaner no-show, etc.) | Same: **retry the next day**. |

**Product implications:**

- Pending count does **not** drop when a wash is merely deferred; it drops only when marked **completed**.
- Users should be able to understand that a missed visit will be **retried the following day** (FAQ + optional notification).
- Ops need a way to flag a visit as “missed — retry next day” vs “completed.”
- Edge cases if the next day is not a normal society service day, or multiple consecutive misses, should be handled by ops playbooks and refined in the technical/ops design (e.g., retry window, escalate to support). Intent of this PRD: **do not abandon the wash without a next-day attempt.**

---

## 6. User Journeys

### 6.1 First-time signup & subscribe

1. Download iOS app → open.
2. Sign up (phone OTP recommended for India) or log in.
3. Select **city** from the live list of active cities (from the product database).
4. Search and select **apartment society** (only societies for that city; serviceability from the database).
5. If society is **not serviceable**: clear message + waitlist option.
6. If serviceable: add **vehicle** (nickname, number plate optional, size tier, colour optional).
7. Choose **interior package** (none / 1 / 2 / 4 per month).
8. See **price breakdown** for **that city**: full monthly price, and if mid-month, **pro-rated amount due now** plus note about full price next month. Show society’s 3 service days/week.
9. Complete **payment** for the current (pro-rated or full) period.
10. Land on **Home / Dashboard**: next service info + completed vs pending for the current calendar month.

### 6.2 Ongoing monthly use

1. Open app → dashboard shows progress for the **current calendar month**.
2. Optionally view calendar / list of past and upcoming service days (society schedule + any next-day retries).
3. Receive notifications (service day reminder, wash completed, missed + retry, payment due, failed payment).
4. At calendar month boundary: user is prompted to **pay the full monthly price** for the new month (manual monthly payment allowed; auto-pay optional later if offered).

### 6.3 Plan change

1. User opens Subscription / Plan.
2. Changes car size (e.g., bought new car) or interior frequency.
3. Sees new **city-specific** price and effective date (immediate vs next cycle—policy TBD).
4. Confirms; dashboard entitlements update per policy.

### 6.4 Pause / cancel

1. User requests pause (e.g., long travel) or **cancellation**.
2. **On cancel:** App explains that **service continues until the end of the current calendar month** (already paid); **no refund** for the remaining days; **no charge next month**.
3. Confirms; subscription status shows “Cancels on [month end]” or equivalent until the period ends, then inactive.
4. Pause (if offered): separate from cancel; freezes future service and billing per pause policy *(pause details still flexible)*.

### 6.5 Support

1. User reports missed wash, wrong charge, or access issue.
2. In-app help / contact channel captures context (society, car, date).
3. Support resolves offline; user sees updated completed count if wash is credited; ops may schedule next-day retry per policy.

---

## 7. Functional Requirements (by area)

Requirements use MoSCoW priority: **Must / Should / Could / Won’t (v1)**.

### 7.1 Account & identity

| ID | Requirement | Priority |
|----|-------------|----------|
| A1 | User can register and log in using mobile number + OTP | Must |
| A2 | User can maintain a basic profile (name, phone, email optional) | Must |
| A3 | User can log out and delete/deactivate account per policy | Should |
| A4 | Session remains secure; user re-authenticates when needed | Must |

### 7.2 Location & eligibility

| ID | Requirement | Priority |
|----|-------------|----------|
| L1 | User can select city from the **current list of active cities** provided by the application (database-backed) | Must |
| L2 | User can search and select from **only live/serviceable** societies for that city (database-backed; no wide directory of non-live buildings) | Must |
| L3 | If the user’s society is not listed, app shows service unavailable for that search / empty state | Must |
| L4 | If unavailable, user can join a waitlist with contact details | Should |
| L5 | User can update society if they move (must pick another live society; may change schedule/pricing) | Should |
| L6 | Cities, societies, and serviceability can be updated by ops without requiring an app store release | Must |

### 7.3 Vehicle

| ID | Requirement | Priority |
|----|-------------|----------|
| V1 | User can add **exactly one** vehicle with size tier (Small / Medium / Large) for the subscription | Must |
| V2 | User can edit vehicle details and size | Must |
| V3 | Multiple vehicles / multi-car subscriptions in one account | Won’t (v1) |
| V4 | Optional: registration number, colour, parking slot / tower | Should |

### 7.4 Subscription & pricing

| ID | Requirement | Priority |
|----|-------------|----------|
| S1 | User can view plan options driven by car size + interior frequency | Must |
| S2 | User can see transparent price before pay (**city-specific** full monthly + pro-rated amount if mid-month) | Must |
| S3 | User can start a monthly subscription on a **calendar-month** basis | Must |
| S4 | User can view current plan, price, and next billing date (start of next calendar month if active) | Must |
| S5 | User can change interior frequency or car size per policy | Should |
| S6 | User can pause subscription for a date range | Should |
| S7 | User can cancel subscription; service remains active until **end of current calendar month** | Must |
| S8 | Pricing is **city-specific** (size + interior matrix per city) | Must |
| S9 | Taxes (GST) shown clearly on checkout and invoices | Must |
| S10 | Mid-month start charges **pro-rated** fee through month end and sets pro-rated entitlements | Must |
| S11 | Cancel does **not** refund the current month; blocks renewal for the next month | Must |

### 7.5 Service schedule & wash tracking

| ID | Requirement | Priority |
|----|-------------|----------|
| W1 | User understands service is 3 days per week | Must |
| W2 | User can see which days of the week apply (**for their society**) | Must |
| W3 | Dashboard shows **completed vs pending** exterior washes for **current calendar month** | Must |
| W4 | Dashboard shows interior cleans completed vs included (if any) for current calendar month | Must |
| W5 | User can see history of past washes (date, type exterior/interior, status) | Should |
| W6 | User is notified when a wash is marked complete | Should |
| W7 | Ops/admin can mark a wash complete (backend/ops process; may be non-app for v1) | Must |
| W8 | Pending count updates correctly after completion, mid-month start, or cancel-at-month-end | Must |
| W9 | Ops can mark a visit missed; system/process schedules **next-day retry** (car unavailable or weather/access/ops issues) | Must |
| W10 | Missed-but-retried washes stay in **pending** until completed | Must |
| W11 | Society service-day pattern (which 3 weekdays) is configurable per society in application data | Must |
| W12 | App does **not** auto-assign which service days include interior; count-only for interiors; day-of coordination is offline | Must |

### 7.6 Payments & billing

| ID | Requirement | Priority |
|----|-------------|----------|
| P1 | User can pay subscription via common India methods (UPI, cards, netbanking as available) | Must |
| P2 | **Manual monthly payment** is supported: user pays each calendar month (or pro-rated first period) without mandatory auto-pay | Must |
| P3 | User can view payment history and simple invoices/receipts | Should |
| P4 | Failed / missed payment: clear status, retry path, and service impact policy (e.g. no service for unpaid month) | Must |
| P5 | Refunds: not expected for mid-month cancel of a paid month; other refunds per policy (may be manual in v1) | Should |
| P6 | First charge may be pro-rated; subsequent months are full monthly (city tariff) once paid | Must |
| P7 | Auto-pay / mandates | Won’t (v1) — may be added later as optional convenience |

### 7.7 Notifications

| ID | Requirement | Priority |
|----|-------------|----------|
| N1 | Push notification: wash completed | Should |
| N2 | Push / in-app: upcoming service day reminder | Could |
| N3 | Payment success, failure, renewal reminder | Must |
| N4 | Subscription cancelled confirmation (with service-until date) | Should |
| N5 | Missed wash / next-day retry notification | Should |

### 7.8 Support & trust

| ID | Requirement | Priority |
|----|-------------|----------|
| H1 | In-app FAQ (pricing, pro-rate, cancel-at-month-end, next-day retry, society schedule) | Should |
| H2 | Contact support (WhatsApp, email, or in-app ticket) | Must |
| H3 | Terms of service, privacy policy, cancellation policy accessible | Must |

### 7.9 Admin / operations (minimum for v1 product to work)

Even if not exposed in the consumer iOS app, the **business** requires:

| ID | Requirement | Priority |
|----|-------------|----------|
| O1 | Maintain list of cities and serviceable societies in the application database | Must |
| O2 | Maintain **city-specific** pricing by size and interior tier | Must |
| O3 | Assign **per-society** service-day pattern (exactly 3 days/week) | Must |
| O4 | Mark washes complete (and optionally interior) per vehicle per day via a **minimal internal process** (not a productized ops suite) | Must |
| O5 | Mark wash missed and record **next-day retry** via the same minimal process | Must |
| O6 | View subscribers by society for field planning (can be lightweight: export, simple list, or query—not a full ops product) | Should |
| O7 | Full-featured cleaner mobile app | Won’t (v1) |
| O8 | Full ops suite (routing, workforce management, RWA portals, advanced analytics, etc.) | Won’t (v1) |

*v1 ops surface stays intentionally thin: enough to keep cities/societies/pricing accurate and to record complete/missed washes so the consumer dashboard stays truthful. Exact form (minimal admin page, scripted API use, etc.) is a technical design choice—not a multi-module ops product.*

---

## 8. User Experience Principles

1. **Eligibility first** — Don’t let users pay before confirming their society is live.
2. **Price honesty** — Size + interior + **city** always show the amount due now (pro-rated or full) and the ongoing monthly price.
3. **Progress at a glance** — Completed vs pending is the hero of the home screen (calendar month).
4. **Low cognitive load** — Fixed 3-day society schedule; no complex slot-picking in v1.
5. **India-first UX** — Phone login, INR, GST clarity, lightweight screens for average devices.
6. **Calm trust** — Clear cancel messaging (service until month end); no dark patterns on renewal.

### 8.1 Key screens (consumer app)

| Screen | Purpose |
|--------|---------|
| Splash / Login | OTP auth |
| City & Society | Eligibility — **live societies only** |
| Add vehicle | Size & identity |
| Plan builder | Interior frequency + **city** price |
| Checkout | Pay pro-rated or full month |
| Home dashboard | Progress, next service, plan summary |
| Wash history | Past cleans + missed/retry status |
| Subscription | Manage plan, pause, cancel (with end-of-month messaging) |
| Payments | History & methods |
| Help / Support | FAQ + contact |
| Profile | Account settings |

### 8.2 Dashboard content (minimum)

- Greeting / vehicle name
- **Completed X / Entitled Y** exterior washes this **calendar month**
- **Interior: A / B** if subscribed
- Progress indicator (ring or bar)
- Next service day (or next-day retry if applicable)
- Society’s weekly service days
- Active plan / price (and “service until …” if cancellation scheduled)
- Quick link to history and manage plan

---

## 9. Business Rules (summary)

| # | Rule |
|---|------|
| BR1 | Service is **subscription-only** in v1 (no pure one-off booking as primary flow). |
| BR2 | Service runs **3 days per week** on a schedule defined **per society**. |
| BR3 | Monthly price is determined by **city**, **car size**, and **interior frequency**. |
| BR4 | Only users in **serviceable apartment societies** in **active cities** can subscribe; both lists come from the **application database**. The consumer app **lists only live societies** (not a broad non-serviceable directory). |
| BR5 | Exterior washes are the default entitlement from the society’s weekly schedule within the active period. |
| BR6 | Interior cleans are capped at the purchased (pro-rated if needed) monthly frequency. |
| BR7 | Billing and wash counting use the **calendar month**. |
| BR8 | Mid-month **start** → **pro-rated** payment and entitlement through month end. |
| BR9 | **Cancel** → service continues through **month end**; no refund for remaining days; no next-month charge. |
| BR10 | A wash is **completed** only when marked done by authorised ops/cleaner process. |
| BR11 | If wash cannot be done (car unavailable, weather, access, ops failure) → **attempt next day**; remains pending until completed. |
| BR12 | **One vehicle per account/subscription in v1** (no multi-car). |
| BR13 | Users **pay each month** (manual monthly payment); auto-pay is not required for v1. Unpaid month → no service for that month (exact grace rules TBD in tech/ops). |
| BR14 | Interior **frequency** is productized; interior **calendar days** are coordinated **offline** by ops with the user. |

---

## 10. Geographic & Operational Scope (v1)

| Dimension | v1 scope |
|-----------|----------|
| **Country** | India |
| **Cities** | Any cities marked active in the application database (ops-maintained) |
| **Housing** | Apartments / gated societies only |
| **Service days** | Exactly three days per week, **per society** configuration |
| **Pricing** | **City-specific** matrices |
| **Language** | English first; Hindi or regional language Could |
| **Currency** | INR |
| **Platform** | Native iOS only |
| **Android / web consumer** | Out of v1 |

---

## 11. Success Metrics

### 11.1 Product / growth

| Metric | Why it matters |
|--------|----------------|
| Subscription conversion rate (eligible users → paid) | Funnel health |
| Monthly active subscribers | Core growth |
| Churn rate (monthly; measured at calendar-month renewal) | Retention / product-market fit |
| Waitlist → conversion when society goes live | Expansion demand |

### 11.2 Service quality

| Metric | Why it matters |
|--------|----------------|
| Wash completion rate (completed / entitled) | Delivery reliability |
| Missed visits and next-day recovery rate | Ops quality + policy effectiveness |
| Support tickets per 100 subscribers | Friction |
| App rating (App Store) | Trust |

### 11.3 Experience

| Metric | Why it matters |
|--------|----------------|
| Time to first successful subscription | Onboarding friction |
| % users who open dashboard weekly | Engagement with progress feature |
| Payment success rate (including first pro-rated charge) | Billing health |

*Numeric targets to be set once pilot societies and pricing are locked in ops data.*

---

## 12. Out of Scope (v1)

The following are **not** required for the first release:

1. Native Android app or consumer web app
2. One-off / on-demand booking as the main product
3. Full marketplace of independent cleaners
4. Detailing packages (polish, ceramic, engine wash) beyond standard exterior + interior
5. Multi-city expansion automation (manual ops configuration OK)
6. Society admin portal for RWAs
7. Advanced cleaner routing / GPS live tracking
8. In-app chat with cleaners
9. Corporate / fleet subscriptions
10. Loyalty points / referral programme *(Could later)*
11. Multi-language full localisation
12. Independent houses / standalone villas as a primary segment
13. Mid-month cancel **refunds** (explicitly not offered under current policy)
14. **Multi-car** accounts / multiple vehicles per subscription
15. **XL / luxury** vehicle size tier
16. **Mandatory auto-pay** / UPI autopay mandates
17. **Automated interior day scheduling** in the app (ops coordinates offline)
18. Full-featured **cleaner field app**

---

## 13. Assumptions

1. Field cleaners can access apartment parking on designated service days with society permission.
2. Ops can mark washes complete the same day (or within a short SLA), and can flag missed + next-day retry.
3. Water and supplies are handled operationally outside the consumer app.
4. Each subscriber has **one vehicle** in v1.
5. Payment gateway supports Indian methods (UPI, cards, etc.) for **one-time / monthly manual** charges, including variable first-period (pro-rated) amounts. Auto-pay is not required for launch.
6. Legal entity can issue GST-compliant invoices as required.
7. Ops will keep cities, societies, schedules, and city price matrices up to date in the application database.
8. Next-day retries are operationally feasible in pilot societies (staffing/logistics).
9. Ops can coordinate interior visit days with users outside the app (phone/WhatsApp/on-site).

---

## 14. Decisions log & remaining open questions

### 14.1 Decided (v1.1)

| # | Topic | Decision |
|---|--------|----------|
| Q1 | Pilot cities / societies | **Not fixed in the PRD.** Active cities and societies are maintained in the **application database** and exposed to the app. Ops onboard/disable locations as needed. |
| Q2 | Billing period | **Calendar month.** Mid-month signup pays a **pro-rated** amount through month end. |
| Q3 | Pro-rate on start / cancel | **Start:** yes, pro-rated. **Cancel:** service continues until **end of month** (already paid); no mid-month refund; no next-month charge. |
| Q4 | Car unavailable on service day | **Retry the next day.** |
| Q5 | Weather / access / ops failure | **Retry the next day.** |
| Q6 | Service-day pattern | **Per society** (each society has its own 3 days/week). |
| Q7 | Pricing by city | **Yes** — amounts are **city-specific**. |
| Q8 | Multi-car | **No.** One vehicle per user/subscription in v1. |
| Q9 | Society listing | **Option A — only live/serviceable societies** appear in the app. No wide directory of non-live buildings. Waitlist (Should) if user’s society is missing. |
| Q10 | Ops tooling | **No full ops suite and no cleaner field app.** Wash complete/missed still required via a **minimal internal process** only (thin admin or equivalent—not a productized ops platform). Exact implementation left to technical design. |
| Q11 | Payment style | **Allow manual monthly payments** (user pays each month). Auto-pay not required for v1. |
| Q12 | Brand name | **Clean My Car** (confirmed). |
| Q13 | XL / luxury tier | **Not required** for v1. Size tiers: Small / Medium / Large only. |
| Q14 | Which days get interior | **Offline coordination** with the user. App does not automate interior day assignment; it only tracks interior count (included vs completed). |

### 14.2 Optional (can be decided during technical design)

| # | Question | Impact | Suggested default if deferred |
|---|----------|--------|-------------------------------|
| Q15 | Exact **pro-rate formula** (calendar days remaining vs remaining service days)? | Checkout amounts & entitlement | Pro-rate by **calendar days remaining in the month** (simple, explainable); entitlement from remaining society service days in that window |
| Q16 | Next-day retry when tomorrow is **not** a society service day, or after **repeated** misses? | Ops playbook | Still attempt next calendar day when possible; after N misses, ops handles offline |
| Q17 | Plan **upgrade/downgrade** mid-month? | Billing | Apply from **next calendar month** (simplest with manual monthly pay) |

---

## 15. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Society denies cleaner access | Pre-onboard societies; document access rules; only **live** societies listed and able to accept payment |
| Users misunderstand “3 days/week” entitlement | Clear onboarding copy + dashboard; show **this society’s** days |
| Users confused by pro-rate vs full month | Checkout shows both amounts; FAQ |
| Cancel expectation of refund | Explicit cancel copy: service until month end, no refund |
| Ops lag in marking washes complete | Same-day completion SLA |
| Next-day retries overload capacity | Ops staffing plan; monitor retry rate; escalate multi-day misses |
| Payment failures at month boundary | Clear retry UX; defined grace policy (TBD) |
| Wrong car size selected (underpay) | Size guide with photos; ops verification |
| Stale city/society list | Database is source of truth; ops process to disable societies promptly |
| Scope creep into full marketplace | Strict out-of-scope list for v1 |

---

## 16. Release Phasing (product, not engineering)

### Phase 0 — Foundations
- Ops seed **live** cities, societies, **per-society schedules**, and **city price matrices** in the application database
- Optionally lock Q15–Q17 (or use suggested defaults in §14.2)
- Define legal terms, GST posture, cancellation policy (aligned with §5.7)

### Phase 1 — MVP (iOS)
- Auth, eligibility (**only live societies** listed), **single** vehicle, subscribe
- City-specific pricing; pro-rated first charge; calendar-month cycle
- **Manual monthly payment** for each period
- Dashboard: completed vs pending (+ interior counts)
- **Minimal** internal process to mark washes complete, missed, and next-day retry (no full ops suite / no cleaner app)
- Cancel with service-until-month-end behaviour
- Interior days coordinated offline

### Phase 2 — Retention & polish
- Pause, plan changes, wash history, richer notifications (including retry)
- Waitlist when society not listed
- Improved invoices; optional auto-pay as convenience

### Phase 3 — Scale
- More cities/societies via ops configuration
- Android
- Optional richer ops tools, referrals, multi-car (if ever needed), etc.

---

## 17. Document Approval

| Role | Name | Status | Date |
|------|------|--------|------|
| Product owner | | Pending | |
| Operations | | Pending | |
| Design | | Pending | |
| Engineering lead | | Pending | |

**Review outcome:**
- [ ] Approved as-is for technical design
- [ ] Approved with noted changes
- [ ] Needs another revision

---

## 18. Appendix A — Illustrative Plan Matrix (placeholders)

*Replace with real commercial prices. Maintain a separate matrix **per city**.*

**Example: City = Bengaluru**

| Car size | Exterior only | + Interior 1×/mo | + Interior 2×/mo | + Interior 4×/mo |
|----------|---------------|------------------|------------------|------------------|
| Small | ₹A | ₹A+I1 | ₹A+I2 | ₹A+I4 |
| Medium | ₹B | ₹B+I1 | ₹B+I2 | ₹B+I4 |
| Large | ₹C | ₹C+I1 | ₹C+I2 | ₹C+I4 |

Service: **3 exterior-capable days per week per society**; interior count per plan is productized—specific interior days coordinated offline. Mid-month join: pro-rate of the chosen monthly cell through month end.

---

## 19. Appendix B — Glossary

| Term | Meaning |
|------|---------|
| **Subscription** | Paid plan entitling the user to scheduled cleans for the active period |
| **Calendar month** | Billing and entitlement window from the 1st to the last day of a month |
| **Pro-rated charge** | Partial month payment from signup date through month end on first join |
| **Service day** | One of the three weekly days when cleaners visit **that society** |
| **Exterior wash** | Outside clean of the vehicle |
| **Interior clean** | Inside cabin clean (vacuum/wipe as per SOP) |
| **Entitled** | Number of washes included for the current calendar month (active period) |
| **Completed** | Washes finished and recorded |
| **Pending** | Entitled washes not yet completed in the period |
| **Next-day retry** | Follow-up attempt the day after a missed/failed service visit |
| **Society** | Apartment complex / gated community where service is delivered |
| **Serviceable** | Society is onboarded and currently accepting subscribers (database flag) |
| **City tariff** | Price matrix for a given city (size × interior) |

---

## 20. Next Steps (after PRD approval)

1. PRD v1.3 is ready for technical design (optionally confirm Q15–Q17 defaults).
2. Produce a **Technical Design Document** covering:
   - iOS app architecture
   - FastAPI backend services & data model (cities, **live** societies only in consumer APIs, schedules, city pricing, single vehicle)
   - Calendar-month billing, pro-ration, cancel-at-month-end, **manual monthly pay**
   - Auth, payments, notifications
   - Minimal wash completion / missed / next-day retry mechanism (no full ops suite)
   - Environments, security, and rollout
3. UX wireframes for core flows (live society pick → pro-rated checkout → dashboard → monthly pay → cancel).
4. Ops runbook: society go-live, daily completion, next-day retries, offline interior coordination.

---

*End of PRD v1.3 — Clean My Car*
