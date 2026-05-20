import { describe, it, expect, afterEach } from 'vitest';
import { renderComponent, screen, cleanup } from '$lib/test-utils';
import TemplateEditor from '../TemplateEditor.svelte';

describe('TemplateEditor', () => {
	afterEach(() => cleanup());

	it('renders title/body inputs only for subscribed events', () => {
		renderComponent(TemplateEditor, { props: { subscribedEvents: ['job.started'], templates: {} } });
		expect(screen.getByLabelText('job.started title')).toBeTruthy();
		expect(screen.getByLabelText('job.started body')).toBeTruthy();
		expect(screen.queryByLabelText('job.failed title')).toBeNull();
	});

	it('shows available variables for an event', () => {
		renderComponent(TemplateEditor, { props: { subscribedEvents: ['job.started'], templates: {} } });
		expect(screen.getByText(/\{job_title\}/)).toBeTruthy();
		expect(screen.getByText(/\{drive_mount\}/)).toBeTruthy();
	});

	it('prefills existing template values', () => {
		renderComponent(TemplateEditor, {
			props: {
				subscribedEvents: ['job.started'],
				templates: { 'job.started': { title: 'Hi {job_title}', body: 'B' } }
			}
		});
		expect((screen.getByLabelText('job.started title') as HTMLInputElement).value).toBe('Hi {job_title}');
	});
});
