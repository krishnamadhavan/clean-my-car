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
            if case let .server(status, code, _, _) = error,
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

    func setMyLocation(cityId: UUID, societyId: UUID) async throws -> UserLocation {
        try await send(
            method: .put,
            path: APIPath.meLocation,
            body: UserLocationUpdateBody(cityId: cityId, societyId: societyId),
            authenticated: true
        )
    }

    func listCities() async throws -> [CitySummary] {
        try await send(method: .get, path: APIPath.cities)
    }

    func listSocieties(
        cityId: UUID,
        q: String? = nil,
        page: Int = 1,
        pageSize: Int = 50
    ) async throws -> SocietyListResponse {
        var path = "\(APIPath.citySocieties(cityId))?page=\(page)&page_size=\(pageSize)"
        if let q, !q.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            let encoded = q.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? q
            path += "&q=\(encoded)"
        }
        return try await send(method: .get, path: path)
    }

    func getSociety(id: UUID) async throws -> SocietyDetail {
        try await send(method: .get, path: APIPath.society(id))
    }

    func joinWaitlist(
        cityId: UUID,
        societyName: String,
        phone: String? = nil,
        notes: String? = nil
    ) async throws -> WaitlistEntry {
        try await send(
            method: .post,
            path: APIPath.waitlist,
            body: WaitlistCreateBody(
                cityId: cityId,
                societyName: societyName,
                phone: phone,
                notes: notes
            ),
            authenticated: true
        )
    }

    func listMyWaitlist() async throws -> WaitlistListResponse {
        try await send(method: .get, path: APIPath.meWaitlist, authenticated: true)
    }

    func listVehicleMakes() async throws -> [VehicleMakeSummary] {
        try await send(method: .get, path: APIPath.vehicleMakes)
    }

    func listVehicleModels(makeId: UUID) async throws -> [VehicleModelSummary] {
        let response: VehicleModelListResponse = try await send(
            method: .get,
            path: APIPath.vehicleModels(makeId: makeId)
        )
        return response.items
    }

    func putMyVehicle(
        modelId: UUID,
        nickname: String? = nil,
        plateNumber: String? = nil,
        colour: String? = nil,
        parkingSlot: String? = nil,
        parkingTower: String? = nil
    ) async throws -> UserVehicle {
        try await send(
            method: .put,
            path: APIPath.meVehicle,
            body: VehiclePutBody(
                modelId: modelId,
                nickname: nickname,
                plateNumber: plateNumber,
                colour: colour,
                parkingSlot: parkingSlot,
                parkingTower: parkingTower
            ),
            authenticated: true
        )
    }

    func patchMyVehicle(_ body: VehiclePatchBody) async throws -> UserVehicle {
        try await send(
            method: .patch,
            path: APIPath.meVehicle,
            body: body,
            authenticated: true
        )
    }

    func deleteMyVehicle() async throws {
        let _: MessageResponse = try await send(
            method: .delete,
            path: APIPath.meVehicle,
            authenticated: true
        )
    }

    func listVehicleSizeTiers() async throws -> [VehicleSizeTierInfo] {
        let response: VehicleSizeTierListResponse = try await send(
            method: .get,
            path: APIPath.vehicleSizeTiers
        )
        return response.items
    }

    func listInteriorOptions() async throws -> [InteriorOption] {
        let response: InteriorOptionsResponse = try await send(
            method: .get,
            path: APIPath.interiorOptions
        )
        return response.items
    }

    func getCityPricing(cityId: UUID) async throws -> CityPricing {
        try await send(method: .get, path: APIPath.cityPricing(cityId))
    }

    func createQuote(
        cityId: UUID,
        sizeTier: VehicleSizeTier,
        interiorFrequency: Int,
        startDate: Date? = nil,
        societyId: UUID? = nil
    ) async throws -> QuoteResponse {
        try await send(
            method: .post,
            path: APIPath.pricingQuote,
            body: QuoteRequestBody(
                cityId: cityId,
                sizeTier: sizeTier,
                interiorFrequency: interiorFrequency,
                startDate: startDate.map(JSONCoders.formatDay),
                societyId: societyId
            )
        )
    }

    private enum Method: String {
        case get = "GET"
        case post = "POST"
        case put = "PUT"
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
