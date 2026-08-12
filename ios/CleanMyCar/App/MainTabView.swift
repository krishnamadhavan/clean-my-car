import SwiftUI

struct MainTabView: View {
    @State private var selection: Tab = .home

    var body: some View {
        TabView(selection: $selection) {
            HomeView()
                .tabItem {
                    Label("Home", systemImage: selection == .home ? "house.fill" : "house")
                }
                .tag(Tab.home)

            ScheduleView()
                .tabItem {
                    Label("Schedule", systemImage: selection == .schedule ? "calendar.circle.fill" : "calendar")
                }
                .tag(Tab.schedule)

            PlanView()
                .tabItem {
                    Label("Plan", systemImage: selection == .plan ? "creditcard.fill" : "creditcard")
                }
                .tag(Tab.plan)

            AccountView()
                .tabItem {
                    Label("Account", systemImage: selection == .account ? "person.crop.circle.fill" : "person.crop.circle")
                }
                .tag(Tab.account)
        }
    }

    private enum Tab: Hashable {
        case home
        case schedule
        case plan
        case account
    }
}

#Preview {
    MainTabView()
        .environmentObject(AppState())
}
