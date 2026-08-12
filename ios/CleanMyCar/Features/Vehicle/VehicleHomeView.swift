import SwiftUI

/// Module 5 hub — single vehicle (VEH-01), edit (VEH-02), delete (VEH-04), size guide (VEH-05).
struct VehicleHomeView: View {
    @EnvironmentObject private var appState: AppState

    @State private var vehicle: UserVehicle?
    @State private var isLoading = true
    @State private var isDeleting = false
    @State private var errorMessage: String?
    @State private var showEditor = false
    @State private var confirmDelete = false

    var body: some View {
        List {
            Section {
                if isLoading {
                    ProgressView("Loading vehicle…")
                } else if let vehicle {
                    VStack(alignment: .leading, spacing: 8) {
                        Text(vehicle.displayTitle)
                            .font(.title3.weight(.semibold))
                        Text(vehicle.subtitle)
                            .foregroundStyle(.secondary)
                        if let colour = vehicle.colour, !colour.isEmpty {
                            LabeledContent("Colour", value: colour)
                        }
                        if let slot = vehicle.parkingSlot, !slot.isEmpty {
                            LabeledContent("Parking", value: parkingLine(vehicle))
                        }
                    }
                    .padding(.vertical, 4)

                    Button {
                        showEditor = true
                    } label: {
                        Label("Edit vehicle", systemImage: "pencil")
                    }

                    Button(role: .destructive) {
                        confirmDelete = true
                    } label: {
                        if isDeleting {
                            ProgressView()
                        } else {
                            Label("Remove vehicle", systemImage: "trash")
                        }
                    }
                    .disabled(isDeleting)
                } else {
                    ContentUnavailableView(
                        "No vehicle yet",
                        systemImage: "car",
                        description: Text("Add one car from the make/model catalog. Size tier is assigned from the model.")
                    )
                    Button {
                        showEditor = true
                    } label: {
                        Label("Add vehicle", systemImage: "plus.circle")
                    }
                }
            } header: {
                Text("Your vehicle")
            } footer: {
                Text("v1 supports exactly one vehicle per account.")
            }

            Section("Catalog") {
                NavigationLink {
                    SizeTierGuideView()
                        .environmentObject(appState)
                } label: {
                    Label("Size tier guide", systemImage: "ruler")
                }
            }

            if let errorMessage {
                Section {
                    Text(errorMessage)
                        .foregroundStyle(BrandColor.accent)
                }
            }
        }
        .navigationTitle("Vehicle")
        .navigationBarTitleDisplayMode(.inline)
        .refreshable { await load() }
        .task { await load() }
        .sheet(isPresented: $showEditor) {
            VehicleEditorView(existing: vehicle) { saved in
                vehicle = saved
            }
            .environmentObject(appState)
        }
        .confirmationDialog(
            "Remove this vehicle?",
            isPresented: $confirmDelete,
            titleVisibility: .visible
        ) {
            Button("Remove vehicle", role: .destructive) {
                Task { await deleteVehicle() }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("You can add another vehicle later. Active subscriptions may block removal once that module ships.")
        }
    }

    private func parkingLine(_ vehicle: UserVehicle) -> String {
        [vehicle.parkingTower, vehicle.parkingSlot]
            .compactMap { $0 }
            .filter { !$0.isEmpty }
            .joined(separator: " · ")
    }

    private func load() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            vehicle = try await appState.apiClient.fetchMyVehicle()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func deleteVehicle() async {
        isDeleting = true
        errorMessage = nil
        defer { isDeleting = false }
        do {
            try await appState.apiClient.deleteMyVehicle()
            vehicle = nil
            await appState.refreshProfile()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    NavigationStack {
        VehicleHomeView()
            .environmentObject(AppState())
    }
}
