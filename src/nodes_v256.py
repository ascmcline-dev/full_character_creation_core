from __future__ import annotations

import copy
import json
from typing import Any

from .nodes_v230 import MALE_SIZE_PROMPTS_V230, _clean_phrase, _sentences
from .nodes_v246 import _rebuild_active_summary_v246
from .nodes_v255 import (
    CharacterBlueprintCreatorV255,
    CharacterPromptAssemblerV255,
    CharacterShotControlV255,
    QwenDatasetQueueV255,
)

# -----------------------------------------------------------------------------
# V2.4.16 / Studio V2.8.16
#
# Anatomy-routing correction build:
# - male genital state is a user-controlled field directly below foreskin status
# - no hard-coded non-aroused wording remains in current-version clinical prompts
# - pubic-hair anatomy is keyed to the resolved groin anatomy, not identity label
# - male, female, neutral, and custom chest/groin areas receive independent locks
# - nonbinary identity can combine explicitly selected chest and groin anatomy
#   without either area inheriting terminology from the identity label
# - positive male pelvic geometry prevents exposed rear/profile floor poses from
#   silently changing to female external anatomy
# -----------------------------------------------------------------------------

MALE_GENITAL_STATES_V256 = [
    "Unspecified — Do Not Force",
    "Non-Aroused / Flaccid",
    "Aroused / Erect",
]

_GENERIC_CLINICAL_OLD = (
    "unclothed neutral non-aroused clinical anatomy documentation",
    "unclothed adult subject in neutral non-aroused clinical anatomy documentation",
    "neutral non-aroused adult clinical anatomy documentation",
    "neutral non-aroused clinical anatomy documentation",
)
_GENERIC_CLINICAL_NEW = "unclothed adult subject in neutral clinical anatomy documentation"


def _replace_current_terms(text: str, old_groin: str, new_groin: str, old_pubic: str, new_pubic: str) -> str:
    value = str(text or "")
    if old_groin:
        value = value.replace(old_groin, new_groin)
    if old_pubic:
        value = value.replace(old_pubic, new_pubic)
    for phrase in _GENERIC_CLINICAL_OLD:
        value = value.replace(phrase, _GENERIC_CLINICAL_NEW)
    value = value.replace("in a neutral non-aroused clinical state", "in a neutral clinical documentation state")
    value = value.replace("neutral non-aroused clinical state", "neutral clinical documentation state")
    value = value.replace("neutral non-aroused state", "neutral clinical documentation state")
    return value


def _replace_profile_strings(value: Any, old_groin: str, new_groin: str, old_pubic: str, new_pubic: str) -> Any:
    if isinstance(value, str):
        return _replace_current_terms(value, old_groin, new_groin, old_pubic, new_pubic)
    if isinstance(value, list):
        return [_replace_profile_strings(item, old_groin, new_groin, old_pubic, new_pubic) for item in value]
    if isinstance(value, dict):
        return {
            key: _replace_profile_strings(item, old_groin, new_groin, old_pubic, new_pubic)
            for key, item in value.items()
        }
    return value


def _state_prompt(selection: str) -> str:
    if selection == "Non-Aroused / Flaccid":
        return "the penis remains in a natural flaccid state"
    if selection == "Aroused / Erect":
        return "the penis remains in a natural erect state"
    return ""


def _male_groin_prompt(profile: dict[str, Any], state: str) -> str:
    parts = ["adult male external genital anatomy"]
    size = MALE_SIZE_PROMPTS_V230.get(str(profile.get("male_genital_size", "")), "")
    if size:
        parts.append(size)
    foreskin = str(profile.get("male_foreskin_status", ""))
    if foreskin == "Circumcised":
        parts.append("circumcised anatomy")
    elif foreskin == "Uncircumcised / Intact Foreskin":
        parts.append("uncircumcised anatomy with intact natural foreskin")
    state_text = _state_prompt(state)
    if state_text:
        parts.append(state_text)
    return _sentences(*parts)


def _resolved_groin_prompt(profile: dict[str, Any], state: str) -> str:
    resolved = str(profile.get("resolved_groin_anatomy", ""))
    if resolved == "Male External Anatomy":
        return _male_groin_prompt(profile, state)
    if resolved == "Female External Anatomy":
        return "adult female external genital anatomy in a neutral clinical documentation state"
    if resolved == "Custom Groin Anatomy":
        return _clean_phrase(profile.get("groin_anatomy_prompt", ""))
    return ""


def _pubic_area(resolved_groin: str) -> str:
    if resolved_groin == "Male External Anatomy":
        return (
            "across the male suprapubic hair-bearing region above the penis, around the base of the penis, "
            "and along the natural groin hair-bearing region"
        )
    if resolved_groin == "Female External Anatomy":
        return "over the mons pubis and natural external groin hair-bearing region"
    return "across the selected pubic and natural groin hair-bearing region"


def _pubic_hair_prompt_v256(resolved_groin: str, style: str, custom: str = "") -> str:
    if style == "Unspecified":
        return ""
    if style == "Custom":
        return _clean_phrase(custom)

    anatomy = {
        "Male External Anatomy": "male pubic hair",
        "Female External Anatomy": "female pubic hair",
    }.get(resolved_groin, "adult pubic hair")
    area = _pubic_area(resolved_groin)
    if style == "Hairless / Fully Removed":
        return _sentences(
            "pubic-hair grooming authority: fully removed pubic hair with smooth natural skin",
            area,
        )
    wording = {
        "Fine Natural": f"fine sparse natural {anatomy} with light even coverage {area}",
        "Fine Trimmed": f"fine neatly trimmed {anatomy}, short and even, with precise light coverage {area}",
        "Neatly Trimmed Short": f"neatly trimmed short {anatomy} with even maintained coverage {area}",
        "Natural Average": f"average natural {anatomy} with realistic moderate coverage {area}",
        "Full Natural": f"full natural {anatomy} with dense realistic untrimmed coverage {area}",
    }.get(style, "")
    return _sentences(f"pubic-hair grooming authority: {wording}" if wording else "")


def _chest_area_lock(resolved_chest: str) -> str:
    if resolved_chest == "Masculine Chest — Use Male Chest Control":
        return _sentences(
            "chest-region anatomy lock: the selected chest has adult male pectoral anatomy",
            "the left and right pectorals, sternum, male nipples, and male areolae remain physically consistent with the selected masculine chest",
            "the selected adult male pectoral configuration remains unchanged in every visible view",
        )
    if resolved_chest == "Bust Anatomy — Use Bust Controls":
        return _sentences(
            "chest-region anatomy lock: the selected chest has adult bust anatomy",
            "the left and right breasts, nipples, areolae, sternum relationship, and configured bust proportions remain physically consistent with the selected bust controls",
            "the selected adult bust configuration remains unchanged in every visible view",
        )
    if resolved_chest == "Flat / Neutral Chest":
        return _sentences(
            "chest-region anatomy lock: the selected chest remains flat and neutral with minimal projection",
            "the selected flat neutral chest configuration remains unchanged in every visible view",
        )
    if resolved_chest == "Custom Chest Description":
        return "chest-region anatomy lock: preserve the explicitly configured custom chest anatomy without replacing it with another anatomy category"
    return ""


def _sex_anatomy_lock(resolved_groin: str, state: str) -> str:
    if resolved_groin == "Male External Anatomy":
        return _sentences(
            "groin-region anatomy lock: one anatomically male pelvis has exactly one penis and one scrotum naturally attached to the surrounding male pelvic anatomy",
            "the scrotum remains correctly positioned between the upper thighs and the male perineal anatomy remains continuous toward the rear pelvis",
            "the penis and scrotum remain present wherever physically exposed by the selected crop, pose, or camera view",
            _state_prompt(state),
            "the selected adult male external anatomy remains unchanged in every visible view",
        )
    if resolved_groin == "Female External Anatomy":
        return _sentences(
            "groin-region anatomy lock: the selected pelvis has adult female external genital anatomy with one anatomically continuous vulvar region",
            "the mons pubis, labia, external opening, perineal transition, and upper-thigh attachment remain physically consistent wherever visible",
            "the selected adult female external anatomy remains unchanged in every visible view",
        )
    if resolved_groin == "Custom Groin Anatomy":
        return "groin-region anatomy lock: preserve the explicitly configured custom groin anatomy exactly and do not replace it with male or female anatomy unless the custom description states that anatomy"
    return ""


def _merge_unique(*parts: Any) -> str:
    seen: set[str] = set()
    out: list[str] = []
    for part in parts:
        text = _clean_phrase(part)
        if not text:
            continue
        key = " ".join(text.lower().split())
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return _sentences(*out)


def _plan_mentions_any(plan: dict[str, Any], tokens: tuple[str, ...]) -> bool:
    text = " ".join(str(plan.get(key, "") or "") for key in (
        "shot_type", "framing_prompt", "crop_authority_prompt", "pose_prompt",
        "camera_prompt", "focus_region", "selected_extreme_closeup_focus",
        "selected_closeup_region", "final_shot_prompt",
    )).lower()
    return any(token in text for token in tokens)


def _plan_shows_groin(plan: dict[str, Any]) -> bool:
    return _plan_mentions_any(plan, (
        "pelvis", "groin", "pubic", "genital", "buttock", "hip",
        "upper thigh", "three-quarter-body", "full-body", "full body",
        "all fours", "hands-and-knees", "extended puppy", "floor pose",
    ))


def _plan_shows_chest(plan: dict[str, Any]) -> bool:
    return _plan_mentions_any(plan, (
        "chest", "upper torso", "upper-torso", "shoulder", "waist-up",
        "three-quarter-body", "full-body", "full body", "all fours",
        "hands-and-knees", "extended puppy", "floor pose",
    ))


class CharacterBlueprintCreatorV256(CharacterBlueprintCreatorV255):
    FUNCTION = "build_blueprint_v256"
    DESCRIPTION = (
        "Current Character Creator with anatomy-area locks keyed to resolved chest and groin selections, gender-specific pubic-hair regions, and an optional male genital state directly beneath Foreskin Status. Nonbinary identity can use any explicit chest/groin combination without anatomy leakage."
    )

    @classmethod
    def INPUT_TYPES(cls):
        inherited = copy.deepcopy(super().INPUT_TYPES())
        required = inherited.get("required", {})
        rebuilt: dict[str, Any] = {}
        for name, spec in required.items():
            rebuilt[name] = spec
            if name == "male_foreskin_status":
                rebuilt["male_genital_state"] = (
                    MALE_GENITAL_STATES_V256,
                    {"default": "Unspecified — Do Not Force"},
                )
        inherited["required"] = rebuilt
        return inherited

    def build_blueprint_v256(self, **kwargs):
        state = str(kwargs.get("male_genital_state", "Unspecified — Do Not Force"))
        result = list(super().build_blueprint_v255(**kwargs))
        original_profile = copy.deepcopy(result[8])
        old_groin = str(original_profile.get("groin_anatomy_prompt", "") or "")
        old_pubic = str(original_profile.get("pubic_hair_prompt", "") or "")

        profile = copy.deepcopy(original_profile)
        resolved_chest = str(profile.get("resolved_chest_anatomy", ""))
        resolved_groin = str(profile.get("resolved_groin_anatomy", ""))
        effective_state = state if resolved_groin == "Male External Anatomy" else "Not applicable"
        new_groin = _resolved_groin_prompt(profile, state)
        new_pubic = _pubic_hair_prompt_v256(
            resolved_groin,
            str(profile.get("pubic_hair_style", "Unspecified")),
            str(kwargs.get("custom_pubic_hair_style", "")),
        )

        profile = _replace_profile_strings(profile, old_groin, new_groin, old_pubic, new_pubic)
        chest_lock = _chest_area_lock(resolved_chest)
        sex_lock = _sex_anatomy_lock(resolved_groin, state)
        mark_integrity = str(profile.get("anatomy_integrity_lock", "") or "")
        anatomy_integrity = _merge_unique(mark_integrity, chest_lock, sex_lock)

        profile["schema"] = "CHARACTER_BLUEPRINT_V256"
        profile["schema_version"] = 26
        profile["fcc_core_version"] = "2.4.16"
        profile["fcc_studio_version"] = "2.8.16"
        profile["male_genital_state"] = effective_state
        profile["male_genital_state_selection"] = state
        profile["groin_anatomy_prompt"] = new_groin
        profile["pubic_hair_prompt"] = new_pubic
        profile["chest_region_integrity_prompt"] = chest_lock
        profile["sex_anatomy_integrity_prompt"] = sex_lock
        profile["anatomy_integrity_lock"] = anatomy_integrity
        profile["lower_body_silhouette_prompt"] = str(profile.get("clothed_lower_body", "") or "")
        body_type_label = str(profile.get("body_type", "Average") or "Average").lower().replace("custom / unspecified", "natural")
        profile["upper_limb_proportion_prompt"] = (
            f"the documented arm has {body_type_label} adult upper-limb proportions with natural shoulder-to-upper-arm, elbow, forearm, wrist, and hand continuity"
        )
        profile["lower_limb_proportion_prompt"] = (
            f"the documented leg has {body_type_label} adult lower-limb proportions with natural thigh, knee, shin, calf, ankle, and foot continuity"
        )
        profile["resolved_anatomy_area_locks"] = {
            "identity": str(profile.get("primary_character_gender", "")),
            "chest": resolved_chest,
            "groin": resolved_groin,
            "male_genital_state": effective_state,
        }

        # Rebuild the anatomy fields from their separated components. This keeps
        # the explicit groin anatomy out of Stage 2 leg/foot prompts while the
        # full clinical character still contains it for pelvis-visible images.
        anatomy_upper = _merge_unique(profile.get("anatomy_upper_body", ""), chest_lock)
        clothed_upper = _merge_unique(profile.get("clothed_upper_body", ""), chest_lock)
        clothed_lower = str(profile.get("clothed_lower_body", "") or "")
        anatomy_lower = _merge_unique(clothed_lower, new_groin, new_pubic)
        profile["anatomy_upper_body"] = anatomy_upper
        profile["upper_body_identity"] = anatomy_upper
        profile["clothed_upper_body"] = clothed_upper
        profile["anatomy_lower_body"] = anatomy_lower
        profile["lower_body_identity"] = anatomy_lower

        # Current-version clinical wording is neutral documentation. The male
        # genital state is controlled only by the new field.
        active_presentation = _replace_current_terms(
            str(profile.get("active_presentation_prompt", "") or ""), old_groin, new_groin, old_pubic, new_pubic
        )
        presentation_mode = str(profile.get("presentation_mode", ""))
        if presentation_mode == "Clinical Anatomy":
            active_presentation = _GENERIC_CLINICAL_NEW
            if profile.get("piercing_entries"):
                active_presentation = _merge_unique(active_presentation, "only the defined permanent piercings remain")
        profile["active_presentation_prompt"] = active_presentation

        if presentation_mode == "Clinical Anatomy":
            active_body = _merge_unique(anatomy_upper, anatomy_lower)
        elif presentation_mode == "Custom Presentation" and str(profile.get("custom_presentation_body_detail", "")) == "Clinical Anatomy — Include Selected Chest / Groin":
            active_body = _merge_unique(anatomy_upper, anatomy_lower)
        else:
            active_body = _merge_unique(clothed_upper, clothed_lower)
        profile["active_body_prompt"] = active_body

        gender_authority = str(profile.get("gender_authority_prompt", "") or "")
        identity_details = str(profile.get("identity_detail_prompt", "") or "")
        marks = str(profile.get("marks_prompt", "") or "")
        tattoo_lock = str(profile.get("tattoo_count_lock", "") or "")
        piercing_lock = str(profile.get("piercing_count_lock", "") or "")
        clothed_presentation = str(profile.get("default_clothing_prompt", "") or "")
        clinical_presentation = _GENERIC_CLINICAL_NEW
        if profile.get("piercing_entries"):
            clinical_presentation = _merge_unique(clinical_presentation, "only the defined permanent piercings remain")

        active_character = _merge_unique(
            gender_authority, identity_details, active_body, active_presentation,
            marks, tattoo_lock, piercing_lock, anatomy_integrity,
        )
        clothed_character = _merge_unique(
            gender_authority, identity_details, clothed_upper, clothed_lower,
            clothed_presentation, marks, tattoo_lock, piercing_lock, chest_lock,
        )
        clinical_character = _merge_unique(
            gender_authority, identity_details, anatomy_upper, anatomy_lower,
            clinical_presentation, marks, tattoo_lock, piercing_lock, anatomy_integrity,
        )
        profile["active_character_prompt"] = active_character
        profile["full_profile_prompt"] = active_character
        profile["clothed_character_prompt"] = clothed_character
        profile["clinical_character_prompt"] = clinical_character

        anatomy_summary = "\n".join([
            f"Gender identity: {profile.get('primary_character_gender', '')}",
            f"Resolved chest anatomy: {resolved_chest}",
            f"Resolved groin anatomy: {resolved_groin}",
            f"Male genital size: {profile.get('male_genital_size') if resolved_groin == 'Male External Anatomy' else '[inactive]'}",
            f"Foreskin status: {profile.get('male_foreskin_status') if resolved_groin == 'Male External Anatomy' else '[inactive]'}",
            f"Male genital state: {effective_state if resolved_groin == 'Male External Anatomy' else '[inactive]'}",
            f"Pubic hair: {profile.get('pubic_hair_style', 'Unspecified')} (included only in clinical crops that show the groin)",
            "Area-lock rule: chest and groin anatomy follow their independently resolved selections, including Adult Nonbinary combinations.",
        ])
        summary = str(profile.get("presentation_summary", "") or "")
        summary = summary.replace("V2.4.15", "V2.4.16")
        summary += (
            "\nAnatomy V2.4.16: chest and groin regions are independently locked to their resolved selections; male prompts use male suprapubic terminology and positive penis/scrotum continuity."
            f"\nMale genital state: {effective_state if resolved_groin == 'Male External Anatomy' else '[inactive]'}"
        )
        profile["presentation_summary"] = summary
        profile["anatomy_configuration_summary"] = anatomy_summary

        # Update all inherited scalar string outputs, then set authoritative
        # current-version fields explicitly by their stable output positions.
        for index, value in enumerate(result):
            if isinstance(value, str):
                result[index] = _replace_current_terms(value, old_groin, new_groin, old_pubic, new_pubic)
        result[1] = anatomy_upper
        result[2] = anatomy_lower
        result[3] = str(profile.get("chest_anatomy_prompt", "") if presentation_mode == "Clinical Anatomy" else profile.get("chest_clothed_prompt", ""))
        result[6] = active_character
        result[8] = profile
        result[10] = clothed_upper
        result[11] = anatomy_upper
        result[12] = clothed_lower
        result[13] = anatomy_lower
        result[15] = json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True)
        result[16] = active_presentation
        result[17] = active_body
        result[18] = active_character
        result[19] = clothed_character
        result[20] = clinical_character
        result[21] = summary
        result[24] = anatomy_integrity
        result[28] = anatomy_summary
        return tuple(result)


class CharacterShotControlV256(CharacterShotControlV255):
    FUNCTION = "build_shot_plan_v256"
    DESCRIPTION = (
        "Current Shot Control preserving V2.4.15 rear-floor and camera-height fixes. Anatomy selection and genital-state authority are supplied by the connected V2.4.16 Character Blueprint."
    )

    def build_shot_plan_v256(self, **kwargs):
        result = list(super().build_shot_plan_v255(**kwargs))
        plan = copy.deepcopy(result[0])
        plan["schema"] = "FCC_SHOT_PLAN_V256"
        plan["schema_version"] = 26
        plan["fcc_core_version"] = "2.4.16"
        result[0] = plan
        result[8] = json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True)
        return tuple(result)


class CharacterPromptAssemblerV256(CharacterPromptAssemblerV255):
    FUNCTION = "assemble_prompt_v256"
    DESCRIPTION = (
        "Current prompt compiler preserving V2.4.15 framing, floor-pose, garment, tattoo, and piercing behavior while enforcing resolved chest/groin anatomy-area locks and optional male genital state."
    )

    def assemble_prompt_v256(
        self, character_blueprint, shot_plan, generation_purpose, reference_label,
        trigger_word="", custom_prefix="", custom_suffix="",
    ):
        result = list(super().assemble_prompt_v255(
            character_blueprint, shot_plan, generation_purpose, reference_label,
            trigger_word, custom_prefix, custom_suffix,
        ))
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan = shot_plan if isinstance(shot_plan, dict) else {}
        for index, value in enumerate(result):
            if isinstance(value, str):
                for phrase in _GENERIC_CLINICAL_OLD:
                    value = value.replace(phrase, _GENERIC_CLINICAL_NEW)
                value = value.replace("in a neutral non-aroused clinical state", "in a neutral clinical documentation state")
                result[index] = value
        notes = str(result[10] or "").replace("V2.4.15", "V2.4.16")
        notes += (
            "\nAnatomy V2.4.16: chest and groin text is selected from independent resolved anatomy fields. Male state is emitted only for Male External Anatomy and only from the Male Genital State control."
        )
        result[10] = notes
        try:
            sections = json.loads(result[18]) if result[18] else {}
        except Exception:
            sections = {}
        sections["routing_mode"] = str(sections.get("routing_mode", "")) + "+v256_anatomy_area_locks"
        sections["resolved_chest_anatomy"] = profile.get("resolved_chest_anatomy", "")
        sections["resolved_groin_anatomy"] = profile.get("resolved_groin_anatomy", "")
        sections["male_genital_state"] = profile.get("male_genital_state", "Not applicable")

        visible_locks = []
        if _plan_shows_chest(plan):
            visible_locks.append(profile.get("chest_region_integrity_prompt", ""))
        if profile.get("presentation_mode") == "Clinical Anatomy" and _plan_shows_groin(plan):
            visible_locks.append(profile.get("sex_anatomy_integrity_prompt", ""))
        lock_text = _merge_unique(*visible_locks)
        if lock_text:
            sections["visible_body"] = _merge_unique(sections.get("visible_body", ""), lock_text)
            sections["visible_anatomy_area_locks"] = lock_text
            final_prompt = str(result[13] or result[0] or result[1] or "")
            if lock_text not in final_prompt:
                final_prompt = _merge_unique(final_prompt, lock_text)
            result[13] = final_prompt
            if str(generation_purpose).startswith("Krea"):
                result[0] = final_prompt
            else:
                result[1] = final_prompt

        result[18] = json.dumps(sections, indent=2, ensure_ascii=False)
        result[12] = _rebuild_active_summary_v246(profile, plan, sections, notes)
        return tuple(result)


class QwenDatasetQueueV256(QwenDatasetQueueV255):
    DESCRIPTION = (
        "Compatibility queue registered to V2.4.16. Stage 3 remains camera-angle expansion from manually approved references; anatomy-area selection is owned by the approved source image and Character Blueprint."
    )
