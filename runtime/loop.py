"""
Main agent loop — the only place Anthropic API calls happen.

Haiku path : single-pass, all skill content pre-injected into system prompt.
Sonnet path: tool-use loop (reserved for future agents needing dynamic reasoning).
Stream path: Sonnet with SSE output for the /chat endpoint.
"""

import json
import re
import os
import anthropic
from dataclasses import dataclass
from typing import Optional, Generator
from runtime.registry import AgentDefinition, MODELS, preload_skill_content
from tools.exa_search import exa_search
from tools.work_items import list_work_items, get_work_item_detail
from tools.contractor_actions import (
    send_estimate,
    email_client,
    accept_work,
    reject_work,
    update_work_price,
    add_contractor_note,
)
from tools.agent_tasks import refresh_scope, price_materials, re_estimate_job

# Map tool names to Python callables.
# Work item tools need business_id injected at call time (see _execute_tool).
TOOL_EXECUTORS = {
    'exa_search': lambda inp, _bid: exa_search(inp['query'], inp.get('objective', '')),
    'list_work_items': lambda inp, bid: list_work_items(bid, inp.get('status_filter'), inp.get('limit', 20)),
    'get_work_item_detail': lambda inp, bid: get_work_item_detail(bid, inp['work_item_id']),
    'refresh_scope': lambda inp, bid: refresh_scope(bid, inp['work_item_id'], inp.get('contractor_notes', '')),
    'price_materials': lambda inp, bid: price_materials(bid, inp['work_item_id']),
    're_estimate_job': lambda inp, bid: re_estimate_job(bid, inp['work_item_id']),
    'send_estimate': lambda inp, bid: send_estimate(bid, inp['work_item_id'], inp.get('message', '')),
    'email_client': lambda inp, bid: email_client(bid, inp['work_item_id'], inp['subject'], inp['body']),
    'accept_work': lambda inp, bid: accept_work(bid, inp['work_item_id']),
    'reject_work': lambda inp, bid: reject_work(bid, inp['work_item_id'], inp.get('reason', '')),
    'update_work_price': lambda inp, bid: update_work_price(bid, inp['work_item_id'], inp['new_price'], inp.get('reason_code', '')),
    'add_contractor_note': lambda inp, bid: add_contractor_note(bid, inp['work_item_id'], inp['note']),
}

# Human-readable labels shown in the UI while a tool is running
TOOL_LABELS = {
    'list_work_items': 'Checking your pipeline',
    'get_work_item_detail': 'Looking up job details',
    'refresh_scope': 'Analyzing scope',
    'price_materials': 'Pricing materials',
    're_estimate_job': 'Re-running estimate',
    'send_estimate': 'Sending estimate',
    'email_client': 'Emailing customer',
    'accept_work': 'Accepting job',
    'reject_work': 'Declining job',
    'update_work_price': 'Updating price',
    'add_contractor_note': 'Saving note',
    'exa_search': 'Searching for prices',
}

MAX_ITERATIONS = 12
MAX_TOOL_CALLS = 24

client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])


@dataclass
class AgentResult:
    output: str
    iterations: int
    error: Optional[str] = None


def _execute_tool(name: str, inp: dict, business_id: str = '') -> dict:
    """Execute a tool by name, injecting business_id where needed."""
    executor = TOOL_EXECUTORS.get(name)
    if not executor:
        return {'error': f'Unknown tool: {name}'}
    try:
        return executor(inp, business_id)
    except Exception as e:
        return {'error': str(e)}


def run_agent(agent: AgentDefinition, user_message: str) -> AgentResult:
    """Run an agent against a user message. Returns structured output."""
    skill_content = preload_skill_content(agent.skills)
    system = f"{agent.instructions}\n\n{skill_content}".strip()

    if agent.model == 'haiku':
        return _run_haiku(system, user_message)

    return _run_sonnet(system, user_message, agent)


def _run_haiku(system: str, user_message: str) -> AgentResult:
    try:
        response = client.messages.create(
            model=MODELS['haiku'],
            max_tokens=1024,
            system=system,
            messages=[{'role': 'user', 'content': user_message}],
        )
        output = _extract_text(response.content)
        return AgentResult(output=output, iterations=1)
    except Exception as e:
        return AgentResult(output='', iterations=1, error=str(e))


def _run_sonnet(system: str, user_message: str, agent: AgentDefinition) -> AgentResult:
    """Tool-use loop for Sonnet agents."""
    messages = [{'role': 'user', 'content': user_message}]
    iterations = 0
    tool_calls = 0
    api_tools = agent.tools if agent.tools else anthropic.NOT_GIVEN

    while iterations < MAX_ITERATIONS and tool_calls < MAX_TOOL_CALLS:
        iterations += 1
        try:
            response = client.messages.create(
                model=MODELS['sonnet'],
                max_tokens=4096,
                system=system,
                tools=api_tools,
                messages=messages,
            )
        except Exception as e:
            return AgentResult(output='', iterations=iterations, error=str(e))

        if response.stop_reason != 'tool_use':
            return AgentResult(output=_extract_text(response.content), iterations=iterations)

        # Execute tool calls and feed results back
        messages.append({'role': 'assistant', 'content': response.content})
        tool_results = []
        for block in response.content:
            if block.type != 'tool_use':
                continue
            tool_calls += 1
            result = _execute_tool(block.name, block.input)
            tool_results.append({
                'type': 'tool_result',
                'tool_use_id': block.id,
                'content': json.dumps(result),
            })
        messages.append({'role': 'user', 'content': tool_results})

    return AgentResult(output='', iterations=iterations, error='Max iterations reached')


# ── Streaming path for /chat ───────────────────────────────────────────────────

def run_agent_stream(
    agent: AgentDefinition,
    messages: list[dict],
    business_id: str = '',
) -> Generator[str, None, None]:
    """
    Streaming tool-use loop for the /chat endpoint.

    Yields SSE-formatted strings:
      event: text   — a text token chunk
      event: tool   — a tool is being called (label for the UI)
      event: chips  — JSON array of follow-up chip suggestions (end of response)
      event: done   — signals the stream is complete
    """
    skill_content = preload_skill_content(agent.skills)
    system = f"{agent.instructions}\n\n{skill_content}".strip()
    api_tools = agent.tools if agent.tools else anthropic.NOT_GIVEN

    working_messages = list(messages)
    iterations = 0
    tool_calls = 0
    full_text = ''

    while iterations < MAX_ITERATIONS and tool_calls < MAX_TOOL_CALLS:
        iterations += 1
        accumulated = ''
        tool_uses = []
        stop_reason = 'end_turn'

        try:
            with client.messages.stream(
                model=MODELS['sonnet'],
                max_tokens=4096,
                system=system,
                tools=api_tools,
                messages=working_messages,
            ) as stream:
                for event in stream:
                    if event.type == 'content_block_delta':
                        delta = event.delta
                        if hasattr(delta, 'text'):
                            accumulated += delta.text
                            # Stream text tokens — but buffer the <chips> block
                            # so we don't emit it as visible text.
                            # We detect the opening tag and hold the rest.
                            yield _sse('text', delta.text)
                        elif hasattr(delta, 'partial_json'):
                            # Tool input accumulating — no need to yield
                            pass

                    elif event.type == 'message_stop':
                        pass

                # After stream, get the final message for tool use info
                final = stream.get_final_message()
                stop_reason = final.stop_reason

                for block in final.content:
                    if block.type == 'tool_use':
                        tool_uses.append(block)

        except Exception as e:
            yield _sse('text', f'\n[Error: {e}]')
            yield _sse('done', '')
            return

        full_text += accumulated

        if stop_reason != 'tool_use' or not tool_uses:
            # Stream is done — parse chips out of the accumulated text
            chips = _extract_chips(full_text)
            if chips:
                yield _sse('chips', json.dumps(chips))
            yield _sse('done', '')
            return

        # Execute tool calls, yield tool labels, feed results back
        working_messages.append({'role': 'assistant', 'content': final.content})
        tool_results = []
        for block in tool_uses:
            tool_calls += 1
            label = TOOL_LABELS.get(block.name, block.name)
            yield _sse('tool', label)
            result = _execute_tool(block.name, block.input, business_id)
            tool_results.append({
                'type': 'tool_result',
                'tool_use_id': block.id,
                'content': json.dumps(result),
            })
        working_messages.append({'role': 'user', 'content': tool_results})

    yield _sse('done', '')


def _sse(event: str, data: str) -> str:
    """Format a single SSE event."""
    return f'event: {event}\ndata: {data}\n\n'


def _extract_chips(text: str) -> list[str]:
    """
    Pull the <chips>[...]</chips> block from the agent response text.
    Returns a list of chip strings, or empty list if none found.
    """
    match = re.search(r'<chips>(\[.*?\])</chips>', text, re.DOTALL)
    if not match:
        return []
    try:
        chips = json.loads(match.group(1))
        return chips if isinstance(chips, list) else []
    except json.JSONDecodeError:
        return []


def _extract_text(content: list) -> str:
    return '\n'.join(block.text for block in content if hasattr(block, 'text'))


def parse_json_output(raw: str) -> Optional[dict]:
    """Extract the first JSON object from agent output."""
    match = re.search(r'\{[\s\S]*\}', raw)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
