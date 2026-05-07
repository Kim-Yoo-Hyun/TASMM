# Open-Vocabulary Octree-Graph for 3D Scene Understanding

## Bibliographic Info

- Year/Venue: 2025 ICCV
- Source: https://openaccess.thecvf.com/content/ICCV2025/html/Wang_Open-Vocabulary_Octree-Graph_for_3D_Scene_Understanding_ICCV_2025_paper.html

## One-Line Contribution

Combines adaptive octree occupancy with graph relations for efficient open-vocabulary 3D scene understanding.

## Existing Limitation

Point-cloud maps are unordered, storage-heavy, and weak at occupancy and spatial relation representation for planning and complex retrieval.

## Why This Is Semantic Mapping

It redefines map storage around objects as adaptive octree graph nodes with semantic features and relation edges.

## Method / Map Representation

Chronological segment merging, instance feature aggregation, adaptive-octree object representation, and graph edges for spatial relations.

## Dataset / Benchmark / Metrics

Various datasets and tasks; semantic understanding, text retrieval, planning-relevant representation efficiency.

## Author Organization Pattern

Representation limitation, structured storage design, then multi-task experiments for versatility.

## Useful Insight

Occupancy and relations should be first-class semantic map fields.

## Failure Lesson

If graph queries work but navigation fails, traversability and action interfaces are still missing.
