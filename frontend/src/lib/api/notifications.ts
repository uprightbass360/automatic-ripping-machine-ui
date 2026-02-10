import type { Notification } from '$lib/types/arm';
import { apiFetch } from './client';

export function fetchNotifications(): Promise<Notification[]> {
	return apiFetch<Notification[]>('/api/notifications');
}
