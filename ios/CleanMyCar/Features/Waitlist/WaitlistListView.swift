import SwiftUI

/// Module 4 — at most one waitlist request per account (WAIT-02 list + update via WAIT-01).
struct WaitlistListView: View {
    @EnvironmentObject private var appState: AppState

    @State private var entry: WaitlistEntry?
    @State private var isLoading = true
    @State private var errorMessage: String?
    @State private var showEditor = false

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
                        "Accounts keep a single waitlist request. Changing city or society replaces this entry — it does not create another one."
                    )
                }
            } else {
                ContentUnavailableView(
                    "No waitlist request",
                    systemImage: "bell.slash",
                    description: Text(
                        "If your society is not live yet, join the waitlist so ops can notify you. You can change city and society later; only one request is stored."
                    )
                )
            }

            Section {
                Button {
                    showEditor = true
                } label: {
                    Label(
                        hasEntry ? "Edit request" : "Join waitlist",
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
        .sheet(isPresented: $showEditor) {
            WaitlistJoinView(
                initialCity: entry?.city,
                existing: entry
            ) {
                showEditor = false
                Task { await load() }
            }
            .environmentObject(appState)
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
}

#Preview {
    NavigationStack {
        WaitlistListView()
            .environmentObject(AppState())
    }
}
