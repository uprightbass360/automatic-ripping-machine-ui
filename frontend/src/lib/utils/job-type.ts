export interface VideoTypeConfig {
	label: string;
	iconPath: string;
	badgeClasses: string;
	placeholderClasses: string;
	accentBorder: string;
	iconColor: string;
}

const MOVIE_CONFIG: VideoTypeConfig = {
	label: 'Movie',
	iconPath: 'M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z',
	badgeClasses: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
	placeholderClasses: 'bg-blue-100 text-blue-400 dark:bg-blue-900/30 dark:text-blue-500',
	accentBorder: 'border-l-blue-500',
	iconColor: 'text-blue-500 dark:text-blue-400',
};

const SERIES_CONFIG: VideoTypeConfig = {
	label: 'Series',
	iconPath: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
	badgeClasses: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
	placeholderClasses: 'bg-purple-100 text-purple-400 dark:bg-purple-900/30 dark:text-purple-500',
	accentBorder: 'border-l-purple-500',
	iconColor: 'text-purple-500 dark:text-purple-400',
};

const MUSIC_CONFIG: VideoTypeConfig = {
	label: 'Music',
	iconPath: 'M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3',
	badgeClasses: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
	placeholderClasses: 'bg-green-100 text-green-400 dark:bg-green-900/30 dark:text-green-500',
	accentBorder: 'border-l-green-500',
	iconColor: 'text-green-500 dark:text-green-400',
};

const FALLBACK_CONFIG: VideoTypeConfig = {
	label: 'Disc',
	iconPath: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4',
	badgeClasses: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
	placeholderClasses: 'bg-primary/10 text-gray-400 dark:bg-primary/15 dark:text-gray-500',
	accentBorder: 'border-l-gray-400',
	iconColor: 'text-gray-500 dark:text-gray-400',
};

const TYPE_MAP: Record<string, VideoTypeConfig> = {
	movie: MOVIE_CONFIG,
	series: SERIES_CONFIG,
	music: MUSIC_CONFIG,
};

export function getVideoTypeConfig(videoType: string | null): VideoTypeConfig {
	if (!videoType) return FALLBACK_CONFIG;
	return TYPE_MAP[videoType.toLowerCase()] ?? FALLBACK_CONFIG;
}

const ACTIVE_STATUSES = new Set([
	'active',
	'ripping',
	'processing',
	'transcoding',
	'pending',
	'waiting',
]);

const DISC_TYPE_LABELS: Record<string, string> = {
	dvd: 'DVD',
	bluray: 'Blu-ray',
	bluray4k: '4K UHD',
	music: 'Music CD',
	data: 'Data',
};

export function discTypeLabel(disctype: string | null | undefined): string {
	if (!disctype) return 'Unknown';
	return DISC_TYPE_LABELS[disctype.toLowerCase()] ?? disctype;
}

export function isJobActive(status: string | null): boolean {
	if (!status) return false;
	return ACTIVE_STATUSES.has(status.toLowerCase());
}
