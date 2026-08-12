# Database ER diagram

Visual ER diagram in the style of a **pgAdmin / Workbench export** (table boxes + FK lines).

## Diagram

![Database ER diagram](./diagrams/database-er.svg)

**File:** [`docs/diagrams/database-er.svg`](./diagrams/database-er.svg)

- Open the SVG in a browser, Preview, or VS Code to zoom/export (e.g. export PNG from the viewer if needed).
- Gray header on `otp_challenges` = no FK to `users` (OTP can run before signup).

## Maintenance rule (mandatory)

**Update `docs/diagrams/database-er.svg` whenever the database design changes** (same PR as models + Alembic):

- Add/remove/rename tables or columns
- Change FKs, nullability, uniqueness, or `ON DELETE`

Also refresh the short notes below if relationships change.

## Current tables

| Table | Role |
|-------|------|
| `cities` | Active service cities; **`display_order` unique** |
| `societies` | Live apartment societies + 3 service weekdays |
| `users` | Accounts; optional `city_id` / `society_id` |
| `refresh_tokens` | Hashed refresh sessions |
| `otp_challenges` | Phone OTP challenges (no user FK) |
| `waitlist_entries` | Demand capture when society not live (Module 4); one per user |
| `vehicle_makes` | Car brands (ops catalog); **`display_order` unique** |
| `vehicle_models` | Models under a make + **ops-defined** size_tier |
| `vehicles` | One vehicle per user; `model_id` + size_tier snapshot |
| `city_pricing` | Per-city GST/currency presentation (Module 6) |
| `city_size_prices` | Base monthly exterior price by size (paise) |
| `city_interior_prices` | Interior add-on by frequency 0/1/2/4 (paise) |
| `ops_operators` | Ops staff (email/password, roles) |
| `ops_refresh_tokens` | Ops session refresh tokens (hashed) |
| `subscriptions` | Calendar-month plans (Module 7); status + period + cancel_at |
| `payments` | Payment intents / captures (Module 8); reconcile by ops |

## Relationships

| FK | Parent | Child | ON DELETE |
|----|--------|-------|-----------|
| `societies.city_id` | `cities` | `societies` | CASCADE |
| `users.city_id` | `cities` | `users` | SET NULL |
| `users.society_id` | `societies` | `users` | SET NULL |
| `refresh_tokens.user_id` | `users` | `refresh_tokens` | CASCADE |
| `waitlist_entries.user_id` | `users` | `waitlist_entries` | SET NULL (unique when set — one entry per user) |
| `waitlist_entries.city_id` | `cities` | `waitlist_entries` | CASCADE |
| `vehicle_models.make_id` | `vehicle_makes` | `vehicle_models` | CASCADE |
| `vehicles.user_id` | `users` | `vehicles` | CASCADE (unique) |
| `vehicles.model_id` | `vehicle_models` | `vehicles` | RESTRICT |
| `city_pricing.city_id` | `cities` | `city_pricing` | CASCADE (unique) |
| `city_size_prices.pricing_id` | `city_pricing` | `city_size_prices` | CASCADE |
| `city_interior_prices.pricing_id` | `city_pricing` | `city_interior_prices` | CASCADE |
| `ops_refresh_tokens.operator_id` | `ops_operators` | `ops_refresh_tokens` | CASCADE |
| `subscriptions.user_id` | `users` | `subscriptions` | CASCADE |
| `subscriptions.city_id` | `cities` | `subscriptions` | RESTRICT |
| `subscriptions.society_id` | `societies` | `subscriptions` | RESTRICT |
| `subscriptions.vehicle_id` | `vehicles` | `subscriptions` | SET NULL |
| `payments.user_id` | `users` | `payments` | CASCADE |
| `payments.subscription_id` | `subscriptions` | `payments` | SET NULL |
| `payments.reconciled_by_operator_id` | `ops_operators` | `payments` | SET NULL |

## Alembic map

| Revision | Summary |
|----------|---------|
| `20260731_0001` | users, otp_challenges, refresh_tokens |
| `20260801_0002` | users.deleted_at |
| `20260801_0003` | cities, societies, user location FKs |
| `20260802_0004` | waitlist_entries |
| `20260802_0005` | vehicle_makes, vehicle_models, vehicles |
| `20260802_0006` | city_pricing, city_size_prices, city_interior_prices |
| `20260803_0007` | ops_operators, ops_refresh_tokens |
| `20260807_0008` | cities.display_order unique index |
| `20260807_0009` | vehicle_makes.display_order unique index |
| `20260812_0010` | subscriptions, payments |
