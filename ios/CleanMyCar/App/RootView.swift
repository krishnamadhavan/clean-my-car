import SwiftUI

struct RootView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        Group {
            switch appState.phase {
            case .launching:
                launching
            case .signedIn:
                MainTabView()
            case .signedOut:
                WelcomeView()
            }
        }
        .task {
            await appState.bootstrap()
        }
    }

    private var launching: some View {
        VStack(spacing: 16) {
            ProgressView()
            Text("Starting Clean My Car")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(BrandColor.background.ignoresSafeArea())
    }
}

#Preview {
    RootView()
        .environmentObject(AppState())
}
