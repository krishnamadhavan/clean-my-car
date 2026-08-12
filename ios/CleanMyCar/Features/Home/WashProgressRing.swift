import SwiftUI

/// Circular exterior wash progress for the home dashboard.
struct WashProgressRing: View {
    let completed: Int
    let entitled: Int
    var lineWidth: CGFloat = 14
    var size: CGFloat = 148

    private var progress: Double {
        guard entitled > 0 else { return 0 }
        return min(Double(completed) / Double(entitled), 1)
    }

    var body: some View {
        ZStack {
            Circle()
                .stroke(BrandColor.primarySoft.opacity(0.35), lineWidth: lineWidth)
            Circle()
                .trim(from: 0, to: progress)
                .stroke(
                    AngularGradient(
                        colors: [BrandColor.secondary, BrandColor.primary, BrandColor.secondaryAlt],
                        center: .center
                    ),
                    style: StrokeStyle(lineWidth: lineWidth, lineCap: .round)
                )
                .rotationEffect(.degrees(-90))
                .animation(.easeInOut(duration: 0.6), value: progress)

            VStack(spacing: 4) {
                Text("\(completed)")
                    .font(.system(size: 40, weight: .bold, design: .rounded))
                    .foregroundStyle(BrandColor.primary)
                Text("of \(entitled)")
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(.secondary)
                Text("washes")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .frame(width: size, height: size)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(completed) of \(entitled) exterior washes completed this month")
    }
}

#Preview {
    WashProgressRing(completed: 7, entitled: 12)
        .padding()
        .background(BrandColor.background)
}
