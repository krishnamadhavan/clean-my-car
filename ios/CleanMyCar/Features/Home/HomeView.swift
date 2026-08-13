import SwiftUI

/// Home dashboard — live profile / vehicle / location; wash & plan use static preview
/// until `GET /me/dashboard` and subscription APIs ship.
struct HomeView: View {
    @EnvironmentObject private var appState: AppState

    @State private var vehicle: UserVehicle?
    @State private var location: UserLocation?
    @State private var isLoadingExtras = false
    @State private var loadError: String?
    @State private var showLocationSetup = false
    @State private var showVehicleEditor = false
    @State private var showQuote = false

    private let preview = DashboardPreview.sample

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    previewBanner
                    greetingHeader
                    progressCard
                    nextServiceCard
                    planCard
                    vehicleCard
                    locationCard
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
            }
            .background(BrandColor.background.ignoresSafeArea())
            .navigationTitle("Home")
            .refreshable {
                await reload()
            }
            .task {
                await reload()
            }
            .sheet(isPresented: $showLocationSetup) {
                LocationSetupView { saved in
                    location = saved
                }
                .environmentObject(appState)
            }
            .sheet(isPresented: $showVehicleEditor) {
                VehicleEditorView(existing: vehicle) { saved in
                    vehicle = saved
                }
                .environmentObject(appState)
            }
            .sheet(isPresented: $showQuote, onDismiss: {
                Task { await reload() }
            }) {
                QuoteView(location: location, vehicle: vehicle)
                    .environmentObject(appState)
            }
        }
    }

    // MARK: - Sections

    private var previewBanner: some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: "sparkles")
                .foregroundStyle(BrandColor.secondaryAlt)
            VStack(alignment: .leading, spacing: 2) {
                Text("Sample wash progress")
                    .font(.subheadline.weight(.semibold))
                Text("Live completed / pending counts arrive with the subscription module.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer(minLength: 0)
        }
        .padding(12)
        .background(BrandColor.primarySoft.opacity(0.28))
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    private var greetingHeader: some View {
        HStack(alignment: .center) {
            VStack(alignment: .leading, spacing: 4) {
                Text(greetingText)
                    .font(.title2.weight(.bold))
                Text(monthCaption)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            Image(systemName: "car.side.fill")
                .font(.title)
                .foregroundStyle(BrandColor.primary)
                .padding(12)
                .background(BrandColor.primarySoft.opacity(0.35))
                .clipShape(Circle())
        }
    }

    private var progressCard: some View {
        AppCard {
            HStack(alignment: .center, spacing: 20) {
                WashProgressRing(
                    completed: preview.exteriorCompleted,
                    entitled: preview.exteriorEntitled
                )

                VStack(alignment: .leading, spacing: 12) {
                    Text("This month")
                        .font(.headline)

                    metricRow(
                        title: "Pending",
                        value: "\(preview.exteriorPending)",
                        systemImage: "clock"
                    )
                    metricRow(
                        title: "Interior",
                        value: "\(preview.interiorCompleted) / \(preview.interiorIncluded)",
                        systemImage: "sofa"
                    )

                    ProgressView(value: preview.interiorProgress)
                        .tint(BrandColor.secondary)
                        .accessibilityLabel(
                            "Interior \(preview.interiorCompleted) of \(preview.interiorIncluded)"
                        )
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
    }

    private var nextServiceCard: some View {
        AppCard {
            Label(
                preview.isNextServiceRetry ? "Next-day retry" : "Next service",
                systemImage: preview.isNextServiceRetry ? "arrow.clockwise" : "calendar"
            )
            .font(.headline)
            .foregroundStyle(BrandColor.primary)

            Text(preview.nextServiceDate.formatted(date: .complete, time: .omitted))
                .font(.title3.weight(.semibold))
            Text(preview.nextServiceDate.formatted(date: .omitted, time: .shortened))
                .font(.subheadline)
                .foregroundStyle(.secondary)

            Divider().padding(.vertical, 4)

            Text("Weekly service days")
                .font(.caption.weight(.semibold))
                .foregroundStyle(.secondary)
            ServiceWeekdayChips(active: preview.serviceWeekdays)
        }
    }

    private var planCard: some View {
        AppCard {
            HStack {
                Label("Your plan", systemImage: "tag.fill")
                    .font(.headline)
                Spacer()
                Text(INRFormat.rupees(fromPaise: preview.monthlyPricePaise))
                    .font(.headline)
                    .foregroundStyle(BrandColor.primary)
            }
            Text(preview.planLabel)
                .font(.subheadline)
            Text("/ month · sample tariff until you run a live quote")
                .font(.caption)
                .foregroundStyle(.secondary)

            if appState.profile?.hasSubscription == true {
                Label("Subscription active", systemImage: "checkmark.seal.fill")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.green)
            } else {
                Text("No subscription yet. Price your city with a live quote.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Button {
                showQuote = true
            } label: {
                Text(canQuote ? "Get live quote" : "Get quote (needs society + vehicle)")
                    .font(.subheadline.weight(.semibold))
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.regular)
            .disabled(!canQuote)
        }
    }

    private var vehicleCard: some View {
        AppCard {
            Label("Vehicle", systemImage: "car.fill")
                .font(.headline)

            if isLoadingExtras, vehicle == nil {
                ProgressView()
                    .frame(maxWidth: .infinity, alignment: .leading)
            } else if let vehicle {
                Text(vehicle.displayTitle)
                    .font(.title3.weight(.semibold))
                Text(vehicle.subtitle)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                if let colour = vehicle.colour, !colour.isEmpty {
                    Text(colour)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            } else {
                Text("No vehicle registered yet.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                Text("Pick make and model from the ops catalog. Size tier is set automatically.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Button {
                showVehicleEditor = true
            } label: {
                Text(vehicle == nil ? "Add vehicle" : "Update vehicle")
                    .font(.subheadline.weight(.semibold))
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.bordered)
        }
    }

    private var locationCard: some View {
        AppCard {
            Label("Society", systemImage: "building.2.fill")
                .font(.headline)

            if isLoadingExtras, location == nil {
                ProgressView()
                    .frame(maxWidth: .infinity, alignment: .leading)
            } else if let society = location?.society {
                Text(society.name)
                    .font(.title3.weight(.semibold))
                if let city = location?.city {
                    Text("\(city.name), \(city.state)")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                if !society.serviceWeekdays.isEmpty {
                    Text(WeekdayLabel.joined(society.serviceWeekdays))
                        .font(.caption.weight(.medium))
                        .foregroundStyle(BrandColor.secondaryAlt)
                }
                if let address = society.addressLine, !address.isEmpty {
                    Text(address)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            } else if location?.city != nil {
                Text(location?.city?.name ?? "")
                    .font(.title3.weight(.semibold))
                Text("Pick a society to unlock service days.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            } else {
                Text("No society selected")
                    .font(.title3.weight(.semibold))
                Text("Choose a live apartment community to check eligibility.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            if let loadError {
                Text(loadError)
                    .font(.caption)
                    .foregroundStyle(BrandColor.accent)
            }

            Button {
                showLocationSetup = true
            } label: {
                Text(location?.society == nil ? "Set city & society" : "Change society")
                    .font(.subheadline.weight(.semibold))
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.bordered)
        }
    }

    private var canQuote: Bool {
        location?.city != nil && vehicle != nil
    }

    // MARK: - Helpers

    private var greetingText: String {
        let name = appState.profile?.name?.trimmingCharacters(in: .whitespacesAndNewlines)
        if let name, !name.isEmpty {
            return "Hello, \(name)"
        }
        return "Hello"
    }

    private var monthCaption: String {
        let month = Date().formatted(.dateTime.month(.wide).year())
        return "Wash progress for \(month)"
    }

    private func metricRow(title: String, value: String, systemImage: String) -> some View {
        HStack(spacing: 8) {
            Image(systemName: systemImage)
                .font(.caption)
                .foregroundStyle(BrandColor.secondary)
                .frame(width: 16)
            VStack(alignment: .leading, spacing: 1) {
                Text(title)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text(value)
                    .font(.subheadline.weight(.semibold))
            }
        }
    }

    private func reload() async {
        await appState.refreshProfile()
        isLoadingExtras = true
        loadError = nil
        defer { isLoadingExtras = false }

        async let vehicleTask = loadVehicle()
        async let locationTask = loadLocation()
        vehicle = await vehicleTask
        location = await locationTask
    }

    private func loadVehicle() async -> UserVehicle? {
        do {
            return try await appState.apiClient.fetchMyVehicle()
        } catch {
            loadError = error.localizedDescription
            return vehicle
        }
    }

    private func loadLocation() async -> UserLocation? {
        do {
            return try await appState.apiClient.fetchMyLocation()
        } catch {
            loadError = error.localizedDescription
            return location
        }
    }
}

#Preview {
    HomeView()
        .environmentObject(AppState())
}
