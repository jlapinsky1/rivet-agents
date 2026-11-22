"""
Settings tools — read and update business configuration.

Tools:
  get_settings    — read current business settings
  update_settings — apply one or more setting updates and signal the UI to navigate
"""

from db.supabase_client import get_business_settings, update_business_settings

# Maps individual setting keys to the Settings screen + section that owns them.
# Used to emit a navigate hint so the UI opens the right panel after an update.
_SETTING_SECTION = {
    'weeklyGoal':          ('Settings', 'Goals & Capacity'),
    'weeklyHours':         ('Settings', 'Goals & Capacity'),
    'minimumHourlyRate':   ('Settings', 'Pricing & Costs'),
    'minimumPrice':        ('Settings', 'Pricing & Costs'),
    'helperRate':          ('Settings', 'Pricing & Costs'),
    'mileageRate':         ('Settings', 'Pricing & Costs'),
    'materialMarkup':      ('Settings', 'Pricing & Costs'),
    'minimumMargin':       ('Settings', 'Advanced Engine'),
    'minimumJobProfit':    ('Settings', 'Advanced Engine'),
    'dailyCapacityLimit':  ('Settings', 'Advanced Engine'),
    'businessName':        ('Settings', 'Business'),
    'phone':               ('Settings', 'Business'),
    'email':               ('Settings', 'Business'),
    'homeBaseAddress':     ('Settings', 'Business'),
}

# Keys the agent is allowed to read and write
_ALLOWED_KEYS = set(_SETTING_SECTION.keys())


def get_settings(business_id: str) -> dict:
    """Return the current values of all configurable business settings."""
    settings = get_business_settings(business_id)
    return {k: settings[k] for k in _ALLOWED_KEYS if k in settings}


def update_settings(business_id: str, updates: dict) -> dict:
    """
    Merge updates into business settings and return the new values.

    Returns a dict with:
      ok        — True on success
      updated   — the keys and their new values
      _navigate — {screen, section} hint for the frontend (stripped before persisting)
    """
    # Only allow known keys to prevent arbitrary writes
    safe = {k: v for k, v in updates.items() if k in _ALLOWED_KEYS}
    if not safe:
        return {'error': 'No recognised setting keys in update. Check the settings guide.'}

    merged = update_business_settings(business_id, safe)

    # Pick the navigation target from the first updated key
    navigate = None
    for key in safe:
        screen, section = _SETTING_SECTION[key]
        navigate = {'screen': screen, 'section': section}
        break

    result: dict = {'ok': True, 'updated': {k: merged.get(k) for k in safe}}
    if navigate:
        result['_navigate'] = navigate
    return result


def navigate_settings(section: str) -> dict:
    """
    Emit a navigate hint to open a specific Settings section in the UI.
    No data is read or written — purely a UI navigation signal.
    """
    return {'_navigate': {'screen': 'Settings', 'section': section}}


# ── Anthropic tool schemas ────────────────────────────────────────────────────

NAVIGATE_SETTINGS_TOOL = {
    'name': 'navigate_settings',
    'description': (
        'Open a specific Settings section in the contractor\'s UI. '
        'Use this when a contractor asks where to find a setting, how to configure '
        'something, or wants to be taken to a specific settings panel — without '
        'making any changes yet. '
        'Valid sections: Business, Goals & Capacity, Pricing & Costs, Advanced Engine, '
        'Quote Form, Service Area.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'section': {
                'type': 'string',
                'description': 'The Settings section to open.',
            },
        },
        'required': ['section'],
    },
}

GET_SETTINGS_TOOL = {
    'name': 'get_settings',
    'description': (
        'Read the current business settings — weekly goal, hourly rate, margins, '
        'pricing floors, capacity, and cost rates. Call this before answering any '
        'question about how the business is configured or before suggesting changes.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {},
        'required': [],
    },
}

UPDATE_SETTINGS_TOOL = {
    'name': 'update_settings',
    'description': (
        'Update one or more business settings. Only call after confirming the '
        'specific values with the contractor. After a successful update the UI '
        'will automatically open the relevant settings panel so the contractor '
        'can see the change.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'updates': {
                'type': 'object',
                'description': (
                    'Key/value pairs to update. Valid keys: '
                    'weeklyGoal (number, dollars), '
                    'weeklyHours (number, hours per week), '
                    'minimumHourlyRate (number, dollars per hour), '
                    'minimumPrice (number, dollars — smallest job worth taking), '
                    'helperRate (number, dollars per hour for hired help), '
                    'mileageRate (number, dollars per mile), '
                    'materialMarkup (number, percent e.g. 20 for 20%), '
                    'minimumMargin (number, percent e.g. 55 for 55%), '
                    'minimumJobProfit (number, dollars), '
                    'dailyCapacityLimit (number, jobs per day), '
                    'businessName (string), '
                    'phone (string), '
                    'email (string), '
                    'homeBaseAddress (string).'
                ),
                'additionalProperties': True,
            },
        },
        'required': ['updates'],
    },
}
