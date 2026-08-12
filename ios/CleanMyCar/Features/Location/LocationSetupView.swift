import SwiftUI

/// Pick city + live society (LOC-01/02/05) or join the waitlist (WAIT-01).
struct LocationSetupView: View {
    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss

    var onSaved: ((UserLocation) -> Void)?

    @State private var cities: [CitySummary] = []
    @State private var selectedCity: CitySummary?
    @State private var societies: [SocietySummary] = []
    @State private var search = ""
    @State private var isLoadingCities = true
    @State private var isLoadingSocieties = false
    @State private var isSaving = false
    @State private var errorMessage: String?
    @State private var showWaitlist = false
    @State private var existingWaitlist: WaitlistEntry?

    var body: some View {
        NavigationStack {
            Group {
                if selectedCity == nil {
                    cityList
                } else {
                    societyList
                }
            }
            .background(BrandColor.background.ignoresSafeArea())
            .navigationTitle(selectedCity == nil ? "Select city" : "Select society")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    if selectedCity == nil {
                        Button("Close") { dismiss() }
                    } else {
                        Button("Cities") {
                            selectedCity = nil
                            societies = []
                            search = ""
                            errorMessage = nil
                        }
                    }
                }
            }
            .task {
                await loadCities()
                await loadExistingWaitlist()
            }
            .sheet(isPresented: $showWaitlist) {
                WaitlistJoinView(
                    initialCity: selectedCity,
                    existing: existingWaitlist
                ) {
                    showWaitlist = false
                    Task { await loadExistingWaitlist() }
                }
                .environmentObject(appState)
            }
        }
    }

    private var cityList: some View {
        List {
            if isLoadingCities {
                ProgressView("Loading cities…")
            } else if cities.isEmpty {
                ContentUnavailableView(
                    "No cities yet",
                    systemImage: "building.2",
                    description: Text("Ops has not activated any service cities.")
                )
            } else {
                ForEach(cities) { city in
                    Button {
                        selectedCity = city
                        Task { await loadSocieties(for: city) }
                    } label: {
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(city.name)
                                    .font(.body.weight(.medium))
                                    .foregroundStyle(.primary)
                                Text(city.state)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                            Image(systemName: "chevron.right")
                                .font(.caption.weight(.semibold))
                                .foregroundStyle(.tertiary)
                        }
                    }
                }
            }
        }
        .overlay(alignment: .bottom) {
            if let errorMessage {
                errorBanner(errorMessage)
            }
        }
    }

    private var societyList: some View {
        List {
            Section {
                TextField("Search societies", text: $search)
                    .textInputAutocapitalization(.words)
                    .onChange(of: search) { _, _ in
                        guard let city = selectedCity else { return }
                        Task { await loadSocieties(for: city, debounce: true) }
                    }
            }

            if isLoadingSocieties {
                ProgressView("Loading societies…")
            } else if societies.isEmpty {
                Section {
                    ContentUnavailableView(
                        "No live societies",
                        systemImage: "mappin.slash",
                        description: Text(
                            search.isEmpty
                                ? "Nothing is serviceable in this city yet. Join the waitlist if your building is missing."
                                : "No matches for “\(search)”. Try another name or join the waitlist."
                        )
                    )
                    Button {
                        showWaitlist = true
                    } label: {
                        Label(
                            existingWaitlist == nil ? "Join waitlist" : "Update waitlist request",
                            systemImage: existingWaitlist == nil ? "bell.badge" : "pencil"
                        )
                    }
                }
            } else {
                Section("Live societies") {
                    ForEach(societies) { society in
                        NavigationLink {
                            SocietyDetailView(societyId: society.id) { detail in
                                await save(detail: detail)
                            }
                            .environmentObject(appState)
                        } label: {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(society.name)
                                    .font(.body.weight(.medium))
                                if let address = society.addressLine, !address.isEmpty {
                                    Text(address)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                if !society.serviceWeekdays.isEmpty {
                                    Text(WeekdayLabel.joined(society.serviceWeekdays))
                                        .font(.caption.weight(.semibold))
                                        .foregroundStyle(BrandColor.secondaryAlt)
                                }
                            }
                            .padding(.vertical, 2)
                        }
                        .disabled(isSaving)
                    }
                }

                Section {
                    Button {
                        showWaitlist = true
                    } label: {
                        Label(
                            existingWaitlist == nil
                                ? "Can’t find your society? Join waitlist"
                                : "Update your waitlist for a different society",
                            systemImage: existingWaitlist == nil ? "bell.badge" : "pencil"
                        )
                    }
                    if let existingWaitlist {
                        Text("You already requested “\(existingWaitlist.societyName)”. Saving a new name replaces that single request.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
        .overlay {
            if isSaving {
                ProgressView("Saving…")
                    .padding(20)
                    .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
            }
        }
        .overlay(alignment: .bottom) {
            if let errorMessage {
                errorBanner(errorMessage)
            }
        }
    }

    private func errorBanner(_ text: String) -> some View {
        Text(text)
            .font(.caption)
            .foregroundStyle(.white)
            .padding(12)
            .frame(maxWidth: .infinity)
            .background(BrandColor.accent)
    }

    private func loadCities() async {
        isLoadingCities = true
        errorMessage = nil
        defer { isLoadingCities = false }
        do {
            cities = try await appState.apiClient.listCities()
                .sorted { $0.displayOrder < $1.displayOrder }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func loadExistingWaitlist() async {
        do {
            let response = try await appState.apiClient.listMyWaitlist()
            existingWaitlist = response.items.first
        } catch {
            // Non-blocking; join form still works as create.
            existingWaitlist = nil
        }
    }

    private func loadSocieties(for city: CitySummary, debounce: Bool = false) async {
        if debounce {
            try? await Task.sleep(nanoseconds: 300_000_000)
        }
        isLoadingSocieties = true
        errorMessage = nil
        defer { isLoadingSocieties = false }
        do {
            let response = try await appState.apiClient.listSocieties(
                cityId: city.id,
                q: search.isEmpty ? nil : search,
                pageSize: 50
            )
            societies = response.items
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func save(detail: SocietyDetail) async {
        isSaving = true
        errorMessage = nil
        defer { isSaving = false }
        do {
            let location = try await appState.apiClient.setMyLocation(
                cityId: detail.city.id,
                societyId: detail.id
            )
            onSaved?(location)
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    LocationSetupView()
        .environmentObject(AppState())
}
