# E003-M17 Real Proposal Denominator Staging

## Status

real_proposal_denominator_staged

## 사실

- Source route: `sequence_ready_scan_bootstrap`
- Ready scan rows: 8
- Query manifest rows: 8
- Object target rows: 460
- Detector target rows: 344
- Evaluation target rows: 344
- Prompt label count: 98
- Detector target label count: 85
- Proposal schema copied: True
- Paper-table command ready: False
- Detector predictions ready: False
- Real RGB-D/open-vocabulary claim ready: False
- Docker required for M17: False
- Docker required for next detector: True
- Output directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M17_real_proposal_denominator_staging_v0`

## Scan Summary

| Scan | frames | sampled | objects | detector targets | evaluation targets |
| --- | ---: | ---: | ---: | ---: | ---: |
| `280d8ebb-6cc6-2788-9153-98959a2da801` | 536 | 60 | 66 | 51 | 51 |
| `38770ca1-86d7-27b8-8619-ab66f67d9adf` | 844 | 61 | 83 | 48 | 48 |
| `75c25975-9ca2-2844-9769-84677f46d4cf` | 129 | 43 | 38 | 33 | 33 |
| `8eabc45f-5af7-2f32-8528-640861d2a135` | 246 | 62 | 58 | 44 | 44 |
| `a0905fd9-66f7-2272-9dfb-0483fdcc54c7` | 455 | 57 | 73 | 59 | 59 |
| `c7895f27-339c-2d13-836b-c12dca280261` | 189 | 63 | 48 | 37 | 37 |
| `c7895f7c-339c-2d13-819f-3bb0b26c91f6` | 174 | 58 | 36 | 20 | 20 |
| `ddc73797-765b-241a-9e2c-097c5989baf6` | 325 | 55 | 58 | 52 | 52 |

## 논문 주장

- E003-M17 supports real RGB-D/open-vocabulary detector input staging.
- E003-M17 supports saying that sequence-ready 3RScan scans can now be passed to a Dockerized detector using a fixed manifest, prompt set, and output schema.
- E003-M17 does not support real perception robustness results because detector predictions have not been generated.

## 에이전트 추론

- This staging intentionally rebuilds the real-proposal denominator from sequence-ready scans because current E001 rescans have no sequence-ready rows.
- Object targets are split into detector targets, structural context, and generic context so prompt labels do not silently define the evaluation denominator.
- The next step should create or select the Dockerized detector scaffold before any paper-table command is considered ready.

## 사용자 판단 필요

- None for E003-M17. Next recommended unit: `E003-M18 Dockerized real-proposal detector scaffold`.

## Outputs

- `real_proposal_query_manifest.jsonl`
- `real_proposal_object_targets.jsonl`
- `scan_target_summary.jsonl`
- `prompt_set.json`
- `proposal_output_schema.json`
- `staging_decision.json`
- `coverage.json`
- `report.md`
