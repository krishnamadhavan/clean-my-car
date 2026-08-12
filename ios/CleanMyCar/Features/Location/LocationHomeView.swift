import SwiftUI

/// Module 3 hub — current location (LOC-04), change society, service days.
struct LocationHomeView: View {
    @EnvironmentObject private var appState: AppState

    @State private var location: UserLocation?
    @State private var isLoading = true
    @State private var errorMessage: String?
    @State private var showSetup = false

    var body: some View {
        List {
            Section {
                if isLoading {
                    ProgressView("Loading location…")
                } else if let society = location?.society {
                    VStack(alignment: .leading, spacing: 8) {
                        Text(society.name)
                            .font(.title3.weight(.semibold))
                        if let city = location?.city {
                            Text("\(city.name), \(city.state)")
                                .foregroundStyle(.secondary)
                        }
                        if let address = society.addressLine, !address.isEmpty {
                            Text(address)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .padding(.vertical, 4)

                    if !society.serviceWeekdays.isEmpty {
                        ServiceWeekdayChips(active: society.serviceWeekdays)
                    }

                    NavigationLink {
                        SocietyDetailView(societyId: society.id)
                            .environmentObject(appState)
                    } label: {
                        Label("View society details", systemImage: "building.2")
                    }

                    Button {
                        showSetup = true
                    } label: {
                        Label("Change city or society", systemImage: "arrow.triangle.2.circlepath")
                    }
                } else {
                    ContentUnavailableView(
                        "No society selected",
                        systemImage: "building.2",
                        description: Text("Choose a live apartment community to check eligibility and service days.")
                    )
                    Button {
                        showSetup = true
                    } label: {
                        Label("Set city & society", systemImage: "plus.circle")
                    }
                }
            } header: {
                Text("Your location")
            } footer: {
                Text("Only live/serviceable societies appear. If your building is missing, join the waitlist from the picker.")
            }

            Section("Waitlist") {
                NavigationLink {
                    WaitlistListView()
                        .environmentObject(appState)
                } label: {
                    Label("My waitlist entries", systemImage: "bell")
                }
            }

            if let errorMessage {
                Section {
                    Text(errorMessage)
                        .foregroundStyle(BrandColor.accent)
                }
            }
        }
        .navigationTitle("Location")
        .navigationBarTitleDisplayMode(.inline)
        .refreshable { await load() }
        .task { await load() }
        .sheet(isPresented: $showSetup) {
            LocationSetupView { saved in
                location = saved
            }
            .environmentObject(appState)
        }
    }

    private func load() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            location = try await appState.apiClient.fetchMyLocation()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    NavigationStack {
        LocationHomeView()
            .environmentObject(AppState())
    }
}
