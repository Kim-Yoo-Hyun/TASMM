# EmbodiedScan: A Holistic Multi-Modal 3D Perception Suite Towards Embodied AI

## Bibliographic Info

- Year/Venue: 2024 CVPR
- Source: https://openaccess.thecvf.com/content/CVPR2024/html/Wang_EmbodiedScan_A_Holistic_Multi-Modal_3D_Perception_Suite_Towards_Embodied_AI_CVPR_2024_paper.html

## One-Line Contribution

Provides a large ego-centric multi-modal 3D perception dataset and benchmark for embodied scene understanding.

## Existing Limitation

Embodied agents need holistic 3D scene understanding, but datasets often lack aligned ego-centric RGB-D, language, boxes, and dense occupancy annotations.

## Why This Is Semantic Mapping

It supplies the annotated 3D scene perception substrate that semantic maps can be built and evaluated against.

## Method / Map Representation

Dataset plus baseline framework, Embodied Perceptron, for arbitrary multi-modal inputs.

## Dataset / Benchmark / Metrics

Over 5k scans, 1M ego-centric RGB-D views, 1M language prompts, 160k 3D boxes, 760+ categories, dense semantic occupancy with 80 categories.

## Author Organization Pattern

Dataset gap, dataset construction, benchmark tasks, baseline framework, then in-the-wild generalization.

## Useful Insight

For a thesis, benchmark selection should expose whether the map supports language-grounded 3D perception, not only object labels.

## Failure Lesson

If methods fail here, the issue may be missing holistic multi-modal context rather than just weak semantic labels.
