export function timeAgo(dateString: string | null): string {
	if (!dateString) return 'N/A';
	const date = new Date(dateString);
	const now = new Date();
	const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

	if (seconds < 60) return `${seconds}s ago`;
	const minutes = Math.floor(seconds / 60);
	if (minutes < 60) return `${minutes}m ago`;
	const hours = Math.floor(minutes / 60);
	if (hours < 24) return `${hours}h ago`;
	const days = Math.floor(hours / 24);
	return `${days}d ago`;
}

export function formatBytes(bytes: number): string {
	if (bytes === 0) return '0 B';
	const k = 1024;
	const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
	const i = Math.floor(Math.log(bytes) / Math.log(k));
	return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function formatDateTime(dateString: string | null): string {
	if (!dateString) return 'N/A';
	return new Date(dateString).toLocaleString();
}

export function elapsedTime(startTime: string | null): string {
	if (!startTime) return 'N/A';
	const start = new Date(startTime);
	const now = new Date();
	const totalSeconds = Math.max(0, Math.floor((now.getTime() - start.getTime()) / 1000));

	const hours = Math.floor(totalSeconds / 3600);
	const minutes = Math.floor((totalSeconds % 3600) / 60);
	const seconds = totalSeconds % 60;

	if (hours > 0) return `${hours}h ${minutes}m`;
	if (minutes > 0) return `${minutes}m ${seconds}s`;
	return `${seconds}s`;
}

export function statusColor(status: string | null): string {
	switch (status?.toLowerCase()) {
		case 'active':
		case 'ripping':
		case 'processing':
			return 'bg-blue-500';
		case 'transcoding':
			return 'bg-indigo-500';
		case 'success':
		case 'completed':
		case 'complete':
			return 'bg-green-500';
		case 'fail':
		case 'failed':
		case 'error':
			return 'bg-red-500';
		case 'waiting':
		case 'pending':
			return 'bg-yellow-500';
		default:
			return 'bg-gray-500';
	}
}
