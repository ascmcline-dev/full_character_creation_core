from __future__ import annotations

import copy
import json
from typing import Any

from .macro_v260 import build_stage0_macro
from .nodes_v230 import _clean_phrase, _is_extreme_closeup_v231, _sentences
from .nodes_v259 import (
    CharacterBlueprintCreatorV259,
    CharacterPromptAssemblerV259,
    CharacterShotControlV259,
    QwenDatasetQueueV259,
    _replace_active_output_size,
    _replace_summary_line,
)

CORE_VERSION = "2.4.20"
STUDIO_VERSION = "2.8.20"


class CharacterBlueprintCreatorV260(CharacterBlueprintCreatorV259):
    FUNCTION = "build_blueprint_v260"
    DESCRIPTION = (
        "V2.4.20 Character Creator. Preserves the locked V2.4.19 controls while exposing canonical local anatomy and mark records to the native Clinical Macro compiler."
    )

    def build_blueprint_v260(self, **kwargs):
        result = list(super().build_blueprint_v259(**kwargs))
        profile = copy.deepcopy(result[8])
        profile["schema"] = "CHARACTER_BLUEPRINT_V260"
        profile["schema_version"] = 30
        profile["fcc_core_version"] = CORE_VERSION
        profile["fcc_studio_version"] = STUDIO_VERSION
        summary = str(profile.get("presentation_summary", "")).replace("V2.4.19", CORE_VERSION)
        summary += (
            "\nMacro V2.4.20: extreme clinical records use native single-detail source magnification, local-only anatomy authority, local intersecting marks, and medical surface texture."
        )
        profile["presentation_summary"] = summary
        result[8] = profile
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        result[21] = summary
        return tuple(result)


class CharacterShotControlV260(CharacterShotControlV259):
    FUNCTION = "build_shot_plan_v260"
    DESCRIPTION = (
        "V2.4.20 Shot Control. Extreme Close-Up uses a native one-detail macro route with no standing pose, room context, social-photo environment, or wider-body crop authority."
    )

    def build_shot_plan_v260(self, **kwargs):
        result = list(super().build_shot_plan_v259(**kwargs))
        plan = copy.deepcopy(result[0])
        if _is_extreme_closeup_v231(plan):
            macro = build_stage0_macro({}, plan, "")
            plan["framing_prompt"] = macro["crop"]
            plan["crop_authority_prompt"] = (
                "native source-magnification macro route; the generator composes only the named local target and never frames a wider body photograph"
            )
            plan["camera_prompt"] = macro["camera"]
            plan["pose_prompt"] = ""
            plan["expression_prompt"] = ""
            plan["scene_prompt"] = ""
            plan["environment_prompt"] = macro["environment"]
            plan["photo_style_prompt"] = ""
            plan["background_focus_prompt"] = ""
            plan["recommended_width"] = 1024
            plan["recommended_height"] = 1024
            plan["aspect_ratio"] = "Square 1:1 — Native Clinical Macro"
            plan["resolution_summary"] = "1024 × 1024 | Square 1:1 — Native Clinical Macro"
            plan["macro_compiler"] = "FCC_NATIVE_CLINICAL_MACRO_V260"
            plan["native_macro"] = True
            plan["ignored_controls"] = sorted(set(list(plan.get("ignored_controls", [])) + [
                "pose", "expression", "scene cast", "general photo style", "background focus", "regional close-up focus"
            ]))
            plan["final_shot_prompt"] = _sentences(
                plan["framing_prompt"],
                plan["crop_authority_prompt"],
                plan["camera_prompt"],
                plan["environment_prompt"],
                _clean_phrase(kwargs.get("shot_suffix", "")),
            )

            summary = str(plan.get("active_settings_summary", ""))
            summary = _replace_summary_line(summary, "Framing", plan["framing_prompt"])
            summary = _replace_summary_line(summary, "Camera", plan["camera_prompt"])
            summary = _replace_summary_line(summary, "Pose", "[inactive for native macro route]")
            summary = _replace_summary_line(summary, "Expression", "[inactive for native macro route]")
            summary = _replace_summary_line(summary, "Environment", plan["environment_prompt"])
            summary = _replace_summary_line(summary, "Aspect", "Square 1:1 — Native Clinical Macro (1024 × 1024)")
            summary = _replace_active_output_size(summary, 1024, 1024, plan["aspect_ratio"])
            summary += (
                "\nV2.4.20 Native Clinical Macro: the selected local detail is generated directly at macro scale; wider body composition, pose, social-photo styling, and room context are inactive."
            )
            plan["active_settings_summary"] = summary
            result[1] = plan["final_shot_prompt"]
            result[2] = plan["framing_prompt"]
            result[3] = plan["camera_prompt"]
            result[4] = ""
            result[5] = ""
            result[6] = plan["environment_prompt"]
            result[7] = summary
            result[9] = 1024
            result[10] = 1024

        plan["schema"] = "FCC_SHOT_PLAN_V260"
        plan["schema_version"] = 30
        plan["fcc_core_version"] = CORE_VERSION
        result[0] = plan
        result[8] = json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True)
        return tuple(result)


class CharacterPromptAssemblerV260(CharacterPromptAssemblerV259):
    FUNCTION = "assemble_prompt_v260"
    DESCRIPTION = (
        "V2.4.20 compiler. Extreme Clinical Macro bypasses the full-character assembler and emits only the named local target, local canonical anatomy, intersecting permanent details, medical surface texture, and neutral macro illumination."
    )

    def assemble_prompt_v260(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        result = list(super().assemble_prompt_v259(
            character_blueprint, shot_plan, generation_purpose, reference_label,
            trigger_word, custom_prefix, custom_suffix,
        ))
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan = shot_plan if isinstance(shot_plan, dict) else {}

        if not _is_extreme_closeup_v231(plan):
            result[10] = str(result[10] or "").replace("V2.4.19", CORE_VERSION)
            result[12] = str(result[12] or "").replace("V2.4.19", CORE_VERSION)
            try:
                sections = json.loads(result[18]) if result[18] else {}
                sections["compiler_version"] = CORE_VERSION
                result[18] = json.dumps(sections, indent=2, ensure_ascii=False)
            except Exception:
                pass
            return tuple(result)

        krea = str(generation_purpose).startswith("Krea")
        qwen = str(generation_purpose).startswith("Qwen")
        if qwen:
            purpose = _sentences(
                f"Edit {reference_label} into one native clinical macro photograph of the same selected local anatomical detail",
                "replace the wider reference composition with the single local macro field",
                "preserve same-person local tissue characteristics and only permanent details physically intersecting this crop",
            )
        elif generation_purpose == "Krea — LoRA Expansion":
            purpose = "native clinical macro photograph using the loaded identity LoRA only for the selected local tissue characteristics"
        else:
            purpose = "native clinical macro documentation photograph"

        macro = build_stage0_macro(
            profile, plan, purpose,
            trigger_word if krea else "",
            custom_prefix,
            custom_suffix,
        )
        final_prompt = macro["prompt"]
        shot_prompt = _sentences(macro["crop"], macro["camera"], macro["environment"])
        presentation = "local uncovered clinical documentation only; no wider clothing or body-presentation context enters the macro field"
        sections = {
            "schema": "FCC_PROMPT_SECTIONS_V260_NATIVE_MACRO",
            "compiler_version": CORE_VERSION,
            "routing_mode": "native_clinical_macro_local_only",
            "purpose": purpose,
            "focus": macro["focus"],
            "shot_scene": shot_prompt,
            "primary_character": macro["local_authority"],
            "visible_presentation": presentation,
            "visible_body": macro["local_authority"],
            "visible_marks": macro["marks"],
            "visible_tattoo_records": macro["records"]["tattoos"],
            "visible_piercing_records": macro["records"]["piercings"],
            "visible_scar_mole_beauty_mark_records": macro["records"]["scars"],
            "macro_surface_authority": macro["surface"],
            "macro_environment": macro["environment"],
            "macro_region_tags": macro["tags"],
            "final_prompt": final_prompt,
        }
        active_summary = "\n".join([
            "FCC NATIVE CLINICAL MACRO — ACTIVE PATH",
            f"Focus: {macro['focus']}",
            "Composition: native source-magnification single-detail macro",
            f"Camera: {macro['camera']}",
            f"Local anatomy: {macro['local_authority']}",
            f"Local permanent details: {macro['marks']}",
            f"Environment: {macro['environment']}",
            "Output: 1024 × 1024 | Square 1:1",
            "Wider character identity, height, full-body build, pose, wardrobe, room context, and unrelated anatomy are inactive.",
        ])
        notes = _sentences(
            str(result[10] or "").replace("V2.4.19", CORE_VERSION),
            "Stage 0 V2.4.20 Native Clinical Macro bypasses the full-character prompt route and compiles one local target only",
            "only configured marks intersecting the selected local surface are emitted",
        )

        if krea:
            result[0] = final_prompt
            result[1] = ""
        else:
            result[1] = final_prompt
            if not qwen:
                result[0] = final_prompt
        result[2] = shot_prompt
        result[3] = presentation
        result[4] = macro["marks"]
        result[5] = "required" if qwen else "not required"
        result[7] = 1024
        result[8] = 1024
        result[10] = notes
        result[11] = "Clinical Anatomy — Local Macro"
        result[12] = active_summary
        result[13] = final_prompt
        result[14] = "Only the named local detail and its minimum attachment tissue are visible."
        result[15] = macro["crop"]
        result[16] = ""
        result[17] = "1024 × 1024 | Square 1:1 — Native Clinical Macro"
        result[18] = json.dumps(sections, indent=2, ensure_ascii=False)
        result[19] = macro["local_authority"]
        result[20] = ""
        return tuple(result)


class QwenDatasetQueueV260(QwenDatasetQueueV259):
    DESCRIPTION = (
        "V2.4.20 compatibility queue. Existing Stage 3 behavior is preserved; local extreme records use the native Clinical Macro handoff when routed through the current compiler."
    )
