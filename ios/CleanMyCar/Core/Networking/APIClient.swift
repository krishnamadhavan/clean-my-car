import Foundation

/// HTTP client for the consumer API (`/api/v1`).
///
/// Authenticated calls send the Keychain access token. A 401 triggers one
/// refresh-token rotation, then a single retry. A failed refresh signs the user out.
@MainActor
final class APIClient {
    let baseURL: URL
    let sessionStore: SessionStore
    var onSessionInvalidated: (() -> Void)?

    private let urlSession: URLSession
    private var refreshTask: Task<Void, Error>?

    init(
        baseURL: URL = AppConfig.apiBaseURL,
        sessionStore: SessionStore,
        urlSession: URLSession = .shared
    ) {
        self.baseURL = baseURL
        self.sessionStore = sessionStore
        self.urlSession = urlSession
    }

    func requestOTP(phone: String) async throws -> OTPRequestResponse {
        try await send(
            method: .post,
            path: APIPath.otpRequest,
            body: OTPRequestBody(phone: phone)
        )
    }

    func verifyOTP(phone: String, otp: String) async throws -> TokenPairResponse {
        try await send(
            method: .post,
            path: APIPath.otpVerify,
            body: OTPVerifyBody(phone: phone, otp: otp)
        )
    }

    func refreshTokens() async throws -> AccessTokenResponse {
        guard let refresh = sessionStore.refreshToken else {
            throw APIError.sessionExpired
        }
        return try await send(
            method: .post,
            path: APIPath.tokenRefresh,
            body: RefreshTokenBody(refreshToken: refresh),
            allowRefreshRetry: false
        )
    }

    func logout() async throws {
        guard let refresh = sessionStore.refreshToken else { return }
        let _: MessageResponse = try await send(
            method: .post,
            path: APIPath.logout,
            body: LogoutBody(refreshToken: refresh),
            allowRefreshRetry: false
        )
    }

    func fetchMe() async throws -> UserProfile {
        try await send(method: .get, path: APIPath.me, authenticated: true)
    }

    func updateMe(name: String?, email: String?) async throws -> UserProfile {
        try await send(
            method: .patch,
            path: APIPath.me,
            body: ProfileUpdateBody(name: name, email: email),
            authenticated: true
        )
    }

    func deactivateMe() async throws {
        let _: MessageResponse = try await send(
            method: .post,
            path: APIPath.deactivate,
            authenticated: true
        )
    }

    func deleteMe() async throws {
        let _: MessageResponse = try await send(
            method: .delete,
            path: APIPath.me,
            authenticated: true
        )
    }

    func fetchMyVehicle() async throws -> UserVehicle? {
        do {
            return try await send(method: .get, path: APIPath.meVehicle, authenticated: true)
        } catch let error as APIError {
            if case let .server(status, code, _) = error,
               status == 404 || code == "vehicle_not_found" || code == "not_found"
            {
                return nil
            }
            throw error
        }
    }

    func fetchMyLocation() async throws -> UserLocation {
        try await send(method: .get, path: APIPath.meLocation, authenticated: true)
    }

    private enum Method: String {
        case get = "GET"
        case post = "POST"
        case patch = "PATCH"
        case delete = "DELETE"
    }

    private func send<T: Decodable>(
        method: Method,
        path: String,
        body: (any Encodable)? = nil,
        authenticated: Bool = false,
        allowRefreshRetry: Bool = true
    ) async throws -> T {
        let data = try await perform(
            method: method,
            path: path,
            body: body,
            authenticated: authenticated,
            allowRefreshRetry: allowRefreshRetry
        )
        do {
            return try JSONCoders.decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decoding(error.localizedDescription)
        }
    }

    private func perform(
        method: Method,
        path: String,
        body: (any Encodable)?,
        authenticated: Bool,
        allowRefreshRetry: Bool
    ) async throws -> Data {
        guard let url = URL(string: path, relativeTo: baseURL)?.absoluteURL else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        if body != nil {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try encodeBody(body)
        }
        if authenticated, let token = sessionStore.accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await urlSession.data(for: request)
        } catch {
            throw APIError.transport(error.localizedDescription)
        }

        guard let http = response as? HTTPURLResponse else {
            throw APIError.server(status: -1, code: nil, message: "Invalid response")
        }

        if http.statusCode == 401, authenticated, allowRefreshRetry, sessionStore.hasSession {
            do {
                try await refreshSession()
                return try await perform(
                    method: method,
                    path: path,
                    body: body,
                    authenticated: authenticated,
                    allowRefreshRetry: false
                )
            } catch {
                invalidateSession()
                throw APIError.sessionExpired
            }
        }

        guard (200 ..< 300).contains(http.statusCode) else {
            let apiError = APIError.from(status: http.statusCode, data: data)
            if http.statusCode == 401 {
                if authenticated {
                    invalidateSession()
                }
                throw apiError
            }
            throw apiError
        }

        return data
    }

    private func encodeBody(_ body: (any Encodable)?) throws -> Data {
        guard let body else { return Data() }
        do {
            return try JSONCoders.encoder.encode(AnyEncodable(body))
        } catch {
            throw APIError.decoding(error.localizedDescription)
        }
    }

    private func refreshSession() async throws {
        if let refreshTask {
            try await refreshTask.value
            return
        }

        let task = Task { @MainActor in
            let tokens = try await refreshTokens()
            sessionStore.updateAfterRefresh(access: tokens.accessToken, refresh: tokens.refreshToken)
        }
        refreshTask = task
        defer { refreshTask = nil }
        try await task.value
    }

    private func invalidateSession() {
        sessionStore.clear()
        onSessionInvalidated?()
    }
}
