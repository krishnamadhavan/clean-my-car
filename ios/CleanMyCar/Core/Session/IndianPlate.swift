import Foundation

/// Indian registration plate rules aligned with `backend/src/app/core/plate.py`.
///
/// - **Standard** (state RTO): e.g. `KA01AB1234`
/// - **Bharat (BH) series**: e.g. `26BH1234AB`
/// - Empty / optional is allowed.
enum IndianPlate {
    /// `SS` + RTO (1–2 digits) + series (1–3 letters) + 4 digits
    private static let standard = /^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$/
    /// `YY` + `BH` + 4 digits + 2 letters
    private static let bharat = /^[0-9]{2}BH[0-9]{4}[A-Z]{2}$/

    static let placeholder = "KA01AB1234 or 26BH1234AB"
    static let formatHint =
        "Standard: KA01AB1234 · BH series: 26BH1234AB. Spaces and hyphens are removed."

    static let invalidMessage =
        "Invalid Indian vehicle plate. Use standard format (e.g. KA01AB1234) or BH series (e.g. 26BH1234AB)."

    /// Strip spaces/hyphens and uppercase (same as backend normalization).
    static func normalizeInput(_ raw: String) -> String {
        raw
            .uppercased()
            .replacingOccurrences(of: " ", with: "")
            .replacingOccurrences(of: "-", with: "")
            .filter { $0.isLetter || $0.isNumber }
    }

    /// Empty → valid optional plate (`nil`). Non-empty must match standard or BH.
    static func validate(_ raw: String) -> (normalized: String?, error: String?) {
        let cleaned = normalizeInput(raw)
        if cleaned.isEmpty {
            return (nil, nil)
        }
        if cleaned.wholeMatch(of: standard) != nil || cleaned.wholeMatch(of: bharat) != nil {
            return (cleaned, nil)
        }
        return (nil, invalidMessage)
    }

    static func isValidOrEmpty(_ raw: String) -> Bool {
        validate(raw).error == nil
    }

    enum Kind {
        case empty
        case standard
        case bharat
        case invalid
    }

    static func kind(of raw: String) -> Kind {
        let cleaned = normalizeInput(raw)
        if cleaned.isEmpty { return .empty }
        if cleaned.wholeMatch(of: standard) != nil { return .standard }
        if cleaned.wholeMatch(of: bharat) != nil { return .bharat }
        return .invalid
    }
}
