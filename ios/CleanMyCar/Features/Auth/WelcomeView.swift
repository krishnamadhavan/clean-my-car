import SwiftUI

/// Entry screen for unauthenticated users (OTP login comes next).
struct WelcomeView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 28) {
                    header
                    statusCard
                    actions
                    nextSteps
                }
                .padding(24)
            }
            .background(BrandColor.background.ignoresSafeArea())
            .navigationTitle("Clean My Car")
            .navigationBarTitleDisplayMode(.large)
        }
    }

    private var header: some View {
        VStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(BrandColor.primarySoft.opacity(0.45))
                    .frame(width: 96, height: 96)
                Image(systemName: "car.side")
                    .font(.system(size: 40, weight: .semibold))
                    .foregroundStyle(BrandColor.primary)
            }
            Text("Apartment car cleaning, on a schedule")
                .font(.title2.weight(.semibold))
                .multilineTextAlignment(.center)
            Text(
                "Subscribe for exterior washes on fixed society service days. Track completed vs pending washes for the month."
            )
            .font(.body)
            .foregroundStyle(.secondary)
            .multilineTextAlignment(.center)
        }
        .padding(.top, 12)
    }

    private var statusCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Label("Local backend", systemImage: "server.rack")
                .font(.headline)
            Text(AppConfig.apiBaseURL.absoluteString)
                .font(.caption.monospaced())
                .foregroundStyle(.secondary)
                .textSelection(.enabled)
            HStack {
                Circle()
                    .fill(statusColor)
                    .frame(width: 10, height: 10)
                Text(appState.apiStatus.label)
                    .font(.subheadline.weight(.medium))
            }
            if let err = appState.lastError {
                Text(err)
                    .font(.caption)
                    .foregroundStyle(BrandColor.accent)
            }
            Button {
                Task { await appState.checkAPIHealth() }
            } label: {
                Label("Recheck API", systemImage: "arrow.clockwise")
            }
            .buttonStyle(.bordered)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(.background)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        .shadow(color: .black.opacity(0.04), radius: 8, y: 2)
    }

    private var actions: some View {
        VStack(spacing: 12) {
            Button {
                // Scaffold: skip real OTP; full auth module next.
                appState.isAuthenticated = true
            } label: {
                Text("Continue (scaffold)")
                    .font(.headline)
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)

            Text("OTP phone login will replace this temporary entry point.")
                .font(.caption)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
    }

    private var nextSteps: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Scaffold roadmap")
                .font(.headline)
            bullet("Phone OTP auth against `/api/v1/auth/*`")
            bullet("City / society eligibility + waitlist")
            bullet("Vehicle registration + quote")
            bullet("Subscription + monthly wash dashboard")
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(.background)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
    }

    private func bullet(_ text: String) -> some View {
        HStack(alignment: .top, spacing: 8) {
            Image(systemName: "checkmark.circle")
                .foregroundStyle(BrandColor.secondary)
            Text(text)
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
    }

    private var statusColor: Color {
        switch appState.apiStatus {
        case .healthy: return .green
        case .checking: return BrandColor.secondary
        case .unhealthy, .unreachable: return BrandColor.accent
        case .unknown: return .gray
        }
    }
}

#Preview {
    WelcomeView()
        .environmentObject(AppState())
}
