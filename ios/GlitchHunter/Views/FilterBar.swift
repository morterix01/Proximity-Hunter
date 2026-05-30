import SwiftUI

struct FilterBar: View {
    @Binding var selected: Store?
    let scrapingActive: Bool

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 10) {
                chip(title: "Tutti", store: nil)
                ForEach(Store.allCases) { store in
                    chip(title: store.display, store: store)
                }
            }
            .padding(.horizontal, 16)
        }
    }

    @ViewBuilder
    private func chip(title: String, store: Store?) -> some View {
        let isOn = selected == store
        Button {
            withAnimation(.spring(response: 0.35, dampingFraction: 0.7)) {
                selected = store
            }
        } label: {
            HStack(spacing: 6) {
                if isOn && scrapingActive {
                    BlinkingDot()
                }
                Text(title)
                    .font(.subheadline.weight(.semibold))
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 9)
            .foregroundStyle(isOn ? Color.black : Theme.textPrimary)
            .background(
                Capsule().fill(isOn ? Theme.green : Theme.surface)
            )
        }
        .buttonStyle(.plain)
    }
}

/// Green blinking "Scraping Attivo" indicator.
struct BlinkingDot: View {
    @State private var on = false
    var body: some View {
        Circle()
            .fill(Color.black.opacity(0.9))
            .frame(width: 7, height: 7)
            .opacity(on ? 1 : 0.25)
            .onAppear {
                withAnimation(.easeInOut(duration: 0.6).repeatForever(autoreverses: true)) {
                    on = true
                }
            }
    }
}
