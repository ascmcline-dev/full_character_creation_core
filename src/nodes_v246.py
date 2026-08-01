from __future__ import annotations

import copy
import json
from typing import Any

from .nodes_v230 import _clean_phrase, _is_extreme_closeup_v231, _sentences
from .nodes_v243 import WIDE_FULL_BODY, _is_regional
from .nodes_v244 import PRESET_OUTFITS
from .nodes_v245 import (
    CharacterBlueprintCreatorV245,
    CharacterPromptAssemblerV245,
    CharacterShotControlV245,
    QwenDatasetQueueV245,
)

# -----------------------------------------------------------------------------
# V2.4.6 / Studio V2.8.6
# - stable garment-first prompt compilation for clothed Krea generations
# - safer high-hem crop-top preset with an explicit continuous fabric panel
# - waist-up crops retain the visible waistband / upper portion of the bottom
# - complete outfits are described as complete outfits, not isolated tops
# - clothing appears before body-silhouette language in Krea prompts
# -----------------------------------------------------------------------------

SAFE_HIGH_HEM_TOP = (
    "opaque sleeveless crop top made as one complete sewn tank-style garment, with a round neckline, wide shoulder straps, "
    "continuous front and back fabric panels, side seams, and a straight horizontal lower hem at the upper waist; "
    "the entire bust is enclosed inside the opaque fabric panel and a narrow strip of upper abdomen is visible below the hem"
)

# Replace the failure-prone wording globally before the inherited Creator resolves
# the preset. The prior phrase 'lower-bust edge barely visible' encouraged some
# checkpoints to turn the garment into a narrow under-bust band.
PRESET_OUTFITS["High-Hem Crop Top and Daisy Dukes"] = {
    "kind": "complete",
    "top": SAFE_HIGH_HEM_TOP,
    "bottom": (
        "very short fitted Daisy Duke denim cut-off shorts with a clearly visible high-rise waistband, button, zipper fly, "
        "front pockets, side seams, and secure coverage across the hips and pelvis"
    ),
    "footwear": "casual low-profile sneakers or sandals",
}


def _stable_top_phrase_v246(top: str) -> str:
    """Turn common top descriptions into visually complete sewn garments."""
    top = _clean_phrase(top)
    low = top.lower()
    if not top:
        return ""
    if any(token in low for token in ("high-hem crop top", "cropped tank top", "crop top")):
        return SAFE_HIGH_HEM_TOP
    if "t-shirt" in low or " t shirt" in low or "tee" in low:
        return (
            f"{top}, constructed as a complete opaque short-sleeve shirt with a visible neckline, two sleeves, "
            "continuous front and back fabric panels, side seams, and a lower hem"
        )
    if "tank top" in low:
        return (
            f"{top}, constructed as a complete opaque sleeveless top with a visible neckline, two shoulder straps, "
            "continuous front and back fabric panels, side seams, and a lower hem"
        )
    if "blouse" in low:
        return (
            f"{top}, constructed as a complete opaque blouse with a visible neckline or collar, continuous front and back panels, "
            "sleeves or arm openings, side seams, and a lower hem"
        )
    return f"{top}, visibly constructed as one complete sewn upper-body garment with continuous fabric coverage"


def _stable_bottom_phrase_v246(bottom: str) -> str:
    bottom = _clean_phrase(bottom)
    low = bottom.lower()
    if not bottom:
        return ""
    if any(token in low for token in ("jeans", "denim", "pants", "trousers")):
        return (
            f"{bottom}, with a clearly visible waistband, front closure, upper hip panels, pockets, and continuous lower-garment fabric"
        )
    if "skirt" in low:
        return f"{bottom}, with a clearly visible waistband and continuous skirt fabric around the hips"
    if "shorts" in low:
        return f"{bottom}, with a clearly visible waistband, front closure, upper hip panels, and two leg openings"
    return f"{bottom}, visibly constructed as one complete lower-body garment"


def _shot_scope_v246(plan: dict[str, Any]) -> str:
    if _is_extreme_closeup_v231(plan):
        return "extreme"
    if _is_regional(plan):
        return "regional"
    shot = str(plan.get("shot_type", ""))
    if shot == "Face Close-Up":
        return "face"
    if shot == "Head and Shoulders":
        return "head_shoulders"
    if shot == "Chest-Up":
        return "chest_up"
    if shot == "Waist-Up Midshot":
        return "waist_up"
    if shot == "Three-Quarter Body":
        return "three_quarter"
    if shot in {"Full Body", WIDE_FULL_BODY}:
        return "full"
    return "other"


def _stable_clothed_presentation_v246(profile: dict[str, Any], plan: dict[str, Any], fallback: str) -> str:
    """Compile only the garments that should be visible, with complete-garment geometry."""
    if profile.get("presentation_mode") != "Clothed Character":
        return fallback
    scope = _shot_scope_v246(plan)
    if scope in {"extreme", "regional"}:
        # Region-first routing from V2.4.5 remains authoritative.
        return fallback

    components = profile.get("outfit_components") if isinstance(profile.get("outfit_components"), dict) else {}
    kind = str(components.get("kind", "complete"))
    top_raw = _clean_phrase(
        components.get("top") or components.get("swimwear_top") or components.get("one_piece") or components.get("raw") or ""
    )
    bottom_raw = _clean_phrase(
        components.get("bottom") or components.get("swimwear_bottom") or components.get("one_piece") or components.get("raw") or ""
    )
    footwear = _clean_phrase(components.get("footwear", ""))
    top = _stable_top_phrase_v246(top_raw)
    bottom = _stable_bottom_phrase_v246(bottom_raw)

    if kind == "bottom_only":
        if scope in {"face", "head_shoulders", "chest_up"}:
            return "the upper torso is uncovered"
        return _sentences(
            "the upper torso is uncovered",
            f"wearing {bottom}" if bottom else fallback,
        )
    if kind == "top_only":
        if scope in {"face", "head_shoulders"}:
            return f"the neckline and shoulder edges of {top} are visible at the lower edge of the crop" if top else fallback
        return _sentences(
            f"wearing {top}" if top else fallback,
            "the selected upper garment remains clearly recognizable as one complete article of clothing",
            "the lower body is uncovered" if scope in {"waist_up", "three_quarter", "full", "other"} else "",
        )

    if kind == "one_piece":
        garment = top or bottom
        return _sentences(
            f"wearing {garment}" if garment else fallback,
            "the one-piece garment remains continuous across every visible covered body region",
        )

    if kind == "swimwear":
        # Keep the specialized inherited wording; it already names both pieces
        # and coverage, and regional routing filters top/bottom independently.
        return fallback

    if scope == "face":
        return f"only the neckline and shoulder edge of {top} are visible at the bottom of the portrait" if top else fallback
    if scope == "head_shoulders":
        return _sentences(
            f"the neckline, shoulder area, and upper fabric panel of {top} are visible" if top else fallback,
            "the upper garment remains a clearly recognizable complete article of clothing",
        )
    if scope == "chest_up":
        return _sentences(
            f"wearing {top}" if top else fallback,
            "the upper garment's continuous opaque fabric panel covers the complete chest and remains clearly recognizable as clothing",
        )
    if scope == "waist_up":
        return _sentences(
            "wearing a complete coordinated outfit",
            f"upper garment: {top}" if top else "",
            "the upper garment remains clearly recognizable as one complete sewn article of clothing",
            f"lower garment: {bottom}" if bottom else "",
            "the lower garment's waistband and upper portion are clearly visible at the bottom of the frame" if bottom else "",
        )

    return _sentences(
        "wearing a complete coordinated outfit",
        f"upper garment: {top}" if top else "",
        f"lower garment: {bottom}" if bottom else "",
        f"footwear: {footwear}" if footwear and scope == "full" else "",
        "every selected garment is visibly present wherever its body region falls inside the frame",
    )


def _rebuild_active_summary_v246(profile: dict, plan: dict, sections: dict, notes: str) -> str:
    return "\n\n".join([
        profile.get("presentation_summary", "Character settings unavailable"),
        plan.get("active_settings_summary", "Shot settings unavailable"),
        f"FINAL PRIMARY CHARACTER\n{sections.get('primary_character', '')}",
        f"FINAL SCENE / SHOT\n{sections.get('shot_scene', '')}",
        f"FINAL VISIBLE PRESENTATION\n{sections.get('visible_presentation') or '[not visible / omitted]'}",
        f"FINAL VISIBLE BODY\n{sections.get('visible_body') or '[none needed for this crop]'}",
        f"FINAL VISIBLE TAN / SKIN VARIATION\n{sections.get('visible_tan_skin_variation') or '[none / intentionally low weight]'}",
        f"FINAL VISIBLE MARKS\n{sections.get('visible_marks') or '[none visible in this crop]'}",
        notes,
    ])


class CharacterBlueprintCreatorV246(CharacterBlueprintCreatorV245):
    FUNCTION = "build_blueprint_v246"
    DESCRIPTION = (
        "Current Character Creator with stable complete-garment outfit presets, dedicated hair highlights, structured tattoos, "
        "clarified piercing routing, crop-aware anatomy, and current-only registration."
    )

    def build_blueprint_v246(self, **kwargs):
        result = list(super().build_blueprint_v245(**kwargs))
        profile = copy.deepcopy(result[8])
        profile["schema"] = "CHARACTER_BLUEPRINT_V246"
        profile["schema_version"] = 17
        profile["presentation_summary"] = str(profile.get("presentation_summary", "")) + (
            "\nGarment stability: complete outfits retain both the selected top and selected bottom when the crop reaches the waist; "
            "high-hem crop tops use one continuous opaque sewn fabric panel rather than under-bust band wording."
        )
        result[8] = profile
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        result[21] = profile["presentation_summary"]
        return tuple(result)


class CharacterShotControlV246(CharacterShotControlV245):
    FUNCTION = "build_shot_plan_v246"
    DESCRIPTION = "Current Shot Control inherited from v2.4.5 for use with the v2.4.6 stable garment compiler."

    def build_shot_plan_v246(self, **kwargs):
        result = list(super().build_shot_plan_v245(**kwargs))
        plan = copy.deepcopy(result[0])
        plan["schema"] = "FCC_SHOT_PLAN_V246"
        plan["schema_version"] = 15
        result[0] = plan
        result[8] = json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True)
        return tuple(result)


class CharacterPromptAssemblerV246(CharacterPromptAssemblerV245):
    FUNCTION = "assemble_prompt_v246"
    DESCRIPTION = (
        "Garment-first visibility compiler: complete sewn clothing geometry, waist-up bottom retention, safer high-hem crop tops, "
        "and all v2.4.5 tattoo, piercing, tan, pose, selfie, and style routing."
    )

    def assemble_prompt_v246(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        result = list(super().assemble_prompt_v245(
            character_blueprint, shot_plan, generation_purpose, reference_label,
            trigger_word, custom_prefix, custom_suffix,
        ))

        # Preserve all region-first and extreme-macro routing. Only standard
        # clothed shots receive the stronger garment compiler.
        if profile.get("presentation_mode") != "Clothed Character" or _is_extreme_closeup_v231(plan) or _is_regional(plan):
            result[10] = str(result[10]).replace("Visibility Compiler V2.4.5", "Visibility Compiler V2.4.6")
            return tuple(result)

        old_presentation = str(result[3] or "")
        new_presentation = _stable_clothed_presentation_v246(profile, plan, old_presentation)
        if not new_presentation:
            return tuple(result)

        try:
            sections = json.loads(result[18]) if result[18] else {}
        except Exception:
            sections = {}
        sections["visible_presentation"] = new_presentation
        sections["routing_mode"] = "standard_garment_first_visibility_compiled_v246"

        body = str(sections.get("visible_body", ""))
        shot = str(sections.get("shot_scene", result[2] or ""))
        character = str(sections.get("primary_character", result[19] or ""))
        tan = str(sections.get("visible_tan_skin_variation", ""))
        marks = str(sections.get("visible_marks", result[4] or ""))
        purpose = str(sections.get("purpose", "A realistic camera photograph"))

        if generation_purpose.startswith("Krea"):
            # Garment-first ordering is deliberate. It gives the model the full
            # article of clothing before body-silhouette language can be read as
            # exposed anatomy.
            final_prompt = _sentences(
                trigger_word, custom_prefix, purpose, shot, character,
                new_presentation, body, tan, marks, custom_suffix,
            )
            result[0] = final_prompt
        else:
            final_prompt = str(result[13] or "")
            if old_presentation and old_presentation in final_prompt:
                final_prompt = final_prompt.replace(old_presentation, new_presentation, 1)
            elif new_presentation:
                final_prompt = _sentences(final_prompt, new_presentation)
            result[1] = final_prompt

        sections["final_prompt"] = final_prompt
        result[3] = new_presentation
        result[13] = final_prompt
        result[16] = new_presentation
        notes = str(result[10]).replace("Visibility Compiler V2.4.5", "Visibility Compiler V2.4.6")
        notes += (
            "\nGarment-first compiler: complete sewn top geometry is stated before body silhouette; "
            "waist-up complete outfits retain the lower garment waistband and upper portion."
        )
        result[10] = notes
        result[18] = json.dumps(sections, indent=2, ensure_ascii=False)
        result[12] = _rebuild_active_summary_v246(profile, plan, sections, notes)
        return tuple(result)


class QwenDatasetQueueV246(QwenDatasetQueueV245):
    DESCRIPTION = "Current FCC Qwen dataset queue for the v2.4.6 garment-first visibility architecture."
