from __future__ import annotations

import copy
import json
import re
from typing import Any

from .nodes_v230 import _clean_phrase, _sentences
from .nodes_v253 import (
    CharacterBlueprintCreatorV253,
    CharacterPromptAssemblerV253,
    CharacterShotControlV253,
    QwenDatasetQueueV253,
    _image_plane_side,
    _piercing_geometry,
    _piercing_location,
    _rebuild_active_summary_v246,
    _tattoo_prompt_v253,
)

# -----------------------------------------------------------------------------
# V2.4.14 / Studio V2.8.14
#
# This revision preserves all V2.4.13 live passes and adds only the confirmed
# structural improvements needed for the staged workflow:
# - quantity-aware piercing language for multiple items at one location
# - explicit same-side placement for multiple nostril/eyebrow jewelry
# - current-version metadata for the Stage 0 / Stage 2 / Stage 3 / Stage 4 flow
# -----------------------------------------------------------------------------


def _number_word(value: int) -> str:
    return {
        1: "one",
        2: "two",
        3: "three",
        4: "four",
        5: "five",
        6: "six",
    }.get(int(value), str(int(value)))


def _opposite_side(side: str) -> str:
    return "left" if str(side).lower() == "right" else "right"


def _piercing_record_prompt_v254(record: dict[str, Any], plan: dict[str, Any] | None = None) -> str:
    location = str(record.get("location", "")).strip()
    location_low = location.lower()
    material = _clean_phrase(record.get("material", "")) or "metal"
    jewelry = _clean_phrase(record.get("jewelry_type", "piercing jewelry")) or "piercing jewelry"
    jewelry_low = jewelry.lower()
    quantity = max(1, int(record.get("quantity", 1) or 1))
    side_match = re.match(r"^(left|right)\b", location_low)
    side = side_match.group(1) if side_match else ""
    view = str((plan or {}).get("camera_view", ""))
    image_plane = _image_plane_side(view, side)
    plane_text = f", appearing on the {image_plane}" if image_plane else ""

    if quantity == 1:
        location_phrase = (
            f"exactly one healed permanent {material} {jewelry} is present at the subject's anatomical {location_low}{plane_text}"
            if side
            else f"exactly one healed permanent {material} {jewelry} is present at the exact configured {location_low}"
        )
        return _sentences(
            location_phrase,
            _piercing_location(location),
            _piercing_geometry(jewelry),
            "the jewelry is physically inserted through living tissue at a healed piercing opening",
            "it is not resting on the skin, glued on, clipped on, painted on, floating, or attached as a surface ornament",
            "do not add another piercing opening, detached jewelry end, duplicate item, or jewelry on the opposite anatomical side",
        )

    count_word = _number_word(quantity)
    plural_jewelry = jewelry if jewelry_low.endswith("s") else f"{jewelry}s"
    if "hoop" in jewelry_low or "ring" in jewelry_low:
        geometry = _sentences(
            f"each of the {count_word} items is its own complete continuous circular ring",
            f"the {count_word} rings pass through {count_word} separate adjacent healed piercing openings at the same configured location",
            "the rings remain closely grouped and are not distributed across opposite sides of the anatomy",
        )
    elif "barbell" in jewelry_low:
        geometry = _sentences(
            f"each of the {count_word} items is one complete barbell with its own continuous shaft and attached ends",
            f"the {count_word} barbells pass through {count_word} separate adjacent healed piercing channels at the same configured location",
        )
    elif "stud" in jewelry_low:
        geometry = _sentences(
            f"each of the {count_word} items is one complete stud anchored by its own post through a separate healed opening",
            "none of the studs floats or rests on the surface",
        )
    else:
        geometry = _sentences(
            f"the {count_word} separate jewelry items pass through {count_word} separate adjacent healed piercing openings at the same configured location",
            "each item is physically anchored within the tissue",
        )

    same_side = ""
    if side:
        opposite = _opposite_side(side)
        same_side = _sentences(
            f"all {count_word} {plural_jewelry} remain together on the same anatomical {side} location{plane_text}",
            f"the anatomical {opposite} corresponding location remains completely unpierced and has no jewelry",
            "do not place one item on each side, mirror the group, or relocate any item to the centerline",
        )

    return _sentences(
        f"exactly {count_word} separate healed permanent {material} {plural_jewelry} are present at the exact configured {location_low}",
        _piercing_location(location),
        geometry,
        same_side,
        "every item is inserted through living tissue and is not glued on, clipped on, painted on, floating, or laid across the skin",
        "do not add an extra opening, extra item, detached bead, third end, or duplicate group",
    )


def _piercing_prompt_v254(sections: dict[str, Any], plan: dict[str, Any]) -> str:
    records = sections.get("visible_piercing_records")
    if not isinstance(records, list) or not records:
        return ""
    return _sentences(*[
        _piercing_record_prompt_v254(record, plan)
        for record in records
        if isinstance(record, dict)
    ])


class CharacterBlueprintCreatorV254(CharacterBlueprintCreatorV253):
    FUNCTION = "build_blueprint_v254"
    DESCRIPTION = (
        "Current Character Creator preserving the V2.4.13 quality fixes and adding staged-dataset metadata for the independent Stage 0 baseline, Stage 2 regional atlas, Stage 3 Qwen expansion, and Stage 4 identity-LoRA dataset build."
    )

    def build_blueprint_v254(self, **kwargs):
        result = list(super().build_blueprint_v253(**kwargs))
        profile = copy.deepcopy(result[8])
        profile["fcc_core_version"] = "2.4.14"
        profile["fcc_studio_version"] = "2.8.14"
        profile["dataset_architecture"] = {
            "stage_0": "standalone Krea2 Character Creator + Shot Control baseline generation",
            "stage_2": "Krea2 pre-LoRA anchors plus body-only regional atlas from head to toe",
            "stage_3": "Qwen Image Edit angle expansion from approved Stage 2 references",
            "stage_4": "Krea2 final dataset generation with the trained identity LoRA",
        }
        result[8] = profile
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False)
        return tuple(result)


class CharacterShotControlV254(CharacterShotControlV253):
    FUNCTION = "build_shot_plan_v254"
    DESCRIPTION = (
        "Current Shot Control preserving all V2.4.13 Face Close, floor-pose, camera, complete-head, and automatic-resolution behavior for the standalone Stage 0 baseline and Stage 4 final dataset lane."
    )

    def build_shot_plan_v254(self, *args, **kwargs):
        result = list(super().build_shot_plan_v253(*args, **kwargs))
        try:
            plan = json.loads(result[8]) if result[8] else {}
        except Exception:
            plan = {}
        if isinstance(plan, dict):
            plan["fcc_core_version"] = "2.4.14"
            plan["stage_0_resolution_source"] = "Shot Control recommended_width / recommended_height"
            result[8] = json.dumps(plan, indent=2, ensure_ascii=False)
        return tuple(result)


class CharacterPromptAssemblerV254(CharacterPromptAssemblerV253):
    FUNCTION = "assemble_prompt_v254"
    DESCRIPTION = (
        "Current prompt compiler preserving every V2.4.13 live pass while adding quantity-aware same-location piercing geometry and V2.4.14 staged-workflow notes."
    )

    def assemble_prompt_v254(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        result = list(super().assemble_prompt_v253(
            character_blueprint, shot_plan, generation_purpose, reference_label,
            trigger_word, custom_prefix, custom_suffix,
        ))
        try:
            sections = json.loads(result[18]) if result[18] else {}
        except Exception:
            sections = {}

        old_marks = str(sections.get("visible_marks", result[4] or "") or "")
        tattoo_text = _tattoo_prompt_v253(sections, plan)
        piercing_text = _piercing_prompt_v254(sections, plan)
        new_marks = _sentences(tattoo_text, piercing_text)
        changed = bool(new_marks and new_marks != old_marks)

        notes = str(result[10] or "").replace("V2.4.13", "V2.4.14")
        if changed:
            sections["visible_marks"] = new_marks
            result[4] = new_marks
            notes += (
                "\nPiercings V2.4.14: quantities greater than one are compiled as separate adjacent healed openings at one configured anatomical location; same-side groups cannot split across opposite sides."
            )

            purpose = str(sections.get("purpose", "A realistic camera photograph"))
            shot = str(sections.get("shot_scene", result[2] or ""))
            character = str(sections.get("primary_character", result[19] or ""))
            presentation = str(sections.get("visible_presentation", result[3] or ""))
            body = str(sections.get("visible_body", ""))
            tan = str(sections.get("visible_tan_skin_variation", ""))
            if generation_purpose.startswith("Krea"):
                final_prompt = _sentences(
                    trigger_word, custom_prefix, purpose, shot, character,
                    presentation, body, tan, new_marks, custom_suffix,
                )
                result[0] = final_prompt
            else:
                final_prompt = str(result[13] or result[1] or "")
                if old_marks and old_marks in final_prompt:
                    final_prompt = final_prompt.replace(old_marks, new_marks, 1)
                result[1] = final_prompt
            sections["final_prompt"] = final_prompt
            result[13] = final_prompt

        sections["routing_mode"] = str(sections.get("routing_mode", "")) + "+v254_staged_dataset"
        result[10] = notes
        result[18] = json.dumps(sections, indent=2, ensure_ascii=False)
        result[12] = _rebuild_active_summary_v246(profile, plan, sections, notes)
        return tuple(result)


class QwenDatasetQueueV254(QwenDatasetQueueV253):
    DESCRIPTION = (
        "Compatibility queue registered to the V2.4.14 staged suite. Stage 3 uses approved Stage 2 references for clean Qwen angle expansion; Stage 0 and Stage 2 remain independent Krea2 lanes."
    )
