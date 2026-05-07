# Evaluation

## Dataset / Benchmark

- `ScanNet` and `Replica` for open-vocabulary 3D semantic segmentation and efficiency.
- `HM3D` scenes `00829`, `00848`, `00880` for object navigation.
- Added `YCB` objects to increase object diversity.
- Dynamic navigation variants in `Habitat Simulator`: `In-anchor relocation` and `Cross-anchor relocation`.
- Real-world object navigation with wheeled and quadruped platforms.

## Splits

Paper uses selected `ScanNet`, `Replica`, and three `HM3D` scenes. Full split should be checked against the appendix before implementation.

## Metrics

- semantic segmentation: `mIoU`, `F-mIoU`, `mAcc`
- object density: `ODR`
- efficiency: average memory, peak memory, `TPF`
- navigation: `SR`
- dynamic navigation: success within three attempts

## Baselines

- `ConceptGraphs`
- `HOV-SG`
- candidate-selection ablation: `Random Pick`, `Based on Ma`, `Based on M'a`

## Main Results

논문 주장: DualMap achieves strong performance in 3D open-vocabulary segmentation, efficient scene mapping, and online language-guided navigation in simulation and real-world scenarios.

## Reproducibility Notes

Need code/config availability check.

## Evaluation Weaknesses

- Need to isolate stale object false-positive rate, not only overall navigation success.
- Need to know if moved objects are instance-specific or category-level.
- Dynamic setup is useful for CAND-001, but CAND-001 needs its own stale-memory metrics.
