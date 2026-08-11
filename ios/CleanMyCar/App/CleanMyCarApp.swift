import SwiftUI

@main
struct CleanMyCarApp: App {
    @StateObject private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(appState)
                .tint(BrandColor.primary)
        }
    }
}
