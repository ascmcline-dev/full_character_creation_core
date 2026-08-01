from __future__ import annotations

from full_character_creation_core import NODE_CLASS_MAPPINGS
from full_character_creation_core.src.nodes_v243 import AUTO_ASPECT, WIDE_FULL_BODY
from full_character_creation_core.src.nodes_v244 import AUTO_LENS, NATURAL_SIDE_LYING
from full_character_creation_core.src.nodes_v245 import (
    ALL_FOURS,
    EXTENDED_PUPPY,
    CharacterBlueprintCreatorV245,
    CharacterPromptAssemblerV245,
    CharacterShotControlV245,
)


def defaults(cls):
    values = {}
    for section in ("required", "optional"):
        for name, spec in cls.INPUT_TYPES().get(section, {}).items():
            if name in {"character_blueprint", "shot_plan"}:
                continue
            choices = spec[0]
            cfg = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
            if "default" in cfg:
                values[name] = cfg["default"]
            elif isinstance(choices, list):
                values[name] = choices[0]
            elif choices == "STRING":
                values[name] = ""
            elif choices == "INT":
                values[name] = 0
    return values


def make_profile(**overrides):
    values = defaults(CharacterBlueprintCreatorV245)
    values.update(overrides)
    result = CharacterBlueprintCreatorV245().build_blueprint_v245(**values)
    return result[8], result


def make_plan(profile, **overrides):
    values = defaults(CharacterShotControlV245)
    values["character_blueprint"] = profile
    values.update(overrides)
    result = CharacterShotControlV245().build_shot_plan_v245(**values)
    return result[0], result


def assemble(profile, plan, purpose="Krea — First Identity Image"):
    values = defaults(CharacterPromptAssemblerV245)
    values.update({
        "character_blueprint": profile,
        "shot_plan": plan,
        "generation_purpose": purpose,
        "reference_label": "Image 1",
    })
    return CharacterPromptAssemblerV245().assemble_prompt_v245(**values)


def test_current_only_registry():
    assert set(NODE_CLASS_MAPPINGS) == {
        "QwenDatasetQueue", "FCCDatasetDirector", "FCCQueueItemRouter",
        "FCCKreaBlueprintDatasetDirector", "FCCKreaQueueItemRouter",
        "CharacterBlueprintCreatorV254", "CharacterShotControlV254", "CharacterPromptAssemblerV254",
        "FCCQwenAnglePromptMode", "FCCSupportPanel",
    }


def test_hair_highlights_are_preserved_with_red_base():
    profile, result = make_profile(hair_color="Red", hair_highlights="blue and pink face-framing streaks")
    hair = profile["hair_prompt"].lower()
    assert "auburn-copper red" in hair
    assert "blue and pink face-framing streaks" in hair
    assert "blue and pink" in result[29].lower()


def test_structured_lower_back_tattoo_is_canonical_record():
    profile, _ = make_profile(
        tattoo_status="One",
        tattoo_input_mode="Structured Single Tattoo",
        structured_tattoo_location="Lower Back / Tramp Stamp",
        structured_tattoo_description="Nordic butterfly design",
        preset_outfit_if_selected="High-Hem Crop Top and Daisy Dukes",
    )
    record = profile["tattoo_records"][0]
    assert record["source"] == "structured"
    assert record["location"] == "Lower Back / Tramp Stamp"
    assert "lower back immediately above the waistband" in record["raw"].lower()


def test_crop_top_does_not_hide_lower_back_tattoo_in_rear_view():
    profile, _ = make_profile(
        tattoo_status="One",
        tattoo_input_mode="Structured Single Tattoo",
        structured_tattoo_location="Lower Back / Tramp Stamp",
        structured_tattoo_description="Nordic butterfly design",
        preset_outfit_if_selected="High-Hem Crop Top and Daisy Dukes",
    )
    plan, _ = make_plan(profile, shot_type="Three-Quarter Body", camera_view="Rear Three-Quarter Left")
    prompt = assemble(profile, plan)[13].lower()
    assert "nordic butterfly" in prompt
    assert "lower back" in prompt


def test_face_crop_still_omits_lower_back_tattoo():
    profile, _ = make_profile(
        tattoo_status="One",
        tattoo_input_mode="Structured Single Tattoo",
        structured_tattoo_location="Lower Back / Tramp Stamp",
        structured_tattoo_description="Nordic butterfly design",
    )
    plan, _ = make_plan(profile, shot_type="Face Close-Up")
    prompt = assemble(profile, plan)[13].lower()
    assert "nordic butterfly" not in prompt


def test_reclining_face_closeup_uses_compact_pose_and_85mm():
    profile, _ = make_profile()
    plan, _ = make_plan(profile, shot_type="Face Close-Up", pose=NATURAL_SIDE_LYING, lens=AUTO_LENS)
    assert plan["lens_effective"] == "85mm Portrait — Recommended"
    pose = plan["pose_prompt"].lower()
    assert "head is lightly supported" in pose
    assert "hips and legs" not in pose
    assert "waist" not in plan["camera_prompt"].lower()


def test_full_body_pulls_back_and_reports_effective_lens():
    profile, _ = make_profile()
    plan, _ = make_plan(profile, shot_type="Full Body", lens=AUTO_LENS, aspect_ratio=AUTO_ASPECT)
    framing = plan["framing_prompt"].lower()
    assert "forty-five to fifty-five percent" in framing
    assert "camera is centered at navel height" in framing
    result = assemble(profile, plan)
    assert "EFFECTIVE LENS: 50mm Normal" in result[17]


def test_wide_full_body_is_intentionally_landscape():
    profile, _ = make_profile()
    plan, _ = make_plan(profile, shot_type=WIDE_FULL_BODY, lens=AUTO_LENS, aspect_ratio=AUTO_ASPECT)
    assert plan["recommended_width"] == 1536
    assert plan["recommended_height"] == 1024
    assert plan["lens_effective"] == "35mm Environmental"


def test_raw_instagram_has_amateur_grit_terms():
    profile, _ = make_profile()
    plan, _ = make_plan(profile, photo_style="Raw Instagram / Unfiltered Social Snapshot")
    prompt = assemble(profile, plan)[13].lower()
    for token in ("iso grain", "jpeg compression", "uneven automatic white balance", "micro-motion softness", "unpolished everyday finish"):
        assert token in prompt


def test_selfie_is_off_center_and_body_selfie_uses_mirror():
    profile, _ = make_profile()
    face, _ = make_plan(profile, shot_type="Face Close-Up", photo_style="Natural Arm's-Length Selfie")
    body, _ = make_plan(profile, shot_type="Full Body", photo_style="Natural Arm's-Length Selfie")
    assert "slightly above and to one side" in face["camera_prompt"].lower()
    assert "mirror-selfie" in body["camera_prompt"].lower()


def test_finger_heart_uses_both_hands_and_explicit_geometry():
    profile, _ = make_profile()
    plan, _ = make_plan(profile, pose="Finger Heart Near Face")
    pose = plan["pose_prompt"].lower()
    assert "both hands" in pose
    assert "both thumbs meet" in pose
    assert "both index fingers" in pose
    assert "symmetrical heart" in pose


def test_all_fours_and_extended_puppy_are_available_and_grounded():
    choices = CharacterShotControlV245.INPUT_TYPES()["required"]["pose"][0]
    assert ALL_FOURS in choices
    assert EXTENDED_PUPPY in choices
    profile, _ = make_profile()
    all_fours, _ = make_plan(profile, shot_type="Full Body", pose=ALL_FOURS, aspect_ratio=AUTO_ASPECT)
    puppy, _ = make_plan(profile, shot_type="Full Body", pose=EXTENDED_PUPPY, aspect_ratio=AUTO_ASPECT)
    assert "both palms are flat" in all_fours["pose_prompt"].lower()
    assert "both knees and lower legs rest on the surface" in all_fours["pose_prompt"].lower()
    assert "hips elevated directly above the knees" in puppy["pose_prompt"].lower()
    assert all_fours["recommended_width"] == 1536 and all_fours["recommended_height"] == 1024


def test_tan_is_after_body_and_presentation():
    profile, _ = make_profile(
        tan_profile="Medium Tan — Even",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
        bust_size="Medium",
        bust_shape="Natural Teardrop — Gentle Upper Slope",
    )
    plan, _ = make_plan(profile, shot_type="Waist-Up Midshot")
    prompt = assemble(profile, plan)[13].lower()
    assert prompt.index("medium bust") < prompt.index("uniform medium tan")
    assert prompt.index("clinical anatomy documentation") < prompt.index("uniform medium tan")


def test_clothed_nipple_macro_keeps_garment_and_omits_piercing():
    profile, _ = make_profile(
        preset_outfit_if_selected="Swimwear",
        piercing_status="One",
        piercing_input_mode="Descriptor List",
        piercing_descriptors="Left Nipple Steel Hoop",
    )
    plan, _ = make_plan(
        profile,
        shot_type="Extreme Close-Up — Single Detail",
        extreme_closeup_focus="Left Nipple and Areola",
    )
    prompt = assemble(profile, plan)[13].lower()
    assert "garment-covered chest area" in prompt
    assert "micro string bikini top" in prompt
    assert "steel hoop" not in prompt


def test_piercing_records_remain_structured_without_global_locks():
    profile, _ = make_profile(
        piercing_status="One",
        piercing_input_mode="Structured Single Piercing",
        piercing_location="Septum",
        piercing_type="Hoop",
        piercing_material="Steel",
    )
    plan, _ = make_plan(profile, shot_type="Face Close-Up")
    prompt = assemble(profile, plan)[13].lower()
    assert "central nasal septum" in prompt
    assert "piercing count lock" not in prompt
    assert "anatomy integrity" not in prompt


def test_character_creator_support_panel_assets_and_links_exist():
    from pathlib import Path
    package = Path(__file__).resolve().parents[1]
    js = (package / "web" / "js" / "fcc_suite_ui_v252_compat.js").read_text(encoding="utf-8")
    asset = package / "web" / "js" / "assets" / "kaustorment_support.webp"
    assert asset.is_file() and asset.stat().st_size > 1000
    header = asset.read_bytes()[:16]
    assert header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    assert "addDOMWidget" in js
    assert "kaustorment_support.webp" in js
    assert "buymeacoffee.com/ascmclinej" in js
    assert "discord.gg/ufU6UcrK6" in js
    assert 'id === "CharacterBlueprintCreatorV252"' in js
    assert 'id === "FCCSupportPanel"' in js
    assert "restoreCompatibilityWidgets" in js
    assert "widget.hidden = false" in js
    assert "__fccOriginalComputeSize" in js
    assert "__fccOriginalDraw" in js
    assert "setWidgetVisible" not in js
    assert "HIDDEN_SIZE" not in js
    assert "fcc_v252_dedicated_support_panel" in js
