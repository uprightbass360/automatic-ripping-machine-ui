/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	darkMode: 'class',
	theme: {
		extend: {
			animation: {
				indeterminate: 'indeterminate 1.5s ease-in-out infinite'
			},
			keyframes: {
				indeterminate: {
					'0%': { transform: 'translateX(-100%)' },
					'100%': { transform: 'translateX(400%)' }
				}
			},
			colors: {
				primary: {
					DEFAULT: 'rgb(var(--color-primary) / <alpha-value>)',
					hover: 'rgb(var(--color-primary-hover) / <alpha-value>)',
					dark: 'rgb(var(--color-primary-dark) / <alpha-value>)',
					'light-bg': 'rgb(var(--color-primary-light-bg) / <alpha-value>)',
					'light-bg-dark': 'rgb(var(--color-primary-light-bg-dark) / <alpha-value>)',
					text: 'rgb(var(--color-primary-text) / <alpha-value>)',
					'text-dark': 'rgb(var(--color-primary-text-dark) / <alpha-value>)',
					border: 'rgb(var(--color-primary-border) / <alpha-value>)',
				'on-primary': 'rgb(var(--color-on-primary) / <alpha-value>)'
				},
				page: {
					DEFAULT: 'rgb(var(--color-page-bg) / <alpha-value>)',
					dark: 'rgb(var(--color-page-bg-dark) / <alpha-value>)'
				},
				surface: {
					DEFAULT: 'rgb(var(--color-surface) / <alpha-value>)',
					dark: 'rgb(var(--color-surface-dark) / <alpha-value>)'
				}
			}
		}
	},
	plugins: []
};
