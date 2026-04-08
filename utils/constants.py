"""Sales Academy constants — colors, labels, certification names."""

# Groupon brand colors
GROUPON_GREEN = "#53A318"
GROUPON_DARK_GREEN = "#3D7A12"
GROUPON_LIGHT_GREEN = "#E8F5E0"

# Status colors
COLOR_PASS = "#28a745"
COLOR_FAIL = "#dc3545"
COLOR_PENDING = "#6c757d"
COLOR_WARNING = "#ffc107"
COLOR_INFO = "#17a2b8"

# Activity type colors for schedule
ACTIVITY_COLORS = {
    "classroom": "#4A90D9",
    "call_block": "#53A318",
    "certification": "#E67E22",
    "roleplay": "#E67E22",
    "huddle": "#9B59B6",
    "video": "#8E44AD",
    "shadowing": "#8E44AD",
    "break": "#95A5A6",
    "lunch": "#95A5A6",
    "other": "#95A5A6",
}

# Role display labels
ROLE_LABELS = {
    "rep": "Sales Rep",
    "manager": "Manager",
    "admin": "Training Admin",
}

ROLE_ICONS = {
    "rep": "👤",
    "manager": "👥",
    "admin": "⚙️",
}

# Certification names in display order
CERTIFICATION_NAMES = [
    "Front End",
    "OH: Front End",
    "TUIT & Needs Assessment",
    "OH: TUIT",
    "Presentation: The What & The How",
    "OH: Presentation",
    "Appointment Setting",
    "Gatekeepers",
    "Promotional Programs",
    "Salesloft",
]

# Short names for heatmap columns
CERTIFICATION_SHORT_NAMES = [
    "Front End",
    "OH: FE",
    "TUIT & NA",
    "OH: TUIT",
    "Presentation",
    "OH: Pres",
    "Appt Setting",
    "Gatekeepers",
    "Promo Prog",
    "Salesloft",
]

# Target week for each certification (1-indexed to match cert display_order)
CERT_TARGET_WEEKS = {
    "Front End": 1,
    "OH: Front End": 2,
    "TUIT & Needs Assessment": 2,
    "OH: TUIT": 3,
    "Presentation: The What & The How": 3,
    "OH: Presentation": 3,
    "Appointment Setting": 4,
    "Gatekeepers": 4,
    "Promotional Programs": 5,
    "Salesloft": 5,
}

# Material categories in display order
MATERIAL_CATEGORIES = [
    "Sales Process (Pre-Close)",
    "Objection Handling",
    "Conversation Cards",
    "Groupon",
    "Market Management",
    "Pipeline Process",
    "Sales Process (Post Close)",
    "Tooling",
    "3PIP",
    "SOP",
]

# Program duration
PROGRAM_WEEKS = 6
MAX_COHORT_SIZE = 20
