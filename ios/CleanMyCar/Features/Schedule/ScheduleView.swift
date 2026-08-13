import SwiftUI

/// Upcoming wash days from `GET /me/schedule` (WASH-04) — only scheduled service days.
struct ScheduleView: View {
    @EnvironmentObject private var appState: AppState

    @State private var schedule: ScheduleResponse?
    @State private var isLoading = true
    @State private var errorMessage: String?

    private var items: [ScheduleOccurrence] {
        schedule?.items ?? []
    }

    var body: some View {
        NavigationStack {
            Group {
                if isLoading, schedule == nil {
                    ProgressView("Loading schedule…")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List {
                        if let errorMessage {
                            Section {
                                Text(errorMessage)
                                    .font(.subheadline)
                                    .foregroundStyle(BrandColor.accent)
                            }
                        }

                        if let message = schedule?.message, items.isEmpty {
                            Section {
                                HStack(alignment: .top, spacing: 10) {
                                    Image(systemName: "calendar.badge.clock")
                                        .foregroundStyle(BrandColor.primary)
                                    Text(message)
                                        .font(.subheadline)
                                        .foregroundStyle(.secondary)
                                }
                                .listRowBackground(BrandColor.primarySoft.opacity(0.2))
                            }
                        }

                        if !items.isEmpty {
                            Section {
                                if let weekdays = schedule?.serviceWeekdays, !weekdays.isEmpty {
                                    Text("Service days: \(WeekdayLabel.joined(weekdays))")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                if let until = schedule?.untilDate {
                                    Text(
                                        "Through \(until.formatted(date: .abbreviated, time: .omitted))"
                                    )
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                }
                            }

                            Section("Coming up") {
                                ForEach(items) { item in
                                    scheduleRow(item)
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("Schedule")
            .refreshable { await loadSchedule() }
            .task { await loadSchedule() }
        }
    }

    private func scheduleRow(_ item: ScheduleOccurrence) -> some View {
        HStack(spacing: 12) {
            VStack {
                Text(item.date.formatted(.dateTime.day()))
                    .font(.title3.weight(.bold))
                    .foregroundStyle(BrandColor.primary)
                Text(item.date.formatted(.dateTime.month(.abbreviated)))
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
            .frame(width: 44)

            VStack(alignment: .leading, spacing: 4) {
                Text(item.date.formatted(.dateTime.weekday(.wide)))
                    .font(.headline)
                Text(item.title)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                if let note = item.note, !note.isEmpty {
                    Text(note)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                if let society = item.societyName {
                    Text(society)
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                }
            }

            Spacer()

            Image(systemName: item.kind.systemImage)
                .foregroundStyle(item.kind == .retryScheduled ? BrandColor.accent : BrandColor.primary)
        }
        .padding(.vertical, 4)
    }

    @MainActor
    private func loadSchedule() async {
        if schedule == nil {
            isLoading = true
        }
        errorMessage = nil
        defer { isLoading = false }
        do {
            schedule = try await appState.apiClient.fetchMySchedule()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    ScheduleView()
        .environmentObject(AppState())
}
