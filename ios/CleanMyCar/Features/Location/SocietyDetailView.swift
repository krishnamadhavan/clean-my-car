import SwiftUI

/// Society detail from `GET /societies/{id}` (LOC-03).
struct SocietyDetailView: View {
    @EnvironmentObject private var appState: AppState

    let societyId: UUID
    var onSelect: ((SocietyDetail) async -> Void)?

    @State private var detail: SocietyDetail?
    @State private var isLoading = true
    @State private var isSelecting = false
    @State private var errorMessage: String?

    var body: some View {
        List {
            if isLoading {
                ProgressView("Loading society…")
            } else if let detail {
                Section {
                    Text(detail.name)
                        .font(.title2.weight(.bold))
                    Text(detail.city.name + ", " + detail.city.state)
                        .foregroundStyle(.secondary)
                    if let address = detail.addressLine, !address.isEmpty {
                        Label(address, systemImage: "mappin.and.ellipse")
                            .font(.subheadline)
                    }
                    if detail.isServiceable {
                        Label("Live / serviceable", systemImage: "checkmark.seal.fill")
                            .font(.subheadline.weight(.semibold))
                            .foregroundStyle(.green)
                    }
                }

                Section("Service weekdays") {
                    ServiceWeekdayChips(active: detail.serviceWeekdays)
                        .listRowInsets(EdgeInsets(top: 12, leading: 16, bottom: 12, trailing: 16))
                    Text(WeekdayLabel.joined(detail.serviceWeekdays))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                if onSelect != nil {
                    Section {
                        Button {
                            Task { await select(detail) }
                        } label: {
                            if isSelecting {
                                ProgressView()
                                    .frame(maxWidth: .infinity)
                            } else {
                                Text("Use this society")
                                    .font(.headline)
                                    .frame(maxWidth: .infinity)
                            }
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(isSelecting)
                    }
                }
            }

            if let errorMessage {
                Section {
                    Text(errorMessage)
                        .foregroundStyle(BrandColor.accent)
                }
            }
        }
        .navigationTitle("Society")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await load()
        }
    }

    private func load() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            detail = try await appState.apiClient.getSociety(id: societyId)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func select(_ detail: SocietyDetail) async {
        isSelecting = true
        errorMessage = nil
        defer { isSelecting = false }
        if let onSelect {
            await onSelect(detail)
        }
    }
}

#Preview {
    NavigationStack {
        SocietyDetailView(societyId: UUID())
            .environmentObject(AppState())
    }
}
