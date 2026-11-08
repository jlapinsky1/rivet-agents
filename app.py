"""
Rivet Agents — FastAPI service

POST /agent
  Body: { task, businessId, ...taskInput }

Adding a new agent:
  1. Create agents/<name>.py and call register_agent()
  2. Add a task case in the router below
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# Bootstrap agent registrations
import agents.job_advisor  # noqa: F401

from runtime.registry import get_agent
from runtime.loop import run_agent, parse_json_output
from db.supabase_client import (
    get_work_item,
    save_scope_analysis,
    save_contractor_notes,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title='Rivet Agents', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['POST', 'GET'],
    allow_headers=['Content-Type'],
)


def err(msg: str, status: int = 400) -> JSONResponse:
    return JSONResponse({'error': msg}, status_code=status)


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.post('/agent')
async def agent_router(request: Request):
    try:
        body = await request.json()
    except Exception:
        return err('Invalid JSON body')

    task = body.get('task')
    business_id = body.get('businessId')

    if not task:
        return err('task is required')
    if not business_id:
        return err('businessId is required')

    # ── refresh-scope ─────────────────────────────────────────────────────────
    # Saves contractor notes (if provided), runs job-advisor, persists scope_analysis.
    if task == 'refresh-scope':
        work_item_id = body.get('workItemId')
        contractor_notes = body.get('contractorNotes')

        if not work_item_id:
            return err('workItemId is required')

        # Persist notes first if provided
        if isinstance(contractor_notes, str):
            save_contractor_notes(work_item_id, business_id, contractor_notes)

        # Fetch work item
        item = get_work_item(work_item_id, business_id)
        if not item:
            return err('Work item not found', 404)

        # Build agent message
        lines = [f"Job: {item['title']}"]
        if item.get('description'):
            lines.append(f"Customer description: {item['description']}")
        notes = item.get('customer_notes')
        if notes and notes != item.get('description'):
            lines.append(f"Additional notes: {notes}")
        photos = item.get('photos') or []
        lines.append(f"Photos submitted: {len(photos)}")
        cn = contractor_notes if isinstance(contractor_notes, str) else item.get('contractor_notes')
        if cn:
            lines.append(f"Contractor follow-up notes: {cn}")

        agent = get_agent('job-advisor')
        if not agent:
            return err('Agent not found', 500)

        try:
            result = run_agent(agent, '\n'.join(lines))
        except Exception as e:
            return err(f'Agent error: {e}', 500)

        if result.error and not result.output:
            return err(f'Agent error: {result.error}', 500)

        parsed = parse_json_output(result.output)
        if not parsed:
            parsed = {'readyToQuote': False, 'questions': [], 'context': result.output}
        if not isinstance(parsed.get('questions'), list):
            parsed['questions'] = []

        # Persist and return
        save_scope_analysis(work_item_id, business_id, parsed)
        return JSONResponse({
            'scopeAnalysis': parsed,
            'contractorNotes': cn or '',
        })

    return err(f'Unknown task: {task}')
