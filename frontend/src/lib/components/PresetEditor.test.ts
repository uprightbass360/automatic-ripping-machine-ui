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
        renderComponent(PresetEditor, { props: { ...baseProps, presets: [mockPresets[0], second] } });
        const select = screen.getByRole('combobox') as HTMLSelectElement;
        await fireEvent.change(select, { target: { value: 'software_quality' } });
        expect(select.value).toBe('software_quality');
    });
});
