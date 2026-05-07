# Paper Card

## Problem

Open-set segmentation and CLIP-style semantics can produce many candidate objects and concepts. The paper asks what granularity a robot should keep in the map when it has task descriptions in natural language.

## Core Idea

Use task relevance to cluster 3D primitives into task-sufficient objects/regions and build a compact hierarchical 3D scene graph online.

## Input / Output

- Input: RGB-D observations, 3D primitives, natural-language task list
- Output: task-relevant hierarchical 3D scene graph

## Method

The method formulates task-driven 3D scene understanding with an Information Bottleneck objective and uses an agglomerative clustering pipeline to retain task-relevant semantic concepts.

## Main Claims

- Task-dependent granularity is necessary for open-set mapping.
- A compact task-driven scene graph can improve task execution while running online on onboard compute.

## Strengths

- Strong conceptual link between map representation and robot tasks.
- Directly relevant to human instruction following.
- Treats map granularity as an explicit research variable.

## Limitations

- Requires task list or task distribution.
- Evaluation is not primarily about dynamic stale object memory.
- Contribution is close to intent-conditioned map representation, so differentiation must be explicit.

## Relevance to My Research

This is the strongest prior for intent-aware semantic mapping. A new contribution should not merely repeat task-driven clustering; it should add temporal trust, staleness, or interaction-driven update.

## Follow-up Questions

- Can task-driven granularity also decide what stale memory to re-check?
- Can the task list be a single ambiguous human instruction rather than a pre-defined list?
