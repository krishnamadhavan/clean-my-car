/** Shared TypeScript types for ops API responses (Modules 1–8). */

export type VehicleSizeTier = 'small' | 'medium' | 'large'
export type WaitlistStatus = 'pending' | 'contacted' | 'converted' | 'closed'
export type SubscriptionStatus =
  | 'pending_payment'
  | 'active'
  | 'cancel_scheduled'
  | 'paused'
  | 'expired'
  | 'inactive'
export type PaymentStatus = 'pending' | 'succeeded' | 'failed' | 'cancelled'
export type PaymentKind = 'subscription_start' | 'renewal' | 'adjustment'

export interface OpsOperator {
  id: string
  email: string
  name: string | null
  is_active: boolean
  roles: string[]
  last_login_at: string | null
  created_at: string
}

export interface OpsTokenPair {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  operator: OpsOperator
}

export interface OpsAccessToken {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface City {
  id: string
  name: string
  state: string
  is_active: boolean
  display_order: number
  created_at: string
  updated_at: string
}

export interface Society {
  id: string
  city_id: string
  name: string
  address_line: string | null
  service_weekdays: number[]
  is_serviceable: boolean
  display_order: number
  created_at: string
  updated_at: string
}

export interface OpsUserSummary {
  id: string
  phone: string
  name: string | null
  email: string | null
  is_active: boolean
  deleted_at: string | null
  city_id: string | null
  society_id: string | null
  created_at: string
}

export interface OpsUserDetail extends OpsUserSummary {
  city: { id: string; name: string; state: string; is_active: boolean } | null
  society: { id: string; name: string; is_serviceable: boolean } | null
  has_vehicle: boolean
  has_subscription: boolean
  updated_at: string
}

export interface WaitlistEntry {
  id: string
  user_id: string | null
  city_id: string
  city: { id: string; name: string; state: string } | null
  society_name: string
  phone: string
  notes: string | null
  status: WaitlistStatus
  created_at: string
  updated_at: string
}

export interface WaitlistSummary {
  total: number
  by_status: { status: WaitlistStatus; count: number }[]
  by_city: { city_id: string; city_name: string; count: number }[]
}

export interface VehicleMake {
  id: string
  name: string
  is_active: boolean
  display_order: number
  created_at: string
  updated_at: string
}

export interface VehicleModel {
  id: string
  make_id: string
  name: string
  size_tier: VehicleSizeTier
  is_active: boolean
  display_order: number
  created_at: string
  updated_at: string
}

export interface UserVehicle {
  id: string
  user_id: string
  model_id: string
  size_tier: VehicleSizeTier
  nickname: string | null
  plate_number: string | null
  colour: string | null
  parking_slot: string | null
  parking_tower: string | null
  make: VehicleMake | null
  model: VehicleModel | null
  created_at: string
  updated_at: string
}

export interface CityPricing {
  id: string
  city_id: string
  city: City
  currency: string
  amounts_include_gst: boolean
  gst_rate_bps: number
  is_active: boolean
  size_prices: { size_tier: VehicleSizeTier; monthly_amount_paise: number }[]
  interior_prices: { interior_frequency: number; monthly_amount_paise: number }[]
  matrix: {
    size_tier: VehicleSizeTier
    interior_frequency: number
    base_amount_paise: number
    interior_amount_paise: number
    monthly_total_paise: number
  }[]
  created_at: string
  updated_at: string
}

export interface MissingPricing {
  items: { city: City; has_inactive_pricing: boolean }[]
  total: number
}

export interface QuoteOut {
  city: { id: string; name: string; state: string }
  size_tier: VehicleSizeTier
  interior_frequency: number
  currency: string
  full_monthly_total_paise: number
  amount_due_now_paise: number
  is_prorated: boolean
  billing_month: string
  next_billing_month: string
  start_date: string
  days_in_month: number
  remaining_days: number
}

export interface ApiErrorBody {
  code?: string
  message?: string
  detail?: unknown
}

export interface OpsSubscription {
  id: string
  user_id: string
  user: {
    id: string
    phone: string
    name: string | null
    email: string | null
    is_active: boolean
  } | null
  city_id: string
  city: { id: string; name: string; state: string; display_order: number } | null
  society_id: string
  society: {
    id: string
    city_id: string
    name: string
    address_line: string | null
    service_weekdays: number[]
    service_weekday_labels: string[]
    display_order: number
  } | null
  vehicle_id: string | null
  size_tier: VehicleSizeTier
  interior_frequency: number
  status: SubscriptionStatus
  monthly_amount_paise: number
  currency: string
  period_start: string
  period_end: string
  cancel_at: string | null
  paused_from: string | null
  paused_until: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface OpsPayment {
  id: string
  user_id: string
  user: {
    id: string
    phone: string
    name: string | null
    email: string | null
    is_active: boolean
  } | null
  subscription_id: string | null
  amount_paise: number
  currency: string
  status: PaymentStatus
  kind: PaymentKind
  period_start: string | null
  period_end: string | null
  provider: string
  provider_ref: string | null
  failure_reason: string | null
  captured_at: string | null
  reconciled_at: string | null
  reconciled_by_operator_id: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export type WashStatus =
  | 'scheduled'
  | 'completed'
  | 'missed'
  | 'retry_scheduled'
  | 'skipped'

export type SupportTicketStatus = 'open' | 'in_progress' | 'resolved' | 'closed'
export type SupportTicketCategory = 'billing' | 'service' | 'account' | 'other'
export type LegalDocType = 'terms' | 'privacy' | 'cancellation'

export interface OpsOverview {
  cities_total: number
  cities_active: number
  societies_live: number
  waitlist_open: number
  subscriptions_active: number
  subscriptions_pending_payment: number
  washes_scheduled_today: number
  washes_completed_today: number
}

export interface OpsWash {
  id: string
  user_id: string
  subscription_id: string
  society_id: string
  vehicle_id: string | null
  service_date: string
  status: WashStatus
  includes_exterior: boolean
  includes_interior: boolean
  completed_at: string | null
  completed_by_operator_id: string | null
  miss_reason: string | null
  retry_of_wash_id: string | null
  notes: string | null
  user_phone: string | null
  user_name: string | null
  society_name: string | null
  created_at: string
  updated_at: string
}

export interface OpsSupportTicket {
  id: string
  user_id: string
  category: SupportTicketCategory
  message: string
  status: SupportTicketStatus
  wash_id: string | null
  payment_id: string | null
  ops_reply: string | null
  ops_notes: string | null
  user_phone: string | null
  user_name: string | null
  created_at: string
  updated_at: string
}

export interface FaqEntry {
  id: string
  question: string
  answer: string
  category: string
  display_order: number
}

export interface LegalDocument {
  doc_type: LegalDocType
  version: string
  title: string
  body: string | null
  url: string | null
  published_at: string | null
}

export interface AppConfig {
  min_ios_version: string
  force_update: boolean
  feature_flags: Record<string, unknown>
  support_whatsapp: string | null
  support_email: string | null
  support_phone: string | null
  support_whatsapp_url: string | null
}

export interface AuditEvent {
  id: string
  operator_id: string | null
  action: string
  resource_type: string
  resource_id: string | null
  details: Record<string, unknown> | null
  summary: string | null
  created_at: string
}
