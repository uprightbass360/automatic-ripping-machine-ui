import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderComponent, screen, waitFor, cleanup } from '$lib/test-utils';
import { fireEvent } from '@testing-library/svelte';
import TranscodeOverrides from './TranscodeOverrides.svelte';
import type { Job } from '$lib/types/arm';

vi.mock('$lib/api/settings', () => ({
    fetchTranscoderScheme: vi.fn().mockResolvedValue({
        slug: 'software', name: 'Software (CPU)',
        supported_encoders: [{ slug: 'x265', name: 'x265', tuning_presets: [] }],
        supported_audio_encoders: ['copy', 'aac'],
        supported_subtitle_modes: ['all'],
        advanced_fields: {}
    }),
    fetchTranscoderPresets: vi.fn().mockResolvedValue({
        presets: [{
            slug: 'software_balanced', name: 'Balanced', scheme: 'software',
            description: '', builtin: true,
            shared: {}, tiers: { dvd: {}, bluray: {}, uhd: {} }
        }]
    })
}));

const updateMock = vi.fn().mockResolvedValue({ success: true });
vi.mock('$lib/api/jobs', () => ({
    updateJobTranscodeConfig: (...args: unknown[]) => updateMock(...args)
}));

const baseJob = {
    job_id: 1,
    transcode_overrides: { preset_slug: 'software_balanced', overrides: { shared: {}, tiers: {} } }
} as unknown as Job;

beforeEach(() => updateMock.mockClear());
afterEach(() => cleanup());

describe('TranscodeOverrides', () => {
    it('renders PresetEditor and submits new-shape overrides on save', async () => {
        const { container } = renderComponent(TranscodeOverrides, { props: { job: baseJob } });
        await waitFor(() => screen.getByText(/Software \(CPU\)/));
        const qualityInput = container.querySelector('input[data-testid="tier-bluray-quality"]') as HTMLInputElement;
        await fireEvent.input(qualityInput, { target: { value: '18' } });
        await fireEvent.click(screen.getByRole('button', { name: /Save changes/i }));
        await waitFor(() => expect(updateMock).toHaveBeenCalled());
        expect(updateMock).toHaveBeenCalledWith(1, expect.objectContaining({
            preset_slug: 'software_balanced',
            overrides: expect.objectContaining({ tiers: expect.objectContaining({ bluray: { video_quality: 18 } }) })
        }));
    });

    it('does not show "Save as new preset" (scope=job)', async () => {
        renderComponent(TranscodeOverrides, { props: { job: baseJob } });
        await waitFor(() => screen.getByText(/Software \(CPU\)/));
        expect(screen.queryByText(/Save as new preset/i)).toBeNull();
    });
});
