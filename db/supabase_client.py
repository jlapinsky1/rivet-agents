"""
Supabase client — service role, used for server-side reads/writes.
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
