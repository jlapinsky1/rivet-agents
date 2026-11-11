"""
Agent task tools — invoke other agents or backend tasks from within the contractor advisor.

Tools:
  refresh_scope      — run the job-advisor agent to generate scope questions / readyToQuote
  price_materials    — run the material-pricer agent to generate a BOM with Exa-sourced prices
  re_estimate_job    — call the re-estimate Netlify function to refresh price + recommendation
"""

import os
import json
import logging
import urllib.request
from db.supabase_client import (
    get_work_item,
    save_scope_analysis,
    save_contractor_notes,
)

logger = logging.getLogger(__name__)

NETLIFY_URL = os.environ.get('NETLIFY_URL', '')


# ── Callables ─────────────────────────────────────────────────────────────────

def refresh_scope(business_id: str, work_item_id: int, contractor_notes: str = '') -> dict:
    """
    Run the job-advisor agent against a specific work item.
    Saves contractor notes first if provided, then returns updated scope analysis.
    """
    # Import here to avoid circular imports at module load time
    from runtime.loop import run_agent, parse_json_output
    from runtime.registry import get_agent

    if contractor_notes:
        save_contractor_notes(work_item_id, business_id, contractor_notes)

    item = get_work_item(work_item_id, business_id)
    if not item:
        return {'error': f'Work item {work_item_id} not found'}

    lines = [f"Job: {item['title']}"]
    if item.get('description'):
        lines.append(f"Customer description: {item['description']}")
    notes = item.get('customer_notes')
    if notes and notes != item.get('description'):
        lines.append(f"Additional notes: {notes}")
    photos = item.get('photos') or []
    lines.append(f"Photos submitted: {len(photos)}")
    cn = contractor_notes or item.get('contractor_notes')
    if cn:
        lines.append(f"Contractor follow-up notes: {cn}")

    agent = get_agent('job-advisor')
    if not agent:
        return {'error': 'job-advisor agent not found'}

    try:
        result = run_agent(agent, '\n'.join(lines))
    except Exception as e:
        return {'error': str(e)}

    parsed = parse_json_output(result.output)
    if not parsed:
        parsed = {'readyToQuote': False, 'questions': [], 'context': result.output}
    if not isinstance(parsed.get('questions'), list):
        parsed['questions'] = []

    save_scope_analysis(work_item_id, business_id, parsed)
    return {'scopeAnalysis': parsed}


def price_materials(business_id: str, work_item_id: int) -> dict:
    """
    Run the material-pricer agent to generate a Bill of Materials with live price ranges.
    Returns the BOM. This can take 30+ seconds for new jobs (uses Exa AI search).
    """
    from runtime.loop import run_agent, parse_json_output
    from runtime.registry import get_agent
    from db.supabase_client import get_work_item_for_pricing, save_materials_bom

    item = get_work_item_for_pricing(work_item_id, business_id)
    if not item:
        return {'error': f'Work item {work_item_id} not found'}

    # Return cached BOM if already priced
    if item.get('materials_bom'):
        return {'bom': item['materials_bom'], 'cached': True}

    lines = [f"Job: {item['title']}"]
    if item.get('description'):
        lines.append(f"Customer description: {item['description']}")
    if item.get('customer_notes') and item['customer_notes'] != item.get('description'):
        lines.append(f"Customer notes: {item['customer_notes']}")
    if item.get('contractor_notes'):
        lines.append(f"Contractor notes: {item['contractor_notes']}")
    if item.get('address'):
        lines.append(f"Customer location: {item['address']}")

    agent = get_agent('material-pricer')
    if not agent:
        return {'error': 'material-pricer agent not found'}

    try:
        result = run_agent(agent, '\n'.join(lines))
    except Exception as e:
        return {'error': str(e)}

    bom = parse_json_output(result.output)
    if not bom:
        return {'error': 'Agent did not return valid BOM'}

    save_materials_bom(work_item_id, business_id, bom)
    return {'bom': bom}


def re_estimate_job(business_id: str, work_item_id: int) -> dict:
    """
    Re-run the estimator to refresh the price and recommendation.
    This incorporates any updated contractor notes, scope analysis, and materials BOM.
    Requires NETLIFY_URL environment variable.
    """
    if not NETLIFY_URL:
        return {'error': 'NETLIFY_URL not configured — cannot re-estimate'}

    payload = json.dumps({'workItemId': work_item_id, 'businessId': business_id}).encode()
    req = urllib.request.Request(
        f'{NETLIFY_URL}/api/re-estimate-job',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data
    except urllib.error.HTTPError as e:
        return {'error': f'Re-estimate failed: HTTP {e.code}'}
    except Exception as e:
        return {'error': str(e)}


# ── Anthropic tool schemas ────────────────────────────────────────────────────

REFRESH_SCOPE_TOOL = {
    'name': 'refresh_scope',
    'description': (
        'Run the AI scope analyzer on a specific work item. '
        'Returns clarifying questions if more info is needed, or confirms the job is ready to quote. '
        'Use when a contractor wants to understand what is missing before pricing a job, '
        'or when they have added new notes and want the analysis refreshed.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'work_item_id': {'type': 'integer', 'description': 'The work item id.'},
            'contractor_notes': {
                'type': 'string',
                'description': 'Optional notes from the contractor to include before analyzing.',
            },
        },
        'required': ['work_item_id'],
    },
}

PRICE_MATERIALS_TOOL = {
    'name': 'price_materials',
    'description': (
        'Generate a Bill of Materials with live price ranges for a job. '
        'Uses AI to search current material prices. '
        'Takes 20-40 seconds for new jobs. Returns a BOM immediately if one is already cached. '
        'Use when a contractor asks to price out materials, generate a BOM, or see material costs.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'work_item_id': {'type': 'integer', 'description': 'The work item id.'},
        },
        'required': ['work_item_id'],
    },
}

RE_ESTIMATE_JOB_TOOL = {
    'name': 're_estimate_job',
    'description': (
        'Re-run the estimator on a job to refresh its recommended price and recommendation rating. '
        'The estimator incorporates any updated contractor notes, scope analysis, and materials BOM. '
        'Use after scope is refreshed and returns readyToQuote=true, or after the BOM is priced.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'work_item_id': {'type': 'integer', 'description': 'The work item id.'},
        },
        'required': ['work_item_id'],
    },
}
