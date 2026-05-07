# Open-Vocabulary Functional 3D Scene Graphs for Real-World Indoor Spaces

## Bibliographic Info

- Year/Venue: 2025 CVPR
- Source: https://arxiv.org/abs/2503.19199

## One-Line Contribution

Introduces functional 3D scene graphs that capture objects, interactive elements, and functional relationships.

## Existing Limitation

Traditional 3D scene graphs focus on spatial relationships and miss functional knowledge needed for interaction.

## Why This Is Semantic Mapping

The semantic map must encode what objects afford and how they can be used, not only where they are.

## Method / Map Representation

Functional 3D scene graph from posed RGB-D; VLMs and LLMs encode functional knowledge under limited training data.

## Dataset / Benchmark / Metrics

Extended SceneFun3D and FunGraph3D; functional relation prediction; downstream 3D QA and robotic manipulation.

## Author Organization Pattern

Defines a new task, creates/extends datasets, adapts baselines, and demonstrates functional downstream tasks.

## Useful Insight

Affordance/function is a strong bridge from semantic mapping to human assistance.

## Failure Lesson

If function predictions fail, pure visual semantics may be insufficient without human interaction data.
