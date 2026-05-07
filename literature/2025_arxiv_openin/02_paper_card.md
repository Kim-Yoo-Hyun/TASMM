# Paper Card

## Problem

Domestic objects often move and category-level navigation is insufficient when the target is a specific instance.

## Core Idea

Use an open-vocabulary Carrier-Relationship Scene Graph to track relationships between movable objects and static carriers.

## Input / Output

- Input: visual observations, target instance query, scene graph state
- Output: updated carrier relationship and navigation decision

## Method

The paper models instance navigation as an MDP, using LLM commonsense and VLM feature similarity to choose actions based on the Carrier-Relationship Scene Graph.

## Main Claims

- Updating carrier relationships helps robots navigate efficiently to moved targets.
- Dynamic scene representation is necessary for instance-oriented domestic navigation.

## Strengths

- Strong match to stale semantic memory.
- Evaluates long-sequence tasks and real robot validation.

## Limitations

- Carrier relation may not cover all object movement.
- LLM commonsense priors can be user- or home-specific.

## Relevance to My Research

This is the closest prior for relation-based stale memory.

## Follow-up Questions

- Can stale memory be modeled without assuming carrier relationships?
- Can human correction update the Carrier-Relationship Scene Graph?
