from full_character_creation_core.src.nodes_v247 import (
    ALL_FOURS,
    EXTENDED_PUPPY,
    CharacterBlueprintCreatorV247,
    CharacterShotControlV247,
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


def _profile():
    kwargs = _defaults(CharacterBlueprintCreatorV247)
    kwargs.update({"tattoo_status": "None", "piercing_status": "None"})
    return CharacterBlueprintCreatorV247().build_blueprint_v247(**kwargs)[8]


def _plan(pose, shot="Three-Quarter Body", view="Back View"):
    profile = _profile()
    kwargs = _defaults(CharacterShotControlV247)
    kwargs.update({
        "pose": pose,
        "shot_type": shot,
        "camera_view": view,
        "aspect_ratio": "Auto by Shot",
        "lens": "Auto by Shot — Recommended",
    })
    return CharacterShotControlV247().build_shot_plan_v247(character_blueprint=profile, **kwargs)[0]


def test_current_pose_list_uses_neutral_solo_label():
    choices = CharacterShotControlV247.INPUT_TYPES()["required"]["pose"][0]
    assert ALL_FOURS in choices
    assert "Doggy-Style / All Fours — Hands and Knees" not in choices
    assert EXTENDED_PUPPY in choices


def test_all_fours_never_contains_standing_framing():
    plan = _plan(ALL_FOURS)
    combined = (plan["framing_prompt"] + " " + plan["pose_prompt"]).lower()
    assert "standing three-quarter" not in combined
    assert "solo tabletop pose" in combined
    assert "one continuous figure" in combined
    assert plan["recommended_width"] == 1536
    assert plan["recommended_height"] == 1024


def test_extended_puppy_is_not_tabletop():
    plan = _plan(EXTENDED_PUPPY)
    pose = plan["pose_prompt"].lower()
    assert "extended puppy yoga pose" in pose
    assert "arms reach far forward" in pose
    assert "chest and sternum lower" in pose
    assert "tabletop pose" not in pose


def test_rear_floor_camera_is_single_subject_and_rear_aligned():
    plan = _plan(ALL_FOURS, view="Back View")
    camera = plan["camera_prompt"].lower()
    scene = plan["scene_prompt"].lower()
    assert "strict rear floor-level view" in camera
    assert "camera is centered on the spine and pelvis" in camera
    assert "one single adult primary character" in scene
    assert plan["expression_prompt"] == ""


def test_floor_full_body_has_complete_landmarks():
    plan = _plan(EXTENDED_PUPPY, shot="Full Body")
    framing = plan["framing_prompt"].lower()
    for token in ("head and hair", "arms", "hands", "pelvis", "knees", "lower legs", "feet"):
        assert token in framing
