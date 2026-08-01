from .src.nodes_v254 import (
    QwenDatasetQueueV254,
    CharacterBlueprintCreatorV254,
    CharacterShotControlV254,
    CharacterPromptAssemblerV254,
)
from .src.dataset_v254 import (
    FCCFaceAngleDatasetDirector,
    FCCKreaBlueprintDatasetDirector,
    FCCKreaQueueItemRouter,
)
from .src.nodes import FCCQueueItemRouter
from .src.workflow_tools import FCCQwenAnglePromptMode, FCCSupportPanel

NODE_CLASS_MAPPINGS = {
    "QwenDatasetQueue": QwenDatasetQueueV254,
    "FCCDatasetDirector": FCCFaceAngleDatasetDirector,
    "FCCQueueItemRouter": FCCQueueItemRouter,
    "FCCKreaBlueprintDatasetDirector": FCCKreaBlueprintDatasetDirector,
    "FCCKreaQueueItemRouter": FCCKreaQueueItemRouter,
    "CharacterBlueprintCreatorV254": CharacterBlueprintCreatorV254,
    "CharacterShotControlV254": CharacterShotControlV254,
    "CharacterPromptAssemblerV254": CharacterPromptAssemblerV254,
    "FCCQwenAnglePromptMode": FCCQwenAnglePromptMode,
    "FCCSupportPanel": FCCSupportPanel,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "QwenDatasetQueue": "FCC Legacy Qwen Queue (Stage 3 Compatibility)",
    "FCCDatasetDirector": "FCC Stage 3 Qwen Angle-Expansion Director",
    "FCCQueueItemRouter": "FCC Stage 3 Qwen Item + Live Count",
    "FCCKreaBlueprintDatasetDirector": "FCC Stage 2 Krea Regional-Atlas Director",
    "FCCKreaQueueItemRouter": "FCC Stage 2 Krea Item + Live Count",
    "CharacterBlueprintCreatorV254": "FCC Character Creator",
    "CharacterShotControlV254": "FCC Universal Shot Control",
    "CharacterPromptAssemblerV254": "FCC Character + Shot Prompt Assembler",
    "FCCQwenAnglePromptMode": "FCC Qwen Angle Prompt Mode (2511 / 2509)",
    "FCCSupportPanel": "FCC Support / Community Panel",
}

WEB_DIRECTORY = "./web/js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
