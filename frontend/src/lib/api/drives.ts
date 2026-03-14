import type { Drive } from '$lib/types/arm';
import { apiFetch } from './client';

export function fetchDrives(): Promise<Drive[]> {
	return apiFetch<Drive[]>('/api/drives');
}

export function updateDrive(
	driveId: number,
	data: { name?: string; description?: string; uhd_capable?: boolean }
): Promise<{ success: boolean; drive_id: number }> {
	return apiFetch(`/api/drives/${driveId}`, {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

export function scanDrive(driveId: number): Promise<{ success: boolean; drive_id: number; devname: string }> {
	return apiFetch(`/api/drives/${driveId}/scan`, { method: 'POST' });
}
