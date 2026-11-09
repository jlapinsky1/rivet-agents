"""
Exa AI search tool — Tier 1 material pricing (fast, semantic web search).

Uses exa-py SDK. Tool schema includes `objective` as required per Exa's
canonical guidance: an LLM tool that takes only `query` is wrong.
"""

import os
from exa_py import Exa

EXA_API_KEY = os.environ.get('EXA_API_KEY', '')

_client: Exa | None = None


def _get_client() -> Exa:
    global _client
    if _client is None:
        _client = Exa(api_key=EXA_API_KEY)
    return _client


# Anthropic tool schema — `objective` is required alongside `query`
# so the model tells Exa which results should rank first and what to extract.
EXA_SEARCH_TOOL = {
    'name': 'exa_search',
    'description': (
        'Search the live web and return the most relevant URLs and content. '
        'Use for current material prices, product specs, and regional cost data.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': 'Natural-language search query for the material or product',
            },
            'objective': {
                'type': 'string',
                'description': (
                    'Goal for this search turn; say which documents should rank first, '
                    'which should be excluded, and what specific facts or figures to pull from them.'
                ),
            },
        },
        'required': ['query', 'objective'],
    },
}


def exa_search(query: str, objective: str = '') -> list[dict]:
    """Call Exa search and return highlights + source info per result."""
    if not EXA_API_KEY:
        return [{'error': 'EXA_API_KEY not configured'}]

    try:
        exa = _get_client()
        result = exa.search(
            query,
            objective=objective or None,
            contents={'highlights': True},
        )
        return [
            {
                'title': r.title or '',
                'url': r.url or '',
                'highlights': r.highlights or [],
            }
            for r in result.results
        ]
    except Exception as e:
        return [{'error': str(e)}]
