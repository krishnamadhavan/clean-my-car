import Foundation
import SwiftUI

@MainActor
final class AppState: ObservableObject {
    enum Phase {
        case launching
        case signedOut
        case signedIn
    }

    @Published private(set) var phase: Phase = .launching
    @Published private(set) var profile: UserProfile?
    @Published var apiStatus: APIHealthStatus = .unknown
    @Published var lastError: String?

    let apiClient: APIClient
    let sessionStore: SessionStore

    var isAuthenticated: Bool { phase == .signedIn }

    init() {
        let store = SessionStore()
        sessionStore = store
        let client = APIClient(sessionStore: store)
        apiClient = client
        client.onSessionInvalidated = { [weak self] in
            self?.handleSessionInvalidated()
        }
    }

    func bootstrap() async {
        await checkAPIHealth()
        guard sessionStore.hasSession else {
            phase = .signedOut
            return
        }
        do {
            profile = try await apiClient.fetchMe()
            phase = .signedIn
        } catch {
            sessionStore.clear()
            profile = nil
            phase = .signedOut
        }
    }

    func checkAPIHealth() async {
        apiStatus = .checking
        lastError = nil
        do {
            let health = try await apiClient.health()
            apiStatus = health.status.lowercased() == "ok" ? .healthy : .unhealthy
        } catch {
            apiStatus = .unreachable
            lastError = error.localizedDescription
        }
    }

    func requestOTP(phone: String) async throws -> OTPChallenge {
        let response = try await apiClient.requestOTP(phone: phone)
        return OTPChallenge(response: response)
    }

    func verifyOTP(phone: String, otp: String) async throws {
        let tokens = try await apiClient.verifyOTP(phone: phone, otp: otp)
        sessionStore.setTokens(access: tokens.accessToken, refresh: tokens.refreshToken)
        profile = try await apiClient.fetchMe()
        phase = .signedIn
    }

    func refreshProfile() async {
        guard phase == .signedIn else { return }
        do {
            profile = try await apiClient.fetchMe()
        } catch {
            lastError = error.localizedDescription
        }
    }

    func updateProfile(name: String?, email: String?) async throws {
        profile = try await apiClient.updateMe(name: name, email: email)
    }

    func signOut() async {
        do {
            try await apiClient.logout()
        } catch {
            // Always clear local session even if the revoke call fails.
        }
        clearLocalSession()
    }

    func deactivateAccount() async throws {
        try await apiClient.deactivateMe()
        clearLocalSession()
    }

    func deleteAccount() async throws {
        try await apiClient.deleteMe()
        clearLocalSession()
    }

    private func handleSessionInvalidated() {
        clearLocalSession()
    }

    private func clearLocalSession() {
        sessionStore.clear()
        profile = nil
        phase = .signedOut
    }
}

enum APIHealthStatus: String {
    case unknown
    case checking
    case healthy
    case unhealthy
    case unreachable

    var label: String {
        switch self {
        case .unknown: return "Not checked"
        case .checking: return "Checking…"
        case .healthy: return "API reachable"
        case .unhealthy: return "API unhealthy"
        case .unreachable: return "API unreachable"
        }
    }
}
