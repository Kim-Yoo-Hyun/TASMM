# E003-M16 Real Proposal Route Decision

## Status

real_proposal_denominator_staging_required

## 사실

- Scan gate rows: 54
- Sequence-ready scans: 8
- Proposal-alignment-ready scans: 8
- Query alignment rows: 294
- Query rows with reference sequence ready: 123
- Query rows with current rescan sequence ready: 0
- Query rows with current real RGB-D proposal ready: 0
- Pair rows with current real proposal ready: 0
- Selected route: `sequence_ready_scan_bootstrap`
- Next recommended unit: `E003-M17 real-proposal denominator staging`
- M16 Docker required: False
- Future detector Docker required: True
- Output directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M16_real_proposal_route_decision_v0`

## Proposal Source Decision

| Source | Status | Ready rows/scans | Next action |
| --- | --- | ---: | --- |
| `current_e001_rescan_rgbd_sequence` | `blocked` | 0 | stage sequence payloads for current E001 rescans or rebuild denominator |
| `current_e001_reference_sequence_only` | `insufficient_for_current_proposals` | 123 | do not use as the main real-proposal denominator |
| `sequence_ready_scan_bootstrap` | `staging_candidate` | 8 | create E003-M17 real-proposal denominator staging from sequence-ready scans and 3DSSG object ids |
| `annotation_proxy_noise_suite` | `complete_controlled_non_real` | 294 | keep as controlled table, not real perception table |

## Docker Command Plan

- Status: `planned_not_executable_until_E003_M17_staging`
- Docker image tag: `research2/real-smoke`
- Dockerfile planned path: `experiments/E003_perception_noise_expansion/docker/real_proposals/Dockerfile`
- Paper-table command ready: False
- Reason not ready: current E001 denominator has 0 current-rescan RGB-D proposal-ready rows

Planned command:

```bash
docker run --gpus all --rm -v /home/yoohyun/research2/local_dataset:/data:ro -v /home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M17_real_proposal_denominator_staging_v0:/inputs:ro -v /home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M18_dockerized_real_proposals_v0:/outputs research2/real-smoke python /workspace/tools/run_rgbd_ov_proposals.py --manifest /inputs/real_proposal_query_manifest.jsonl --schema /inputs/proposal_output_schema.json --output /outputs/real_proposals.jsonl --detector open_vocab_rgbd_detector_v0 --prompt-set /inputs/prompt_set.json --seed 101
```

## 논문 주장

- E003-M16 supports saying that the controlled E003 table is ready, but real proposal evaluation is not yet ready.
- E003-M16 supports selecting `sequence_ready_scan_bootstrap` as the next staging route because current E001 rescans have 0 sequence-ready rows.
- E003-M16 supports a concrete proposal output schema and Docker command plan for later real detector execution.
- E003-M16 does not support real RGB-D/open-vocabulary robustness results yet.

## 에이전트 추론

- The current E001 denominator cannot be upgraded to real current-scene proposals without staging current rescan RGB-D frames.
- Reference scan sequences are useful for inspection, but current object proposal recall must be measured on the rescan/current scene.
- The most direct top-tier strengthening path is E003-M17 denominator staging followed by a Dockerized detector smoke run.

## 사용자 판단 필요

- None for route decision. Next is `E003-M17 real-proposal denominator staging` unless redirected to E004 task-context memory trust.

## Outputs

- `proposal_source_rows.jsonl`
- `scan_alignment_gate_rows.jsonl`
- `query_alignment_gate_rows.jsonl`
- `pair_alignment_gate_rows.jsonl`
- `proposal_output_schema.json`
- `docker_command_plan.json`
- `route_decision.json`
- `coverage.json`
- `report.md`
