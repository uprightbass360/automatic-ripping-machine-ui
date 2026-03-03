# ARM UI Theme Generation Template

Generate new color themes for the ARM (Automatic Ripping Machine) dashboard UI. The UI is a SvelteKit app using Tailwind CSS v4 with a CSS custom property-based theming system.

## How Themes Work

Each theme is a TypeScript object in `colorScheme.ts` with 13 CSS custom properties applied to `:root`. Dark-only themes set `forceDark: true`. Themes may optionally include custom CSS rules in `app.css` using the `[data-scheme="<id>"]` selector.

## Required Output

For each theme, provide **two blocks**:

### Block 1: TypeScript object (goes in `colorScheme.ts`)

```typescript
{
    id: '<unique_kebab_id>',       // URL-safe, lowercase, no spaces
    label: '<Display Name>',       // Short (1-2 words) shown under swatch
    swatch: '<tailwind_bg_class>', // e.g. 'bg-amber-500' — used for the preview circle
    forceDark: false,              // true = locks dark mode on, no light mode toggle
    tokens: {
        // === Primary accent color (buttons, active states, links) ===
        '--color-primary':            'rgb(R, G, B)',  // Main accent — 500-600 range
        '--color-primary-hover':      'rgb(R, G, B)',  // Hovered accent — one shade darker (600-700)
        '--color-primary-dark':       'rgb(R, G, B)',  // Deep accent for borders/outlines (700-800)

        // === Backgrounds with accent tint ===
        '--color-primary-light-bg':      'rgb(R, G, B)',  // Light mode: highlighted row/card bg (100 range)
        '--color-primary-light-bg-dark': 'rgb(R, G, B)',  // Dark mode: highlighted row/card bg (900 range, muted)

        // === Text colored with accent ===
        '--color-primary-text':      'rgb(R, G, B)',  // Light mode: links, headings (700 range)
        '--color-primary-text-dark': 'rgb(R, G, B)',  // Dark mode: links, headings (300-400 range)

        // === Misc ===
        '--color-primary-border':    'rgb(R, G, B)',  // Borders on focused/active elements (500 range)
        '--color-on-primary':        'rgb(R, G, B)',  // Text ON primary bg (white or black for contrast)

        // === Page & surface backgrounds ===
        '--color-page':         'rgb(R, G, B)',  // Light mode: full page bg (very light, accent-tinted)
        '--color-page-dark':    'rgb(R, G, B)',  // Dark mode: full page bg (very dark, accent-tinted)
        '--color-surface':      'rgb(R, G, B)',  // Light mode: card/panel bg (slightly lighter than page)
        '--color-surface-dark': 'rgb(R, G, B)'   // Dark mode: card/panel bg (slightly lighter than page-dark)
    }
}
```

### Block 2 (optional): Custom CSS (goes in `app.css`)

For themes with distinctive visual styles beyond color tokens. Use `[data-scheme="<id>"]` selector prefix on everything.

```css
/* ── <Theme Name> theme ──────────────────────────────────── */

/* Available selectors for customization: */
[data-scheme="<id>"] { }                              /* Root — font-family, etc. */
[data-scheme="<id>"] body { }                         /* Body — gradients, bg images */
[data-scheme="<id>"] aside { }                        /* Sidebar container */
[data-scheme="<id>"] aside nav a { }                  /* Nav links */
[data-scheme="<id>"] aside nav a:hover { }            /* Nav link hover */
[data-scheme="<id>"] aside nav a[data-active="true"] { } /* Active nav link */
[data-scheme="<id>"] aside nav a svg { }              /* Nav icons */
[data-scheme="<id>"] aside [data-logo] img { }        /* Logo image — filters */
[data-scheme="<id>"] aside [data-stats] { }           /* Sidebar stats panel */
[data-scheme="<id>"] aside hr { }                     /* Sidebar dividers */
[data-scheme="<id>"] header { }                       /* Top header bar */
[data-scheme="<id>"] [data-progress-track] { }        /* Progress bar track */
[data-scheme="<id>"] [data-progress-fill] { }         /* Progress bar fill */
[data-scheme="<id>"] aside::before { }                /* Pseudo-element for decorative lines */
```

## Design Guidelines

1. **All RGB values must use `rgb(R, G, B)` format** — not hex, not hsl. The Tailwind v4 `color-mix()` system requires this.
2. **Light/dark dual-mode themes** (`forceDark: false`): Need visually distinct light AND dark variants. Light-mode backgrounds should be very light (pastel), dark-mode backgrounds very dark. Both must have good text contrast.
3. **Dark-only themes** (`forceDark: true`): Set matching values for light/dark token pairs (e.g., `--color-page` = `--color-page-dark`). These are often more stylized/dramatic.
4. **Swatch class** must be a valid Tailwind background color: `bg-{color}-{shade}` where color is one of: slate, gray, zinc, neutral, stone, red, orange, amber, yellow, lime, green, emerald, teal, cyan, sky, blue, indigo, violet, purple, fuchsia, pink, rose. Shade: 50-950.
5. **`--color-on-primary`**: Use `rgb(255, 255, 255)` (white) for dark accents, `rgb(0, 0, 0)` (black) for light/bright accents. This is the text color shown ON TOP of the primary color.
6. **Contrast**: Ensure `--color-primary-text` is readable on white/light-gray (#f9fafb). Ensure `--color-primary-text-dark` is readable on dark backgrounds (#111827).
7. **Custom CSS is optional** — simple color-swap themes don't need it. Use it for font changes, animations, gradients, glow effects, clip-paths, etc.

## Existing Theme IDs (do NOT reuse)

`blue`, `ocean`, `forest`, `sunset`, `rose`, `violet`, `glass`, `cinema`, `gaming`, `royale`, `lcars`, `tactical`, `craft`, `terminal`

## Examples of What Exists

**Simple dual-mode theme (color swap only, no custom CSS):**
```typescript
{
    id: 'forest',
    label: 'Forest',
    swatch: 'bg-emerald-500',
    tokens: {
        '--color-primary': 'rgb(5, 150, 105)',
        '--color-primary-hover': 'rgb(4, 120, 87)',
        '--color-primary-dark': 'rgb(6, 95, 70)',
        '--color-primary-light-bg': 'rgb(209, 250, 229)',
        '--color-primary-light-bg-dark': 'rgb(6, 78, 59)',
        '--color-primary-text': 'rgb(4, 120, 87)',
        '--color-primary-text-dark': 'rgb(110, 231, 183)',
        '--color-primary-border': 'rgb(16, 185, 129)',
        '--color-on-primary': 'rgb(255, 255, 255)',
        '--color-page': 'rgb(228, 248, 238)',
        '--color-page-dark': 'rgb(12, 19, 15)',
        '--color-surface': 'rgb(237, 252, 244)',
        '--color-surface-dark': 'rgb(21, 54, 37)'
    }
}
```

**Stylized dark-only theme (with custom CSS):**
```typescript
{
    id: 'cinema',
    label: 'Cinema',
    swatch: 'bg-yellow-600',
    forceDark: true,
    tokens: {
        '--color-primary': 'rgb(212, 175, 55)',
        '--color-primary-hover': 'rgb(188, 155, 40)',
        '--color-primary-dark': 'rgb(138, 109, 59)',
        '--color-primary-light-bg': 'rgb(30, 25, 10)',
        '--color-primary-light-bg-dark': 'rgb(30, 25, 10)',
        '--color-primary-text': 'rgb(212, 175, 55)',
        '--color-primary-text-dark': 'rgb(212, 175, 55)',
        '--color-primary-border': 'rgb(138, 109, 59)',
        '--color-on-primary': 'rgb(13, 13, 13)',
        '--color-page': 'rgb(26, 26, 26)',
        '--color-page-dark': 'rgb(26, 26, 26)',
        '--color-surface': 'rgb(13, 13, 13)',
        '--color-surface-dark': 'rgb(13, 13, 13)'
    }
}
```
```css
[data-scheme="cinema"] {
    font-family: 'Garamond', 'Times New Roman', Georgia, serif;
}
[data-scheme="cinema"] aside {
    border-color: #8a6d3b !important;
}
[data-scheme="cinema"] aside nav a {
    text-transform: uppercase;
    letter-spacing: 0.15em;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 0.75rem;
    border-radius: 0;
    border-left: 2px solid transparent;
}
[data-scheme="cinema"] aside nav a:hover {
    color: #d4af37 !important;
    background: linear-gradient(90deg, rgba(212, 175, 55, 0.05), transparent) !important;
}
[data-scheme="cinema"] aside nav a[data-active="true"] {
    color: #d4af37 !important;
    border-left: 2px solid #d4af37;
    background: transparent !important;
}
[data-scheme="cinema"] aside nav a svg { display: none; }
[data-scheme="cinema"] aside [data-logo] img {
    filter: sepia(1) saturate(2) brightness(0.9) hue-rotate(5deg);
}
[data-scheme="cinema"] aside hr { border-color: #8a6d3b; }
[data-scheme="cinema"] aside [data-stats] {
    background: linear-gradient(to top, #000, transparent);
    border-color: transparent;
}
[data-scheme="cinema"] [data-progress-track] {
    background: #222 !important;
    height: 2px !important;
    border-radius: 0 !important;
}
[data-scheme="cinema"] [data-progress-fill] {
    background: #d4af37 !important;
    box-shadow: 0 0 8px #d4af37;
    border-radius: 0 !important;
}
[data-scheme="cinema"] header { border-color: #8a6d3b !important; }
```

