export interface SetupStatus {
	db_exists: boolean;
	db_initialized: boolean;
	db_current: boolean;
	db_version: string;
	db_head: string;
	first_run: boolean;
	arm_version: string;
	setup_steps: Record<string, string>;
}
