# Schedule

Last updated: 2026-05-11

이 문서는 H001 main experiment implementation을 top-tier submission path로 확장하기 위한 실행 순서를 관리한다. 세부 실험 결과는 `experiments/`에 기록하고, 이 문서는 단계, gate, baseline 확장 방향만 관리한다.

## Current Direction

사실:

- Active direction: `CAND-001` / `Intent- and Staleness-Aware Semantic Mapping`.
- Active hypothesis: `H001_stale-object-memory`.
- Current stage: main experiment implementation.
- Final paper target: Direction B `Task-Aware Dynamic Semantic Mapping for Open-Vocabulary Search and Navigation`.
- Current path: use Direction A `Task-Conditioned Stale Semantic Memory` as the core method/backbone, then expand through real proposal/search bridge, external baselines, and search/navigation metrics.
- Current E003 status: `E003-M59_direct_current_rescan_detector_launch_v0` launched; the direct detector/evaluation bridge run is active in tmux session `e003_m59_direct_bridge`.
- E003-M48 selected backend contract: `grounded_sam_mask_backproject_v0`.
- E003-M50 selected route: `do_not_scale_grounded_sam_yet`.
- E003-M57 launched tmux session `e003_m56_sequence_stage` for the 4 current-rescan sequence payloads; the session has ended and verifier status is ready.

에이전트 추론:

- Current core direction is aligned with recent work on open-vocabulary semantic mapping, 3D scene memory, task-driven mapping, and embodied navigation.
- Direction B is the correct final top-tier target, but the immediate implementation should remain focused on Direction A's memory-decision core to avoid an unfocused system paper.
- Top-tier competitiveness requires moving beyond `3RScan` / `3DSSG` proxy evidence into stronger external baselines and downstream search/navigation evaluation.

## Top-Tier Target Claim

논문 주장 후보:

- `Task-Conditioned Stale Semantic Memory Update` improves dynamic object search/navigation by modulating memory trust, re-observation priority, and candidate visit order under object movement and perception noise.
- The method should improve `ExpectedSearchCost`, `SR`, `SPL` or `AttemptSPL`, stale old-location false positives, and proposal-aware search robustness.

논문 주장:

- Final claim should include real RGB-D / open-vocabulary proposal robustness and a search/navigation bridge, not only annotation-proxy stale memory behavior.
- Direction B is the final target claim family; Direction A is the core method claim that must survive ablation and bridge tests.

## Schedule

| Phase | Goal | Main output | Gate |
| --- | --- | --- | --- |
| E003-M39 | Temporal/spatial support instrumentation | Complete: support fields, runner insertion point, and verification plan fixed | No long rerun until schema and verification command are fixed |
| E003-M40 | Proposal-quality runner smoke | Complete: support fields implemented and short Docker smoke passed | Support fields must appear in validated proposal output |
| E003-M41 | Support-aware selection policy gate | Complete: selected `confidence_sqrt_depth_support_temporal_v0` | No long rerun until policy contract and success checks are fixed |
| E003-M42 | Support-aware selection runner smoke | Complete: selected score mode implemented and short Docker smoke passed | Validator must pass and support-aware score mode must be recorded |
| E003-M43 | Support-aware scaled rerun route gate | Complete: selected `pre_cap_candidate_pool_export_then_offline_replay_v0` | No immediate long rerun because existing artifacts cannot support score ablation |
| E003-M44 | Pre-cap candidate-pool export and offline replay harness | Complete: exported 629 support-instrumented candidates and reproduced runner selection offline | Replay reproduced runner selected stable-candidate set |
| E003-M45 | Scaled candidate-pool export and support-aware replay | Complete: 60,435 candidate pool rows, replay ready, frozen verdict `fail_redesign` | Support-aware score lost targets, added false positives, and failed hard/weak criteria |
| E003-M46 | Support-aware redesign or external proposal baseline gate | Complete: 12 local score policies swept, hard pass 0, weak positive 0 | Selected `external_proposal_baseline_gate_first` |
| E003-M47 | External proposal/mapping baseline feasibility gate | Complete: selected `Grounded-SAM` over `OpenMask3D`, `ConceptGraphs`, `OVIR-3D`, `HOV-SG` | First route must diagnose whether box-depth projection is the current proposal bottleneck |
| E003-M48 | `Grounded-SAM` mask-backprojection contract | Complete: `grounded_sam_mask_backproject_v0` input/output contract, blocked inputs, optional mask fields, and long-running job policy fixed | No result claim; implementation smoke remains next |
| E003-M49 | `Grounded-SAM` Docker/model smoke | Complete: mask-depth rows emitted, validator passed, M21 matcher passed | Implementation smoke only |
| E003-M50 | Same-subset bbox-depth vs mask-depth comparison gate | Complete: bbox-depth beat mask-depth on matched targets, precision, recall, and centroid error | Do not scale `Grounded-SAM` yet |
| E003-M51 | Post-M50 route decision | Complete: selected artifact-local `Grounded-SAM` mask failure analysis | Must avoid spending compute on a route with negative same-subset evidence |
| E003-M52 | `Grounded-SAM` mask failure analysis | Complete: target loss is mask projection dropout and centroid worsening is match-set composition | Do not scale current `Grounded-SAM` route as-is |
| E003-M53 | Bbox-depth continuation and failure-boundary repair gate | Complete: selected search-critical bbox-depth failure-boundary audit | Must preserve the stronger current route while keeping external baseline expansion open |
| E003-M54 | Search-critical bbox-depth failure-boundary audit | Complete: exact current query-instance joins 0, label-level bridge risk identified | Current detector failures cannot yet be used as direct search-decision evidence |
| E003-M55 | Dynamic-pair-aligned real-proposal bridge gate | Complete: selected search-failure current-rescan staging first | Must stage current-rescan sequence payloads before detector output can be evaluated against E001/E002 rows |
| E003-M56 | Current-rescan sequence payload staging plan | Complete: fixed target scan list, command, output paths, logs, and verification for 4 current rescans | Use long-running/background task rule for download/decompression |
| E003-M57 | Current-rescan sequence staging background job | Complete: launched M56 command in `tmux`, recorded job status/log path, and verified 4 / 4 payloads ready | Direct detector bridge design can start |
| E003-M58 | Direct current-rescan detector/evaluation bridge design | Complete: 7 query rows, 5 unique bridge targets, 4 scans, `chair`/`pillow` prompt set, M59 command plan | No real RGB-D search claim until detector bridge output is evaluated |
| E003-M59 | Direct current-rescan detector bridge Docker run | Running: launched in `tmux` with timestamped log and expected files/verification command recorded | Completion verification required before E003-M60 |
| E003-M60 | Direct current-rescan query-level bridge evaluation | Join M59 detector output with M58 query rows and report query-level bridge metrics | No real RGB-D search claim until query-level evaluation passes |
| E004-M01 | Task-context memory trust contract | Fix task context fields for memory trust / re-observation decision | Natural language parser remains adapter, not main claim |
| E004-M02 | Task-conditioned re-observation/search policy | Evaluate task-conditioned policy under stale memory + proposal noise | Must beat static memory, fixed top-k, and detector-confidence-first |
| E005-M01 | External benchmark/baseline integration | Add at least one mapping baseline and one navigation/search baseline | Paper-table claim blocked until external comparison exists |

## External Baseline Expansion

Top-tier submission needs external baselines beyond current internal policies.

### Open-Vocabulary Mapping Baseline

Candidate baselines:

- `ConceptGraphs`
- `HOV-SG`
- `Open3DSG` if implementation/data compatibility is practical

Purpose:

- Compare against map construction and open-vocabulary object/relationship representation baselines.
- Show whether stale-memory decision logic adds value beyond stronger open-vocabulary map representations.

### Dynamic Semantic Mapping Baseline

Candidate baselines:

- `DualMap` or a compatible DualMap-style dynamic mapping baseline

Purpose:

- Compare against online open-vocabulary mapping for dynamically changing scenes.
- Clarify whether the contribution is dynamic map update, stale-memory trust, or downstream search decision.

### Navigation/Search Baseline

Candidate baselines:

- `VLFM`
- `HM3D-OVON` baseline
- `GOAT-Bench` modular baseline

Purpose:

- Connect semantic memory to downstream `SR`, `SPL`, `ExpectedSearchCost`, and lifelong/multimodal navigation metrics.
- Avoid limiting the paper to proxy object retrieval.

### Scene Memory Baseline

Candidate baseline:

- `3D-Mem`

Purpose:

- Compare against recent 3D scene memory and memory-management approaches for embodied exploration/reasoning.
- Position H001 as task-conditioned stale semantic memory rather than generic scene memory.

### Detector/Proposal Baseline

Candidate baselines:

- `Grounded-SAM`
- `OpenMask3D`
- `OVIR-3D`
- `ConceptGraphs` proposal path

Requirement:

- Add at least 1-2 proposal baselines beyond `GroundingDINO`.

Purpose:

- Prevent the real RGB-D/open-vocabulary claim from depending on one detector backend.
- Separate detector/proposal quality from stale-memory update behavior.

## Dataset Plan

사실:

- `3RScan` / `3DSSG` remains the core dataset for object movement, rescan alignment, and stale semantic memory.
- Current 8-scan real-proposal artifact is too small for reliable label-stratified split learning.

에이전트 추론:

- Keep `3RScan` / `3DSSG` as the primary dynamic-memory benchmark.
- Add `HM3D-OVON` or `GOAT-Bench` when the claim shifts to navigation/search metrics.
- Consider `OpenLex3D` only if open-vocabulary representation quality itself becomes a central claim.

## Immediate Next Actions

- E003-M59: verify completion after tmux exits using expected files, validator coverage, and matching coverage.
- E003-M60: if M59 output is valid, run direct current-rescan query-level bridge evaluation.
- Keep `OpenMask3D` as the later 3D instance proposal baseline candidate after the direct bridge denominator is staged/verified or explicitly blocked.
- Keep `Open3DSG`, `ConceptGraphs`, and `HOV-SG` for later map/scene-graph/navigation baseline expansion, not the immediate proposal-geometry diagnosis.

## Claim Boundary

사실:

- Current real RGB-D/open-vocabulary claim readiness is false.
- Current real navigation `SR` / `SPL` claim readiness is false.
- Current internal evidence supports controlled/proxy behavior, not final top-tier paper evidence.
- E003-M39 selects `docker_runner_pre_consolidation_support_evidence_v0` and rejects final-artifact post-processing as insufficient.
- E003-M39 fixes insertion point `select_cap_aware_label_balanced_candidates.after_cleaned_before_grouped`.
- E003-M40 status is `temporal_spatial_support_runner_smoke_ready`.
- E003-M40 attaches support evidence to 95 / 95 selected rows with validator errors/warnings 0 / 0.
- E003-M40 keeps real RGB-D/open-vocabulary claim readiness false because it is a short smoke, not heldout policy evidence.
- E003-M41 status is `support_aware_selection_policy_gate_ready`.
- E003-M41 selects `confidence_sqrt_depth_support_temporal_v0`.
- E003-M41 keeps hard support filter false, support cap changes false, and long rerun readiness false.
- E003-M42 status is `support_aware_selection_runner_smoke_ready`.
- E003-M42 validator errors/warnings are 0 / 0.
- E003-M42 matched/false-positive/precision delta vs E003-M40 is 0 / 0 / 0.0.
- E003-M43 status is `support_aware_scaled_rerun_route_gate_ready`.
- E003-M43 selected route is `pre_cap_candidate_pool_export_then_offline_replay_v0`.
- E003-M43 M42 vs M40 common selected rows are 94 / 95, selected symmetric difference is 2 rows, pre-cap rank changed common rows are 68, and selection-score changed common rows are 89.
- E003-M43 marks existing candidate-pool replay available false and immediate support-aware long rerun recommended false.
- E003-M44 status is `pre_cap_candidate_pool_replay_smoke_ready`.
- E003-M44 exported 629 pre-cap candidate rows with support policy on 629 / 629 rows.
- E003-M44 reproduced runner selection for `confidence_sqrt_depth_support_temporal_v0`: runner selected rows 95, offline replay rows 95, ordered/set reproduction true / true.
- E003-M45 tmux session `e003_m45_scaled_pool` completed with log `logs/20260508_155219_e003_m45_scaled_candidate_pool_export_replay_tmux.log`.
- E003-M45 verification status is `scaled_candidate_pool_replay_ready`, but frozen contract verdict is `fail_redesign`.
- E003-M45 support-aware score result is 196 matched targets, 3211 false positives, and proposal precision 0.057529, worse than the M33 confidence baseline 204 / 3210 / 0.059754.
- E003-M46 status is `score_redesign_or_external_gate_ready`.
- E003-M46 swept 12 bounded score policies and found hard pass 0, weak positive 0.
- E003-M46 selected `external_proposal_baseline_gate_first` because simple support-aware score redesign did not improve the M45 failure.
- E003-M47 status is `external_baseline_feasibility_gate_ready`.
- E003-M47 selected `Grounded-SAM` because it is the smallest controlled change from the current `GroundingDINO` RGB-D backprojection backend.
- `OpenMask3D` remains the stronger 3D instance segmentation baseline candidate, but its scene-format/checkpoint/MinkowskiEngine burden makes it a second route.
- `ConceptGraphs` and `HOV-SG` remain mapping/navigation baselines, not first proposal-failure diagnosis routes.
- E003-M48 status is `grounded_sam_contract_ready`.
- E003-M48 preserves the existing `real_proposal_prediction_jsonl_v0` required fields and adds 9 optional mask diagnostic fields.
- E003-M48 did not execute Docker/model inference and does not make a new result claim.
- E003-M49 `Grounded-SAM` Docker/model smoke emitted 24 mask-depth proposal rows and passed schema/matching smoke.
- E003-M50 same-subset comparison found bbox-depth 31 proposals / 2 matched targets / 29 false positives / precision 0.064516, while mask-depth had 24 / 1 / 23 / 0.041667.
- E003-M51 selected artifact-local mask failure analysis before any scaled `Grounded-SAM` rerun or `OpenMask3D` feasibility.
- E003-M52 found common candidate rows 24, bbox-only candidate rows 7, mask-only candidate rows 0, and skipped mask projection rows 16.
- E003-M52 lost-by-mask target count is 1, label `plant`; common same-target match-distance delta mask minus bbox is -0.018907m.
- E003-M52 diagnoses the aggregate centroid worsening as match-set composition after an easy bbox-depth target dropout, not common-target centroid degradation.
- E003-M52 keeps scaled `Grounded-SAM` recommended false and selects `E003-M53 bbox-depth continuation and failure-boundary repair gate`.
- E003-M53 status is `bbox_continuation_repair_gate_ready`.
- E003-M53 selected route is `search_critical_bbox_failure_boundary_first`.
- E003-M53 route scores: search-critical bbox boundary 46, deployable bbox suppression repair 30, `OpenMask3D` feasibility 27, `ConceptGraphs` mapping 19, `Open3DSG` mapping 16, `HOV-SG` navigation/mapping 10.
- E003-M53 keeps `OpenMask3D` as a later external 3D instance proposal baseline and keeps `Open3DSG` / `ConceptGraphs` / `HOV-SG` for later map/scene-graph/navigation baseline expansion.
- E003-M54 status is `search_critical_bbox_failure_boundary_ready`.
- E003-M54 exact current query-instance joins are 0 because M33/M45 detector-ready scans do not overlap with E001 current `rescan_id` rows.
- E003-M54 reference-memory-only joins are 120, label overlap count is 21, and existing E001/E002 search failures with label-level detector risk are 7.
- E003-M54 strongest bridge labels are `pillow` and `chair`; these remain label-level risks, not direct real RGB-D search-failure proof.
- E003-M55 status is `dynamic_pair_bridge_gate_ready`.
- E003-M55 selected route is `stage_search_failure_current_rescans_first`.
- E003-M55 search-failure current rescans are 4; semantic triplet ready is 4 / 4 and sequence-ready is 0 / 4.
- E003-M55 priority scans are `5555106a-36f1-29c0-8913-df1ba3c3cfd5`, `4731976c-f9f7-2a1a-95cc-31c4d1751d0b`, `ddc73795-765b-241a-9c5d-b97744afe077`, and `10b17957-3938-2467-88a5-9e9254930dad`.
- E003-M56 status is `current_rescan_sequence_staging_plan_ready`.
- E003-M56 target scan count is 4, prelaunch sequence-ready count is 0 / 4, and download-required count is 4 / 4.
- E003-M56 records a resumable `wget -c` staging script and `verify_m56_sequence_payloads.py --require-ready` verification command.
- E003-M57 status is `sequence_staging_job_launched`.
- E003-M57 background job status was `running` at launch in tmux session `e003_m56_sequence_stage`; the session later ended.
- E003-M57 log path is `logs/20260510_170443_e003_m56_sequence_staging.log`.
- E003-M57 verification status is `sequence_payloads_ready`, ready rows 4 / 4.
- E003-M57 does not create a paper result claim; it only prepares the direct current-rescan detector bridge denominator.
- E003-M58 status is `direct_current_rescan_bridge_design_ready`.
- E003-M58 links 7 search-failure query rows, 5 unique bridge targets, 4 current rescans, 29 same-label object targets, and 93 sampled frames for the next detector run.
- E003-M58 detector run executed is false and real RGB-D/open-vocabulary search claim readiness remains false.
- E003-M59 status is `direct_current_rescan_detector_job_launched`.
- E003-M59 background job status is `running`.
- E003-M59 tmux session is `e003_m59_direct_bridge`.
- E003-M59 log path is `logs/20260511_114356_e003_m59_direct_current_rescan_detector_run.log`.
- E003-M59 target scans are 4 and bridge query rows are 7.
- E003-M59 does not create a paper result claim; detector output and query-level bridge metrics are still pending.

논문 주장:

- Do not claim deployable real RGB-D/open-vocabulary robustness until external baselines and heldout-transfer evidence are added.
- Do not claim real navigation `SR` / `SPL` until a simulator, navmesh, or trajectory execution source is integrated.
