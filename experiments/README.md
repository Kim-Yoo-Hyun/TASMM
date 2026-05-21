# Experiments

Updated: 2026-05-21

이 폴더는 main experiment 구현과 내용 기록을 관리한다. 작성 규칙은 `docs/experiments.md`를 따른다.

- Current report: [report.md](report.md)

## Status

Main experiment implementation stage has started. E001-M01 through E001-M05, E002-M01 through E002-M09, E003-M00 through E003-M75, E004-M01 through E004-M05, and E005-M01 through E005-M58 are complete/verified with constraints. E005-M59 `Open3DSG` object-candidate export smoke was launched and failed on CUDA OOM while loading `InstructBLIP`; the selected repair is a lower-memory object-only patch plus a 24GB GPU preflight. E003 has Dockerized real-detector diagnostics and expanded direct current-rescan metrics for 96 query rows over 4 RGB-D-ready current rescans. E004 evaluates `task_context_memory_trust_reobserve_v0` and supports the memory-trust decision claim with limited task-context-specific strength. E005 selected `DualMap` first, then moved to `ConceptGraphs` after faithful `DualMap` object-map outputs were missing. `ConceptGraphs` now has full 9-scan heldout query-level conversion: strict bbox top5 114 / 195 = 0.584615, relaxed bbox 1m top3 144 / 195 = 0.738462. H001 replay on the same `M38` contract gives 172 / 195 = 0.882051. E005-M56 fixes the robustness denominator split and audits `/home/yoohyun/research/local_dataset/Open3DSG_staged` read-only as the next external map/scene-graph baseline route. E005-M57 stores derived schema/contract outputs under `local_dataset/Open3DSG_bridge/`; E005-M58 fixes the object-candidate export schema, read-only Docker command contract, and verifier. E005-M59 used tmux session `e005_m59_open3dsg_object_export`, log `logs/20260521_044206_e005_m59_open3dsg_object_export.log`, and output path `local_dataset/Open3DSG_bridge/E005-M59_object_candidate_export_smoke_v0/`. As of 2026-05-21 04:59 KST, candidate rows are not written, latest GPU free memory is 16,839 MiB, and `Open3DSG` still cannot be used as a query-level object-search baseline. Final real RGB-D/open-vocabulary robustness and real navigation `SR` / `SPL` remain blocked.

## Active Experiment

| ID | Status | Folder | Next action |
| --- | --- | --- | --- |
| E001 | M01-M05 artifacts ready | [E001_semantic_pair_dynamic_search_proxy](E001_semantic_pair_dynamic_search_proxy/README.md) | Input to E002 |
| E002 | M01-M09 path-cost artifacts ready | [E002_path_cost_bridge](E002_path_cost_bridge/README.md) | Input to E003 |
| E003 | M00-M75 query bridge ready | [E003_perception_noise_expansion](E003_perception_noise_expansion/README.md) | Input to E004 |
| E004 | M01-M05 ready with constraints | [E004_task_context_memory_trust](E004_task_context_memory_trust/README.md) | Input to E005 |
| E005 | M01-M58 ready with constraints; M59 lower-memory repair ready | [E005_external_baseline_transition](E005_external_baseline_transition/README.md) | Relaunch E005-M59 when GPU free memory is >= 24GB |

## 사실

- Active hypothesis: `hypothesis/CAND-001/H001_stale-object-memory/`.
- Active experiment: `E005_external_baseline_transition`.
- E001 is the first main experiment for H001.
- E001 starts as a proxy semantic-pair dynamic object search benchmark.
- E002 starts from E001 rows and attaches path/search-cost bridge fields.
- E003 starts from E001 rows and E002 path-cost proxy outputs to test controlled perception/proposal noise.
- E002-M02 evaluates static old-location, fixed top-k, task-conditioned, path-aware, and oracle policies under `euclidean_polyline_proxy_v0`.
- E002-M03/M04 fixes the claim boundary and selects `occupancy_grid_astar_v0` as the next real path-cost source.
- E002-M05 attaches PLY/semseg occupancy-grid A* path costs while preserving the 294 query-row denominator.
- E002-M06 evaluates static, top-k, task-conditioned, grid-aware, and oracle policies under `occupancy_grid_astar_v0`.
- E002-M07 separates occupancy-grid source limits from policy failures and blocks a positive claim for naive grid-aware ordering.
- E002-M08 recomputes grid-path proxy metrics under `target_reachable_eval`, separating 27 source-limited rows from policy metrics.
- E002-M09 tests `reachable_first_task_conditioned_budget_v0`, reducing returned-unreachable attempts without success loss under `target_reachable_eval`.
- E003-M00 separates controlled annotation-proxy perception noise from real RGB-D / open-vocabulary perception claims.
- E003-M01 confirms annotation-proxy noise is ready for 294 query rows, while current RGB-D/open-vocabulary rows remain 0.
- E003-M02 generates `clean_annotation_oracle_v0` and `annotation_score_jitter_v0` noisy query/candidate rows.
- E003-M03 evaluates 5292 clean/noisy policy predictions and reports robustness deltas under target-preserving annotation-proxy ranking noise.
- E003-M04 analyzes 2646 clean-vs-noisy transition rows and fixes the current controlled-noise claim boundary.
- E003-M05 audits real proposal-source readiness and selects `annotation_proposal_dropout_v0` as the next controlled stress profile.
- Docker is the default execution environment for paper-body experiments that require external repos, detectors, simulators, GPU dependencies, system packages, or compiled extensions.
- E003-M06 generates controlled proposal-dropout rows and separates `target_retained_eval` from `target_dropped_eval`.
- E003-M07 separates `natural_target_retained`, `forced_retained`, and `target_dropped` dropout boundaries and selects `annotation_false_positive_v0` as the next controlled stress profile.
- E003-M08 generates controlled annotation-derived false-positive rows and reports matched clean vs false-positive degradation for significant moved `routine_fetch`.
- E003-M09 separates false-positive `target_pushed_down`, `false_positive_added_no_push`, and `no_false_positive_available` boundaries and selects `annotation_centroid_jitter_v0` as the next controlled stress profile.
- E003-M10 generates controlled annotation centroid-jitter rows and separates identity proxy `SR` from localization proxy `SR`.
- E003-M10 significant moved `routine_fetch` `task_conditioned_budget_v0`: identity proxy `SR` 0.696970, localization proxy `SR` 0.606061.
- E003-M11 separates centroid-jitter identity/localization transition boundaries over 7938 boundary rows and 173 hard boundary rows.
- E003-M11 significant moved `routine_fetch` threshold-exceeded `task_conditioned_budget_v0`: identity proxy `SR` 1.000000, localization proxy `SR` 0.000000.
- E003-M12 selects `annotation_combined_moderate_v0` as the next route and keeps Dockerized real proposal route blocked as immediate next.
- E003-M12 confirms real RGB-D proposal-ready rows 0, real open-vocabulary proposal-ready rows 0, and proposal output files 0.
- E003-M13 implements `annotation_combined_moderate_v0`, creating 1176 noisy query rows, 5419 noisy candidate rows, and 10584 prediction rows.
- E003-M13 significant moved `routine_fetch` `task_conditioned_budget_v0`: identity/localization proxy `SR` 0.212121 / 0.212121.
- E003-M13 significant moved `routine_fetch` `reachable_first_task_conditioned_budget_v0`: identity/localization proxy `SR` 0.606061 / 0.606061.
- E003-M14 separates combined-noise failure boundaries over 7938 boundary rows and 521 hard boundary rows.
- E003-M14 significant moved `routine_fetch` reachable-first minus task identity/localization proxy `SR` delta: +0.393939 / +0.393939, with 13 gain rows and 0 loss rows.
- E003-M15 consolidates 5 controlled profiles and 8 claim-evidence rows.
- E003-M15 marks controlled annotation-proxy claim readiness as true, while real RGB-D/open-vocabulary and real navigation claim readiness remain false.
- E003-M16 selects `sequence_ready_scan_bootstrap` for real-proposal staging: 54 scan gates, 8 sequence-ready scans, 294 query rows audited, 0 current E001 rescan real-proposal-ready rows.
- E003-M17 stages 8 sequence-ready `3RScan` scans for real-proposal detector input.
- E003-M17 creates 8 query manifest rows, 460 object target rows, 344 detector target rows, 344 evaluation target rows, and a 98-label prompt set.
- E003-M17 keeps detector predictions ready false and real RGB-D/open-vocabulary claim readiness false.
- E003-M18 creates the Dockerfile, container runner, host wrapper, and output validator for the real-proposal route.
- E003-M18 validator smoke passes on empty scaffold output, and container runner local smoke passes over 8 manifest rows.
- E003-M18 Docker image build/run succeeds through `--docker-sudo --sudo-password-stdin`.
- E003-M18 image `research2/real-smoke:latest` exists with image id `e06a1c71c950` and size 186MB.
- E003-M18 Docker smoke output validates as empty scaffold output with 0 prediction rows and 0 validation errors.
- E003-M18 keeps detector backend integrated false, detector predictions ready false, paper-table command ready false, and real RGB-D/open-vocabulary claim readiness false.
- E003-M19 selects `groundingdino_rgbd_backproject_v0` as the real-detector backend contract.
- E003-M19 Docker backend-contract smoke validates 459 / 459 sampled RGB-D/color/depth/pose frame triplets over 8 scans.
- E003-M19 keeps detector backend integrated false, detector predictions ready false, paper-table command ready false, and real RGB-D/open-vocabulary claim readiness false.
- E003-M20 builds `research2/real-smoke:latest` with `torch`, `transformers`, `timm`, and `GroundingDINO` model-smoke dependencies.
- E003-M20 runs `IDEA-Research/grounding-dino-tiny` through `groundingdino_rgbd_backproject_v0` on one sampled RGB-D frame.
- E003-M20 writes 20 schema-valid proposal rows with 0 validator errors and 0 validator warnings.
- E003-M20 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false until proposal matching/evaluation is implemented.
- E003-M21 matches M20 proposal rows against the M17 target denominator for one evaluated scan.
- E003-M21 matched proposal/target rows: 2 / 2.
- E003-M21 proposal precision smoke: 0.100000.
- E003-M21 scan target recall smoke: 0.039216.
- E003-M21 label-overlap target recall smoke: 0.074074.
- E003-M21 false-positive proposal rows: 18 / 20.
- E003-M21 mean matched centroid error: 0.303314m.
- E003-M21 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false because only one frame from one scan is evaluated.
- E003-M22 removes the M20 early stop and evaluates 6 frames from 1 scan.
- E003-M22 raw predictions: 1664, written predictions: 120, skipped no-depth predictions: 15.
- E003-M22 matches 7 / 120 proposals and 7 target rows; false-positive proposal rows: 113.
- E003-M22 proposal precision smoke: 0.058333.
- E003-M22 scan target recall smoke: 0.137255.
- E003-M22 label-overlap target recall smoke: 0.218750.
- E003-M22 mean matched centroid error: 0.402223m.
- E003-M22 suggests the immediate bottleneck is not frame coverage but proposal consolidation/calibration and same-label over-threshold matching failure.
- E003-M23 sweeps 1188 confidence/depth-support/NMS/score configurations over the M22 detector proposals.
- E003-M23 selected config retains 12 proposals, matches 4 target rows, leaves 8 false-positive proposal rows, and improves proposal precision to 0.333333 while reducing fixed label-overlap target recall to 0.125000.
- E003-M23 full-match-preserving config keeps all 7 matched target rows but retains 97 proposals and 90 false-positive rows, with proposal precision only 0.072165.
- E003-M23 supports a detector calibration diagnostic, but it still keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false.
- E003-M24 separates scan-level targets into active prompt, centroid-frustum, depth-valid, and depth-consistent visible-proxy denominators.
- E003-M24 scan-level evaluation target rows: 51; active M22 prompt target rows: 32; prompt-not-active rows: 19.
- E003-M24 centroid frustum-visible target rows: 8; depth-valid projected target rows: 7; depth-consistent visible-proxy target rows: 5.
- E003-M24 M22 recall over scan / active prompt / depth-consistent visible-proxy denominators: 0.137255 / 0.218750 / 1.000000.
- E003-M24 M23 recall over depth-consistent visible-proxy denominator: 0.600000, so M23 calibration drops matched targets.
- E003-M24 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false.
- E003-M25 fixes expanded max labels at 32 because the M17 staged scans have max target label count 30.
- E003-M25 current prompt cap 12 covers 239 / 344 eval target rows; expanded prompt cap 32 covers 344 / 344, a gain of 105 rows.
- E003-M25 selects `m23_full_match_preserving_v0` as the primary calibration policy.
- E003-M25 fixes the next pilot Docker rerun config: max scans 2, max frames per scan 12, max labels 32, max predictions per frame 60, max predictions 1440.
- E003-M25 adds `run_m23_proposal_calibration.py --selection-policy full_match_preserving`, and smoke-checks that it preserves 7 matched target rows on the M22 diagnostic input.
- E003-M25 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false until the rerun is executed and validated.
- E003-M26 executes the prompt-expanded multi-scan Docker rerun over 2 scans and 24 frames.
- E003-M26 writes 1440 schema-valid detector proposals from 9768 raw predictions, with max predictions reached true.
- E003-M26 prompt-not-active target rows are 0 / 99 under max labels 32.
- E003-M26 matched target rows: 39; scan target recall smoke: 0.393939; depth-consistent visible-proxy recall: 0.628571.
- E003-M26 proposal precision smoke remains low at 0.027083, with 1401 false-positive proposal rows.
- E003-M26 match-preserving calibration keeps 39 matched targets and improves precision only to 0.028932.
- E003-M26 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false.
- E003-M27 separates M26 cap pressure, false-positive domination, calibration limits, and visibility bottleneck counts.
- E003-M27 lower-bound cap/post-depth rejected rows: 8272; saturated frames: 24 / 24.
- E003-M27 selected match-preserving precision: 0.028932; selected false-positive rows: 1309.
- E003-M27 same-label over-threshold false-positive rows: 1302; no-same-label false-positive rows: 7.
- E003-M27 calibration false-positive reduction is only 92 rows while matched rows stay 39.
- E003-M27 selects `cap_aware_label_balanced_ranking_v0` as the next detector policy.
- E003-M27 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false.
- E003-M28 runs an artifact-replay smoke for `cap_aware_label_balanced_ranking_v0` over M26 written proposals.
- E003-M28 label cleanup keeps 1433 / 1440 proposals and drops 7 non-prompt-label rows.
- E003-M28 selected policy: score mode `confidence`, per-scan-label cap 24, same-label spatial consolidation radius 0.5m.
- E003-M28 selected proposal rows: 407, matched target rows: 32, false-positive rows: 375.
- E003-M28 improves proposal precision from 0.027083 to 0.078624 while losing 7 matched targets.
- E003-M28 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false because it is replayed after M26's detector cap.
- E003-M29 inspects `run_rgbd_ov_proposals.py` and finds the current global cap at line 355 and per-frame cap at line 358 inside the detector result loop.
- E003-M29 fixes the runner args contract for `cap_aware_label_balanced_ranking_v0`: `--candidate-selection-policy`, `--selection-score-mode`, `--pre-cap-per-scan-label-cap`, `--pre-cap-spatial-consolidation-radius-m`, `--require-scan-prompt-label`, `--raw-candidate-collection-cap`, and `--pre-cap-policy-output`.
- E003-M29 fixes the output contract: keep `real_proposal_prediction_jsonl_v0`, add optional policy diagnostic fields, and write `pre_cap_policy_summary.json`.
- E003-M29 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false because it does not execute Docker detector inference.
- E003-M30 implements `cap_aware_label_balanced_ranking_v0` inside the Docker runner and host wrapper, then reruns the fixed M26 two-scan pilot.
- E003-M30 raw predictions / projected candidates / final written proposals: 9768 / 9496 / 830.
- E003-M30 matched target rows improve from M26 39 to 48, while false-positive rows drop from 1401 to 782.
- E003-M30 proposal precision improves from M26 0.027083 to 0.057831, but paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness remain false.
- E003-M31 compares M26/M28/M30 at target, label, and frame level.
- E003-M31 M30 gains/losses vs M26: 15 / 6 targets; stable matched / stable missed: 33 / 45.
- E003-M31 top gain labels: clothes +2, kitchen cabinet +2; top loss label: plant -6; top false-positive labels: table 47, chair 42, box 41, light 41, plant 38.
- E003-M31 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false because scale, true visibility, and remaining false positives are unresolved.
- E003-M32 fixes the scaled pre-cap rerun route as 8 staged scans with 24 frames per scan, 192 selected frames, 344 evaluation target rows, max labels 32, max predictions 10000, and raw candidate collection cap 200000.
- E003-M32 estimates 78144 raw predictions and 6640 final prediction rows from the M30 per-frame rate.
- E003-M32 tracks 7 M31 blockers in the scaled rerun contract and keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false until Docker rerun results exist.
- E003-M33 executes the scaled pre-cap Docker rerun over 8 scans and 192 frames.
- E003-M33 writes 3414 schema-valid final proposal rows from 67639 raw predictions, with validator errors/warnings 0 / 0.
- E003-M33 matched target rows: 204 / 344, proposal precision 0.059754, scan target recall 0.593023, depth-consistent visible-proxy recall 0.915584.
- E003-M33 match-preserving calibration does not change selected proposals, and top false-positive labels remain plant, shelf, chair, sofa, table, box, cabinet, and lamp.
- E003-M33 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false because false-positive load and true visibility remain unresolved.
- E003-M34 analyzes M33 false-positive labels, visible-proxy misses, and M31 blocker resolution over the scaled 8-scan result.
- E003-M34 resolves the previous two-scan scale-count blocker, but keeps false-positive load and true visibility as unresolved claim blockers.
- E003-M34 visible-proxy missed target rows: 13 / 154, visible-proxy recall 0.915584.
- E003-M34 top false-positive labels: plant 176, shelf 133, chair 129, sofa 117, table 116, box 111, cabinet 110, lamp 106.
- E003-M34 next recommended unit: `E003-M35 false-positive suppression route decision`.
- E003-M35 selects `recall_preserving_rank_cap_sweep_v0` as the first false-positive suppression route.
- E003-M35 selected probe `visible_miss_guarded_labelwise_rank_cap_v0` keeps matched targets 204 / 204, reduces false-positive rows from 3210 to 1782, and improves precision from 0.059754 to 0.102719 in diagnostic replay.
- E003-M35 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false because the selected probe is not yet executed as a validated M36 sweep.
- E003-M36 executes 56 offline suppression policies over M33 proposals and re-runs target matching after each filter.
- E003-M36 selected deployable 95pct policy `global_rank_cap_le_20` keeps 195 / 204 matched targets and reduces false-positive rows from 3210 to 2819.
- E003-M36 selected diagnostic policy `labelwise_rank_cap_oracle_retain_0p95` keeps 204 / 204 matched targets and reduces false-positive rows from 3210 to 1585.
- E003-M36 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false because split validation is still required.
- E003-M37 runs a balanced 4/4 scan split validation gate over M33 proposal artifacts.
- E003-M37 heldout baseline: matched targets 97, false-positive rows 1523, precision 0.059877.
- E003-M37 dev-selected labelwise policy: heldout matched targets 81 / 97, false-positive rows 1154, precision 0.065587, matched-target retention 0.835052.
- E003-M37 fixed global policy: heldout matched targets 97 / 97, false-positive rows 1433, precision 0.063399.
- E003-M37 heldout oracle: heldout matched targets 97 / 97, false-positive rows 979, precision 0.090149.
- E003-M37 label coverage risk: 24 heldout target labels have no dev matched example.
- E003-M37 keeps runner integration recommended false, paper-table command readiness false, and real RGB-D/open-vocabulary robustness claim readiness false.
- E003-M38 enumerates 210 possible split feasibility rows over the current 8-scan artifact.
- E003-M38 best current split still leaves 7 heldout target labels and 7 heldout target rows without dev matched examples.
- E003-M38 marks stronger split feasible with current 8 scans false.
- E003-M38 selected dev support policy `spatial_support_or_rank_guard_r1p5m_min3_rank_guard_le_12`: heldout matched targets 89 / 97, false-positive rows 1406, matched-target retention 0.917526, precision 0.059532.
- E003-M38 heldout oracle support policy `temporal_support_or_rank_guard_r0p75m_min3_rank_guard_le_20`: heldout matched targets 95 / 97, false-positive rows 1336, precision 0.066387.
- E003-M38 selects route `temporal_spatial_evidence_instrumentation_required`.
- E003-M38 keeps runner integration recommended false, paper-table command readiness false, and real RGB-D/open-vocabulary robustness claim readiness false.
- E003-M39 selects `docker_runner_pre_consolidation_support_evidence_v0`.
- E003-M39 fixes the runner insertion point as `select_cap_aware_label_balanced_candidates.after_cleaned_before_grouped`.
- E003-M39 fixes support policy id `temporal_spatial_support_evidence_v0` with radii 0.75m, 1.0m, 1.5m, and 2.0m.
- E003-M39 keeps deterministic post-processing route readiness false and real RGB-D/open-vocabulary robustness claim readiness false.
- E003-M40 implements runner-side `temporal_spatial_support_evidence_v0` fields and runs a short Docker smoke.
- E003-M40 status: `temporal_spatial_support_runner_smoke_ready`.
- E003-M40 final predictions: 95, with support evidence attached to 95 / 95 selected rows and support row field errors 0.
- E003-M40 selected rows with spatial / temporal support at any configured radius: 93 / 58.
- E003-M40 validator errors/warnings: 0 / 0.
- E003-M40 matched proposals / false positives / proposal precision smoke: 5 / 90 / 0.052632.
- E003-M40 keeps real RGB-D/open-vocabulary robustness claim readiness false because it is a short instrumentation smoke, not heldout policy evidence.
- E003-M41 selects score mode `confidence_sqrt_depth_support_temporal_v0`.
- E003-M41 route: `support_aware_scoring_before_consolidation_and_final_rank`.
- E003-M41 rejects hard support filtering for the next unit and keeps cap changes deferred.
- E003-M41 keeps long rerun readiness false until the selected score mode passes a short runner smoke.
- E003-M42 implements `confidence_sqrt_depth_support_temporal_v0` and runs a short Docker smoke.
- E003-M42 status: `support_aware_selection_runner_smoke_ready`.
- E003-M42 final predictions / matched proposals / false positives / precision smoke: 95 / 5 / 90 / 0.052632.
- E003-M42 has no M40 smoke delta on matched proposals, false positives, or precision.
- E003-M42 keeps real RGB-D/open-vocabulary robustness claim readiness false.
- E003-M43 selects `pre_cap_candidate_pool_export_then_offline_replay_v0` rather than an immediate long support-aware rerun.
- E003-M43 finds M42 vs M40 common selected rows 94 / 95, selected symmetric difference 2 rows, pre-cap rank changed 68 common rows, and selection-score changed 89 common rows.
- E003-M43 marks existing candidate-pool replay available false and runner edit required true.
- E003-M44 exports a 629-row pre-cap candidate pool and verifies offline replay reproduction for `confidence_sqrt_depth_support_temporal_v0`.
- E003-M44 runner selected rows / offline replay selected rows: 95 / 95, ordered and set reproduction true / true.
- E003-M45 confirms support-aware replay fails the frozen hard/weak-positive criteria.
- E003-M46 confirms bounded support-aware score redesign is not enough, so external route and direct bridge work are required.
- E003-M50 confirms `Grounded-SAM mask-depth` is not a positive replacement for `bbox-depth` on the same subset.
- E003-M54 confirms previous detector-ready scans cannot be directly attached to E001/E002 current search failures.
- E003-M59 verifies the first direct current-rescan detector bridge: 96 proposals, 21 matched proposals, precision 0.218750, scan target recall 0.724138.
- E003-M60 query-level bridge shows target detection on 3 / 7 query rows, but `detector_task_budget_v0` success remains 0 / 7.
- E003-M62 shows bounded repair recovers only 2 / 7 rows, while unbounded repair has high expected search cost.
- E003-M71 confirms `OpenMask3D` Docker execution is blocked by `MinkowskiEngine` dependency setup in the current environment.
- E003-M73 expands the direct detector-ready denominator to 96 query rows over 4 RGB-D-ready current rescans.
- E003-M74 completion verification is ready: 478 proposals, 12,192 pre-cap candidate rows, 47 / 62 matched targets, proposal precision 0.098326, scan target recall 0.758065, false-positive proposal rate 0.901674.
- E003-M75 joins E003-M74 proposals to 96 M73 query rows: query target detected 87 / 96, unique target detected 29 / 32, mean detected target rank 9.034483, mean false positives before target 8.034483.
- E003-M75 `detector_task_budget_v0` succeeds on 13 / 96 rows; bounded repair succeeds on 33 / 96 rows with higher mean `ExpectedSearchCost` 4.937500.
- E003-M75 keeps real RGB-D/open-vocabulary search claim readiness false and selects the E004 transition gate as the next step.
- E004-M01 transition gate is complete with status `e004_transition_ready_with_constraints`.
- E004-M01 confirms bounded repair improves query-level success by 20 rows over task budget, but task-context-specific effect readiness is false.
- E004-M01 selects E004-M02 as the next unit: design the task-context memory trust / re-observation decision metric contract.
- E004-M02 metric contract is complete with status `e004_m02_metric_contract_ready`.
- E004-M02 fixes allowed policy inputs, blocked leakage inputs, primary metrics, task-context-specific metrics, and E004-M03 success gates.
- E004-M03 memory trust policy is complete with status `e004_m03_task_context_tradeoff_ready_with_constraints`.
- E004-M03 `static_memory_only_v0` succeeds on 63 / 96 rows.
- E004-M03 `context_agnostic_memory_trust_reobserve_v0` succeeds on 66 / 96 rows.
- E004-M03 `task_context_memory_trust_reobserve_v0` succeeds on 68 / 96 rows, with mean `ExpectedSearchCost` 2.354167 and `AttemptSPL` proxy 0.675347.
- E004-M03 task-context-specific gain over context-agnostic memory trust is concentrated in `high_value_fetch`: +2 success rows with +0.500000 mean `ExpectedSearchCost`.
- E004-M03 keeps final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` claim readiness false.
- E004-M04 claim-boundary ablation is complete with status `e004_m04_claim_boundary_ready`.
- E004-M04 `context_agnostic_memory_trust_reobserve_v0`: 66 / 96, mean `ExpectedSearchCost` 2.187500.
- E004-M04 `task_context_memory_trust_reobserve_v0`: 68 / 96, mean `ExpectedSearchCost` 2.354167.
- E004-M04 `all_high_value_memory_trust_counterfactual_v0`: 72 / 96, mean `ExpectedSearchCost` 2.687500.
- E004-M04 task-context-specific claim strength is `limited_positive`; memory-trust decision claim readiness is true.
- E004-M05 scale/split stress is complete with status `e004_m05_split_stress_ready_limited_task_context`.
- E004-M05 task-context vs static success delta is +5 rows; task-context vs context-agnostic success delta is +2 rows.
- E004-M05 leave-one-scan memory-trust positive and task-context positive gates are true.
- E004-M05 bootstrap positive rates: task-context vs static 0.952, task-context vs context-agnostic 0.872, all-high-value vs task-context 0.872.
- E004-M05 task-context positive label groups are only `chair` and `pillow`; label breadth sufficient is false.
- E005-M01 external baseline transition is complete with status `e005_m01_external_baseline_transition_ready`.
- E005-M01 scored 10 candidate baselines and selected `DualMap` as the first external route.
- E005-M01 selected `ConceptGraphs` as backup, because it is the strongest open-vocabulary graph mapping fallback over posed RGB-D observations.
- E005-M01 keeps `OpenMask3D` as a later 3D instance proposal baseline because the local Docker/MinkowskiEngine blocker is still present.
- E005-M02 `DualMap` source/interface audit is complete with status `e005_m02_dualmap_interface_audit_ready_with_staging_required`.
- E005-M02 checked official `DualMap` repo commit `157235ec49e6a1f439babbc571c4c02ad1f06aa9` and license `Apache-2.0`.
- E005-M02 direct drop-in to current E004 JSONL rows: false.
- E005-M02 Dataset Mode staging route feasible: true.
- E005-M02 adapter contract ready: true.
- E005-M02 external baseline comparison ready: false.
- E005-M03 `DualMap` 3RScan dataset-format staging feasibility is complete with status `e005_m03_dualmap_3rscan_staging_feasibility_ready_with_conversion_required`.
- E005-M03 selected scans from E003-M73: 4.
- E005-M03 preflight-ready scans: 4 / 4.
- E005-M03 RGB-D-pose triplets across selected scans: 826.
- E005-M03 selected adapter: `scannet_exported_3rscan_adapter_v0`.
- E005-M03 materialization required: true.
- E005-M03 depth conversion `.pgm` -> `.png` required: true.
- E005-M03 object `*.pkl` schema inspection ready: false.
- E005-M04 `DualMap` staging root materialization is complete with status `e005_m04_dualmap_staging_root_materialized_smoke_ready`.
- E005-M04 staged dataset root: `local_dataset/DualMap_staged/3rscan_scannet_exported/scannet`.
- E005-M04 materialized scans: 4 / 4.
- E005-M04 color symlinks / depth PNG / pose symlinks: 826 / 826 / 826.
- E005-M04 intrinsic files: 4.
- E005-M04 runtime command plan ready: true.
- E005-M04 `DualMap` runtime launched: false.
- E005-M04 object `*.pkl` schema inspected: false.
- E005-M05 `DualMap` runtime preflight is complete with status `e005_m05_dualmap_runtime_blocked_env_bootstrap_required`.
- E005-M05 official repo head matches audited commit `157235ec49e6a1f439babbc571c4c02ad1f06aa9`.
- E005-M05 smoke scan color/depth/pose frame counts: 93 / 93 / 93.
- E005-M05 Docker daemon ready: true.
- E005-M05 NVIDIA runtime detected: true.
- E005-M05 GPU probe: `NVIDIA GeForce RTX 5090, 32607 MiB, 580.126.09`.
- E005-M05 static object `*.pkl` schema inspected: true.
- E005-M05 static schema fields: `uid`, `pcd_points`, `pcd_colors`, `clip_ft`, `class_id`, `nav_goal`.
- E005-M05 `mobileclip` submodule ready: false.
- E005-M05 current Python runtime dependency ready: false.
- E005-M05 `DualMap` runtime launched: false.
- E005-M05 runtime object `*.pkl` inspected: false.
- E005-M06 `DualMap` bootstrap launch is complete with status `e005_m06_dualmap_bootstrap_job_launched`.
- E005-M06 tmux session: `e005_m06_dualmap_bootstrap`.
- E005-M06 log path: `logs/20260513_142937_e005_m06_dualmap_bootstrap.log`.
- E005-M06 Docker image target: `research2/dualmap-smoke:latest`.
- E005-M06 initial verifier status: `e005_m06_dualmap_bootstrap_running`.
- E005-M06 local `mobileclip` ready: true.
- E005-M06 Docker image ready at initial verification: false.
- E005-M06 bounded Dockerfile repair applied: absolute env Python for `mobileclip` install and import smoke.
- E005-M06 one-scan runtime launched: false.
- E005-M07 `DualMap` bootstrap completion verification is complete with status `e005_m06_dualmap_bootstrap_ready`.
- E005-M07 tmux session stopped: true.
- E005-M07 Docker image ready: true.
- E005-M07 image id: `sha256:7c053613ab51d968f4e70896364af2493595e827fb7605f0fd16c514c5cc0bf4`.
- E005-M07 image size: 7,927,047,638 bytes.
- E005-M07 local `mobileclip` ready: true.
- E005-M07 dependency import smoke: `dualmap_import_smoke_ok`.
- E005-M07 one-scan runtime launched: false.
- E005-M08 `DualMap` one-scan runtime smoke launch is complete with status `e005_m08_dualmap_runtime_job_launched`.
- E005-M08 verifier status is `e005_m08_dualmap_runtime_running`.
- E005-M08 tmux session: `e005_m08_dualmap_runtime`.
- E005-M08 log path: `logs/20260513_153046_e005_m08_dualmap_one_scan_runtime.log`.
- E005-M08 output path: `local_dataset/DualMap_outputs/ddc73795-765b-241a-9c5d-b97744afe077`.
- E005-M08 scan id: `ddc73795-765b-241a-9c5d-b97744afe077`.
- E005-M08 runtime object `*.pkl` count while running: 0.
- E005-M09 `DualMap` runtime completion verification is complete with status `e005_m08_dualmap_runtime_failed`.
- E005-M09 confirms tmux stopped and background returncode is 137.
- E005-M09 output inventory: runtime object `*.pkl` 0, `layout.pcd` 0, `system_time.csv` 0, DualMap log 1.
- E005-M09 failure signals: `cuda_out_of_memory`, `clip_model_init_failed`, `yolo_not_initialized_after_detector_init_failure`, `fastsam_not_initialized_after_detector_init_failure`, `hydra_job_error`.
- E005-M09 GPU snapshot after cleanup: free 1510 MiB, with an unrelated `python3` process using 27714 MiB.
- E005-M10 selects detector-enabled free-GPU retry.
- E005-M12 verifies the retry failed at `/home/mambauser/.cache/clip` permission.
- E005-M13 fixes the cache route with a writable `/home/mambauser/.cache` mount.
- E005-M15 verifies cache-fixed runtime completion with `layout.pcd` 1, `system_time.csv` 1, `detector_time.csv` 1, but object `*.pkl` 0.
- E005-M16 diagnoses M14 as an object-output failure under `stride=20`, `stable_num=8`, and local objects 8 -> 0.
- E005-M18 verifies denser stride `stride=5` also completes without object `*.pkl`: processed keyframes 19, local objects 26 -> 0, `layout.pcd` 1, `system_time.csv` 1, `detector_time.csv` 1.
- E005-M19 selects `ConceptGraphs` fallback source/interface audit and leaves lower-`stable_num` `DualMap` as schema-only diagnostic fallback.
- E005-M20 audits official `ConceptGraphs` source/interface at commit `93277a02bd89171f8121e84203121cf7af9ebb5d`, license `MIT`, and selects `conceptgraphs_depth_aligned_scannet_smoke`.
- E005-M20 finds local direct ConceptGraphs-ready scans 0 / 4 because the current staged scans have `intrinsic_depth.txt` and color/depth resolution mismatch, but no `intrinsic_color.txt`.
- E005-M21 materializes `local_dataset/ConceptGraphs_staged/3rscan_depth_aligned_scannet/` with 4 / 4 scans ready, 826 / 826 / 826 color/depth/pose files, and 4 / 4 resolution-aligned scans.
- E005-M22 verifies Docker ready true, NVIDIA runtime true, GPU free memory 24008 MiB, staged scans 4 / 4, and SAM checkpoint ready true.
- E005-M22 finds `ConceptGraphs` repo, `Grounded-Segment-Anything` repo, `research2/conceptgraphs-smoke:latest`, and `groundingdino_swint_ogc.pth` are not ready yet.
- E005-M23 launches tmux `e005_m23_conceptgraphs_acquisition`, log `logs/20260514_165555_e005_m23_conceptgraphs_acquisition.log`.
- E005-M24 verifies acquisition complete: `ConceptGraphs` head matched, `GSA` head matched, SAM symlinks ready, `groundingdino_swint_ogc.pth` ready 693,997,677 bytes.

## 논문 주장

Supported experiment target:

- `Task-Conditioned Stale Semantic Memory Update` for semantic-pair dynamic object search proxy behavior.

Non-claims:

- real navigation `SR` / `SPL`.
- real RGB-D perception robustness.
- open-vocabulary perception robustness.
- learned task policy.
- natural-language intention understanding.

## 에이전트 추론

E005 now shows that `DualMap` can execute on the staged `3RScan` adapter, but the current route does not produce object-map `*.pkl` outputs. `ConceptGraphs` is the active external mapping baseline route and now has full 9-scan heldout query-level aggregation. `Open3DSG` is the next second external map/scene-graph route, but M59 still needs object-candidate rows before any query-level comparison.

## 사용자 판단 필요

Relaunch E005-M59 with the lower-memory object-only patch when GPU free memory is >= 24GB.
