TEETH = [(str(n), str(n)) for n in (
    list(range(11, 19)) + list(range(21, 29)) + list(range(31, 39)) + list(range(41, 49)))]

SURFACES = [
    ('w', 'Whole tooth'), ('m', 'Mesial'), ('d', 'Distal'), ('o', 'Occlusal'),
    ('b', 'Buccal'), ('l', 'Lingual'), ('i', 'Incisal'),
]

CONDITIONS = [
    ('healthy', 'Healthy'), ('caries', 'Caries'), ('filled', 'Filled'),
    ('crown', 'Crown'), ('root_canal', 'Root Canal'), ('implant', 'Implant'),
    ('bridge', 'Bridge'), ('sealant', 'Sealant'), ('fractured', 'Fractured'),
    ('extraction_needed', 'Extraction Needed'), ('missing', 'Missing / Extracted'),
]

CONDITION_COLORS = {
    'healthy': '#e8f3ef', 'caries': '#e5484d', 'filled': '#3b82f6',
    'crown': '#f5a524', 'root_canal': '#a855f7', 'implant': '#0f766e',
    'bridge': '#d97706', 'sealant': '#22c55e', 'fractured': '#be123c',
    'extraction_needed': '#7f1d1d', 'missing': '#9ca3af',
}

GENDERS = [('male', 'Male'), ('female', 'Female'), ('other', 'Other')]
