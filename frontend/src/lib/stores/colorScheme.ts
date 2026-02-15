import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export interface ColorScheme {
	id: string;
	label: string;
	/** Tailwind color name for the swatch preview */
	swatch: string;
	tokens: Record<string, string>;
}

/**
 * RGB triplet tokens applied as CSS custom properties on :root.
 * Tailwind references them via `rgb(var(--color-primary) / <alpha>)`.
 */
export const COLOR_SCHEMES: ColorScheme[] = [
	{
		id: 'blue',
		label: 'Default',
		swatch: 'bg-blue-500',
		tokens: {
			'--color-primary': '37 99 235',          // blue-600
			'--color-primary-hover': '29 78 216',    // blue-700
			'--color-primary-dark': '30 64 175',     // blue-800
			'--color-primary-light-bg': '219 234 254', // blue-100
			'--color-primary-light-bg-dark': '30 58 138', // blue-900
			'--color-primary-text': '29 78 216',     // blue-700
			'--color-primary-text-dark': '96 165 250', // blue-400
			'--color-primary-border': '59 130 246',  // blue-500
			'--color-on-primary': '255 255 255',     // white
			'--color-page-bg': '232 240 255',        // blue-tinted light
			'--color-page-bg-dark': '13 16 28',      // dark navy
			'--color-surface': '241 247 255',        // blue-tinted surface
			'--color-surface-dark': '22 28 45'       // blue-tinted dark
		}
	},
	{
		id: 'ocean',
		label: 'Ocean',
		swatch: 'bg-teal-500',
		tokens: {
			'--color-primary': '13 148 136',         // teal-600
			'--color-primary-hover': '15 118 110',   // teal-700
			'--color-primary-dark': '17 94 89',      // teal-800
			'--color-primary-light-bg': '204 251 241', // teal-100
			'--color-primary-light-bg-dark': '19 78 74', // teal-900
			'--color-primary-text': '15 118 110',    // teal-700
			'--color-primary-text-dark': '94 234 212', // teal-400
			'--color-primary-border': '20 184 166',  // teal-500
			'--color-on-primary': '255 255 255',     // white
			'--color-page-bg': '228 248 245',        // teal-tinted light
			'--color-page-bg-dark': '12 19 20',      // dark teal
			'--color-surface': '238 252 249',        // teal-tinted surface
			'--color-surface-dark': '9 69 79'        // teal-tinted dark
		}
	},
	{
		id: 'forest',
		label: 'Forest',
		swatch: 'bg-emerald-500',
		tokens: {
			'--color-primary': '5 150 105',          // emerald-600
			'--color-primary-hover': '4 120 87',     // emerald-700
			'--color-primary-dark': '6 95 70',       // emerald-800
			'--color-primary-light-bg': '209 250 229', // emerald-100
			'--color-primary-light-bg-dark': '6 78 59', // emerald-900
			'--color-primary-text': '4 120 87',      // emerald-700
			'--color-primary-text-dark': '110 231 183', // emerald-400
			'--color-primary-border': '16 185 129',  // emerald-500
			'--color-on-primary': '255 255 255',     // white
			'--color-page-bg': '228 248 238',        // emerald-tinted light
			'--color-page-bg-dark': '12 19 15',      // dark forest
			'--color-surface': '237 252 244',        // emerald-tinted surface
			'--color-surface-dark': '21 54 37'       // emerald-tinted dark
		}
	},
	{
		id: 'sunset',
		label: 'Red Alert',
		swatch: 'bg-red-500',
		tokens: {
			'--color-primary': '220 38 38',          // red-600
			'--color-primary-hover': '185 28 28',    // red-700
			'--color-primary-dark': '153 27 27',     // red-800
			'--color-primary-light-bg': '254 226 226', // red-100
			'--color-primary-light-bg-dark': '127 29 29', // red-900
			'--color-primary-text': '185 28 28',     // red-700
			'--color-primary-text-dark': '248 113 113', // red-400
			'--color-primary-border': '239 68 68',   // red-500
			'--color-on-primary': '255 255 255',     // white
			'--color-page-bg': '255 235 235',        // red-tinted light
			'--color-page-bg-dark': '38 0 0',        // dark red
			'--color-surface': '255 243 243',        // red-tinted surface
			'--color-surface-dark': '68 1 0'         // red alert dark
		}
	},
	{
		id: 'rose',
		label: 'Rose',
		swatch: 'bg-pink-500',
		tokens: {
			'--color-primary': '219 39 119',         // pink-600
			'--color-primary-hover': '190 24 93',    // pink-700
			'--color-primary-dark': '157 23 77',     // pink-800
			'--color-primary-light-bg': '252 231 243', // pink-100
			'--color-primary-light-bg-dark': '131 24 67', // pink-900
			'--color-primary-text': '190 24 93',     // pink-700
			'--color-primary-text-dark': '244 114 182', // pink-400
			'--color-primary-border': '236 72 153',  // pink-500
			'--color-on-primary': '255 255 255',     // white
			'--color-page-bg': '252 232 243',        // pink-tinted light
			'--color-page-bg-dark': '47 0 23',       // dark rose
			'--color-surface': '253 242 249',        // pink-tinted surface
			'--color-surface-dark': '132 28 81'      // rose dark
		}
	},
	{
		id: 'violet',
		label: 'Grape',
		swatch: 'bg-purple-500',
		tokens: {
			'--color-primary': '147 51 234',         // purple-600
			'--color-primary-hover': '126 34 206',   // purple-700
			'--color-primary-dark': '107 33 168',    // purple-800
			'--color-primary-light-bg': '237 226 255', // purple-100
			'--color-primary-light-bg-dark': '76 29 149', // purple-900
			'--color-primary-text': '126 34 206',    // purple-700
			'--color-primary-text-dark': '192 132 252', // purple-400
			'--color-primary-border': '168 85 247',  // purple-500
			'--color-on-primary': '255 255 255',     // white
			'--color-page-bg': '243 235 255',        // purple-tinted light
			'--color-page-bg-dark': '16 13 26',      // dark violet
			'--color-surface': '247 243 255',        // purple-tinted surface
			'--color-surface-dark': '48 22 92'       // grape dark
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
}

export const colorScheme = writable<string>(getInitialScheme());

if (browser) {
	colorScheme.subscribe((id) => {
		localStorage.setItem('colorScheme', id);
		applyScheme(id);
	});
}
