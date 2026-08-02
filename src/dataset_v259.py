from __future__ import annotations

import copy
import json
import re
from typing import Any

from .nodes_v230 import _clean_phrase, _sentences
from .nodes_v259 import (
    CORE_VERSION,
    _clean_skin_authority_v259,
    _piercing_prompt_v259,
    _scar_prompt_v259,
    _tattoo_prompt_v259,
)
from .dataset_v254 import (
    FCCKreaQueueItemRouter,
    _anchor_specs,
    _body_only_authority,
    _face_identity,
    _photo_base,
    _regional_outfit,
    _regional_specs,
    _skin,
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
from .dataset_v258 import (
    _extreme_specs as _extreme_specs_v258,
    _region_marks,
)

# Counts are base-shot counts before Variations Per Shot is applied.
KREA_BLUEPRINT_PLANS = [
    "Identity Anchors — 3",
    "Body-Only Regional Atlas — Clothed (102)",
    "Body-Only Regional Atlas — Clinical Unclothed (102)",
    "Complete Body-Only Regional Atlas — Clothed and Clinical (204)",
    "Extreme Clinical Anatomy Close-Ups — Krea Structural Draft (count shown after blueprint)",
    "Complete Pre-LoRA Documentation — Anchors + Body Atlas (207)",
]


def _nonface_identity_v259(profile: dict[str, Any]) -> str:
    heritage = _clean_phrase(profile.get("heritage_prompt", ""))
    body = _clean_phrase(profile.get("body_type_authority_prompt", ""))
    return _unique_sentences(
        "one adult primary subject",
        profile.get("age_range", "") and f"age range {profile.get('age_range')}",
        heritage,
        body,
        profile.get("height", "") and f"selected height category {profile.get('height')}",
        profile.get("gluteal_build", "") and f"selected gluteal build {profile.get('gluteal_build')}",
        "the subject's identity label does not alter or blend the independently resolved chest and groin anatomy",
    )


def _complexion_lock_v259(profile: dict[str, Any]) -> str:
    selected = str(profile.get("skin_tone", "") or "").strip().lower()
    return _unique_sentences(
        f"the documented region retains the same selected underlying {selected} skin tone" if selected else "the documented region retains the selected underlying complexion",
        "lighting changes highlights and shadows only; it does not lighten, tan, recolor, or replace the underlying skin tone",
        profile.get("base_complexion_stability_prompt", ""),
    )


def _spec_metadata(shot_id: str, regions: set[str]) -> dict[str, Any]:
    sid = str(shot_id)
    meta: dict[str, Any] = {
        "crop_class": "true_extreme_single_detail",
        "target_surface": "local skin surface",
        "camera_view": "direct view of the named surface",
        "camera_elevation": "surface-normal documentation angle",
        "identity_reference_required": True,
        "recommended_execution_lane": "Qwen reference edit from an approved same-character regional reference",
        "krea_role": "structural draft only; identity match is not guaranteed",
    }
    if "gluteal_fold" in sid:
        meta.update({
            "target_surface": "posterior gluteal fold",
            "camera_view": "strict direct rear close-up",
            "camera_elevation": "lens level with the gluteal fold",
        })
    elif "perineal" in sid or "scrotal_lower" in sid:
        meta.update({
            "target_surface": "inferior or rear-lower perineal surface",
            "camera_view": "rear-lower or underside close-up",
            "camera_elevation": "lens aligned beneath the pelvis",
        })
    elif "left_profile" in sid:
        meta.update({"target_surface": "anatomical left lateral surface", "camera_view": "strict anatomical-left profile close-up"})
    elif "right_profile" in sid:
        meta.update({"target_surface": "anatomical right lateral surface", "camera_view": "strict anatomical-right profile close-up"})
    elif "sole" in sid:
        meta.update({"target_surface": "plantar sole surface", "camera_view": "direct underside view of the sole"})
    elif "palm" in sid:
        meta.update({"target_surface": "palmar hand surface", "camera_view": "direct view perpendicular to the palm"})
    elif "heel" in sid:
        meta.update({"target_surface": "posterior heel and Achilles transition", "camera_view": "direct rear/underside heel close-up"})
    elif "nipple" in sid or "bust" in sid or "pectoral" in sid or "sternum" in sid:
        meta.update({"target_surface": "anterior chest detail", "camera_view": "direct frontal or named one-sided chest close-up"})
    elif "groin" in sid or "genital" in sid or "pubic" in sid:
        meta.update({"target_surface": "anterior groin detail", "camera_view": "direct frontal close-up unless the shot id explicitly names profile or rear-lower"})
    elif "fingertip" in sid:
        meta.update({"target_surface": "distal fingertip and nail surface", "camera_view": "direct macro view of fingertips only"})
    return meta


def _decorate_extreme_specs(profile: dict[str, Any]) -> list[dict[str, Any]]:
    specs = copy.deepcopy(_extreme_specs_v258(profile))
    for spec in specs:
        spec.update(_spec_metadata(str(spec.get("shot_id", "")), set(spec.get("regions", set()))))
    return specs


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
        return _decorate_extreme_specs(profile)
    return anchors + clothed + clinical


def _region_mark_text_v259(profile: dict[str, Any], regions: set[str], presentation: str) -> str:
    tattoos: list[dict[str, Any]] = []
    scars: list[dict[str, Any]] = []
    piercings: list[dict[str, Any]] = []
    for record in profile.get("tattoo_records", []) if isinstance(profile.get("tattoo_records"), list) else []:
        if isinstance(record, dict) and set(record.get("region_tags", [])) & regions:
            tattoos.append(record)
    for record in profile.get("scar_mole_beauty_mark_records", []) if isinstance(profile.get("scar_mole_beauty_mark_records"), list) else []:
        if isinstance(record, dict) and set(record.get("region_tags", [])) & regions:
            scars.append(record)
    for record in profile.get("piercing_records", []) if isinstance(profile.get("piercing_records"), list) else []:
        if isinstance(record, dict) and set(record.get("region_tags", [])) & regions:
            piercings.append(record)

    parts: list[str] = []
    for record in tattoos:
        text = _tattoo_prompt_v259(record, {})
        if presentation == "clothed":
            text = _sentences(text, "show the tattoo only on skin genuinely exposed inside this crop; do not remove clothing to expose unrelated areas")
        parts.append(text)
    parts.extend(_piercing_prompt_v259(record, {}) for record in piercings)
    parts.extend(_scar_prompt_v259(record) for record in scars)
    parts.append(_clean_skin_authority_v259(profile, tattoos, scars, piercings))
    return _unique_sentences(*parts)


def _clinical_body_v259(profile: dict[str, Any], regions: set[str]) -> str:
    return _unique_sentences(
        _clinical_body(profile, regions),
        "only the anatomy explicitly resolved for this documented region is present; do not add a second chest category or a second groin category",
    )


def _clothed_body_v259(profile: dict[str, Any], regions: set[str]) -> str:
    return _unique_sentences(
        _clothed_body(profile, regions),
        "the selected garment follows the resolved chest and body structure without changing it into athletic or compression clothing unless that exact garment was selected",
    )


def _extreme_authority_v259(profile: dict[str, Any], spec: dict[str, Any]) -> str:
    regions = set(spec.get("regions", set()))
    sid = str(spec.get("shot_id", ""))
    parts = [
        "TRUE EXTREME SINGLE-DETAIL AUTHORITY",
        f"target surface: {spec.get('target_surface', 'named local surface')}",
        f"camera: {spec.get('camera_view', 'direct local close-up')}",
        f"camera elevation: {spec.get('camera_elevation', 'surface-normal documentation angle')}",
        "the one named anatomical detail occupies approximately ninety to ninety-five percent of the frame",
        "show only the named feature and the minimum immediately adjacent tissue required to prove natural attachment",
        "exclude the complete head, face, torso, pelvis, limb, full person, distant body, split view, collage, and regional-atlas composition",
        "do not replace the target with a different surface simply because that surface is easier to show",
        "this Krea output is a structural draft; exact same-person identity requires the recommended Qwen reference-edit handoff",
        "this opt-in validation image is excluded from automatic identity-LoRA training until manually approved",
    ]
    if "gluteal_fold" in sid:
        parts.extend([
            "the visible anatomy is posterior: buttock surface above and posterior upper-thigh surface below",
            "the front groin, pubic mound, lower abdomen, and anterior thigh remain outside the frame",
        ])
    if regions & {"chest", "breast", "bust", "pectoral", "nipple", "areola", "sternum"}:
        parts.extend([
            profile.get("active_chest_anatomy_prompt", profile.get("chest_anatomy_prompt", "")),
            profile.get("active_chest_integrity_prompt", profile.get("chest_region_integrity_prompt", "")),
            "the selected chest size and geometry remain identical to the canonical blueprint; do not resize or replace the chest for this crop",
        ])
    if regions & {"groin", "pubic", "genital", "male_genital", "female_genital", "perineal", "suprapubic"}:
        parts.extend([
            profile.get("groin_anatomy_prompt", ""),
            profile.get("pubic_hair_prompt", ""),
            profile.get("sex_anatomy_integrity_prompt", profile.get("groin_region_integrity_prompt", "")),
        ])
    if regions & {"buttocks", "gluteal", "left_buttock", "right_buttock"}:
        parts.append("preserve the configured gluteal build while showing only the named posterior fold or surface detail")
    return _unique_sentences(*parts)


def _build_prompt_v259(profile: dict[str, Any], spec: dict[str, Any], suffix: str) -> str:
    regions = set(spec["regions"])
    presentation = str(spec["presentation"])
    anchor = spec["category"] == "identity_anchor"
    identity = _face_identity(profile) if anchor else _nonface_identity_v259(profile)
    body_only = "" if anchor else _body_only_authority()
    if presentation == "clinical":
        presentation_text = _clinical_body_v259(profile, regions)
        body_scope = ""
    elif presentation == "clothed":
        presentation_text = _regional_outfit(profile, regions)
        body_scope = _clothed_body_v259(profile, regions)
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
    base = _unique_sentences(
        purpose,
        spec["description"],
        _photo_base(),
        identity,
        _complexion_lock_v259(profile),
        body_only,
        body_scope,
        presentation_text,
        _skin(profile),
        _region_mark_text_v259(profile, regions, presentation),
        "keep every required boundary of the selected region inside the frame and keep unrelated regions outside the crop",
        _clean_phrase(suffix),
    )
    if spec.get("category") == "extreme_clinical_validation":
        return _unique_sentences(base, _extreme_authority_v259(profile, spec))
    return base


class FCCKreaBlueprintDatasetDirector:
    CATEGORY = "character creation/studio"
    FUNCTION = "direct"
    DESCRIPTION = (
        "Stage 2 canonical body director. Regional records stay Krea blueprint renders; extreme records carry explicit target-surface/camera metadata and are labeled Krea structural drafts requiring Qwen reference-edit handoff for exact identity."
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
                prompt = _build_prompt_v259(profile, spec, prompt_suffix)
                prefix = f"{root}/{spec['category']}/{index:04d}_{sid}"
                prompts.append(prompt)
                seeds.append(seed)
                shot_ids.append(sid)
                categories.append(spec["category"])
                prefixes.append(prefix)
                widths.append(int(spec["width"]))
                heights.append(int(spec["height"]))
                manifest.append({
                    "index": index,
                    "shot_id": sid,
                    "category": spec["category"],
                    "seed": seed,
                    "filename_prefix": prefix,
                    "width": spec["width"],
                    "height": spec["height"],
                    "presentation": spec["presentation"],
                    "regions": sorted(spec["regions"]),
                    "identity_training_role": spec["identity_training_role"],
                    "face_identity_source": spec["category"] == "identity_anchor",
                    "body_only": spec["category"] != "identity_anchor",
                    "optional_validation_only": spec["category"] == "extreme_clinical_validation",
                    "resolved_chest_anatomy": _resolved_chest(profile),
                    "resolved_groin_anatomy": _resolved_groin(profile),
                    "male_genital_state": profile.get("male_genital_state", "Not applicable"),
                    "crop_class": spec.get("crop_class", "regional_documentation"),
                    "target_surface": spec.get("target_surface", "regional surface"),
                    "camera_view": spec.get("camera_view", "director-defined regional view"),
                    "camera_elevation": spec.get("camera_elevation", "director-defined"),
                    "identity_reference_required": bool(spec.get("identity_reference_required", False)),
                    "recommended_execution_lane": spec.get("recommended_execution_lane", "Krea blueprint text-to-image"),
                    "krea_role": spec.get("krea_role", "canonical regional blueprint render"),
                    "prompt": prompt,
                })
        total = len(manifest)
        variations = int(variations_per_shot)
        base_count = len(specs)
        progress = [f"{item['index']} of {total} | {item['category']} | {item['shot_id']}" for item in manifest]
        plan_json = json.dumps({
            "schema": "FCC_KREA_STAGE2_CANONICAL_ATLAS_V259",
            "schema_version": 9,
            "character_id": profile.get("character_id", "character"),
            "dataset_plan": plan_name,
            "base_shots": base_count,
            "variations_per_shot": variations,
            "total_items": total,
            "resolved_count_label": f"{base_count} base shots / {total} total outputs",
            "resolved_chest_anatomy": _resolved_chest(profile),
            "resolved_groin_anatomy": _resolved_groin(profile),
            "male_genital_state": profile.get("male_genital_state", "Not applicable"),
            "body_only_rule": "All non-anchor Stage 2 records exclude the complete face and facial features.",
            "extreme_rule": "Extreme Krea records are structural drafts. Exact same-person identity requires reference-conditioned Qwen edit from an approved same-character regional reference.",
            "manual_review": "Every generated image requires manual approval.",
            "items": manifest,
        }, indent=2, ensure_ascii=False)
        preview_lines = [f"RESOLVED COUNT: {base_count} base shots | {total} total outputs"]
        preview_lines.extend(
            f"{item['index']:03d} | {item['category']} | {item['shot_id']} | {item['width']}x{item['height']}"
            for item in manifest
        )
        preview = "\n".join(preview_lines)
        extreme = any(item["optional_validation_only"] for item in manifest)
        dashboard = "\n".join([
            "FCC STAGE 2 — CANONICAL DOCUMENTATION V2.4.19",
            f"Character: {profile.get('character_id', 'character')}",
            f"Plan: {plan_name}",
            f"RESOLVED BASE SHOTS: {base_count}",
            f"VARIATIONS PER SHOT: {variations}",
            f"TOTAL OUTPUTS: {total}",
            f"Resolved chest: {_resolved_chest(profile)}",
            f"Resolved groin: {_resolved_groin(profile)}",
            "BODY ATLAS: body-only regional records exclude the complete face.",
            "EXTREME STATUS: Krea structural draft; Qwen reference-edit handoff required for exact identity." if extreme else "EXTREME STATUS: not active in this plan.",
            "MANUAL REVIEW: required for every output.",
        ])
        return prompts, seeds, shot_ids, categories, prefixes, widths, heights, plan_json, preview, dashboard, progress


class FCCFaceAngleDatasetDirector(FCCFaceAngleDatasetDirectorV256):
    DESCRIPTION = (
        "Stage 3 Qwen face-angle director registered to V2.4.19. Existing angle behavior remains unchanged while Stage 2 regional and extreme handoff validation proceeds."
    )
