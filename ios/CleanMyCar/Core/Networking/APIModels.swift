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
