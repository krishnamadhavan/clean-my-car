import SwiftUI

/// Home dashboard — live data from `GET /me/dashboard` (DASH-01).
struct HomeView: View {
    @EnvironmentObject private var appState: AppState

    @State private var dashboard: DashboardResponse?
    @State private var vehicle: UserVehicle?
    @State private var location: UserLocation?
    @State private var isLoadingExtras = false
    @State private var loadError: String?
    @State private var showLocationSetup = false
    @State private var showVehicleEditor = false
    @State private var showQuote = false

    private var washSummary: WashSummary? { dashboard?.washSummary }
    private var serviceWeekdays: [Int] {
        if let days = dashboard?.serviceWeekdays, !days.isEmpty { return days }
        return location?.society?.serviceWeekdays ?? []
    }

    private var canQuote: Bool {
        location?.city != nil && vehicle != nil
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    if let loadError {
                        Text(loadError)
                            .font(.caption)
                            .foregroundStyle(BrandColor.accent)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
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
            .refreshable { await reload() }
            .task { await reload() }
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
            let completed = washSummary?.exteriorCompleted ?? 0
            let entitled = washSummary?.exteriorEntitled ?? 0
            let pending = washSummary?.exteriorPending ?? max(entitled - completed, 0)
            let interiorDone = washSummary?.interiorCompleted ?? 0
            let interiorIncluded = washSummary?.interiorIncluded ?? 0
            let interiorProgress =
                interiorIncluded > 0
                    ? min(Double(interiorDone) / Double(interiorIncluded), 1)
                    : 0

            HStack(alignment: .center, spacing: 20) {
                WashProgressRing(completed: completed, entitled: max(entitled, 1))

                VStack(alignment: .leading, spacing: 12) {
                    Text("This month")
                        .font(.headline)

                    metricRow(title: "Pending", value: "\(pending)", systemImage: "clock")
                    metricRow(
                        title: "Interior",
                        value: "\(interiorDone) / \(interiorIncluded)",
                        systemImage: "sofa"
                    )

                    ProgressView(value: interiorProgress)
                        .tint(BrandColor.secondary)

                    if dashboard?.hasSubscription != true {
                        Text(dashboard?.message ?? "Subscribe to track wash progress.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
    }

    private var nextServiceCard: some View {
        AppCard {
            if let next = dashboard?.nextService {
                Label(
                    next.isRetry ? "Next-day retry" : "Next service",
                    systemImage: next.isRetry ? "arrow.clockwise" : "calendar"
                )
                .font(.headline)
                .foregroundStyle(BrandColor.primary)

                Text(next.date.formatted(date: .complete, time: .omitted))
                    .font(.title3.weight(.semibold))
                Text(next.title)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            } else {
                Label("Next service", systemImage: "calendar")
                    .font(.headline)
                    .foregroundStyle(BrandColor.primary)
                Text(dashboard?.hasSubscription == true
                    ? "No upcoming washes in this period."
                    : "Subscribe to see your next wash day.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

            if !serviceWeekdays.isEmpty {
                Divider().padding(.vertical, 4)
                Text("Weekly service days")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.secondary)
                ServiceWeekdayChips(active: serviceWeekdays)
            }
        }
    }

    private var planCard: some View {
        AppCard {
            HStack {
                Label("Your plan", systemImage: "tag.fill")
                    .font(.headline)
                Spacer()
                if let sub = dashboard?.subscription {
                    Text(INRFormat.rupees(fromPaise: sub.monthlyAmountPaise))
                        .font(.headline)
                        .foregroundStyle(BrandColor.primary)
                }
            }

            if let sub = dashboard?.subscription {
                Text(sub.planLabel)
                    .font(.subheadline)
                Text(sub.status.label)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.secondary)
                if let due = dashboard?.amountDuePaise, due > 0 {
                    Text("Amount due: \(INRFormat.rupees(fromPaise: due))")
                        .font(.caption)
                        .foregroundStyle(BrandColor.accent)
                }
            } else {
                Text("No active subscription")
                    .font(.subheadline)
                Text(dashboard?.billingMessage ?? "Get a live quote to start.")
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
            } else {
                Text("No vehicle registered yet.")
                    .font(.subheadline)
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

            if let society = location?.society ?? dashboard?.society {
                Text(society.name)
                    .font(.title3.weight(.semibold))
                if let city = location?.city ?? dashboard?.city {
                    Text("\(city.name), \(city.state)")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                if !society.serviceWeekdays.isEmpty {
                    Text(WeekdayLabel.joined(society.serviceWeekdays))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            } else {
                Text("Set your city and society to unlock service.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
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

    private var greetingText: String {
        let name = appState.profile?.name?.trimmingCharacters(in: .whitespacesAndNewlines)
        if let name, !name.isEmpty { return "Hello, \(name)" }
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

        async let dashTask: DashboardResponse? = {
            do { return try await appState.apiClient.fetchDashboard() }
            catch {
                loadError = error.localizedDescription
                return nil
            }
        }()
        async let vehicleTask = loadVehicle()
        async let locationTask = loadLocation()

        dashboard = await dashTask
        vehicle = await vehicleTask
        location = await locationTask

        if let dashVehicle = dashboard?.vehicle {
            vehicle = dashVehicle
        }
    }

    private func loadVehicle() async -> UserVehicle? {
        do {
            return try await appState.apiClient.fetchMyVehicle()
        } catch {
            return vehicle
        }
    }

    private func loadLocation() async -> UserLocation? {
        do {
            return try await appState.apiClient.fetchMyLocation()
        } catch {
            return location
        }
    }
}

#Preview {
    HomeView()
        .environmentObject(AppState())
}
