import SwiftUI

/// Live quote from `POST /pricing/quote` using the user’s city, vehicle size, and society.
struct QuoteView: View {
    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss

    let location: UserLocation?
    let vehicle: UserVehicle?

    @State private var interiorOptions: [InteriorOption] = []
    @State private var interiorFrequency = 0
    @State private var quote: QuoteResponse?
    @State private var isLoadingOptions = true
    @State private var isQuoting = false
    @State private var errorMessage: String?

    private var canQuote: Bool {
        location?.city != nil && vehicle != nil
    }

    var body: some View {
        NavigationStack {
            Form {
                prerequisitesSection
                if canQuote {
                    packageSection
                    if let quote {
                        quoteSection(quote)
                    }
                }
                if let errorMessage {
                    Section {
                        Text(errorMessage)
                            .foregroundStyle(BrandColor.accent)
                    }
                }
            }
            .navigationTitle("Get a quote")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    if isQuoting {
                        ProgressView()
                    } else {
                        Button("Calculate") {
                            Task { await loadQuote() }
                        }
                        .disabled(!canQuote)
                    }
                }
            }
            .task {
                await loadOptions()
                if canQuote {
                    await loadQuote()
                }
            }
        }
    }

    private var prerequisitesSection: some View {
        Section("Your setup") {
            if let city = location?.city {
                LabeledContent("City", value: "\(city.name), \(city.state)")
            } else {
                Text("Set your society on Home first.")
                    .foregroundStyle(.secondary)
            }

            if let society = location?.society {
                LabeledContent("Society", value: society.name)
            }

            if let vehicle {
                LabeledContent("Vehicle", value: vehicle.displayTitle)
                LabeledContent("Size", value: vehicle.sizeTier.label)
            } else {
                Text("Add a vehicle on Home first (size comes from the model).")
                    .foregroundStyle(.secondary)
            }
        }
    }

    private var packageSection: some View {
        Section("Interior package") {
            if isLoadingOptions {
                ProgressView()
            } else if interiorOptions.isEmpty {
                // Fallback if PRICE-03 empty
                Picker("Interior", selection: $interiorFrequency) {
                    Text("None").tag(0)
                    Text("1× / month").tag(1)
                    Text("2× / month").tag(2)
                    Text("4× / month").tag(4)
                }
                .onChange(of: interiorFrequency) { _, _ in
                    Task { await loadQuote() }
                }
            } else {
                Picker("Interior", selection: $interiorFrequency) {
                    ForEach(interiorOptions) { option in
                        Text(option.label).tag(option.frequency)
                    }
                }
                .onChange(of: interiorFrequency) { _, _ in
                    Task { await loadQuote() }
                }

                if let selected = interiorOptions.first(where: { $0.frequency == interiorFrequency }) {
                    Text(selected.description)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }

    private func quoteSection(_ quote: QuoteResponse) -> some View {
        Group {
            Section("Due now") {
                LabeledContent("Billing month", value: quote.billingMonth)
                LabeledContent("Days covered", value: "\(quote.remainingDays) of \(quote.daysInMonth)")
                if quote.isProrated {
                    Text("Mid-month start — pro-rated for the rest of this month.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                LabeledContent("Amount due now") {
                    Text(INRFormat.rupees(fromPaise: quote.amountDueNowPaise))
                        .font(.title3.weight(.bold))
                        .foregroundStyle(BrandColor.primary)
                }
                if !quote.amountsIncludeGst, quote.amountDueNowBreakdown.gstPaise > 0 {
                    LabeledContent(
                        "of which GST",
                        value: INRFormat.rupees(fromPaise: quote.amountDueNowBreakdown.gstPaise)
                    )
                }
            }

            Section("From next month") {
                LabeledContent("Month", value: quote.nextBillingMonth)
                LabeledContent(
                    "Full monthly",
                    value: INRFormat.rupees(fromPaise: quote.nextFullMonthAmountPaise)
                )
                LabeledContent(
                    "Exterior base",
                    value: INRFormat.rupees(fromPaise: quote.fullMonthlyBasePaise)
                )
                LabeledContent(
                    "Interior add-on",
                    value: INRFormat.rupees(fromPaise: quote.fullMonthlyInteriorPaise)
                )
            }

            Section("Entitlement preview") {
                if let exterior = quote.exteriorEntitledThisPeriod {
                    LabeledContent("Exterior this period", value: "\(exterior) washes")
                }
                if let full = quote.exteriorEntitledFullMonth {
                    LabeledContent("Exterior full month", value: "\(full) washes")
                }
                LabeledContent(
                    "Interior this period",
                    value: "\(quote.interiorEntitledThisPeriod)"
                )
                LabeledContent(
                    "Interior full month",
                    value: "\(quote.interiorEntitledFullMonth)"
                )
                if let weekdays = quote.serviceWeekdays, !weekdays.isEmpty {
                    LabeledContent("Service days", value: WeekdayLabel.joined(weekdays))
                }
            }

            Section {
                Text("Checkout / payment will connect when the subscription module ships.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Button("Start subscription") {}
                    .disabled(true)
            }
        }
    }

    private func loadOptions() async {
        isLoadingOptions = true
        defer { isLoadingOptions = false }
        do {
            interiorOptions = try await appState.apiClient.listInteriorOptions()
            if let first = interiorOptions.first {
                interiorFrequency = first.frequency
            }
        } catch {
            // Fall back to hard-coded frequencies in the picker.
            errorMessage = nil
        }
    }

    private func loadQuote() async {
        guard let cityId = location?.city?.id, let vehicle else {
            errorMessage = "City and vehicle are required for a quote."
            return
        }
        isQuoting = true
        errorMessage = nil
        defer { isQuoting = false }
        do {
            quote = try await appState.apiClient.createQuote(
                cityId: cityId,
                sizeTier: vehicle.sizeTier,
                interiorFrequency: interiorFrequency,
                societyId: location?.society?.id
            )
        } catch {
            quote = nil
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    QuoteView(location: nil, vehicle: nil)
        .environmentObject(AppState())
}
