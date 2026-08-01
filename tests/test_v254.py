import json

from full_character_creation_core import NODE_CLASS_MAPPINGS
from full_character_creation_core.src.dataset_v254 import (
    FCCFaceAngleDatasetDirector,
    FCCKreaBlueprintDatasetDirector,
    KREA_BLUEPRINT_PLANS,
    QWEN_ANGLE_TARGETS,
    _select_specs,
)
from full_character_creation_core.src.nodes_v254 import _piercing_record_prompt_v254


def test_v254_registry_is_current_only():
    assert set(NODE_CLASS_MAPPINGS) == {
        "QwenDatasetQueue", "FCCDatasetDirector", "FCCQueueItemRouter",
        "FCCKreaBlueprintDatasetDirector", "FCCKreaQueueItemRouter",
        "CharacterBlueprintCreatorV254", "CharacterShotControlV254", "CharacterPromptAssemblerV254",
        "FCCQwenAnglePromptMode", "FCCSupportPanel",
    }


def test_stage2_plans_remove_general_midshot_fullbody_matrix():
    assert KREA_BLUEPRINT_PLANS[0] == "Identity Anchors — 3"
    complete = _select_specs("Complete Pre-LoRA Documentation — Anchors + Body Atlas")
    categories = {item["category"] for item in complete}
    assert "canonical_midshot" not in categories
    assert "canonical_full_body" not in categories
    assert sum(1 for item in complete if item["category"] == "identity_anchor") == 3
    assert any(item["shot_id"].endswith("left_palm") for item in complete)
    assert any(item["shot_id"].endswith("right_foot_outer_profile") for item in complete)
    assert any(item["shot_id"].endswith("full_back_rear_left") for item in complete)


def test_stage2_body_only_prompts_and_special_hand_foot_geometry():
    director = FCCKreaBlueprintDatasetDirector()
    profile = {
        "character_id": "test_character",
        "gender_authority_prompt": "adult woman",
        "age_range": "25–34",
        "heritage_prompt": "Caribbean heritage",
        "body_type_authority_prompt": "athletic adult build",
        "anatomy_upper_body": "athletic upper body",
        "anatomy_lower_body": "balanced lower body",
        "base_complexion_stability_prompt": "medium complexion remains consistent",
        "tattoo_records": [{
            "location": "Right Forearm",
            "description": "colored hummingbird with an orchid",
            "quantity": 1,
            "region_tags": ["right_forearm", "forearm", "arms"],
        }],
    }
    out = director.direct(profile, "Body-Only Regional Atlas — Clinical Unclothed", "Test", 2000, 1, "")
    prompts, shot_ids, plan_json = out[0], out[2], out[7]
    mapping = dict(zip(shot_ids, prompts))
    palm = next(v for k, v in mapping.items() if "right_palm" in k)
    assert "camera positioned directly above" in palm
    assert "no head, torso, pelvis" in palm
    foot = next(v for k, v in mapping.items() if "right_foot_dorsal" in k)
    assert "foot naturally pointed downward" in foot
    assert "no knee unless needed" in foot
    forearm = next(v for k, v in mapping.items() if "right_forearm_outer" in k)
    assert "hummingbird" in forearm
    assert "complete face and facial features remain outside the frame" in forearm
    data = json.loads(plan_json)
    assert data["schema"] == "FCC_KREA_STAGE2_REGIONAL_ATLAS_V254"
    assert all(item["body_only"] for item in data["items"])


def test_stage3_supports_face_midshot_fullbody_and_regional_targets():
    director = FCCFaceAngleDatasetDirector()
    expected = {
        QWEN_ANGLE_TARGETS[0]: (8, 1024, 1280, "close_up"),
        QWEN_ANGLE_TARGETS[1]: (12, 1024, 1280, "close_up"),
        QWEN_ANGLE_TARGETS[2]: (8, 1024, 1280, "medium_shot"),
        QWEN_ANGLE_TARGETS[3]: (8, 1024, 1536, "wide_shot"),
        QWEN_ANGLE_TARGETS[4]: (8, 1024, 1024, "close_up"),
    }
    for target, (count, width, height, distance) in expected.items():
        out = director.direct({}, target, "Image 1", "Test", 1000, 1, 8, False)
        assert len(out[0]) == count
        assert set(out[5]) == {width}
        assert set(out[6]) == {height}
        plan = json.loads(out[7])
        assert all(item["distance"] == distance for item in plan["items"])
        assert plan["manual_review"].startswith("Every image")


def test_multiple_same_nostril_hoops_do_not_split_across_sides():
    prompt = _piercing_record_prompt_v254({
        "location": "Right Nostril",
        "material": "Steel",
        "jewelry_type": "Hoop",
        "quantity": 2,
    }, {"camera_view": "Front View"})
    assert "exactly two separate" in prompt
    assert "same anatomical right location" in prompt
    assert "anatomical left corresponding location remains completely unpierced" in prompt
    assert "do not place one item on each side" in prompt
