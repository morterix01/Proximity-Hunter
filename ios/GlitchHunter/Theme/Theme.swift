import SwiftUI

/// Forced dark palette per spec.
/// Background #0f0f13 · Green accent #00ffa3 · Red accent #ff3366
enum Theme {
    static let background = Color(hex: 0x0F0F13)
    static let surface    = Color(hex: 0x1A1A22)
    static let green      = Color(hex: 0x00FFA3)   // "Super Sconto"
    static let red        = Color(hex: 0xFF3366)   // "Errore Prezzo"
    static let textPrimary   = Color.white
    static let textSecondary = Color.white.opacity(0.6)

    /// Accent color for a glitch tier.
    static func accent(for tier: DealTier) -> Color {
        switch tier {
        case .error: return red
        case .super_, .none: return green
        }
    }
}

extension Color {
    init(hex: UInt, alpha: Double = 1.0) {
        self.init(
            .sRGB,
            red: Double((hex >> 16) & 0xFF) / 255.0,
            green: Double((hex >> 8) & 0xFF) / 255.0,
            blue: Double(hex & 0xFF) / 255.0,
            opacity: alpha
        )
    }
}
