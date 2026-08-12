import SwiftUI

/// Module 4 — at most one waitlist request per account (WAIT-02 list + update via WAIT-01).
struct WaitlistListView: View {
    @EnvironmentObject private var appState: AppState

    @State private var entry: WaitlistEntry?
    @State private var isLoading = true
    @State private var errorMessage: String?
    @State private var showCityPicker = false
    @State private var cities: [CitySummary] = []
    @State private var editorCity: CitySummary?

    private var hasEntry: Bool { entry != nil }

    var body: some View {
        List {
            if isLoading {
                ProgressView("Loading waitlist…")
            } else if let entry {
                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text(entry.societyName)
                                .font(.title3.weight(.semibold))
                            Spacer()
                            Text(entry.status.label)
                                .font(.caption.weight(.semibold))
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(statusColor(entry.status).opacity(0.15))
                                .foregroundStyle(statusColor(entry.status))
                                .clipShape(Capsule())
                        }
                        if let city = entry.city {
                            Text("\(city.name), \(city.state)")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                        Text("Updated \(entry.updatedAt.formatted(date: .abbreviated, time: .shortened))")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        if let notes = entry.notes, !notes.isEmpty {
                            Text(notes)
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .padding(.vertical, 4)
                } header: {
                    Text("Your waitlist request")
                } footer: {
                    Text(
                        "Accounts keep a single waitlist request. Updating city or society replaces this entry — it does not create another one."
                    )
                }
            } else {
                ContentUnavailableView(
                    "No waitlist request",
                    systemImage: "bell.slash",
                    description: Text(
                        "If your society is not live yet, join the waitlist so ops can notify you. You can change the society later; only one request is stored."
                    )
                )
            }

            Section {
                Button {
                    Task { await prepareEditor() }
                } label: {
                    Label(
                        hasEntry ? "Update city or society" : "Join waitlist",
                        systemImage: hasEntry ? "pencil" : "bell.badge"
                    )
                }
            }

            if let errorMessage {
                Section {
                    Text(errorMessage)
                        .foregroundStyle(BrandColor.accent)
                }
            }
        }
        .navigationTitle("Waitlist")
        .navigationBarTitleDisplayMode(.inline)
        .refreshable { await load() }
        .task { await load() }
        .sheet(item: $editorCity) { city in
            WaitlistJoinView(city: city, existing: entry) {
                editorCity = nil
                Task { await load() }
            }
            .environmentObject(appState)
        }
        .confirmationDialog(
            hasEntry ? "Update for which city?" : "Choose a city",
            isPresented: $showCityPicker,
            titleVisibility: .visible
        ) {
            ForEach(cities) { city in
                Button("\(city.name), \(city.state)") {
                    editorCity = city
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            if hasEntry {
                Text("Your existing request will be replaced with the new city and society name.")
            }
        }
    }

    private func statusColor(_ status: WaitlistStatus) -> Color {
        switch status {
        case .pending: return BrandColor.secondaryAlt
        case .contacted: return BrandColor.primary
        case .converted: return .green
        case .closed: return .secondary
        }
    }

    private func load() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            let response = try await appState.apiClient.listMyWaitlist()
            entry = response.items.first
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func prepareEditor() async {
        errorMessage = nil
        do {
            cities = try await appState.apiClient.listCities()
                .sorted { $0.displayOrder < $1.displayOrder }
            if cities.isEmpty {
                errorMessage = "No active cities yet."
                return
            }
            // If editing and we already know the city, open the form directly.
            if let entry,
               let city = cities.first(where: { $0.id == entry.cityId })
                ?? entry.city
            {
                editorCity = city
            } else {
                showCityPicker = true
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    NavigationStack {
        WaitlistListView()
            .environmentObject(AppState())
    }
}
