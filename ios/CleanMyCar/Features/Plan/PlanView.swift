import SwiftUI

/// Plan / billing surface — static until subscription & payment APIs ship.
struct PlanView: View {
    private let preview = DashboardPreview.sample

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    sampleBanner
                    currentPlanCard
                    includesCard
                    billingCard
                }
                .padding(16)
            }
            .background(BrandColor.background.ignoresSafeArea())
            .navigationTitle("Plan")
        }
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
