# Evaluation

## Dataset / Benchmark

- `Replica` and `ScanNet` for open-vocabulary semantic mapping / semantic segmentation.
- `3RScan` for scene graph relationship evaluation.
- real-world scenes for practical validation.

## Splits

Reported scenes include eight `Replica` scenes, five `ScanNet` scenes, and four `3RScan` scenes. Exact list is in the paper.

## Metrics

- semantic mapping: `mIoU`, `F-mIoU`, `mAcc`
- scene graph: relationship `Recall`
- runtime

## Baselines

- `ConceptGraphs`
- `HOV-SG`
- 3DGS-based semantic mapping methods for novel-view semantic segmentation
- `OpenGS-SLAM` where applicable

## Main Results

논문 주장: OGScene3D improves incremental open-vocabulary scene understanding by combining semantic Gaussian representation, temporal memory, and progressive graph updates.

## Reproducibility Notes

Need code/data check.

## Evaluation Weaknesses

- Need to separate dynamic object movement from incremental static exploration.
- It may not evaluate human instruction following directly.
- Useful for temporal confidence design, but not the primary H001 benchmark.
