import SwiftUI

/// Placeholder home / dashboard tab (subscription progress comes later).
struct HomeView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        NavigationStack {
            List {
                Section("Status") {
                    LabeledContent("API", value: appState.apiStatus.label)
                    LabeledContent("Base URL", value: AppConfig.apiBaseURL.absoluteString)
                }
                Section("This month") {
                    Text("Wash progress (completed vs pending) will appear here after the subscription module is wired.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                Section {
                    Button {
                        Task { await appState.checkAPIHealth() }
                    } label: {
                        Label("Refresh API health", systemImage: "arrow.clockwise")
                    }
                }
            }
            .navigationTitle("Home")
        }
    }
}

#Preview {
    HomeView()
        .environmentObject(AppState())
}
