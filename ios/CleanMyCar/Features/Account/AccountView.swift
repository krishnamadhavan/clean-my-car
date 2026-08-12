import SwiftUI

struct AccountView: View {
    @EnvironmentObject private var appState: AppState
    @State private var isEditing = false
    @State private var isSigningOut = false
    @State private var isWorking = false
    @State private var confirm: AccountConfirm?
    @State private var banner: String?

    var body: some View {
        NavigationStack {
            List {
                profileSection
                modulesSection
                statusSection
                sessionSection
                dangerSection
            }
            .navigationTitle("Account")
            .refreshable {
                await appState.refreshProfile()
            }
            .sheet(isPresented: $isEditing) {
                EditProfileView()
            }
            .overlay {
                if isWorking {
                    ProgressView()
                        .padding(20)
                        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
                }
            }
            .alert("Something went wrong", isPresented: Binding(
                get: { banner != nil },
                set: { if !$0 { banner = nil } }
            )) {
                Button("OK", role: .cancel) { banner = nil }
            } message: {
                Text(banner ?? "")
            }
            .confirmationDialog(
                confirm?.title ?? "",
                isPresented: Binding(
                    get: { confirm != nil },
                    set: { if !$0 { confirm = nil } }
                ),
                titleVisibility: .visible
            ) {
                if let confirm {
                    Button(confirm.actionTitle, role: .destructive) {
                        Task { await perform(confirm) }
                    }
                    Button("Cancel", role: .cancel) {}
                }
            } message: {
                Text(confirm?.message ?? "")
            }
        }
    }

    @ViewBuilder
    private var profileSection: some View {
        Section("Profile") {
            if let profile = appState.profile {
                LabeledContent("Name", value: profile.name?.nilIfEmpty ?? "Not set")
                LabeledContent("Phone", value: IndianPhone.display(profile.phone))
                LabeledContent("Email", value: profile.email?.nilIfEmpty ?? "Not set")
                Button {
                    isEditing = true
                } label: {
                    Label("Edit name and email", systemImage: "pencil")
                }
            } else {
                Text("Loading profile…")
                    .foregroundStyle(.secondary)
            }
        }
    }

    private var modulesSection: some View {
        Section("Service setup") {
            NavigationLink {
                LocationHomeView()
                    .environmentObject(appState)
            } label: {
                Label("Location & society", systemImage: "building.2.fill")
            }
            NavigationLink {
                VehicleHomeView()
                    .environmentObject(appState)
            } label: {
                Label("Vehicle", systemImage: "car.fill")
            }
            NavigationLink {
                WaitlistListView()
                    .environmentObject(appState)
            } label: {
                Label("Waitlist", systemImage: "bell.fill")
            }
        }
    }

    @ViewBuilder
    private var statusSection: some View {
        Section("Account") {
            if let profile = appState.profile {
                LabeledContent("Status", value: profile.isActive ? "Active" : "Inactive")
                LabeledContent("Vehicle", value: profile.hasVehicle ? "Registered" : "Not added yet")
                LabeledContent("Subscription", value: profile.hasSubscription ? "Active" : "None")
                LabeledContent("Member since", value: profile.createdAt.formatted(date: .abbreviated, time: .omitted))
            }
        }
    }

    private var sessionSection: some View {
        Section {
            Button(role: .destructive) {
                Task { await signOut() }
            } label: {
                if isSigningOut {
                    ProgressView()
                } else {
                    Label("Sign out", systemImage: "rectangle.portrait.and.arrow.right")
                }
            }
            .disabled(isSigningOut || isWorking)
        }
    }

    private var dangerSection: some View {
        Section {
            Button("Deactivate account", role: .destructive) {
                confirm = .deactivate
            }
            Button("Delete account", role: .destructive) {
                confirm = .delete
            }
        } header: {
            Text("Danger zone")
        } footer: {
            Text(
                "Deactivate blocks sign-in until support restores the account. Delete clears your profile; the same number can sign up again after a one-day cool-off."
            )
        }
    }

    private func signOut() async {
        isSigningOut = true
        defer { isSigningOut = false }
        await appState.signOut()
    }

    private func perform(_ confirm: AccountConfirm) async {
        isWorking = true
        defer { isWorking = false }
        do {
            switch confirm {
            case .deactivate:
                try await appState.deactivateAccount()
            case .delete:
                try await appState.deleteAccount()
            }
        } catch {
            banner = error.localizedDescription
        }
    }
}

private enum AccountConfirm {
    case deactivate
    case delete

    var title: String {
        switch self {
        case .deactivate: return "Deactivate this account?"
        case .delete: return "Delete this account?"
        }
    }

    var message: String {
        switch self {
        case .deactivate:
            return "You will be signed out and cannot sign in again until support reactivates the account."
        case .delete:
            return "Your name and email will be cleared and you will be signed out. You can create a new account with this number after the cool-off period."
        }
    }

    var actionTitle: String {
        switch self {
        case .deactivate: return "Deactivate"
        case .delete: return "Delete account"
        }
    }
}

private extension String {
    var nilIfEmpty: String? {
        let trimmed = trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }
}

#Preview {
    AccountView()
        .environmentObject(AppState())
}
