from .src.nodes_v260 import (
    QwenDatasetQueueV260,
    CharacterBlueprintCreatorV260,
    CharacterShotControlV260,
    CharacterPromptAssemblerV260,
)
from .src.dataset_v260 import (
    FCCFaceAngleDatasetDirector,
    FCCKreaBlueprintDatasetDirector,
    FCCKreaQueueItemRouter,
)
from .src.nodes import FCCQueueItemRouter
from .src.workflow_tools import FCCQwenAnglePromptMode, FCCSupportPanel

NODE_CLASS_MAPPINGS = {
    "QwenDatasetQueue": QwenDatasetQueueV260,
    "FCCDatasetDirector": FCCFaceAngleDatasetDirector,
    "FCCQueueItemRouter": FCCQueueItemRouter,
    "FCCKreaBlueprintDatasetDirector": FCCKreaBlueprintDatasetDirector,
    "FCCKreaQueueItemRouter": FCCKreaQueueItemRouter,
    "CharacterBlueprintCreatorV260": CharacterBlueprintCreatorV260,
    "CharacterShotControlV260": CharacterShotControlV260,
    "CharacterPromptAssemblerV260": CharacterPromptAssemblerV260,
    "FCCQwenAnglePromptMode": FCCQwenAnglePromptMode,
    "FCCSupportPanel": FCCSupportPanel,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "QwenDatasetQueue": "FCC Legacy Qwen Queue (Stage 3 Compatibility)",
    "FCCDatasetDirector": "FCC Stage 3 Qwen Angle-Completion Director",
    "FCCQueueItemRouter": "FCC Stage 3 Qwen Item + Live Count",
    "FCCKreaBlueprintDatasetDirector": "FCC Stage 2 Canonical Regional + Native Extreme Macro Director",
    "FCCKreaQueueItemRouter": "FCC Stage 2 Item + Live Count",
    "CharacterBlueprintCreatorV260": "FCC Character Creator",
    "CharacterShotControlV260": "FCC Universal Shot Control",
    "CharacterPromptAssemblerV260": "FCC Character + Shot Prompt Assembler",
    "FCCQwenAnglePromptMode": "FCC Qwen Angle Prompt Mode (2511 / 2509)",
    "FCCSupportPanel": "FCC Support / Community Panel",
}

WEB_DIRECTORY = "./web/js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
