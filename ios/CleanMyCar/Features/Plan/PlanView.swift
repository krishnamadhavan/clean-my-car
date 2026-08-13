import SwiftUI

/// Plan / billing — live subscription (Module 7) + pay/cancel (Module 8).
struct PlanView: View {
    @EnvironmentObject private var appState: AppState

    @State private var vehicle: UserVehicle?
    @State private var location: UserLocation?
    @State private var subscription: UserSubscription?
    @State private var billing: BillingSummary?
    @State private var isLoading = true
    @State private var hasLoadedOnce = false
    @State private var isWorking = false
    @State private var errorMessage: String?
    @State private var showQuote = false
    @State private var confirmCancel = false
    /// Drops stale `loadContext` results when several reloads overlap.
    @State private var loadRequestID = 0

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    if let errorMessage {
                        Text(errorMessage)
                            .font(.caption)
                            .foregroundStyle(BrandColor.accent)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    if isLoading, !hasLoadedOnce {
                        ProgressView("Loading plan…")
                            .frame(maxWidth: .infinity)
                            .padding()
                    } else if let subscription {
                        liveSubscriptionCard(subscription)
                        billingCard
                        actionsCard(subscription)
                    } else {
                        noPlanCard
                        liveQuoteCard
                    }
                }
                .padding(16)
            }
            .background(BrandColor.background.ignoresSafeArea())
            .navigationTitle("Plan")
            .refreshable { await loadContext(showFullScreenLoading: false) }
            .task { await loadContext(showFullScreenLoading: true) }
            .overlay {
                if isWorking {
                    ProgressView()
                        .padding(20)
                        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
                }
            }
            .sheet(isPresented: $showQuote, onDismiss: {
                // Always reconcile after quote sheet closes (subscribe or cancel).
                Task { await loadContext(showFullScreenLoading: false) }
            }) {
                QuoteView(location: location, vehicle: vehicle)
                    .environmentObject(appState)
            }
            .confirmationDialog(
                "Cancel at month end?",
                isPresented: $confirmCancel,
                titleVisibility: .visible
            ) {
                Button("Cancel subscription", role: .destructive) {
                    Task { await cancelSub() }
                }
                Button("Keep plan", role: .cancel) {}
            } message: {
                Text(
                    "Service continues until \(subscription?.periodEnd.formatted(date: .abbreviated, time: .omitted) ?? "month end"). No refund for the current period."
                )
            }
        }
    }

    private var noPlanCard: some View {
        AppCard {
            Text("No active plan")
                .font(.title3.weight(.semibold))
            Text("Set society and vehicle on Home, then get a quote and start your subscription.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
    }

    private var liveQuoteCard: some View {
        AppCard {
            Label("Get started", systemImage: "indianrupeesign.circle.fill")
                .font(.headline)
            if location?.city == nil || vehicle == nil {
                Text("Set your society and vehicle on Home first.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            } else {
                Text("\(location?.city?.name ?? "") · \(vehicle?.sizeTier.label ?? "")")
                    .font(.subheadline)
                Button {
                    showQuote = true
                } label: {
                    Text("Quote & subscribe")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
            }
        }
    }

    private func liveSubscriptionCard(_ sub: UserSubscription) -> some View {
        AppCard {
            HStack {
                Text("Current plan")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.secondary)
                Spacer()
                Text(sub.status.label)
                    .font(.caption.weight(.semibold))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(BrandColor.primarySoft.opacity(0.45))
                    .clipShape(Capsule())
            }
            Text(sub.planLabel)
                .font(.title3.weight(.semibold))
            HStack(alignment: .firstTextBaseline, spacing: 4) {
                Text(INRFormat.rupees(fromPaise: sub.monthlyAmountPaise))
                    .font(.largeTitle.weight(.bold))
                    .foregroundStyle(BrandColor.primary)
                Text("/ month")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            if let society = sub.society {
                Text(society.name)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            LabeledContent(
                "Period",
                value: "\(sub.periodStart.formatted(date: .abbreviated, time: .omitted)) – \(sub.periodEnd.formatted(date: .abbreviated, time: .omitted))"
            )
            if let cancelAt = sub.cancelAt {
                Text("Service until \(cancelAt.formatted(date: .abbreviated, time: .omitted))")
                    .font(.caption)
                    .foregroundStyle(BrandColor.accent)
            }
        }
    }

    private var billingCard: some View {
        AppCard {
            Text("Billing")
                .font(.headline)
            if let billing {
                Text(billing.message)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                if billing.amountDuePaise > 0 {
                    LabeledContent(
                        "Amount due",
                        value: INRFormat.rupees(fromPaise: billing.amountDuePaise)
                    )
                    .font(.body.weight(.semibold))
                }
            } else {
                Text("Loading billing…")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            Text("Payments are manual (dev confirm). Gateway SDK comes later.")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }

    private func actionsCard(_ sub: UserSubscription) -> some View {
        AppCard {
            if sub.status == .pendingPayment || (billing?.amountDuePaise ?? 0) > 0 {
                Button {
                    Task { await payNow() }
                } label: {
                    Text("Pay now")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
            }

            if sub.status == .cancelScheduled {
                Button {
                    Task { await undoCancel() }
                } label: {
                    Text("Keep subscription")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
            } else if sub.status == .active || sub.status == .pendingPayment {
                Button(role: .destructive) {
                    confirmCancel = true
                } label: {
                    Text("Cancel at month end")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
            }
        }
    }

    @MainActor
    private func loadContext(showFullScreenLoading: Bool = false) async {
        loadRequestID += 1
        let requestID = loadRequestID
        if showFullScreenLoading, !hasLoadedOnce {
            isLoading = true
        }
        errorMessage = nil
        defer {
            if requestID == loadRequestID {
                isLoading = false
                hasLoadedOnce = true
            }
        }

        do {
            async let vehicleTask = appState.apiClient.fetchMyVehicle()
            async let locationTask = appState.apiClient.fetchMyLocation()
            async let subscriptionTask = appState.apiClient.fetchMySubscription()
            async let billingTask = appState.apiClient.fetchBillingSummary()

            let nextVehicle = try await vehicleTask
            let nextLocation = try await locationTask
            let nextSubscription = try await subscriptionTask
            let nextBilling = try await billingTask

            guard requestID == loadRequestID else { return }

            vehicle = nextVehicle
            location = nextLocation
            subscription = nextSubscription
            billing = nextBilling
            await appState.refreshProfile()
        } catch is CancellationError {
            // Superseded or view torn down.
        } catch {
            guard requestID == loadRequestID else { return }
            // Keep the last good plan/vehicle/location; only surface the error.
            errorMessage = error.localizedDescription
        }
    }

    @MainActor
    private func payNow() async {
        isWorking = true
        errorMessage = nil
        defer { isWorking = false }
        do {
            var intentId = billing?.openPaymentIntentId
            if intentId == nil {
                let intent = try await appState.apiClient.createPaymentIntent(
                    subscriptionId: subscription?.id
                )
                intentId = intent.id
            }
            guard let intentId else { return }
            _ = try await appState.apiClient.confirmPaymentIntent(
                intentId,
                providerRef: "IOS-DEV-\(Int(Date().timeIntervalSince1970))"
            )
            await loadContext(showFullScreenLoading: false)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    @MainActor
    private func cancelSub() async {
        isWorking = true
        errorMessage = nil
        defer { isWorking = false }
        do {
            subscription = try await appState.apiClient.cancelSubscription()
            await loadContext(showFullScreenLoading: false)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    @MainActor
    private func undoCancel() async {
        isWorking = true
        errorMessage = nil
        defer { isWorking = false }
        do {
            subscription = try await appState.apiClient.undoCancelSubscription()
            await loadContext(showFullScreenLoading: false)
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    PlanView()
        .environmentObject(AppState())
}
