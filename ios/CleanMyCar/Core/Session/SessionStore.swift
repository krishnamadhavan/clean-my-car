import Foundation
import Security

/// Access + refresh tokens persisted in the Keychain.
@MainActor
final class SessionStore {
    private enum Account {
        static let access = "access_token"
        static let refresh = "refresh_token"
    }

    private(set) var accessToken: String?
    private(set) var refreshToken: String?

    var hasSession: Bool {
        refreshToken != nil
    }

    init() {
        accessToken = Keychain.get(Account.access)
        refreshToken = Keychain.get(Account.refresh)
    }

    func setTokens(access: String, refresh: String) {
        accessToken = access
        refreshToken = refresh
        Keychain.set(access, account: Account.access)
        Keychain.set(refresh, account: Account.refresh)
    }

    func updateAfterRefresh(access: String, refresh: String?) {
        accessToken = access
        Keychain.set(access, account: Account.access)
        if let refresh {
            refreshToken = refresh
            Keychain.set(refresh, account: Account.refresh)
        }
    }

    func clear() {
        accessToken = nil
        refreshToken = nil
        Keychain.delete(Account.access)
        Keychain.delete(Account.refresh)
    }
}

private enum Keychain {
    private static let service = "com.cleanmycar.app.tokens"

    static func set(_ value: String, account: String) {
        guard let data = value.data(using: .utf8) else { return }
        delete(account)
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly,
        ]
        SecItemAdd(query as CFDictionary, nil)
    }

    static func get(_ account: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var item: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &item)
        guard status == errSecSuccess, let data = item as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }

    static func delete(_ account: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
        ]
        SecItemDelete(query as CFDictionary)
    }
}
