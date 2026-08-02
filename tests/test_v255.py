import json

from full_character_creation_core import NODE_CLASS_MAPPINGS
from full_character_creation_core.src.nodes_v245 import EXTENDED_PUPPY
from full_character_creation_core.src.nodes_v247 import ALL_FOURS
from full_character_creation_core.src.nodes_v255 import (
    CharacterBlueprintCreatorV255,
    CharacterShotControlV255,
)
from full_character_creation_core.src.dataset_v255 import (
    FCCKreaBlueprintDatasetDirector,
    KREA_BLUEPRINT_PLANS,
    _select_specs,
)
from full_character_creation_core.src.workflow_tools import FCCQwenAnglePromptMode


def _defaults(cls):
    values = {}
    for section in ("required", "optional"):
        for name, spec in cls.INPUT_TYPES().get(section, {}).items():
            if name in {"character_blueprint", "shot_plan"}:
                continue
            kind = spec[0]
            cfg = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
            if "default" in cfg:
                values[name] = cfg["default"]
            elif isinstance(kind, list):
                values[name] = kind[0]
            elif kind == "STRING":
                values[name] = ""
            elif kind == "INT":
                values[name] = 0
            elif kind == "FLOAT":
                values[name] = 0.0
            elif kind == "BOOLEAN":
                values[name] = False
            else:
                values[name] = ""
    return values


def _profile():
    values = _defaults(CharacterBlueprintCreatorV255)
    values.update({"tattoo_status": "None", "piercing_status": "None"})
    return CharacterBlueprintCreatorV255().build_blueprint_v255(**values)[8]


def _plan(pose, view="Back View", height="Eye Level"):
    values = _defaults(CharacterShotControlV255)
    values.update({
        "shot_type": "Three-Quarter Body",
        "camera_view": view,
        "camera_height": height,
        "pose": pose,
        "lens": "50mm Normal",
        "aspect_ratio": "Auto by Shot",
    })
    return CharacterShotControlV255().build_shot_plan_v255(character_blueprint=_profile(), **values)[0]


def test_v255_registry_is_current_only():
    assert "CharacterBlueprintCreatorV260" in NODE_CLASS_MAPPINGS
    assert "CharacterShotControlV260" in NODE_CLASS_MAPPINGS
    assert "CharacterPromptAssemblerV260" in NODE_CLASS_MAPPINGS
    assert not any(name.endswith("V254") for name in NODE_CLASS_MAPPINGS)


def test_all_fours_back_view_is_strict_direct_rear_not_three_quarter():
    plan = _plan(ALL_FOURS, "Back View", "Eye Level")
    camera = plan["camera_prompt"].lower()
    assert plan["rear_all_fours_lock"] is True
    assert "six-o'clock position directly behind the sacrum" in camera
    assert "centered exactly on the spinal midline" in camera
    assert "balanced left-right symmetry" in camera
    assert "not rear three-quarter" in camera
    assert "zero downward tilt" in camera


def test_extended_puppy_arms_are_forward_parallel_and_not_sideways():
    plan = _plan(EXTENDED_PUPPY, "Back View", "Eye Level")
    pose = plan["pose_prompt"].lower()
    assert "reach straight forward from the shoulders" in pose
    assert "parallel to one another" in pose
    assert "parallel to the body's head-to-pelvis axis" in pose
    assert "beyond the crown of the head" in pose
    assert "do not spread sideways" in pose
    assert "do not form a t shape" in pose


def test_extended_puppy_eye_level_and_low_angle_are_physically_distinct():
    eye = _plan(EXTENDED_PUPPY, "Back View", "Eye Level")["camera_prompt"].lower()
    low = _plan(EXTENDED_PUPPY, "Back View", "Low Angle")["camera_prompt"].lower()
    assert "sixty to eighty centimeters above the floor" in eye
    assert "zero downward tilt" in eye
    assert "ten to twenty centimeters above the floor" in low
    assert "angles upward" in low
    assert eye != low
    assert "only camera-height option that uses a true overhead view" not in eye
    assert "only camera-height option that uses a true overhead view" not in low


def test_extreme_clinical_lane_is_opt_in_and_not_in_complete_plan():
    assert "Extreme Clinical Body Validation — Opt-In Only" in KREA_BLUEPRINT_PLANS
    complete = _select_specs("Complete Pre-LoRA Documentation — Anchors + Body Atlas")
    extreme = _select_specs("Extreme Clinical Body Validation — Opt-In Only")
    assert extreme
    assert all(item["category"] == "extreme_clinical_validation" for item in extreme)
    assert not any(item["category"] == "extreme_clinical_validation" for item in complete)
    assert any("nipple_areola" in item["shot_id"] for item in extreme)
    assert any("pubic_mound" in item["shot_id"] for item in extreme)
    assert any("gluteal_fold" in item["shot_id"] for item in extreme)


def test_extreme_clinical_prompts_are_body_only_and_excluded_from_default_lora():
    director = FCCKreaBlueprintDatasetDirector()
    profile = {
        "character_id": "test_character",
        "gender_authority_prompt": "adult woman",
        "age_range": "25–34",
        "body_type_authority_prompt": "balanced adult build",
        "anatomy_upper_body": "balanced upper-body anatomy",
        "anatomy_lower_body": "balanced lower-body anatomy",
        "bust_anatomy_authority_prompt": "medium natural bust",
        "groin_anatomy_prompt": "adult female external anatomy in a neutral non-aroused state",
        "pubic_hair_prompt": "natural pubic hair coverage",
        "base_complexion_stability_prompt": "complexion remains consistent",
    }
    out = director.direct(profile, "Extreme Clinical Body Validation — Opt-In Only", "Test", 3000, 1, "")
    plan = json.loads(out[7])
    assert plan["schema"] == "FCC_KREA_STAGE2_REGIONAL_ATLAS_V255"
    assert all(item["body_only"] for item in plan["items"])
    assert all(item["optional_validation_only"] for item in plan["items"])
    prompt = out[0][0].lower()
    assert "complete head, face, and all facial features remain outside the frame" in prompt
    assert "not automatically approved for identity-lora training" in prompt


def test_qwen_reference_rule_changes_by_target_category():
    tool = FCCQwenAnglePromptMode()
    _, regional = tool.build_prompt(
        "camera-only angle expansion",
        "regional_reference_angle__back__eye_level__close_up_v01",
        "regional_reference_angle",
        "Qwen Image Edit 2511 — Multiple Angles <sks>",
    )
    assert "body-only regional reference" in regional
    assert "do not substitute a face portrait" in regional
    _, face = tool.build_prompt(
        "camera-only angle expansion",
        "face__front__eye_level__close_up_v01",
        "face_identity_angle",
        "Qwen Image Edit 2511 — Multiple Angles <sks>",
    )
    assert "face anchor or face-close" in face
