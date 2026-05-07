# E003-M02 Annotation-Proxy Noise Generator

## Status

annotation_proxy_noise_ready

## 사실

- Input query rows: 294
- Input candidate rows: 1248
- Profiles: `clean_annotation_oracle_v0`, `annotation_score_jitter_v0`
- Noisy query rows: 588
- Noisy candidate rows: 2496
- Noise manifest rows: 588
- Output directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M02_annotation_proxy_noise_v0`

## Profile Summary

| Profile | Rows | Target retained | Rank changed | Target rank changed |
| --- | ---: | ---: | ---: | ---: |
| `clean_annotation_oracle_v0` | 294 | 1.0 | 0.0 | 0.0 |
| `annotation_score_jitter_v0` | 294 | 1.0 | 0.411565 | 0.159864 |

## 논문 주장

- E003-M02 supports controlled annotation-proxy score/rank noise input generation.
- E003-M02 preserves target presence, so it tests ranking robustness rather than proposal recall failure.
- E003-M02 does not support real RGB-D or open-vocabulary perception robustness.

## 에이전트 추론

- `clean_annotation_oracle_v0` is the reference condition for robustness deltas.
- `annotation_score_jitter_v0` is the first stress condition because it changes ranking without mixing in target dropout.
- E003-M03 should evaluate policy robustness on these noisy rows before adding dropout or false-positive profiles.

## 사용자 판단 필요

- None for E003-M02. Continue to E003-M03 noisy policy evaluation.

## Outputs

- `noise_manifest.jsonl`
- `noisy_query_rows.jsonl`
- `noisy_candidate_rows.jsonl`
- `coverage.json`
- `report.md`
