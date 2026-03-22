# MakeMKV Key Validity Check

## Summary

Surface the MakeMKV license key validity status in the header bar and provide a manual check/update button on the settings page. Key validity is persisted in the database and refreshed automatically on every rip, or manually via the settings page.

## Changes

### 1. ARM Backend — Persist Key Validity in AppState

Add two columns to the `AppState` singleton table:

- `makemkv_key_valid` (Boolean, nullable, default `None`) — `True` if last check succeeded, `False` if failed, `None` if never checked
- `makemkv_key_checked_at` (DateTime, nullable, default `None`) — timestamp of last check

Requires an Alembic migration.

### 2. ARM Backend — Update prep_mkv() to Persist Result

After `prep_mkv()` in `arm/ripper/makemkv.py` succeeds or fails, write the result to `AppState`:

- On success: `key_valid = True`, `key_checked_at = utcnow()`
- On `UpdateKeyRunTimeError`: `key_valid = False`, `key_checked_at = utcnow()`

This happens automatically on every rip, keeping the value fresh.

### 3. ARM Backend — Key Check Endpoint

New endpoint: `POST /api/v1/system/makemkv-key-check`

- Runs `prep_mkv()` (which may fetch/update the beta key as a side effect)
- Persists result to `AppState`
- Returns `{ "key_valid": true|false, "checked_at": "ISO timestamp", "message": "..." }`
- On success: message = "MakeMKV key is valid"
- On failure: message = error description from `UpdateKeyRunTimeError`

### 4. ARM Backend — Expose Key Status in Existing Endpoints

Add `makemkv_key_valid` and `makemkv_key_checked_at` to the response of `GET /api/v1/system/ripping-enabled` (which the UI dashboard already polls). Read from `AppState` — zero cost.

### 5. UI Backend — Dashboard Includes Key Status

The dashboard endpoint already calls ARM for ripping-enabled status. Include the new `makemkv_key_valid` and `makemkv_key_checked_at` fields in the dashboard response.

### 6. UI Backend — Proxy Key Check

New endpoint: `POST /api/dashboard/makemkv-key-check`

Proxies to `POST /api/v1/system/makemkv-key-check` on ARM. Returns the result directly.

### 7. Frontend — Dashboard Store & Types

Add to `DashboardData`:

- `makemkv_key_valid: boolean | null`
- `makemkv_key_checked_at: string | null`

Update `emptyDashboard` defaults to `null` for both.

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

### 9. Frontend — Settings MakeMKV Panel

Add to the MakeMKV settings panel:

- **"Check Key" button** — POSTs to `/api/dashboard/makemkv-key-check`
- While checking: button shows spinner/disabled state
- On success: green success message "MakeMKV key is valid" with timestamp
- On failure: red error message with the failure reason
- Message auto-dismisses after 10 seconds or on next check

### 10. Frontend — Update FindVUK Setting Label

Change the `MAKEMKV_COMMUNITY_KEYDB` setting in the settings page:

- **Label**: "Use FindVUK" (was "Community Key Database")
- **Description**: "Override default MakeMKV decryption key lookup to use community database"

## Data Flow

```
Rip starts → prep_mkv() → success/fail → AppState updated
                                              ↓
Dashboard polls (5s) → reads AppState → header dot color
                                              ↓
User clicks dot → navigates to /settings#makemkv
                                              ↓
User clicks "Check Key" → POST /makemkv-key-check → prep_mkv() → AppState updated → success/error message
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
- `arm/ripper/makemkv.py` — persist result after `prep_mkv()`
- `arm/api/v1/system.py` — new endpoint + include in ripping-enabled response

**UI backend (`~/src/automatic-ripping-machine-ui`):**
- `backend/routers/dashboard.py` — include key fields in dashboard, add proxy endpoint
- `backend/services/arm_client.py` — add `check_makemkv_key()` function

**UI frontend:**
- `frontend/src/lib/types/arm.ts` — update `DashboardData`
- `frontend/src/lib/stores/dashboard.ts` — update defaults
- `frontend/src/lib/api/dashboard.ts` — add `checkMakemkvKey()`
- `frontend/src/routes/+layout.svelte` — add Key status dot
- `frontend/src/routes/settings/+page.svelte` — add Check Key button, update FindVUK label/description

## Design Constraints

- Key check endpoint may take several seconds (network call to forum.makemkv.com) — UI must handle loading state
- Dashboard poll must not call the check endpoint — it only reads the stored value
- `prep_mkv()` is synchronous (subprocess) — endpoint must be sync or run in thread
