import SafariServices
import SwiftUI

/// Wraps SFSafariViewController for in-app browsing when you prefer not to
/// hand off to the external store app.
struct SafariView: UIViewControllerRepresentable {
    let url: URL

    func makeUIViewController(context: Context) -> SFSafariViewController {
        SFSafariViewController(url: url)
    }

    func updateUIViewController(_ controller: SFSafariViewController, context: Context) {}
}
