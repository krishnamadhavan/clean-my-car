import SwiftUI

struct LegalDocumentView: View {
    @EnvironmentObject private var appState: AppState
    let docType: String
    let title: String

    @State private var document: LegalDocument?
    @State private var isLoading = true
    @State private var errorMessage: String?

    var body: some View {
        Group {
            if isLoading && document == nil {
                ProgressView("Loading…")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if let document {
                ScrollView {
                    VStack(alignment: .leading, spacing: 12) {
                        Text(document.title)
                            .font(.title2.weight(.semibold))
                        Text("Version \(document.version)")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        if let body = document.body, !body.isEmpty {
                            Text(body)
                                .font(.body)
                        }
                        if let urlString = document.url, let url = URL(string: urlString) {
                            Link("Open full document", destination: url)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(16)
                }
            } else if let errorMessage {
                ContentUnavailableView("Unavailable", systemImage: "doc", description: Text(errorMessage))
            }
        }
        .navigationTitle(title)
        .navigationBarTitleDisplayMode(.inline)
        .task { await load() }
    }

    @MainActor
    private func load() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            document = try await appState.apiClient.fetchLegal(docType: docType)
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
