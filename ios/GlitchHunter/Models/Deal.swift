import Foundation

enum DealTier: String, Codable {
    case error
    case super_ = "super"
    case none

    var label: String {
        switch self {
        case .error:  return "ERRORE PREZZO"
        case .super_: return "SUPER SCONTO"
        case .none:   return "SCONTO"
        }
    }
}

enum Store: String, Codable, CaseIterable, Identifiable {
    case amazon
    case unieuro
    case mediaworld

    var id: String { rawValue }
    var display: String {
        switch self {
        case .amazon:     return "Amazon"
        case .unieuro:    return "Unieuro"
        case .mediaworld: return "MediaWorld"
        }
    }
}

/// Mirrors backend `DealOut`.
struct Deal: Codable, Identifiable, Hashable {
    let id: Int
    let store: String
    let title: String
    let url: String
    let imageURL: String?
    let tier: DealTier
    let oldPrice: Double
    let newPrice: Double
    let dropPct: Double
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id, store, title, url, tier
        case imageURL = "image_url"
        case oldPrice = "old_price"
        case newPrice = "new_price"
        case dropPct  = "drop_pct"
        case createdAt = "created_at"
    }

    var storeEnum: Store? { Store(rawValue: store) }
    var productURL: URL? { URL(string: url) }

    var oldPriceText: String { Self.currency.string(from: oldPrice as NSNumber) ?? "" }
    var newPriceText: String { Self.currency.string(from: newPrice as NSNumber) ?? "" }
    var dropText: String { "-\(Int(dropPct.rounded()))%" }

    private static let currency: NumberFormatter = {
        let f = NumberFormatter()
        f.numberStyle = .currency
        f.currencyCode = "EUR"
        f.locale = Locale(identifier: "it_IT")
        return f
    }()
}
