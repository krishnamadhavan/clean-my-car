import SwiftUI

struct RootView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        Group {
            if appState.isAuthenticated {
                MainTabView()
            } else {
                WelcomeView()
            }
        }
        .task {
            await appState.checkAPIHealth()
        }
    }
}

#Preview {
    RootView()
        .environmentObject(AppState())
}
