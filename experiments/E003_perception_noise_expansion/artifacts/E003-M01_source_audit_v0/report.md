# E003-M01 Source Audit

## Status

source_audit_ready

## 사실

- Query rows: 294
- Candidate rows: 1248
- Annotation-proxy noise ready rows: 294
- RGB-D sequence available query rows: 0
- E003 RGB-D ready rows: 0
- E003 open-vocabulary ready rows: 0
- Local sequence scan count: 8
- Ready pair sequence-ready count: 0
- Open-vocabulary hint count: 0
- E002-M09 target-reachable eval rows: 267
- Output directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M01_source_audit_v0`

## First Executable Plan

- First unit: `E003-M02_annotation_proxy_noise_generator_v0`
- Command: `python experiments/E003_perception_noise_expansion/tools/build_noise_inputs.py`
- Reference profile: `clean_annotation_oracle_v0`
- First stress profile: `annotation_score_jitter_v0`
- Ready rows: 294

## 논문 주장

- E003-M01 supports starting with controlled annotation-proxy proposal noise.
- E003-M01 does not support real RGB-D or open-vocabulary perception robustness.
- Real perception claims remain blocked until aligned detector/proposal outputs are generated.

## 에이전트 추론

- The first executable profile should preserve target presence and perturb ranking first, because this isolates memory-update robustness from detector recall failure.
- Proposal dropout, false positives, centroid jitter, and combined noise should follow after the clean and score-jitter path is executable.
- Local sequence payloads exist in the dataset, but they are not connected to the current E001 query denominator.

## 사용자 판단 필요

- None for E003-M01. Continue to E003-M02 annotation-proxy noise generator.

## Outputs

- `source_audit_rows.jsonl`
- `pair_readiness_rows.jsonl`
- `noise_plan.json`
- `coverage.json`
- `report.md`
