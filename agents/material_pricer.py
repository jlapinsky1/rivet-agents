"""
Material Pricer agent.

Task  : price-materials
Model : Sonnet (tool-use loop — calls exa_search per material line item)
Skill : material-pricer
Goal  : Given a job description + extracted context, build a Bill of Materials
        with real web-sourced price ranges via Exa AI.
"""

from runtime.registry import AgentDefinition, register_agent
from tools.exa_search import EXA_SEARCH_TOOL

material_pricer = AgentDefinition(
    id='material-pricer',
    name='Material Pricer',
    instructions=(
        'You are a materials estimator for a handyman business. '
        'Given a job description, identify every material that needs to be purchased, '
        'search for real current prices using the exa_search tool, '
        'and return a structured Bill of Materials as a single JSON object. '
        'Load and follow the material-pricer skill instructions exactly. '
        'Return ONLY valid JSON. No text before or after.'
    ),
    skills=['material-pricer'],
    model='sonnet',
    tools=[EXA_SEARCH_TOOL],
)

register_agent(material_pricer)
