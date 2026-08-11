import SwiftUI

/// Placeholder account tab.
struct AccountView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        NavigationStack {
            List {
                Section("Profile") {
                    Text("Phone OTP profile, vehicle, and plan management will live here.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                Section {
                    Button(role: .destructive) {
                        Task { await appState.signOut() }
                    } label: {
                        Label("Sign out", systemImage: "rectangle.portrait.and.arrow.right")
                    }
                }
            }
            .navigationTitle("Account")
        }
    }
}

#Preview {
    AccountView()
        .environmentObject(AppState())
}
