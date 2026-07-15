"""Built-in Pico skills.

Skills are lightweight prompt profiles. They do not add new tools by
themselves; they give the agent a repeatable workflow for a task family.
"""

from dataclasses import dataclass

from . import repo_map


@dataclass(frozen=True)
class Skill:
    name: str
    title: str
    description: str
    instructions: str


BUILTIN_SKILLS = {
    repo_map.NAME: Skill(
        name=repo_map.NAME,
        title=repo_map.TITLE,
        description=repo_map.DESCRIPTION,
        instructions=repo_map.INSTRUCTIONS,
    ),
}


def normalize_skill_name(name):
    return str(name or "").strip().lower().replace("_", "-")


def list_skills():
    return [BUILTIN_SKILLS[name] for name in sorted(BUILTIN_SKILLS)]


def get_skill(name):
    normalized = normalize_skill_name(name)
    if not normalized:
        return None
    return BUILTIN_SKILLS.get(normalized)


def require_skill(name):
    skill = get_skill(name)
    if skill is None:
        known = ", ".join(sorted(BUILTIN_SKILLS)) or "(none)"
        raise ValueError(f"unknown skill: {name}. available skills: {known}")
    return skill


def render_skill_list(active_skill_name=""):
    active = normalize_skill_name(active_skill_name)
    lines = ["Available skills:"]
    if not BUILTIN_SKILLS:
        lines.append("- none")
        return "\n".join(lines)
    for skill in list_skills():
        marker = "*" if skill.name == active else " "
        lines.append(f"{marker} {skill.name}: {skill.description}")
    lines.append("Use `/skills <name>` to activate one, or `/skills none` to clear it.")
    return "\n".join(lines)


__all__ = [
    "BUILTIN_SKILLS",
    "Skill",
    "get_skill",
    "list_skills",
    "normalize_skill_name",
    "render_skill_list",
    "require_skill",
]
