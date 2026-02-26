import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export interface ColorScheme {
	id: string;
	label: string;
	/** Tailwind color name for the swatch preview */
	swatch: string;
	/** Force dark mode when this scheme is active */
	forceDark?: boolean;
	tokens: Record<string, string>;
}

/**
 * Color tokens applied as CSS custom properties on :root.
 * Tailwind v4 references them via `color-mix()` for opacity modifiers.
 */
export const COLOR_SCHEMES: ColorScheme[] = [
	{
		id: 'blue',
		label: 'Default',
		swatch: 'bg-blue-500',
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
			'--color-surface-dark': 'rgb(22, 28, 45)'      // blue-tinted dark
		}
	},
	{
		id: 'ocean',
		label: 'Ocean',
		swatch: 'bg-teal-500',
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
			'--color-surface-dark': 'rgb(9, 69, 79)'        // teal-tinted dark
		}
	},
	{
		id: 'forest',
		label: 'Forest',
		swatch: 'bg-emerald-500',
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
			'--color-surface-dark': 'rgb(21, 54, 37)'       // emerald-tinted dark
		}
	},
	{
		id: 'sunset',
		label: 'Red Alert',
		swatch: 'bg-red-500',
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
			'--color-surface-dark': 'rgb(68, 1, 0)'         // red alert dark
		}
	},
	{
		id: 'rose',
		label: 'Rose',
		swatch: 'bg-pink-500',
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
			'--color-surface-dark': 'rgb(132, 28, 81)'      // rose dark
		}
	},
	{
		id: 'violet',
		label: 'Grape',
		swatch: 'bg-purple-500',
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
			'--color-surface-dark': 'rgb(48, 22, 92)'       // grape dark
		}
	},
	{
		id: 'glass',
		label: 'Glass',
		swatch: 'bg-indigo-400',
		forceDark: true,
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
			'--color-surface-dark': 'rgb(30, 27, 75)'       // indigo-950
		}
	},
	{
		id: 'cinema',
		label: 'Cinema',
		swatch: 'bg-yellow-600',
		forceDark: true,
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
			'--color-surface-dark': 'rgb(13, 13, 13)'        // cinema black
		}
	},
	{
		id: 'gaming',
		label: 'Gaming',
		swatch: 'bg-fuchsia-500',
		forceDark: true,
		tokens: {
			'--color-primary': 'rgb(0, 210, 255)',            // neon blue
			'--color-primary-hover': 'rgb(188, 19, 254)',     // neon purple
			'--color-primary-dark': 'rgb(27, 27, 47)',        // border dark
			'--color-primary-light-bg': 'rgb(0, 210, 255)',   // blue (unused in dark)
			'--color-primary-light-bg-dark': 'rgb(0, 30, 50)', // dark blue tint
			'--color-primary-text': 'rgb(0, 210, 255)',       // neon blue
			'--color-primary-text-dark': 'rgb(0, 210, 255)',  // neon blue
			'--color-primary-border': 'rgb(0, 210, 255)',     // neon blue
			'--color-on-primary': 'rgb(5, 5, 10)',            // bg dark
			'--color-page': 'rgb(5, 5, 10)',                  // bg dark
			'--color-page-dark': 'rgb(5, 5, 10)',             // bg dark
			'--color-surface': 'rgb(12, 12, 18)',             // surface
			'--color-surface-dark': 'rgb(12, 12, 18)'         // surface
		}
	},
	{
		id: 'royale',
		label: 'Royale',
		swatch: 'bg-yellow-400',
		forceDark: true,
		tokens: {
			'--color-primary': 'rgb(0, 123, 255)',            // fortnite blue
			'--color-primary-hover': 'rgb(248, 251, 17)',     // fortnite yellow
			'--color-primary-dark': 'rgb(17, 42, 94)',        // deep blue border
			'--color-primary-light-bg': 'rgb(11, 26, 61)',    // item bg
			'--color-primary-light-bg-dark': 'rgb(11, 26, 61)', // item bg
			'--color-primary-text': 'rgb(248, 251, 17)',      // yellow
			'--color-primary-text-dark': 'rgb(248, 251, 17)', // yellow
			'--color-primary-border': 'rgb(17, 42, 94)',      // deep blue
			'--color-on-primary': 'rgb(0, 0, 0)',             // black
			'--color-page': 'rgb(5, 5, 5)',                   // near-black
			'--color-page-dark': 'rgb(5, 5, 5)',              // near-black
			'--color-surface': 'rgb(2, 11, 36)',              // dark blue
			'--color-surface-dark': 'rgb(2, 11, 36)'          // dark blue
		}
	},
	{
		id: 'lcars',
		label: 'LCARS',
		swatch: 'bg-orange-400',
		forceDark: true,
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
			'--color-surface-dark': 'rgb(0, 0, 0)'
		}
	},
	{
		id: 'tactical',
		label: 'Tactical',
		swatch: 'bg-teal-400',
		forceDark: true,
		tokens: {
			'--color-primary': 'rgb(100, 255, 218)',          // tactical teal
			'--color-primary-hover': 'rgb(80, 200, 175)',     // dimmer teal
			'--color-primary-dark': 'rgb(10, 25, 47)',        // navy
			'--color-primary-light-bg': 'rgb(10, 25, 47)',    // navy
			'--color-primary-light-bg-dark': 'rgb(10, 25, 47)',
			'--color-primary-text': 'rgb(100, 255, 218)',     // teal
			'--color-primary-text-dark': 'rgb(100, 255, 218)',
			'--color-primary-border': 'rgb(100, 255, 218)',   // teal
			'--color-on-primary': 'rgb(2, 6, 23)',            // deep navy
			'--color-page': 'rgb(2, 6, 23)',                  // deep navy
			'--color-page-dark': 'rgb(2, 6, 23)',
			'--color-surface': 'rgb(10, 25, 47)',             // navy
			'--color-surface-dark': 'rgb(10, 25, 47)'
		}
	},
	{
		id: 'craft',
		label: 'Craft',
		swatch: 'bg-green-500',
		forceDark: true,
		tokens: {
			'--color-primary': 'rgb(56, 255, 56)',            // MC green
			'--color-primary-hover': 'rgb(128, 128, 255)',    // MC hover blue
			'--color-primary-dark': 'rgb(34, 34, 34)',        // dark stone
			'--color-primary-light-bg': 'rgb(74, 74, 74)',    // pressed button
			'--color-primary-light-bg-dark': 'rgb(74, 74, 74)',
			'--color-primary-text': 'rgb(56, 255, 56)',       // MC green
			'--color-primary-text-dark': 'rgb(56, 255, 56)',
			'--color-primary-border': 'rgb(0, 0, 0)',         // black
			'--color-on-primary': 'rgb(224, 224, 224)',       // light gray
			'--color-page': 'rgb(30, 30, 30)',                // dark bg
			'--color-page-dark': 'rgb(30, 30, 30)',
			'--color-surface': 'rgb(49, 49, 49)',             // stone
			'--color-surface-dark': 'rgb(49, 49, 49)'
		}
	},
	{
		id: 'terminal',
		label: 'Terminal',
		swatch: 'bg-green-400',
		forceDark: true,
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
			'--color-surface-dark': 'rgb(8, 8, 8)'          // barely-off-black
		}
	}
];

const DEFAULT_SCHEME = COLOR_SCHEMES[0];

function getInitialScheme(): string {
	if (!browser) return DEFAULT_SCHEME.id;
	return localStorage.getItem('colorScheme') ?? DEFAULT_SCHEME.id;
}

function applyScheme(id: string) {
	if (!browser) return;
	const scheme = COLOR_SCHEMES.find((s) => s.id === id) ?? DEFAULT_SCHEME;
	const root = document.documentElement;
	for (const [prop, value] of Object.entries(scheme.tokens)) {
		root.style.setProperty(prop, value);
	}
	root.setAttribute('data-scheme', scheme.id);
	if (scheme.forceDark) {
		root.classList.add('dark');
	}
}

export const colorScheme = writable<string>(getInitialScheme());

if (browser) {
	colorScheme.subscribe((id) => {
		localStorage.setItem('colorScheme', id);
		applyScheme(id);
	});
}
