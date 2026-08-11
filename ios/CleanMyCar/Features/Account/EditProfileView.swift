import SwiftUI

struct EditProfileView: View {
    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss

    @State private var name = ""
    @State private var email = ""
    @State private var isSaving = false
    @State private var formError: String?

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("Name", text: $name)
                        .textContentType(.name)
                        .textInputAutocapitalization(.words)
                    TextField("Email (optional)", text: $email)
                        .textContentType(.emailAddress)
                        .keyboardType(.emailAddress)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                } footer: {
                    Text("Leave a field empty to clear it on the server.")
                }

                if let formError {
                    Section {
                        Text(formError)
                            .foregroundStyle(BrandColor.accent)
                    }
                }
            }
            .navigationTitle("Edit profile")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                        .disabled(isSaving)
                }
                ToolbarItem(placement: .confirmationAction) {
                    if isSaving {
                        ProgressView()
                    } else {
                        Button("Save") {
                            Task { await save() }
                        }
                        .disabled(!canSave)
                    }
                }
            }
            .onAppear {
                name = appState.profile?.name ?? ""
                email = appState.profile?.email ?? ""
            }
        }
    }

    private var canSave: Bool {
        let trimmedEmail = email.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmedEmail.isEmpty || trimmedEmail.contains("@")
    }

    private func save() async {
        let trimmedName = name.trimmingCharacters(in: .whitespacesAndNewlines)
        let trimmedEmail = email.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        if !trimmedEmail.isEmpty, !isLikelyEmail(trimmedEmail) {
            formError = "Enter a valid email address, or leave it blank."
            return
        }

        isSaving = true
        formError = nil
        defer { isSaving = false }
        do {
            try await appState.updateProfile(
                name: trimmedName.isEmpty ? nil : trimmedName,
                email: trimmedEmail.isEmpty ? nil : trimmedEmail
            )
            dismiss()
        } catch {
            formError = error.localizedDescription
        }
    }

    private func isLikelyEmail(_ value: String) -> Bool {
        value.wholeMatch(of: /^[^@\s]+@[^@\s]+\.[^@\s]+$/) != nil
    }
}

#Preview {
    EditProfileView()
        .environmentObject(AppState())
}
