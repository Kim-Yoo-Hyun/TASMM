# Paper Card

## Problem

Large-scale language navigation needs semantic abstraction beyond object-level dense maps.

## Core Idea

Construct a floor-room-object hierarchical open-vocabulary 3D scene graph.

## Input / Output

- Input: RGB-D / 3D scene observations
- Output: hierarchical 3D scene graph and navigation graph

## Method

Builds object, room, and floor nodes, plus navigation structure for language-grounded robot navigation.

## Main Claims

- Hierarchical open-vocabulary scene graphs support scalable language-grounded navigation.

## Strengths

- Strong hierarchy argument.
- Evaluates representation size and real navigation.

## Limitations

- Not centered on dynamic moved object memory.
- Room/floor segmentation quality may dominate performance.

## Relevance to My Research

Good prior for hierarchical fallback when object memory is stale.

## Follow-up Questions

- Can stale instance memory trigger room-level search?
