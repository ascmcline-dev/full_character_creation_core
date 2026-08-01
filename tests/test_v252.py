import json

from full_character_creation_core.src.nodes_v247 import EXTENDED_PUPPY
from full_character_creation_core.src.nodes_v252 import (
    CharacterBlueprintCreatorV252,
    CharacterPromptAssemblerV252,
    CharacterShotControlV252,
)


def _defaults(cls):
    values = {}
    for name, spec in cls.INPUT_TYPES()["required"].items():
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


def _profile(**updates):
    values = _defaults(CharacterBlueprintCreatorV252)
    values.update({"tattoo_status": "None", "piercing_status": "None"})
    values.update(updates)
    return CharacterBlueprintCreatorV252().build_blueprint_v252(**values)[8]


def _plan(profile, **updates):
    values = _defaults(CharacterShotControlV252)
    values.update({
        "shot_type": "Face Close-Up",
        "camera_view": "Front View",
        "camera_height": "Eye Level",
        "pose": "Neutral Standing",
        "lens": "85mm Portrait — Recommended",
        "aspect_ratio": "Auto by Shot",
    })
    values.update(updates)
    return CharacterShotControlV252().build_shot_plan_v252(character_blueprint=profile, **values)[0]


def _assemble(profile, plan):
    return CharacterPromptAssemblerV252().assemble_prompt_v252(
        profile, plan, "Krea — First Identity Image", "Image 1"
    )


def test_face_close_has_hard_lower_boundary_and_no_standing_arm_leak():
    profile = _profile(
        visible_presentation_mode="Clothed — Use Outfit Controls",
        outfit_input_method="Preset — Ready-Made Complete Outfit",
        preset_outfit_if_selected="Opaque Fitted Tank Top",
    )
    plan = _plan(profile)
    result = _assemble(profile, plan)
    prompt = result[0].lower()
    assert plan["face_close_lock"] is True
    assert "seventy to eighty percent" in prompt
    assert "lower frame ends at the base of the neck and upper trapezius line" in prompt
    assert "arms and torso remain outside" in prompt
    assert "both arms resting naturally at the sides" not in prompt
    assert "continuous front and back fabric panels" not in prompt
    assert "do not widen the composition to show the top's length or hem" in prompt


def test_rear_puppy_eye_level_has_no_downward_or_overhead_authority():
    profile = _profile()
    plan = _plan(
        profile,
        shot_type="Three-Quarter Body",
        pose=EXTENDED_PUPPY,
        camera_view="Back View",
        camera_height="Eye Level",
    )
    camera = plan["camera_prompt"].lower()
    assert plan["rear_puppy_camera_height_lock"] is True
    assert "behind the pelvis at rear hip height" in camera
    assert "lens axis remains level" in camera
    assert "no elevated, downward-looking, high-angle, or overhead perspective" in camera
    assert "hands are the farthest body landmarks" in camera


def test_rear_puppy_low_and_overhead_are_distinct():
    profile = _profile()
    low = _plan(profile, shot_type="Three-Quarter Body", pose=EXTENDED_PUPPY, camera_view="Back View", camera_height="Low Angle")
    overhead = _plan(profile, shot_type="Three-Quarter Body", pose=EXTENDED_PUPPY, camera_view="Back View", camera_height="Overhead")
    assert "just above the floor" in low["camera_prompt"].lower()
    assert "angles upward" in low["camera_prompt"].lower()
    assert "high above and behind the rear pelvis" in overhead["camera_prompt"].lower()
    assert "top-down rear composition" in overhead["camera_prompt"].lower()


def test_opaque_tank_has_dense_material_natural_waist_and_close_fit():
    profile = _profile(
        visible_presentation_mode="Clothed — Use Outfit Controls",
        outfit_input_method="Preset — Ready-Made Complete Outfit",
        preset_outfit_if_selected="Opaque Fitted Tank Top",
        chest_anatomy="Bust Anatomy — Use Bust Controls",
        bust_size="Medium",
    )
    plan = _plan(profile, shot_type="Chest-Up", camera_height="Low Angle", pose="Relaxed Standing")
    result = _assemble(profile, plan)
    prompt = result[0].lower()
    assert "dense midweight double-layer matte cotton-spandex jersey" in prompt
    assert "uniform optical opacity" in prompt
    assert "finished lower hem at the natural waist" in prompt
    assert "does not hang loosely, billow, become translucent, or turn sheer" in prompt
    assert "outward covered silhouette preserve the complete selected bust volume" in prompt
    assert "rather than transparency, extreme stretching" in prompt


def test_crop_top_has_explicit_lower_ribcage_hem_above_navel():
    profile = _profile(
        visible_presentation_mode="Clothed — Use Outfit Controls",
        outfit_input_method="Preset — Ready-Made Complete Outfit",
        preset_outfit_if_selected="High-Hem Crop Top and Daisy Dukes",
    )
    plan = _plan(profile, shot_type="Waist-Up Midshot")
    prompt = _assemble(profile, plan)[0].lower()
    assert "finished hem at the lower ribcage clearly above the navel" in prompt
    assert "narrow strip of midriff remains visible" in prompt
    assert "uniform optical opacity" in prompt


def test_single_visible_tattoo_is_one_combined_design_on_anatomical_side():
    profile = _profile(
        visible_presentation_mode="Clothed — Use Outfit Controls",
        outfit_input_method="Preset — Ready-Made Complete Outfit",
        preset_outfit_if_selected="Opaque Fitted Tank Top",
        tattoo_status="One",
        tattoo_input_mode="Structured Single Tattoo",
        structured_tattoo_location="Right Forearm",
        structured_tattoo_description="a colored large hummingbird with a orchid",
    )
    plan = _plan(profile, shot_type="Chest-Up")
    result = _assemble(profile, plan)
    sections = json.loads(result[18])
    marks = sections["visible_marks"].lower()
    assert "exactly one visible permanent tattoo" in marks
    assert "single combined tattoo design" in marks
    assert "anatomical right forearm" in marks
    assert "anatomical left arm and all other visible skin remain tattoo-free" in marks
    assert "not split into separate designs, mirrored, duplicated, or relocated" in marks


def test_locked_raw_instagram_and_skin_stability_remain_present():
    profile = _profile(skin_tone="Light", tan_profile="None")
    plan = _plan(profile, photo_style="Raw Instagram / Unfiltered Social Snapshot")
    prompt = _assemble(profile, plan)[0].lower()
    assert "iso grain" in prompt
    assert "jpeg compression" in prompt
    assert "naturally light fair complexion" in prompt
