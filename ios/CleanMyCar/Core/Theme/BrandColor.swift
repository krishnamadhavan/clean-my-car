import SwiftUI

/// Clean My Car brand palette (aligned with ops-ui theme tokens).
enum BrandColor {
    static let primary = Color(hex: 0x4B_49_AC)
    static let primarySoft = Color(hex: 0x98_BD_FF)
    static let secondary = Color(hex: 0x7D_A0_FA)
    static let secondaryAlt = Color(hex: 0x79_78_E9)
    static let accent = Color(hex: 0xF3_79_7E)
    static let background = Color(hex: 0xF7_F8_FC)
}

extension Color {
    init(hex: UInt32, opacity: Double = 1) {
        let r = Double((hex >> 16) & 0xFF) / 255
        let g = Double((hex >> 8) & 0xFF) / 255
        let b = Double(hex & 0xFF) / 255
        self.init(.sRGB, red: r, green: g, blue: b, opacity: opacity)
    }
}
