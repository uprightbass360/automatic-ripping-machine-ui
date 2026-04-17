import { describe, it, expect, afterEach } from 'vitest';
import { renderComponent, screen, cleanup } from '$lib/test-utils';
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
