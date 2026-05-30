import Foundation

@MainActor
final class DealsViewModel: ObservableObject {
    @Published var deals: [Deal] = []
    @Published var selectedStore: Store? = nil      // nil == "Tutti"
    @Published var isLoading = false
    @Published var isScrapingActive = true          // drives the blinking status dot
    @Published var errorMessage: String?

    private let api = NetworkManager.shared

    var filteredDeals: [Deal] {
        guard let store = selectedStore else { return deals }
        return deals.filter { $0.storeEnum == store }
    }

    func load() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            deals = try await api.fetchDeals()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func refresh() async {
        await load()
    }

    func select(_ store: Store?) {
        selectedStore = store
    }
}
