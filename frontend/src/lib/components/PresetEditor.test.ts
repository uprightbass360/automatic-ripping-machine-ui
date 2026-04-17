import { describe, it, expect, afterEach, vi } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup } from '$lib/test-utils';
import PresetEditor from './PresetEditor.svelte';
import type { Scheme, Preset } from '$lib/types/presets';

const mockScheme: Scheme = {
    slug: 'software',
    name: 'Software (CPU)',
    supported_encoders: [
        { slug: 'x265', name: 'x265', tuning_presets: [] },
        { slug: 'x264', name: 'x264', tuning_presets: [] }
    ],
    supported_audio_encoders: ['copy', 'aac'],
    supported_subtitle_modes: ['all', 'first', 'none'],
    advanced_fields: {}
};

const mockPresets: Preset[] = [
    {
        slug: 'software_balanced', name: 'Balanced', scheme: 'software',
        description: 'Balanced encoding', builtin: true,
        shared: { audio_encoder: 'copy', subtitle_mode: 'all' },
        tiers: {
            dvd: { video_encoder: 'x265', video_quality: 22 },
            bluray: { video_encoder: 'x265', video_quality: 22 },
            uhd: { video_encoder: 'x265', video_quality: 22 }
        }
    }
];

describe('PresetEditor', () => {
    afterEach(() => cleanup());

    it('renders the active scheme name in the header', () => {
        renderComponent(PresetEditor, {
            props: {
                scope: 'global',
                initialState: { preset_slug: 'software_balanced', overrides: { shared: {}, tiers: {} } },
                scheme: mockScheme,
                presets: mockPresets,
                offline: false,
                saving: false,
                onSave: async () => {}
            }
        });
        expect(screen.getByText(/Software \(CPU\)/i)).toBeInTheDocument();
    });
});

const customPreset: Preset = {
    slug: 'my-custom', name: 'My Custom', scheme: 'software',
    description: '', builtin: false, parent_slug: 'software_balanced',
    shared: {}, tiers: { dvd: {}, bluray: {}, uhd: {} }
};

const unavailablePreset: Preset = {
    slug: 'nvidia-imp', name: 'Nvidia Import', scheme: 'nvidia',
    description: '', builtin: false, parent_slug: 'nvidia_balanced',
    shared: {}, tiers: { dvd: {}, bluray: {}, uhd: {} },
    unavailable: true, reason: 'scheme mismatch'
};

describe('PresetEditor dropdown', () => {
    afterEach(() => cleanup());

    const baseProps = {
        scope: 'global' as const,
        initialState: { preset_slug: 'software_balanced', overrides: { shared: {}, tiers: {} } },
        scheme: mockScheme,
        offline: false,
        saving: false,
        onSave: async () => {}
    };

    it('renders built-in, custom, and unavailable groups', () => {
        renderComponent(PresetEditor, {
            props: { ...baseProps, presets: [...mockPresets, customPreset, unavailablePreset] }
        });
        expect(screen.getByRole('option', { name: /Balanced/ })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: /My Custom/ })).toBeInTheDocument();
        const unavail = screen.getByRole('option', { name: /Nvidia Import/ }) as HTMLOptionElement;
        expect(unavail.disabled).toBe(true);
    });

    it('shows preset description below the dropdown', () => {
        renderComponent(PresetEditor, { props: { ...baseProps, presets: mockPresets } });
        expect(screen.getByText(/Balanced encoding/)).toBeInTheDocument();
    });

    it('updates selectedSlug when dropdown changes', async () => {
        const second: Preset = { ...mockPresets[0], slug: 'software_quality', name: 'Quality' };
        const { container } = renderComponent(PresetEditor, { props: { ...baseProps, presets: [mockPresets[0], second] } });
        const select = container.querySelector('#preset-select') as HTMLSelectElement;
        await fireEvent.change(select, { target: { value: 'software_quality' } });
        expect(select.value).toBe('software_quality');
    });
});

describe('PresetEditor customize panel', () => {
    afterEach(() => cleanup());

    const props = {
        scope: 'global' as const,
        initialState: { preset_slug: 'software_balanced', overrides: { shared: {}, tiers: {} } },
        scheme: mockScheme,
        presets: mockPresets,
        offline: false,
        saving: false,
        onSave: async () => {}
    };

    it('renders Shared row with audio_encoder and subtitle_mode dropdowns', () => {
        renderComponent(PresetEditor, { props });
        expect(screen.getByText(/Audio encoder/i)).toBeInTheDocument();
        expect(screen.getByText(/Subtitle mode/i)).toBeInTheDocument();
    });

    it('renders three tier sections', () => {
        renderComponent(PresetEditor, { props });
        expect(screen.getByText(/^DVD/)).toBeInTheDocument();
        expect(screen.getByText(/Blu-ray/)).toBeInTheDocument();
        expect(screen.getByText(/^UHD/)).toBeInTheDocument();
    });

    it('only shows scheme-supported encoders (no nvenc options)', () => {
        renderComponent(PresetEditor, { props });
        // mockScheme has x265 and x264 only - no nvenc options should appear
        expect(screen.queryByRole('option', { name: /nvenc/i })).toBeNull();
    });

    it('writes to overrides.tiers[tier][key] when a tier field changes', async () => {
        const { container } = renderComponent(PresetEditor, { props });
        const qualityInput = container.querySelector('input[data-testid="tier-bluray-quality"]') as HTMLInputElement;
        expect(qualityInput).toBeTruthy();
        await fireEvent.input(qualityInput, { target: { value: '18' } });
        // Visual: dirty pill should show "1 change"
        expect(screen.getByText(/1 change/i)).toBeInTheDocument();
    });
});

describe('PresetEditor save bar', () => {
    afterEach(() => cleanup());

    const baseProps = {
        scope: 'global' as const,
        initialState: { preset_slug: 'software_balanced', overrides: { shared: {}, tiers: {} } },
        scheme: mockScheme,
        presets: mockPresets,
        offline: false,
        saving: false
    };

    it('Save button disabled when not dirty and slug unchanged', () => {
        renderComponent(PresetEditor, { props: { ...baseProps, onSave: async () => {} } });
        const btn = screen.getByRole('button', { name: /Save changes/i }) as HTMLButtonElement;
        expect(btn.disabled).toBe(true);
    });

    it('Save button enabled when dirty', async () => {
        const { container } = renderComponent(PresetEditor, { props: { ...baseProps, onSave: async () => {} } });
        const qualityInput = container.querySelector('input[data-testid="tier-bluray-quality"]') as HTMLInputElement;
        await fireEvent.input(qualityInput, { target: { value: '18' } });
        const btn = screen.getByRole('button', { name: /Save changes/i }) as HTMLButtonElement;
        expect(btn.disabled).toBe(false);
    });

    it('calls onSave with current state when Save clicked', async () => {
        const onSave = vi.fn().mockResolvedValue(undefined);
        const { container } = renderComponent(PresetEditor, { props: { ...baseProps, onSave } });
        const qualityInput = container.querySelector('input[data-testid="tier-bluray-quality"]') as HTMLInputElement;
        await fireEvent.input(qualityInput, { target: { value: '18' } });
        await fireEvent.click(screen.getByRole('button', { name: /Save changes/i }));
        expect(onSave).toHaveBeenCalledWith(expect.objectContaining({
            preset_slug: 'software_balanced',
            overrides: expect.objectContaining({ tiers: expect.objectContaining({ bluray: { video_quality: 18 } }) })
        }));
    });

    it('Revert clears overrides', async () => {
        const { container } = renderComponent(PresetEditor, { props: { ...baseProps, onSave: async () => {} } });
        const qualityInput = container.querySelector('input[data-testid="tier-bluray-quality"]') as HTMLInputElement;
        await fireEvent.input(qualityInput, { target: { value: '18' } });
        expect(screen.getByText(/1 change/i)).toBeInTheDocument();
        await fireEvent.click(screen.getByRole('button', { name: /Revert/i }));
        expect(screen.queryByText(/^\d+ changes?$/i)).toBeNull();
    });

    it('hides "Save as new preset" when scope=job', () => {
        renderComponent(PresetEditor, { props: { ...baseProps, scope: 'job', onSave: async () => {} } });
        expect(screen.queryByText(/Save as new preset/i)).toBeNull();
    });

    it('shows "Save as new preset" when scope=global with onSaveAsNew handler', () => {
        renderComponent(PresetEditor, { props: { ...baseProps, onSave: async () => {}, onSaveAsNew: async () => {} } });
        expect(screen.getByText(/Save as new preset/i)).toBeInTheDocument();
    });
});
