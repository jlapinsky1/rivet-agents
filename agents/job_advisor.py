"""
Job Advisor agent.

Task   : refresh-scope
Model  : Haiku (single-pass, no tool use)
Skills : scope-clarifier
Goal   : Determine if a job has enough info to quote. If yes, say so.
         If no, surface the minimum questions needed to get there.
"""

from runtime.registry import AgentDefinition, register_agent

job_advisor = AgentDefinition(
    id='job-advisor',
    name='Job Advisor',
    instructions=(
        'You are a consultant reviewing incoming job requests on behalf of a handyman contractor. '
        'Your primary goal is to determine whether a job has enough information to quote. '
        'Load the scope-clarifier skill, assess the job, and return a JSON object with '
        '"readyToQuote" (boolean), "questions" (array of 0-4 strings), and "context" '
        '(1-2 sentence assessment). '
        'Return ONLY valid JSON. No text before or after.'
    ),
    skills=['scope-clarifier'],
    model='haiku',
)

register_agent(job_advisor)
