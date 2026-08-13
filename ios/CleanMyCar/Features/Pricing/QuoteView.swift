import SwiftUI

/// Live quote from `POST /pricing/quote`; can start subscription + pay (Modules 7–8).
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
    @State private var isStarting = false
    @State private var errorMessage: String?
    @State private var successMessage: String?
    /// Ignores stale quote responses when the user changes package or taps Calculate again.
    @State private var quoteRequestID = 0

    private var canQuote: Bool {
        location?.city != nil && vehicle != nil
    }

    private var calculateDisabled: Bool {
        !canQuote || isQuoting || isLoadingOptions || isStarting
    }

    var body: some View {
        NavigationStack {
            Form {
                if let errorMessage {
                    Section {
                        Text(errorMessage)
                            .foregroundStyle(BrandColor.accent)
                    }
                }

                prerequisitesSection

                if canQuote {
                    packageSection
                    calculateSection
                    if isQuoting, quote == nil {
                        Section {
                            HStack {
                                ProgressView()
                                Text("Calculating quote…")
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                    if let quote {
                        quoteSection(quote)
                    }
                } else {
                    Section {
                        Text("Set a serviceable society and vehicle on Home, then calculate a live quote.")
                            .foregroundStyle(.secondary)
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
                        .disabled(calculateDisabled)
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
                .disabled(isQuoting || isStarting)
                .onChange(of: interiorFrequency) { _, _ in
                    Task { await loadQuote() }
                }
            } else {
                Picker("Interior", selection: $interiorFrequency) {
                    ForEach(interiorOptions) { option in
                        Text(option.label).tag(option.frequency)
                    }
                }
                .disabled(isQuoting || isStarting)
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

    private var calculateSection: some View {
        Section {
            Button {
                Task { await loadQuote() }
            } label: {
                if isQuoting {
                    HStack {
                        ProgressView()
                        Text("Calculating…")
                    }
                    .frame(maxWidth: .infinity)
                } else {
                    Text(quote == nil ? "Calculate price" : "Recalculate")
                        .frame(maxWidth: .infinity)
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(calculateDisabled)

            if !canQuote {
                Text("City and vehicle are required.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
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
                if let successMessage {
                    Label(successMessage, systemImage: "checkmark.circle.fill")
                        .foregroundStyle(.green)
                }
                Text("Dev checkout: starts the plan and confirms payment immediately (manual provider).")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Button {
                    Task { await startAndPay() }
                } label: {
                    if isStarting {
                        ProgressView()
                            .frame(maxWidth: .infinity)
                    } else {
                        Text("Subscribe & pay \(INRFormat.rupees(fromPaise: quote.amountDueNowPaise))")
                            .frame(maxWidth: .infinity)
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(isStarting || !canQuote || isQuoting)
            }
        }
    }

    @MainActor
    private func startAndPay() async {
        isStarting = true
        errorMessage = nil
        successMessage = nil
        defer { isStarting = false }
        do {
            let started = try await appState.apiClient.startSubscription(
                interiorFrequency: interiorFrequency
            )
            _ = try await appState.apiClient.confirmPaymentIntent(
                started.paymentIntentId,
                providerRef: "IOS-DEV-\(Int(Date().timeIntervalSince1970))"
            )
            await appState.refreshProfile()
            successMessage = "Subscription active. You’re paid for this period."
            // Plan reloads on sheet `onDismiss` so state stays consistent after close.
            try? await Task.sleep(nanoseconds: 600_000_000)
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    @MainActor
    private func loadOptions() async {
        isLoadingOptions = true
        defer { isLoadingOptions = false }
        do {
            interiorOptions = try await appState.apiClient.listInteriorOptions()
            if let first = interiorOptions.first {
                // Avoid an extra quote round-trip when default is already correct.
                if interiorFrequency != first.frequency {
                    interiorFrequency = first.frequency
                }
            }
        } catch {
            // Fall back to hard-coded frequencies in the picker; do not clear quote errors.
            interiorOptions = []
        }
    }

    @MainActor
    private func loadQuote() async {
        guard let cityId = location?.city?.id, let vehicle else {
            errorMessage = "City and vehicle are required for a quote."
            quote = nil
            return
        }
        quoteRequestID += 1
        let requestID = quoteRequestID
        isQuoting = true
        errorMessage = nil
        defer {
            if requestID == quoteRequestID {
                isQuoting = false
            }
        }
        do {
            let result = try await appState.apiClient.createQuote(
                cityId: cityId,
                sizeTier: vehicle.sizeTier,
                interiorFrequency: interiorFrequency,
                societyId: location?.society?.id
            )
            guard requestID == quoteRequestID else { return }
            quote = result
        } catch is CancellationError {
            // Sheet dismissed or superseded request.
        } catch {
            guard requestID == quoteRequestID else { return }
            quote = nil
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    QuoteView(location: nil, vehicle: nil)
        .environmentObject(AppState())
}
