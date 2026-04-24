# Fitness Tracker Integration Research

> Last updated: 2026-04-16

Research findings on integrating external fitness tracker step data into the Steps Challenge webapp. Goal: allow participants to sync daily step totals from their fitness devices instead of (or in addition to) manual entry.

---

## Strategy Overview

**Strava** is our primary integration point. It has a public, free API with standard OAuth 2.0 and serves as a hub that most fitness platforms can sync into. For passive step data (all-day steps from users who don't log workouts), we add an **Apple Shortcuts webhook** for iPhone users. **Fitbit** has its own public API (transitioning to Google Health API) and can be integrated directly if needed.

**Manual entry remains the universal fallback** — always available, no setup required.

---

## Device Coverage Matrix

| Device | Phone | Passive Steps Path | Active Steps (Workouts) | Notes |
|--------|-------|-------------------|------------------------|-------|
| **Garmin** | iPhone | Garmin Connect → Apple Health → Shortcuts → webhook ✅ | Garmin Connect → Strava → our app ✅ | Full coverage on iPhone |
| **Garmin** | Android | ⚠️ No clean path (manual entry) | Garmin Connect → Strava → our app ✅ | Garmin syncs to Health Connect but no way to bridge to our server without Tasker (power-user) |
| **Apple Watch** | iPhone | Apple Health → Shortcuts → webhook ✅ | Apple Health → Strava → our app ✅ | Full coverage |
| **Fitbit** | Any | Direct via Fitbit/Google Health API ✅ | Direct via Fitbit/Google Health API ✅ | Full coverage; best direct API story |
| **No device** | Any | Manual entry ✅ | Manual entry ✅ | Always available |

### Known Gap: Garmin + Android Passive Steps

Garmin Connect on Android syncs passive steps to **Google Health Connect** (as of July 2025, Android 14+). However, Health Connect is an on-device Android framework — like Apple HealthKit, it has no server-side API. Data stays on the phone unless a local app pushes it out.

Unlike iOS (which has Shortcuts), Android has no clean native way to read Health Connect data and POST to a webhook. **Tasker** with a Google Fit plugin can do it, but requires a paid app, plugin installation, and manual configuration — too much friction for casual users.

**Mitigation:** Android + Garmin users can either:
1. Use Strava for activity-based steps (walks/runs)
2. Use manual entry for passive steps
3. Use Tasker if they're power users

---

## Garmin Connect — ❌ No-Go (Direct API)

### Official API: Garmin Health API

- **Access model:** Business/enterprise only. Requires formal application and approval through the [Garmin Connect Developer Program](https://developer.garmin.com/gc-developer-program/).
- **No personal/hobbyist access.** Garmin explicitly excludes individual developers and personal-use projects.
- **Auth:** OAuth 1.0a (not 2.0).
- **Data delivery:** Push-based (webhooks) + pull endpoints for daily summaries.
- **Cost:** Free for evaluation; licensing required for commercial use.
- **Verdict:** Not viable for a small group challenge app.

### Unofficial: `python-garminconnect`

- Reverse-engineered library that scrapes Garmin Connect by simulating mobile app login.
- Requires storing user's Garmin username/password — unacceptable for multi-user app.
- Can break without notice if Garmin changes their endpoints.
- Only viable for single-user personal scripts, not production.

### Garmin User Paths (Indirect)

**iPhone users:** Garmin Connect app syncs passive steps to Apple Health natively. From there, Apple Shortcuts can push to our webhook. For activities, Garmin Connect syncs to Strava.

**Android users:** Garmin Connect syncs to Google Health Connect (Android 14+), but there's no clean way to bridge that to our server. Activities can go through Strava. Passive steps require manual entry or Tasker (power-user).

---

## Strava — ✅ Primary Integration

### API Overview

- **Access:** Public API, free for individual developers. Register at [developers.strava.com](https://developers.strava.com/).
- **Auth:** OAuth 2.0 (standard, well-documented).
- **Rate limits:** 100 requests/15 min, 1,000 requests/day (per app).
- **Data available:** Activities, athlete stats, segment efforts. Step count is available through activity details.

### Key Considerations

- Strava is primarily an **activity-based** platform (runs, walks, rides), not a raw step counter.
- Daily step totals are not a first-class Strava concept — would need to sum steps across activities for a given day, or pull from athlete stats.
- Users who only wear a device for passive step counting (no logged activities) may have incomplete data in Strava.
- Works well for users who actively log walks/runs.

### Integration Path

1. Register Strava API application → receive client ID + secret.
2. OAuth 2.0 flow: user authorizes our app → we receive access + refresh tokens.
3. Pull activity data or athlete stats for step counts.
4. Store as `DailySteps` with `source=STRAVA`.

### Effort Estimate

Low-medium. OAuth 2.0 is simpler than Garmin's OAuth 1.0a. Good library support in Python (`stravalib`, `requests-oauthlib`). Well-documented API.

---

## Apple Watch / Apple Health — ✅ Via Shortcuts Webhook

### The Core Problem

**Apple Health has no server-side API.** HealthKit is an on-device iOS framework only. There is no REST API, no webhook system, no cloud endpoint. Apple Health data never leaves the device unless an app on that device explicitly reads and transmits it.

This means: **a pure webapp cannot pull Apple Health data.** Some iOS-side mechanism is required to bridge data to our server.

### Options Assessed

#### Option A: Build a Native iOS App — ❌ Overkill

- Write a companion iOS app using HealthKit to read step data.
- App sends daily totals to our backend via REST API.
- **Verdict:** Requires iOS development (Swift), App Store review, Apple Developer Program ($99/year). Massive scope increase. Not viable for this project.

#### Option B: Apple Shortcuts Automation — ✅ Recommended

- Users install a pre-built iOS Shortcut that:
  1. Reads today's step count from Health app.
  2. Formats as JSON.
  3. POSTs to our webhook endpoint.
- Schedule as daily automation (e.g., 10 PM each night).
- **Pros:** No app development, no App Store, free, uses native iOS features. Captures all-day passive steps.
- **Cons:** Requires each user to set up the Shortcut (one-time). Some iOS versions require user to confirm each run (can be disabled). Not 100% reliable if phone is off/dead.
- **Verdict:** Best option for small group of users. We provide a pre-built Shortcut link for one-tap install.

#### Option C: Health Auto Export App — Viable Fallback

- [Health Auto Export](https://www.healthautoexport.com/) is an iOS app ($0 free tier, $2.99/mo premium) that exports HealthKit data to webhooks automatically.
- Supports background export on a schedule (hourly, daily).
- **Verdict:** Good for users who want "set and forget" but requires installing and paying for a third-party app.

#### Option D: Apple Health → Strava — Activities Only

- Step data flows: **Apple Watch → Apple Health → Strava → our app via Strava API.**
- **Verdict:** Reuses Strava integration but misses passive all-day step tracking.

### Also Covers Garmin (iPhone)

Garmin Connect on iPhone syncs passive steps to Apple Health natively. This means the Apple Shortcuts webhook also captures Garmin passive steps for iPhone users. Chain: **Garmin Watch → Garmin Connect → Apple Health → Shortcuts → webhook.**

### Backend Work Required

One webhook endpoint (`POST /webhooks/apple-health`) that accepts JSON payload (`{ "steps": 9876, "date": "2026-04-16" }`) and authenticates the user via a per-user API key embedded in the Shortcut.

---

## Fitbit / Google Health API — ✅ Direct API Available

### API Overview

- **Access:** Public API, free for individual developers.
- **Auth:** Google OAuth 2.0 (Fitbit is now owned by Google).
- **Daily steps:** First-class endpoint — daily step count is a native concept.
- **Status:** Legacy Fitbit Web API sunsets September 2026. **Use the Google Health API for all new integrations.**
- **Rate limits:** Standard Google API quotas.

### Key Considerations

- The Google Health API is the **easiest direct integration** — public API, OAuth 2.0, daily steps as native data.
- No business approval needed (unlike Garmin).
- **All new integrations must target the Google Health API**, not the legacy Fitbit API.
- Credentials come from Google Cloud Console → APIs & Services → Credentials.
- Enable "Google Health API" under APIs & Services → Library.

### Fitbit → Strava Does NOT Work for Steps

Fitbit syncs only GPS-tracked exercises (runs, rides) to Strava — **not passive daily steps**. A direct Google Health API integration is needed for full step coverage.

### Integration Path

1. Register app in Google Cloud Console → enable Google Health API.
2. Create OAuth 2.0 client ID (Web application) under Credentials.
3. OAuth 2.0 flow: user authorizes → access + refresh tokens.
4. Pull daily step summary via dataset aggregate endpoint.
5. Store as `DailySteps` with `source=GOOGLE_HEALTH`.

### Effort Estimate

Low-medium. Very similar to Strava integration (OAuth 2.0, REST API). Could be implemented as a second provider using the same patterns.

---

## Backend Changes Required (All Providers)

Regardless of which providers we support, the following backend changes are needed:

### 1. Data Model: Multi-Source Steps

**Current:** `UniqueConstraint("user_id", "date")` — one entry per user per day.

**Needed:** `UniqueConstraint("user_id", "date", "source")` — one entry per source per day. This allows both manual and synced entries to coexist without overwriting each other.

### 2. User Preference: Active Source

Add `preferred_step_source` to User model. Leaderboard queries use only the preferred source's data (with fallback to whatever exists).

Options:
- `manual` (default) — use manually entered steps
- `strava` — use Strava-synced steps
- `apple_health` — use Apple Health steps (via Shortcut/webhook)
- `google_health` — use Google Health API-synced steps (Fitbit/Pixel Watch devices)

### 3. Webhook Receiver

Generic webhook endpoint that accepts step data from Apple Shortcuts, Health Auto Export, or future providers. Authenticates via per-user API key.

### 4. OAuth Integrations

- **Strava:** Standard OAuth 2.0 flow — connect, callback, disconnect, token refresh.
- **Google Health API:** Standard OAuth 2.0 flow — same pattern, different endpoints. Credentials from Google Cloud Console.

---

## Recommended Implementation Order

| Phase | Work | Testable Independently? |
|-------|------|------------------------|
| 1 | Data model changes (multi-source constraint, preferred source) | ✅ pytest + SQLite |
| 2 | Webhook endpoint for Apple Health Shortcuts | ✅ mock payloads |
| 3 | Strava OAuth 2.0 flow + step sync | ✅ mock OAuth + API |
| 4 | Frontend: provider connection UI, source preference picker | ✅ Vitest |
| 5 | Pre-built Apple Shortcut + setup instructions | ✅ manual test |
| 6 | Google Health API integration | ✅ mock OAuth + API |

---

## References

- [Garmin Connect Developer Program](https://developer.garmin.com/gc-developer-program/)
- [Garmin Health API (business only)](https://developer.garmin.com/health-api/overview/)
- [Garmin Health Connect sync (Android)](https://support.garmin.com/en-US/?faq=JToBEy0jfe6pIygark2Ui5)
- [Strava Developer API](https://developers.strava.com/)
- [Apple HealthKit Documentation](https://developer.apple.com/documentation/healthkit)
- [Health Auto Export App](https://www.healthautoexport.com/)
- [Google Health API (Fitbit successor)](https://developers.google.com/health/about)
- [Fitbit API Migration Guide](https://developers.google.com/fitbit/web-api/migration-guide)
- [`python-garminconnect` (unofficial)](https://github.com/cyberjunky/python-garminconnect)
