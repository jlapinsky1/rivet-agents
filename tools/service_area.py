"""
Service area tools — read and update the quote form's geographic coverage.

Tools:
  get_service_area    — read current service area config (mode, radius, ZIP lists)
  update_service_area — apply changes to the service area config
"""

import os
import json
import urllib.request
import urllib.error
import logging

logger = logging.getLogger(__name__)

NETLIFY_URL = os.environ.get('NETLIFY_URL', '')
_ENDPOINT = '/api/agent/service-area'


def _get_current() -> dict:
    """Fetch current service area config from Netlify."""
    if not NETLIFY_URL:
        return {'error': 'NETLIFY_URL not configured'}
    req = urllib.request.Request(
        f'{NETLIFY_URL}{_ENDPOINT}',
        headers={'Content-Type': 'application/json'},
        method='GET',
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {'error': f'HTTP {e.code}'}
    except Exception as e:
        return {'error': str(e)}


def get_service_area(business_id: str) -> dict:
    """Return the current service area configuration."""
    config = _get_current()
    if 'error' in config:
        return config
    return {
        'mode': config.get('mode', 'zip-list'),
        'centerZip': config.get('centerZip', ''),
        'radiusMiles': config.get('radiusMiles', 30),
        'serviceableZips': config.get('serviceableZips', []),
        'excludedZips': config.get('excludedZips', []),
        'unavailableZips': config.get('unavailableZips', []),
        'updatedAt': config.get('updatedAt', ''),
    }


def update_service_area(business_id: str, updates: dict) -> dict:
    """
    Apply changes to the service area config using read-modify-write.

    Supported update keys:
      mode               — 'radius' or 'zip-list'
      centerZip          — five-digit ZIP string (required for radius mode)
      radiusMiles        — number
      addServiceableZips — list of ZIPs to add to the serviceable list
      removeServiceableZips — list of ZIPs to remove from the serviceable list
      addExcludedZips    — list of ZIPs to permanently block
      removeExcludedZips — list of ZIPs to unblock
      addUnavailableZips — list of ZIPs to temporarily pause
      removeUnavailableZips — list of ZIPs to unpause
    """
    if not NETLIFY_URL:
        return {'error': 'NETLIFY_URL not configured'}

    # Read current state
    current = _get_current()
    if 'error' in current:
        return current

    # Apply scalar updates
    merged = {
        'mode': current.get('mode', 'zip-list'),
        'centerZip': current.get('centerZip', ''),
        'radiusMiles': current.get('radiusMiles', 30),
        'serviceableZips': list(current.get('serviceableZips', [])),
        'excludedZips': list(current.get('excludedZips', [])),
        'unavailableZips': list(current.get('unavailableZips', [])),
    }

    if 'mode' in updates:
        merged['mode'] = updates['mode']
    if 'centerZip' in updates:
        merged['centerZip'] = str(updates['centerZip']).strip()
    if 'radiusMiles' in updates:
        merged['radiusMiles'] = int(updates['radiusMiles'])

    # Apply list mutations
    def add_zips(key, new_zips):
        merged[key] = sorted(set(merged[key]) | set(new_zips))

    def remove_zips(key, del_zips):
        del_set = set(del_zips)
        merged[key] = [z for z in merged[key] if z not in del_set]

    if updates.get('addServiceableZips'):
        add_zips('serviceableZips', updates['addServiceableZips'])
    if updates.get('removeServiceableZips'):
        remove_zips('serviceableZips', updates['removeServiceableZips'])
    if updates.get('addExcludedZips'):
        add_zips('excludedZips', updates['addExcludedZips'])
    if updates.get('removeExcludedZips'):
        remove_zips('excludedZips', updates['removeExcludedZips'])
    if updates.get('addUnavailableZips'):
        add_zips('unavailableZips', updates['addUnavailableZips'])
    if updates.get('removeUnavailableZips'):
        remove_zips('unavailableZips', updates['removeUnavailableZips'])

    # PUT the merged config
    payload = json.dumps(merged).encode()
    req = urllib.request.Request(
        f'{NETLIFY_URL}{_ENDPOINT}',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='PUT',
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            saved = result.get('config', merged)
            return {
                'ok': True,
                'serviceArea': {
                    'mode': saved.get('mode'),
                    'centerZip': saved.get('centerZip'),
                    'radiusMiles': saved.get('radiusMiles'),
                    'serviceableZips': saved.get('serviceableZips', []),
                    'excludedZips': saved.get('excludedZips', []),
                    'unavailableZips': saved.get('unavailableZips', []),
                },
                '_navigate': {'screen': 'Settings', 'section': 'Service Area'},
            }
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        return {'error': f'HTTP {e.code}: {body}'}
    except Exception as e:
        return {'error': str(e)}


# ── Anthropic tool schemas ────────────────────────────────────────────────────

GET_SERVICE_AREA_TOOL = {
    'name': 'get_service_area',
    'description': (
        'Read the current service area configuration: coverage mode (radius or ZIP list), '
        'center ZIP, radius in miles, and the serviceable/excluded/unavailable ZIP lists. '
        'Call this before answering any question about where the contractor takes jobs or '
        'before suggesting changes to coverage.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {},
        'required': [],
    },
}

UPDATE_SERVICE_AREA_TOOL = {
    'name': 'update_service_area',
    'description': (
        'Update the service area configuration. Supports switching modes, setting the '
        'radius center ZIP and miles, and adding or removing ZIPs from the serviceable, '
        'excluded, and unavailable lists. After a successful update the UI will open '
        'Settings > Service Area so the contractor can review the change.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'updates': {
                'type': 'object',
                'description': (
                    'Changes to apply. Supported keys: '
                    'mode (string: "radius" or "zip-list"), '
                    'centerZip (string: five-digit ZIP — required when switching to radius mode), '
                    'radiusMiles (number: how far out to travel), '
                    'addServiceableZips (array of ZIP strings to allow), '
                    'removeServiceableZips (array of ZIP strings to remove), '
                    'addExcludedZips (array of ZIP strings to permanently block), '
                    'removeExcludedZips (array of ZIP strings to unblock), '
                    'addUnavailableZips (array of ZIP strings to temporarily pause), '
                    'removeUnavailableZips (array of ZIP strings to unpause).'
                ),
                'additionalProperties': True,
            },
        },
        'required': ['updates'],
    },
}
