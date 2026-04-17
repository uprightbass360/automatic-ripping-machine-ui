export interface Encoder {
    slug: string;
    name: string;
    tuning_presets: string[];
}

export interface AdvancedField {
    type: 'enum' | 'int' | 'string';
    values?: string[];
    default?: string;
    description?: string;
    min?: number;
    max?: number;
}

export interface Scheme {
    slug: string;
    name: string;
    supported_encoders: Encoder[];
    supported_audio_encoders: string[];
    supported_subtitle_modes: string[];
    advanced_fields: Record<string, AdvancedField>;
}

export interface Preset {
    slug: string;
    name: string;
    scheme: string;
    description: string;
    builtin: boolean;
    shared: Record<string, unknown>;
    tiers: Record<'dvd' | 'bluray' | 'uhd', Record<string, unknown>>;
    parent_slug?: string;
    unavailable?: boolean;
    reason?: string;
}

export interface Overrides {
    shared: Record<string, unknown>;
    tiers: Record<string, Record<string, unknown>>;
}

export interface PresetEditorState {
    preset_slug: string;
    overrides: Overrides;
}
