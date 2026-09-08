import json
import os
from typing import Any, Dict

from openai import OpenAI

from prompts import (
    STAGE_1_SYSTEM,
    STAGE_1_USER,
    STAGE_2_SYSTEM,
    STAGE_2_USER,
    STAGE_3_SYSTEM,
    STAGE_3_USER,
)


class WorkflowError(Exception):
    """Raised when an AI workflow stage fails."""


MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise WorkflowError(
            "OPENAI_API_KEY is missing. Add it to Streamlit Secrets."
        )
    return OpenAI(api_key=api_key)


def _call_ai(system_prompt: str, user_prompt: str) -> str:
    try:
        response = _client().chat.completions.create(
            model=MODEL,
            temperature=0.4,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content.strip()
    except WorkflowError:
        raise
    except Exception as exc:
        raise WorkflowError(f"AI request failed: {exc}") from exc


def _json(text: str) -> Dict[str, Any]:
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        lines = [
            line for line in lines
            if not line.strip().startswith("```")
        ]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise WorkflowError(
            "The AI returned invalid JSON. Please generate the pack again."
        ) from exc


def stage_1_plan_and_generate(
    topic: str,
    level: str,
    goals: str,
    study_time: str,
    preferences: str,
) -> Dict[str, Any]:
    """Stage 1: Understand the learner, plan the material, and generate content."""

    prompt = STAGE_1_USER.format(
        topic=topic,
        level=level,
        goals=goals or "Not specified",
        study_time=study_time or "Not specified",
        preferences=preferences or "Not specified",
    )

    return _json(_call_ai(STAGE_1_SYSTEM, prompt))


def stage_2_assess_and_review(
    stage_1_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Stage 2: Assess generated content and perform quality review."""

    prompt = STAGE_2_USER.format(
        stage_1_context=json.dumps(stage_1_context, indent=2)
    )

    return _json(_call_ai(STAGE_2_SYSTEM, prompt))


def stage_3_refine(
    stage_1_context: Dict[str, Any],
    stage_2_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Stage 3: Refine the complete study pack using review feedback."""

    prompt = STAGE_3_USER.format(
        stage_1_context=json.dumps(stage_1_context, indent=2),
        stage_2_context=json.dumps(stage_2_context, indent=2),
    )

    return _json(_call_ai(STAGE_3_SYSTEM, prompt))


def to_markdown(result: Dict[str, Any]) -> str:
    if result["status"] == "failed":
        return (
            f"# Workflow Failed\n\n"
            f"**Stage:** {result.get('failed_stage')}\n\n"
            f"**Error:** {result.get('error')}"
        )

    pack = result["final_pack"]

    lines = [
        f"# {pack.get('title', 'Personalized Study Pack')}",
        "",
        "## Learning Objectives",
    ]

    for item in pack.get("learning_objectives", []):
        lines.append(f"- {item}")

    lines.extend(["", "## Study Notes"])
    notes = pack.get("study_notes", [])
    if isinstance(notes, str):
        lines.append(notes)
    else:
        for note in notes:
            lines.append(f"- {note}")

    lines.extend(["", "## Worked Examples"])
    for example in pack.get("worked_examples", []):
        lines.append(f"- {example}")

    lines.extend(["", "## Practice Questions"])
    for i, question in enumerate(pack.get("practice_questions", []), 1):
        if isinstance(question, dict):
            lines.append(f"**{i}. {question.get('question', '')}**")
            for option in question.get("options", []):
                lines.append(f"- {option}")
        else:
            lines.append(f"**{i}. {question}**")

    lines.extend(["", "## Answer Key"])
    for answer in pack.get("answer_key", []):
        lines.append(f"- {answer}")

    lines.extend(["", "## Revision Plan"])
    for item in pack.get("revision_plan", []):
        lines.append(f"- {item}")

    return "\n".join(lines)


def generate_study_pack(
    topic: str,
    level: str,
    goals: str,
    study_time: str,
    preferences: str,
) -> Dict[str, Any]:
    """
    Main 3-stage workflow orchestrator.

    Context flow:
    User Input
       ↓
    Stage 1: Plan + Generate
       ↓ context passing
    Stage 2: Assess + Review
       ↓ context + feedback
    Stage 3: Refine
       ↓
    Final Study Pack

    Any stage failure is captured and returned safely to the UI.
    """

    if not topic.strip():
        return {
            "status": "failed",
            "failed_stage": "input_validation",
            "error": "Topic is required.",
        }

    result: Dict[str, Any] = {
        "status": "running",
        "stages": {},
    }

    try:
        result["stages"]["stage_1"] = stage_1_plan_and_generate(
            topic,
            level,
            goals,
            study_time,
            preferences,
        )
    except Exception as exc:
        result.update({
            "status": "failed",
            "failed_stage": "stage_1_plan_and_generate",
            "error": str(exc),
        })
        return result

    try:
        result["stages"]["stage_2"] = stage_2_assess_and_review(
            result["stages"]["stage_1"]
        )
    except Exception as exc:
        result.update({
            "status": "failed",
            "failed_stage": "stage_2_assess_and_review",
            "error": str(exc),
        })
        return result

    try:
        result["stages"]["stage_3"] = stage_3_refine(
            result["stages"]["stage_1"],
            result["stages"]["stage_2"],
        )
    except Exception as exc:
        result.update({
            "status": "failed",
            "failed_stage": "stage_3_refine",
            "error": str(exc),
        })
        return result

    result["status"] = "completed"
    result["final_pack"] = result["stages"]["stage_3"]
    result["markdown"] = to_markdown(result)

    return result
