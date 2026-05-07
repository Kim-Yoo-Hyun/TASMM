# E003-M25 Visibility Prompt Rerun Gate

## Status

visibility_prompt_rerun_gate_ready

## 사실

- M17 staged scans: 8
- Current max labels: 12
- Expanded max labels: 32
- Max target label count: 30
- Current active eval target rows: 239
- Expanded active eval target rows: 344
- Prompt coverage gain rows: 105
- M24 scan eval target rows: 51
- M24 active prompt target rows: 32
- M24 depth-consistent visible-proxy target rows: 5
- Primary calibration policy: `m23_full_match_preserving_v0`
- Pilot Docker rerun max scans: 2
- Pilot Docker rerun max frames per scan: 12
- Pilot Docker rerun max predictions per frame: 60
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M25 supports fixing the rerun contract for prompt-expanded, visibility-aware real detector evaluation.
- E003-M25 does not support real RGB-D/open-vocabulary robustness because it does not execute the rerun.

## 에이전트 추론

- The next Docker run should expand the prompt cap before interpreting detector recall.
- The primary calibration should preserve M22 matched targets while the visibility-aware denominator is still diagnostic.
- The selected M23 precision-maximizing config should stay secondary because it drops matched targets.

## 사용자 판단 필요

- None for E003-M25. Next is executing the prompt-expanded Docker rerun.
