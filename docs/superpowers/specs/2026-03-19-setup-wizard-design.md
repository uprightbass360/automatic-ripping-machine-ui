# Setup Wizard Design

## Overview

Add a first-run setup wizard that guides new users through system configuration after a fresh deploy. The backend auto-initializes the database on startup (eliminating the current broken state where tables don't exist), and the UI presents a multi-step wizard for initial configuration review.

## Problem

On a fresh ARM deployment:
- The ARM backend (`arm-rippers`) starts and creates the SQLite file but **never creates tables** (no Alembic migration runs)
- The DB has zero tables — any endpoint that queries the DB returns 500
- The only way tables get created is by inserting a disc (ripper calls `check_db_version()`)
- The UI appears functional but the system is silently broken — it can't rip anything
- The transcoder, by contrast, auto-initializes correctly via `init_db()` in its lifespan

## Goals

- Eliminate the broken first-run state — DB should be ready before any request is served
- Provide a guided onboarding experience for new users
- Build an extensible wizard framework that future milestones can add steps to (auth, Apprise, import)
- Cleanly separate concerns: backend ensures infrastructure, UI guides configuration

## Non-Goals

- Authentication (Milestone 1 — wizard step added later)
- Database import from COMPLETED_PATH (separate sub-feature)
- Apprise notification setup (Milestone 5)
- Migration trigger UI (auto-init handles migrations automatically)

## Architecture

Two repos are modified:

1. **automatic-ripping-machine-neu** (ARM backend) — branch `feat/setup-wizard`
2. **automatic-ripping-machine-ui** (UI frontend + backend) — branch `feat/setup-wizard`

The transcoder requires no changes.

---

## Design

### 1. Backend — Auto-initialize DB on startup

**File:** `arm/runui.py`

Modify `startup()` to call `check_db_version()` before `arm_db_check()`. The function `check_db_version()` exists in `arm/services/config.py` and takes two arguments: `install_path` (from `cfg.arm_config['INSTALLPATH']`) and `db_file` (from `cfg.arm_config['DBFILE']`). It uses raw `sqlite3` internally — not the SQLAlchemy ORM — so it does not depend on `init_engine()` having run. However, `_alembic_upgrade()` (called internally) uses Alembic's `env.py` which reads the DB URL from ARM config, so the config must be loaded first (which it always is at module import time).

**Required fix to `check_db_version()`:** The current implementation has a gap — when the DB file exists but has no tables (the exact broken state this spec fixes), it catches the `sqlite3.OperationalError` for the missing `alembic_version` table and **returns without running migrations**. This must be patched: when `alembic_version` is missing but the DB file exists, run `_alembic_upgrade()` instead of returning. This is a code change in `arm/services/config.py`, not just a wiring change in `startup()`.

**Updated flow:**
```
startup()
  → db.init_engine(...)
  → check_db_version(INSTALLPATH, DBFILE)   # NEW — creates tables if needed
  → _clear_stale_pause()
  → arm_db_check()                          # Now always returns db_current=True
  → drives_update(startup=True)             # Now works because tables exist
```

**Safety:** `check_db_version()` is idempotent. The ripper still calls it too (no conflict). If it fails, startup logs the error but the server still starts (graceful degradation).

### 2. Backend — AppState migration

**New Alembic migration:** Add `setup_complete` boolean column to the `app_state` table (default `False`).

This flag tracks whether the user has completed the setup wizard. It prevents the UI from re-showing the wizard on every page load after setup is done.

**Existing deployment upgrade:** The migration includes a data migration that sets `setup_complete = True` when `alembic_version` already has a row (i.e., this is not a fresh DB being created for the first time). This is deterministic and prevents existing users from seeing the wizard on upgrade. Fresh installs get `setup_complete = False` because the migration runs as part of the initial `alembic upgrade head`.

### 3. Backend — Setup endpoints

**File:** New router `arm/api/v1/setup.py`

#### `GET /api/v1/setup/status`

Returns setup state. Must work regardless of DB state (catches DB errors gracefully).

```json
{
  "db_exists": true,
  "db_initialized": true,
  "db_current": true,
  "db_version": "h2i3j4k5l6m7",
  "db_head": "h2i3j4k5l6m7",
  "first_run": true,
  "arm_version": "13.3.0",
  "setup_steps": {
    "database": "complete",
    "drives": "pending",
    "settings_reviewed": "pending"
  }
}
```

**`first_run` logic:** `True` when `app_state.setup_complete` is `False` (or table doesn't exist). Distinguished from "backend unreachable" by the endpoint successfully responding.

**`setup_steps` logic:**
- `database`: `"complete"` when `db_initialized && db_current`, else `"pending"`
- `drives`: informational only — shows drive count but is NOT part of the completion gate (headless/NAS setups may have zero drives permanently)
- `settings_reviewed`: `"complete"` when `app_state.setup_complete` is `True`, else `"pending"`

**Completion gate:** The wizard redirect triggers when `first_run` is `true`, which is solely based on `app_state.setup_complete`. The `setup_steps` object is informational for the wizard UI — it does NOT gate completion. The "Finish Setup" button is always available regardless of step states.

Extensible — future milestones add keys (e.g., `"auth"`, `"apprise"`).

#### `POST /api/v1/setup/complete`

Marks setup as done. Sets `app_state.setup_complete = True`. Returns `{"success": true}`.

### 4. UI Backend — Proxy endpoints

**File:** New router in UI backend

- `GET /api/setup/status` → proxies to ARM's `GET /api/v1/setup/status`
- `POST /api/setup/complete` → proxies to ARM's `POST /api/v1/setup/complete`

### 5. UI Frontend — Layout guard

**File:** `frontend/src/routes/+layout.ts` (SvelteKit load function)

Use the existing `+layout.ts` load function to check setup status before rendering. If `first_run` is `true`, use SvelteKit's `redirect()` to send the user to `/setup` before the page renders. This avoids a flash of the main UI before redirecting (which would happen with an `onMount` approach in `+layout.svelte`).

**Guards:**
- If fetch fails (network error, ARM unreachable): do NOT redirect. Return normally and let the existing "service down" indicators handle it.
- If already on `/setup` route: do not redirect (avoid loop). The `/setup` route uses a separate layout or the load function checks `url.pathname`.
- If `setup_complete` is `true` (i.e., `first_run` is `false`): never redirect.

### 6. UI Frontend — Setup wizard components

**Route:** `frontend/src/routes/setup/+page.svelte`

**Component architecture:**
```
/setup/+page.svelte
  └── SetupWizard.svelte
        ├── Step registry (array of SetupStep configs)
        ├── StepIndicator.svelte (progress dots)
        └── Steps rendered dynamically:
              ├── WelcomeStep.svelte
              ├── DriveScanStep.svelte
              └── SettingsReviewStep.svelte
```

**Step registry interface:**
```typescript
interface SetupStep {
  id: string;
  label: string;
  component: Component;
  isComplete: (status: SetupStatus) => boolean;
}
```

Future milestones add steps by pushing to the registry array. The framework handles navigation, progress tracking, and completion.

### 7. Wizard steps

**Step 1: WelcomeStep**
- Shows: ARM version, CPU, RAM, database status (green checkmark), transcoder status
- Data from: `/api/setup/status`, `/api/system-info` (already exists in UI proxy layer)
- No user action — just "Next"

**Step 2: DriveScanStep**
- Shows: detected optical drives (maker, model, capabilities)
- If no drives: info message "No optical drives detected. ARM will detect drives when they become available."
- "Scan Again" button to re-trigger drive detection
- Non-blocking — user can proceed with zero drives

**Step 3: SettingsReviewStep**
- Shows: key path configuration (RAW_PATH, COMPLETED_PATH, TRANSCODE_PATH), rip method, metadata provider
- Read-only summary with "Edit in Settings" link per section
- "Finish Setup" button → calls `POST /api/setup/complete` → redirects to dashboard

**Post-wizard:** `setup_complete = true` in AppState. Layout guard stops redirecting. Users can revisit `/setup` directly to see current status.

---

## Testing

### ARM Backend
- Test `startup()` calls `check_db_version()` and creates tables
- Test `GET /api/v1/setup/status` with no DB, empty DB, initialized DB
- Test `POST /api/v1/setup/complete` sets flag
- Test setup_complete flag prevents `first_run: true`

### UI Backend
- Test proxy endpoints forward correctly
- Test proxy handles ARM unreachable gracefully

### UI Frontend
- Test SetupWizard renders steps from registry
- Test StepIndicator shows correct progress
- Test each step component renders expected content
- Test layout guard redirects on `first_run: true`
- Test layout guard does NOT redirect on network error
- Test "Finish Setup" calls complete endpoint and redirects

---

## Dependencies

All required packages are already installed in both projects. No new dependencies needed.

## Migration path

**Existing deployments:** The Alembic migration that adds `setup_complete` includes a data migration: if `alembic_version` already has a row when this migration runs (meaning the DB was previously initialized), set `setup_complete = True`. This prevents existing users from seeing the wizard on upgrade.

**Fresh installs:** `alembic upgrade head` runs all migrations including this one. Since it's the first time, no prior `alembic_version` row exists, so `setup_complete` stays at its default `False`. The wizard triggers on first UI load.

**Empty DB file (current broken state):** The patched `check_db_version()` detects the missing `alembic_version` table and runs `alembic upgrade head`, creating all tables including the new `setup_complete` column. Since this is effectively a fresh install, `setup_complete = False` and the wizard triggers.
