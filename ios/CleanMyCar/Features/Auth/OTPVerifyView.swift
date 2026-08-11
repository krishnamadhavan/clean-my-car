import SwiftUI

struct OTPVerifyView: View {
    @EnvironmentObject private var appState: AppState

    @State private var challenge: OTPChallenge
    @State private var code = ""
    @State private var isVerifying = false
    @State private var isResending = false
    @State private var formError: String?

    init(challenge: OTPChallenge) {
        _challenge = State(initialValue: challenge)
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                header
                codeCard
                resendRow
            }
            .padding(24)
        }
        .background(BrandColor.background.ignoresSafeArea())
        .navigationTitle("Enter code")
        .navigationBarTitleDisplayMode(.inline)
    }

    private var header: some View {
        VStack(spacing: 8) {
            Text("We sent a 6-digit code to")
                .font(.body)
                .foregroundStyle(.secondary)
            Text(IndianPhone.display(challenge.phone))
                .font(.title3.weight(.semibold).monospaced())
        }
        .frame(maxWidth: .infinity)
        .padding(.top, 8)
    }

    private var codeCard: some View {
        AppCard {
            TextField("000000", text: $code)
                .keyboardType(.numberPad)
                .textContentType(.oneTimeCode)
                .multilineTextAlignment(.center)
                .font(.largeTitle.monospacedDigit().weight(.semibold))
                .onChange(of: code) { _, newValue in
                    code = String(newValue.filter(\.isNumber).prefix(6))
                    formError = nil
                }

            Text("Code expires \(challenge.expiresAt.formatted(date: .omitted, time: .shortened)).")
                .font(.caption)
                .foregroundStyle(.secondary)

            #if DEBUG
            if let debug = challenge.debugOTP, !debug.isEmpty {
                HStack {
                    Image(systemName: "ladybug")
                    Text("Dev OTP: \(debug)")
                        .font(.caption.monospaced())
                    Spacer()
                    Button("Fill") { code = debug }
                        .font(.caption.weight(.semibold))
                }
                .foregroundStyle(BrandColor.secondaryAlt)
                .padding(10)
                .background(BrandColor.primarySoft.opacity(0.25))
                .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
            }
            #endif

            if let formError {
                Text(formError)
                    .font(.caption)
                    .foregroundStyle(BrandColor.accent)
            }

            Button {
                Task { await verify() }
            } label: {
                if isVerifying {
                    ProgressView()
                        .frame(maxWidth: .infinity)
                } else {
                    Text("Verify and continue")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                }
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
            .disabled(isVerifying || code.count != 6)
        }
    }

    private var resendRow: some View {
        TimelineView(.periodic(from: .now, by: 1)) { context in
            let remaining = max(0, Int(challenge.resendAvailableAt.timeIntervalSince(context.date).rounded(.up)))
            VStack(spacing: 8) {
                if remaining > 0 {
                    Text("Resend available in \(remaining)s")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                } else {
                    Button {
                        Task { await resend() }
                    } label: {
                        if isResending {
                            ProgressView()
                        } else {
                            Text("Resend code")
                                .font(.subheadline.weight(.semibold))
                        }
                    }
                    .disabled(isResending)
                }
            }
            .frame(maxWidth: .infinity)
        }
    }

    private func verify() async {
        guard code.count == 6 else { return }
        isVerifying = true
        formError = nil
        defer { isVerifying = false }
        do {
            try await appState.verifyOTP(phone: challenge.phone, otp: code)
        } catch {
            formError = error.localizedDescription
        }
    }

    private func resend() async {
        isResending = true
        formError = nil
        defer { isResending = false }
        do {
            challenge = try await appState.requestOTP(phone: challenge.phone)
            code = ""
        } catch {
            formError = error.localizedDescription
        }
    }
}

#Preview {
    NavigationStack {
        OTPVerifyView(
            challenge: OTPChallenge(
                phone: "+919876543210",
                expiresAt: Date().addingTimeInterval(300),
                resendAvailableAt: Date().addingTimeInterval(60),
                debugOTP: "123456"
            )
        )
    }
    .environmentObject(AppState())
}
