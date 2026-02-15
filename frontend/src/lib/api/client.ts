const BASE = '';

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
	const res = await fetch(`${BASE}${path}`, {
		...init,
		headers: {
			'Content-Type': 'application/json',
			...init?.headers
		}
	});
	if (!res.ok) {
		let message = `API ${res.status}: ${res.statusText}`;
		try {
			const body = await res.json();
			if (body.detail) message = body.detail;
		} catch { /* use default message */ }
		throw new Error(message);
	}
	return res.json();
}
