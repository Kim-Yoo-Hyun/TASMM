# E003-M58 Direct Current-Rescan Detector Bridge Design

## Status

direct_current_rescan_bridge_design_ready

## 사실

- Direct bridge query rows: 7
- Direct bridge base rows: 5
- Direct bridge scans: 4
- Target labels: ['chair', 'pillow']
- Linked bridge query target uids: 5 / 5
- Object target rows: 29
- Same-label distractor object rows: 24
- Prompt label count: 2
- Sampled frame count for next detector run: 93
- Detector run executed: False
- Paper-table command ready: False
- Real RGB-D/open-vocabulary search claim ready: False

## Scan Summary

| Scan | labels | query rows | base rows | bridge targets | distractors | sampled frames |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `10b17957-3938-2467-88a5-9e9254930dad` | `pillow` | 1 | 1 | 1 | 4 | 22 |
| `4731976c-f9f7-2a1a-95cc-31c4d1751d0b` | `pillow` | 2 | 2 | 2 | 3 | 24 |
| `5555106a-36f1-29c0-8913-df1ba3c3cfd5` | `chair` | 3 | 1 | 1 | 11 | 23 |
| `ddc73795-765b-241a-9c5d-b97744afe077` | `pillow` | 1 | 1 | 1 | 6 | 24 |

## 논문 주장

- E003-M58 supports saying that the direct current-rescan bridge denominator is ready.
- E003-M58 does not support a real RGB-D/open-vocabulary search result because no detector run or query-level bridge evaluation has been executed.
- E003-M58 preserves E001/E002 dynamic-pair current-rescan identity, which is the missing causality link from E003-M54.

## 에이전트 추론

- The next detector run should use this artifact as the `--m17-dir` input so the existing Docker runner and M21 matcher can be reused without schema drift.
- The first bridge uses only `chair` and `pillow` prompts because those are the labels with existing E001/E002 search failures and M33 detector risk.
- Query-level bridge evaluation should be a separate step after detector output exists; otherwise detector matching and search-decision metrics would be mixed.

## 사용자 판단 필요

- None. The next unit should execute or launch the recorded detector command if compute is available.

## Next Command Plan

- Output dir: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M59_direct_current_rescan_detector_run_v0`
- Next unit: `E003-M60 direct current-rescan query-level bridge evaluation`
- Exact command: `python experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py --m17-dir /home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M58_direct_current_rescan_bridge_design_v0 --out-dir /home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M59_direct_current_rescan_detector_run_v0 --max-scans 4 --max-frames-per-scan 24 --max-labels 8 --max-predictions 4000 --max-predictions-per-frame 60 --threshold 0.08 --text-threshold 0.08 --candidate-selection-policy cap_aware_label_balanced_ranking_v0 --selection-score-mode confidence --pre-cap-per-scan-label-cap 24 --pre-cap-spatial-consolidation-radius-m 0.5 --raw-candidate-collection-cap 200000 --export-pre-cap-candidate-pool --build --docker-sudo --sudo-password-stdin`
