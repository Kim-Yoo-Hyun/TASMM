# Evaluation

## Dataset / Benchmark

- `LangMap` / `HieraNav`
- all 36 `HM3D-Sem` validation scenes
- scene, room, region, and instance goal levels
- 414 object categories and 18K+ navigation tasks

## Splits

Uses `HM3D-Sem` validation scenes. Exact task split should be checked before implementation.

## Metrics

- `SR`
- `SPL`
- `SeqSR`
- `SeqSR-4`
- annotation discriminability via one-to-many text-to-view matching

## Baselines

- `PSL`
- `SenseAct-Mono`
- `3D-Mem`
- `Uni-NaVid`
- `MTU3D`

## Main Results

논문 주장: existing approaches struggle across hierarchical open-vocabulary goals.

## Reproducibility Notes

Need to verify code/data release.

## Evaluation Weaknesses

- May not contain dynamic moved-object episodes.
- If used for CAND-001, dynamic perturbation or replay extension may be needed.
- Best used as static granularity sanity check, not H001 primary benchmark.
