# Paper Card

## Problem

Spatial 3D scene graphs do not capture functional relationships needed for interaction.

## Core Idea

Predict open-vocabulary functional 3D scene graphs that include objects, interactive elements, and functional relationships.

## Input / Output

- Input: posed RGB-D images
- Output: functional 3D scene graph

## Method

Uses VLMs and LLMs to encode functional knowledge under limited training data.

## Main Claims

- Functional 3D scene graphs outperform adapted spatial scene graph baselines for functionality.
- Functional relations enable downstream 3D QA and robotic manipulation.

## Strengths

- Strong human-friendly robot intelligence angle.
- Provides datasets and downstream applications.

## Limitations

- Functional annotation and evaluation are heavier than navigation-only setups.
- Not directly about dynamic stale memory.

## Relevance to My Research

Good candidate if thesis shifts from dynamic memory to affordance-aware assistance.

## Follow-up Questions

- Can functional relation memory become stale?
- Can functional affordance guide re-checking moved objects?
