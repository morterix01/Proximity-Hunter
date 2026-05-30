import SwiftUI

struct DealCard: View {
    let deal: Deal
    @State private var glitch = false

    private var accent: Color { Theme.accent(for: deal.tier) }

    var body: some View {
        ZStack(alignment: .topTrailing) {
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .fill(Theme.surface)
                .overlay(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .stroke(accent.opacity(0.35), lineWidth: 1)
                )

            VStack(alignment: .leading, spacing: 10) {
                thumbnail
                Text(deal.title)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(Theme.textPrimary)
                    .lineLimit(2)
                    .multilineTextAlignment(.leading)

                HStack(alignment: .firstTextBaseline, spacing: 8) {
                    Text(deal.oldPriceText)
                        .font(.footnote)
                        .strikethrough(true, color: Theme.textSecondary)
                        .foregroundStyle(Theme.textSecondary)
                    Text(deal.newPriceText)
                        .font(.title2.weight(.heavy))
                        .foregroundStyle(accent)
                }

                Text(deal.storeEnum?.display ?? deal.store)
                    .font(.caption2.weight(.bold))
                    .foregroundStyle(Theme.textSecondary)
            }
            .padding(14)

            badge
                .padding(10)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .shadow(color: accent.opacity(glitch ? 0.55 : 0.2), radius: glitch ? 16 : 8)
        .onAppear {
            // Neon/glitch pulse for "Errore Prezzo".
            guard deal.tier == .error else { return }
            withAnimation(.easeInOut(duration: 0.7).repeatForever(autoreverses: true)) {
                glitch = true
            }
        }
    }

    private var thumbnail: some View {
        AsyncImage(url: URL(string: deal.imageURL ?? "")) { phase in
            switch phase {
            case .success(let image):
                image.resizable().scaledToFit()
            default:
                RoundedRectangle(cornerRadius: 10).fill(Theme.background)
            }
        }
        .frame(height: 120)
        .frame(maxWidth: .infinity)
        .background(Theme.background)
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }

    private var badge: some View {
        Text(deal.dropText)
            .font(.caption.weight(.black))
            .foregroundStyle(.black)
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .background(
                Capsule().fill(accent)
            )
            .shadow(color: accent.opacity(0.9), radius: glitch ? 10 : 4)
            .overlay(
                Capsule().stroke(.white.opacity(0.25), lineWidth: 0.5)
            )
    }
}
