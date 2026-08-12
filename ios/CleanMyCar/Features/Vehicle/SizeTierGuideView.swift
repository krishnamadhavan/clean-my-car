import SwiftUI

/// Informational size tiers from `GET /vehicle-size-tiers` (VEH-05).
/// Users do not pick a tier — it is derived from the model catalog.
struct SizeTierGuideView: View {
    @EnvironmentObject private var appState: AppState

    @State private var tiers: [VehicleSizeTierInfo] = []
    @State private var isLoading = true
    @State private var errorMessage: String?

    var body: some View {
        List {
            Section {
                Text("Size is set by the model you choose. Ops maintain the catalog; you never pick Small / Medium / Large free-form.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

            if isLoading {
                ProgressView("Loading…")
            } else {
                ForEach(tiers) { tier in
                    VStack(alignment: .leading, spacing: 6) {
                        Text(tier.label)
                            .font(.headline)
                        Text(tier.description)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    .padding(.vertical, 4)
                }
            }

            if let errorMessage {
                Section {
                    Text(errorMessage)
                        .foregroundStyle(BrandColor.accent)
                }
            }
        }
        .navigationTitle("Size guide")
        .navigationBarTitleDisplayMode(.inline)
        .task { await load() }
    }

    private func load() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            tiers = try await appState.apiClient.listVehicleSizeTiers()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    NavigationStack {
        SizeTierGuideView()
            .environmentObject(AppState())
    }
}
