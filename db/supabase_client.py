"""
Supabase client — service role, used for server-side reads/writes.

Migration required (run once in Supabase SQL editor):

    create table contractor_conversations (
      id uuid primary key default gen_random_uuid(),
      business_id text not null,
      messages jsonb not null default '[]',
      created_at timestamptz default now(),
      updated_at timestamptz default now()
    );
    create index on contractor_conversations(business_id);
"""

import os
from supabase import create_client, Client

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ['SUPABASE_URL']
        key = os.environ['SUPABASE_SERVICE_KEY']
        _client = create_client(url, key)
    return _client


# ── Work items ────────────────────────────────────────────────────────────────

def get_work_item(work_item_id: int, business_id: str) -> dict | None:
    client = get_client()
    res = (
        client.table('work_items')
        .select('title, description, customer_notes, photos, contractor_notes')
        .eq('id', work_item_id)
        .eq('business_id', business_id)
        .single()
        .execute()
    )
    return res.data


def get_work_item_for_pricing(work_item_id: int, business_id: str) -> dict | None:
    """Fetch job context needed for material pricing, including address for regional pricing."""
    client = get_client()
    res = (
        client.table('work_items')
        .select('title, description, customer_notes, contractor_notes, address, materials_bom')
        .eq('id', work_item_id)
        .eq('business_id', business_id)
        .single()
        .execute()
    )
    return res.data


def get_work_item_detail_full(work_item_id: int, business_id: str) -> dict | None:
    """Full detail for the contractor advisor agent."""
    client = get_client()
    res = (
        client.table('work_items')
        .select(
            'id, title, description, customer_notes, contractor_notes, '
            'photos, address, price, op_status, recommendation, '
            'email, phone, customer_name, scope_analysis, materials_bom, '
            'created_at, preferred_date'
        )
        .eq('id', work_item_id)
        .eq('business_id', business_id)
        .single()
        .execute()
    )
    return res.data


def get_work_items_for_business(
    business_id: str,
    status_filter: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """
    Return a summary list of work items for the contractor advisor.
    Excludes completed and declined by default unless explicitly requested.
    """
    client = get_client()
    query = (
        client.table('work_items')
        .select(
            'id, title, op_status, price, customer_name, email, '
            'recommendation, created_at, scope_analysis'
        )
        .eq('business_id', business_id)
        .order('created_at', desc=True)
        .limit(limit)
    )

    if status_filter:
        query = query.eq('op_status', status_filter)
    else:
        # Default: exclude terminal states
        query = query.not_.in_('op_status', ['completed', 'declined'])

    res = query.execute()
    return res.data or []


# ── Scope + notes ─────────────────────────────────────────────────────────────

def save_materials_bom(work_item_id: int, business_id: str, bom: dict) -> None:
    client = get_client()
    client.table('work_items').update(
        {'materials_bom': bom}
    ).eq('id', work_item_id).eq('business_id', business_id).execute()


def save_scope_analysis(work_item_id: int, business_id: str, scope_analysis: dict) -> None:
    client = get_client()
    client.table('work_items').update(
        {'scope_analysis': scope_analysis}
    ).eq('id', work_item_id).eq('business_id', business_id).execute()


def save_contractor_notes(work_item_id: int, business_id: str, notes: str) -> None:
    client = get_client()
    client.table('work_items').update(
        {'contractor_notes': notes}
    ).eq('id', work_item_id).eq('business_id', business_id).execute()


# ── Conversations ─────────────────────────────────────────────────────────────

def get_conversation(conversation_id: str, business_id: str) -> dict | None:
    """Load a saved conversation by id. Returns None if not found."""
    client = get_client()
    res = (
        client.table('contractor_conversations')
        .select('id, messages')
        .eq('id', conversation_id)
        .eq('business_id', business_id)
        .single()
        .execute()
    )
    return res.data


def upsert_conversation(
    conversation_id: str | None,
    business_id: str,
    messages: list[dict],
) -> str:
    """
    Save or update a conversation. Returns the conversation id.
    If conversation_id is None, creates a new row.
    """
    import datetime
    client = get_client()
    now = datetime.datetime.utcnow().isoformat()

    if conversation_id:
        client.table('contractor_conversations').update({
            'messages': messages,
            'updated_at': now,
        }).eq('id', conversation_id).eq('business_id', business_id).execute()
        return conversation_id
    else:
        res = client.table('contractor_conversations').insert({
            'business_id': business_id,
            'messages': messages,
        }).execute()
        return res.data[0]['id']
