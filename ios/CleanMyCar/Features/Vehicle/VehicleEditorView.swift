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
    @State private var formError: String?
    @State private var plateError: String?
    @State private var fieldErrors: [String: String] = [:]

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
                    if let modelError = fieldErrors["model_id"] ?? fieldErrors["modelId"] {
                        Text(modelError)
                            .font(.caption)
                            .foregroundStyle(BrandColor.accent)
                    }
                }

                Section {
                    TextField("Nickname", text: $nickname)
                    plateField
                    TextField("Colour", text: $colour)
                    TextField("Parking slot", text: $parkingSlot)
                    TextField("Tower / block", text: $parkingTower)
                } header: {
                    Text("Details (optional)")
                } footer: {
                    Text(IndianPlate.formatHint)
                }

                Section {
                    NavigationLink {
                        SizeTierGuideView()
                            .environmentObject(appState)
                    } label: {
                        Label("What do size tiers mean?", systemImage: "ruler")
                    }
                }

                if let formError {
                    Section {
                        Text(formError)
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
                        .disabled(!canSave)
                    }
                }
            }
            .task {
                await loadMakes()
                prefillFromExisting()
            }
        }
    }

    private var plateField: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("Registration plate")
                    .foregroundStyle(.secondary)
                Spacer()
                plateKindBadge
            }
            TextField(IndianPlate.placeholder, text: $plateNumber)
                .textInputAutocapitalization(.characters)
                .autocorrectionDisabled()
                .keyboardType(.asciiCapable)
                .font(.body.monospaced())
                .onChange(of: plateNumber) { _, newValue in
                    let normalized = IndianPlate.normalizeInput(newValue)
                    if normalized != newValue {
                        plateNumber = normalized
                    }
                    plateError = nil
                    fieldErrors.removeValue(forKey: "plate_number")
                    fieldErrors.removeValue(forKey: "plateNumber")
                    // Live feedback only after the user has typed enough to be wrong mid-entry
                    if !normalized.isEmpty, normalized.count >= 8 {
                        plateError = IndianPlate.validate(normalized).error
                    }
                }

            if let plateError {
                Text(plateError)
                    .font(.caption)
                    .foregroundStyle(BrandColor.accent)
            } else if let apiPlate = fieldErrors["plate_number"] ?? fieldErrors["plateNumber"] {
                Text(apiPlate)
                    .font(.caption)
                    .foregroundStyle(BrandColor.accent)
            }
        }
    }

    @ViewBuilder
    private var plateKindBadge: some View {
        switch IndianPlate.kind(of: plateNumber) {
        case .empty:
            EmptyView()
        case .standard:
            Text("Standard")
                .font(.caption2.weight(.semibold))
                .foregroundStyle(.green)
        case .bharat:
            Text("BH series")
                .font(.caption2.weight(.semibold))
                .foregroundStyle(BrandColor.primary)
        case .invalid:
            Text("Invalid")
                .font(.caption2.weight(.semibold))
                .foregroundStyle(BrandColor.accent)
        }
    }

    private var canSave: Bool {
        selectedModel != nil && !isSaving && IndianPlate.isValidOrEmpty(plateNumber)
    }

    private func prefillFromExisting() {
        guard let existing else { return }
        nickname = existing.nickname ?? ""
        plateNumber = existing.plateNumber.map(IndianPlate.normalizeInput) ?? ""
        colour = existing.colour ?? ""
        parkingSlot = existing.parkingSlot ?? ""
        parkingTower = existing.parkingTower ?? ""
    }

    private func loadMakes() async {
        isLoadingMakes = true
        formError = nil
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
            applyError(error)
        }
    }

    private func loadModels(for make: VehicleMakeSummary) async {
        isLoadingModels = true
        formError = nil
        defer { isLoadingModels = false }
        do {
            models = try await appState.apiClient.listVehicleModels(makeId: make.id)
                .sorted { $0.displayOrder < $1.displayOrder }
        } catch {
            applyError(error)
        }
    }

    private func save() async {
        guard let selectedModel else { return }

        // Client-side plate check before hitting the API
        let plateResult = IndianPlate.validate(plateNumber)
        if let message = plateResult.error {
            plateError = message
            return
        }
        plateError = nil
        isSaving = true
        formError = nil
        fieldErrors = [:]
        defer { isSaving = false }
        do {
            let vehicle = try await appState.apiClient.putMyVehicle(
                modelId: selectedModel.id,
                nickname: nickname.nilIfEmpty,
                plateNumber: plateResult.normalized,
                colour: colour.nilIfEmpty,
                parkingSlot: parkingSlot.nilIfEmpty,
                parkingTower: parkingTower.nilIfEmpty
            )
            await appState.refreshProfile()
            onSaved?(vehicle)
            dismiss()
        } catch {
            applyError(error)
        }
    }

    private func applyError(_ error: Error) {
        if let apiError = error as? APIError {
            fieldErrors = apiError.fieldErrors
            if let plateMsg = apiError.message(forField: "plate_number")
                ?? apiError.message(forField: "plateNumber")
            {
                plateError = plateMsg
            }
            // Prefer a short general message; avoid duplicating the plate line if that's all we have.
            let general = apiError.localizedDescription
            if plateError != nil, fieldErrors.count <= 1,
               general == plateError || general.contains("plate")
            {
                formError = nil
            } else {
                formError = general
            }
        } else {
            formError = error.localizedDescription
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
