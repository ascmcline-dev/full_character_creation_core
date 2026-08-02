from __future__ import annotations

import copy
import json
from typing import Any

from .nodes_v230 import _clean_phrase, _sentences
from .nodes_v257 import _piercing_prompt, _scar_record_prompt
from .dataset_v254 import (
    FCCKreaQueueItemRouter,
    _anchor_specs,
    _body_only_authority,
    _face_identity,
    _photo_base,
    _regional_outfit,
    _regional_specs,
    _skin,
    _slug,
    _spec,
    _special_region_authority,
    _unique_sentences,
)
from .dataset_v256 import (
    FCCFaceAngleDatasetDirector as FCCFaceAngleDatasetDirectorV256,
    _clinical_body,
    _clothed_body,
    _copy_specs_for_profile,
    _resolved_chest,
    _resolved_groin,
)
from .nodes_v253 import _tattoo_record_prompt_v253

# Counts are base-shot counts before Variations Per Shot is applied.
KREA_BLUEPRINT_PLANS = [
    "Identity Anchors — 3",
    "Body-Only Regional Atlas — Clothed (102)",
    "Body-Only Regional Atlas — Clinical Unclothed (102)",
    "Complete Body-Only Regional Atlas — Clothed and Clinical (204)",
    "Extreme Clinical Anatomy Close-Ups — Opt-In (resolved count)",
    "Complete Pre-LoRA Documentation — Anchors + Body Atlas (207)",
]


def _nonface_identity(profile: dict[str, Any]) -> str:
    # Stage 2 body-only records should not ask the model to blend a broad gender
    # identity label with independently selected chest/groin anatomy. Identity is
    # retained through age, heritage, complexion, body build, marks, and the
    # explicit anatomy objects used by the selected region.
    heritage = _clean_phrase(profile.get("heritage_prompt", ""))
    return _unique_sentences(
        "one adult primary subject",
        profile.get("age_range", "") and f"age range {profile.get('age_range')}",
        heritage,
        "the subject's identity label does not alter or blend the independently resolved chest and groin anatomy",
    )


def _complexion_lock(profile: dict[str, Any]) -> str:
    selected = str(profile.get("skin_tone", "") or "").strip()
    if selected:
        selected = selected.lower().replace("custom / unspecified", "selected")
    return _unique_sentences(
        f"the documented region retains the same selected underlying {selected} skin tone" if selected else "the documented region retains the selected underlying complexion",
        "lighting may change highlights and shadows only; it does not lighten, tan, recolor, or replace the underlying skin tone",
        profile.get("base_complexion_stability_prompt", ""),
    )


def _record_intersects(record: dict[str, Any], regions: set[str]) -> bool:
    tags = set(record.get("region_tags", []))
    if not tags or "unknown" in tags:
        return False
    return bool(tags & regions)


def _region_marks(profile: dict[str, Any], regions: set[str], presentation: str) -> str:
    parts: list[str] = []
    for record in profile.get("tattoo_records", []) if isinstance(profile.get("tattoo_records"), list) else []:
        if isinstance(record, dict) and _record_intersects(record, regions):
            text = _tattoo_record_prompt_v253(record, None)
            if presentation == "clothed":
                text = _sentences(
                    text,
                    "show the tattoo only on skin genuinely exposed within this regional crop; do not remove or redesign clothing to expose unrelated areas",
                )
            parts.append(text)
    # Reuse the tested physical piercing compiler with a minimal neutral plan.
    piercing_records = [
        r for r in profile.get("piercing_records", []) if isinstance(r, dict) and _record_intersects(r, regions)
    ] if isinstance(profile.get("piercing_records"), list) else []
    if piercing_records:
        parts.append(_sentences(*(_piercing_prompt(record, {}) for record in piercing_records)))
    for record in profile.get("scar_mole_beauty_mark_records", []) if isinstance(profile.get("scar_mole_beauty_mark_records"), list) else []:
        if isinstance(record, dict) and _record_intersects(record, regions):
            parts.append(_scar_record_prompt(record))
    return _unique_sentences(*parts)


def _clinical_body_v257(profile: dict[str, Any], regions: set[str]) -> str:
    # Parent V256 already separates lower-limb geometry from groin anatomy. Use
    # the canonical current chest fields and add one direct exclusivity rule.
    return _unique_sentences(
        _clinical_body(profile, regions),
        "only the anatomy explicitly resolved for this documented region is present; do not add a second chest category or a second groin category",
    )


def _clothed_body_v257(profile: dict[str, Any], regions: set[str]) -> str:
    return _unique_sentences(
        _clothed_body(profile, regions),
        "the selected garment follows the resolved chest and body structure without changing it into an athletic or compression outfit unless that exact outfit was selected",
    )


def _true_extreme_common() -> list[dict[str, Any]]:
    role = "OPTIONAL EXTREME CLINICAL VALIDATION ONLY — EXCLUDE FROM DEFAULT IDENTITY-LORA DATASET"
    rows = [
        ("extreme_navel_detail", "true extreme close-up of the existing navel and only the immediately surrounding abdominal skin", {"abdomen", "waist", "navel"}),
        ("extreme_left_palm_detail", "true extreme close-up of the anatomical left palm surface, palm lines, finger bases, and lower wrist attachment", {"hand", "left_hand", "wrist"}),
        ("extreme_right_palm_detail", "true extreme close-up of the anatomical right palm surface, palm lines, finger bases, and lower wrist attachment", {"hand", "right_hand", "wrist"}),
        ("extreme_left_fingertips", "true extreme close-up of the anatomical left fingertips and natural fingernails with only the distal fingers visible", {"hand", "left_hand"}),
        ("extreme_right_fingertips", "true extreme close-up of the anatomical right fingertips and natural fingernails with only the distal fingers visible", {"hand", "right_hand"}),
        ("extreme_left_sole_detail", "true extreme close-up of the anatomical left sole surface, heel pad, arch, ball, and toe pads", {"foot", "sole", "left_foot"}),
        ("extreme_right_sole_detail", "true extreme close-up of the anatomical right sole surface, heel pad, arch, ball, and toe pads", {"foot", "sole", "right_foot"}),
        ("extreme_left_heel_detail", "true extreme close-up of the anatomical left heel and Achilles-to-heel skin transition", {"foot", "sole", "left_foot", "ankle"}),
        ("extreme_right_heel_detail", "true extreme close-up of the anatomical right heel and Achilles-to-heel skin transition", {"foot", "sole", "right_foot", "ankle"}),
        ("extreme_left_gluteal_fold", "true extreme close-up of the anatomical left gluteal fold and only the immediate posterior upper-thigh attachment", {"buttocks", "left_buttock", "left_thigh"}),
        ("extreme_right_gluteal_fold", "true extreme close-up of the anatomical right gluteal fold and only the immediate posterior upper-thigh attachment", {"buttocks", "right_buttock", "right_thigh"}),
    ]
    return [_spec(sid, "extreme_clinical_validation", desc, "clinical", regs, 1024, 1024, role) for sid, desc, regs in rows]


def _true_extreme_chest(profile: dict[str, Any]) -> list[dict[str, Any]]:
    role = "OPTIONAL EXTREME CLINICAL VALIDATION ONLY — EXCLUDE FROM DEFAULT IDENTITY-LORA DATASET"
    resolved = _resolved_chest(profile)
    if resolved == "Bust Anatomy — Use Bust Controls":
        rows = [
            ("extreme_left_nipple_areola", "true one-sided extreme close-up of the existing anatomical left nipple and surrounding areola only", {"chest", "breast", "left_breast", "left_nipple"}),
            ("extreme_right_nipple_areola", "true one-sided extreme close-up of the existing anatomical right nipple and surrounding areola only", {"chest", "breast", "right_breast", "right_nipple"}),
            ("extreme_left_lower_bust_contour", "true extreme close-up of the anatomical left lower breast contour and fold with minimal adjacent rib and upper-abdomen context", {"chest", "breast", "left_breast"}),
            ("extreme_right_lower_bust_contour", "true extreme close-up of the anatomical right lower breast contour and fold with minimal adjacent rib and upper-abdomen context", {"chest", "breast", "right_breast"}),
            ("extreme_sternum_bust_transition", "true extreme close-up of the sternum and inner left/right bust transitions only", {"chest", "breast", "sternum"}),
        ]
    elif resolved == "Masculine Chest — Use Male Chest Control":
        rows = [
            ("extreme_left_male_nipple_areola", "true one-sided extreme close-up of the existing anatomical left male nipple and surrounding areola only", {"chest", "pectoral", "left_pectoral", "left_nipple"}),
            ("extreme_right_male_nipple_areola", "true one-sided extreme close-up of the existing anatomical right male nipple and surrounding areola only", {"chest", "pectoral", "right_pectoral", "right_nipple"}),
            ("extreme_left_lower_pectoral_boundary", "true extreme close-up of the anatomical left lower pectoral boundary with minimal adjacent rib and upper-abdomen context", {"chest", "pectoral", "left_pectoral"}),
            ("extreme_right_lower_pectoral_boundary", "true extreme close-up of the anatomical right lower pectoral boundary with minimal adjacent rib and upper-abdomen context", {"chest", "pectoral", "right_pectoral"}),
            ("extreme_sternum_pectoral_transition", "true extreme close-up of the sternum and inner left/right pectoral transitions only", {"chest", "pectoral", "sternum"}),
        ]
    else:
        noun = "flat neutral chest" if resolved == "Flat / Neutral Chest" else "configured custom chest"
        tag = "neutral_chest" if resolved == "Flat / Neutral Chest" else "custom_chest"
        rows = [
            ("extreme_selected_chest_center", f"true extreme close-up of the central {noun} surface and sternum transition only", {"chest", tag, "sternum"}),
            ("extreme_selected_chest_left_detail", f"true extreme close-up of the anatomical left {noun} surface and lower boundary only", {"chest", tag}),
            ("extreme_selected_chest_right_detail", f"true extreme close-up of the anatomical right {noun} surface and lower boundary only", {"chest", tag}),
        ]
    return [_spec(sid, "extreme_clinical_validation", desc, "clinical", regs, 1024, 1024, role) for sid, desc, regs in rows]


def _true_extreme_groin(profile: dict[str, Any]) -> list[dict[str, Any]]:
    role = "OPTIONAL EXTREME CLINICAL VALIDATION ONLY — EXCLUDE FROM DEFAULT IDENTITY-LORA DATASET"
    resolved = _resolved_groin(profile)
    if resolved == "Male External Anatomy":
        rows = [
            ("extreme_male_suprapubic_detail", "true extreme close-up of the male suprapubic hair-bearing region immediately above the penis base", {"pelvis", "groin", "pubic", "suprapubic", "male_genital"}),
            ("extreme_male_genital_front_detail", "true extreme direct-front close-up of the configured penis and scrotum with only minimal attachment context", {"groin", "male_genital"}),
            ("extreme_male_genital_left_profile_detail", "true extreme anatomical-left profile close-up of the configured male external anatomy and immediate groin attachment", {"groin", "male_genital", "left_groin"}),
            ("extreme_male_genital_right_profile_detail", "true extreme anatomical-right profile close-up of the configured male external anatomy and immediate groin attachment", {"groin", "male_genital", "right_groin"}),
            ("extreme_scrotal_lower_detail", "true extreme lower-view close-up of the scrotum and immediate upper-inner-thigh attachment", {"groin", "male_genital", "perineal"}),
            ("extreme_male_perineal_detail", "true extreme rear-lower close-up of the male perineal transition only", {"groin", "male_genital", "perineal"}),
        ]
    elif resolved == "Female External Anatomy":
        rows = [
            ("extreme_female_pubic_mound_detail", "true extreme close-up of the female pubic mound and lower-abdomen transition only", {"pelvis", "groin", "pubic", "female_genital"}),
            ("extreme_female_external_front_detail", "true extreme direct-front close-up of the configured adult female external anatomy with minimal attachment context", {"groin", "female_genital"}),
            ("extreme_female_external_left_profile_detail", "true extreme anatomical-left profile close-up of the configured female external anatomy and immediate groin attachment", {"groin", "female_genital", "left_groin"}),
            ("extreme_female_external_right_profile_detail", "true extreme anatomical-right profile close-up of the configured female external anatomy and immediate groin attachment", {"groin", "female_genital", "right_groin"}),
            ("extreme_female_perineal_detail", "true extreme lower/rear close-up of the female perineal transition only", {"groin", "female_genital", "perineal"}),
        ]
    elif resolved == "Custom Groin Anatomy":
        rows = [
            ("extreme_custom_groin_front_detail", "true extreme direct-front close-up of the explicitly configured custom groin anatomy only", {"groin", "custom_groin"}),
            ("extreme_custom_groin_left_profile_detail", "true extreme anatomical-left profile close-up of the explicitly configured custom groin anatomy only", {"groin", "custom_groin", "left_groin"}),
            ("extreme_custom_groin_right_profile_detail", "true extreme anatomical-right profile close-up of the explicitly configured custom groin anatomy only", {"groin", "custom_groin", "right_groin"}),
        ]
    else:
        rows = []
    return [_spec(sid, "extreme_clinical_validation", desc, "clinical", regs, 1024, 1024, role) for sid, desc, regs in rows]


def _mark_extreme_specs(profile: dict[str, Any]) -> list[dict[str, Any]]:
    role = "OPTIONAL EXTREME CLINICAL VALIDATION ONLY — EXCLUDE FROM DEFAULT IDENTITY-LORA DATASET"
    specs: list[dict[str, Any]] = []
    index = 0
    for collection, prefix in (
        (profile.get("tattoo_records", []), "tattoo"),
        (profile.get("scar_mole_beauty_mark_records", []), "skin_mark"),
        (profile.get("piercing_records", []), "piercing"),
    ):
        if not isinstance(collection, list):
            continue
        for record in collection:
            if not isinstance(record, dict):
                continue
            tags = set(record.get("region_tags", []))
            if tags & {"face", "eye", "eyes", "eyebrow", "nose", "nostril", "mouth", "lip", "lips", "ear", "ears"}:
                continue  # face details belong in the separate identity-detail set
            if not tags or "unknown" in tags:
                continue
            index += 1
            raw = _clean_phrase(record.get("raw", ""))
            specs.append(_spec(
                f"extreme_{prefix}_detail_{index:02d}",
                "extreme_clinical_validation",
                f"true extreme close-up documentation of the configured permanent {prefix.replace('_', ' ')} at its exact location: {raw}",
                "clinical", tags, 1024, 1024, role,
            ))
    return specs


def _extreme_specs(profile: dict[str, Any]) -> list[dict[str, Any]]:
    return _true_extreme_chest(profile) + _true_extreme_groin(profile) + _true_extreme_common() + _mark_extreme_specs(profile)


def _select_specs(plan: str, profile: dict[str, Any]) -> list[dict[str, Any]]:
    anchors = _anchor_specs()
    clothed = _copy_specs_for_profile(_regional_specs("clothed"), profile)
    clinical = _copy_specs_for_profile(_regional_specs("clinical"), profile)
    if plan == KREA_BLUEPRINT_PLANS[0]:
        return anchors
    if plan == KREA_BLUEPRINT_PLANS[1]:
        return clothed
    if plan == KREA_BLUEPRINT_PLANS[2]:
        return clinical
    if plan == KREA_BLUEPRINT_PLANS[3]:
        return clothed + clinical
    if plan == KREA_BLUEPRINT_PLANS[4]:
        return _extreme_specs(profile)
    return anchors + clothed + clinical


def _extreme_authority(profile: dict[str, Any], spec: dict[str, Any]) -> str:
    regions = set(spec.get("regions", set()))
    parts = [
        "true single-detail body-only clinical close-up documentation",
        "the one named anatomical detail occupies approximately eighty to ninety percent of the frame",
        "the complete head, face, eyes, nose, mouth, and ears remain outside the frame",
        "exclude the complete torso, complete pelvis, complete limb, complete person, distant body, and every unrelated regional-atlas composition",
        "show only the named feature and the minimum immediately adjacent tissue needed to prove natural attachment",
        "this opt-in validation image is not automatically approved for identity-LoRA training",
    ]
    if regions & {"chest", "breast", "bust", "pectoral", "nipple", "areola", "sternum"}:
        parts.append(profile.get("active_chest_integrity_prompt", profile.get("chest_region_integrity_prompt", "")))
    if regions & {"groin", "pubic", "genital", "penis", "scrotum", "vulva", "perineum"}:
        parts.extend([
            profile.get("groin_anatomy_prompt", ""),
            profile.get("pubic_hair_prompt", ""),
            profile.get("sex_anatomy_integrity_prompt", profile.get("groin_region_integrity_prompt", "")),
        ])
    if regions & {"buttocks", "gluteal", "left_buttock", "right_buttock"}:
        parts.append("preserve the configured gluteal build while showing only the named fold or surface detail")
    return _unique_sentences(*parts)


def _build_prompt(profile: dict[str, Any], spec: dict[str, Any], suffix: str) -> str:
    regions = set(spec["regions"])
    presentation = str(spec["presentation"])
    anchor = spec["category"] == "identity_anchor"
    identity = _face_identity(profile) if anchor else _nonface_identity(profile)
    body_only = "" if anchor else _body_only_authority()
    if presentation == "clinical":
        presentation_text = _clinical_body_v257(profile, regions)
        body_scope = ""
    elif presentation == "clothed":
        presentation_text = _regional_outfit(profile, regions)
        body_scope = _clothed_body_v257(profile, regions)
    else:
        presentation_text = _sentences(
            "a simple opaque neutral identity-documentation top may appear only where the selected anchor crop permits it",
            "clothing must not widen the crop or cover the face",
        )
        body_scope = ""
    purpose = _sentences(
        "FCC Stage 2 Krea2 pre-LoRA documentation run",
        "construct the adult subject directly from the connected canonical Character Blueprint",
        "this is an original Krea2 blueprint render and not an edit of another image",
        spec["identity_training_role"],
    )
    return _unique_sentences(
        purpose, spec["description"], _photo_base(), identity, _complexion_lock(profile),
        body_only, body_scope, presentation_text, _skin(profile),
        _region_marks(profile, regions, presentation),
        _special_region_authority(spec["shot_id"], regions),
        "keep every required boundary of the selected region inside the frame and keep unrelated regions outside the crop",
        _clean_phrase(suffix),
    )


class FCCKreaBlueprintDatasetDirector:
    CATEGORY = "character creation/studio"
    FUNCTION = "direct"
    DESCRIPTION = (
        "Stage 2 Krea2 director aligned to the canonical V2.4.17 anatomy object. Plan names advertise base counts, nonbinary identity no longer blends body anatomy, and the opt-in extreme plan contains true single-detail close-ups rather than regional torso crops."
    )
    RETURN_TYPES = ("STRING", "INT", "STRING", "STRING", "STRING", "INT", "INT", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("krea_prompts", "seeds", "shot_ids", "categories", "filename_prefixes", "widths", "heights", "dataset_plan_json", "queue_preview", "dashboard", "progress_labels")
    OUTPUT_IS_LIST = (True, True, True, True, True, True, True, False, False, False, True)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character_blueprint": ("CHARACTER_BLUEPRINT",),
                "dataset_plan": (KREA_BLUEPRINT_PLANS, {"default": KREA_BLUEPRINT_PLANS[0]}),
                "project_name": ("STRING", {"default": "FCC_Character"}),
                "starting_seed": ("INT", {"default": 2000, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
                "variations_per_shot": ("INT", {"default": 1, "min": 1, "max": 3}),
            },
            "optional": {"prompt_suffix": ("STRING", {"default": "", "multiline": True})},
        }

    def direct(self, character_blueprint, dataset_plan, project_name, starting_seed, variations_per_shot, prompt_suffix=""):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan_name = str(dataset_plan)
        specs = _select_specs(plan_name, profile)
        prompts: list[str] = []
        seeds: list[int] = []
        shot_ids: list[str] = []
        categories: list[str] = []
        prefixes: list[str] = []
        widths: list[int] = []
        heights: list[int] = []
        manifest: list[dict[str, Any]] = []
        root = f"{str(project_name).strip() or 'FCC_Character'}/Stage_2_Krea_PreLoRA_Documentation"
        index = 0
        for spec in specs:
            for variation in range(int(variations_per_shot)):
                index += 1
                sid = f"{spec['shot_id']}_v{variation + 1:02d}"
                seed = int(starting_seed) + index - 1
                prompt = _build_prompt(profile, spec, prompt_suffix)
                if spec.get("category") == "extreme_clinical_validation":
                    prompt = _unique_sentences(prompt, _extreme_authority(profile, spec))
                prefix = f"{root}/{spec['category']}/{index:04d}_{sid}"
                prompts.append(prompt); seeds.append(seed); shot_ids.append(sid); categories.append(spec["category"]); prefixes.append(prefix)
                widths.append(int(spec["width"])); heights.append(int(spec["height"]))
                manifest.append({
                    "index": index, "shot_id": sid, "category": spec["category"], "seed": seed,
                    "filename_prefix": prefix, "width": spec["width"], "height": spec["height"],
                    "presentation": spec["presentation"], "regions": sorted(spec["regions"]),
                    "identity_training_role": spec["identity_training_role"],
                    "face_identity_source": spec["category"] == "identity_anchor",
                    "body_only": spec["category"] != "identity_anchor",
                    "optional_validation_only": spec["category"] == "extreme_clinical_validation",
                    "resolved_chest_anatomy": _resolved_chest(profile),
                    "resolved_groin_anatomy": _resolved_groin(profile),
                    "male_genital_state": profile.get("male_genital_state", "Not applicable"),
                    "prompt": prompt,
                })
        total = len(manifest)
        variations = int(variations_per_shot)
        base_count = len(specs)
        progress = [f"{item['index']} of {total} | {item['category']} | {item['shot_id']}" for item in manifest]
        plan_json = json.dumps({
            "schema": "FCC_KREA_STAGE2_CANONICAL_ATLAS_V257", "schema_version": 7,
            "character_id": profile.get("character_id", "character"), "dataset_plan": plan_name,
            "base_shots": base_count, "variations_per_shot": variations, "total_items": total,
            "resolved_chest_anatomy": _resolved_chest(profile), "resolved_groin_anatomy": _resolved_groin(profile),
            "male_genital_state": profile.get("male_genital_state", "Not applicable"),
            "body_only_rule": "All non-anchor Stage 2 records exclude the complete face and facial features.",
            "canonical_anatomy_rule": "Every regional item consumes the same exclusive resolved chest/groin object as Stage 0; Adult Nonbinary identity never blends anatomy categories.",
            "extreme_clinical_rule": "The opt-in extreme plan contains true single-detail close-ups, is stored separately, and is excluded from automatic identity-LoRA selection.",
            "progress_note": "ComfyUI list execution may refresh previews after the queued list completes; use the item router for one-record-at-a-time inspection.",
            "manual_review": "Every generated image requires manual approval.", "items": manifest,
        }, indent=2, ensure_ascii=False)
        preview = "\n".join(f"{item['index']:03d} | {item['category']} | {item['shot_id']} | {item['width']}x{item['height']}" for item in manifest)
        dashboard = "\n".join([
            "FCC STAGE 2 — KREA CANONICAL DOCUMENTATION V2.4.17",
            f"Character: {profile.get('character_id', 'character')}", f"Plan: {plan_name}",
            f"Base shots: {base_count}", f"Variations per shot: {variations}", f"TOTAL OUTPUTS: {total}",
            f"Resolved chest: {_resolved_chest(profile)}", f"Resolved groin: {_resolved_groin(profile)}",
            "BODY ATLAS: body-only records exclude the complete face.",
            "EXTREME CLINICAL: true single-detail opt-in close-ups; never silently added to LoRA training.",
        ])
        return prompts, seeds, shot_ids, categories, prefixes, widths, heights, plan_json, preview, dashboard, progress


class FCCFaceAngleDatasetDirector(FCCFaceAngleDatasetDirectorV256):
    DESCRIPTION = (
        "Stage 3 Qwen director registered to V2.4.17. Qwen remains manually reviewed and is intentionally unchanged while Stage 0 and Stage 2 are validated."
    )
