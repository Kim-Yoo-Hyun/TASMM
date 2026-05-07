# Paper Card

## Problem

Embodied agents must ground free-form natural-language instructions to specific targets in open-world environments.

## Core Idea

Construct an instance-level open-vocabulary visual-language map and use structural-semantic consistency to ground instructions.

## Input / Output

- Input: navigation scene observations and free-form instruction
- Output: target instance / heatmap alignment

## Method

The paper performs fine-grained instance-level semantic mapping and uses Structural-Semantic Consensus over global geometry and VLM similarity.

## Main Claims

- Instance-level visual-language mapping improves instruction grounding.
- Structural and semantic consistency reduce cross-view grounding errors.

## Strengths

- Direct human-language interface.
- Strong bridge from semantic map to instruction grounding.

## Limitations

- Primarily static instruction grounding.
- Does not center dynamic stale object memory.

## Relevance to My Research

Useful static grounding baseline before adding dynamic staleness.

## Follow-up Questions

- What happens when the grounded target moved after mapping?
- Can correction update the instance-level map?
