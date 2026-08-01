from full_character_creation_core.src.nodes_v247 import CharacterShotControlV247
from full_character_creation_core.src.nodes_v248 import (
    ALL_FOURS,
    EXTENDED_PUPPY,
    FORWARD_LEAN,
    CharacterBlueprintCreatorV248,
    CharacterShotControlV248,
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
    kwargs = _defaults(CharacterBlueprintCreatorV248)
    kwargs.update({"tattoo_status": "None", "piercing_status": "None"})
    return CharacterBlueprintCreatorV248().build_blueprint_v248(**kwargs)[8]


def _plan(cls, pose, shot="Three-Quarter Body", view="Back View"):
    profile = _profile()
    kwargs = _defaults(cls)
    kwargs.update({
        "pose": pose,
        "shot_type": shot,
        "camera_view": view,
        "aspect_ratio": "Auto by Shot",
        "lens": "Auto by Shot — Recommended",
    })
    fn = "build_shot_plan_v248" if cls is CharacterShotControlV248 else "build_shot_plan_v247"
    return getattr(cls(), fn)(character_blueprint=profile, **kwargs)[0]


def test_section_a_locked_pose_registration():
    choices = CharacterShotControlV248.INPUT_TYPES()["required"]["pose"][0]
    assert ALL_FOURS in choices
    assert EXTENDED_PUPPY in choices
    assert "Doggy-Style / All Fours — Hands and Knees" not in choices


def test_requested_pose_menu_maintenance():
    choices = CharacterShotControlV248.INPUT_TYPES()["required"]["pose"][0]
    assert FORWARD_LEAN in choices
    assert "Finger Heart Near Face" not in choices
    assert "Licking a Popsicle" not in choices


def test_rear_all_fours_camera_is_behind_pelvis():
    plan = _plan(CharacterShotControlV248, ALL_FOURS, view="Back View")
    camera = plan["camera_prompt"].lower()
    assert plan["rear_tabletop_lock"] is True
    assert "rear side of the pelvis" in camera
    assert "rear hips and lower back occupy the central foreground" in camera
    assert "back of the head is the only visible side" in camera
    assert "face located on the far side" in camera


def test_rear_all_fours_is_true_tabletop_geometry():
    plan = _plan(CharacterShotControlV248, ALL_FOURS, view="Back View")
    pose = plan["pose_prompt"].lower()
    assert "torso is elevated" in pose
    assert "parallel to the floor" in pose
    assert "shoulders are vertically above the wrists" in pose
    assert "hip sockets are vertically above the knees" in pose
    assert "thighs are near vertical" in pose
    assert "pelvis remains clearly separated above the heels" in pose
    assert "head is lifted" in pose
    assert "gaze is directed forward away from the camera" in pose


def test_front_all_fours_passed_behavior_is_unchanged():
    old = _plan(CharacterShotControlV247, ALL_FOURS, view="Front View")
    new = _plan(CharacterShotControlV248, ALL_FOURS, view="Front View")
    assert new["framing_prompt"] == old["framing_prompt"]
    assert new["camera_prompt"] == old["camera_prompt"]
    assert new["pose_prompt"] == old["pose_prompt"]
    assert new["recommended_width"] == old["recommended_width"] == 1536
    assert new["recommended_height"] == old["recommended_height"] == 1024


def test_forward_lean_is_body_only():
    plan = _plan(CharacterShotControlV248, FORWARD_LEAN, view="Front View")
    pose = plan["pose_prompt"].lower()
    assert "forward lean from the hips" in pose
    for forbidden in ("seated", "bed", "bench", "chair", "support surface", "furniture"):
        assert forbidden not in pose
