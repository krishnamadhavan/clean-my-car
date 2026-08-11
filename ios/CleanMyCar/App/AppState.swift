import Foundation
import SwiftUI

/// Lightweight app-wide state for the scaffold (auth + API readiness).
@MainActor
final class AppState: ObservableObject {
    @Published var isAuthenticated = false
    @Published var apiStatus: APIHealthStatus = .unknown
    @Published var lastError: String?

    let apiClient: APIClient

    init(apiClient: APIClient = APIClient()) {
        self.apiClient = apiClient
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
