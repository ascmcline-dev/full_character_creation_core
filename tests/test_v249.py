from full_character_creation_core.src.nodes_v248 import (
    ALL_FOURS,
    EXTENDED_PUPPY,
    CharacterBlueprintCreatorV248,
    CharacterShotControlV248,
)
from full_character_creation_core.src.nodes_v249 import (
    CharacterBlueprintCreatorV249,
    CharacterShotControlV249,
)


def _defaults(cls):
    values = {}
    for name, spec in cls.INPUT_TYPES()["required"].items():
        if name == "character_blueprint":
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


def _profile(cls=CharacterBlueprintCreatorV249):
    kwargs = _defaults(cls)
    kwargs.update({"tattoo_status": "None", "piercing_status": "None"})
    fn = "build_blueprint_v249" if cls is CharacterBlueprintCreatorV249 else "build_blueprint_v248"
    return getattr(cls(), fn)(**kwargs)[8]


def _plan(cls, pose, shot="Three-Quarter Body", view="Back View"):
    kwargs = _defaults(cls)
    kwargs.update({
        "pose": pose,
        "shot_type": shot,
        "camera_view": view,
        "aspect_ratio": "Auto by Shot",
        "lens": "Auto by Shot — Recommended",
    })
    fn = "build_shot_plan_v249" if cls is CharacterShotControlV249 else "build_shot_plan_v248"
    return getattr(cls(), fn)(character_blueprint=_profile(), **kwargs)[0]


def test_section_a_registration_remains_locked():
    choices = CharacterShotControlV249.INPUT_TYPES()["required"]["pose"][0]
    assert ALL_FOURS in choices
    assert EXTENDED_PUPPY in choices
    assert "Doggy-Style / All Fours — Hands and Knees" not in choices
    assert "Finger Heart Near Face" not in choices
    assert "Licking a Popsicle" not in choices


def test_section_b_rear_all_fours_is_unchanged():
    old = _plan(CharacterShotControlV248, ALL_FOURS, view="Back View")
    new = _plan(CharacterShotControlV249, ALL_FOURS, view="Back View")
    assert new["framing_prompt"] == old["framing_prompt"]
    assert new["camera_prompt"] == old["camera_prompt"]
    assert new["pose_prompt"] == old["pose_prompt"]
    assert new.get("rear_tabletop_lock") is True


def test_rear_puppy_direct_back_is_anchored_behind_pelvis():
    plan = _plan(CharacterShotControlV249, EXTENDED_PUPPY, view="Back View")
    camera = plan["camera_prompt"].lower()
    assert plan.get("rear_puppy_lock") is True
    assert "strict direct rear view photographed from behind the pelvis" in camera
    assert "rear hips, sacrum, and lower back form the nearest central foreground" in camera
    assert "hands are the farthest body landmarks" in camera
    assert "only posterior body surfaces" in camera


def test_rear_puppy_pose_avoids_front_view_trigger_word():
    plan = _plan(CharacterShotControlV249, EXTENDED_PUPPY, view="Back View")
    pose = plan["pose_prompt"].lower()
    assert "extended puppy yoga pose" in pose
    assert "arms extend straight away from the knees along the floor" in pose
    assert "facial plane is directed toward the floor and away from the rear camera" in pose
    assert "forward" not in pose
    assert "tabletop pose" not in pose


def test_rear_three_quarter_left_stays_rear_dominant():
    plan = _plan(CharacterShotControlV249, EXTENDED_PUPPY, view="Rear Three-Quarter Left")
    camera = plan["camera_prompt"].lower()
    assert plan.get("rear_puppy_lock") is True
    assert "behind the pelvis" in camera
    assert "twenty to thirty degrees" in camera
    assert "anatomical left" in camera
    assert "rear hips, sacrum, lower back, and back remain the dominant visible surfaces" in camera
    assert "only a narrow side contour" in camera
    assert "facial plane remains directed toward the floor and away from the lens" in camera


def test_rear_three_quarter_right_stays_rear_dominant():
    plan = _plan(CharacterShotControlV249, EXTENDED_PUPPY, view="Rear Three-Quarter Right")
    camera = plan["camera_prompt"].lower()
    assert "anatomical right" in camera
    assert "rear view remains primary" in camera


def test_front_extended_puppy_is_inherited_unchanged():
    old = _plan(CharacterShotControlV248, EXTENDED_PUPPY, view="Front View")
    new = _plan(CharacterShotControlV249, EXTENDED_PUPPY, view="Front View")
    assert new["framing_prompt"] == old["framing_prompt"]
    assert new["camera_prompt"] == old["camera_prompt"]
    assert new["pose_prompt"] == old["pose_prompt"]
    assert not new.get("rear_puppy_lock")


def _assemble(profile_updates=None, shot_updates=None, purpose="Krea — First Identity Image"):
    profile_updates = profile_updates or {}
    shot_updates = shot_updates or {}
    ckw = _defaults(CharacterBlueprintCreatorV249)
    ckw.update({"tattoo_status": "None", "piercing_status": "None"})
    ckw.update(profile_updates)
    profile = CharacterBlueprintCreatorV249().build_blueprint_v249(**ckw)[8]
    skw = _defaults(CharacterShotControlV249)
    skw.update({
        "shot_type": "Full Body",
        "camera_view": "Front View",
        "pose": "Neutral Standing",
        "lens": "Auto by Shot — Recommended",
        "aspect_ratio": "Auto by Shot",
    })
    skw.update(shot_updates)
    plan = CharacterShotControlV249().build_shot_plan_v249(character_blueprint=profile, **skw)[0]
    from full_character_creation_core.src.nodes_v249 import CharacterPromptAssemblerV249
    result = CharacterPromptAssemblerV249().assemble_prompt_v249(
        profile, plan, purpose, "Image 1"
    )
    return profile, plan, result


def test_simple_dress_has_complete_rear_bodice_and_attached_skirt():
    _, _, result = _assemble(
        {
            "visible_presentation_mode": "Clothed — Use Outfit Controls",
            "outfit_input_method": "Preset — Ready-Made Complete Outfit",
            "preset_outfit_if_selected": "Simple Dress",
        },
        {"camera_view": "Back View", "shot_type": "Full Body"},
    )
    prompt = result[0].lower()
    assert "one complete opaque one-piece dress" in prompt
    assert "full rear fabric panels" in prompt
    assert "rear bodice continuously covers both shoulders, the upper back, mid-back, and waist" in prompt
    assert "attached straight skirt" in prompt
    assert "upper-body garment" not in prompt


def test_standard_opaque_garment_preserves_selected_bust_silhouette():
    _, _, result = _assemble(
        {
            "primary_character_gender": "Adult Woman",
            "chest_anatomy": "Bust Anatomy — Use Bust Controls",
            "bust_size": "Large",
            "bust_shape": "Natural Teardrop — Gentle Upper Slope",
            "bust_position": "High-Set / Perky",
            "bust_firmness": "Firm",
            "bust_augmentation": "Round High-Profile Implants",
            "visible_presentation_mode": "Clothed — Use Outfit Controls",
            "outfit_input_method": "Preset — Ready-Made Complete Outfit",
            "preset_outfit_if_selected": "Simple Dress",
        },
        {"camera_view": "Front View", "shot_type": "Waist-Up Midshot"},
    )
    prompt = result[0].lower()
    assert "non-compressive across the chest" in prompt
    assert "preserves the complete selected covered volume" in prompt
    assert "large bust silhouette" in prompt
    assert "high-set" in prompt
    assert "high-profile augmented contour" in prompt
    assert "nipple and areola details are not described through the clothing" in prompt
    assert "bust size subtly shapes" not in prompt


def test_rear_clothed_view_omits_bust_silhouette_details():
    _, _, result = _assemble(
        {
            "primary_character_gender": "Adult Woman",
            "chest_anatomy": "Bust Anatomy — Use Bust Controls",
            "bust_size": "Large",
            "bust_shape": "Natural Teardrop — Gentle Upper Slope",
            "bust_position": "High-Set / Perky",
            "bust_augmentation": "Round High-Profile Implants",
            "visible_presentation_mode": "Clothed — Use Outfit Controls",
            "outfit_input_method": "Preset — Ready-Made Complete Outfit",
            "preset_outfit_if_selected": "Simple Dress",
        },
        {"camera_view": "Back View", "shot_type": "Full Body"},
    )
    prompt = result[0].lower()
    assert "non-compressive across the chest" not in prompt
    assert "high-profile augmented" not in prompt
    assert "bust size subtly shapes" not in prompt


def test_dress_precedes_body_silhouette_in_krea_prompt():
    _, _, result = _assemble(
        {
            "visible_presentation_mode": "Clothed — Use Outfit Controls",
            "outfit_input_method": "Preset — Ready-Made Complete Outfit",
            "preset_outfit_if_selected": "Simple Dress",
        },
        {"camera_view": "Front View", "shot_type": "Full Body"},
    )
    prompt = result[0].lower()
    assert prompt.index("wearing simple fitted knee-length dress") < prompt.index("shoulder and upper-torso silhouette")
