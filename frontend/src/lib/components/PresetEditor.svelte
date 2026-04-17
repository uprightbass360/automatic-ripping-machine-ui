<script lang="ts">
    import type { Scheme, Preset, Overrides, PresetEditorState } from '$lib/types/presets';

    interface Props {
        scope: 'global' | 'job';
        initialState: PresetEditorState;
        scheme: Scheme | null;
        presets: Preset[];
        offline: boolean;
        saving: boolean;
        onSave: (state: PresetEditorState) => Promise<void>;
        onSaveAsNew?: (state: { name: string; parent_slug: string; overrides: Overrides }) => Promise<void>;
        onRetry?: () => void;
    }

    let { scope, initialState, scheme, presets, offline, saving, onSave, onSaveAsNew, onRetry }: Props = $props();

    const initialSlug = initialState.preset_slug;
    let selectedSlug = $state<string>(initialSlug);
    let overrides = $state<Overrides>(structuredClone(initialState.overrides));

    const dirty = $derived(
        Object.keys(overrides.shared).length +
        Object.values(overrides.tiers).reduce((n, t) => n + Object.keys(t).length, 0) > 0
    );
    const selectedPreset = $derived(presets.find(p => p.slug === selectedSlug));
    const isUnavailable = $derived(selectedPreset?.unavailable === true);
    const canSave = $derived(!saving && !isUnavailable && (dirty || selectedSlug !== initialSlug));

    const builtinCount = $derived(presets.filter(p => p.builtin && !p.unavailable).length);
    const customCount = $derived(presets.filter(p => !p.builtin && !p.unavailable).length);

    function setShared(key: string, value: unknown) {
        if (value === '' || value === null || value === undefined) {
            delete overrides.shared[key];
        } else {
            overrides.shared[key] = value;
        }
        overrides = { ...overrides };
    }

    function setTier(tier: string, key: string, value: unknown) {
        if (!overrides.tiers[tier]) overrides.tiers[tier] = {};
        if (value === '' || value === null || value === undefined) {
            delete overrides.tiers[tier][key];
            if (Object.keys(overrides.tiers[tier]).length === 0) delete overrides.tiers[tier];
        } else {
            overrides.tiers[tier][key] = value;
        }
        overrides = { ...overrides };
    }

    function effectiveShared(key: string): unknown {
        if (key in overrides.shared) return overrides.shared[key];
        return selectedPreset?.shared[key] ?? '';
    }

    function effectiveTier(tier: string, key: string): unknown {
        if (overrides.tiers[tier]?.[key] !== undefined) return overrides.tiers[tier][key];
        return selectedPreset?.tiers[tier as 'dvd' | 'bluray' | 'uhd']?.[key] ?? '';
    }

    function isSharedDirty(key: string): boolean {
        return key in overrides.shared;
    }

    function isTierDirty(tier: string, key: string): boolean {
        return overrides.tiers[tier]?.[key] !== undefined;
    }

    const TIER_LABELS: Record<string, string> = { dvd: 'DVD', bluray: 'Blu-ray', uhd: 'UHD' };
    const TIER_HINTS: Record<string, string> = { dvd: '< 720p', bluray: '720p–1080p', uhd: '> 1080p' };

    const dirtyRing = 'rounded-lg ring-2 ring-primary/40 dark:ring-primary/50';
    const inputClass = 'rounded-lg border border-primary/25 bg-primary/5 px-3 py-1.5 text-sm focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white';

    let saveAsModalOpen = $state(false);
    let newPresetName = $state('');

    function handleSave() {
        if (!canSave) return;
        onSave({ preset_slug: selectedSlug, overrides });
    }

    function handleRevert() {
        overrides = { shared: {}, tiers: {} };
        selectedSlug = initialSlug;
    }

    function handleSaveAsConfirm() {
        if (!onSaveAsNew || !newPresetName.trim()) return;
        onSaveAsNew({ name: newPresetName.trim(), parent_slug: selectedSlug, overrides });
        saveAsModalOpen = false;
        newPresetName = '';
    }

    function disabledSaveReason(): string {
        if (saving) return 'Saving...';
        if (isUnavailable) return 'Selected preset is not available in the active scheme';
        if (!dirty && selectedSlug === initialSlug) return 'No changes to save';
        return '';
    }

    function slugify(name: string): string {
        return name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'custom';
    }
</script>

{#if offline || !scheme}
    <div class="rounded-lg border border-amber-500/40 bg-amber-50 p-4 text-amber-900 dark:border-amber-500/30 dark:bg-amber-950/30 dark:text-amber-200">
        <p class="font-semibold">Transcoder service unavailable</p>
        <p class="mt-1 text-sm">Cannot load preset options. Check that arm-transcoder is running.</p>
        {#if onRetry}
            <button onclick={onRetry} class="mt-2 rounded-md bg-amber-600 px-3 py-1 text-sm font-medium text-white hover:bg-amber-700">
                Retry
            </button>
        {/if}
    </div>
{:else}
    <div class="space-y-4">
        <div class="flex items-baseline justify-between border-b border-gray-200 pb-2 dark:border-gray-700">
            <div>
                <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Active scheme</p>
                <p class="text-base font-semibold text-gray-900 dark:text-white">{scheme.name}</p>
            </div>
            <p class="text-xs text-gray-500 dark:text-gray-400">{builtinCount} built-in · {customCount} custom</p>
        </div>
        <div>
            <label for="preset-select" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Preset</label>
            <select
                id="preset-select"
                bind:value={selectedSlug}
                onchange={() => { overrides = { shared: {}, tiers: {} }; }}
                class="mt-1 w-full rounded-lg border border-primary/25 bg-primary/5 px-3 py-1.5 text-sm focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white"
            >
                <optgroup label="Built-in">
                    {#each presets.filter(p => p.builtin && !p.unavailable) as p (p.slug)}
                        <option value={p.slug}>{p.name}</option>
                    {/each}
                </optgroup>
                {#if presets.some(p => !p.builtin && !p.unavailable)}
                    <optgroup label="Custom">
                        {#each presets.filter(p => !p.builtin && !p.unavailable) as p (p.slug)}
                            <option value={p.slug}>{p.name}</option>
                        {/each}
                    </optgroup>
                {/if}
                {#if presets.some(p => p.unavailable)}
                    <optgroup label="Unavailable (other scheme)">
                        {#each presets.filter(p => p.unavailable) as p (p.slug)}
                            <option value={p.slug} disabled title={p.reason}>{p.name} ({p.scheme})</option>
                        {/each}
                    </optgroup>
                {/if}
            </select>
            {#if selectedPreset?.description}
                <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{selectedPreset.description}</p>
            {/if}
        </div>

        <div>
            <div class="flex items-center justify-between">
                <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Customize</h4>
                {#if dirty}
                    {@const total = Object.keys(overrides.shared).length + Object.values(overrides.tiers).reduce((n, t) => n + Object.keys(t).length, 0)}
                    <span class="rounded-full bg-primary/20 px-2 py-0.5 text-xs font-medium text-primary dark:text-primary-300">
                        {total} {total === 1 ? 'change' : 'changes'}
                    </span>
                {/if}
            </div>

            <div class="mt-3 space-y-3">
                <div class="rounded-lg border border-gray-200 p-3 dark:border-gray-700">
                    <p class="mb-2 text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Shared</p>
                    <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                        <label class="space-y-1">
                            <span class="text-xs text-gray-600 dark:text-gray-400">Audio encoder</span>
                            <div class={isSharedDirty('audio_encoder') ? dirtyRing : ''}>
                                <select
                                    value={effectiveShared('audio_encoder')}
                                    onchange={(e) => setShared('audio_encoder', (e.target as HTMLSelectElement).value)}
                                    class="{inputClass} w-full"
                                >
                                    {#each scheme.supported_audio_encoders as enc}
                                        <option value={enc}>{enc}</option>
                                    {/each}
                                </select>
                            </div>
                        </label>
                        <label class="space-y-1">
                            <span class="text-xs text-gray-600 dark:text-gray-400">Subtitle mode</span>
                            <div class={isSharedDirty('subtitle_mode') ? dirtyRing : ''}>
                                <select
                                    value={effectiveShared('subtitle_mode')}
                                    onchange={(e) => setShared('subtitle_mode', (e.target as HTMLSelectElement).value)}
                                    class="{inputClass} w-full"
                                >
                                    {#each scheme.supported_subtitle_modes as mode}
                                        <option value={mode}>{mode}</option>
                                    {/each}
                                </select>
                            </div>
                        </label>
                    </div>
                </div>

                {#each ['dvd', 'bluray', 'uhd'] as tier}
                    <div class="rounded-lg border border-gray-200 p-3 dark:border-gray-700">
                        <p class="mb-2 text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                            {TIER_LABELS[tier]} <span class="text-gray-400">· {TIER_HINTS[tier]}</span>
                        </p>
                        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                            <label class="space-y-1">
                                <span class="text-xs text-gray-600 dark:text-gray-400">Encoder</span>
                                <div class={isTierDirty(tier, 'video_encoder') ? dirtyRing : ''}>
                                    <select
                                        value={effectiveTier(tier, 'video_encoder')}
                                        onchange={(e) => setTier(tier, 'video_encoder', (e.target as HTMLSelectElement).value)}
                                        class="{inputClass} w-full"
                                    >
                                        {#each scheme.supported_encoders as enc}
                                            <option value={enc.slug}>{enc.name}</option>
                                        {/each}
                                    </select>
                                </div>
                            </label>
                            <label class="space-y-1">
                                <span class="text-xs text-gray-600 dark:text-gray-400">Quality (CRF 0-51)</span>
                                <div class={isTierDirty(tier, 'video_quality') ? dirtyRing : ''}>
                                    <input
                                        type="number" min="0" max="51" step="1"
                                        data-testid="tier-{tier}-quality"
                                        value={effectiveTier(tier, 'video_quality')}
                                        oninput={(e) => setTier(tier, 'video_quality', Number((e.target as HTMLInputElement).value))}
                                        class="{inputClass} w-full"
                                    />
                                </div>
                            </label>
                            <label class="space-y-1 lg:col-span-2">
                                <span class="text-xs text-gray-600 dark:text-gray-400">HandBrake preset</span>
                                <div class={isTierDirty(tier, 'handbrake_preset') ? dirtyRing : ''}>
                                    <input
                                        type="text"
                                        value={effectiveTier(tier, 'handbrake_preset')}
                                        oninput={(e) => setTier(tier, 'handbrake_preset', (e.target as HTMLInputElement).value)}
                                        class="{inputClass} w-full"
                                    />
                                </div>
                            </label>
                            {#each Object.entries(scheme.advanced_fields) as [key, def]}
                                <label class="space-y-1">
                                    <span class="text-xs text-gray-600 dark:text-gray-400">{key}</span>
                                    <div class={isTierDirty(tier, key) ? dirtyRing : ''}>
                                        {#if def.type === 'enum' && def.values}
                                            <select
                                                value={effectiveTier(tier, key) || def.default || ''}
                                                onchange={(e) => setTier(tier, key, (e.target as HTMLSelectElement).value)}
                                                class="{inputClass} w-full"
                                            >
                                                {#each def.values as v}
                                                    <option value={v}>{v}</option>
                                                {/each}
                                            </select>
                                        {:else}
                                            <input
                                                type="text"
                                                value={effectiveTier(tier, key)}
                                                oninput={(e) => setTier(tier, key, (e.target as HTMLInputElement).value)}
                                                class="{inputClass} w-full"
                                            />
                                        {/if}
                                    </div>
                                    {#if def.description}
                                        <span class="block text-xs text-gray-400">{def.description}</span>
                                    {/if}
                                </label>
                            {/each}
                        </div>
                    </div>
                {/each}
            </div>
        </div>

        <div class="flex items-center justify-between border-t border-gray-200 pt-3 dark:border-gray-700">
            <div class="flex items-center gap-3">
                <button
                    type="button"
                    onclick={handleSave}
                    disabled={!canSave}
                    title={disabledSaveReason()}
                    aria-label="Save changes"
                    class="rounded-lg bg-primary px-4 py-1.5 text-sm font-semibold text-white hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    {saving ? 'Saving...' : 'Save'}
                </button>
                {#if scope === 'global' && onSaveAsNew}
                    <button
                        type="button"
                        onclick={() => { saveAsModalOpen = true; newPresetName = ''; }}
                        disabled={!dirty}
                        class="text-sm text-primary underline-offset-2 hover:underline disabled:opacity-50"
                    >
                        Save as new preset
                    </button>
                {/if}
            </div>
            <button
                type="button"
                onclick={handleRevert}
                disabled={!dirty && selectedSlug === initialSlug}
                class="text-sm text-gray-500 hover:text-gray-700 disabled:opacity-50 dark:text-gray-400 dark:hover:text-gray-200"
            >
                Revert
            </button>
        </div>
    </div>

    {#if saveAsModalOpen}
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" role="dialog" aria-modal="true">
            <div class="w-full max-w-md rounded-lg bg-white p-5 shadow-xl dark:bg-gray-800">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Save as new preset</h3>
                <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    Saves your current customizations as a new preset based on <strong>{selectedPreset?.name}</strong>.
                </p>
                <label class="mt-3 block">
                    <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Name</span>
                    <input
                        type="text"
                        bind:value={newPresetName}
                        placeholder="e.g. Weekend Rips"
                        class="{inputClass} mt-1 w-full"
                    />
                    {#if newPresetName.trim()}
                        <span class="mt-1 block text-xs text-gray-500 dark:text-gray-400">Will be saved as: <code>{slugify(newPresetName)}</code></span>
                    {/if}
                </label>
                <div class="mt-4 flex justify-end gap-2">
                    <button type="button" onclick={() => { saveAsModalOpen = false; }}
                            class="rounded-lg px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700">
                        Cancel
                    </button>
                    <button type="button" onclick={handleSaveAsConfirm}
                            disabled={!newPresetName.trim()}
                            class="rounded-lg bg-primary px-3 py-1.5 text-sm font-semibold text-white hover:bg-primary/90 disabled:opacity-50">
                        Create preset
                    </button>
                </div>
            </div>
        </div>
    {/if}
{/if}
