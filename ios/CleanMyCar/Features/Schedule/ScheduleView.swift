import SwiftUI

/// Upcoming service days / retries — static until WASH-04 ships.
struct ScheduleView: View {
    private let preview = DashboardPreview.sample

    private var sampleItems: [ScheduleItem] {
        let calendar = Calendar.current
        return (0 ..< 6).compactMap { offset -> ScheduleItem? in
            guard let day = calendar.date(byAdding: .day, value: offset * 2 + 1, to: Date()) else {
                return nil
            }
            let weekday = (calendar.component(.weekday, from: day) + 5) % 7 // Mon=0
            let isService = preview.serviceWeekdays.contains(weekday)
            return ScheduleItem(
                id: offset,
                date: day,
                kind: isService ? .scheduled : .offDay,
                note: isService ? "Exterior wash" : "No society service day"
            )
        }
    }

    var body: some View {
        NavigationStack {
            List {
                Section {
                    HStack(alignment: .top, spacing: 10) {
                        Image(systemName: "calendar.badge.clock")
                            .foregroundStyle(BrandColor.primary)
                        Text("Upcoming visits use sample data until the schedule API is available.")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    .listRowBackground(BrandColor.primarySoft.opacity(0.2))
                }

                Section("Coming up") {
                    ForEach(sampleItems) { item in
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
                                Text(item.note)
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                            }

                            Spacer()

                            Image(systemName: item.kind.systemImage)
                                .foregroundStyle(item.kind.color)
                        }
                        .padding(.vertical, 4)
                        .opacity(item.kind == .offDay ? 0.55 : 1)
                    }
                }
            }
            .navigationTitle("Schedule")
        }
    }
}

private struct ScheduleItem: Identifiable {
    enum Kind {
        case scheduled
        case retry
        case offDay

        var systemImage: String {
            switch self {
            case .scheduled: return "drop.fill"
            case .retry: return "arrow.clockwise"
            case .offDay: return "moon.zzz"
            }
        }

        var color: Color {
            switch self {
            case .scheduled: return BrandColor.primary
            case .retry: return BrandColor.accent
            case .offDay: return .secondary
            }
        }
    }

    let id: Int
    let date: Date
    let kind: Kind
    let note: String
}

#Preview {
    ScheduleView()
}
