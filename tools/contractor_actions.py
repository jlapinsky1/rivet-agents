"""
Contractor action tools — mutations on work items and outbound communications.

Tools:
  send_estimate        — mark item as quoted and email the customer their quote link
  email_client         — send a free-form email to the customer
  accept_work          — set opStatus to approved
  reject_work          — set opStatus to declined
  update_work_price    — write a new price to a work item
  add_contractor_note  — append or replace the contractor note on a work item
"""

import os
import json
import logging
from db.supabase_client import (
    get_client,
    save_contractor_notes,
)

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
RESEND_FROM_EMAIL = os.environ.get('RESEND_FROM_EMAIL', 'noreply@rivet.app')
SITE_URL = os.environ.get('SITE_URL', '')


# ── Helpers ───────────────────────────────────────────────────────────────────

def _update_work_item(work_item_id: int, business_id: str, fields: dict) -> dict:
    """Generic Supabase update. Returns {'ok': True} or {'error': str}."""
    try:
        client = get_client()
        client.table('work_items').update(fields).eq('id', work_item_id).eq('business_id', business_id).execute()
        return {'ok': True}
    except Exception as e:
        logger.exception('work_item update failed')
        return {'error': str(e)}


def _send_email(to: str, subject: str, html: str) -> dict:
    """Send via Resend. Returns {'ok': True} or {'error': str}."""
    if not RESEND_API_KEY:
        return {'error': 'RESEND_API_KEY not configured'}
    if not to:
        return {'error': 'No customer email on file'}

    import urllib.request
    payload = json.dumps({
        'from': f'Rivet <{RESEND_FROM_EMAIL}>',
        'to': [to],
        'subject': subject,
        'html': html,
    }).encode()

    req = urllib.request.Request(
        'https://api.resend.com/emails',
        data=payload,
        headers={
            'Authorization': f'Bearer {RESEND_API_KEY}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {'ok': True, 'resend_id': json.loads(resp.read()).get('id')}
    except Exception as e:
        return {'error': str(e)}


def _load_customer_email(work_item_id: int, business_id: str) -> str:
    """Pull email field from work_items."""
    try:
        client = get_client()
        res = (
            client.table('work_items')
            .select('email, customer_name, title, price')
            .eq('id', work_item_id)
            .eq('business_id', business_id)
            .single()
            .execute()
        )
        return res.data or {}
    except Exception:
        return {}


# ── Callables ─────────────────────────────────────────────────────────────────

def send_estimate(business_id: str, work_item_id: int, message: str = '') -> dict:
    """Mark work item as quoted and email the customer their estimate."""
    info = _load_customer_email(work_item_id, business_id)
    if isinstance(info, dict) and 'error' in info:
        return info

    customer_email = info.get('email', '')
    customer_name = info.get('customer_name', 'there')
    title = info.get('title', 'your job')
    price = info.get('price')

    # Update status to quoted
    result = _update_work_item(work_item_id, business_id, {'op_status': 'quoted'})
    if 'error' in result:
        return result

    # Email the customer
    first_name = customer_name.split(' ')[0] if customer_name else 'there'
    price_str = f'${price:,.0f}' if price else 'being finalized'
    quote_url = f'{SITE_URL}/quote/{work_item_id}' if SITE_URL else ''

    body_lines = [
        f'<p>Hi {first_name},</p>',
        f'<p>Your estimate for <strong>{title}</strong> is ready.</p>',
        f'<p>Estimated price: <strong>{price_str}</strong></p>',
    ]
    if message:
        body_lines.append(f'<p>{message}</p>')
    if quote_url:
        body_lines.append(
            f'<p><a href="{quote_url}" style="background:#2e7d5a;color:#fff;padding:10px 20px;'
            f'border-radius:8px;text-decoration:none;display:inline-block;">View Your Estimate</a></p>'
        )
    body_lines.append('<p>Reply to this email with any questions.</p>')

    email_result = _send_email(
        to=customer_email,
        subject=f'Your estimate is ready - {title}',
        html=''.join(body_lines),
    )

    return {**result, 'email': email_result, 'customer_email': customer_email}


def email_client(business_id: str, work_item_id: int, subject: str, body: str) -> dict:
    """Send a free-form email to the customer for a given work item."""
    info = _load_customer_email(work_item_id, business_id)
    if isinstance(info, dict) and 'error' in info:
        return info

    customer_email = info.get('email', '')
    html = body.replace('\n', '<br>')
    return _send_email(to=customer_email, subject=subject, html=html)


def accept_work(business_id: str, work_item_id: int) -> dict:
    """Set the work item status to approved."""
    return _update_work_item(work_item_id, business_id, {'op_status': 'approved'})


def reject_work(business_id: str, work_item_id: int, reason: str = '') -> dict:
    """Set the work item status to declined, optionally recording a reason."""
    fields: dict = {'op_status': 'declined'}
    if reason:
        # Append reason to contractor notes
        try:
            client = get_client()
            res = (
                client.table('work_items')
                .select('contractor_notes')
                .eq('id', work_item_id)
                .eq('business_id', business_id)
                .single()
                .execute()
            )
            existing = res.data.get('contractor_notes') or ''
            combined = f'{existing}\nDeclined: {reason}'.strip() if existing else f'Declined: {reason}'
            fields['contractor_notes'] = combined
        except Exception:
            pass
    return _update_work_item(work_item_id, business_id, fields)


def update_work_price(business_id: str, work_item_id: int, new_price: float, reason_code: str = '') -> dict:
    """Write a new price to the work item, optionally recording the reason for calibration."""
    result = _update_work_item(work_item_id, business_id, {'price': new_price})
    if reason_code and 'ok' in result:
        # Append reason to contractor notes so it appears in the UI and audit trail
        try:
            client = get_client()
            res = (
                client.table('work_items')
                .select('contractor_notes')
                .eq('id', work_item_id)
                .eq('business_id', business_id)
                .single()
                .execute()
            )
            existing = res.data.get('contractor_notes') or ''
            note = f'Price changed to ${new_price:,.0f} — reason: {reason_code}'
            combined = f'{existing}\n{note}'.strip() if existing else note
            save_contractor_notes(work_item_id, business_id, combined)
        except Exception:
            pass
    return result


def add_contractor_note(business_id: str, work_item_id: int, note: str) -> dict:
    """Append a note to the work item's contractor_notes field."""
    try:
        client = get_client()
        res = (
            client.table('work_items')
            .select('contractor_notes')
            .eq('id', work_item_id)
            .eq('business_id', business_id)
            .single()
            .execute()
        )
        existing = res.data.get('contractor_notes') or ''
        combined = f'{existing}\n{note}'.strip() if existing else note
        save_contractor_notes(work_item_id, business_id, combined)
        return {'ok': True}
    except Exception as e:
        return {'error': str(e)}


# ── Anthropic tool schemas ────────────────────────────────────────────────────

SEND_ESTIMATE_TOOL = {
    'name': 'send_estimate',
    'description': (
        'Mark a work item as quoted and email the customer their estimate. '
        'Only call this after confirming with the contractor.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'work_item_id': {'type': 'integer', 'description': 'The work item id.'},
            'message': {'type': 'string', 'description': 'Optional personal note to include in the email.'},
        },
        'required': ['work_item_id'],
    },
}

EMAIL_CLIENT_TOOL = {
    'name': 'email_client',
    'description': (
        'Send a free-form email to the customer for a specific work item. '
        'Use for follow-up questions, clarifications, or status updates. '
        'Only call after confirming the message content with the contractor.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'work_item_id': {'type': 'integer', 'description': 'The work item id.'},
            'subject': {'type': 'string', 'description': 'Email subject line.'},
            'body': {'type': 'string', 'description': 'Plain text email body. Keep it concise and professional.'},
        },
        'required': ['work_item_id', 'subject', 'body'],
    },
}

ACCEPT_WORK_TOOL = {
    'name': 'accept_work',
    'description': 'Mark a work item as approved. Use when the contractor decides to take the job.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'work_item_id': {'type': 'integer', 'description': 'The work item id.'},
        },
        'required': ['work_item_id'],
    },
}

REJECT_WORK_TOOL = {
    'name': 'reject_work',
    'description': 'Mark a work item as declined. Use when the contractor decides to pass on the job.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'work_item_id': {'type': 'integer', 'description': 'The work item id.'},
            'reason': {'type': 'string', 'description': 'Optional reason for declining (saved as a note).'},
        },
        'required': ['work_item_id'],
    },
}

UPDATE_WORK_PRICE_TOOL = {
    'name': 'update_work_price',
    'description': (
        'Update the price on a work item with the contractor\'s own figure. '
        'Use when the contractor wants to override the system estimate. '
        'Include a reason_code when the contractor explains why they changed it.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'work_item_id': {'type': 'integer', 'description': 'The work item id.'},
            'new_price': {'type': 'number', 'description': 'The new price in dollars (e.g. 850 for $850).'},
            'reason_code': {
                'type': 'string',
                'description': (
                    'Optional. Why the price was changed. One of: SYSTEM_TOO_LOW, SYSTEM_TOO_HIGH, '
                    'SCOPE_CHANGED, NEW_CUSTOMER_INFO, OWNER_EXPERIENCE, MATERIAL_COST_DIFFERENT, '
                    'SITE_CONDITION_DIFFERENT, OTHER.'
                ),
            },
        },
        'required': ['work_item_id', 'new_price'],
    },
}

ADD_CONTRACTOR_NOTE_TOOL = {
    'name': 'add_contractor_note',
    'description': 'Append a note to a work item. Use to record reasoning, pricing decisions, or customer context.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'work_item_id': {'type': 'integer', 'description': 'The work item id.'},
            'note': {'type': 'string', 'description': 'The note text to append.'},
        },
        'required': ['work_item_id', 'note'],
    },
}
