from __future__ import annotations

import copy
import json
from typing import Any

from .nodes_v230 import _clean_phrase, _is_extreme_closeup_v231, _sentences
from .nodes_v243 import _is_regional
from .nodes_v246 import _rebuild_active_summary_v246
from .nodes_v249 import (
    CharacterBlueprintCreatorV249,
    CharacterPromptAssemblerV249,
    CharacterShotControlV249,
    QwenDatasetQueueV249,
)

# -----------------------------------------------------------------------------
# V2.4.10 / Studio V2.8.10
# Targeted open-section completion:
# - Inherits the v2.4.9 rear Extended Puppy camera lock, complete one-piece
#   dress topology, covered-bust silhouette fidelity, and support panel fix.
# - Adds a positive base-complexion stability route when Tan Profile is None.
#   This prevents warm photography styles or broad body crops from silently
#   turning a selected Light / Very Light complexion into a tanned complexion.
# - No negative tan wording is emitted; the selected base complexion is stated
#   once as the consistent underlying skin coloration.
# -----------------------------------------------------------------------------


SKIN_TONE_STABILITY_V250: dict[str, str] = {
    "Very Light": (
        "the visible skin retains a naturally very light fair complexion with consistent pale underlying coloration across every visible skin region"
    ),
    "Light": (
        "the visible skin retains a naturally light fair complexion with consistent light underlying coloration across every visible skin region"
    ),
    "Light-Medium": (
        "the visible skin retains a consistent light-medium complexion across every visible skin region"
    ),
    "Medium": (
        "the visible skin retains a consistent natural medium complexion across every visible skin region"
    ),
    "Olive": (
        "the visible skin retains a consistent natural olive complexion across every visible skin region"
    ),
    "Deep Tan": (
        "the visible skin retains a consistent naturally deep warm complexion across every visible skin region"
    ),
    "Brown": (
        "the visible skin retains a consistent natural brown complexion across every visible skin region"
    ),
    "Deep Brown": (
        "the visible skin retains a consistent natural deep-brown complexion across every visible skin region"
    ),
    "Very Deep": (
        "the visible skin retains a consistent natural very-deep complexion across every visible skin region"
    ),
}


def _base_complexion_stability_v250(profile: dict[str, Any]) -> str:
    """Return a concise positive skin-tone lock only when no tan is selected."""
    tan_profile = str(profile.get("tan_profile", "None") or "None").strip()
    tan_level = str(profile.get("tan_level", "None") or "None").strip()
    if tan_profile != "None" or tan_level != "None":
        return ""
    skin_tone = str(profile.get("skin_tone", "") or "").strip()
    phrase = SKIN_TONE_STABILITY_V250.get(skin_tone, "")
    if not phrase:
        return ""
    return _sentences(
        phrase,
        "ambient warmth or coolness affects illumination only while the selected underlying complexion remains visually consistent",
    )


class CharacterBlueprintCreatorV250(CharacterBlueprintCreatorV249):
    FUNCTION = "build_blueprint_v250"
    DESCRIPTION = (
        "Current Character Creator with v2.4.9 rear-pose, dress, clothed-bust, and support fixes, "
        "plus a no-tan base-complexion stability route."
    )

    def build_blueprint_v250(self, **kwargs):
        result = list(super().build_blueprint_v249(**kwargs))
        profile = copy.deepcopy(result[8])
        profile["schema"] = "CHARACTER_BLUEPRINT_V250"
        profile["schema_version"] = 21
        profile["base_complexion_stability_prompt"] = _base_complexion_stability_v250(profile)
        profile["presentation_summary"] = str(profile.get("presentation_summary", "")) + (
            "\nBase complexion stability: when Tan Level / Tan-Line Mode is None, the selected skin tone remains the consistent underlying coloration across visible skin."
        )
        result[8] = profile
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        result[21] = profile["presentation_summary"]
        return tuple(result)


class CharacterShotControlV250(CharacterShotControlV249):
    FUNCTION = "build_shot_plan_v250"
    DESCRIPTION = (
        "Current Shot Control inheriting the locked v2.4.9 rear Extended Puppy camera route and all prior framing behavior."
    )

    def build_shot_plan_v250(self, **kwargs):
        result = list(super().build_shot_plan_v249(**kwargs))
        plan = copy.deepcopy(result[0])
        plan["schema"] = "FCC_SHOT_PLAN_V250"
        plan["schema_version"] = 19
        result[0] = plan
        result[8] = json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True)
        return tuple(result)


class CharacterPromptAssemblerV250(CharacterPromptAssemblerV249):
    FUNCTION = "assemble_prompt_v250"
    DESCRIPTION = (
        "Current visibility compiler with rear Extended Puppy orientation lock, complete dress topology, "
        "non-compressive clothed-bust fidelity, support-panel routing, and positive base-complexion stability when tan is None."
    )

    def assemble_prompt_v250(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        result = list(super().assemble_prompt_v249(
            character_blueprint, shot_plan, generation_purpose, reference_label,
            trigger_word, custom_prefix, custom_suffix,
        ))

        skin_lock = _base_complexion_stability_v250(profile)
        if not skin_lock:
            result[10] = str(result[10]).replace("V2.4.9", "V2.4.10")
            return tuple(result)

        try:
            sections = json.loads(result[18]) if result[18] else {}
        except Exception:
            sections = {}

        existing_skin = str(sections.get("visible_tan_skin_variation", "") or "").strip()
        # With Tan Profile None, the inherited tan section should be empty. If a
        # legacy workflow supplied another skin-variation phrase, preserve it
        # after the base-complexion statement rather than silently discarding it.
        skin_section = _sentences(skin_lock, existing_skin)
        sections["visible_tan_skin_variation"] = skin_section
        sections["base_complexion_stability"] = True

        purpose = str(sections.get("purpose", "A realistic camera photograph"))
        shot = str(sections.get("shot_scene", result[2] or ""))
        character = str(sections.get("primary_character", result[19] or ""))
        presentation = str(sections.get("visible_presentation", result[3] or ""))
        body = str(sections.get("visible_body", ""))
        marks = str(sections.get("visible_marks", result[4] or ""))

        if generation_purpose.startswith("Krea"):
            # Preserve the garment-first order inherited from v2.4.9.
            final_prompt = _sentences(
                trigger_word, custom_prefix, purpose, shot, character,
                presentation, body, skin_section, marks, custom_suffix,
            )
            result[0] = final_prompt
        else:
            final_prompt = str(result[13] or result[1] or "")
            if existing_skin and existing_skin in final_prompt:
                final_prompt = final_prompt.replace(existing_skin, skin_section, 1)
            elif skin_section:
                final_prompt = _sentences(final_prompt, skin_section)
            result[1] = final_prompt

        sections["final_prompt"] = final_prompt
        sections["routing_mode"] = str(sections.get("routing_mode", "")) + "+base_complexion_v250"
        result[13] = final_prompt
        result[18] = json.dumps(sections, indent=2, ensure_ascii=False)

        notes = str(result[10] or "").replace("V2.4.9", "V2.4.10")
        notes += (
            "\nBase-complexion compiler V2.4.10: Tan Profile None keeps the selected underlying skin tone consistent across visible regions without emitting tan-line or no-tan wording."
        )
        result[10] = notes
        result[12] = _rebuild_active_summary_v246(profile, plan, sections, notes)
        return tuple(result)


class QwenDatasetQueueV250(QwenDatasetQueueV249):
    DESCRIPTION = (
        "Current FCC Qwen dataset queue paired with the v2.4.10 rear-pose, dress, clothed-bust, support, and base-complexion compiler."
    )
