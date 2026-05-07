# Paper Card

## Problem

Many scene graph methods require a complete pre-built semantic map, which is unrealistic for robots exploring incrementally.

## Core Idea

Build semantic Gaussian maps and scene graphs incrementally using confidence, temporal memory, and progressive graph updates.

## Input / Output

- Input: incremental scene observations
- Output: open-vocabulary semantic Gaussian map and scene graph

## Method

The paper reports confidence-based Gaussian semantic representation, hierarchical semantic optimization, temporal memory, and progressive scene graph construction.

## Main Claims

- Incremental open-vocabulary scene graph mapping is possible without a complete pre-built map.
- Confidence and temporal memory improve global semantic consistency.

## Strengths

- Directly aligned with 2026 trend: online/incremental + temporal memory.
- Useful prior for confidence design.

## Limitations

- Need to check whether it handles moved objects or only incremental observation of static scenes.
- Gaussian representation may be heavier than needed for first thesis experiment.

## Relevance to My Research

Important for temporal memory language, but likely not the first implementation target.

## Follow-up Questions

- Does temporal memory represent staleness or just multi-view consistency?
- Can object-level stale verification be evaluated without Gaussian reconstruction?
