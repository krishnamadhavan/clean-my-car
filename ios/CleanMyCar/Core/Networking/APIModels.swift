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

enum VehicleSizeTier: String, Decodable, Sendable {
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

struct VehicleMakeSummary: Decodable, Sendable, Equatable {
    let id: UUID
    let name: String
    let displayOrder: Int
}

struct VehicleModelSummary: Decodable, Sendable, Equatable {
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

struct CitySummary: Decodable, Sendable, Equatable, Identifiable {
    let id: UUID
    let name: String
    let state: String
    let displayOrder: Int
}

struct SocietySummary: Decodable, Sendable, Equatable, Identifiable {
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
