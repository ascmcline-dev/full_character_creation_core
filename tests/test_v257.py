import json

from full_character_creation_core import NODE_CLASS_MAPPINGS
from full_character_creation_core.src.nodes_v257 import (
    CharacterBlueprintCreatorV257,
    CharacterPromptAssemblerV257,
    CharacterShotControlV257,
)
from full_character_creation_core.src.dataset_v257 import (
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
    kwargs = defaults(CharacterBlueprintCreatorV257)
    kwargs.update(updates)
    return CharacterBlueprintCreatorV257().build_blueprint_v257(**kwargs)[8]


def make_plan(**updates):
    kwargs = defaults(CharacterShotControlV257)
    kwargs.update(updates)
    return CharacterShotControlV257().build_shot_plan_v257(**kwargs)[0]


def test_v257_classes_remain_importable_for_regression():
    assert CharacterBlueprintCreatorV257 is not None
    assert CharacterShotControlV257 is not None
    assert CharacterPromptAssemblerV257 is not None


def test_nonbust_paths_prune_all_bust_authority():
    profile = make_profile(
        primary_character_gender="Adult Nonbinary",
        chest_anatomy="Flat / Neutral Chest",
        groin_anatomy="Male External Anatomy",
        bust_size="Large",
        bust_shape="Round — Even Upper and Lower Fullness",
        bust_position="High and Tight",
        bust_augmentation="Very Firm Augmented Projection",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
    )
    assert profile["bust_controls_active"] is False
    assert profile["bust_anatomy_authority_prompt"] == ""
    assert profile["bust_clothed_authority_prompt"] == ""
    assert "Bust vertical placement effect" not in profile["presentation_summary"]
    assert "Clothed bust fidelity" not in profile["presentation_summary"]
    active = profile["active_character_prompt"].lower()
    assert "breast" not in active
    assert "augmentation" not in active


def test_daisy_dukes_keep_complete_outfit_and_full_leg_sleeve():
    profile = make_profile(
        visible_presentation_mode="Clothed — Use Outfit Controls",
        preset_outfit_if_selected="High-Hem Crop Top and Daisy Dukes",
        tattoo_status="One",
        tattoo_input_mode="Structured Single Tattoo",
        structured_tattoo_location="Full Left Leg Sleeve",
        structured_tattoo_description="colored floral vines",
    )
    plan = make_plan(shot_type="Full Body", camera_view="Front View", pose="Neutral Standing")
    result = CharacterPromptAssemblerV257().assemble_prompt_v257(
        profile, plan, "Krea2 — Direct Character Generation", "Image 1"
    )
    prompt = result[0]
    sections = json.loads(result[18])
    assert "rigid distressed blue denim cutoff" in prompt
    assert "full anatomical left leg sleeve" in prompt
    assert len(sections["visible_tattoo_records"]) == 1
    assert "athletic compression garment supports the chest" not in prompt
    assert "yoga pants" not in prompt.lower()
    assert "leggings" not in prompt.lower()


def test_center_lip_ring_cannot_become_septum_and_navel_option_exists():
    inputs = CharacterBlueprintCreatorV257.INPUT_TYPES()["required"]
    assert "Navel / Belly Button" in inputs["piercing_location"][0]
    profile = make_profile(
        piercing_status="One",
        piercing_input_mode="Structured Single Piercing",
        piercing_location="Center Lip",
        piercing_type="Seam Ring",
        piercing_material="Steel",
        piercing_visibility="Documentation",
    )
    plan = make_plan(shot_type="Full Body", camera_view="Front View", pose="Neutral Standing")
    prompt = CharacterPromptAssemblerV257().assemble_prompt_v257(
        profile, plan, "Krea2 — Direct Character Generation", "Image 1"
    )[0].lower()
    assert "lower-lip vermilion edge" in prompt
    assert "nasal region remains unpierced" in prompt
    assert "smooth continuous hoop has no bead" in prompt
    assert "septum" not in prompt


def test_scar_mole_beauty_mark_box_is_saved_and_visible():
    profile = make_profile(
        scar_mole_beauty_mark_descriptors=(
            "above upper lip on left side, a small beauty mole\n"
            "upper back, healed shrapnel scar"
        )
    )
    assert len(profile["scar_mole_beauty_mark_records"]) == 2
    plan = make_plan(shot_type="Full Body", camera_view="Front View", pose="Neutral Standing")
    result = CharacterPromptAssemblerV257().assemble_prompt_v257(
        profile, plan, "Krea2 — Direct Character Generation", "Image 1"
    )
    assert "small beauty mole" in result[0]


def test_stage2_plan_counts_and_true_extreme_rules():
    profile = make_profile(
        primary_character_gender="Adult Nonbinary",
        chest_anatomy="Flat / Neutral Chest",
        groin_anatomy="Male External Anatomy",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
    )
    director = FCCKreaBlueprintDatasetDirector()
    output = director.direct(profile, KREA_BLUEPRINT_PLANS[4], "Test", 2000, 1, "")
    plan = json.loads(output[7])
    assert plan["base_shots"] == plan["total_items"]
    assert plan["base_shots"] > 0
    assert "TOTAL OUTPUTS" in output[9]
    for prompt in output[0]:
        assert "eighty to ninety percent of the frame" in prompt
        assert "exclude the complete torso" in prompt
        assert "adult nonbinary" not in prompt.lower()


def test_extended_puppy_rear_is_landmark_first_and_horizontal():
    plan = make_plan(
        shot_type="Full Body",
        camera_view="Back View",
        camera_height="Eye Level",
        pose="Extended Puppy Pose",
    )
    assert "both shoulder joints point toward twelve o'clock" in plan["pose_prompt"]
    assert "never extend toward three o'clock or nine o'clock" in plan["pose_prompt"]
    assert "lens center is aligned with the rear pelvis and sacrum" in plan["camera_prompt"]
    assert "zero downward tilt" in plan["camera_prompt"]


def test_navel_piercing_is_centered_on_existing_navel_tissue():
    profile = make_profile(
        piercing_status="One",
        piercing_input_mode="Structured Single Piercing",
        piercing_location="Navel / Belly Button",
        piercing_type="Curved Barbell",
        piercing_material="Steel",
        piercing_visibility="Documentation",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
    )
    plan = make_plan(shot_type="Full Body", camera_view="Front View", pose="Neutral Standing")
    prompt = CharacterPromptAssemblerV257().assemble_prompt_v257(
        profile, plan, "Krea2 — Direct Character Generation", "Image 1"
    )[0].lower()
    assert "existing navel" in prompt
    assert "living navel-rim tissue" in prompt
    assert "one natural navel" in prompt


def test_stage2_extreme_dynamic_body_marks_and_no_old_regional_scale_lock():
    profile = make_profile(
        tattoo_status="One",
        tattoo_input_mode="Structured Single Tattoo",
        structured_tattoo_location="Full Left Leg Sleeve",
        structured_tattoo_description="colored floral vines",
        scar_mole_beauty_mark_descriptors="upper back, healed shrapnel scar",
    )
    output = FCCKreaBlueprintDatasetDirector().direct(
        profile, KREA_BLUEPRINT_PLANS[4], "Test", 2000, 1, ""
    )
    shot_ids = output[2]
    assert any("tattoo_detail" in shot_id for shot_id in shot_ids)
    assert any("skin_mark_detail" in shot_id for shot_id in shot_ids)
    for prompt in output[0]:
        assert "sixty-five to eighty percent" not in prompt.lower()


def test_daisy_crop_top_exposes_navel_piercing():
    profile = make_profile(
        visible_presentation_mode="Clothed — Use Outfit Controls",
        outfit_source="Preset — Ready-Made Complete Outfit",
        preset_outfit_if_selected="High-Hem Crop Top and Daisy Dukes",
        piercing_status="One",
        piercing_input_mode="Structured Single Piercing",
        piercing_location="Navel / Belly Button",
        piercing_type="Curved Barbell",
        piercing_material="Steel",
        piercing_visibility="Documentation",
    )
    plan = make_plan(shot_type="Full Body", camera_view="Front View", pose="Neutral Standing")
    result = CharacterPromptAssemblerV257().assemble_prompt_v257(
        profile, plan, "Krea2 — Direct Character Generation", "Image 1"
    )
    prompt = result[0].lower()
    sections = json.loads(result[18])
    assert "existing navel" in prompt
    assert len(sections["visible_piercing_records"]) == 1
