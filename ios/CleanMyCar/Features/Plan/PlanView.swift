import SwiftUI

/// Plan / billing surface — live quote when city + vehicle exist; subscription still sample.
struct PlanView: View {
    @EnvironmentObject private var appState: AppState

    private let preview = DashboardPreview.sample

    @State private var vehicle: UserVehicle?
    @State private var location: UserLocation?
    @State private var showQuote = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    sampleBanner
                    liveQuoteCard
                    currentPlanCard
                    includesCard
                    billingCard
                }
                .padding(16)
            }
            .background(BrandColor.background.ignoresSafeArea())
            .navigationTitle("Plan")
            .task {
                await loadContext()
            }
            .sheet(isPresented: $showQuote) {
                QuoteView(location: location, vehicle: vehicle)
                    .environmentObject(appState)
            }
        }
    }

    private var liveQuoteCard: some View {
        AppCard {
            Label("City pricing", systemImage: "indianrupeesign.circle.fill")
                .font(.headline)
            if location?.city == nil || vehicle == nil {
                Text("Set your society and vehicle on Home, then calculate a live pro-rated quote.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            } else {
                Text("\(location?.city?.name ?? "") · \(vehicle?.sizeTier.label ?? "")")
                    .font(.subheadline)
                Button {
                    showQuote = true
                } label: {
                    Text("Calculate live quote")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
            }
        }
    }

    private func loadContext() async {
        async let v = try? appState.apiClient.fetchMyVehicle()
        async let l = try? appState.apiClient.fetchMyLocation()
        vehicle = await v
        location = await l
    }

    private var sampleBanner: some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: "info.circle.fill")
                .foregroundStyle(BrandColor.secondary)
            Text("Plan details are a design preview. Subscribe, cancel, and pay land with Module 7–8.")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(BrandColor.primarySoft.opacity(0.28))
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    private var currentPlanCard: some View {
        AppCard {
            Text("Current plan")
                .font(.caption.weight(.semibold))
                .foregroundStyle(.secondary)
            Text(preview.planLabel)
                .font(.title3.weight(.semibold))
            HStack(alignment: .firstTextBaseline, spacing: 4) {
                Text(INRFormat.rupees(fromPaise: preview.monthlyPricePaise))
                    .font(.largeTitle.weight(.bold))
                    .foregroundStyle(BrandColor.primary)
                Text("/ month")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

            Button {} label: {
                Text("Change plan")
                    .font(.headline)
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .disabled(true)

            Text("Coming soon")
                .font(.caption)
                .foregroundStyle(.secondary)
                .frame(maxWidth: .infinity)
        }
    }

    private var includesCard: some View {
        AppCard {
            Text("Included this month")
                .font(.headline)
            includeRow(icon: "drop.fill", title: "Exterior washes", detail: "\(preview.exteriorEntitled) entitled")
            includeRow(icon: "sofa.fill", title: "Interior cleans", detail: "\(preview.interiorIncluded)× per month")
            includeRow(
                icon: "calendar",
                title: "Service days",
                detail: WeekdayLabel.joined(preview.serviceWeekdays)
            )
        }
    }

    private var billingCard: some View {
        AppCard {
            Text("Billing")
                .font(.headline)
            LabeledContent("Cycle", value: "Calendar month")
            LabeledContent("Next charge", value: "1st of next month")
            LabeledContent("Payment", value: "Manual monthly (UPI / card)")

            Button(role: .destructive) {} label: {
                Text("Cancel subscription")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.bordered)
            .disabled(true)
            .padding(.top, 4)
        }
    }

    private func includeRow(icon: String, title: String, detail: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .foregroundStyle(BrandColor.primary)
                .frame(width: 24)
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.subheadline.weight(.medium))
                Text(detail)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    PlanView()
}
