import SwiftUI

/// Highlights the three weekly service days for a society (0=Mon … 6=Sun).
struct ServiceWeekdayChips: View {
    let active: [Int]

    private var activeSet: Set<Int> { Set(active) }

    var body: some View {
        HStack(spacing: 6) {
            ForEach(0 ..< 7, id: \.self) { day in
                let isOn = activeSet.contains(day)
                Text(WeekdayLabel.shortName(for: day))
                    .font(.caption.weight(.semibold))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
                    .background(isOn ? BrandColor.primary : BrandColor.background)
                    .foregroundStyle(isOn ? Color.white : Color.secondary)
                    .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
            }
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Service days \(WeekdayLabel.joined(active))")
    }
}

#Preview {
    ServiceWeekdayChips(active: [0, 2, 4])
        .padding()
}
