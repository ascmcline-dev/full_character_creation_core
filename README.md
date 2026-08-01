# Full Character Creation Core — V2.4.14

Integrated node suite for Full Character Creation Studio V2.8.14.

## Staged workflow

- **Stage 0:** standalone Krea2 generation baseline using Character Creator + Universal Shot Control. It has its own local randomized KSampler seed and does not depend on any queue stage.
- **Stage 2:** Krea2 pre-LoRA documentation. It can generate three identity anchors plus a body-only regional atlas from crown/nape through hands, torso, anatomy, legs, and feet in every believable direct/profile/rear/three-quarter view.
- **Stage 3:** Qwen Image Edit angle expansion from any approved Stage 2 face, midshot, full-body, or regional reference. The encoder receives clean angle metadata only.
- **Stage 4:** Krea2 final dataset expansion with the trained identity LoRA, Character Blueprint, and Shot Control.

All image approval remains manual in this version. Automatic pass/reject, caption curation, saved blueprint/LoRA binding, and character-evolution controls remain future features.
