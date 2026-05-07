# E003-M15 Controlled Perception Claim Summary

## Status

controlled_perception_claim_summary_ready

## 사실

- Profile summary rows: 5
- Claim evidence rows: 8
- Controlled claim ready: True
- Real RGB-D/open-vocabulary claim ready: False
- Real navigation claim ready: False
- Main method-signal subset: `significant_moved|routine_fetch`
- Combined `task_conditioned_budget_v0` identity `SR`: 0.212121
- Combined `reachable_first_task_conditioned_budget_v0` identity `SR`: 0.606061
- Reachable-first minus task identity `SR` delta: 0.393939
- Reachable-first gain/loss rows: 13 / 0
- Docker required: False
- Output directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M15_controlled_perception_claim_summary_v0`

## Profile Evidence

| Profile | Boundary | rows | hard rows | main signal | limitation |
| --- | --- | ---: | ---: | --- | --- |
| `annotation_score_jitter_v0` | `E003-M04_robustness_failure_analysis_v0` | None | 29 | `task_conditioned_budget_v0` significant routine proxy `SR` delta -0.090909 | target-drop and real detector proposal recall are absent |
| `annotation_proposal_dropout_v0` | `E003-M07_dropout_failure_boundary_v0` | 7938 | 294 | target-dropped significant routine `SR` 0.0 | target-dropped rows are proposal-recall ceiling cases |
| `annotation_false_positive_v0` | `E003-M09_false_positive_failure_boundary_v0` | 7938 | 231 | target-pushed task/reachable `SR` 0.0 / 0.428571 | no real detector hallucinations or same-label detector false positives |
| `annotation_centroid_jitter_v0` | `E003-M11_centroid_jitter_failure_boundary_v0` | 7938 | 173 | threshold identity/localization `SR` 1.0 / 0.0 | grid/path costs are not recomputed after centroid perturbation |
| `annotation_combined_moderate_v0` | `E003-M14_combined_noise_failure_boundary_v0` | 7938 | 521 | combined task/reachable identity `SR` 0.212121 / 0.606061 | not real RGB-D/open-vocabulary detector output and not real navigation |

## 논문 주장

- Under controlled annotation-proxy perception/proposal noise, H001 can separate proposal-recall, distractor rank/budget, and centroid-localization failures, and reachable-first ordering mitigates combined distractor/rank-budget damage in significant moved routine-fetch rows.
- E003 can be written as a controlled annotation-proxy robustness suite, not as a real RGB-D/open-vocabulary perception result.
- Target-dropped, false-positive rank/budget, and centroid-localization failures should remain separate denominators in paper tables.
- `reachable_first_task_conditioned_budget_v0` is the current strongest method signal under false-positive and combined stress.

## Claim Ledger

- `C-E003-001` [supported_controlled_annotation_proxy]: E003 provides a controlled annotation-proxy perception/proposal-noise suite for H001 stale semantic-memory search.
- `C-E003-002` [supported_with_boundary]: Target-dropped rows should be reported as proposal-recall ceilings rather than recoverable memory-policy failures.
- `C-E003-003` [supported_subset]: `reachable_first_task_conditioned_budget_v0` mitigates distractor/rank-budget failures in significant moved `routine_fetch` under false-positive and combined stress.
- `C-E003-004` [supported_controlled_annotation_proxy]: Identity retrieval and spatial localization must be reported separately under centroid noise.
- `C-E003-005` [weakened_not_main_claim]: `task_conditioned_budget_v0` alone is robust under all perception-like noise.
- `C-E003-006` [unsupported_blocked]: H001 is robust to real RGB-D or open-vocabulary detector outputs.
- `C-E003-007` [unsupported_blocked]: E003 reports real navigation `SR` / `SPL` or deployable search-policy performance.
- `C-E003-008` [unsupported_blocked]: E003 evaluates natural-language intention understanding.

## 에이전트 추론

- Combined stress is the most informative current evidence: `task_conditioned_budget_v0` drops to 0.212121 identity `SR`, while `reachable_first_task_conditioned_budget_v0` reaches 0.606061.
- False-positive target-pushed rows show the same pattern: task-conditioned `SR` 0.0 vs reachable-first `SR` 0.428571.
- Centroid jitter requires a separate localization metric because threshold-exceeded rows have identity `SR` 1.0 and localization `SR` 0.0.
- For top-tier positioning, this summary is necessary but not sufficient: a real proposal route is still needed before claiming real perception robustness.

## 사용자 판단 필요

- Next recommended unit: `E003-M16 Dockerized real-proposal route decision`.
- 사용자 판단이 필요한 지점은 real RGB-D/open-vocabulary proposal route를 바로 시작할지, 또는 E004 task-context memory trust로 이동하기 전에 E003 real-proposal gate를 먼저 여는지다.

## Real Proposal Promotion Gate

- Status: `controlled_claim_ready_real_proposal_blocked`
- Paper controlled table readiness: `ready_as_controlled_stress_table`
- Real perception table readiness: `blocked`
- Real navigation table readiness: `blocked`

Minimum unblock requirements:
- Dockerfile or Docker image tag for detector/open-vocabulary proposal generation
- exact mounted dataset path and output path
- RGB-D frame, depth, pose, and scan-alignment route for the selected query denominator
- proposal output schema with label, confidence, mask or point support, centroid, and source frame ids
- matching/evaluation schema from proposals to 3DSSG object ids
- proposal recall, false-positive, localization-error, and stale-memory policy metrics
- seed/config record for detector thresholds and text prompts

## Outputs

- `profile_summary_rows.jsonl`
- `claim_evidence_rows.jsonl`
- `promotion_gate.json`
- `claim_summary.json`
- `coverage.json`
- `report.md`
