import '@testing-library/jest-dom/vitest';

// jsdom doesn't implement window.matchMedia — stub it for stores that
// check prefers-color-scheme on the client side.
Object.defineProperty(globalThis, 'matchMedia', {
	writable: true,
	value: (query: string) => ({
		matches: false,
		media: query,
		onchange: null,
		addListener: () => {},
		removeListener: () => {},
		addEventListener: () => {},
		removeEventListener: () => {},
		dispatchEvent: () => false
	})
});
