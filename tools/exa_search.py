"""
Exa AI search tool — Tier 1 material pricing (fast, semantic web search).

Returns page content from relevant sources. The calling agent extracts
price ranges from the text. No structured SKU data — that's Apify (Tier 2).
"""

import os
import httpx

EXA_API_KEY = os.environ.get('EXA_API_KEY', '')
EXA_BASE_URL = 'https://api.exa.ai'

# Anthropic tool schema — registered on agents that need web pricing
EXA_SEARCH_TOOL = {
    'name': 'exa_search',
    'description': (
        'Search the web for material pricing, product specifications, and regional cost data. '
        'Returns page titles, URLs, and text excerpts from relevant sources. '
        'Use specific queries like "2x6x8 pressure treated pine price 2024" or '
        '"composite deck board cost per linear foot Southeast US".'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': 'Specific search query for a material or product price',
            },
            'num_results': {
                'type': 'integer',
                'description': 'Number of results to return (1–8)',
                'default': 5,
            },
        },
        'required': ['query'],
    },
}


def exa_search(query: str, num_results: int = 5) -> list[dict]:
    """Call Exa search API and return title + url + text for each result."""
    if not EXA_API_KEY:
        return [{'error': 'EXA_API_KEY not configured'}]

    try:
        response = httpx.post(
            f'{EXA_BASE_URL}/search',
            headers={'x-api-key': EXA_API_KEY, 'Content-Type': 'application/json'},
            json={
                'query': query,
                'numResults': min(max(1, num_results), 8),
                'type': 'neural',
                'contents': {'text': {'maxCharacters': 800}},
            },
            timeout=10.0,
        )
        response.raise_for_status()
        results = response.json().get('results', [])
        return [
            {
                'title': r.get('title', ''),
                'url': r.get('url', ''),
                'text': r.get('text', ''),
            }
            for r in results
        ]
    except httpx.TimeoutException:
        return [{'error': 'Exa search timed out'}]
    except Exception as e:
        return [{'error': str(e)}]
