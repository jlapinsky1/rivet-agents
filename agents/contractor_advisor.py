"""
Contractor Advisor agent.

Conversational agent that helps contractors manage their pipeline through natural
language: reviewing jobs, sending estimates, emailing clients, adjusting pricing,
running scope analysis, pricing materials, re-estimating, and accepting or rejecting work.

Uses Sonnet (tool-use loop) so it can query the pipeline and take actions.
"""

from runtime.registry import AgentDefinition, register_agent
from tools.work_items import LIST_WORK_ITEMS_TOOL, GET_WORK_ITEM_DETAIL_TOOL
from tools.contractor_actions import (
    SEND_ESTIMATE_TOOL,
    EMAIL_CLIENT_TOOL,
    ACCEPT_WORK_TOOL,
    REJECT_WORK_TOOL,
    UPDATE_WORK_PRICE_TOOL,
    ADD_CONTRACTOR_NOTE_TOOL,
)
from tools.agent_tasks import (
    REFRESH_SCOPE_TOOL,
    PRICE_MATERIALS_TOOL,
    RE_ESTIMATE_JOB_TOOL,
)

contractor_advisor = AgentDefinition(
    id='contractor-advisor',
    name='Contractor Advisor',
    instructions=(
        'You are Ask Rivet, a conversational assistant for contractors. '
        'Help them manage their pipeline: review incoming jobs, analyze scope, '
        'price materials, send estimates, follow up with customers, adjust pricing, '
        'and accept or decline work. '
        'All behavior guidance is in the contractor-advisor skill.'
    ),
    skills=['contractor-advisor'],
    model='sonnet',
    tools=[
        LIST_WORK_ITEMS_TOOL,
        GET_WORK_ITEM_DETAIL_TOOL,
        REFRESH_SCOPE_TOOL,
        PRICE_MATERIALS_TOOL,
        RE_ESTIMATE_JOB_TOOL,
        SEND_ESTIMATE_TOOL,
        EMAIL_CLIENT_TOOL,
        ACCEPT_WORK_TOOL,
        REJECT_WORK_TOOL,
        UPDATE_WORK_PRICE_TOOL,
        ADD_CONTRACTOR_NOTE_TOOL,
    ],
)

register_agent(contractor_advisor)
