import Foundation

enum JSONCoders {
    static let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .custom(decodeISO8601)
        return decoder
    }()

    static let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        return encoder
    }()

    private static let fractional: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter
    }()

    private static let whole: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        return formatter
    }()

    /// Calendar dates from pricing (`yyyy-MM-dd`, Asia/Kolkata product calendar).
    private static let dayOnly: DateFormatter = {
        let formatter = DateFormatter()
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(identifier: "Asia/Kolkata") ?? .gmt
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }()

    private static func decodeISO8601(_ decoder: Decoder) throws -> Date {
        let container = try decoder.singleValueContainer()
        let raw = try container.decode(String.self)
        if let date = fractional.date(from: raw) ?? whole.date(from: raw) ?? dayOnly.date(from: raw) {
            return date
        }
        throw DecodingError.dataCorruptedError(
            in: container,
            debugDescription: "Unrecognized date: \(raw)"
        )
    }

    static func parseDate(_ raw: String) -> Date? {
        fractional.date(from: raw) ?? whole.date(from: raw) ?? dayOnly.date(from: raw)
    }

    static func formatDay(_ date: Date) -> String {
        dayOnly.string(from: date)
    }
}

/// Type-erased `Encodable` so `JSONEncoder` can encode an `any Encodable` value.
struct AnyEncodable: Encodable {
    private let encodeClosure: (Encoder) throws -> Void

    init(_ value: any Encodable) {
        encodeClosure = { encoder in
            try value.encode(to: encoder)
        }
    }

    func encode(to encoder: Encoder) throws {
        try encodeClosure(encoder)
    }
}
