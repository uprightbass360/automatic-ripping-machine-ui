export function timeAgo(dateString: string | null): string {
	if (!dateString) return 'N/A';
	const date = new Date(dateString);
	const now = new Date();
	const seconds = Math.max(0, Math.floor((now.getTime() - date.getTime()) / 1000));

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

/**
 * Map a status string to a CSS class. Receives values from three different
 * enums depending on caller:
 *   - arm_contracts.JobState (arm-neu Job.status) - StatusBadge in JobRow,
 *     JobCard, ActiveJobRow, DriveCard, jobs/[id]. Disambiguated in v2.0.0:
 *     'ripping' -> 'video_ripping'/'audio_ripping', 'waiting' ->
 *     'manual_paused'/'makemkv_throttled'. Old strings kept as defensive
 *     fallbacks for in-flight jobs observed mid-deploy.
 *   - arm_contracts.JobStatus (transcoder TranscodeJob.status) - StatusBadge
 *     in TranscodeCard, transcoder/+page.svelte
 *   - arm_contracts.TrackStatus (Track.status) - StatusBadge at jobs/[id]:849.
 *     'failed' is a real TrackStatus member as of v2.0.0 (was previously
 *     only handled defensively for transcoder JobStatus).
 * Plus two locally-generated literals: 'importing' (folder-import override
 * for status='ripping') and 'skipped' (UI-only marker for filtered/disabled
 * tracks). Both are produced inline at the StatusBadge call site, not by any
 * backend.
 */
export function statusColor(status: string | null): string {
	switch (status?.toLowerCase()) {
		case 'identifying':
			return 'status-scanning';
		case 'ready':
		case 'ripping':         // legacy pre-v2.0.0; in-flight jobs mid-deploy
		case 'video_ripping':
		case 'audio_ripping':
		case 'importing': // locally generated when isFolderImport && status='ripping'
			return 'status-active';
		case 'copying':
		case 'ejecting':
			return 'status-warning';
		case 'transcoding':
		case 'processing': // JobStatus (transcoder) - TranscodeCard / transcoder page
			return 'status-processing';
		case 'success':
		case 'completed': // JobStatus (transcoder) terminal
		case 'transcoded': // TrackStatus terminal (transcode-phase)
			return 'status-success';
		case 'fail':
		case 'failed': // JobStatus (transcoder) terminal AND TrackStatus.failed (v2.0.0+)
			return 'status-error';
		case 'waiting':         // legacy pre-v2.0.0; in-flight jobs mid-deploy
		case 'manual_paused':
		case 'makemkv_throttled':
		case 'waiting_transcode':
		case 'pending': // JobStatus (transcoder) + TrackStatus member
			return 'status-warning';
		case 'skipped': // locally generated for !track.enabled || filtered (jobs/[id]:849)
			return 'status-unknown';
		default:
			return 'status-unknown';
	}
}

const STATUS_LABELS: Record<string, string> = {
	identifying: 'Scanning',
	ready: 'Ready',
	active: 'Active',
	ripping: 'Ripping',           // legacy pre-v2.0.0; in-flight jobs mid-deploy
	video_ripping: 'Ripping',
	audio_ripping: 'Ripping',
	importing: 'Processing',
	copying: 'Copying',
	ejecting: 'Ejecting',
	processing: 'Transcoding',
	transcoding: 'Transcoding',
	success: 'Success',
	completed: 'Completed',
	complete: 'Complete',
	fail: 'Failed',
	failed: 'Failed',
	error: 'Error',
	waiting: 'Waiting',           // legacy pre-v2.0.0; in-flight jobs mid-deploy
	manual_paused: 'Paused',
	makemkv_throttled: 'Throttled',
	waiting_transcode: 'Waiting to Transcode',
	pending: 'Pending',
	skipped: 'Skipped',
	transcoded: 'Transcoded',
	info: 'Scanning',
	cancelled: 'Cancelled',
};

export function statusLabel(status: string | null): string {
	if (!status) return 'Unknown';
	return STATUS_LABELS[status.toLowerCase()] ?? status;
}
