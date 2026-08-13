import SwiftUI

struct NotificationPreferencesView: View {
    @EnvironmentObject private var appState: AppState
    @State private var washCompleted = true
    @State private var paymentEvents = true
    @State private var serviceReminders = true
    @State private var marketing = false
    @State private var isLoading = true
    @State private var isSaving = false
    @State private var errorMessage: String?
    @State private var successMessage: String?

    var body: some View {
        Form {
            if let errorMessage {
                Section {
                    Text(errorMessage).foregroundStyle(BrandColor.accent)
                }
            }
            if let successMessage {
                Section {
                    Text(successMessage).foregroundStyle(.green)
                }
            }
            if isLoading {
                Section { ProgressView() }
            } else {
                Section("Alerts") {
                    Toggle("Wash completed", isOn: $washCompleted)
                        .onChange(of: washCompleted) { _, _ in Task { await save() } }
                    Toggle("Payment events", isOn: $paymentEvents)
                        .onChange(of: paymentEvents) { _, _ in Task { await save() } }
                    Toggle("Service reminders", isOn: $serviceReminders)
                        .onChange(of: serviceReminders) { _, _ in Task { await save() } }
                    Toggle("Marketing", isOn: $marketing)
                        .onChange(of: marketing) { _, _ in Task { await save() } }
                }
            }
        }
        .navigationTitle("Notifications")
        .overlay {
            if isSaving {
                ProgressView()
                    .padding(16)
                    .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
            }
        }
        .task { await load() }
    }

    @MainActor
    private func load() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            let prefs = try await appState.apiClient.fetchNotificationPreferences()
            washCompleted = prefs.washCompleted
            paymentEvents = prefs.paymentEvents
            serviceReminders = prefs.serviceReminders
            marketing = prefs.marketing
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    @MainActor
    private func save() async {
        guard !isLoading else { return }
        isSaving = true
        errorMessage = nil
        successMessage = nil
        defer { isSaving = false }
        do {
            let prefs = try await appState.apiClient.updateNotificationPreferences(
                washCompleted: washCompleted,
                paymentEvents: paymentEvents,
                serviceReminders: serviceReminders,
                marketing: marketing
            )
            washCompleted = prefs.washCompleted
            paymentEvents = prefs.paymentEvents
            serviceReminders = prefs.serviceReminders
            marketing = prefs.marketing
            successMessage = "Saved"
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
