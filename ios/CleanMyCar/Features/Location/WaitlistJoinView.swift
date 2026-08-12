import SwiftUI

struct WaitlistJoinView: View {
    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss

    let city: CitySummary
    var onJoined: (() -> Void)?

    @State private var societyName = ""
    @State private var notes = ""
    @State private var isSubmitting = false
    @State private var errorMessage: String?
    @State private var didSucceed = false

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    LabeledContent("City", value: "\(city.name), \(city.state)")
                    TextField("Society / apartment name", text: $societyName)
                        .textInputAutocapitalization(.words)
                    TextField("Notes (optional)", text: $notes, axis: .vertical)
                        .lineLimit(3 ... 6)
                } footer: {
                    Text("We’ll use your account phone number. Ops will contact you when service is nearby.")
                }

                if let errorMessage {
                    Section {
                        Text(errorMessage)
                            .foregroundStyle(BrandColor.accent)
                    }
                }

                if didSucceed {
                    Section {
                        Label("You’re on the waitlist", systemImage: "checkmark.circle.fill")
                            .foregroundStyle(.green)
                    }
                }
            }
            .navigationTitle("Join waitlist")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    if isSubmitting {
                        ProgressView()
                    } else if didSucceed {
                        Button("Done") {
                            onJoined?()
                            dismiss()
                        }
                    } else {
                        Button("Submit") {
                            Task { await submit() }
                        }
                        .disabled(societyName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    }
                }
            }
        }
    }

    private func submit() async {
        let name = societyName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !name.isEmpty else { return }
        isSubmitting = true
        errorMessage = nil
        defer { isSubmitting = false }
        do {
            _ = try await appState.apiClient.joinWaitlist(
                cityId: city.id,
                societyName: name,
                notes: notes.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty
            )
            didSucceed = true
        } catch {
            errorMessage = error.localizedDescription
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
    WaitlistJoinView(
        city: CitySummary(
            id: UUID(),
            name: "Bengaluru",
            state: "Karnataka",
            displayOrder: 1
        )
    )
    .environmentObject(AppState())
}
