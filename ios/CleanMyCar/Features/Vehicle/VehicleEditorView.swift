import SwiftUI

/// Register or replace the single vehicle (VEH-06/07 + VEH-02).
struct VehicleEditorView: View {
    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss

    var existing: UserVehicle?
    var onSaved: ((UserVehicle) -> Void)?

    @State private var makes: [VehicleMakeSummary] = []
    @State private var models: [VehicleModelSummary] = []
    @State private var selectedMake: VehicleMakeSummary?
    @State private var selectedModel: VehicleModelSummary?

    @State private var nickname = ""
    @State private var plateNumber = ""
    @State private var colour = ""
    @State private var parkingSlot = ""
    @State private var parkingTower = ""

    @State private var isLoadingMakes = true
    @State private var isLoadingModels = false
    @State private var isSaving = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            Form {
                Section("Make") {
                    if isLoadingMakes {
                        ProgressView()
                    } else {
                        Picker("Brand", selection: $selectedMake) {
                            Text("Select make").tag(Optional<VehicleMakeSummary>.none)
                            ForEach(makes) { make in
                                Text(make.name).tag(Optional(make))
                            }
                        }
                        .onChange(of: selectedMake) { _, make in
                            selectedModel = nil
                            models = []
                            guard let make else { return }
                            Task { await loadModels(for: make) }
                        }
                    }
                }

                Section("Model") {
                    if isLoadingModels {
                        ProgressView()
                    } else if selectedMake == nil {
                        Text("Choose a make first.")
                            .foregroundStyle(.secondary)
                    } else if models.isEmpty {
                        Text("No active models for this make.")
                            .foregroundStyle(.secondary)
                    } else {
                        Picker("Model", selection: $selectedModel) {
                            Text("Select model").tag(Optional<VehicleModelSummary>.none)
                            ForEach(models) { model in
                                Text("\(model.name) · \(model.sizeTier.label)")
                                    .tag(Optional(model))
                            }
                        }
                    }

                    if let selectedModel {
                        LabeledContent("Size tier", value: selectedModel.sizeTier.label)
                            .foregroundStyle(.secondary)
                    }
                }

                Section("Details (optional)") {
                    TextField("Nickname", text: $nickname)
                    TextField("Plate number", text: $plateNumber)
                        .textInputAutocapitalization(.characters)
                    TextField("Colour", text: $colour)
                    TextField("Parking slot", text: $parkingSlot)
                    TextField("Tower / block", text: $parkingTower)
                }

                if let errorMessage {
                    Section {
                        Text(errorMessage)
                            .foregroundStyle(BrandColor.accent)
                    }
                }
            }
            .navigationTitle(existing == nil ? "Add vehicle" : "Update vehicle")
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
                        .disabled(selectedModel == nil)
                    }
                }
            }
            .task {
                await loadMakes()
                prefillFromExisting()
            }
        }
    }

    private func prefillFromExisting() {
        guard let existing else { return }
        nickname = existing.nickname ?? ""
        plateNumber = existing.plateNumber ?? ""
        colour = existing.colour ?? ""
        parkingSlot = existing.parkingSlot ?? ""
        parkingTower = existing.parkingTower ?? ""
    }

    private func loadMakes() async {
        isLoadingMakes = true
        errorMessage = nil
        defer { isLoadingMakes = false }
        do {
            makes = try await appState.apiClient.listVehicleMakes()
                .sorted { $0.displayOrder < $1.displayOrder }
            if let existing, let make = existing.make {
                selectedMake = makes.first(where: { $0.id == make.id }) ?? make
                await loadModels(for: selectedMake!)
                if let model = existing.model {
                    selectedModel = models.first(where: { $0.id == model.id })
                }
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func loadModels(for make: VehicleMakeSummary) async {
        isLoadingModels = true
        errorMessage = nil
        defer { isLoadingModels = false }
        do {
            models = try await appState.apiClient.listVehicleModels(makeId: make.id)
                .sorted { $0.displayOrder < $1.displayOrder }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func save() async {
        guard let selectedModel else { return }
        isSaving = true
        errorMessage = nil
        defer { isSaving = false }
        do {
            let vehicle = try await appState.apiClient.putMyVehicle(
                modelId: selectedModel.id,
                nickname: nickname.nilIfEmpty,
                plateNumber: plateNumber.nilIfEmpty,
                colour: colour.nilIfEmpty,
                parkingSlot: parkingSlot.nilIfEmpty,
                parkingTower: parkingTower.nilIfEmpty
            )
            await appState.refreshProfile()
            onSaved?(vehicle)
            dismiss()
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
    VehicleEditorView()
        .environmentObject(AppState())
}
