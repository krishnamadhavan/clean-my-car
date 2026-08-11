import Foundation

enum IndianPhone {
    private static let bodyPattern = /^[6-9]\d{9}$/

    /// Keep only digits and collapse common India prefixes to a 10-digit body.
    static func normalizeInput(_ raw: String) -> String {
        var digits = raw.filter(\.isNumber)
        if digits.hasPrefix("91"), digits.count >= 12 {
            digits = String(digits.dropFirst(2))
        } else if digits.hasPrefix("0"), digits.count == 11 {
            digits = String(digits.dropFirst())
        }
        return String(digits.prefix(10))
    }

    static func isValidBody(_ digits: String) -> Bool {
        digits.wholeMatch(of: bodyPattern) != nil
    }

    static func e164(fromBody digits: String) -> String {
        "+91\(digits)"
    }

    static func display(_ phone: String) -> String {
        let digits = phone.filter(\.isNumber)
        let body: String
        if digits.hasPrefix("91"), digits.count == 12 {
            body = String(digits.dropFirst(2))
        } else {
            body = digits
        }
        guard body.count == 10 else { return phone }
        let head = body.prefix(5)
        let tail = body.suffix(5)
        return "+91 \(head) \(tail)"
    }
}
