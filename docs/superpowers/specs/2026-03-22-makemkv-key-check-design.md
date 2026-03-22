# MakeMKV Key Validity Check

## Summary

Surface the MakeMKV license key validity status in the header bar and provide a manual check/update button on the settings page. Key validity is persisted in the database and refreshed automatically on every rip, or manually via the settings page.

## Changes

### 1. ARM Backend — Persist Key Validity in AppState

Add two columns to the `AppState` singleton table (`arm/models/app_state.py`):

- `makemkv_key_valid` (Boolean, nullable, default `None`) — `True` if last check succeeded, `False` if failed, `None` if never checked
- `makemkv_key_checked_at` (DateTime, nullable, default `None`) — timestamp of last check

Requires an Alembic migration.

### 2. ARM Backend — Update prep_mkv() to Persist Result

Modify `prep_mkv()` itself in `arm/ripper/makemkv.py` to persist the result to `AppState` before returning/raising. This ensures every caller (rip flow, API endpoint) automatically gets persistence as a side effect:

- On success: `key_valid = True`, `key_checked_at = utcnow()`
- On `UpdateKeyRunTimeError`: set `key_valid = False`, `key_checked_at = utcnow()`, then re-raise

This happens automatically on every rip, keeping the value fresh.

### 3. ARM Backend — Key Check Endpoint

New endpoint: `POST /api/v1/system/makemkv-key-check`

- Calls `prep_mkv()` (which may fetch/update the beta key as a side effect)
- Result is already persisted by `prep_mkv()` itself (section 2)
- Returns `{ "key_valid": true|false, "checked_at": "ISO timestamp", "message": "..." }`
- On success: message = "MakeMKV key is valid"
- On `UpdateKeyRunTimeError`: map `returncode` via `UpdateKeyErrorCodes` to a user-facing message (e.g., "Beta key expired — update MakeMKV or set MAKEMKV_PERMA_KEY", "Could not reach forum.makemkv.com")
- FastAPI runs sync route handlers in a thread pool, so the blocking subprocess is safe

### 4. ARM Backend — Expose Key Status in Existing Endpoints

Add `makemkv_key_valid` and `makemkv_key_checked_at` to the response of `GET /api/v1/system/ripping-enabled`. Read from `AppState.get()` — zero cost.

### 5. UI Backend — Dashboard Includes Key Status

The dashboard currently reads `ripping_paused` directly from the ARM database via `arm_db`, but new features should interact with ARM via API, not raw DB calls. The key status fields (`makemkv_key_valid`, `makemkv_key_checked_at`) are already exposed in the `GET /api/v1/system/ripping-enabled` response (section 4). The dashboard endpoint should call ARM's API for these values via `arm_client` and include them in the dashboard response.

### 6. UI Backend — Proxy Key Check

New endpoint: `POST /api/dashboard/makemkv-key-check`

Proxies to `POST /api/v1/system/makemkv-key-check` on ARM via `arm_client`. Use a **30-second timeout** for this specific call since `prep_mkv()` makes a network request to `forum.makemkv.com` which can be slow (the default `arm_client` timeout is 10 seconds). Returns the result directly.

### 7. Frontend — Dashboard Store & Types

Add to `DashboardData` in `frontend/src/lib/types/arm.ts`:

- `makemkv_key_valid: boolean | null`
- `makemkv_key_checked_at: string | null`

Update `emptyDashboard` in `frontend/src/lib/stores/dashboard.ts` — defaults to `null` for both.

### 8. Frontend — Header Status Dot

Add a 4th status dot in the service health section of `+layout.svelte`, after the Transcode dot:

```
[●] ARM  [●] DB  [●] Transcode  [●] Key
```

- **Green**: `makemkv_key_valid === true`
- **Red**: `makemkv_key_valid === false`
- **Gray**: `makemkv_key_valid === null` (never checked)
- Wraps in an `<a href="/settings#makemkv">` — always navigates to settings
- Tooltip shows last check time or "Not checked yet"
- Desktop only (matches existing dots in `hidden lg:flex` container) — mobile does not show status dots

Note: The settings page MakeMKV panel needs an `id="makemkv"` anchor element for the `#makemkv` hash link to scroll correctly.

### 9. Frontend — Settings MakeMKV Panel

Add to the MakeMKV settings panel:

- **`id="makemkv"` anchor** on the panel container for hash-link scrolling
- **"Check Key" button** — POSTs to `/api/dashboard/makemkv-key-check`
- While checking: button shows spinner/disabled state
- On success: green success message "MakeMKV key is valid" with timestamp
- On failure: red error message with the failure reason
- Message auto-dismisses after 10 seconds or on next check

### 10. Frontend — Update FindVUK Setting Label

Change the `MAKEMKV_COMMUNITY_KEYDB` setting in the settings page:

- **Label**: "Use FindVUK" (was "Community Key Database")
- **Description**: "Download FindVUK community keydb.cfg for Blu-ray decryption keys"

## Data Flow

```
Rip starts → prep_mkv() → success/fail → AppState updated (inside prep_mkv)
                                              ↓
Dashboard polls (5s) → arm_client calls ripping-enabled API → header dot color
                                              ↓
User clicks dot → navigates to /settings#makemkv
                                              ↓
User clicks "Check Key" → POST → arm_client → ARM endpoint → prep_mkv() → AppState updated → response → success/error message
```

## States

| State | Header Dot | Settings Button | Last Checked |
|-------|-----------|----------------|--------------|
| Never checked | Gray | "Check Key" | "Not checked yet" |
| Valid | Green | "Check Key" | "Last checked: {time}" |
| Invalid | Red | "Check Key" | "Last checked: {time}" |
| Checking... | Previous color | Disabled + spinner | — |

## Files Changed

**ARM backend (`~/src/automatic-ripping-machine-neu`):**
- `arm/models/app_state.py` — add columns
- `arm/migrations/versions/xxx_add_makemkv_key_fields.py` — migration
- `arm/ripper/makemkv.py` — persist result inside `prep_mkv()` before return/raise
- `arm/api/v1/system.py` — new key-check endpoint, include key status in ripping-enabled response

**UI backend (`~/src/automatic-ripping-machine-ui`):**
- `backend/routers/dashboard.py` — include key fields in dashboard response (via arm_client), add proxy endpoint
- `backend/services/arm_client.py` — add `check_makemkv_key()` with 30s timeout

**UI frontend:**
- `frontend/src/lib/types/arm.ts` — update `DashboardData`
- `frontend/src/lib/stores/dashboard.ts` — update defaults
- `frontend/src/lib/api/dashboard.ts` — add `checkMakemkvKey()`
- `frontend/src/routes/+layout.svelte` — add Key status dot
- `frontend/src/routes/settings/+page.svelte` — add `id="makemkv"` anchor, Check Key button + result message, update FindVUK label/description

## Design Constraints

- Key check endpoint may take up to 30 seconds (network call to forum.makemkv.com) — UI must handle loading state, arm_client uses 30s timeout for this call
- Dashboard poll must not call the check endpoint — it reads the stored value via ARM's ripping-enabled API
- `prep_mkv()` is synchronous (subprocess) — FastAPI runs sync handlers in a thread pool, so this is safe
- `UpdateKeyRunTimeError` carries a `returncode` but not a user-friendly message — the endpoint must map codes via `UpdateKeyErrorCodes` enum to meaningful strings
