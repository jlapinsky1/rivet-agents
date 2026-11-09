"""
Main agent loop — the only place Anthropic API calls happen.

Haiku path : single-pass, all skill content pre-injected into system prompt.
Sonnet path: tool-use loop (reserved for future agents needing dynamic reasoning).
"""

import json
import re
import os
import anthropic
from dataclasses import dataclass
from typing import Optional
from runtime.registry import AgentDefinition, MODELS, preload_skill_content
from tools.exa_search import exa_search

# Map tool names to Python callables
TOOL_EXECUTORS = {
    'exa_search': lambda inp: exa_search(inp['query'], inp.get('num_results', 5)),
}


MAX_ITERATIONS = 12
MAX_TOOL_CALLS = 24

client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])


@dataclass
class AgentResult:
    output: str
    iterations: int
    error: Optional[str] = None


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
            executor = TOOL_EXECUTORS.get(block.name)
            if executor:
                try:
                    result = executor(block.input)
                except Exception as e:
                    result = {'error': str(e)}
            else:
                result = {'error': f'Unknown tool: {block.name}'}
            tool_results.append({
                'type': 'tool_result',
                'tool_use_id': block.id,
                'content': json.dumps(result),
            })
        messages.append({'role': 'user', 'content': tool_results})

    return AgentResult(output='', iterations=iterations, error='Max iterations reached')


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
