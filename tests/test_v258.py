import json

from full_character_creation_core import NODE_CLASS_MAPPINGS
from full_character_creation_core.src.nodes_v258 import (
    BACKGROUND_FOCUS_OPTIONS,
    NEW_TATTOO_LOCATIONS,
    CharacterBlueprintCreatorV258,
    CharacterPromptAssemblerV258,
    CharacterShotControlV258,
)
from full_character_creation_core.src.dataset_v258 import (
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


def make_profile(**updates):
    kwargs = defaults(CharacterBlueprintCreatorV258)
    kwargs.update(updates)
    return CharacterBlueprintCreatorV258().build_blueprint_v258(**kwargs)[8]


def make_plan(profile=None, **updates):
    kwargs = defaults(CharacterShotControlV258)
    if profile is not None:
        kwargs["character_blueprint"] = profile
    kwargs.update(updates)
    return CharacterShotControlV258().build_shot_plan_v258(**kwargs)[0]


def assemble(profile, plan):
    return CharacterPromptAssemblerV258().assemble_prompt_v258(
        profile, plan, "Krea — First Identity Image", "Image 1"
    )


def test_registry_current_v258_only():
    assert "CharacterBlueprintCreatorV260" in NODE_CLASS_MAPPINGS
    assert "CharacterShotControlV260" in NODE_CLASS_MAPPINGS
    assert "CharacterPromptAssemblerV260" in NODE_CLASS_MAPPINGS
    assert "CharacterBlueprintCreatorV257" not in NODE_CLASS_MAPPINGS


def test_clinical_hard_clears_stored_daisy_outfit_and_coverage():
    profile = make_profile(
        primary_character_gender="Adult Nonbinary",
        chest_anatomy="Flat / Neutral Chest",
        groin_anatomy="Unspecified — Do Not Describe",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
        preset_outfit_if_selected="High-Hem Crop Top and Daisy Dukes",
    )
    plan = make_plan(profile, shot_type="Full Body", camera_view="Front View")
    result = assemble(profile, plan)
    prompt = result[0].lower()
    sections = json.loads(result[18])
    assert sections["visible_presentation"] == "unclothed adult subject in neutral clinical anatomy documentation"
    assert "denim cutoff" not in prompt
    assert "crop top" not in prompt
    assert "wearing" not in sections["visible_presentation"].lower()
    assert profile["resolved_presentation_authority"]["stored_outfit_is_active"] is False
    assert profile["resolved_presentation_authority"]["garment_coverage"] == []


def test_daisy_is_active_only_when_clothed_and_has_no_hidden_footwear():
    profile = make_profile(
        visible_presentation_mode="Clothed — Use Outfit Controls",
        outfit_input_method="Preset — Ready-Made Complete Outfit",
        preset_outfit_if_selected="High-Hem Crop Top and Daisy Dukes",
    )
    plan = make_plan(profile, shot_type="Full Body", camera_view="Front View")
    prompt = assemble(profile, plan)[0].lower()
    assert "rigid distressed blue denim cutoff" in prompt
    assert "no unlisted footwear" in prompt
    assert "sneakers or sandals" not in prompt
    assert profile["outfit_components"].get("footwear", "") == ""
    assert "no skin tone, nipple contour, areola detail" in prompt


def test_face_close_is_square_and_excludes_presentation_and_body():
    profile = make_profile(
        visible_presentation_mode="Clinical Anatomy — No Clothing",
        chest_anatomy="Bust Anatomy — Use Bust Controls",
        bust_size="Large",
    )
    plan = make_plan(profile, shot_type="Face Close-Up", camera_view="Front View")
    result = assemble(profile, plan)
    sections = json.loads(result[18])
    assert plan["recommended_width"] == 1024
    assert plan["recommended_height"] == 1024
    assert sections["visible_presentation"] == ""
    assert sections["visible_body"] == ""
    assert "lower image edge intersects the neck before either clavicle begins" in result[0]
    assert result[0].rstrip().endswith("do not widen or lower the composition.")


def test_waist_up_is_crop_scoped_and_final_authority_is_last():
    profile = make_profile(
        primary_character_gender="Adult Nonbinary",
        body_type="Slim",
        chest_anatomy="Flat / Neutral Chest",
        groin_anatomy="Male External Anatomy",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
    )
    plan = make_plan(profile, shot_type="Waist-Up Midshot", camera_view="Front View")
    result = assemble(profile, plan)
    sections = json.loads(result[18])
    assert "slim legs" not in sections["visible_body"].lower()
    assert "male external genital" not in sections["visible_body"].lower()
    assert "pelvis and knees are aligned" not in plan["camera_prompt"].lower()
    assert "pelvis and knees are outside the crop" in plan["camera_prompt"].lower()
    assert "FINAL WAIST-UP FRAME AUTHORITY" in result[0]
    assert result[0].rstrip().endswith("chest dimensions, clothing, tattoos, piercings, and marks do not change the selected waist-up crop.")


def test_front_view_lock_prevents_relaxed_pose_yaw():
    profile = make_profile()
    plan = make_plan(
        profile,
        shot_type="Three-Quarter Body",
        camera_view="Front View",
        pose="Relaxed Standing",
    )
    assert "both shoulders remain equally distant from the camera" in plan["pose_prompt"]
    assert "does not rotate the shoulders, ribcage, waist, or pelvis" in plan["pose_prompt"]


def test_full_body_frame_authority_is_appended_after_long_garment_prompt():
    profile = make_profile(
        visible_presentation_mode="Clothed — Use Outfit Controls",
        preset_outfit_if_selected="High-Hem Crop Top and Daisy Dukes",
    )
    plan = make_plan(profile, shot_type="Full Body", camera_view="Front View")
    prompt = assemble(profile, plan)[0]
    assert "FINAL FULL-BODY FRAME AUTHORITY" in prompt
    assert prompt.rstrip().endswith("clothing, chest proportions, tattoos, piercings, scars, moles, and other details do not convert the image into a portrait, waist-up image, or three-quarter crop.")


def test_raw_instagram_default_has_natural_readable_focus_and_no_forced_falloff():
    inputs = CharacterShotControlV258.INPUT_TYPES()["required"]
    assert "background_focus" in inputs
    assert inputs["background_focus"][0] == BACKGROUND_FOCUS_OPTIONS
    profile = make_profile()
    plan = make_plan(
        profile,
        photo_style="Raw Instagram / Unfiltered Social Snapshot",
        background_focus="Natural Snapshot Focus — No Artificial Bokeh",
    )
    env = plan["environment_prompt"].lower()
    assert "small focus falloff" not in env
    assert "surrounding environment remains naturally readable" in env
    assert "synthetic portrait-mode cutout" in env


def test_new_structured_tattoo_locations_are_available_and_compiled():
    options = CharacterBlueprintCreatorV258.INPUT_TYPES()["required"]["structured_tattoo_location"][0]
    for location in NEW_TATTOO_LOCATIONS:
        assert location in options
    profile = make_profile(
        tattoo_status="One",
        tattoo_input_mode="Structured Single Tattoo",
        structured_tattoo_location="Full Left Leg + Left Buttock",
        structured_tattoo_description="biomechanical artwork",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
    )
    record = profile["tattoo_records"][0]
    assert record["location"] == "Full Left Leg + Left Buttock"
    assert "left_buttock" in record["region_tags"]
    plan = make_plan(profile, shot_type="Full Body", camera_view="Back View")
    prompt = assemble(profile, plan)[0].lower()
    assert "left buttock" in prompt
    assert "gluteal fold" in prompt
    assert "opposite" not in prompt or "right buttock" in prompt


def test_front_pelvic_tattoo_stays_beside_not_on_genital_tissue():
    profile = make_profile(
        tattoo_status="One",
        tattoo_input_mode="Structured Single Tattoo",
        structured_tattoo_location="Left Front Pelvic Bone / Groin Line",
        structured_tattoo_description="small floral vine",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
    )
    plan = make_plan(profile, shot_type="Full Body", camera_view="Front View")
    prompt = assemble(profile, plan)[0].lower()
    assert "left front pelvic-bone and inguinal groin line" in prompt
    assert "without crossing onto genital tissue" in prompt
    assert "right front pelvic line" in prompt


def test_center_lip_ring_uses_lower_lip_term_and_avoids_seam_ring_bias():
    profile = make_profile(
        piercing_status="One",
        piercing_input_mode="Structured Single Piercing",
        piercing_location="Center Lip",
        piercing_type="Seam Ring",
        piercing_material="Steel",
        piercing_visibility="Documentation",
    )
    plan = make_plan(profile, shot_type="Face Close-Up", camera_view="Front View")
    prompt = assemble(profile, plan)[0].lower()
    assert "small lower-lip hoop" in prompt
    assert "living lower-lip vermilion tissue" in prompt
    assert "seam ring" not in prompt
    assert "septum" not in prompt
    assert "nostrils remain completely bare" in prompt


def test_marks_are_exactly_one_and_other_skin_is_clear():
    profile = make_profile(
        scar_mole_beauty_mark_descriptors="above upper lip on left side, a small brown beauty mole"
    )
    plan = make_plan(profile, shot_type="Face Close-Up", camera_view="Front View")
    prompt = assemble(profile, plan)[0].lower()
    assert "exactly one permanent natural mole or beauty mark" in prompt
    assert "all other visible skin remains free of this mark" in prompt
    assert "do not duplicate, mirror, relocate" in prompt


def test_stage2_uses_v258_mark_compilers_and_schema():
    profile = make_profile(
        tattoo_status="One",
        tattoo_input_mode="Structured Single Tattoo",
        structured_tattoo_location="Full Left Leg + Left Buttock",
        structured_tattoo_description="biomechanical artwork",
        scar_mole_beauty_mark_descriptors="left upper thigh, healed linear scar",
    )
    output = FCCKreaBlueprintDatasetDirector().direct(
        profile, KREA_BLUEPRINT_PLANS[4], "Test", 2000, 1, ""
    )
    plan = json.loads(output[7])
    assert plan["schema"] == "FCC_KREA_STAGE2_CANONICAL_ATLAS_V258"
    assert plan["schema_version"] == 8
    joined = "\n".join(output[0]).lower()
    assert "exactly one permanent" in joined
    assert "do not duplicate, mirror, relocate" in joined
