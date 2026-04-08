# Job Detail Header Redesign

## Overview

Reorganize the top of the job detail page (`/jobs/[id]`) into a single structured container with clear visual grouping. Drawing styling cues from the settings page (bordered containers, grid lines, consistent input styling).

## Layout Structure

One container with four vertical sections:

```
+------------------------------------------------------------------+
| Title Bar: Title (Year)  badges...     [action buttons -->]      |
+------------------------------------------------------------------+
| Poster |  4-col metadata grid with full cell borders             |
| (2:3)  |  (rows/cols adapt to field count)                       |
|        |                                                          |
+------------------------------------------------------------------+
| Panel toggle bar: Identify | Rip Settings | Transcode | CRC | Debug |
+------------------------------------------------------------------+
| (expanded panel content, if any panel is active)                 |
+------------------------------------------------------------------+
```

### I. Title Bar

Top edge of the container, spans full width.

**Left side (flowing):**
- Title (large, bold, white)
- Year (muted, in parentheses)
- Status badge (pill)
- Multi-Title badge (purple pill, when applicable)
- IMDb badge (yellow pill, when applicable)

**Right side (pushed with `margin-left: auto`):**
- Action buttons (pill-style, contextual per job state)

**Action buttons by state:**
- Active jobs: Abandon (yellow)
- Completed success: Re-transcode (indigo), Fix Permissions (blue/outlined), Delete (red/outlined), Purge (orange/outlined)
- Completed fail: Delete (red/outlined), Purge (orange/outlined)
- Waiting: Abandon (yellow)

**Removed:** Log button (was in the old action bar). Log is accessible from the inline log feed and log page.

### II. Poster + Metadata Grid

Below the title bar, inside the same container.

**Poster (left column):**
- Fixed width: 120px
- Aspect ratio: 2:3 (natural height via `aspect-ratio: 2/3`)
- Top-aligned (`align-items: flex-start`)
- Separated from grid by vertical border
- Placeholder icon when no poster available (dashed border, disc icon)
- Music discs: 1:1 aspect ratio (album art)

**Metadata Grid (right side):**
- Always 4 columns
- Pad incomplete last row with empty bordered cells
- All cells have full borders (top, bottom, left, right dividers using `border-primary/15`)
- Labels: uppercase, small, muted (`text-xs text-gray-500 uppercase tracking-wide`)
- Values: white, medium weight (`text-sm font-medium text-white`)
- Monospace for: Label, CRC, paths
- Select dropdown for Title Mode (matching settings page inputClass styling)
- IMDb/TVDB render as linked text (the ID, e.g. tt0133093, linking to external site)

### III. Panel Toggle Bar

Attached to the bottom of the container, full width.

- Equal-width buttons separated by vertical dividers
- Inactive: muted text, no background
- Active: primary color text, subtle background tint, bottom border highlight (2px solid primary)
- Clicking a panel toggles it (click active panel to collapse)

**Panels shown (contextual):**
- Identify (always for video discs)
- Rip Settings (always)
- Transcode Settings (video discs only)
- CRC Lookup (DVD only)
- Debug (always)

### IV. Expanded Panel Content

When a panel is active, its content renders below the toggle bar within the same container. Same components as today (TitleSearch, RipSettings, TranscodeOverrides, CrcLookup), just relocated.

## Metadata Fields by Job Type

### Video Disc - Movie

| Field | Source | Notes |
|-------|--------|-------|
| Type | `video_type` | "Movie", "Series", etc. |
| Disc Type | `disctype` | "Blu-ray", "DVD", "4K UHD" |
| Title Mode | `multi_title` | Select dropdown (Single/Multi), video discs only |
| Titles | `no_of_titles` | Integer |
| Label | `label` | Monospace |
| Device | `devpath` | e.g. /dev/sr0 |
| Source | `source_type` | "Disc" or "Folder" |
| CRC | `crc_id` | Monospace, only when present AND DVD |
| IMDb | `imdb_id` | Linked text, only when present |
| Disc # | `disc_number`/`disc_total` | "2 of 4", only when disc_number present |
| Started | `start_time` | Formatted datetime |
| Finished | `stop_time` | Formatted datetime, completed jobs only |
| Duration | `job_length` | Time string, completed jobs only |
| Elapsed | computed | Active jobs only (replaces Finished/Duration) |
| Output | `path` | Monospace, truncated with tooltip, when present |
| Raw | `raw_path` | Monospace, when present |
| Transcode | `transcode_path` | Monospace, when present |

### Video Disc - Series

All movie fields plus:

| Field | Source | Notes |
|-------|--------|-------|
| Season | `season` or `season_auto` | When present |
| TVDB | `tvdb_id` | Linked text, when present |

### Music Disc

| Field | Source | Notes |
|-------|--------|-------|
| Type | `video_type` / `disctype` | "Music" |
| Disc Type | `disctype` | "Music CD" |
| Titles | `no_of_titles` | Track count |
| Label | `label` | Monospace |
| Device | `devpath` | |
| Source | `source_type` | |
| Artist | `artist` or `artist_auto` | When present |
| Album | `album` or `album_auto` | When present |
| Started | `start_time` | |
| Finished | `stop_time` | Completed only |
| Duration | `job_length` | Completed only |
| Elapsed | computed | Active only |
| Output | `path` | When present |

**Not shown for music:** Title Mode, CRC, IMDb, TVDB, Season, Disc #

### Folder Import

Same as video disc fields but:
- Source shows "Folder"
- Source Path field added (shows `source_path`, monospace)
- Device may or may not be present

### Waiting / Unidentified

Whatever fields are populated. Typically a minimal set:
- Type (may be "unknown"), Disc Type, Titles, Label, Device, Source, Started

## Grid Column Logic

- Always 4 columns
- Field count varies by job type and state (7-16 fields)
- Rows = ceil(field_count / 4)
- Empty cells on the last row rendered with borders but no content
- All cells get `border-bottom` and interior cells get `border-right` (rightmost column borders handled by the container edge)

## Breadcrumb

Replace "Back to Dashboard" link with breadcrumb:

```
Dashboard > [Job Title]
```

"Dashboard" links to `/`, job title is plain text (current page).

## Styling Tokens

All styling follows existing patterns from the settings page:

- Container: `rounded-lg border border-primary/20 bg-surface dark:border-primary/20 dark:bg-surface-dark`
- Grid borders: `border-primary/15` (or `border-primary/20` to match container)
- Labels: `text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400`
- Values: `text-sm font-medium text-gray-900 dark:text-white`
- Monospace values: `font-mono text-xs`
- Select inputs: settings page `inputClass` pattern (`rounded-md border border-primary/25 bg-primary/5 px-3 py-2 text-sm`)
- Action buttons: pill style (`rounded-full px-3 py-1.5 text-xs font-medium`)
- Panel toggle bar: `bg-surface/50` background, `border-t border-primary/15`

## Scope

This spec covers only the header section of the job detail page (everything above the tracks table and inline log feeds). The tracks table, error banners, auto-vs-manual diff banner, and inline log feeds remain unchanged.

## Responsive Behavior

- On mobile (< md): poster stacks above the grid, grid drops to 2 columns
- Panel toggle bar wraps or scrolls horizontally on small screens
- Action buttons in title bar wrap below the title/badges on narrow screens
