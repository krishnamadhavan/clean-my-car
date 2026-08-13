import SwiftUI

/// Highlights society service days (0=Mon … 5=Sat). Sunday is never serviceable.
struct ServiceWeekdayChips: View {
    let active: [Int]

    private var activeSet: Set<Int> { Set(active.filter { (0 ... 5).contains($0) }) }

    var body: some View {
        HStack(spacing: 6) {
            ForEach(0 ..< 6, id: \.self) { day in
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
