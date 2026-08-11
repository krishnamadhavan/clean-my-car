import SwiftUI

struct MainTabView: View {
    var body: some View {
        TabView {
            HomeView()
                .tabItem {
                    Label("Home", systemImage: "house.fill")
                }

            AccountView()
                .tabItem {
                    Label("Account", systemImage: "person.crop.circle")
                }
        }
    }
}

#Preview {
    MainTabView()
        .environmentObject(AppState())
}
