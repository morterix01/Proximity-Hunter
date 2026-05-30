import SwiftUI

struct ContentView: View {
    @StateObject private var vm = DealsViewModel()
    @Environment(\.openURL) private var openURL

    private let columns = [
        GridItem(.flexible(), spacing: 14),
        GridItem(.flexible(), spacing: 14),
    ]

    var body: some View {
        ZStack {
            Theme.background.ignoresSafeArea()

            VStack(spacing: 14) {
                header
                FilterBar(selected: $vm.selectedStore, scrapingActive: vm.isScrapingActive)

                content
            }
            .padding(.top, 8)
        }
        .preferredColorScheme(.dark)        // forced Dark Mode
        .task { await vm.load() }
    }

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("GlitchHunter")
                    .font(.largeTitle.weight(.black))
                    .foregroundStyle(Theme.green)
                Text("Caccia agli errori di prezzo")
                    .font(.caption)
                    .foregroundStyle(Theme.textSecondary)
            }
            Spacer()
        }
        .padding(.horizontal, 16)
    }

    @ViewBuilder
    private var content: some View {
        if vm.isLoading && vm.deals.isEmpty {
            Spacer(); ProgressView().tint(Theme.green); Spacer()
        } else if let error = vm.errorMessage, vm.deals.isEmpty {
            errorState(error)
        } else {
            ScrollView {
                LazyVGrid(columns: columns, spacing: 14) {
                    ForEach(vm.filteredDeals) { deal in
                        DealCard(deal: deal)
                            .onTapGesture { open(deal) }
                            .transition(.scale.combined(with: .opacity))
                    }
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 24)
                .animation(.spring(response: 0.4, dampingFraction: 0.75),
                           value: vm.filteredDeals)
            }
            .refreshable { await vm.refresh() }
        }
    }

    private func errorState(_ message: String) -> some View {
        VStack(spacing: 12) {
            Spacer()
            Image(systemName: "wifi.exclamationmark")
                .font(.largeTitle).foregroundStyle(Theme.red)
            Text(message).font(.footnote).foregroundStyle(Theme.textSecondary)
            Button("Riprova") { Task { await vm.load() } }
                .buttonStyle(.borderedProminent).tint(Theme.green)
            Spacer()
        }
    }

    /// Hand off to the installed store app for instant purchase; falls back to
    /// the web automatically when the app isn't installed.
    private func open(_ deal: Deal) {
        guard let url = deal.productURL else { return }
        openURL(url)
    }
}

#Preview {
    ContentView()
}
