import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';
import { fetchThemes, fetchTheme } from '$lib/api/themes';

export interface ColorScheme {
	id: string;
	label: string;
	/** Hex color for the swatch preview */
	swatch: string;
	/** Lock the theme to light or dark mode when this scheme is active */
	mode?: 'light' | 'dark';
	tokens: Record<string, string>;
	/** Custom CSS injected at runtime */
	css?: string;
	/** Theme author */
	author?: string;
	/** Theme description */
	description?: string;
	/** Whether this is a built-in theme */
	builtin?: boolean;
}

/**
 * Color tokens applied as CSS custom properties on :root.
 * Tailwind v4 references them via `color-mix()` for opacity modifiers.
 * These are the compiled-in fallbacks that work even when the backend is down.
 */
export const COLOR_SCHEMES: ColorScheme[] = [
	{
		id: 'blue',
		label: 'Default',
		swatch: '#3b82f6',
		tokens: {
			'--color-primary': 'rgb(37, 99, 235)',          // blue-600
			'--color-primary-hover': 'rgb(29, 78, 216)',    // blue-700
			'--color-primary-dark': 'rgb(30, 64, 175)',     // blue-800
			'--color-primary-light-bg': 'rgb(219, 234, 254)', // blue-100
			'--color-primary-light-bg-dark': 'rgb(30, 58, 138)', // blue-900
			'--color-primary-text': 'rgb(29, 78, 216)',     // blue-700
			'--color-primary-text-dark': 'rgb(96, 165, 250)', // blue-400
			'--color-primary-border': 'rgb(59, 130, 246)',  // blue-500
			'--color-on-primary': 'rgb(255, 255, 255)',     // white
			'--color-page': 'rgb(232, 240, 255)',           // blue-tinted light
			'--color-page-dark': 'rgb(13, 16, 28)',         // dark navy
			'--color-surface': 'rgb(241, 247, 255)',        // blue-tinted surface
			'--color-surface-dark': 'rgb(22, 28, 45)',      // blue-tinted dark
			'--radius': '0.5rem'
		}
	},
	{
		id: 'ocean',
		label: 'Ocean',
		swatch: '#14b8a6',
		tokens: {
			'--color-primary': 'rgb(13, 148, 136)',         // teal-600
			'--color-primary-hover': 'rgb(15, 118, 110)',   // teal-700
			'--color-primary-dark': 'rgb(17, 94, 89)',      // teal-800
			'--color-primary-light-bg': 'rgb(204, 251, 241)', // teal-100
			'--color-primary-light-bg-dark': 'rgb(19, 78, 74)', // teal-900
			'--color-primary-text': 'rgb(15, 118, 110)',    // teal-700
			'--color-primary-text-dark': 'rgb(94, 234, 212)', // teal-400
			'--color-primary-border': 'rgb(20, 184, 166)',  // teal-500
			'--color-on-primary': 'rgb(255, 255, 255)',     // white
			'--color-page': 'rgb(228, 248, 245)',           // teal-tinted light
			'--color-page-dark': 'rgb(12, 19, 20)',         // dark teal
			'--color-surface': 'rgb(238, 252, 249)',        // teal-tinted surface
			'--color-surface-dark': 'rgb(9, 69, 79)',        // teal-tinted dark
			'--radius': '0.5rem'
		}
	},
	{
		id: 'forest',
		label: 'Forest',
		swatch: '#10b981',
		tokens: {
			'--color-primary': 'rgb(5, 150, 105)',          // emerald-600
			'--color-primary-hover': 'rgb(4, 120, 87)',     // emerald-700
			'--color-primary-dark': 'rgb(6, 95, 70)',       // emerald-800
			'--color-primary-light-bg': 'rgb(209, 250, 229)', // emerald-100
			'--color-primary-light-bg-dark': 'rgb(6, 78, 59)', // emerald-900
			'--color-primary-text': 'rgb(4, 120, 87)',      // emerald-700
			'--color-primary-text-dark': 'rgb(110, 231, 183)', // emerald-400
			'--color-primary-border': 'rgb(16, 185, 129)',  // emerald-500
			'--color-on-primary': 'rgb(255, 255, 255)',     // white
			'--color-page': 'rgb(228, 248, 238)',           // emerald-tinted light
			'--color-page-dark': 'rgb(12, 19, 15)',         // dark forest
			'--color-surface': 'rgb(237, 252, 244)',        // emerald-tinted surface
			'--color-surface-dark': 'rgb(21, 54, 37)',       // emerald-tinted dark
			'--radius': '0.5rem'
		}
	},
	{
		id: 'sunset',
		label: 'Red Alert',
		swatch: '#ef4444',
		tokens: {
			'--color-primary': 'rgb(220, 38, 38)',          // red-600
			'--color-primary-hover': 'rgb(185, 28, 28)',    // red-700
			'--color-primary-dark': 'rgb(153, 27, 27)',     // red-800
			'--color-primary-light-bg': 'rgb(254, 226, 226)', // red-100
			'--color-primary-light-bg-dark': 'rgb(127, 29, 29)', // red-900
			'--color-primary-text': 'rgb(185, 28, 28)',     // red-700
			'--color-primary-text-dark': 'rgb(248, 113, 113)', // red-400
			'--color-primary-border': 'rgb(239, 68, 68)',   // red-500
			'--color-on-primary': 'rgb(255, 255, 255)',     // white
			'--color-page': 'rgb(255, 235, 235)',           // red-tinted light
			'--color-page-dark': 'rgb(38, 0, 0)',           // dark red
			'--color-surface': 'rgb(255, 243, 243)',        // red-tinted surface
			'--color-surface-dark': 'rgb(68, 1, 0)',         // red alert dark
			'--radius': '0.5rem'
		}
	},
	{
		id: 'rose',
		label: 'Rose',
		swatch: '#ec4899',
		tokens: {
			'--color-primary': 'rgb(219, 39, 119)',         // pink-600
			'--color-primary-hover': 'rgb(190, 24, 93)',    // pink-700
			'--color-primary-dark': 'rgb(157, 23, 77)',     // pink-800
			'--color-primary-light-bg': 'rgb(252, 231, 243)', // pink-100
			'--color-primary-light-bg-dark': 'rgb(131, 24, 67)', // pink-900
			'--color-primary-text': 'rgb(190, 24, 93)',     // pink-700
			'--color-primary-text-dark': 'rgb(244, 114, 182)', // pink-400
			'--color-primary-border': 'rgb(236, 72, 153)',  // pink-500
			'--color-on-primary': 'rgb(255, 255, 255)',     // white
			'--color-page': 'rgb(252, 232, 243)',           // pink-tinted light
			'--color-page-dark': 'rgb(47, 0, 23)',          // dark rose
			'--color-surface': 'rgb(253, 242, 249)',        // pink-tinted surface
			'--color-surface-dark': 'rgb(132, 28, 81)',      // rose dark
			'--radius': '0.5rem'
		}
	},
	{
		id: 'violet',
		label: 'Grape',
		swatch: '#a855f7',
		tokens: {
			'--color-primary': 'rgb(147, 51, 234)',         // purple-600
			'--color-primary-hover': 'rgb(126, 34, 206)',   // purple-700
			'--color-primary-dark': 'rgb(107, 33, 168)',    // purple-800
			'--color-primary-light-bg': 'rgb(237, 226, 255)', // purple-100
			'--color-primary-light-bg-dark': 'rgb(76, 29, 149)', // purple-900
			'--color-primary-text': 'rgb(126, 34, 206)',    // purple-700
			'--color-primary-text-dark': 'rgb(192, 132, 252)', // purple-400
			'--color-primary-border': 'rgb(168, 85, 247)',  // purple-500
			'--color-on-primary': 'rgb(255, 255, 255)',     // white
			'--color-page': 'rgb(243, 235, 255)',           // purple-tinted light
			'--color-page-dark': 'rgb(16, 13, 26)',         // dark violet
			'--color-surface': 'rgb(247, 243, 255)',        // purple-tinted surface
			'--color-surface-dark': 'rgb(48, 22, 92)',       // grape dark
			'--radius': '0.5rem'
		}
	},
	{
		id: 'glass',
		label: 'Glass',
		swatch: '#818cf8',
		mode: 'dark',
		tokens: {
			'--color-primary': 'rgb(129, 140, 248)',        // indigo-400
			'--color-primary-hover': 'rgb(99, 102, 241)',   // indigo-500
			'--color-primary-dark': 'rgb(67, 56, 202)',     // indigo-700
			'--color-primary-light-bg': 'rgb(49, 46, 129)', // indigo-900
			'--color-primary-light-bg-dark': 'rgb(49, 46, 129)', // indigo-900
			'--color-primary-text': 'rgb(165, 180, 252)',   // indigo-300
			'--color-primary-text-dark': 'rgb(165, 180, 252)', // indigo-300
			'--color-primary-border': 'rgb(129, 140, 248)', // indigo-400
			'--color-on-primary': 'rgb(255, 255, 255)',     // white
			'--color-page': 'rgb(15, 23, 42)',              // slate-900
			'--color-page-dark': 'rgb(15, 23, 42)',         // slate-900
			'--color-surface': 'rgb(30, 27, 75)',           // indigo-950
			'--color-surface-dark': 'rgb(30, 27, 75)',       // indigo-950
			'--radius': '0.5rem'
		}
	},
	{
		id: 'cinema',
		label: 'Cinema',
		swatch: '#ca8a04',
		mode: 'dark',
		tokens: {
			'--color-primary': 'rgb(212, 175, 55)',          // gold
			'--color-primary-hover': 'rgb(188, 155, 40)',    // darker gold
			'--color-primary-dark': 'rgb(138, 109, 59)',     // muted gold
			'--color-primary-light-bg': 'rgb(30, 25, 10)',   // dark gold tint
			'--color-primary-light-bg-dark': 'rgb(30, 25, 10)', // dark gold tint
			'--color-primary-text': 'rgb(212, 175, 55)',     // gold
			'--color-primary-text-dark': 'rgb(212, 175, 55)', // gold
			'--color-primary-border': 'rgb(138, 109, 59)',   // muted gold
			'--color-on-primary': 'rgb(13, 13, 13)',         // cinema black
			'--color-page': 'rgb(26, 26, 26)',               // dark gray
			'--color-page-dark': 'rgb(26, 26, 26)',          // dark gray
			'--color-surface': 'rgb(13, 13, 13)',            // cinema black
			'--color-surface-dark': 'rgb(13, 13, 13)',        // cinema black
			'--radius': '0.5rem'
		}
	},
	{
		id: 'gaming',
		label: 'Gaming',
		swatch: '#d946ef',
		mode: 'dark',
		tokens: {
			'--color-primary': 'rgb(0, 135, 164)',            // darker neon blue (headers)
			'--color-primary-hover': 'rgb(188, 19, 254)',     // neon purple
			'--color-primary-dark': 'rgb(27, 27, 47)',        // border dark
			'--color-primary-light-bg': 'rgb(0, 210, 255)',   // blue (unused in dark)
			'--color-primary-light-bg-dark': 'rgb(0, 30, 50)', // dark blue tint
			'--color-primary-text': 'rgb(0, 210, 255)',       // neon blue
			'--color-primary-text-dark': 'rgb(0, 210, 255)',  // neon blue
			'--color-primary-border': 'rgb(0, 210, 255)',     // neon blue
			'--color-on-primary': 'rgb(255, 255, 255)',       // white
			'--color-page': 'rgb(5, 5, 10)',                  // bg dark
			'--color-page-dark': 'rgb(5, 5, 10)',             // bg dark
			'--color-surface': 'rgb(12, 12, 18)',             // surface
			'--color-surface-dark': 'rgb(12, 12, 18)',         // surface
			'--radius': '0px'
		}
	},
	{
		id: 'royale',
		label: 'Royale',
		swatch: '#facc15',
		mode: 'dark',
		tokens: {
			'--color-primary': 'rgb(0, 123, 255)',            // fortnite blue
			'--color-primary-hover': 'rgb(248, 251, 17)',     // fortnite yellow
			'--color-primary-dark': 'rgb(17, 42, 94)',        // deep blue border
			'--color-primary-light-bg': 'rgb(11, 26, 61)',    // item bg
			'--color-primary-light-bg-dark': 'rgb(11, 26, 61)', // item bg
			'--color-primary-text': 'rgb(248, 251, 17)',      // yellow
			'--color-primary-text-dark': 'rgb(248, 251, 17)', // yellow
			'--color-primary-border': 'rgb(17, 42, 94)',      // deep blue
			'--color-on-primary': 'rgb(255, 255, 255)',       // white
			'--color-page': 'rgb(5, 5, 5)',                   // near-black
			'--color-page-dark': 'rgb(5, 5, 5)',              // near-black
			'--color-surface': 'rgb(2, 11, 36)',              // dark blue
			'--color-surface-dark': 'rgb(2, 11, 36)',          // dark blue
			'--radius': '0.5rem'
		}
	},
	{
		id: 'lcars',
		label: 'LCARS',
		swatch: '#fb923c',
		mode: 'dark',
		tokens: {
			'--color-primary': 'rgb(255, 153, 0)',            // lcars orange
			'--color-primary-hover': 'rgb(255, 204, 51)',     // lcars yellow
			'--color-primary-dark': 'rgb(40, 30, 0)',         // dark orange
			'--color-primary-light-bg': 'rgb(153, 153, 255)', // lcars blue
			'--color-primary-light-bg-dark': 'rgb(30, 30, 60)', // dark blue
			'--color-primary-text': 'rgb(255, 204, 51)',      // yellow
			'--color-primary-text-dark': 'rgb(255, 153, 0)',  // orange
			'--color-primary-border': 'rgb(255, 153, 0)',     // orange
			'--color-on-primary': 'rgb(0, 0, 0)',             // black
			'--color-page': 'rgb(0, 0, 0)',                   // pure black
			'--color-page-dark': 'rgb(0, 0, 0)',
			'--color-surface': 'rgb(0, 0, 0)',                // pure black
			'--color-surface-dark': 'rgb(0, 0, 0)',
			'--radius': '20px'
		}
	},
	{
		id: 'tactical',
		label: 'Tactical',
		swatch: '#2dd4bf',
		mode: 'dark',
		tokens: {
			'--color-primary': 'rgb(0, 120, 100)',            // darker teal (readable headers)
			'--color-primary-hover': 'rgb(80, 200, 175)',     // dimmer teal
			'--color-primary-dark': 'rgb(10, 25, 47)',        // navy
			'--color-primary-light-bg': 'rgb(10, 25, 47)',    // navy
			'--color-primary-light-bg-dark': 'rgb(10, 25, 47)',
			'--color-primary-text': 'rgb(100, 255, 218)',     // teal
			'--color-primary-text-dark': 'rgb(100, 255, 218)',
			'--color-primary-border': 'rgb(100, 255, 218)',   // teal
			'--color-on-primary': 'rgb(255, 255, 255)',       // white
			'--color-page': 'rgb(2, 6, 23)',                  // deep navy
			'--color-page-dark': 'rgb(2, 6, 23)',
			'--color-surface': 'rgb(10, 25, 47)',             // navy
			'--color-surface-dark': 'rgb(10, 25, 47)',
			'--radius': '0px'
		}
	},
	{
		id: 'craft',
		label: 'Craft',
		swatch: '#22c55e',
		mode: 'dark',
		tokens: {
			'--color-primary': 'rgb(30, 130, 30)',            // darker MC green (readable headers)
			'--color-primary-hover': 'rgb(128, 128, 255)',    // MC hover blue
			'--color-primary-dark': 'rgb(34, 34, 34)',        // dark stone
			'--color-primary-light-bg': 'rgb(74, 74, 74)',    // pressed button
			'--color-primary-light-bg-dark': 'rgb(74, 74, 74)',
			'--color-primary-text': 'rgb(56, 255, 56)',       // MC green
			'--color-primary-text-dark': 'rgb(56, 255, 56)',
			'--color-primary-border': 'rgb(0, 0, 0)',         // black
			'--color-on-primary': 'rgb(255, 255, 255)',       // white
			'--color-page': 'rgb(30, 30, 30)',                // dark bg
			'--color-page-dark': 'rgb(30, 30, 30)',
			'--color-surface': 'rgb(49, 49, 49)',             // stone
			'--color-surface-dark': 'rgb(49, 49, 49)',
			'--radius': '0px'
		}
	},
	{
		id: 'terminal',
		label: 'Terminal',
		swatch: '#4ade80',
		mode: 'dark',
		tokens: {
			'--color-primary': 'rgb(57, 255, 20)',          // terminal green
			'--color-primary-hover': 'rgb(45, 200, 16)',    // dimmer green
			'--color-primary-dark': 'rgb(10, 26, 5)',       // dark green
			'--color-primary-light-bg': 'rgb(10, 26, 5)',   // dark green (light bg unused)
			'--color-primary-light-bg-dark': 'rgb(10, 26, 5)', // dark green
			'--color-primary-text': 'rgb(57, 255, 20)',     // terminal green
			'--color-primary-text-dark': 'rgb(57, 255, 20)', // terminal green
			'--color-primary-border': 'rgb(57, 255, 20)',   // terminal green
			'--color-on-primary': 'rgb(5, 5, 5)',           // near-black
			'--color-page': 'rgb(5, 5, 5)',                 // CRT black
			'--color-page-dark': 'rgb(5, 5, 5)',            // CRT black
			'--color-surface': 'rgb(8, 8, 8)',              // barely-off-black
			'--color-surface-dark': 'rgb(8, 8, 8)',          // barely-off-black
			'--radius': '0px'
		}
	},
	{
		id: 'blockbuster',
		label: 'Blockbuster Video',
		swatch: '#2563eb',
		mode: 'dark',
		tokens: {
			'--color-primary': 'rgb(255, 235, 0)',            // vibrant yellow
			'--color-primary-hover': 'rgb(215, 200, 0)',      // slightly darker yellow
			'--color-primary-dark': 'rgb(180, 160, 0)',       // deep gold for borders
			'--color-primary-light-bg': 'rgb(0, 51, 153)',    // rich blue
			'--color-primary-light-bg-dark': 'rgb(0, 31, 103)', // deep blue
			'--color-primary-text': 'rgb(255, 235, 0)',       // yellow
			'--color-primary-text-dark': 'rgb(255, 235, 0)',  // yellow
			'--color-primary-border': 'rgb(255, 235, 0)',     // yellow
			'--color-on-primary': 'rgb(0, 0, 0)',             // black on yellow
			'--color-page': 'rgb(0, 41, 123)',                // darker blue page
			'--color-page-dark': 'rgb(0, 41, 123)',
			'--color-surface': 'rgb(0, 51, 153)',             // standard blue surface
			'--color-surface-dark': 'rgb(0, 51, 153)',
			'--radius': '0px'
		}
	},
	{
		id: 'hollywood-video-v2',
		label: 'Hollywood Video',
		swatch: '#4c1d95',
		mode: 'dark',
		tokens: {
			'--color-primary': 'rgb(217, 11, 28)',             // #D90B1C Red
			'--color-primary-hover': 'rgb(170, 8, 22)',        // darker red
			'--color-primary-dark': 'rgb(110, 5, 14)',         // deep red
			'--color-primary-light-bg': 'rgb(35, 22, 64)',     // #231640 Purple
			'--color-primary-light-bg-dark': 'rgb(22, 14, 38)', // #160E26 Deep Purple
			'--color-primary-text': 'rgb(242, 183, 5)',        // #F2B705 Gold
			'--color-primary-text-dark': 'rgb(242, 183, 5)',   // #F2B705 Gold
			'--color-primary-border': 'rgb(35, 22, 64)',       // #231640 Purple
			'--color-on-primary': 'rgb(255, 255, 255)',        // White on Red
			'--color-page': 'rgb(22, 14, 38)',                 // #160E26 Deep Purple
			'--color-page-dark': 'rgb(22, 14, 38)',            // #160E26 Deep Purple
			'--color-surface': 'rgb(35, 22, 64)',              // #231640 Purple
			'--color-surface-dark': 'rgb(35, 22, 64)',          // #231640 Purple
			'--radius': '0.5rem'
		}
	}
];

const DEFAULT_SCHEME = COLOR_SCHEMES[0];

/** Writable store of all available schemes (built-in + API-loaded) */
export const allSchemes = writable<ColorScheme[]>([...COLOR_SCHEMES]);

/** Cache of full theme data (with CSS) fetched from the API */
const cssCache = new Map<string, string>();

function getInitialScheme(): string {
	if (!browser) return DEFAULT_SCHEME.id;
	return localStorage.getItem('colorScheme') ?? DEFAULT_SCHEME.id;
}

function applyScheme(id: string) {
	if (!browser) return;
	const schemes = get(allSchemes);
	const scheme = schemes.find((s) => s.id === id) ?? DEFAULT_SCHEME;
	const root = document.documentElement;
	for (const [prop, value] of Object.entries(scheme.tokens)) {
		root.style.setProperty(prop, value);
	}

	root.dataset.scheme = scheme.id;


	// Inject theme CSS into a managed <style> element
	injectThemeCss(scheme);

	if (scheme.mode === 'dark') {
		root.classList.add('dark');
	} else if (scheme.mode === 'light') {
		root.classList.remove('dark');
	} else {
		// Restore the user's saved theme preference
		const saved = localStorage.getItem('theme');
		const prefersDark = saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches);
		root.classList.toggle('dark', prefersDark);
	}
}

function injectThemeCss(scheme: ColorScheme) {
	const styleId = 'arm-theme-css';
	let el = document.getElementById(styleId) as HTMLStyleElement | null;

	// Get CSS from scheme object or cache
	const css = scheme.css ?? cssCache.get(scheme.id) ?? '';

	if (!css) {
		// No custom CSS — remove any existing injected style
		el?.remove();
		return;
	}

	if (!el) {
		el = document.createElement('style');
		el.id = styleId;
		document.head.appendChild(el);
	}
	el.textContent = css;
}

export const colorScheme = writable<string>(getInitialScheme());

/** True when the active color scheme locks the mode (light or dark) */
export const schemeLocksMode = derived(colorScheme, (id) => {
	const schemes = get(allSchemes);
	const scheme = schemes.find((s) => s.id === id);
	return scheme?.mode != null;
});

/**
 * Load themes from the API, merging with built-in fallbacks.
 * Call this on app startup. Falls back silently if backend is unreachable.
 */
export async function loadThemesFromApi(): Promise<void> {
	try {
		const apiThemes = await fetchThemes();
		if (!apiThemes?.length) return;

		// Build merged list: API themes take precedence, keep built-in order
		const merged = new Map<string, ColorScheme>();

		// Start with built-in fallbacks
		for (const s of COLOR_SCHEMES) {
			merged.set(s.id, { ...s, builtin: true });
		}

		// Overlay API themes (merge tokens so built-in defaults like --radius aren't lost)
		for (const t of apiThemes) {
			const existing = merged.get(t.id);
			merged.set(t.id, {
				id: t.id,
				label: t.label,
				swatch: t.swatch,
				mode: t.mode,
				tokens: { ...(existing?.tokens ?? {}), ...t.tokens },
				author: t.author,
				description: t.description,
				builtin: t.builtin ?? false
			});
		}

		allSchemes.set(Array.from(merged.values()));

		// Fetch full CSS for the currently active scheme
		const currentId = get(colorScheme);
		await loadThemeCss(currentId);
	} catch {
		// Backend unreachable — built-in themes are already loaded
	}
}

/**
 * Fetch and cache full theme CSS from the API, then re-apply the scheme.
 */
export async function loadThemeCss(id: string): Promise<void> {
	if (cssCache.has(id)) {
		// Already cached — update the scheme object and re-apply
		const schemes = get(allSchemes);
		const scheme = schemes.find((s) => s.id === id);
		if (scheme) {
			scheme.css = cssCache.get(id);
			applyScheme(id);
		}
		return;
	}

	try {
		const full = await fetchTheme(id);
		if (full?.css) {
			cssCache.set(id, full.css);
			// Update the scheme in the store
			allSchemes.update((schemes) =>
				schemes.map((s) => (s.id === id ? { ...s, css: full.css } : s))
			);
		}
		applyScheme(id);
	} catch {
		// Fetch failed — apply without CSS
		applyScheme(id);
	}
}

if (browser) {
	colorScheme.subscribe(async (id) => {
		localStorage.setItem('colorScheme', id);
		// Apply tokens synchronously so there's no flash of default-blue
		// between page load and API response.  loadThemeCss will re-apply
		// with custom CSS once the fetch completes.
		applyScheme(id);
		await loadThemeCss(id);
	});
}
