# Paper Card

## Problem

Dense per-point language feature maps are hard to query for planning and do not directly expose object relations.

## Core Idea

Build an open-vocabulary 3D scene graph from posed RGB-D images, with object nodes and relation/caption information.

## Input / Output

- Input: posed RGB-D sequence
- Output: open-vocabulary object-centric 3D scene graph

## Method

Foundation models segment and describe 2D observations; multi-view association fuses them into 3D objects and graph structure.

## Main Claims

- Open-vocabulary 3D scene graphs can support language queries, localization, and planning.

## Strengths

- Strong representation argument.
- Good writing model for "map as interface between perception and planning."

## Limitations

- Mostly assumes posed RGB-D and relatively static scenes.
- Dynamic stale memory is not the central contribution.

## Relevance to My Research

ConceptGraphs is a baseline representation for object-centric semantic maps.

## Follow-up Questions

- How should object nodes store temporal trust?
- Can graph edges encode "needs verification" status?
