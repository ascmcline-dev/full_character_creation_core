from __future__ import annotations

from typing import Tuple


PROMPT_MODES = [
    "Qwen Image Edit 2511 — Multiple Angles <sks>",
    "Qwen Image Edit 2509 — Multiple Angles",
    "Original FCC Dataset Prompt",
]


def _clean_text(*values: str) -> str:
    return " ".join(str(value or "").lower().replace("_", " ") for value in values)


def _infer_azimuth(shot_id: str, legacy_prompt: str) -> str:
    text = _clean_text(shot_id, legacy_prompt)
    if any(token in text for token in (
        "rear turn left", "rear three quarter left", "back left", "rear left",
        "back-left", "back left quarter",
    )):
        return "back-left quarter view"
    if any(token in text for token in (
        "rear turn right", "rear three quarter right", "back right", "rear right",
        "back-right", "back right quarter",
    )):
        return "back-right quarter view"
    if "rear three quarter" in text or "back three quarter" in text:
        return "back-right quarter view"
    if any(token in text for token in (
        "three quarter left", "front left", "front-left", "three-quarter left",
    )):
        return "front-left quarter view"
    if any(token in text for token in (
        "three quarter right", "front right", "front-right", "three-quarter right",
    )):
        return "front-right quarter view"
    if any(token in text for token in (
        "left profile", "left side", "true left profile", "left-profile",
    )):
        return "left side view"
    if any(token in text for token in (
        "right profile", "right side", "true right profile", "right-profile",
    )):
        return "right side view"
    if any(token in text for token in (
        "direct back", "back view", "rear view", "from behind", " full back",
    )):
        return "back view"
    return "front view"


def _infer_elevation(shot_id: str, legacy_prompt: str) -> str:
    text = _clean_text(shot_id, legacy_prompt)
    if any(token in text for token in (
        "top down", "top-down", "overhead", "high angle", "high-angle",
    )):
        return "high-angle shot"
    if any(token in text for token in (
        "slight up", "chin slightly raised", "from below", "low angle", "low-angle",
    )):
        return "low-angle shot"
    if any(token in text for token in (
        "slight down", "chin slightly lowered", "from above", "elevated",
        "camera only slightly above", "slightly above eye level",
    )):
        return "elevated shot"
    return "eye-level shot"


def _infer_distance(shot_id: str, category: str, legacy_prompt: str) -> str:
    text = _clean_text(shot_id, category, legacy_prompt)
    category_key = str(category or "").strip().lower()
    if any(token in text for token in (
        "extreme close", "macro extreme", "macro close", "close-up", "close up",
        "head-and-shoulders", "head and shoulders",
    )):
        return "close-up"
    if category_key in {"extreme_closeup", "closeup", "anatomy_focus"}:
        return "close-up"
    if any(token in text for token in (
        "full-body", "full body", "wide shot", "environmental full",
    )):
        return "wide shot"
    if category_key == "full_body":
        return "wide shot"
    return "medium shot"


def _exact_face_angle_tokens(shot_id: str):
    """Resolve v2.8.13 face-only IDs without heuristic ambiguity."""
    text = str(shot_id or "").lower()
    match = __import__("re").search(
        r"face__(front_left|front_right|left_side|right_side|back_left|back_right|front|back)__(eye_level|low_angle|elevated|high_angle)__(close_up|medium|wide)",
        text,
    )
    if not match:
        return None
    az_key, el_key, dist_key = match.groups()
    azimuth = {
        "front": "front view",
        "front_right": "front-right quarter view",
        "right_side": "right side view",
        "back_right": "back-right quarter view",
        "back": "back view",
        "back_left": "back-left quarter view",
        "left_side": "left side view",
        "front_left": "front-left quarter view",
    }[az_key]
    elevation = {
        "low_angle": "low-angle shot",
        "eye_level": "eye-level shot",
        "elevated": "elevated shot",
        "high_angle": "high-angle shot",
    }[el_key]
    distance = {"close_up": "close-up", "medium": "medium shot", "wide": "wide shot"}[dist_key]
    return azimuth, elevation, distance


def _infer_camera(shot_id: str, category: str, legacy_prompt: str) -> Tuple[str, str, str]:
    exact = _exact_face_angle_tokens(shot_id)
    if exact:
        return exact
    return (
        _infer_azimuth(shot_id, legacy_prompt),
        _infer_elevation(shot_id, legacy_prompt),
        _infer_distance(shot_id, category, legacy_prompt),
    )


def _prompt_2511(azimuth: str, elevation: str, distance: str) -> str:
    return f"<sks> {azimuth} {elevation} {distance}"


def _prompt_2509(azimuth: str, elevation: str, distance: str) -> str:
    horizontal = {
        "front view": "Turn the camera to a straight-on front view.",
        "front-right quarter view": "Rotate the camera 45 degrees to the right.",
        "right side view": "Rotate the camera 90 degrees to the right.",
        "back-right quarter view": "Rotate the camera 135 degrees to the right.",
        "back view": "Rotate the camera 180 degrees around the subject.",
        "back-left quarter view": "Rotate the camera 135 degrees to the left.",
        "left side view": "Rotate the camera 90 degrees to the left.",
        "front-left quarter view": "Rotate the camera 45 degrees to the left.",
    }[azimuth]
    vertical = {
        "low-angle shot": "Move the camera down and look up.",
        "eye-level shot": "Keep the camera at eye level.",
        "elevated shot": "Move the camera up and look slightly down.",
        "high-angle shot": "Turn the camera to a top-down view.",
    }[elevation]
    framing = {
        "close-up": "Turn the camera to a close-up.",
        "medium shot": "Use a medium shot.",
        "wide shot": "Turn the camera to a wide-angle shot.",
    }[distance]
    return f"{horizontal} {vertical} {framing}"


class FCCQwenAnglePromptMode:
    CATEGORY = "character creation/dataset"
    FUNCTION = "build_prompt"
    DESCRIPTION = (
        "Face-only v2.8.13 camera prompt selector. It maps exact approved-face shot IDs to clean Qwen Image Edit 2511 or 2509 Multiple Angles prompts. "
        "Angle modes never pass FCC body, anatomy, clothing, tattoo, piercing, count-lock, or character-ID prose into the encoder."
    )
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("qwen_prompt", "routing_summary")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "legacy_prompt": ("STRING", {"forceInput": True}),
                "shot_id": ("STRING", {"forceInput": True}),
                "category": ("STRING", {"forceInput": True}),
                "prompt_mode": (PROMPT_MODES, {"default": PROMPT_MODES[0]}),
            }
        }

    def build_prompt(self, legacy_prompt: str, shot_id: str, category: str, prompt_mode: str):
        azimuth, elevation, distance = _infer_camera(shot_id, category, legacy_prompt)
        if prompt_mode == PROMPT_MODES[1]:
            prompt = _prompt_2509(azimuth, elevation, distance)
        elif prompt_mode == PROMPT_MODES[2]:
            prompt = str(legacy_prompt or "").strip()
        else:
            prompt = _prompt_2511(azimuth, elevation, distance)
        summary = "\n".join([
            f"PROMPT MODE: {prompt_mode}",
            f"SHOT ID: {shot_id}",
            f"CATEGORY: {category}",
            f"AZIMUTH: {azimuth}",
            f"ELEVATION: {elevation}",
            f"DISTANCE: {distance}",
            f"ACTUAL ENCODER PROMPT: {prompt}",
            "REFERENCE RULE: Image 1 must be the approved Krea face portrait, not a body or regional documentation image.",
            "QUALITY DIAGNOSTIC: validate the angle LoRA on a clean compatible Qwen angle lane before adding skin or other LoRAs.",
        ])
        return prompt, summary


class FCCSupportPanel:
    CATEGORY = "character creation/studio"
    FUNCTION = "display"
    DESCRIPTION = (
        "Movable FCC support/community panel. Its frontend DOM content lives in this separate node "
        "so it cannot resize or compress Character Creator controls."
    )
    RETURN_TYPES = ()
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    def display(self):
        return ()
