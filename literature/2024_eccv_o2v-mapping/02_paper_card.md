# Paper Card

## Problem

Open-vocabulary 3D mapping needs online updates, local consistency, and object-level language features.

## Core Idea

Use a voxel-based open-vocabulary field with object-level language features and multi-view weighting.

## Input / Output

- Input: RGB-D observations and poses
- Output: online open-vocabulary 3D semantic field

## Method

The method combines foundation segmentation with voxel-level map updates and adaptive voxel adjustment.

## Main Claims

- O2V Field improves online open-vocabulary mapping and segmentation/localization.

## Strengths

- Strong online mapping baseline.
- Clear limitation-to-module structure.

## Limitations

- Dense/field-style representation may still be weak for human intent and object memory.

## Relevance to My Research

Use as online open-vocabulary baseline before object/graph/staleness extensions.

## Follow-up Questions

- Can task intent decide which voxels/objects receive expensive semantic updates?
