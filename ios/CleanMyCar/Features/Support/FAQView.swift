import SwiftUI

struct FAQView: View {
    @EnvironmentObject private var appState: AppState
    @State private var items: [FaqEntry] = []
    @State private var isLoading = true
    @State private var errorMessage: String?

    var body: some View {
        Group {
            if isLoading && items.isEmpty {
                ProgressView("Loading FAQ…")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                List {
                    if let errorMessage {
                        Section {
                            Text(errorMessage).foregroundStyle(BrandColor.accent)
                        }
                    }
                    ForEach(items) { item in
                        Section(item.question) {
                            Text(item.answer)
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }
        }
        .navigationTitle("FAQ")
        .refreshable { await load() }
        .task { await load() }
    }

    @MainActor
    private func load() async {
        if items.isEmpty { isLoading = true }
        errorMessage = nil
        defer { isLoading = false }
        do {
            items = try await appState.apiClient.fetchFaq()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
