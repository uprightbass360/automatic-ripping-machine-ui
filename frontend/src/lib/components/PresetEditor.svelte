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
    </div>
{/if}
