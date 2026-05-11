# Experiments

Updated: 2026-05-11

이 폴더는 main experiment 구현과 내용 기록을 관리한다. 작성 규칙은 `docs/experiments.md`를 따른다.

- Current report: [report.md](report.md)

## Status

Main experiment implementation stage has started. E001-M01 through E001-M05 artifacts, E002-M01 through E002-M09 artifacts, and E003-M00 through E003-M58 artifacts are complete. E003 has a Dockerized real-detector backend, scaled real-proposal diagnostics, failed support-aware replay/redesign evidence, an external baseline feasibility gate, a negative `Grounded-SAM` mask-depth diagnostic, a search-critical bbox boundary audit, a dynamic-pair bridge gate, verified current-rescan sequence payloads, and a direct current-rescan detector/evaluation bridge design. E003-M59 direct current-rescan detector bridge Docker run has been launched in background tmux session `e003_m59_direct_bridge` for 7 search-failure query rows across 4 scans.

## Active Experiment

| ID | Status | Folder | Next action |
| --- | --- | --- | --- |
| E001 | M01-M05 artifacts ready | [E001_semantic_pair_dynamic_search_proxy](E001_semantic_pair_dynamic_search_proxy/README.md) | Input to E002 |
| E002 | M01-M09 path-cost artifacts ready | [E002_path_cost_bridge](E002_path_cost_bridge/README.md) | Input to E003 |
| E003 | M00-M59 detector job running | [E003_perception_noise_expansion](E003_perception_noise_expansion/README.md) | Verify E003-M59 completion, then run E003-M60 query-level bridge evaluation |

## 사실

- Active hypothesis: `hypothesis/CAND-001/H001_stale-object-memory/`.
- Active experiment: `E003_perception_noise_expansion`.
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

E001 is a main experiment implementation stage, not a final thesis confirmation stage. Thesis direction should be confirmed only after scaled E001 results and failure analysis.

## 사용자 판단 필요

No current decision. Continue with E003-M54 search-critical bbox-depth failure-boundary audit.
