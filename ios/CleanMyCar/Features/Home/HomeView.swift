import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        NavigationStack {
            List {
                Section {
                    Text("Hello, \(appState.profile?.displayName ?? "there")")
                        .font(.title3.weight(.semibold))
                    if let phone = appState.profile?.phone {
                        Text(IndianPhone.display(phone))
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                }

                Section("This month") {
                    Text(
                        "Wash progress (completed vs pending) will appear here after the subscription module is wired."
                    )
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Home")
            .refreshable {
                await appState.refreshProfile()
            }
        }
    }
}

#Preview {
    HomeView()
        .environmentObject(AppState())
}
