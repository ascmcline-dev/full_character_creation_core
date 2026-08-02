import json

from full_character_creation_core import NODE_CLASS_MAPPINGS
from full_character_creation_core.src.nodes_v259 import (
    CharacterBlueprintCreatorV259,
    CharacterPromptAssemblerV259,
    CharacterShotControlV259,
)
from full_character_creation_core.src.dataset_v259 import (
    FCCKreaBlueprintDatasetDirector,
    KREA_BLUEPRINT_PLANS,
)


def defaults(cls):
    values = {}
    for name, spec in cls.INPUT_TYPES()["required"].items():
        kind = spec[0]
        options = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
        if isinstance(kind, list):
            values[name] = options.get("default", kind[0])
        elif kind == "STRING":
            values[name] = options.get("default", "")
        else:
            values[name] = options.get("default", 0)
    return values


def profile(**updates):
    kwargs = defaults(CharacterBlueprintCreatorV259)
    kwargs.update(updates)
    return CharacterBlueprintCreatorV259().build_blueprint_v259(**kwargs)[8]


def plan(p=None, **updates):
    kwargs = defaults(CharacterShotControlV259)
    if p is not None:
        kwargs["character_blueprint"] = p
    kwargs.update(updates)
    return CharacterShotControlV259().build_shot_plan_v259(**kwargs)[0]


def assemble(p, s):
    return CharacterPromptAssemblerV259().assemble_prompt_v259(
        p, s, "Krea — First Identity Image", "Image 1"
    )


def test_registry_current_v259_only():
    assert "CharacterBlueprintCreatorV260" in NODE_CLASS_MAPPINGS
    assert "CharacterShotControlV260" in NODE_CLASS_MAPPINGS
    assert "CharacterPromptAssemblerV260" in NODE_CLASS_MAPPINGS
    assert "CharacterBlueprintCreatorV258" not in NODE_CLASS_MAPPINGS


def test_bust_medium_is_explicitly_separated_from_small_and_position_is_independent():
    p = profile(
        chest_anatomy="Bust Anatomy — Use Bust Controls",
        bust_size="Medium",
        bust_shape="Round — Even Upper and Lower Fullness",
        bust_position="High-Set / Perky",
    )
    text = p["chest_anatomy_prompt"].lower()
    assert "clearly medium" in text
    assert "visibly larger" in text
    assert "preserve the selected bust size and shape unchanged" in text
    assert "independent controls" in text


def test_flat_chest_explicitly_excludes_small_breast_mounds():
    p = profile(chest_anatomy="Flat / Neutral Chest")
    text = p["chest_anatomy_prompt"].lower()
    assert "truly flat" in text
    assert "no breast mound" in text


def test_face_close_and_waist_up_are_square_and_do_not_reuse_pelvis_front_lock():
    p = profile(visible_presentation_mode="Clinical Anatomy — No Clothing")
    face = plan(p, shot_type="Face Close-Up", camera_view="Front View")
    assert (face["recommended_width"], face["recommended_height"]) == (1024, 1024)
    assert "both arms remain lowered below the crop" in face["pose_prompt"].lower()
    waist = plan(p, shot_type="Waist-Up Midshot", camera_view="Front View")
    assert (waist["recommended_width"], waist["recommended_height"]) == (1024, 1024)
    assert "pelvic centerline" not in waist["pose_prompt"].lower()
    assert "both front hip points remain equally visible" not in waist["pose_prompt"].lower()
    assert "pelvis, hip points" in waist["pose_prompt"].lower()


def test_front_pelvic_tattoo_is_not_emitted_in_back_view():
    p = profile(
        tattoo_status="One",
        tattoo_input_mode="Structured Single Tattoo",
        structured_tattoo_location="Left Front Pelvic Bone / Groin Line",
        structured_tattoo_description="large heart",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
    )
    back = plan(p, shot_type="Full Body", camera_view="Back View")
    result = assemble(p, back)
    sections = json.loads(result[18])
    assert sections["visible_tattoo_records"] == []
    assert "do not relocate it onto another visible body region" in result[0].lower()


def test_tattoo_none_emits_clean_skin_authority():
    p = profile(tattoo_status="None", piercing_status="None")
    s = plan(p, shot_type="Full Body", camera_view="Front View")
    prompt = assemble(p, s)[0].lower()
    assert "free of tattoos, body art, decorative ink" in prompt
    assert "no piercing jewelry is present anywhere" in prompt


def test_center_lip_and_navel_use_single_object_geometry():
    p = profile(
        piercing_status="One",
        piercing_input_mode="Structured Single Piercing",
        piercing_location="Center Lip",
        piercing_type="Hoop",
        piercing_material="Steel",
    )
    s = plan(p, shot_type="Face Close-Up", camera_view="Front View")
    prompt = assemble(p, s)[0].lower()
    assert "one ring only" in prompt
    assert "no paired side rings" in prompt
    assert "mouth corner" in prompt

    p2 = profile(
        piercing_status="One",
        piercing_input_mode="Structured Single Piercing",
        piercing_location="Navel / Belly Button",
        piercing_type="Curved Barbell",
        piercing_material="Steel",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
    )
    s2 = plan(p2, shot_type="Full Body", camera_view="Front View")
    prompt2 = assemble(p2, s2)[0].lower()
    assert "one top bead" in prompt2
    assert "one lower bead" in prompt2
    assert "no loose hook" in prompt2


def test_extended_puppy_camera_height_is_not_forced_to_eye_level():
    p = profile()
    eye = plan(p, shot_type="Full Body", camera_view="Back View", camera_height="Eye Level", pose="Extended Puppy Pose")
    high = plan(p, shot_type="Full Body", camera_view="Back View", camera_height="High Angle", pose="Extended Puppy Pose")
    assert "zero downward tilt" in eye["camera_prompt"].lower()
    assert "thirty-five to forty-five degrees" in high["camera_prompt"].lower()
    assert "not a true top-down overhead" in high["camera_prompt"].lower()
    assert eye["camera_prompt"] != high["camera_prompt"]


def test_stage2_extreme_manifest_has_surface_camera_and_reference_handoff():
    p = profile(
        chest_anatomy="Bust Anatomy — Use Bust Controls",
        groin_anatomy="Female External Anatomy",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
    )
    out = FCCKreaBlueprintDatasetDirector().direct(p, KREA_BLUEPRINT_PLANS[4], "Test", 2000, 1, "")
    data = json.loads(out[7])
    assert data["schema"] == "FCC_KREA_STAGE2_CANONICAL_ATLAS_V259"
    assert data["resolved_count_label"]
    assert out[8].startswith("RESOLVED COUNT:")
    gluteal = next(item for item in data["items"] if "gluteal_fold" in item["shot_id"])
    assert gluteal["target_surface"] == "posterior gluteal fold"
    assert gluteal["camera_view"] == "strict direct rear close-up"
    assert gluteal["identity_reference_required"] is True
    assert "Qwen reference edit" in gluteal["recommended_execution_lane"]
    prompt = gluteal["prompt"].lower()
    assert "front groin" in prompt and "remain outside the frame" in prompt
