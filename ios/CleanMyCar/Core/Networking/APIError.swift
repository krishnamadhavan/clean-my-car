import Foundation

enum APIError: LocalizedError, Equatable {
    case invalidURL
    case transport(String)
    case decoding(String)
    case server(status: Int, code: String?, message: String, fieldErrors: [String: String] = [:])
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
        case let .server(_, _, message, fieldErrors):
            if !message.isEmpty {
                return message
            }
            if let first = fieldErrors.values.first {
                return first
            }
            return "Request failed"
        case .unauthorized, .sessionExpired:
            return "Your session expired. Please sign in again."
        }
    }

    var code: String? {
        switch self {
        case let .server(_, code, _, _):
            return code
        default:
            return nil
        }
    }

    /// Field name (snake_case or last path segment) → user-facing message.
    var fieldErrors: [String: String] {
        switch self {
        case let .server(_, _, _, fieldErrors):
            return fieldErrors
        default:
            return [:]
        }
    }

    /// Lookup by API field name (`plate_number`) or camelCase (`plateNumber`).
    func message(forField field: String) -> String? {
        if let direct = fieldErrors[field] {
            return direct
        }
        let snake = field.apiSnakeCase
        if let viaSnake = fieldErrors[snake] {
            return viaSnake
        }
        // Match last segment of loc path, e.g. body.plate_number → plate_number
        for (key, value) in fieldErrors where key == field || key.hasSuffix(".\(field)") || key.hasSuffix(".\(snake)") {
            return value
        }
        return nil
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
                let fieldErrors = parseFieldErrors(items)
                let messages = items.compactMap { cleanValidationMessage($0["msg"] as? String) }
                if !messages.isEmpty || !fieldErrors.isEmpty {
                    return .server(
                        status: status,
                        code: "validation_error",
                        message: messages.joined(separator: "\n"),
                        fieldErrors: fieldErrors
                    )
                }
            }
        }

        if let raw = String(data: data, encoding: .utf8), !raw.isEmpty {
            return .server(status: status, code: nil, message: "HTTP \(status): \(raw)")
        }
        return .server(status: status, code: nil, message: "HTTP \(status)")
    }

    private static func parseFieldErrors(_ items: [[String: Any]]) -> [String: String] {
        var result: [String: String] = [:]
        for item in items {
            guard let msg = cleanValidationMessage(item["msg"] as? String) else { continue }
            let loc = item["loc"] as? [Any] ?? []
            let field = loc.compactMap { $0 as? String }.filter { $0 != "body" && $0 != "query" }.last
            if let field {
                result[field] = msg
            }
        }
        return result
    }

    private static func cleanValidationMessage(_ raw: String?) -> String? {
        guard var msg = raw?.trimmingCharacters(in: .whitespacesAndNewlines), !msg.isEmpty else {
            return nil
        }
        // Pydantic often prefixes with "Value error, "
        if msg.lowercased().hasPrefix("value error, ") {
            msg = String(msg.dropFirst("Value error, ".count))
        }
        return msg
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

private extension String {
    /// plateNumber → plate_number (simple camelCase → snake_case).
    var apiSnakeCase: String {
        var result = ""
        for character in self {
            if character.isUppercase {
                result.append("_")
                result.append(contentsOf: character.lowercased())
            } else {
                result.append(character)
            }
        }
        return result
    }
}
