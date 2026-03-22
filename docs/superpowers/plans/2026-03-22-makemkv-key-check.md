# MakeMKV Key Validity Check — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Surface MakeMKV license key validity in the header bar status dots and provide a manual check/update button on the settings page.

**Architecture:** ARM backend persists key validity in `AppState` (updated by `prep_mkv()` on every rip). ARM exposes the stored value via the existing `ripping-enabled` endpoint and a new `key-check` endpoint. UI backend proxies these via `arm_client`. Frontend adds a status dot in the header and a "Check Key" button on the settings page.

**Tech Stack:** Python/FastAPI (ARM + UI backends), SQLAlchemy + Alembic, SvelteKit/Svelte 5 (frontend), httpx, Vitest + Testing Library

**Spec:** `docs/superpowers/specs/2026-03-22-makemkv-key-check-design.md`

**Repos:**
- ARM backend: `~/src/automatic-ripping-machine-neu` (branch `feat/maintenance`)
- UI: `~/src/automatic-ripping-machine-ui` (branch `feat/jake-maintenance`)

---

## Phase 1: ARM Backend — Persist & Expose Key Status

All tasks in this phase are in `~/src/automatic-ripping-machine-neu`.

### Task 1: Add Key Fields to AppState Model + Migration

**Files:**
- Modify: `arm/models/app_state.py`
- Create: `arm/migrations/versions/j4k5l6m7n8o9_app_state_add_makemkv_key.py`

- [ ] **Step 1: Add columns to AppState model**

```python
# arm/models/app_state.py
from arm.database import db


class AppState(db.Model):
    """Singleton table (one row, id=1) for global application state.

    Follows the same pattern as UISettings — a single-row table for
    app-wide toggles that need to survive restarts and be queryable
    from both the ripper and the UI.
    """
    __tablename__ = 'app_state'

    id = db.Column(db.Integer, primary_key=True)
    ripping_paused = db.Column(db.Boolean, default=False, nullable=False)
    setup_complete = db.Column(db.Boolean, default=False, nullable=False)
    makemkv_key_valid = db.Column(db.Boolean, nullable=True, default=None)
    makemkv_key_checked_at = db.Column(db.DateTime, nullable=True, default=None)

    @classmethod
    def get(cls):
        """Return the singleton row, creating it if it doesn't exist."""
        state = cls.query.get(1)
        if state is None:
            state = cls(id=1, ripping_paused=False, setup_complete=False)
            db.session.add(state)
            db.session.commit()
        return state

    def __repr__(self):
        return f'<AppState ripping_paused={self.ripping_paused} setup_complete={self.setup_complete}>'
```

- [ ] **Step 2: Create Alembic migration**

```python
# arm/migrations/versions/j4k5l6m7n8o9_app_state_add_makemkv_key.py
"""Add makemkv_key_valid and makemkv_key_checked_at to app_state.

Revision ID: j4k5l6m7n8o9
Revises: i3j4k5l6m7n8
Create Date: 2026-03-22
"""
from alembic import op
import sqlalchemy as sa

revision = 'j4k5l6m7n8o9'
down_revision = 'i3j4k5l6m7n8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('app_state') as batch_op:
        batch_op.add_column(sa.Column('makemkv_key_valid', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('makemkv_key_checked_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('app_state') as batch_op:
        batch_op.drop_column('makemkv_key_checked_at')
        batch_op.drop_column('makemkv_key_valid')
```

- [ ] **Step 3: Commit**

```bash
cd ~/src/automatic-ripping-machine-neu
git add arm/models/app_state.py arm/migrations/versions/j4k5l6m7n8o9_app_state_add_makemkv_key.py
git commit -m "feat: add makemkv_key_valid and makemkv_key_checked_at to AppState"
```

---

### Task 2: Update prep_mkv() to Persist Key Check Result

**Files:**
- Modify: `arm/ripper/makemkv.py:1124-1154` (prep_mkv function)
- Modify: `arm/ripper/makemkv.py:446-463` (UpdateKeyRunTimeError — add `self.returncode`)
- Test: `test/test_makemkv_key_persist.py`

**Prerequisites:** Add `from arm.database import db` to the imports at the top of `arm/ripper/makemkv.py` if not already present. Also add `self.returncode = returncode` to `UpdateKeyRunTimeError.__init__()` (line 454) so the endpoint can access the error code later:

- [ ] **Step 1: Write tests for prep_mkv() persistence**

```python
# test/test_makemkv_key_persist.py
"""Tests for prep_mkv() persisting key validity to AppState."""
import subprocess
import unittest.mock

import pytest

from arm.database import db
from arm.models.app_state import AppState


@pytest.fixture
def app_state(app_context):
    """Ensure AppState singleton exists."""
    state = AppState(id=1, ripping_paused=False, setup_complete=True)
    db.session.add(state)
    db.session.commit()
    return state


class TestPrepMkvPersistence:
    def test_success_persists_valid(self, app_state):
        """On successful key update, AppState.makemkv_key_valid is True."""
        with unittest.mock.patch("arm.ripper.makemkv.subprocess.run") as mock_run, \
             unittest.mock.patch("arm.ripper.makemkv.cfg.arm_config", {
                 "INSTALLPATH": "/opt/arm",
                 "MAKEMKV_PERMA_KEY": "",
             }):
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=b"Key updated"
            )
            from arm.ripper.makemkv import prep_mkv
            prep_mkv()

        state = AppState.get()
        assert state.makemkv_key_valid is True
        assert state.makemkv_key_checked_at is not None

    def test_failure_persists_invalid(self, app_state):
        """On UpdateKeyRunTimeError, AppState.makemkv_key_valid is False."""
        from arm.ripper.makemkv import prep_mkv, UpdateKeyRunTimeError

        with unittest.mock.patch("arm.ripper.makemkv.subprocess.run") as mock_run, \
             unittest.mock.patch("arm.ripper.makemkv.cfg.arm_config", {
                 "INSTALLPATH": "/opt/arm",
                 "MAKEMKV_PERMA_KEY": "",
             }):
            mock_run.side_effect = subprocess.CalledProcessError(
                40, ["bash", "/opt/arm/scripts/update_key.sh"], output=b""
            )
            with pytest.raises(UpdateKeyRunTimeError):
                prep_mkv()

        state = AppState.get()
        assert state.makemkv_key_valid is False
        assert state.makemkv_key_checked_at is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/src/automatic-ripping-machine-neu && python -m pytest test/test_makemkv_key_persist.py -v -x`
Expected: FAIL — `assert state.makemkv_key_valid is True` fails because `prep_mkv()` doesn't persist yet.

- [ ] **Step 3: Implement persistence in prep_mkv()**

Modify `arm/ripper/makemkv.py` — replace the existing `prep_mkv()` function (lines 1124-1154):

```python
def prep_mkv():
    """
    Make sure the MakeMKV key is up-to-date.

    Persists the result to AppState so the UI can display key validity.

    Raises:
        UpdateKeyRunTimeError
    """
    from datetime import datetime, timezone
    from arm.models.app_state import AppState

    try:
        logging.info("Updating MakeMKV key...")
        cmd = [
            shutil.which("bash") or "/bin/bash",
            os.path.join(cfg.arm_config["INSTALLPATH"], "scripts/update_key.sh"),
        ]
        # if MAKEMKV_PERMA_KEY is populated
        if cfg.arm_config['MAKEMKV_PERMA_KEY'] is not None and cfg.arm_config['MAKEMKV_PERMA_KEY'] != "":
            logging.debug("MAKEMKV_PERMA_KEY populated, using that...")
            # add MAKEMKV_PERMA_KEY as an argument to the command
            cmd += [cfg.arm_config['MAKEMKV_PERMA_KEY']]
        proc = subprocess.run(cmd, capture_output=True, check=True)
        stdout = proc.stdout.decode("utf-8")
        logging.debug(f"Command Output for update_key.sh: {stdout.splitlines()}")

        # Persist success
        state = AppState.get()
        state.makemkv_key_valid = True
        state.makemkv_key_checked_at = datetime.now(timezone.utc)
        db.session.commit()

    except subprocess.CalledProcessError as err:
        rc = err.returncode
        output = err.stdout.decode("utf-8") if err.stdout else ""
        if rc == UpdateKeyErrorCodes.URL_ERROR:
            logging.error(
                "Could not fetch MakeMKV beta key from forum.makemkv.com. "
                "The server may be unreachable. Set MAKEMKV_PERMA_KEY in "
                "arm.yaml to use a purchased key and avoid this dependency."
            )

        # Persist failure
        state = AppState.get()
        state.makemkv_key_valid = False
        state.makemkv_key_checked_at = datetime.now(timezone.utc)
        db.session.commit()

        raise UpdateKeyRunTimeError(rc, cmd, output=output)
```

Add the `db` import at the top of the file if not already present — check for `from arm.database import db`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/src/automatic-ripping-machine-neu && python -m pytest test/test_makemkv_key_persist.py -v -x`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
cd ~/src/automatic-ripping-machine-neu
git add arm/ripper/makemkv.py test/test_makemkv_key_persist.py
git commit -m "feat: persist MakeMKV key validity to AppState in prep_mkv()"
```

---

### Task 3: Key Check Endpoint + Ripping-Enabled Enhancement

**Files:**
- Modify: `arm/api/v1/system.py`
- Test: `test/test_makemkv_key_api.py`

- [ ] **Step 1: Write tests for key check endpoint and ripping-enabled enhancement**

```python
# test/test_makemkv_key_api.py
"""Tests for MakeMKV key check API endpoints."""
import unittest.mock

import pytest

from arm.database import db
from arm.models.app_state import AppState


@pytest.fixture
def app_state(app_context):
    state = AppState(id=1, ripping_paused=False, setup_complete=True)
    db.session.add(state)
    db.session.commit()
    return state


class TestRippingEnabledKeyStatus:
    """GET /api/v1/system/ripping-enabled includes key status."""

    def test_includes_key_fields_when_never_checked(self, client, app_state):
        response = client.get('/api/v1/system/ripping-enabled')
        data = response.json()
        assert data["ripping_enabled"] is True
        assert data["makemkv_key_valid"] is None
        assert data["makemkv_key_checked_at"] is None

    def test_includes_key_fields_when_valid(self, client, app_state):
        from datetime import datetime, timezone
        app_state.makemkv_key_valid = True
        app_state.makemkv_key_checked_at = datetime(2026, 3, 22, 12, 0, 0, tzinfo=timezone.utc)
        db.session.commit()

        response = client.get('/api/v1/system/ripping-enabled')
        data = response.json()
        assert data["makemkv_key_valid"] is True
        assert data["makemkv_key_checked_at"] is not None


class TestMakemkvKeyCheck:
    """POST /api/v1/system/makemkv-key-check endpoint."""

    def test_success_returns_valid(self, client, app_state):
        with unittest.mock.patch("arm.api.v1.system.prep_mkv") as mock_prep:
            mock_prep.return_value = None  # success = no exception
            # Simulate what prep_mkv does internally
            app_state.makemkv_key_valid = True
            db.session.commit()

            response = client.post('/api/v1/system/makemkv-key-check')

        assert response.status_code == 200
        data = response.json()
        assert data["key_valid"] is True
        assert "message" in data

    def test_failure_returns_invalid(self, client, app_state):
        from arm.ripper.makemkv import UpdateKeyRunTimeError

        with unittest.mock.patch("arm.api.v1.system.prep_mkv") as mock_prep:
            mock_prep.side_effect = UpdateKeyRunTimeError(
                40, ["bash", "/opt/arm/scripts/update_key.sh"], output=""
            )
            # Simulate what prep_mkv does internally
            app_state.makemkv_key_valid = False
            db.session.commit()

            response = client.post('/api/v1/system/makemkv-key-check')

        assert response.status_code == 200
        data = response.json()
        assert data["key_valid"] is False
        assert "message" in data
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/src/automatic-ripping-machine-neu && python -m pytest test/test_makemkv_key_api.py -v -x`
Expected: FAIL — endpoints don't exist yet.

- [ ] **Step 3: Implement the endpoints**

Add to `arm/api/v1/system.py` — after the existing `get_ripping_enabled` function:

First, update the existing `get_ripping_enabled`:

```python
@router.get('/system/ripping-enabled')
def get_ripping_enabled():
    """Return whether ripping is currently enabled, plus MakeMKV key status."""
    state = AppState.get()
    return {
        "ripping_enabled": not state.ripping_paused,
        "makemkv_key_valid": state.makemkv_key_valid,
        "makemkv_key_checked_at": (
            state.makemkv_key_checked_at.isoformat()
            if state.makemkv_key_checked_at else None
        ),
    }
```

Then add the new key-check endpoint:

```python
@router.post('/system/makemkv-key-check')
def check_makemkv_key():
    """Run prep_mkv() to validate/update the MakeMKV key.

    This is a blocking call — it runs update_key.sh which may make a
    network request to forum.makemkv.com.  FastAPI runs sync handlers
    in a thread pool, so this won't block other requests.
    """
    from arm.ripper.makemkv import prep_mkv, UpdateKeyRunTimeError, UpdateKeyErrorCodes

    message = "MakeMKV key is valid"
    try:
        prep_mkv()
    except UpdateKeyRunTimeError as exc:
        code = UpdateKeyErrorCodes(exc.returncode)
        messages = {
            UpdateKeyErrorCodes.URL_ERROR: (
                "Could not reach forum.makemkv.com — set MAKEMKV_PERMA_KEY "
                "in arm.yaml to use a purchased key"
            ),
            UpdateKeyErrorCodes.PARSE_ERROR: "MakeMKV settings file is corrupt",
            UpdateKeyErrorCodes.INTERNAL_ERROR: "Key update script produced invalid output",
            UpdateKeyErrorCodes.INVALID_MAKEMKV_SERIAL: (
                "Invalid MakeMKV serial key format — should match M-XXXX-..."
            ),
        }
        message = messages.get(code, f"Key update failed (error {code.name})")

    state = AppState.get()
    return {
        "key_valid": state.makemkv_key_valid,
        "checked_at": (
            state.makemkv_key_checked_at.isoformat()
            if state.makemkv_key_checked_at else None
        ),
        "message": message,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/src/automatic-ripping-machine-neu && python -m pytest test/test_makemkv_key_api.py -v -x`
Expected: All PASS

- [ ] **Step 5: Run full test suite to check for regressions**

Run: `cd ~/src/automatic-ripping-machine-neu && python -m pytest test/ -x -q`
Expected: All pass. The existing `TestApiRippingEnabled` tests may need updating since the response now has extra fields — if they fail, update them to expect the new fields.

- [ ] **Step 6: Commit**

```bash
cd ~/src/automatic-ripping-machine-neu
git add arm/api/v1/system.py test/test_makemkv_key_api.py
git commit -m "feat: add MakeMKV key check endpoint and expose key status in ripping-enabled"
```

---

## Phase 2: UI Backend — Proxy Layer

All tasks in this phase are in `~/src/automatic-ripping-machine-ui`.

### Task 4: arm_client — Key Check Proxy + Ripping-Enabled Reader

**Files:**
- Modify: `backend/services/arm_client.py`

- [ ] **Step 1: Add functions to arm_client**

Add at the end of `backend/services/arm_client.py`, after the existing maintenance functions:

```python
# --- MakeMKV Key Check ---


async def get_ripping_enabled() -> dict[str, Any] | None:
    """Get ripping-enabled status and MakeMKV key validity from ARM."""
    return await _request("GET", "/api/v1/system/ripping-enabled")


async def check_makemkv_key() -> dict[str, Any] | None:
    """Trigger a MakeMKV key validity check on ARM.

    Uses a 30-second timeout since prep_mkv() may fetch the beta key
    from forum.makemkv.com over the network.
    """
    return await _request("POST", "/api/v1/system/makemkv-key-check", timeout=30.0)
```

Note: The `_request` function passes `**kwargs` to `get_client().request()`. The httpx client's `request()` method accepts a `timeout` kwarg that overrides the client default. Verify this works — if `_request` doesn't pass `timeout` through, add it to the function signature.

- [ ] **Step 2: Commit**

```bash
git add backend/services/arm_client.py
git commit -m "feat: add MakeMKV key check and ripping-enabled proxy to arm_client"
```

---

### Task 5: Dashboard — Include Key Status + Key Check Proxy Endpoint

**Files:**
- Modify: `backend/routers/dashboard.py`
- Modify: `backend/models/schemas.py`

- [ ] **Step 1: Add key fields to DashboardResponse schema**

In `backend/models/schemas.py`, add two fields to `DashboardResponse`:

```python
class DashboardResponse(BaseModel):
    db_available: bool = True
    arm_online: bool = False
    active_jobs: list[JobSchema] = []
    system_info: HardwareInfoSchema | None = None
    drives_online: int = 0
    drive_names: dict[str, str] = {}
    notification_count: int = 0
    ripping_enabled: bool = True
    makemkv_key_valid: bool | None = None
    makemkv_key_checked_at: str | None = None
    transcoder_online: bool = False
    transcoder_stats: dict[str, Any] | None = None
    transcoder_system_stats: SystemStatsSchema | None = None
    active_transcodes: list[dict[str, Any]] = []
    system_stats: SystemStatsSchema | None = None
    transcoder_info: HardwareInfoSchema | None = None
```

- [ ] **Step 2: Update dashboard endpoint to fetch key status via ARM API**

In `backend/routers/dashboard.py`, modify `get_dashboard()` to call `arm_client.get_ripping_enabled()` instead of `arm_db.get_ripping_paused()`:

Replace the section that reads `ripping_paused`:

```python
    ripping_paused = False
    makemkv_key_valid = None
    makemkv_key_checked_at = None

    if db_available:
        active_jobs = arm_db.get_active_jobs()
        drives = arm_db.get_drives()
        drives_online = sum(1 for d in drives if not getattr(d, 'stale', False))
        drive_names = {}
        for d in drives:
            if d.mount and d.name:
                drive_names[d.mount] = d.name
                basename = d.mount.rsplit("/", 1)[-1]
                drive_names[f"/dev/{basename}"] = d.name
        notification_count = arm_db.get_notification_count()
        ripping_paused = arm_db.get_ripping_paused()
```

Change the `ripping_paused = arm_db.get_ripping_paused()` line and add a parallel task for ripping-enabled:

```python
    ripping_paused = False
    makemkv_key_valid = None
    makemkv_key_checked_at = None

    if db_available:
        active_jobs = arm_db.get_active_jobs()
        drives = arm_db.get_drives()
        drives_online = sum(1 for d in drives if not getattr(d, 'stale', False))
        drive_names = {}
        for d in drives:
            if d.mount and d.name:
                drive_names[d.mount] = d.name
                basename = d.mount.rsplit("/", 1)[-1]
                drive_names[f"/dev/{basename}"] = d.name
        notification_count = arm_db.get_notification_count()
        ripping_paused = arm_db.get_ripping_paused()

    # Transcoder + ARM system stats + ripping status in parallel
    transcoder_task = asyncio.create_task(_fetch_transcoder())
    stats_task = asyncio.create_task(arm_client.get_system_stats())
    transcoder_stats_task = asyncio.create_task(transcoder_client.get_system_stats())
    ripping_task = asyncio.create_task(arm_client.get_ripping_enabled())
```

Then after the awaits, extract key status:

```python
    ripping_data = await ripping_task
    if ripping_data and ripping_data.get("ripping_enabled") is not None:
        makemkv_key_valid = ripping_data.get("makemkv_key_valid")
        makemkv_key_checked_at = ripping_data.get("makemkv_key_checked_at")
```

And include the new fields in the return:

```python
    return DashboardResponse(
        ...
        ripping_enabled=not ripping_paused,
        makemkv_key_valid=makemkv_key_valid,
        makemkv_key_checked_at=makemkv_key_checked_at,
        ...
    )
```

- [ ] **Step 3: Add key check proxy endpoint**

Add to `backend/routers/dashboard.py`:

```python
@router.post("/dashboard/makemkv-key-check")
async def check_makemkv_key():
    """Proxy MakeMKV key check to ARM backend."""
    result = await arm_client.check_makemkv_key()
    if result is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="ARM is unreachable")
    if result.get("success") is False:
        from fastapi import HTTPException
        raise HTTPException(status_code=502, detail=result.get("error", "ARM request failed"))
    return result
```

- [ ] **Step 4: Commit**

```bash
git add backend/routers/dashboard.py backend/models/schemas.py
git commit -m "feat: add MakeMKV key status to dashboard and key check proxy endpoint"
```

---

## Phase 3: Frontend

All tasks in this phase are in `~/src/automatic-ripping-machine-ui`.

### Task 6: Dashboard Types & Store + API Function

**Files:**
- Modify: `frontend/src/lib/types/arm.ts`
- Modify: `frontend/src/lib/stores/dashboard.ts`
- Modify: `frontend/src/lib/api/dashboard.ts`

- [ ] **Step 1: Add key fields to DashboardData type**

In `frontend/src/lib/types/arm.ts`, add to the `DashboardData` interface after `ripping_enabled`:

```typescript
	makemkv_key_valid: boolean | null;
	makemkv_key_checked_at: string | null;
```

- [ ] **Step 2: Update emptyDashboard defaults**

In `frontend/src/lib/stores/dashboard.ts`, add to `emptyDashboard`:

```typescript
	makemkv_key_valid: null,
	makemkv_key_checked_at: null,
```

- [ ] **Step 3: Add checkMakemkvKey API function**

In `frontend/src/lib/api/dashboard.ts`, add:

```typescript
export function checkMakemkvKey(): Promise<{ key_valid: boolean; checked_at: string | null; message: string }> {
	return apiFetch('/api/dashboard/makemkv-key-check', { method: 'POST' });
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/types/arm.ts frontend/src/lib/stores/dashboard.ts frontend/src/lib/api/dashboard.ts
git commit -m "feat: add MakeMKV key status to dashboard types, store, and API client"
```

---

### Task 7: Header Status Dot

**Files:**
- Modify: `frontend/src/routes/+layout.svelte`

- [ ] **Step 1: Add Key status dot to header**

In `frontend/src/routes/+layout.svelte`, find the service health dots section (around line 136-149). After the Transcode dot `</a>` (line 148), add:

```svelte
					<a href="/settings#ripping/makemkv" class="flex items-center gap-1.5 hover:opacity-75 transition-opacity"
						title={$dashboard.makemkv_key_valid === true
							? `MakeMKV key valid${$dashboard.makemkv_key_checked_at ? ' — checked ' + new Date($dashboard.makemkv_key_checked_at).toLocaleString() : ''}`
							: $dashboard.makemkv_key_valid === false
								? 'MakeMKV key invalid — click to update'
								: 'MakeMKV key not checked yet'}
					>
						<div class="h-2 w-2 shrink-0 rounded-full {$dashboard.makemkv_key_valid === true ? 'bg-green-500' : $dashboard.makemkv_key_valid === false ? 'bg-red-500' : 'bg-gray-400'}"></div>
						<span class="text-gray-700 dark:text-gray-200">Key</span>
					</a>
```

- [ ] **Step 2: Build check**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/routes/+layout.svelte
git commit -m "feat: add MakeMKV key status dot to header bar"
```

---

### Task 8: Settings Page — Check Key Button + FindVUK Label Update

**Files:**
- Modify: `frontend/src/routes/settings/+page.svelte`

- [ ] **Step 1: Update FindVUK label and description**

In `frontend/src/routes/settings/+page.svelte`, find the `MAKEMKV_COMMUNITY_KEYDB` entry in the settings metadata (around line 645). Change:

```typescript
		MAKEMKV_COMMUNITY_KEYDB: { label: 'Community Key Database', description: 'Download community keydb.cfg at container startup' },
```

to:

```typescript
		MAKEMKV_COMMUNITY_KEYDB: { label: 'Use FindVUK', description: 'Download FindVUK community keydb.cfg for Blu-ray decryption keys' },
```

- [ ] **Step 2: Add Check Key button and result message**

Note: The MakeMKV panel already gets `id="panel-makemkv"` automatically from its label via the panel rendering code. The header link uses `#ripping/makemkv` which the settings page's `parseHash()` handles by switching to the ripping tab and scrolling to the panel.

Import `checkMakemkvKey` at the top of the script:

```typescript
	import { checkMakemkvKey } from '$lib/api/dashboard';
```

Add state variables:

```typescript
	let checkingKey = $state(false);
	let keyCheckResult = $state<{ type: 'success' | 'error'; message: string } | null>(null);
	let keyCheckTimeout: ReturnType<typeof setTimeout> | null = null;
```

Add the handler function:

```typescript
	async function handleKeyCheck() {
		if (checkingKey) return;
		checkingKey = true;
		keyCheckResult = null;
		if (keyCheckTimeout) clearTimeout(keyCheckTimeout);
		try {
			const res = await checkMakemkvKey();
			keyCheckResult = {
				type: res.key_valid ? 'success' : 'error',
				message: res.message
			};
		} catch (e) {
			keyCheckResult = {
				type: 'error',
				message: e instanceof Error ? e.message : 'Failed to check key'
			};
		} finally {
			checkingKey = false;
			keyCheckTimeout = setTimeout(() => (keyCheckResult = null), 10000);
		}
	}
```

In the MakeMKV panel template, add after the panel's settings fields (after the last key input in the MakeMKV subpanel):

```svelte
<!-- Check Key button — inside MakeMKV panel -->
<div class="mt-4 flex items-center gap-3">
	<button
		onclick={handleKeyCheck}
		disabled={checkingKey}
		class="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-on-primary hover:bg-primary-hover disabled:opacity-50"
	>
		{checkingKey ? 'Checking...' : 'Check Key'}
	</button>
	{#if keyCheckResult}
		<span class="text-sm {keyCheckResult.type === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
			{keyCheckResult.message}
		</span>
	{/if}
</div>
```

- [ ] **Step 3: Build check**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/settings/+page.svelte
git commit -m "feat: add Check Key button to settings, update FindVUK label"
```

---

### Task 9: Frontend Tests

**Files:**
- Modify: `frontend/src/routes/settings/__tests__/settings-page.test.ts`

- [ ] **Step 1: Add tests for key check button and FindVUK label**

Add to the existing settings page test file:

```typescript
	describe('MakeMKV key check', () => {
		it('renders Check Key button in MakeMKV panel', async () => {
			renderComponent(SettingsPage);
			await waitFor(() => {
				expect(screen.getByText('MakeMKV')).toBeInTheDocument();
			});
			expect(screen.getByText('Check Key')).toBeInTheDocument();
		});

		it('renders updated FindVUK label', async () => {
			renderComponent(SettingsPage);
			await waitFor(() => {
				expect(screen.getByText('Use FindVUK')).toBeInTheDocument();
			});
		});
	});
```

- [ ] **Step 2: Run tests**

Run: `cd frontend && npx vitest run src/routes/settings/__tests__/settings-page.test.ts`
Expected: All PASS

- [ ] **Step 3: Run full frontend test suite**

Run: `cd frontend && npx vitest run`
Expected: All PASS with no regressions

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/settings/__tests__/settings-page.test.ts
git commit -m "test: add MakeMKV key check and FindVUK label tests"
```

---

### Task 10: Full Verification

- [ ] **Step 1: Run ARM backend full test suite**

Run: `cd ~/src/automatic-ripping-machine-neu && python -m pytest test/ -v -q`
Expected: All PASS

- [ ] **Step 2: Run frontend full test suite**

Run: `cd ~/src/automatic-ripping-machine-ui/frontend && npx vitest run`
Expected: All PASS

- [ ] **Step 3: Build check**

Run: `cd ~/src/automatic-ripping-machine-ui/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 4: Rebuild ARM container and test live**

```bash
cd ~/src/automatic-ripping-machine-neu && docker compose -f docker-compose.yml -f docker-compose.dev.yml build arm-rippers
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d arm-rippers
```

Wait for ARM to start, then rebuild frontend and restart UI:

```bash
cd ~/src/automatic-ripping-machine-ui/frontend && npm run build
docker restart arm-ui
```

Verify:
- `curl http://localhost:8080/api/v1/system/ripping-enabled` returns `makemkv_key_valid` field
- `curl -X POST http://localhost:8080/api/v1/system/makemkv-key-check` returns key check result
- UI header shows Key status dot
- Settings MakeMKV panel has Check Key button
