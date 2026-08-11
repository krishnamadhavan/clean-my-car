# Clean My Car — iOS (consumer app)

Native **SwiftUI** client for apartment residents (phone OTP, eligibility, vehicle, quote, subscription dashboard).

| Item | Value |
|------|--------|
| Project | `CleanMyCar.xcodeproj` |
| Min iOS | **17.0** |
| Language | Swift 5 / SwiftUI |
| API | Consumer FastAPI at `/api/v1/*` |

Consumer modules **Auth** (phone OTP) and **Profile** (`/me`) are wired. Location, vehicle, quote, and subscription come next.

---

## Prerequisites (Mac)

1. **Xcode 16+** (App Store or [developer.apple.com](https://developer.apple.com/xcode/))
   - Open Xcode once and accept the license / install extra components when prompted.
2. **Command Line Tools** (usually installed with Xcode):
   ```bash
   xcode-select -p
   # should print: /Applications/Xcode.app/Contents/Developer
   ```
3. **Docker + Compose** for the backend (from monorepo root).
4. Optional: an **Apple ID** in Xcode → Settings → Accounts (needed for physical device; Simulator works without a paid team).

---

## 1. Start the backend

From the monorepo root:

```bash
cp .env.example .env   # first time only
make up-backend        # API + Postgres on http://localhost:8000
make migrate           # if not already applied
make health            # expect {"status":"ok",...}
```

Swagger: http://localhost:8000/docs

Keep this running while you use the app.

---

## 2. Open the iOS project

```bash
# from monorepo root
make ios-open
# or:
open ios/CleanMyCar.xcodeproj
```

---

## 3. Run on the iOS Simulator

1. In Xcode’s toolbar, choose scheme **CleanMyCar**.
2. Pick a simulator, e.g. **iPhone 16** (or any iOS 17+ device).
3. Press **Run** (▶) or `⌘R`.

The welcome screen calls:

`GET http://127.0.0.1:8000/api/v1/health`

You should see **API reachable** if Docker is up.

Enter a 10-digit Indian mobile number and tap **Send OTP**. In local/dev the API returns `debug_otp`; the verify screen shows it under **DEBUG** so you can sign in without SMS.

### CLI (optional)

```bash
# List simulators
xcrun simctl list devices available

# Build & run (example: booted simulator)
make ios-build
# or:
cd ios
xcodebuild -scheme CleanMyCar -destination 'platform=iOS Simulator,name=iPhone 16' build
```

---

## 4. Run on a physical iPhone

1. Connect the phone, unlock it, trust the computer.
2. In Xcode: select your device as the run destination.
3. **Signing**: Target **CleanMyCar** → Signing & Capabilities → check **Automatically manage signing** → choose your **Team** (Personal Team is fine for dev).
4. Set a unique **Bundle Identifier** if needed (default `com.cleanmycar.app`).
5. On the phone: Settings → General → VPN & Device Management → trust your developer certificate.
6. **API URL**: the phone cannot use `127.0.0.1` (that is the phone itself). Use your Mac’s LAN IP:

```bash
# on Mac
ipconfig getifaddr en0   # often Wi‑Fi
```

Then in Xcode → Product → Scheme → Edit Scheme → Run → Arguments → Environment Variables:

| Name | Value |
|------|--------|
| `API_BASE_URL` | `http://192.168.x.x:8000` |

Ensure the phone and Mac are on the same Wi‑Fi, and that the API is bound to `0.0.0.0` (Docker publish `8000:8000` already does this).

---

## 5. Project layout

```
ios/
├── CleanMyCar.xcodeproj
├── Info.plist                 # ATS local networking for dev HTTP
├── README.md
└── CleanMyCar/
    ├── App/                   # @main, RootView, tabs, AppState
    ├── Core/
    │   ├── Config/            # AppConfig (API base URL)
    │   ├── Networking/        # APIClient, errors, DTOs
    │   ├── Session/           # Keychain tokens + Indian phone helpers
    │   └── Theme/             # Brand colors
    ├── Features/
    │   ├── Auth/              # Welcome + OTP verify
    │   ├── Home/              # Dashboard placeholder
    │   └── Account/           # Profile, edit, logout, deactivate/delete
    └── Resources/
        └── Assets.xcassets
```

---

## 6. Configuration notes

| Setting | Default | Override |
|---------|---------|----------|
| API base | `http://127.0.0.1:8000` | Env `API_BASE_URL` or launch arg `-API_BASE_URL` |
| Min iOS | 17.0 | Project build settings |
| Bundle ID | `com.cleanmycar.app` | Signing & Capabilities |

`Info.plist` sets `NSAllowsLocalNetworking` so **HTTP** to local Docker works in debug. Production should use HTTPS and tighten ATS.

---

## 7. Auth & profile

| Flow | API |
|------|-----|
| Send OTP | `POST /api/v1/auth/otp/request` |
| Verify OTP | `POST /api/v1/auth/otp/verify` |
| Restore session | `GET /api/v1/me` (refresh on 401) |
| Edit name/email | `PATCH /api/v1/me` |
| Sign out | `POST /api/v1/auth/logout` |
| Deactivate | `POST /api/v1/me/deactivate` |
| Delete | `DELETE /api/v1/me` |

Access + refresh tokens live in the Keychain (`com.cleanmycar.app.tokens`). A 401 on an authenticated call rotates the refresh token once and retries. A failed refresh signs the user out.

Local/dev OTP: the verify screen shows `debug_otp` in **DEBUG** builds only (the API includes it outside production).

### Next modules (suggested order)

1. **Location** — list cities/societies, waitlist
2. **Vehicle** — makes/models, plate, parking
3. **Pricing** — quote preview
4. **Home dashboard** — subscription + monthly wash counts

Align with [`docs/PRD.md`](../docs/PRD.md) and [`docs/API_INVENTORY.md`](../docs/API_INVENTORY.md).

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| **API unreachable** on Simulator | `make up-backend` / `make health`; confirm URL is `127.0.0.1:8000` |
| **API unreachable** on device | Use Mac LAN IP in `API_BASE_URL`; same Wi‑Fi; check firewall |
| Signing errors | Select a Team; change bundle ID if taken |
| Blank App Icon | Expected in scaffold — add a 1024×1024 asset later |
| Xcode asks to install platforms | Install the iOS Simulator runtime when prompted |
