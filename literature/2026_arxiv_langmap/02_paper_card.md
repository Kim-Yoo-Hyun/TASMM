# Paper Card

## Problem

Open-vocabulary navigation benchmarks often do not evaluate goals across semantic granularity levels.

## Core Idea

Define HieraNav and LangMap, covering scene, room, region, and instance level navigation goals.

## Input / Output

- Input: natural-language goal at a semantic level
- Output: navigation behavior and success under that goal

## Method

Benchmark construction with real-world 3D indoor scans and human-verified annotations.

## Main Claims

- Hierarchical goal levels expose failures hidden by object-only navigation.
- Existing agents have substantial room for improvement under open-vocabulary hierarchical goals.

## Strengths

- Very useful for measuring whether a semantic map supports human-level abstraction.
- Separates instance, region, room, and scene goals.

## Limitations

- Benchmark paper, not a mapping method.
- Need to check data availability and simulator integration.

## Relevance to My Research

Useful evaluation target if CAND-001 includes granularity selection.

## Follow-up Questions

- Can stale memory be evaluated at instance and region levels separately?
- Does task intent select hierarchy level before object search?
