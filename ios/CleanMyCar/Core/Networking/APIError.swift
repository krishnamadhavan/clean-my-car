import Foundation

enum APIError: LocalizedError, Equatable {
    case invalidURL
    case transport(String)
    case decoding(String)
    case server(status: Int, code: String?, message: String)
    case unauthorized
    case sessionExpired

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API URL"
        case let .transport(message):
            return message
        case let .decoding(message):
            return "Could not read the server response. \(message)"
        case let .server(_, _, message):
            return message
        case .unauthorized, .sessionExpired:
            return "Your session expired. Please sign in again."
        }
    }

    var code: String? {
        switch self {
        case let .server(_, code, _):
            return code
        default:
            return nil
        }
    }

    static func from(status: Int, data: Data) -> APIError {
        if let payload = try? JSONCoders.decoder.decode(AppErrorPayload.self, from: data),
           let message = payload.resolvedMessage, !message.isEmpty
        {
            return .server(
                status: status,
                code: payload.code,
                message: friendlyMessage(code: payload.code, fallback: message, data: data)
            )
        }

        if let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
            if let detail = object["detail"] as? String, !detail.isEmpty {
                return .server(status: status, code: nil, message: detail)
            }
            if let items = object["detail"] as? [[String: Any]] {
                let messages = items.compactMap { $0["msg"] as? String }.filter { !$0.isEmpty }
                if !messages.isEmpty {
                    return .server(
                        status: status,
                        code: "validation_error",
                        message: messages.joined(separator: "\n")
                    )
                }
            }
        }

        if let raw = String(data: data, encoding: .utf8), !raw.isEmpty {
            return .server(status: status, code: nil, message: "HTTP \(status): \(raw)")
        }
        return .server(status: status, code: nil, message: "HTTP \(status)")
    }

    private static func friendlyMessage(code: String?, fallback: String, data: Data) -> String {
        switch code {
        case "otp_invalid":
            return fallback
        case "otp_cooldown":
            return fallback
        case "otp_rate_limited":
            return "Too many OTP requests. Please try again later."
        case "otp_attempts_exceeded":
            return "Too many incorrect attempts. Request a new code."
        case "account_inactive":
            return "This account is deactivated. Contact support to restore it."
        case "account_deleted":
            return "This account has been deleted."
        case "account_deletion_cooling_off":
            if let available = coolingOffDate(from: data) {
                let formatted = available.formatted(date: .abbreviated, time: .shortened)
                return "This number was recently deleted. You can sign up again after \(formatted)."
            }
            return fallback
        case "token_invalid", "refresh_invalid", "unauthorized":
            return fallback
        default:
            return fallback
        }
    }

    private static func coolingOffDate(from data: Data) -> Date? {
        guard
            let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
            let details = object["details"] as? [String: Any],
            let raw = details["available_at"] as? String
        else {
            return nil
        }
        return JSONCoders.parseDate(raw)
    }
}

private struct AppErrorPayload: Decodable {
    let code: String?
    let message: String?
    let detail: String?

    var resolvedMessage: String? {
        message ?? detail
    }
}
