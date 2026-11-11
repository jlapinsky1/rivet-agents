"""
Work item query tools — read contractor's pipeline from Supabase.

Two tools:
  list_work_items      — summary list, optionally filtered by status
  get_work_item_detail — full detail on a single item
"""

from db.supabase_client import get_work_items_for_business, get_work_item_detail_full


# ── Anthropic tool schemas ────────────────────────────────────────────────────

LIST_WORK_ITEMS_TOOL = {
    'name': 'list_work_items',
    'description': (
        'Fetch the contractor\'s work items from their pipeline. '
        'Returns id, title, operational status, price, customer name, recommendation, '
        'customer email, and days since submission. '
        'Filter by status or leave blank to get all active items.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'status_filter': {
                'type': 'string',
                'description': (
                    'Optional. Filter by opStatus. One of: needs_review, quoted, approved, '
                    'scheduled, in_progress, completed, declined. '
                    'Omit to return all non-completed, non-declined items.'
                ),
            },
            'limit': {
                'type': 'integer',
                'description': 'Max number of items to return. Default 20.',
            },
        },
        'required': [],
    },
}

GET_WORK_ITEM_DETAIL_TOOL = {
    'name': 'get_work_item_detail',
    'description': (
        'Fetch full detail on a specific work item by its id. '
        'Returns all fields including scope analysis, contractor notes, '
        'materials BOM, customer contact info, and job description.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'work_item_id': {
                'type': 'integer',
                'description': 'The numeric id of the work item.',
            },
        },
        'required': ['work_item_id'],
    },
}


# ── Callables ─────────────────────────────────────────────────────────────────

def list_work_items(business_id: str, status_filter: str | None = None, limit: int = 20) -> list[dict]:
    return get_work_items_for_business(business_id, status_filter=status_filter, limit=limit)


def get_work_item_detail(business_id: str, work_item_id: int) -> dict:
    item = get_work_item_detail_full(work_item_id, business_id)
    if not item:
        return {'error': f'Work item {work_item_id} not found'}
    return item
