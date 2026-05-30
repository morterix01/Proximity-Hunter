import SwiftUI

@main
struct GlitchHunterApp: App {
    // Firebase + APNs setup lives in the AppDelegate.
    @UIApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate

    var body: some Scene {
        WindowGroup {
            ContentView()
                .preferredColorScheme(.dark)
        }
    }
}
