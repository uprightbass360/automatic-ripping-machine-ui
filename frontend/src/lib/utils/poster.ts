/**
 * Proxy an external poster URL through the backend to avoid browser
 * ORB/CORS blocking (Firefox blocks m.media-amazon.com images on HTTP origins).
 */
export function posterSrc(url: string | null | undefined): string {
	if (!url) return '';
	// Only proxy external URLs — local/relative paths don't need it
	if (!url.startsWith('http://') && !url.startsWith('https://')) return url;
	return `/api/jobs/folder/poster-proxy?url=${encodeURIComponent(url)}`;
}
