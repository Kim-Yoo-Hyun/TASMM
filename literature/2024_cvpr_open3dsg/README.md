# Open3DSG: Open-Vocabulary 3D Scene Graphs from Point Clouds with Queryable Objects and Open-Set Relationships

## Bibliographic Info

- Year/Venue: 2024 CVPR
- Source: https://openaccess.thecvf.com/content/CVPR2024/html/Koch_Open3DSG_Open-Vocabulary_3D_Scene_Graphs_from_Point_Clouds_with_Queryable_CVPR_2024_paper.html

## One-Line Contribution

Predicts 3D scene graphs in an open world without fixed object and relationship labels.

## Existing Limitation

Traditional 3D scene graph prediction depends on labeled datasets with closed object classes and fixed relationship categories.

## Why This Is Semantic Mapping

It converts a point cloud into a queryable semantic relation map where object classes and inter-object relations can be open-set.

## Method / Map Representation

Co-embeds 3D scene graph backbone features with 2D VLM feature spaces and uses grounded LLM context for relationship prediction.

## Dataset / Benchmark / Metrics

3D scene graph prediction, open-vocabulary object class prediction, and open-set relationship prediction.

## Author Organization Pattern

The paper first attacks label-space closure, then shows zero-shot queryability for both nodes and edges.

## Useful Insight

Open-vocabulary mapping should handle relationships, not just categories.

## Failure Lesson

If relationships are noisy, downstream human instruction grounding will fail even when objects are correctly labeled.
