import SwiftUI

struct SupportTicketsView: View {
    @EnvironmentObject private var appState: AppState
    @State private var tickets: [SupportTicket] = []
    @State private var isLoading = true
    @State private var errorMessage: String?
    @State private var showCreate = false

    var body: some View {
        Group {
            if isLoading && tickets.isEmpty {
                ProgressView("Loading tickets…")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                List {
                    if let errorMessage {
                        Section {
                            Text(errorMessage).foregroundStyle(BrandColor.accent)
                        }
                    }
                    if tickets.isEmpty {
                        ContentUnavailableView(
                            "No tickets yet",
                            systemImage: "lifepreserver",
                            description: Text("Create a support ticket if you need help.")
                        )
                    } else {
                        ForEach(tickets) { ticket in
                            NavigationLink {
                                SupportTicketDetailView(ticket: ticket)
                                    .environmentObject(appState)
                            } label: {
                                VStack(alignment: .leading, spacing: 4) {
                                    HStack {
                                        Text(ticket.category.label)
                                            .font(.headline)
                                        Spacer()
                                        Text(ticket.status.label)
                                            .font(.caption.weight(.semibold))
                                            .foregroundStyle(.secondary)
                                    }
                                    Text(ticket.message)
                                        .font(.subheadline)
                                        .foregroundStyle(.secondary)
                                        .lineLimit(2)
                                    Text(ticket.createdAt.formatted(date: .abbreviated, time: .shortened))
                                        .font(.caption2)
                                        .foregroundStyle(.tertiary)
                                }
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle("Support")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    showCreate = true
                } label: {
                    Image(systemName: "plus")
                }
            }
        }
        .sheet(isPresented: $showCreate) {
            CreateSupportTicketView {
                Task { await load() }
            }
            .environmentObject(appState)
        }
        .refreshable { await load() }
        .task { await load() }
    }

    @MainActor
    private func load() async {
        if tickets.isEmpty { isLoading = true }
        errorMessage = nil
        defer { isLoading = false }
        do {
            let response = try await appState.apiClient.listSupportTickets()
            tickets = response.items
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

struct SupportTicketDetailView: View {
    let ticket: SupportTicket

    var body: some View {
        List {
            Section("Status") {
                LabeledContent("Category", value: ticket.category.label)
                LabeledContent("Status", value: ticket.status.label)
                LabeledContent(
                    "Created",
                    value: ticket.createdAt.formatted(date: .abbreviated, time: .shortened)
                )
            }
            Section("Your message") {
                Text(ticket.message)
            }
            if let reply = ticket.opsReply, !reply.isEmpty {
                Section("Support reply") {
                    Text(reply)
                }
            }
        }
        .navigationTitle("Ticket")
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct CreateSupportTicketView: View {
    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss
    var onCreated: (() -> Void)?

    @State private var category: SupportTicketCategory = .other
    @State private var message = ""
    @State private var isSaving = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            Form {
                Section("Category") {
                    Picker("Category", selection: $category) {
                        ForEach(SupportTicketCategory.allCases, id: \.self) { item in
                            Text(item.label).tag(item)
                        }
                    }
                }
                Section("Message") {
                    TextField("How can we help?", text: $message, axis: .vertical)
                        .lineLimit(4 ... 10)
                }
                if let errorMessage {
                    Section {
                        Text(errorMessage).foregroundStyle(BrandColor.accent)
                    }
                }
            }
            .navigationTitle("New ticket")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    if isSaving {
                        ProgressView()
                    } else {
                        Button("Send") {
                            Task { await submit() }
                        }
                        .disabled(message.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    }
                }
            }
        }
    }

    @MainActor
    private func submit() async {
        isSaving = true
        errorMessage = nil
        defer { isSaving = false }
        do {
            _ = try await appState.apiClient.createSupportTicket(
                category: category,
                message: message.trimmingCharacters(in: .whitespacesAndNewlines)
            )
            onCreated?()
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
