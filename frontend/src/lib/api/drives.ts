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

export function deleteDrive(driveId: number): Promise<{ success: boolean; drive_id: number }> {
	return apiFetch(`/api/drives/${driveId}`, { method: 'DELETE' });
}

export interface DriveDiagnostic {
	devname: string;
	status: 'ok' | 'warning';
	dev_node_exists: boolean;
	sysfs_exists: boolean;
	major_minor: string | null;
	in_kernel_cdrom: boolean;
	tray_status: number | null;
	tray_status_name: string | null;
	udevadm: Record<string, string>;
	arm_processing: boolean;
	in_database: boolean;
	db_name?: string;
	db_model?: string;
	db_connection?: string;
	issues: string[];
}

export interface DiagnosticResult {
	success: boolean;
	udevd_running: boolean;
	kernel_drives: string[];
	drives: DriveDiagnostic[];
	issues: string[];
}

export function fetchDriveDiagnostic(): Promise<DiagnosticResult> {
	return apiFetch<DiagnosticResult>('/api/drives/diagnostic');
}
