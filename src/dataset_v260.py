from __future__ import annotations

import copy
import json
from typing import Any

from .dataset_v254 import FCCKreaQueueItemRouter, _spec
from .dataset_v256 import _resolved_chest, _resolved_groin
from .dataset_v258 import _extreme_specs as _extreme_specs_v258
from .dataset_v259 import (
    FCCFaceAngleDatasetDirector as FCCFaceAngleDatasetDirectorV259,
    KREA_BLUEPRINT_PLANS,
    _build_prompt_v259,
    _select_specs as _select_specs_v259,
    _spec_metadata,
)
from .macro_v260 import build_stage2_macro
from .nodes_v260 import CORE_VERSION


def _native_chest_specs(profile: dict[str, Any]) -> list[dict[str, Any]]:
    role = "OPTIONAL EXTREME CLINICAL VALIDATION ONLY — EXCLUDE FROM DEFAULT IDENTITY-LORA DATASET"
    resolved = _resolved_chest(profile)
    if resolved == "Flat / Neutral Chest":
        rows = [
            ("extreme_flat_sternum_transition", "native macro of the central flat-neutral sternum and medial chest transition", {"chest", "neutral_chest", "sternum"}),
            ("extreme_left_nipple_areola", "native macro of exactly one anatomical-left nipple and complete areola on the flat-neutral chest", {"chest", "neutral_chest", "left_nipple", "areola"}),
            ("extreme_right_nipple_areola", "native macro of exactly one anatomical-right nipple and complete areola on the flat-neutral chest", {"chest", "neutral_chest", "right_nipple", "areola"}),
        ]
    elif resolved == "Custom Chest Description":
        rows = [
            ("extreme_custom_chest_sternum_transition", "native macro of the central sternum and medial custom-chest transition", {"chest", "custom_chest", "sternum"}),
            ("extreme_left_nipple_areola", "native macro of exactly one anatomical-left nipple and complete areola on the configured custom chest", {"chest", "custom_chest", "left_nipple", "areola"}),
            ("extreme_right_nipple_areola", "native macro of exactly one anatomical-right nipple and complete areola on the configured custom chest", {"chest", "custom_chest", "right_nipple", "areola"}),
        ]
    else:
        # Bust and masculine routes already contain exact left/right nipple/areola,
        # lower-contour/boundary, and sternum records. Reuse those definitions.
        all_specs = _extreme_specs_v258(profile)
        chest_specs = [s for s in all_specs if set(s.get("regions", set())) & {"chest", "breast", "bust", "pectoral", "nipple", "areola", "sternum", "left_nipple", "right_nipple"}]
        return chest_specs
    return [_spec(sid, "extreme_clinical_validation", desc, "clinical", regs, 1024, 1024, role) for sid, desc, regs in rows]


def _native_extreme_specs(profile: dict[str, Any]) -> list[dict[str, Any]]:
    original = copy.deepcopy(_extreme_specs_v258(profile))
    non_chest = [
        s for s in original
        if not (set(s.get("regions", set())) & {"chest", "breast", "bust", "pectoral", "nipple", "areola", "sternum", "neutral_chest", "custom_chest", "left_nipple", "right_nipple"})
    ]
    specs = _native_chest_specs(profile) + non_chest
    for spec in specs:
        spec.update(_spec_metadata(str(spec.get("shot_id", "")), set(spec.get("regions", set()))))
        spec["crop_class"] = "native_clinical_macro_single_detail"
        spec["macro_compiler"] = "FCC_NATIVE_CLINICAL_MACRO_V260"
        spec["native_macro"] = True
        spec["identity_reference_required"] = True
        spec["recommended_execution_lane"] = "Krea native macro structural draft; optional Qwen reference edit for exact same-person identity"
        spec["krea_role"] = "native local macro structural draft only; manual approval required"
    return specs


def _select_specs_v260(plan: str, profile: dict[str, Any]) -> list[dict[str, Any]]:
    if plan == KREA_BLUEPRINT_PLANS[4]:
        return _native_extreme_specs(profile)
    return _select_specs_v259(plan, profile)


def _build_prompt_v260(profile: dict[str, Any], spec: dict[str, Any], suffix: str) -> tuple[str, dict[str, Any]]:
    if spec.get("category") == "extreme_clinical_validation":
        return build_stage2_macro(profile, spec, suffix)
    return _build_prompt_v259(profile, spec, suffix), {}


class FCCKreaBlueprintDatasetDirector:
    CATEGORY = "character creation/studio"
    FUNCTION = "direct"
    DESCRIPTION = (
        "Stage 2 V2.4.20 director. Regional atlas behavior is preserved. Extreme Clinical uses a native local-only macro compiler instead of full-character construction followed by a regional crop."
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
        specs = _select_specs_v260(plan_name, profile)
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
                prompt, macro_meta = _build_prompt_v260(profile, spec, prompt_suffix)
                prefix = f"{root}/{spec['category']}/{index:04d}_{sid}"
                prompts.append(prompt)
                seeds.append(seed)
                shot_ids.append(sid)
                categories.append(spec["category"])
                prefixes.append(prefix)
                widths.append(int(spec["width"]))
                heights.append(int(spec["height"]))
                item = {
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
                    "macro_compiler": spec.get("macro_compiler", ""),
                    "native_macro": bool(spec.get("native_macro", False)),
                    "prompt": prompt,
                }
                item.update(macro_meta)
                manifest.append(item)
        total = len(manifest)
        variations = int(variations_per_shot)
        base_count = len(specs)
        progress = [f"{item['index']} of {total} | {item['category']} | {item['shot_id']}" for item in manifest]
        plan_json = json.dumps({
            "schema": "FCC_KREA_STAGE2_CANONICAL_ATLAS_V260",
            "schema_version": 10,
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
            "extreme_rule": "Extreme records use FCC_NATIVE_CLINICAL_MACRO_V260: one local target at native source magnification, local canonical anatomy only, intersecting permanent details only, and no full-character prompt construction.",
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
            "FCC STAGE 2 — CANONICAL DOCUMENTATION V2.4.20",
            f"Character: {profile.get('character_id', 'character')}",
            f"Plan: {plan_name}",
            f"RESOLVED BASE SHOTS: {base_count}",
            f"VARIATIONS PER SHOT: {variations}",
            f"TOTAL OUTPUTS: {total}",
            f"Resolved chest: {_resolved_chest(profile)}",
            f"Resolved groin: {_resolved_groin(profile)}",
            "BODY ATLAS: body-only regional records exclude the complete face.",
            "EXTREME STATUS: native single-detail macro structural drafts; Qwen reference-edit handoff remains optional for exact identity." if extreme else "EXTREME STATUS: not active in this plan.",
            "MANUAL REVIEW: required for every output.",
        ])
        return prompts, seeds, shot_ids, categories, prefixes, widths, heights, plan_json, preview, dashboard, progress


class FCCFaceAngleDatasetDirector(FCCFaceAngleDatasetDirectorV259):
    DESCRIPTION = (
        "Stage 3 Qwen face-angle director registered to V2.4.20. Existing clean angle behavior remains unchanged."
    )


__all__ = [
    "FCCKreaBlueprintDatasetDirector",
    "FCCFaceAngleDatasetDirector",
    "FCCKreaQueueItemRouter",
    "KREA_BLUEPRINT_PLANS",
]
