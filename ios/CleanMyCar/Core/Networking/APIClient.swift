import Foundation

enum APIClientError: LocalizedError {
    case invalidURL
    case badStatus(Int, String?)
    case decoding(Error)
    case transport(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API URL"
        case let .badStatus(code, body):
            if let body, !body.isEmpty {
                return "HTTP \(code): \(body)"
            }
            return "HTTP \(code)"
        case let .decoding(error):
            return "Could not decode response: \(error.localizedDescription)"
        case let .transport(error):
            return error.localizedDescription
        }
    }
}

/// Minimal HTTP client for the Clean My Car consumer API.
struct APIClient {
    var baseURL: URL
    var session: URLSession
    var decoder: JSONDecoder

    init(
        baseURL: URL = AppConfig.apiBaseURL,
        session: URLSession = .shared,
        decoder: JSONDecoder = JSONDecoder()
    ) {
        self.baseURL = baseURL
        self.session = session
        self.decoder = decoder
        self.decoder.keyDecodingStrategy = .convertFromSnakeCase
        self.decoder.dateDecodingStrategy = .iso8601
    }

    func health() async throws -> HealthResponse {
        try await get(path: "/api/v1/health")
    }

    func ready() async throws -> ReadyResponse {
        try await get(path: "/api/v1/ready")
    }

    private func get<T: Decodable>(path: String) async throws -> T {
        guard let url = URL(string: path, relativeTo: baseURL)?.absoluteURL else {
            throw APIClientError.invalidURL
        }
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            throw APIClientError.transport(error)
        }

        guard let http = response as? HTTPURLResponse else {
            throw APIClientError.badStatus(-1, nil)
        }
        guard (200 ..< 300).contains(http.statusCode) else {
            let body = String(data: data, encoding: .utf8)
            throw APIClientError.badStatus(http.statusCode, body)
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIClientError.decoding(error)
        }
    }
}

struct HealthResponse: Decodable, Sendable {
    let status: String
}

struct ReadyResponse: Decodable, Sendable {
    let status: String
    let database: String?
}
