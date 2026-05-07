# Paper Card

## Problem

Open-vocabulary semantic mapping for real robot navigation must be online, efficient, and robust to dynamic scene changes.

## Core Idea

Use a dual-map representation: a global abstract map for high-level candidate selection and a local concrete map for precise goal reaching and dynamic update.

## Input / Output

- Input: robot observations and natural-language query
- Output: updated open-vocabulary semantic map and navigation target

## Method

The paper combines hybrid segmentation, object-level status checking, and global/local semantic map roles.

## Main Claims

- Avoiding costly 3D object merging improves online mapping efficiency.
- Global/local map decomposition supports dynamic changing scenes and language-guided navigation.

## Strengths

- Directly targets online navigation in dynamic scenes.
- Evaluates mapping and navigation, not just segmentation.

## Limitations

- Need to inspect how dynamic changes are generated and whether they cover repeated household object movement.
- It may solve engineering efficiency more than human intent modeling.

## Relevance to My Research

This is a central baseline for stale semantic memory and dynamic update.

## Follow-up Questions

- Does DualMap know when to distrust old object memory?
- Can task intent decide which objects enter local concrete verification?
