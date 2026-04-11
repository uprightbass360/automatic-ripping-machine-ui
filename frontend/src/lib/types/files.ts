export interface FileRoot {
	key: string;
	label: string;
	path: string;
	host_path?: string;
	readonly?: boolean;
}

export interface FileEntry {
	name: string;
	type: 'directory' | 'file';
	size: number;
	modified: string;
	extension: string;
	category: string;
	permissions?: string;
	owner?: string;
	group?: string;
}

export interface DirectoryListing {
	path: string;
	parent: string | null;
	entries: FileEntry[];
	readonly?: boolean;
}
