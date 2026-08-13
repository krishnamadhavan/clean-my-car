import Foundation

enum APIPath {
    static func v1(_ path: String) -> String {
        let trimmed = path.hasPrefix("/") ? path : "/\(path)"
        return "\(AppConfig.apiPrefix)\(trimmed)"
    }

    static let otpRequest = v1("/auth/otp/request")
    static let otpVerify = v1("/auth/otp/verify")
    static let tokenRefresh = v1("/auth/token/refresh")
    static let logout = v1("/auth/logout")
    static let me = v1("/me")
    static let deactivate = v1("/me/deactivate")
    static let meVehicle = v1("/me/vehicle")
    static let meLocation = v1("/me/location")
    static let cities = v1("/cities")
    static let waitlist = v1("/waitlist")
    static let meWaitlist = v1("/me/waitlist")
    static let vehicleMakes = v1("/vehicle-makes")
    static let vehicleSizeTiers = v1("/vehicle-size-tiers")
    static let interiorOptions = v1("/interior-options")
    static let pricingQuote = v1("/pricing/quote")
    static let meSubscription = v1("/me/subscription")
    static let meSubscriptionCancel = v1("/me/subscription/cancel")
    static let meSubscriptionCancelUndo = v1("/me/subscription/cancel/undo")
    static let mePaymentIntents = v1("/me/payments/intents")
    static let mePayments = v1("/me/payments")
    static let meBillingSummary = v1("/me/billing/summary")
    static let meSchedule = v1("/me/schedule")
    static let meDashboard = v1("/me/dashboard")
    static let meWashesSummary = v1("/me/washes/summary")
    static let meWashes = v1("/me/washes")
    static let meDevices = v1("/me/devices")
    static let meNotificationPreferences = v1("/me/notification-preferences")

    static func meWash(_ id: UUID) -> String {
        v1("/me/washes/\(id.uuidString)")
    }

    static func meDevice(_ id: UUID) -> String {
        v1("/me/devices/\(id.uuidString)")
    }

    static func mePaymentIntent(_ id: UUID) -> String {
        v1("/me/payments/intents/\(id.uuidString)")
    }

    static func mePaymentIntentConfirm(_ id: UUID) -> String {
        v1("/me/payments/intents/\(id.uuidString)/confirm")
    }

    static func citySocieties(_ cityId: UUID) -> String {
        v1("/cities/\(cityId.uuidString)/societies")
    }

    static func society(_ societyId: UUID) -> String {
        v1("/societies/\(societyId.uuidString)")
    }

    static func vehicleModels(makeId: UUID) -> String {
        v1("/vehicle-makes/\(makeId.uuidString)/models")
    }

    static func cityPricing(_ cityId: UUID) -> String {
        v1("/cities/\(cityId.uuidString)/pricing")
    }
}

struct MessageResponse: Decodable, Sendable {
    let message: String
}

struct OTPRequestBody: Encodable {
    let phone: String
}

struct OTPRequestResponse: Decodable, Sendable {
    let message: String
    let phone: String
    let expiresAt: Date
    let resendAvailableAt: Date
    let debugOtp: String?
}

struct OTPVerifyBody: Encodable {
    let phone: String
    let otp: String
}

struct UserPublic: Decodable, Sendable, Equatable {
    let id: UUID
    let phone: String
    let name: String?
    let email: String?
    let isActive: Bool
    let createdAt: Date
}

struct TokenPairResponse: Decodable, Sendable {
    let accessToken: String
    let refreshToken: String
    let tokenType: String
    let expiresIn: Int
    let user: UserPublic
}

struct RefreshTokenBody: Encodable {
    let refreshToken: String
}

struct AccessTokenResponse: Decodable, Sendable {
    let accessToken: String
    let tokenType: String
    let expiresIn: Int
    let refreshToken: String?
}

struct LogoutBody: Encodable {
    let refreshToken: String
}

struct UserProfile: Decodable, Sendable, Equatable, Identifiable {
    let id: UUID
    let phone: String
    var name: String?
    var email: String?
    let isActive: Bool
    let createdAt: Date
    let hasVehicle: Bool
    let hasSubscription: Bool
    let deletedAt: Date?

    var displayName: String {
        if let name, !name.isEmpty {
            return name
        }
        return IndianPhone.display(phone)
    }
}

struct ProfileUpdateBody: Encodable {
    let name: String?
    let email: String?
}

struct OTPChallenge: Hashable, Identifiable, Sendable {
    let id = UUID()
    let phone: String
    let expiresAt: Date
    let resendAvailableAt: Date
    let debugOTP: String?

    init(response: OTPRequestResponse) {
        phone = response.phone
        expiresAt = response.expiresAt
        resendAvailableAt = response.resendAvailableAt
        debugOTP = response.debugOtp
    }

    init(phone: String, expiresAt: Date, resendAvailableAt: Date, debugOTP: String?) {
        self.phone = phone
        self.expiresAt = expiresAt
        self.resendAvailableAt = resendAvailableAt
        self.debugOTP = debugOTP
    }
}

// MARK: - Vehicle (Module 5)

enum VehicleSizeTier: String, Codable, Sendable, CaseIterable {
    case small
    case medium
    case large

    var label: String {
        switch self {
        case .small: return "Small"
        case .medium: return "Medium"
        case .large: return "Large"
        }
    }
}

struct VehicleMakeSummary: Decodable, Sendable, Equatable, Identifiable, Hashable {
    let id: UUID
    let name: String
    let displayOrder: Int
}

struct VehicleModelSummary: Decodable, Sendable, Equatable, Identifiable, Hashable {
    let id: UUID
    let makeId: UUID
    let name: String
    let sizeTier: VehicleSizeTier
    let displayOrder: Int
}

struct UserVehicle: Decodable, Sendable, Equatable, Identifiable {
    let id: UUID
    let modelId: UUID
    let make: VehicleMakeSummary?
    let model: VehicleModelSummary?
    let sizeTier: VehicleSizeTier
    let nickname: String?
    let plateNumber: String?
    let colour: String?
    let parkingSlot: String?
    let parkingTower: String?
    let createdAt: Date
    let updatedAt: Date

    var displayTitle: String {
        if let nickname, !nickname.isEmpty {
            return nickname
        }
        let makeName = make?.name
        let modelName = model?.name
        switch (makeName, modelName) {
        case let (make?, model?):
            return "\(make) \(model)"
        case let (make?, nil):
            return make
        case let (nil, model?):
            return model
        default:
            return "Your car"
        }
    }

    var subtitle: String {
        var parts: [String] = [sizeTier.label]
        if let plateNumber, !plateNumber.isEmpty {
            parts.append(plateNumber)
        }
        return parts.joined(separator: " · ")
    }
}

// MARK: - Location (Module 3)

struct CitySummary: Decodable, Sendable, Equatable, Identifiable, Hashable {
    let id: UUID
    let name: String
    let state: String
    let displayOrder: Int
}

struct SocietySummary: Decodable, Sendable, Equatable, Identifiable, Hashable {
    let id: UUID
    let cityId: UUID
    let name: String
    let addressLine: String?
    let serviceWeekdays: [Int]
    let serviceWeekdayLabels: [String]
    let displayOrder: Int
}

struct UserLocation: Decodable, Sendable, Equatable {
    let city: CitySummary?
    let society: SocietySummary?
    let updatedAt: Date?

    var hasLocation: Bool {
        city != nil || society != nil
    }
}

struct SocietyListResponse: Decodable, Sendable {
    let items: [SocietySummary]
    let total: Int
    let page: Int
    let pageSize: Int
}

struct SocietyDetail: Decodable, Sendable, Equatable, Identifiable {
    let id: UUID
    let cityId: UUID
    let name: String
    let addressLine: String?
    let serviceWeekdays: [Int]
    let serviceWeekdayLabels: [String]
    let displayOrder: Int
    let city: CitySummary
    let isServiceable: Bool
}

struct UserLocationUpdateBody: Encodable {
    let cityId: UUID
    let societyId: UUID
}

// MARK: - Waitlist (Module 4)

enum WaitlistStatus: String, Decodable, Sendable {
    case pending
    case contacted
    case converted
    case closed

    var label: String {
        rawValue.capitalized
    }
}

struct WaitlistCreateBody: Encodable {
    let cityId: UUID
    let societyName: String
    let phone: String?
    let notes: String?
}

struct WaitlistEntry: Decodable, Sendable, Identifiable, Equatable {
    let id: UUID
    let cityId: UUID
    let city: CitySummary?
    let societyName: String
    let phone: String
    let notes: String?
    let status: WaitlistStatus
    let createdAt: Date
    let updatedAt: Date
}

struct WaitlistListResponse: Decodable, Sendable {
    let items: [WaitlistEntry]
}

// MARK: - Vehicle catalog writes

struct VehicleModelListResponse: Decodable, Sendable {
    let items: [VehicleModelSummary]
}

struct VehiclePutBody: Encodable {
    let modelId: UUID
    let nickname: String?
    let plateNumber: String?
    let colour: String?
    let parkingSlot: String?
    let parkingTower: String?
}

/// PATCH body — only non-nil fields are sent (see `VehiclePatchBody.encode`).
struct VehiclePatchBody: Encodable {
    var modelId: UUID?
    var nickname: String?
    var plateNumber: String?
    var colour: String?
    var parkingSlot: String?
    var parkingTower: String?
    /// Fields to send as JSON null (clear on server).
    var clearFields: Set<String> = []

    enum CodingKeys: String, CodingKey {
        case modelId, nickname, plateNumber, colour, parkingSlot, parkingTower
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        if let modelId { try container.encode(modelId, forKey: .modelId) }
        try encodeOptional(nickname, key: .nickname, into: &container)
        try encodeOptional(plateNumber, key: .plateNumber, into: &container)
        try encodeOptional(colour, key: .colour, into: &container)
        try encodeOptional(parkingSlot, key: .parkingSlot, into: &container)
        try encodeOptional(parkingTower, key: .parkingTower, into: &container)
    }

    private func encodeOptional(
        _ value: String?,
        key: CodingKeys,
        into container: inout KeyedEncodingContainer<CodingKeys>
    ) throws {
        if clearFields.contains(key.stringValue) {
            try container.encodeNil(forKey: key)
        } else if let value {
            try container.encode(value, forKey: key)
        }
    }
}

struct VehicleSizeTierInfo: Decodable, Sendable, Identifiable, Equatable {
    let code: VehicleSizeTier
    let label: String
    let description: String

    var id: String { code.rawValue }
}

struct VehicleSizeTierListResponse: Decodable, Sendable {
    let items: [VehicleSizeTierInfo]
}

// MARK: - Pricing (Module 6)

struct InteriorOption: Decodable, Sendable, Identifiable, Equatable {
    let frequency: Int
    let code: String
    let label: String
    let description: String

    var id: Int { frequency }
}

struct InteriorOptionsResponse: Decodable, Sendable {
    let items: [InteriorOption]
}

struct SizePrice: Decodable, Sendable, Equatable {
    let sizeTier: VehicleSizeTier
    let monthlyAmountPaise: Int
}

struct InteriorPrice: Decodable, Sendable, Equatable {
    let interiorFrequency: Int
    let monthlyAmountPaise: Int
}

struct PricingMatrixCell: Decodable, Sendable, Equatable {
    let sizeTier: VehicleSizeTier
    let interiorFrequency: Int
    let baseAmountPaise: Int
    let interiorAmountPaise: Int
    let monthlyTotalPaise: Int
}

struct CityPricing: Decodable, Sendable, Equatable {
    let city: CitySummary
    let currency: String
    let amountsIncludeGst: Bool
    let gstRateBps: Int
    let sizePrices: [SizePrice]
    let interiorPrices: [InteriorPrice]
    let matrix: [PricingMatrixCell]
}

struct QuoteRequestBody: Encodable {
    let cityId: UUID
    let sizeTier: VehicleSizeTier
    let interiorFrequency: Int
    let startDate: String?
    let societyId: UUID?
}

struct MoneyBreakdown: Decodable, Sendable, Equatable {
    let baseAmountPaise: Int
    let gstPaise: Int
    let totalPaise: Int
}

struct QuoteResponse: Decodable, Sendable, Equatable {
    let city: CitySummary
    let sizeTier: VehicleSizeTier
    let interiorFrequency: Int
    let currency: String
    let amountsIncludeGst: Bool
    let gstRateBps: Int

    let fullMonthlyBasePaise: Int
    let fullMonthlyInteriorPaise: Int
    let fullMonthlyTotalPaise: Int
    let fullMonthlyBreakdown: MoneyBreakdown

    let startDate: Date
    let billingMonth: String
    let daysInMonth: Int
    let remainingDays: Int
    let amountDueNowPaise: Int
    let amountDueNowBreakdown: MoneyBreakdown
    let isProrated: Bool

    let nextBillingMonth: String
    let nextFullMonthAmountPaise: Int

    let exteriorEntitledThisPeriod: Int?
    let exteriorEntitledFullMonth: Int?
    let interiorEntitledThisPeriod: Int
    let interiorEntitledFullMonth: Int

    let society: SocietySummary?
    let serviceWeekdays: [Int]?
    let serviceWeekdayLabels: [String]?
    let proRateMethod: String
}

// MARK: - Subscription & payments (Modules 7–8)

enum SubscriptionStatus: String, Decodable, Sendable {
    case pendingPayment = "pending_payment"
    case active
    case cancelScheduled = "cancel_scheduled"
    case paused
    case expired
    case inactive

    var label: String {
        switch self {
        case .pendingPayment: return "Payment due"
        case .active: return "Active"
        case .cancelScheduled: return "Cancels end of month"
        case .paused: return "Paused"
        case .expired: return "Expired"
        case .inactive: return "Inactive"
        }
    }
}

struct UserSubscription: Decodable, Sendable, Equatable, Identifiable {
    let id: UUID
    let status: SubscriptionStatus
    let cityId: UUID
    let societyId: UUID
    let vehicleId: UUID?
    let sizeTier: VehicleSizeTier
    let interiorFrequency: Int
    let monthlyAmountPaise: Int
    let currency: String
    let periodStart: Date
    let periodEnd: Date
    let cancelAt: Date?
    let pausedFrom: Date?
    let pausedUntil: Date?
    let city: CitySummary?
    let society: SocietySummary?
    let createdAt: Date
    let updatedAt: Date

    var planLabel: String {
        let interior: String
        switch interiorFrequency {
        case 0: interior = "Exterior only"
        case 1: interior = "Interior 1×"
        case 2: interior = "Interior 2×"
        case 4: interior = "Interior 4×"
        default: interior = "Interior \(interiorFrequency)×"
        }
        return "\(sizeTier.label) · \(interior)"
    }
}

struct SubscriptionStartBody: Encodable {
    let interiorFrequency: Int
    let startDate: String?
}

struct SubscriptionStartResponse: Decodable, Sendable {
    let subscription: UserSubscription
    let paymentIntentId: UUID
    let amountDueNowPaise: Int
    let currency: String
    let quote: QuoteResponse
}

enum PaymentStatus: String, Decodable, Sendable {
    case pending
    case succeeded
    case failed
    case cancelled
}

enum PaymentKind: String, Decodable, Sendable {
    case subscriptionStart = "subscription_start"
    case renewal
    case adjustment
}

struct UserPayment: Decodable, Sendable, Identifiable, Equatable {
    let id: UUID
    let subscriptionId: UUID?
    let amountPaise: Int
    let currency: String
    let status: PaymentStatus
    let kind: PaymentKind
    let periodStart: Date?
    let periodEnd: Date?
    let provider: String
    let providerRef: String?
    let failureReason: String?
    let capturedAt: Date?
    let createdAt: Date
    let updatedAt: Date
}

struct PaymentIntentCreateBody: Encodable {
    let subscriptionId: UUID?
}

struct PaymentConfirmBody: Encodable {
    let providerRef: String?
}

struct PaymentListResponse: Decodable, Sendable {
    let items: [UserPayment]
    let total: Int
    let page: Int
    let pageSize: Int
}

struct BillingSummary: Decodable, Sendable {
    let hasSubscription: Bool
    let subscriptionId: UUID?
    let subscriptionStatus: String?
    let amountDuePaise: Int
    let currency: String
    let periodStart: Date?
    let periodEnd: Date?
    let isOverdue: Bool
    let openPaymentIntentId: UUID?
    let message: String
}

// MARK: - Schedule (WASH-04)

enum ScheduleOccurrenceKind: String, Decodable, Sendable {
    case scheduled
    case retryScheduled = "retry_scheduled"

    var systemImage: String {
        switch self {
        case .scheduled: return "drop.fill"
        case .retryScheduled: return "arrow.clockwise"
        }
    }

    var colorLabel: String {
        switch self {
        case .scheduled: return "Wash"
        case .retryScheduled: return "Retry"
        }
    }
}

struct ScheduleOccurrence: Decodable, Sendable, Identifiable, Equatable {
    let date: Date
    let weekday: Int
    let weekdayLabel: String
    let kind: ScheduleOccurrenceKind
    let title: String
    let note: String?
    let societyId: UUID?
    let societyName: String?

    var id: String {
        "\(JSONCoders.formatDay(date))-\(kind.rawValue)-\(title)"
    }
}

struct ScheduleResponse: Decodable, Sendable {
    let items: [ScheduleOccurrence]
    let serviceWeekdays: [Int]
    let serviceWeekdayLabels: [String]
    let subscriptionId: UUID?
    let subscriptionStatus: String?
    let fromDate: Date
    let untilDate: Date
    let message: String?
}

// MARK: - Washes & dashboard (Modules 9–10)

enum WashStatus: String, Decodable, Sendable {
    case scheduled
    case completed
    case missed
    case retryScheduled = "retry_scheduled"
    case skipped
}

struct WashRecord: Decodable, Sendable, Identifiable, Equatable {
    let id: UUID
    let subscriptionId: UUID
    let societyId: UUID
    let vehicleId: UUID?
    let serviceDate: Date
    let status: WashStatus
    let includesExterior: Bool
    let includesInterior: Bool
    let completedAt: Date?
    let missReason: String?
    let retryOfWashId: UUID?
    let notes: String?
    let createdAt: Date
    let updatedAt: Date
}

struct WashListResponse: Decodable, Sendable {
    let items: [WashRecord]
    let total: Int
    let page: Int
    let pageSize: Int
}

struct WashSummary: Decodable, Sendable {
    let yearMonth: String
    let exteriorEntitled: Int
    let exteriorCompleted: Int
    let exteriorPending: Int
    let exteriorMissed: Int
    let interiorIncluded: Int
    let interiorCompleted: Int
    let subscriptionId: UUID?
    let subscriptionStatus: String?
    let message: String?
}

struct DashboardNextService: Decodable, Sendable {
    let date: Date
    let kind: String
    let title: String
    let isRetry: Bool
    let washId: UUID?
}

struct DashboardResponse: Decodable, Sendable {
    let hasSubscription: Bool
    let subscription: UserSubscription?
    let vehicle: UserVehicle?
    let city: CitySummary?
    let society: SocietySummary?
    let serviceWeekdays: [Int]
    let serviceWeekdayLabels: [String]
    let washSummary: WashSummary?
    let nextService: DashboardNextService?
    let amountDuePaise: Int
    let currency: String
    let billingMessage: String?
    let message: String?
}

// MARK: - Notifications (Module 11)

struct DeviceRegistration: Decodable, Sendable, Identifiable {
    let id: UUID
    let token: String
    let platform: String
    let appVersion: String?
    let deviceName: String?
    let createdAt: Date
    let updatedAt: Date
}

struct DeviceUpsertBody: Encodable {
    let token: String
    let platform: String
    let appVersion: String?
    let deviceName: String?
}

struct NotificationPreferences: Decodable, Sendable {
    let washCompleted: Bool
    let paymentEvents: Bool
    let serviceReminders: Bool
    let marketing: Bool
    let updatedAt: Date?
}

struct NotificationPreferencesUpdateBody: Encodable {
    let washCompleted: Bool?
    let paymentEvents: Bool?
    let serviceReminders: Bool?
    let marketing: Bool?
}

// MARK: - Dashboard preview (until DASH-01 / WASH-* APIs exist)

/// Static month snapshot used by the Home dashboard until subscription & wash APIs ship.
struct DashboardPreview: Equatable, Sendable {
    let exteriorCompleted: Int
    let exteriorEntitled: Int
    let interiorCompleted: Int
    let interiorIncluded: Int
    let nextServiceDate: Date
    let isNextServiceRetry: Bool
    /// 0=Mon … 6=Sun
    let serviceWeekdays: [Int]
    let planLabel: String
    let monthlyPricePaise: Int
    let societyName: String
    let cityName: String

    var exteriorPending: Int {
        max(exteriorEntitled - exteriorCompleted, 0)
    }

    var exteriorProgress: Double {
        guard exteriorEntitled > 0 else { return 0 }
        return min(Double(exteriorCompleted) / Double(exteriorEntitled), 1)
    }

    var interiorProgress: Double {
        guard interiorIncluded > 0 else { return 0 }
        return min(Double(interiorCompleted) / Double(interiorIncluded), 1)
    }

    static let sample: DashboardPreview = {
        let calendar = Calendar(identifier: .gregorian)
        var components = calendar.dateComponents([.year, .month, .day], from: Date())
        // Next sample service: two days from “today” at 9:00 local.
        let base = calendar.date(byAdding: .day, value: 2, to: Date()) ?? Date()
        let next = calendar.date(bySettingHour: 9, minute: 0, second: 0, of: base) ?? base
        return DashboardPreview(
            exteriorCompleted: 7,
            exteriorEntitled: 12,
            interiorCompleted: 1,
            interiorIncluded: 2,
            nextServiceDate: next,
            isNextServiceRetry: false,
            serviceWeekdays: [0, 2, 4], // Mon / Wed / Fri
            planLabel: "Medium · Exterior + Interior 2×",
            monthlyPricePaise: 1_499_00,
            societyName: "Green Valley Apartments",
            cityName: "Bengaluru"
        )
    }()
}

enum WeekdayLabel {
    static let short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    static func shortName(for weekday: Int) -> String {
        guard weekday >= 0, weekday < short.count else { return "?" }
        return short[weekday]
    }

    static func joined(_ weekdays: [Int]) -> String {
        weekdays.sorted().map(shortName(for:)).joined(separator: " · ")
    }
}

enum INRFormat {
    static func rupees(fromPaise paise: Int) -> String {
        let rupees = Double(paise) / 100
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = "INR"
        formatter.currencySymbol = "₹"
        formatter.maximumFractionDigits = rupees.rounded() == rupees ? 0 : 2
        return formatter.string(from: NSNumber(value: rupees)) ?? "₹\(Int(rupees))"
    }
}
