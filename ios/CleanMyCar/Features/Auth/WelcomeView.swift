import SwiftUI

struct WelcomeView: View {
    @EnvironmentObject private var appState: AppState
    @State private var phoneDigits = ""
    @State private var isSending = false
    @State private var formError: String?
    @State private var challenge: OTPChallenge?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    header
                    phoneCard
                }
                .padding(24)
            }
            .background(BrandColor.background.ignoresSafeArea())
            .navigationTitle("Clean My Car")
            .navigationBarTitleDisplayMode(.large)
            .navigationDestination(item: $challenge) { item in
                OTPVerifyView(challenge: item)
            }
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
                "Sign in with your mobile number. We’ll send a one-time code to continue."
            )
            .font(.body)
            .foregroundStyle(.secondary)
            .multilineTextAlignment(.center)
        }
        .padding(.top, 12)
    }

    private var phoneCard: some View {
        AppCard {
            Text("Mobile number")
                .font(.headline)
            Text("Indian mobile, 10 digits starting with 6–9.")
                .font(.caption)
                .foregroundStyle(.secondary)

            HStack(spacing: 10) {
                Text("+91")
                    .font(.body.monospaced())
                    .foregroundStyle(.secondary)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 12)
                    .background(BrandColor.background)
                    .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))

                TextField("98765 43210", text: $phoneDigits)
                    .keyboardType(.numberPad)
                    .textContentType(.telephoneNumber)
                    .font(.title3.monospaced())
                    .onChange(of: phoneDigits) { _, newValue in
                        phoneDigits = IndianPhone.normalizeInput(newValue)
                        formError = nil
                    }
            }

            if let formError {
                Text(formError)
                    .font(.caption)
                    .foregroundStyle(BrandColor.accent)
            }

            Button {
                Task { await sendOTP() }
            } label: {
                if isSending {
                    ProgressView()
                        .frame(maxWidth: .infinity)
                } else {
                    Text("Send OTP")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                }
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
            .disabled(isSending || !IndianPhone.isValidBody(phoneDigits))
        }
    }

    private func sendOTP() async {
        guard IndianPhone.isValidBody(phoneDigits) else {
            formError = "Enter a valid 10-digit Indian mobile number."
            return
        }
        isSending = true
        formError = nil
        defer { isSending = false }
        do {
            challenge = try await appState.requestOTP(phone: phoneDigits)
        } catch {
            formError = error.localizedDescription
        }
    }
}

#Preview {
    WelcomeView()
        .environmentObject(AppState())
}
