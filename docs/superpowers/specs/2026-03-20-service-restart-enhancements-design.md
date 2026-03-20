# Service Restart Enhancements Design

## Overview

Improve the ARM restart button UX (disable while restarting, show status message) and add a transcoder restart button with the same UX pattern.

## Scope

### UI Changes
- Restart button disables while request is in-flight, shows "Restarting..." text
- After restart completes, show success/error feedback message
- Add transcoder restart button alongside ARM restart button in Settings > System tab
- Both buttons use the same pattern: confirm dialog → disable + spinner text → feedback

### Transcoder Backend — New Endpoint
**File:** `automatic-ripping-machine-transcoder/src/main.py`

#### `POST /system/restart`
Calls `worker.shutdown()` and relies on Docker `restart: unless-stopped` to bring the container back. Returns `{"success": true}` immediately before shutdown begins.

### UI Backend — New Proxy
**File:** `backend/services/transcoder_client.py` — add `restart_transcoder() -> dict | None`
**File:** `backend/routers/system.py` — add `POST /api/system/restart-transcoder`

### UI Frontend
**File:** `frontend/src/lib/api/system.ts` — add `restartTranscoder()`
**File:** `frontend/src/routes/settings/+page.svelte` — refactor restart section with proper state management

## Design

### Restart Button Component Pattern
Both buttons follow the same pattern:
1. User clicks → `confirm()` dialog with warning
2. Button disables, text changes to "Restarting..."
3. API call fires
4. On success: show green "Service restarted" message, re-enable after 5s delay (give service time to come back)
5. On error: show red error message, re-enable button

### Transcoder Restart Endpoint
The transcoder runs as a Docker container with `restart: unless-stopped`. The restart endpoint:
1. Returns `{"success": true}` immediately
2. Schedules `worker.shutdown()` + `sys.exit(0)` on a background task
3. Docker automatically restarts the container

## Testing

### Transcoder
- Test restart endpoint returns success
- Test restart triggers shutdown

### UI Backend
- Test `restart_transcoder` proxy (success, unreachable)
- Test `POST /api/system/restart-transcoder` router (success, unreachable)

### UI Frontend
- Verify restart buttons render in Settings > System
- Verify disabled state during restart
