import SwiftUI

/// Join or **update** the single waitlist request (one per account; re-submit replaces it).
struct WaitlistJoinView: View {
    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss

    let city: CitySummary
    /// When set, form is an edit of the existing one-per-user waitlist row.
    var existing: WaitlistEntry?
    var onJoined: (() -> Void)?

    @State private var societyName = ""
    @State private var notes = ""
    @State private var isSubmitting = false
    @State private var errorMessage: String?
    @State private var didSucceed = false
    @State private var savedEntry: WaitlistEntry?

    private var isUpdate: Bool { existing != nil }

    var body: some View {
        NavigationStack {
            Form {
                if isUpdate {
                    Section {
                        Label {
                            Text(
                                "You already have one waitlist request. Saving will replace it with this city and society — not add a second entry."
                            )
                        } icon: {
                            Image(systemName: "info.circle.fill")
                                .foregroundStyle(BrandColor.secondary)
                        }
                        .font(.subheadline)
                    }
                }

                Section {
                    LabeledContent("City", value: "\(city.name), \(city.state)")
                    TextField("Society / apartment name", text: $societyName)
                        .textInputAutocapitalization(.words)
                    TextField("Notes (optional)", text: $notes, axis: .vertical)
                        .lineLimit(3 ... 6)
                } header: {
                    Text(isUpdate ? "Update request" : "Request")
                } footer: {
                    Text(
                        isUpdate
                            ? "Ops will see the updated building name. Your account phone number stays the same."
                            : "We’ll use your account phone number. You can only have one open waitlist request; changing it later updates the same entry."
                    )
                }

                if let existing, !didSucceed {
                    Section("Currently on file") {
                        LabeledContent(
                            "Society",
                            value: existing.societyName
                        )
                        if let existingCity = existing.city {
                            LabeledContent(
                                "City",
                                value: "\(existingCity.name), \(existingCity.state)"
                            )
                        }
                        LabeledContent("Status", value: existing.status.label)
                    }
                }

                if let errorMessage {
                    Section {
                        Text(errorMessage)
                            .foregroundStyle(BrandColor.accent)
                    }
                }

                if didSucceed {
                    Section {
                        Label(
                            isUpdate ? "Waitlist request updated" : "You’re on the waitlist",
                            systemImage: "checkmark.circle.fill"
                        )
                        .foregroundStyle(.green)
                        if let savedEntry {
                            Text(savedEntry.societyName)
                                .font(.subheadline.weight(.semibold))
                            if let city = savedEntry.city {
                                Text("\(city.name), \(city.state)")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
            .navigationTitle(isUpdate ? "Update waitlist" : "Join waitlist")
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
                        Button(isUpdate ? "Save changes" : "Submit") {
                            Task { await submit() }
                        }
                        .disabled(societyName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    }
                }
            }
            .onAppear {
                prefillFromExisting()
            }
        }
    }

    private func prefillFromExisting() {
        guard let existing else { return }
        // Prefer the city the user just picked; still prefill society/notes from the open request.
        societyName = existing.societyName
        notes = existing.notes ?? ""
    }

    private func submit() async {
        let name = societyName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !name.isEmpty else { return }
        isSubmitting = true
        errorMessage = nil
        defer { isSubmitting = false }
        do {
            let entry = try await appState.apiClient.joinWaitlist(
                cityId: city.id,
                societyName: name,
                notes: notes.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty
            )
            savedEntry = entry
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

#Preview("Join") {
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

#Preview("Update") {
    WaitlistJoinView(
        city: CitySummary(
            id: UUID(),
            name: "Bengaluru",
            state: "Karnataka",
            displayOrder: 1
        ),
        existing: WaitlistEntry(
            id: UUID(),
            cityId: UUID(),
            city: CitySummary(id: UUID(), name: "Bengaluru", state: "Karnataka", displayOrder: 1),
            societyName: "Old Society",
            phone: "+919876543210",
            notes: "Near tower 3",
            status: .pending,
            createdAt: Date(),
            updatedAt: Date()
        )
    )
    .environmentObject(AppState())
}
