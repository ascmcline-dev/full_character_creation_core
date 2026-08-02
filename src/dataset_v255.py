from __future__ import annotations

import json
from typing import Any

from .nodes_v230 import _clean_phrase, _sentences
from .dataset_v254 import (
    QWEN_ANGLE_TARGETS,
    FCCKreaQueueItemRouter,
    FCCFaceAngleDatasetDirector as FCCFaceAngleDatasetDirectorV254,
    _anchor_specs,
    _regional_specs,
    _spec,
    _build_krea_prompt,
    _slug,
    _unique_sentences,
)


KREA_BLUEPRINT_PLANS = [
    "Identity Anchors — 3",
    "Body-Only Regional Atlas — Clothed",
    "Body-Only Regional Atlas — Clinical Unclothed",
    "Complete Body-Only Regional Atlas — Clothed and Clinical",
    "Extreme Clinical Body Validation — Opt-In Only",
    "Complete Pre-LoRA Documentation — Anchors + Body Atlas",
]


def _extreme_clinical_specs() -> list[dict[str, Any]]:
    """Optional body-only micro documentation. Never part of the default plan."""
    role = "OPTIONAL EXTREME CLINICAL VALIDATION ONLY — EXCLUDE FROM DEFAULT IDENTITY-LORA DATASET"
    rows: list[tuple[str, str, set[str], int, int]] = [
        # Chest / breast surface and construction validation.
        ("extreme_chest_front_complete", "extreme close direct-front clinical documentation of the complete chest region with both lateral boundaries, sternum, complete lower contours, and a small amount of upper abdomen", {"chest", "breast", "upper_torso", "sternum"}, 1024, 1024),
        ("extreme_chest_front_left", "extreme close front-left three-quarter clinical documentation of the chest preserving complete projection and sternum relationship", {"chest", "breast", "upper_torso", "left_breast"}, 1024, 1024),
        ("extreme_chest_front_right", "extreme close front-right three-quarter clinical documentation of the chest preserving complete projection and sternum relationship", {"chest", "breast", "upper_torso", "right_breast"}, 1024, 1024),
        ("extreme_left_breast_profile", "extreme close true anatomical left profile of the left chest or breast with complete side contour and minimum rib attachment context", {"chest", "breast", "left_breast"}, 1024, 1024),
        ("extreme_right_breast_profile", "extreme close true anatomical right profile of the right chest or breast with complete side contour and minimum rib attachment context", {"chest", "breast", "right_breast"}, 1024, 1024),
        ("extreme_left_breast_lower_contour", "neutral extreme close lower-contour view of the anatomical left chest or breast, including the complete lower fold and minimum upper-abdomen attachment", {"chest", "breast", "left_breast"}, 1024, 1024),
        ("extreme_right_breast_lower_contour", "neutral extreme close lower-contour view of the anatomical right chest or breast, including the complete lower fold and minimum upper-abdomen attachment", {"chest", "breast", "right_breast"}, 1024, 1024),
        ("extreme_left_nipple_areola_front", "neutral extreme close direct-front documentation of the existing anatomical left nipple and surrounding areola only", {"chest", "breast", "left_breast", "left_nipple"}, 1024, 1024),
        ("extreme_right_nipple_areola_front", "neutral extreme close direct-front documentation of the existing anatomical right nipple and surrounding areola only", {"chest", "breast", "right_breast", "right_nipple"}, 1024, 1024),
        ("extreme_left_nipple_areola_profile", "neutral extreme close profile documentation of the existing anatomical left nipple and surrounding areola with minimum breast-surface context", {"chest", "breast", "left_breast", "left_nipple"}, 1024, 1024),
        ("extreme_right_nipple_areola_profile", "neutral extreme close profile documentation of the existing anatomical right nipple and surrounding areola with minimum breast-surface context", {"chest", "breast", "right_breast", "right_nipple"}, 1024, 1024),
        ("extreme_sternum_centerline", "extreme close direct-front clinical documentation of the sternum and central chest transition with both inner chest boundaries", {"chest", "breast", "sternum", "upper_torso"}, 1024, 1024),
        # Abdomen / navel.
        ("extreme_navel_front", "extreme close direct-front clinical documentation of the existing navel and immediately surrounding abdomen", {"abdomen", "waist", "navel"}, 1024, 1024),
        ("extreme_navel_left_oblique", "extreme close left-oblique clinical documentation of the existing navel and abdominal surface transition", {"abdomen", "waist", "navel", "left_side_torso"}, 1024, 1024),
        ("extreme_navel_right_oblique", "extreme close right-oblique clinical documentation of the existing navel and abdominal surface transition", {"abdomen", "waist", "navel", "right_side_torso"}, 1024, 1024),
        # Pelvis / pubic mound / groin.
        ("extreme_pubic_mound_front", "neutral extreme close direct-front clinical documentation of the pubic mound and lower-abdomen transition", {"pelvis", "groin", "pubic"}, 1024, 1024),
        ("extreme_pubic_mound_front_left", "neutral extreme close front-left three-quarter clinical documentation of the pubic mound and anatomical left groin transition", {"pelvis", "groin", "pubic", "left_groin"}, 1024, 1024),
        ("extreme_pubic_mound_front_right", "neutral extreme close front-right three-quarter clinical documentation of the pubic mound and anatomical right groin transition", {"pelvis", "groin", "pubic", "right_groin"}, 1024, 1024),
        ("extreme_groin_left_profile", "neutral extreme close anatomical left profile of the groin, pubic mound, and upper-inner-thigh attachment", {"pelvis", "groin", "pubic", "left_groin", "left_thigh"}, 1024, 1024),
        ("extreme_groin_right_profile", "neutral extreme close anatomical right profile of the groin, pubic mound, and upper-inner-thigh attachment", {"pelvis", "groin", "pubic", "right_groin", "right_thigh"}, 1024, 1024),
        ("extreme_groin_lower_view", "neutral non-aroused extreme close lower-angle clinical documentation of the groin and perineal attachment, framed only as anatomy validation", {"pelvis", "groin", "pubic", "perineal"}, 1024, 1024),
        # Rear pelvis / gluteal anatomy.
        ("extreme_gluteal_rear", "extreme close direct-rear clinical documentation of both buttocks, central cleft, lower-back transition, and both upper-thigh attachments", {"pelvis", "hips", "buttocks", "thigh"}, 1024, 1024),
        ("extreme_gluteal_rear_left", "extreme close rear-left three-quarter clinical documentation of the left gluteal contour and upper-thigh attachment", {"pelvis", "hips", "buttocks", "left_buttock", "left_thigh"}, 1024, 1024),
        ("extreme_gluteal_rear_right", "extreme close rear-right three-quarter clinical documentation of the right gluteal contour and upper-thigh attachment", {"pelvis", "hips", "buttocks", "right_buttock", "right_thigh"}, 1024, 1024),
        ("extreme_gluteal_left_profile", "extreme close anatomical left profile of the left gluteal contour, hip, and upper-thigh attachment", {"pelvis", "hips", "buttocks", "left_buttock", "left_thigh"}, 1024, 1024),
        ("extreme_gluteal_right_profile", "extreme close anatomical right profile of the right gluteal contour, hip, and upper-thigh attachment", {"pelvis", "hips", "buttocks", "right_buttock", "right_thigh"}, 1024, 1024),
        ("extreme_left_gluteal_fold", "neutral extreme close lower-rear documentation of the anatomical left gluteal fold and posterior upper-thigh attachment", {"buttocks", "left_buttock", "left_thigh"}, 1024, 1024),
        ("extreme_right_gluteal_fold", "neutral extreme close lower-rear documentation of the anatomical right gluteal fold and posterior upper-thigh attachment", {"buttocks", "right_buttock", "right_thigh"}, 1024, 1024),
        # Joint / limb micro validation not duplicated by broad regional views.
        ("extreme_left_armpit", "neutral extreme close documentation of the anatomical left axillary fold with upper-arm and side-chest attachment", {"shoulders", "upper_arm", "left_upper_arm", "left_axilla"}, 1024, 1024),
        ("extreme_right_armpit", "neutral extreme close documentation of the anatomical right axillary fold with upper-arm and side-chest attachment", {"shoulders", "upper_arm", "right_upper_arm", "right_axilla"}, 1024, 1024),
        ("extreme_left_elbow_crease", "extreme close direct documentation of the anatomical left elbow crease and connected upper-arm and forearm surfaces", {"arms", "elbow", "left_elbow"}, 1024, 1024),
        ("extreme_right_elbow_crease", "extreme close direct documentation of the anatomical right elbow crease and connected upper-arm and forearm surfaces", {"arms", "elbow", "right_elbow"}, 1024, 1024),
        ("extreme_left_knee_joint", "extreme close direct-front clinical documentation of the anatomical left knee joint with minimum thigh and shin attachment", {"legs", "knee", "left_knee"}, 1024, 1024),
        ("extreme_right_knee_joint", "extreme close direct-front clinical documentation of the anatomical right knee joint with minimum thigh and shin attachment", {"legs", "knee", "right_knee"}, 1024, 1024),
    ]
    return [
        _spec(f"clinical_{sid}", "extreme_clinical_validation", desc, "clinical", regions, width, height, role)
        for sid, desc, regions, width, height in rows
    ]


def _select_specs(plan: str) -> list[dict[str, Any]]:
    anchors = _anchor_specs()
    clothed = _regional_specs("clothed")
    clinical = _regional_specs("clinical")
    extreme = _extreme_clinical_specs()
    if plan == KREA_BLUEPRINT_PLANS[0]:
        return anchors
    if plan == KREA_BLUEPRINT_PLANS[1]:
        return clothed
    if plan == KREA_BLUEPRINT_PLANS[2]:
        return clinical
    if plan == KREA_BLUEPRINT_PLANS[3]:
        return clothed + clinical
    if plan == KREA_BLUEPRINT_PLANS[4]:
        return extreme
    # Deliberately excludes the opt-in extreme clinical lane.
    return anchors + clothed + clinical


def _extreme_authority(spec: dict[str, Any]) -> str:
    sid = str(spec.get("shot_id", "")).lower()
    parts = [
        "this is a neutral body-only extreme clinical validation image and not a portrait or scene photograph",
        "the selected region fills approximately sixty-five to eighty percent of the frame while retaining natural scale and rectilinear perspective",
        "increase camera distance instead of enlarging, flattening, shrinking, or distorting the anatomy",
        "the complete head, face, and all facial features remain outside the frame",
        "this optional validation record is not automatically approved for identity-LoRA training",
    ]
    if "nipple_areola" in sid:
        side = "left" if "left" in sid else "right"
        opposite = "right" if side == "left" else "left"
        parts.extend([
            f"exactly one existing anatomical {side} nipple and its surrounding areola are inside this one-sided crop",
            f"the anatomical {opposite} nipple and breast remain outside the frame",
            "do not create an additional nipple, duplicated areola, extra opening, or mirrored second side",
        ])
    if "breast" in sid or "chest" in sid or "sternum" in sid:
        parts.extend([
            "preserve the Character Blueprint chest base width, spacing, vertical position, projection, upper fullness, lower fullness, natural weight, and lower contour",
            "the crop adapts to the anatomy; the anatomy is never reduced to fit the crop",
        ])
    if "pubic" in sid or "groin" in sid:
        parts.extend([
            "neutral non-aroused clinical anatomy only with ordinary relaxed tissue and no sensual pose",
            "preserve the configured pubic-hair coverage and color wherever that surface is physically visible",
        ])
    if "gluteal" in sid:
        parts.append("preserve the configured gluteal build, side, contour, fold, and natural upper-thigh attachment without exaggeration or reshaping")
    return _unique_sentences(*parts)


def _build_krea_prompt_v255(profile: dict[str, Any], spec: dict[str, Any], suffix: str) -> str:
    prompt = _build_krea_prompt(profile, spec, suffix)
    if spec.get("category") == "extreme_clinical_validation":
        prompt = _unique_sentences(prompt, _extreme_authority(spec))
    return prompt


class FCCKreaBlueprintDatasetDirector:
    CATEGORY = "character creation/studio"
    FUNCTION = "direct"
    DESCRIPTION = (
        "Stage 2 Krea2 pre-LoRA director. It produces identity anchors, comprehensive face-excluded body regional atlases, and a separate opt-in extreme clinical body-validation lane. The opt-in lane is never included in Complete Pre-LoRA Documentation and is never automatically approved for LoRA training."
    )
    RETURN_TYPES = ("STRING", "INT", "STRING", "STRING", "STRING", "INT", "INT", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("krea_prompts", "seeds", "shot_ids", "categories", "filename_prefixes", "widths", "heights", "dataset_plan_json", "queue_preview", "dashboard", "progress_labels")
    OUTPUT_IS_LIST = (True, True, True, True, True, True, True, False, False, False, True)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character_blueprint": ("CHARACTER_BLUEPRINT",),
                "dataset_plan": (KREA_BLUEPRINT_PLANS, {"default": "Identity Anchors — 3"}),
                "project_name": ("STRING", {"default": "FCC_Character"}),
                "starting_seed": ("INT", {"default": 2000, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
                "variations_per_shot": ("INT", {"default": 1, "min": 1, "max": 3}),
            },
            "optional": {
                "prompt_suffix": ("STRING", {"default": "", "multiline": True}),
            },
        }

    def direct(self, character_blueprint, dataset_plan, project_name, starting_seed, variations_per_shot, prompt_suffix=""):
        profile = character_blueprint if isinstance(character_blueprint, dict) else {}
        plan_name = str(dataset_plan)
        specs = _select_specs(plan_name)
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
                prompt = _build_krea_prompt_v255(profile, spec, prompt_suffix)
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
                    "prompt": prompt,
                })

        total = len(manifest)
        progress = [f"{item['index']} of {total} | {item['category']} | {item['shot_id']}" for item in manifest]
        plan_json = json.dumps({
            "schema": "FCC_KREA_STAGE2_REGIONAL_ATLAS_V255",
            "schema_version": 5,
            "character_id": profile.get("character_id", "character"),
            "dataset_plan": plan_name,
            "total_items": total,
            "body_only_rule": "All non-anchor Stage 2 regional and extreme-clinical records exclude the complete face and facial features.",
            "extreme_clinical_rule": "Extreme Clinical Body Validation is opt-in only, stored separately, and excluded from the Complete Pre-LoRA plan and default identity-LoRA selection.",
            "manual_review": "Every generated image requires manual approval.",
            "items": manifest,
        }, indent=2, ensure_ascii=False)
        preview = "\n".join(
            f"{item['index']:03d} | {item['category']} | {item['shot_id']} | {item['width']}x{item['height']}"
            for item in manifest
        )
        dashboard = "\n".join([
            "FCC STAGE 2 — KREA PRE-LORA DOCUMENTATION",
            f"Character: {profile.get('character_id', 'character')}",
            f"Plan: {plan_name}",
            f"Total queued items: {total}",
            "IDENTITY ANCHORS: face-visible only in the dedicated anchor plan.",
            "BODY ATLAS: every regional record excludes the complete face.",
            "EXTREME CLINICAL: opt-in validation only; never silently added to LoRA training.",
        ])
        return prompts, seeds, shot_ids, categories, prefixes, widths, heights, plan_json, preview, dashboard, progress


class FCCFaceAngleDatasetDirector(FCCFaceAngleDatasetDirectorV254):
    DESCRIPTION = (
        "Stage 3 Qwen Image Edit angle-completion director. It accepts a manually approved Stage 2 face, midshot, full-body, or body-regional reference and produces feasible camera-angle candidates for manual review."
    )

    def direct(self, *args, **kwargs):
        result = list(super().direct(*args, **kwargs))
        try:
            plan = json.loads(result[7]) if result[7] else {}
        except Exception:
            plan = {}
        plan["schema"] = "FCC_QWEN_STAGE3_ANGLE_EXPANSION_V255"
        plan["schema_version"] = 5
        plan["reference_scope"] = (
            "Use an approved Stage 2 reference matching the selected target: face for face angles, midshot for midshot angles, full body for full-body angles, or body-only regional image for regional angles."
        )
        plan["manual_review"] = "Every result is generated for manual review; no automatic pass/reject gate is active."
        result[7] = json.dumps(plan, indent=2, ensure_ascii=False)
        result[9] = str(result[9]).replace(
            "Use an approved Stage 2 face, midshot, full-body, or regional reference appropriate to the selected target.",
            "Use an approved Stage 2 reference that matches the selected face, midshot, full-body, or body-regional target."
        )
        return tuple(result)
