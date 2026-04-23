import { crossfade } from 'svelte/transition';
import { cubicOut } from 'svelte/easing';

const reducedMotion =
	typeof window !== 'undefined' &&
	typeof window.matchMedia === 'function' &&
	window.matchMedia('(prefers-reduced-motion: reduce)').matches;

export const [send, receive] = crossfade({
	duration: reducedMotion ? 0 : 200,
	easing: cubicOut
});

export const fadeIn = { duration: reducedMotion ? 0 : 150, easing: cubicOut };
export const fadeOut = { duration: reducedMotion ? 0 : 150, easing: cubicOut };
