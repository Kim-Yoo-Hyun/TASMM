# Experiments

Updated: 2026-05-08

이 폴더는 main experiment 구현과 내용 기록을 관리한다. 작성 규칙은 `docs/experiments.md`를 따른다.

## Status

Main experiment implementation stage has started. E001-M01 through E001-M05 artifacts, E002-M01 through E002-M09 artifacts, and E003-M00 through E003-M28 artifacts are complete. E003 has a Dockerized real-detector backend, non-empty model smoke output, detector-to-target matching diagnostics, multi-frame projection diagnostics, proposal calibration diagnostics, visibility/prompt/projection denominator diagnostics, a prompt-expanded two-scan Docker rerun pilot, a false-positive/cap bottleneck gate, and a cap-aware label-balanced replay policy smoke.

## Active Experiment

| ID | Status | Folder | Next action |
| --- | --- | --- | --- |
| E001 | M01-M05 artifacts ready | [E001_semantic_pair_dynamic_search_proxy](E001_semantic_pair_dynamic_search_proxy/README.md) | Input to E002 |
| E002 | M01-M09 path-cost artifacts ready | [E002_path_cost_bridge](E002_path_cost_bridge/README.md) | Input to E003 |
| E003 | M00-M28 cap-aware replay policy ready | [E003_perception_noise_expansion](E003_perception_noise_expansion/README.md) | Docker pre-cap policy integration rerun gate |

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

No current decision. Continue with E003-M29 Docker pre-cap policy integration rerun gate.
