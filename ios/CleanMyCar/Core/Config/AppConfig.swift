import Foundation

/// Runtime configuration for the consumer app.
///
/// Override with launch argument or environment:
/// - `-API_BASE_URL` / `API_BASE_URL` (e.g. `http://127.0.0.1:8000`)
enum AppConfig {
    /// Consumer API origin (no trailing slash).
    ///
    /// - Simulator: `http://127.0.0.1:8000` reaches the host Docker API.
    /// - Physical device: use your Mac's LAN IP, e.g. `http://192.168.1.20:8000`.
    static var apiBaseURL: URL {
        if let override = ProcessInfo.processInfo.environment["API_BASE_URL"],
           let url = URL(string: override), !override.isEmpty
        {
            return url
        }
        let args = ProcessInfo.processInfo.arguments
        if let idx = args.firstIndex(of: "-API_BASE_URL"),
           args.indices.contains(idx + 1),
           let url = URL(string: args[idx + 1])
        {
            return url
        }
        // Default for iOS Simulator + local `make up`
        return URL(string: "http://127.0.0.1:8000")!
    }

    /// Consumer API path prefix (matches FastAPI router).
    static let apiPrefix = "/api/v1"

    static var apiRoot: URL {
        apiBaseURL.appendingPathComponent(apiPrefix.trimmingCharacters(in: CharacterSet(charactersIn: "/")))
    }
}
