"""
Agent and skill registry.

Agents are defined in agents/.
Skills live in skills/<skill-name>/ with a SKILL.md and optional resources/.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


SKILLS_DIR = os.path.join(os.path.dirname(__file__), '..', 'skills')


@dataclass
class SkillManifest:
    name: str
    instructions: str                    # contents of SKILL.md
    resources: dict[str, str] = field(default_factory=dict)  # path -> content


@dataclass
class AgentDefinition:
    id: str
    name: str
    instructions: str
    skills: list[str]
    model: str = 'haiku'                 # 'haiku' | 'sonnet'


# ── Model IDs ────────────────────────────────────────────────────────────────

MODELS = {
    'haiku': 'claude-haiku-4-5-20251001',
    'sonnet': 'claude-sonnet-4-6',
}

# ── Registries ───────────────────────────────────────────────────────────────

_agents: dict[str, AgentDefinition] = {}
_skills: dict[str, SkillManifest] = {}


def register_agent(agent: AgentDefinition) -> None:
    _agents[agent.id] = agent


def get_agent(agent_id: str) -> Optional[AgentDefinition]:
    return _agents.get(agent_id)


def load_skill(skill_name: str) -> SkillManifest:
    """Load a skill's SKILL.md and all files in its resources/ folder."""
    if skill_name in _skills:
        return _skills[skill_name]

    skill_dir = os.path.join(SKILLS_DIR, skill_name)
    skill_md = os.path.join(skill_dir, 'SKILL.md')

    if not os.path.exists(skill_md):
        raise FileNotFoundError(f'SKILL.md not found for skill: {skill_name}')

    with open(skill_md, 'r') as f:
        instructions = f.read()

    resources = {}
    resources_dir = os.path.join(skill_dir, 'resources')
    if os.path.isdir(resources_dir):
        for filename in sorted(os.listdir(resources_dir)):
            filepath = os.path.join(resources_dir, filename)
            if os.path.isfile(filepath):
                with open(filepath, 'r') as f:
                    resources[f'resources/{filename}'] = f.read()

    manifest = SkillManifest(name=skill_name, instructions=instructions, resources=resources)
    _skills[skill_name] = manifest
    return manifest


def preload_skill_content(skill_names: list[str]) -> str:
    """Build a single string of all skill content for Haiku injection."""
    parts = []
    for name in skill_names:
        manifest = load_skill(name)
        parts.append(manifest.instructions)
        for path, content in manifest.resources.items():
            parts.append(f'\n\n---\n# {path}\n\n{content}')
    return '\n\n'.join(parts)
