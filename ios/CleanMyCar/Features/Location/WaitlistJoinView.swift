import SwiftUI

/// Join or **update** the single waitlist request (one per account; re-submit replaces it).
/// City and society are both editable on this form.
struct WaitlistJoinView: View {
    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss

    /// Preferred starting city (e.g. from society search). User can change it.
    var initialCity: CitySummary?
    /// When set, form is an edit of the existing one-per-user waitlist row.
    var existing: WaitlistEntry?
    var onJoined: (() -> Void)?

    @State private var cities: [CitySummary] = []
    @State private var selectedCity: CitySummary?
    @State private var societyName = ""
    @State private var notes = ""
    @State private var isLoadingCities = true
    @State private var isSubmitting = false
    @State private var errorMessage: String?
    @State private var didSucceed = false
    @State private var savedEntry: WaitlistEntry?

    private var isUpdate: Bool { existing != nil }

    private var canSubmit: Bool {
        selectedCity != nil
            && !societyName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !isSubmitting
    }

    var body: some View {
        NavigationStack {
            Form {
                if isUpdate {
                    Section {
                        Label {
                            Text(
                                "You already have one waitlist request. Saving will replace it with the city and society below — not add a second entry."
                            )
                        } icon: {
                            Image(systemName: "info.circle.fill")
                                .foregroundStyle(BrandColor.secondary)
                        }
                        .font(.subheadline)
                    }
                }

                Section {
                    if isLoadingCities {
                        ProgressView("Loading cities…")
                    } else if cities.isEmpty {
                        Text("No active cities available.")
                            .foregroundStyle(.secondary)
                    } else {
                        Picker("City", selection: $selectedCity) {
                            Text("Select city").tag(Optional<CitySummary>.none)
                            ForEach(cities) { city in
                                Text("\(city.name), \(city.state)").tag(Optional(city))
                            }
                        }
                    }

                    TextField("Society / apartment name", text: $societyName)
                        .textInputAutocapitalization(.words)
                    TextField("Notes (optional)", text: $notes, axis: .vertical)
                        .lineLimit(3 ... 6)
                } header: {
                    Text(isUpdate ? "Update request" : "Request")
                } footer: {
                    Text(
                        isUpdate
                            ? "You can change both city and building. Ops will see the updated request. Your account phone number stays the same."
                            : "We’ll use your account phone number. You can only have one open waitlist request; changing city or society later updates the same entry."
                    )
                }

                if let existing, !didSucceed {
                    Section("Currently on file") {
                        LabeledContent("Society", value: existing.societyName)
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
                        .disabled(!canSubmit)
                    }
                }
            }
            .task {
                await loadCitiesAndPrefill()
            }
        }
    }

    private func loadCitiesAndPrefill() async {
        isLoadingCities = true
        errorMessage = nil
        defer { isLoadingCities = false }
        do {
            cities = try await appState.apiClient.listCities()
                .sorted { $0.displayOrder < $1.displayOrder }
        } catch {
            errorMessage = error.localizedDescription
            return
        }

        if let existing {
            societyName = existing.societyName
            notes = existing.notes ?? ""
        }

        // Prefer: initialCity (context) → existing entry city → first city
        if let initialCity,
           let match = cities.first(where: { $0.id == initialCity.id })
        {
            selectedCity = match
        } else if let existing,
                  let match = cities.first(where: { $0.id == existing.cityId })
                  ?? existing.city.flatMap({ c in cities.first(where: { $0.id == c.id }) })
        {
            selectedCity = match
        } else if selectedCity == nil {
            selectedCity = cities.first
        }
    }

    private func submit() async {
        guard let selectedCity else {
            errorMessage = "Choose a city."
            return
        }
        let name = societyName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !name.isEmpty else { return }
        isSubmitting = true
        errorMessage = nil
        defer { isSubmitting = false }
        do {
            let entry = try await appState.apiClient.joinWaitlist(
                cityId: selectedCity.id,
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
        initialCity: CitySummary(
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
