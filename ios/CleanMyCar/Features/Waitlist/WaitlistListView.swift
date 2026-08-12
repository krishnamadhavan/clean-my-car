import SwiftUI

/// Module 4 — list the signed-in user's waitlist entries (WAIT-02).
struct WaitlistListView: View {
    @EnvironmentObject private var appState: AppState

    @State private var entries: [WaitlistEntry] = []
    @State private var isLoading = true
    @State private var errorMessage: String?
    @State private var showJoin = false
    @State private var cities: [CitySummary] = []
    @State private var joinCity: CitySummary?

    var body: some View {
        List {
            if isLoading {
                ProgressView("Loading waitlist…")
            } else if entries.isEmpty {
                ContentUnavailableView(
                    "No waitlist entries",
                    systemImage: "bell.slash",
                    description: Text("If your society is not live yet, join the waitlist so ops can notify you.")
                )
            } else {
                Section("Your entries") {
                    ForEach(entries) { entry in
                        VStack(alignment: .leading, spacing: 6) {
                            HStack {
                                Text(entry.societyName)
                                    .font(.headline)
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
                            Text(entry.createdAt.formatted(date: .abbreviated, time: .shortened))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            if let notes = entry.notes, !notes.isEmpty {
                                Text(notes)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        .padding(.vertical, 4)
                    }
                }
            }

            Section {
                Button {
                    Task { await prepareJoin() }
                } label: {
                    Label("Join waitlist for a city", systemImage: "bell.badge")
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
        .sheet(item: $joinCity) { city in
            WaitlistJoinView(city: city) {
                joinCity = nil
                Task { await load() }
            }
            .environmentObject(appState)
        }
        .confirmationDialog("Choose a city", isPresented: $showJoin, titleVisibility: .visible) {
            ForEach(cities) { city in
                Button("\(city.name), \(city.state)") {
                    joinCity = city
                }
            }
            Button("Cancel", role: .cancel) {}
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
            entries = response.items.sorted { $0.createdAt > $1.createdAt }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func prepareJoin() async {
        errorMessage = nil
        do {
            cities = try await appState.apiClient.listCities()
                .sorted { $0.displayOrder < $1.displayOrder }
            if cities.isEmpty {
                errorMessage = "No active cities yet."
            } else {
                showJoin = true
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
