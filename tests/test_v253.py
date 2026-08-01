import json

from full_character_creation_core.src.nodes_v245 import EXTENDED_PUPPY
from full_character_creation_core.src.nodes_v253 import (
    CharacterBlueprintCreatorV253,
    CharacterPromptAssemblerV253,
    CharacterShotControlV253,
)
from full_character_creation_core.src.dataset_v253 import (
    FCCFaceAngleDatasetDirector,
    FCCKreaBlueprintDatasetDirector,
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


def _profile(**updates):
    values = _defaults(CharacterBlueprintCreatorV253)
    values.update({"tattoo_status": "None", "piercing_status": "None"})
    values.update(updates)
    return CharacterBlueprintCreatorV253().build_blueprint_v253(**values)[8]


def _plan(profile, **updates):
    values = _defaults(CharacterShotControlV253)
    values.update({
        "shot_type": "Face Close-Up",
        "camera_view": "Front View",
        "camera_height": "Eye Level",
        "pose": "Neutral Standing",
        "lens": "85mm Portrait — Recommended",
        "aspect_ratio": "Auto by Shot",
    })
    values.update(updates)
    return CharacterShotControlV253().build_shot_plan_v253(character_blueprint=profile, **values)[0]


def _assemble(profile, plan):
    return CharacterPromptAssemblerV253().assemble_prompt_v253(
        profile, plan, "Krea — First Identity Image", "Image 1"
    )


def test_face_close_requires_clear_crown_and_removes_all_garment_text():
    profile = _profile(
        visible_presentation_mode="Clothed — Use Outfit Controls",
        outfit_input_method="Preset — Ready-Made Complete Outfit",
        preset_outfit_if_selected="Opaque Fitted Tank Top",
    )
    plan = _plan(profile)
    prompt = _assemble(profile, plan)[0].lower()
    assert "small clear margin above the complete crown" in prompt
    assert "lower center edge ends exactly at the base of the neck" in prompt
    assert "garment neckline" in prompt
    assert "wearing solid fitted tank top" not in prompt
    assert "continuous front and rear fabric panels" not in prompt


def test_waist_up_and_three_quarter_keep_complete_head_and_lower_boundary():
    profile = _profile()
    waist = _plan(profile, shot_type="Waist-Up Midshot")
    three = _plan(profile, shot_type="Three-Quarter Body")
    assert "complete-head waist-up" in waist["framing_prompt"].lower()
    assert "never crop the crown" in waist["framing_prompt"].lower()
    assert "both knees and upper calves" in three["framing_prompt"].lower()
    assert "torso-only portrait" in three["framing_prompt"].lower()


def test_extended_puppy_is_face_down_before_camera_geometry():
    profile = _profile()
    plan = _plan(
        profile,
        shot_type="Three-Quarter Body",
        pose=EXTENDED_PUPPY,
        camera_view="Back View",
        camera_height="Eye Level",
    )
    prompt = plan["final_shot_prompt"].lower()
    assert prompt.index("kneeling face-down") < prompt.index("direct rear camera position")
    assert "not supine" in prompt
    assert "pelvis remains elevated above the knees" in prompt
    assert "hands are the farthest landmarks" in prompt
    assert "level lens axis" in prompt


def test_daisy_dukes_are_extra_low_rise_rigid_denim_not_yoga_pants():
    profile = _profile(
        visible_presentation_mode="Clothed — Use Outfit Controls",
        outfit_input_method="Preset — Ready-Made Complete Outfit",
        preset_outfit_if_selected="High-Hem Crop Top and Daisy Dukes",
    )
    bottom = profile["outfit_components"]["bottom"].lower()
    assert "extra-low-rise rigid distressed blue denim cutoff micro-shorts" in bottom
    assert "at or slightly below the pelvic-bone line" in bottom
    assert "heavy irregular frayed denim threads" in bottom
    assert "lower buttock curves" in bottom
    assert "never become leggings, yoga pants" in bottom


def test_front_view_right_forearm_maps_to_left_side_of_image():
    profile = _profile(
        tattoo_status="One",
        tattoo_input_mode="Structured Single Tattoo",
        structured_tattoo_location="Right Forearm",
        structured_tattoo_description="colored hummingbird with an orchid",
    )
    plan = _plan(profile, shot_type="Chest-Up", camera_view="Front View")
    marks = json.loads(_assemble(profile, plan)[18])["visible_marks"].lower()
    assert "anatomical right forearm, which appears on the left side of the image" in marks
    assert "anatomical left corresponding region on the right side of the image" in marks
    assert "ghost" in marks


def test_full_back_tattoo_uses_bilateral_large_coverage_authority():
    profile = _profile(
        tattoo_status="One",
        tattoo_input_mode="Structured Single Tattoo",
        structured_tattoo_location="Full Back",
        structured_tattoo_description="elaborate Japanese samurai and dragon composition",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
    )
    plan = _plan(profile, shot_type="Waist-Up Midshot", camera_view="Back View")
    marks = json.loads(_assemble(profile, plan)[18])["visible_marks"].lower()
    assert "seventy to eighty-five percent" in marks
    assert "centered on the spine" in marks
    assert "both anatomical sides" in marks
    assert "small localized emblem" in marks


def test_eyebrow_curved_barbell_passes_beneath_skin():
    profile = _profile(
        piercing_status="One",
        piercing_input_mode="Structured Single Piercing",
        piercing_location="Left Eyebrow",
        piercing_type="Curved Barbell",
        piercing_material="Black Titanium",
    )
    plan = _plan(profile, camera_view="Front View")
    marks = json.loads(_assemble(profile, plan)[18])["visible_marks"].lower()
    assert "curved shaft passes beneath the skin" in marks
    assert "two healed piercing openings" in marks
    assert "not resting on top of the skin" in marks
    assert "right side of the image" in marks


def test_krea_anchor_plan_puts_approved_face_first_and_body_is_not_qwen_source():
    profile = _profile()
    d = FCCKreaBlueprintDatasetDirector()
    out = d.direct(profile, "Anchors Only — 2", "Test", 2000, 1)
    prompts, ids, manifest = out[0], out[2], json.loads(out[7])
    assert len(prompts) == 2
    assert ids[0].startswith("00_approved_face_anchor_candidate")
    assert "approve this image for qwen image 1" in prompts[0].lower()
    assert "body and anatomy images never feed the qwen angle lane" in manifest["qwen_handoff"].lower()


def test_complete_krea_plan_contains_face_body_clothed_clinical_mid_and_full():
    profile = _profile()
    out = FCCKreaBlueprintDatasetDirector().direct(profile, "Complete Blueprint Documentation", "Test", 2000, 1)
    cats = set(out[3])
    assert {"face_anchor", "head_shoulders", "face_detail", "body_region_clothed", "body_region_clinical", "canonical_midshot", "canonical_full_body"} <= cats
    assert len(out[0]) == 101
    body_prompts = [p.lower() for p,c in zip(out[0],out[3]) if c == "body_region_clinical"]
    assert any("head and face remain outside this regional crop" in p for p in body_prompts)
    assert any("neutral non-aroused adult clinical anatomy documentation" in p for p in body_prompts)


def test_qwen_director_is_face_angles_only_and_contains_no_blueprint_content():
    profile = _profile(
        tattoo_status="One",
        tattoo_input_mode="Structured Single Tattoo",
        structured_tattoo_location="Right Forearm",
        structured_tattoo_description="hummingbird and orchid",
    )
    out = FCCFaceAngleDatasetDirector().direct(
        profile, "Approved Face-Visible Identity Angles — Core 8", "Image 1", "Test", 1000, 1, 8, False
    )
    assert len(out[0]) == 8
    assert all(c == "face_identity_angle" for c in out[3])
    joined=" ".join(out[0]).lower()
    assert "tattoo" not in joined
    assert "bust" not in joined
    assert "clothing" not in joined
    assert all(s.startswith("face__") for s in out[2])
    assert not any("__back" in s or "back__" in s for s in out[2])
    assert any("__left_side__" in s for s in out[2])
    assert any("__right_side__" in s for s in out[2])


def test_2511_and_2509_exact_face_ids_have_unambiguous_camera_mapping():
    mode=FCCQwenAnglePromptMode()
    p2511,summary=mode.build_prompt("camera only", "face__back_left__eye_level__close_up_v01", "face_identity_angle", "Qwen Image Edit 2511 — Multiple Angles <sks>")
    assert p2511 == "<sks> back-left quarter view eye-level shot close-up"
    assert "approved krea face portrait" in summary.lower()
    p2509,_=mode.build_prompt("camera only", "face__right_side__low_angle__close_up_v01", "face_identity_angle", "Qwen Image Edit 2509 — Multiple Angles")
    assert "Rotate the camera 90 degrees to the right." in p2509
    assert "Move the camera down and look up." in p2509
    assert "close-up" in p2509


def test_complete_krea_plan_has_eight_view_midshots_and_full_bodies():
    profile = _profile()
    out = FCCKreaBlueprintDatasetDirector().direct(profile, "Complete Blueprint Documentation", "Test", 2000, 1)
    cats = out[3]
    assert cats.count("canonical_midshot") == 16
    assert cats.count("canonical_full_body") == 16
    assert cats.count("body_region_clothed") == 27
    assert cats.count("body_region_clinical") == 32


def test_regional_hand_prompt_is_crop_isolated_and_has_five_digit_lock():
    profile = _profile(
        visible_presentation_mode="Clothed — Use Outfit Controls",
        outfit_input_method="Preset — Ready-Made Complete Outfit",
        preset_outfit_if_selected="Casual Jeans and T-Shirt",
    )
    out = FCCKreaBlueprintDatasetDirector().direct(profile, "Body Regions Clothed", "Test", 2000, 1)
    prompt = next(p for p, sid in zip(out[0], out[2]) if sid.startswith("clothed_left_hand_dorsal"))
    low = prompt.lower()
    assert "exactly five naturally separated fingers" in low
    assert "opposite arm remains outside the crop" not in low
    assert "do not widen the regional crop to display the complete outfit" in low
    assert "well-fitted jeans" not in low


def test_clinical_chest_close_is_side_specific_and_non_sensual():
    profile = _profile()
    out = FCCKreaBlueprintDatasetDirector().direct(profile, "Body Regions Clinical Unclothed", "Test", 2000, 1)
    prompt = next(p for p, sid in zip(out[0], out[2]) if sid.startswith("clinical_left_chest_close"))
    low = prompt.lower()
    assert "neutral non-aroused adult clinical anatomy documentation" in low
    assert "anatomical left chest or breast region" in low
    assert "do not mirror it or add a second breast" in low
    assert "no sensual posing" in low


def test_krea_manifest_marks_only_face_anchor_as_face_identity_source():
    profile = _profile()
    out = FCCKreaBlueprintDatasetDirector().direct(profile, "Complete Blueprint Documentation", "Test", 2000, 1)
    manifest = json.loads(out[7])
    sources = [item for item in manifest["items"] if item["face_identity_source"]]
    assert len(sources) == 1
    assert sources[0]["category"] == "face_anchor"


def test_all_fours_front_and_three_quarter_are_on_floor_and_keep_hair_highlights():
    from full_character_creation_core.src.nodes_v247 import ALL_FOURS

    profile = _profile(
        hair_color="Auburn / Copper Red",
        hair_highlights="blue and pink face-framing streaks",
        visible_presentation_mode="Clothed — Use Outfit Controls",
        outfit_input_method="Preset — Ready-Made Complete Outfit",
        preset_outfit_if_selected="Casual Jeans and T-Shirt",
    )
    for view in ("Front View", "Three-Quarter Left", "Three-Quarter Right"):
        plan = _plan(
            profile,
            shot_type="Full Body",
            pose=ALL_FOURS,
            camera_view=view,
            camera_height="Eye Level",
            lens="50mm Normal",
        )
        prompt = _assemble(profile, plan)[0].lower()
        assert "tabletop" not in prompt
        assert "directly on the room floor" in prompt
        assert "no table, countertop, desk, bench, bed, platform" in prompt
        assert "blue and pink face-framing streaks" in prompt
        assert "front hairline, temple strands, face-framing sections" in prompt
        assert "do not disappear, revert to one solid color" in prompt


def test_full_arm_and_leg_sleeve_locations_are_available():
    choices = CharacterBlueprintCreatorV253.INPUT_TYPES()["required"]["structured_tattoo_location"][0]
    assert "Full Left Arm Sleeve" in choices
    assert "Full Right Arm Sleeve" in choices
    assert "Full Left Leg Sleeve" in choices
    assert "Full Right Leg Sleeve" in choices


def test_full_left_arm_sleeve_compiles_continuous_coverage():
    profile = _profile(
        tattoo_status="One",
        tattoo_input_mode="Structured Single Tattoo",
        structured_tattoo_location="Full Left Arm Sleeve",
        structured_tattoo_description="Japanese floral and koi composition",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
    )
    plan = _plan(profile, shot_type="Full Body", camera_view="Front View", lens="50mm Normal")
    marks = json.loads(_assemble(profile, plan)[18])["visible_marks"].lower()
    assert "full anatomical left arm sleeve" in marks
    assert "shoulder cap" in marks
    assert "crosses the elbow without breaking" in marks
    assert "ends cleanly at the wrist" in marks
    assert "eighty to ninety-five percent" in marks
    assert "anatomical right arm" in marks
    assert "do not mirror, swap sides, split, shrink" in marks


def test_full_right_leg_sleeve_compiles_continuous_coverage():
    profile = _profile(
        tattoo_status="One",
        tattoo_input_mode="Structured Single Tattoo",
        structured_tattoo_location="Full Right Leg Sleeve",
        structured_tattoo_description="black and gray botanical composition",
        visible_presentation_mode="Clinical Anatomy — No Clothing",
    )
    plan = _plan(profile, shot_type="Full Body", camera_view="Front View", lens="50mm Normal")
    marks = json.loads(_assemble(profile, plan)[18])["visible_marks"].lower()
    assert "full anatomical right leg sleeve" in marks
    assert "begins high on the upper thigh" in marks
    assert "crosses the knee without breaking" in marks
    assert "ends cleanly at the ankle" in marks
    assert "eighty to ninety-five percent" in marks
    assert "anatomical left leg" in marks
