# Research Summary

Updated: 2026-05-11

이 문서는 `research2/` 워크스페이스의 현재 연구 방향, 배경, 가설, 진행 상황, 남은 쟁점, 실험 계획을 연구 보고서 형식으로 요약한다. 이 문서는 paper draft가 아니라 현재까지의 working summary다.

## Research Direction

사실:

- 연구 축은 semantic mapping 기반 human-friendly robot intelligence다.
- 현재 active candidate는 `CAND-001` / `Intent- and Staleness-Aware Semantic Mapping`이다.
- 현재 active hypothesis는 `H001_stale-object-memory`다.
- 목표 venue 기준은 AI, ML, CV, Robotics top-tier journal/conference다.
- 최종 논문 목표는 Direction B `Task-Aware Dynamic Semantic Mapping for Open-Vocabulary Search and Navigation`이다.

에이전트 추론:

- 현재 가장 유망한 방향은 로봇의 semantic map을 단순한 object repository가 아니라 task-conditioned stale memory로 다루는 것이다.
- 핵심 연구 질문은 "사람의 task context가 오래된 semantic memory를 얼마나 믿을지, 어디를 먼저 재관측하거나 탐색할지, 어떤 candidate를 먼저 방문할지 바꿀 수 있는가"다.
- 현재 구현은 Direction A `Task-Conditioned Stale Semantic Memory`를 core method로 고정하고, real proposal/search bridge, external baselines, search/navigation metrics를 붙여 Direction B로 확장하는 방식이다.

## Research Background

사실:

- 최근 semantic mapping / 3D scene graph / open-vocabulary mapping 연구는 `3RScan`, `3DSSG`, RGB-D sequence, open-vocabulary detector, LLM/VLM reasoning과 결합되고 있다.
- 기존 mapping 연구는 scene representation, object grounding, relation graph, open-vocabulary retrieval을 강화해 왔다.
- Robotics 관점에서는 map이 downstream search, navigation, manipulation, instruction following에 실제로 도움이 되는지가 중요하다.

에이전트 추론:

- top-tier paper로 가려면 "더 좋은 map"이 아니라 "더 좋은 행동 또는 decision"을 보여야 한다.
- 특히 dynamic object search/navigation에서는 stale semantic memory, perception noise, path/search cost, human task context가 한 번에 얽힌다.

## Motivation

사실:

- 실제 가정/사무실 환경의 물체는 이동한다.
- 로봇은 과거 map에 있는 old location을 그대로 믿으면 헛걸음할 수 있다.
- 반대로 과거 memory를 완전히 버리면 자주 쓰이는 물체, 안정적인 위치, task-relevant prior를 활용하지 못한다.
- RGB-D / open-vocabulary perception은 false positive, missed target, centroid localization error를 만든다.

논문 주장 후보:

- 사람의 task context는 자연어 이해 자체보다 먼저 memory trust, re-observation priority, candidate visit budget을 바꾸는 condition으로 활용될 수 있다.
- stale semantic memory를 task-conditioned decision layer로 다루면 dynamic object search에서 `SR`, `ExpectedSearchCost`, `AttemptSPL`, stale old-location FP를 개선할 수 있다.

## Limitation of Existing Work

사실:

- 많은 semantic mapping 연구는 map construction과 retrieval 품질에 집중한다.
- open-vocabulary mapping은 풍부한 label/query 대응을 제공하지만, dynamic object가 이동했을 때 old semantic memory를 어떻게 신뢰할지까지 명확히 다루지 않는 경우가 많다.
- 3D scene graph 기반 reasoning은 relation/object 구조를 제공하지만, task-conditioned memory update와 search-cost decision을 end-to-end로 평가하는 benchmark는 아직 약하다.
- real RGB-D/open-vocabulary detector output은 false-positive load가 크며, 단순 confidence/depth/NMS calibration만으로는 recall을 보존하면서 precision을 충분히 올리기 어렵다.

에이전트 추론:

- 기존 한계는 "map이 부정확하다"가 아니라 "map의 불확실성과 오래됨을 task 수행 의사결정에 어떻게 반영할지 불분명하다"로 잡는 것이 더 강하다.
- 이 문제는 semantic mapping 문제다. 로봇이 과거 semantic memory, 현재 RGB-D observation, object identity, task context, 공간 cost를 함께 사용해야 하기 때문이다.

## Problem Definition

사실:

- Input 후보:
  - stale semantic memory from `3RScan` / `3DSSG`
  - current or rescan observation
  - object/category query
  - structured task context such as `routine_fetch`, `high_value_fetch`, `noisy_high_value_fetch`
  - candidate locations and optional path/search cost
  - RGB-D/open-vocabulary proposal rows when available
- Output 후보:
  - candidate visit order
  - memory trust / stale-location suppression decision
  - re-observation or search budget decision
  - predicted target location or failure boundary
- Metrics:
  - proxy `SR`
  - `ExpectedSearchCost`
  - `AttemptSPL`
  - stale old-location FP
  - proposal recall
  - false-positive proposal rows
  - proposal precision
  - scan target recall
  - depth-consistent visible-proxy recall

논문 주장 후보:

- Task-conditioned stale semantic memory update should improve dynamic object search behavior over static memory, fixed top-k, and naive path-aware policies.
- Real navigation `SR` / `SPL` and deployable search policy are not yet supported until simulator/navmesh/trajectory execution is added.

## Core Hypothesis

논문 주장 후보:

- `Task-Conditioned Stale Semantic Memory Update` can improve dynamic object search by using task context to modulate memory trust, search budget, and candidate ranking under object movement and perception noise.
- The method should reduce stale old-location returns and improve search-cost-aware metrics without discarding useful low-motion semantic memory.
- Under real RGB-D/open-vocabulary proposals, the same decision layer should remain useful if proposal recall and false-positive boundaries are explicitly modeled.

사용자 판단 필요:

- 최종 논문 claim은 real RGB-D/open-vocabulary robustness와 search/navigation bridge까지 포함하는 쪽이 top-tier 가능성이 더 높다.
- 단, 현재 real navigation `SR` / `SPL`은 아직 claim하지 않는다.

## Propose Framework

에이전트 추론:

Working name은 `TASMM`로 둘 수 있다: Task- and Staleness-aware Semantic Memory Mapping.

Proposed components:

- Semantic Memory Store:
  - object/category memory
  - scan/rescan identity
  - old/current location
  - motion/staleness score
  - source quality
- Task Context Conditioner:
  - structured task context
  - memory trust adjustment
  - re-observation / search budget adjustment
  - high-value vs routine task tradeoff
- Candidate Proposal Layer:
  - annotation-proxy candidates for controlled experiments
  - RGB-D/open-vocabulary proposals from `groundingdino_rgbd_backproject_v0`
  - proposal schema validation and matching to `3DSSG` denominator
- Search Decision Layer:
  - static old-location baseline
  - fixed top-k baseline
  - `task_conditioned_budget_v0`
  - `reachable_first_task_conditioned_budget_v0`
  - oracle upper bound
- Evaluation Layer:
  - semantic-pair dynamic object search proxy
  - path/search-cost bridge
  - perception/proposal-noise robustness
  - failure boundary and claim boundary analysis

## Current Progress

사실:

- H001 hypothesis phase is `ready_with_constraints`.
- Main experiment implementation has started under `experiments/`.
- E001, E002, and E003 are active experiment tracks.

E001 facts:

- E001 builds a semantic-pair dynamic object search proxy benchmark.
- Ready pairs: 13.
- Base query rows: 98.
- Context-expanded query rows: 294.
- Candidate rows: 1248.
- `task_conditioned_budget_v0` significant moved `routine_fetch` proxy `SR`: 0.727273.
- `task_conditioned_budget_v0` significant moved `high_value_fetch` proxy `SR`: 0.909091.

E002 facts:

- E002 adds path/search-cost bridge fields.
- `occupancy_grid_astar_v0` was implemented as a proxy path-cost source.
- Query rows: 294.
- Candidate rows: 1248.
- Target-reachable rows: 267 / 294.
- `reachable_first_task_conditioned_budget_v0` reduced returned-unreachable rate from 0.111111 to 0.000000 under `target_reachable_eval`.
- Significant `routine_fetch` `SR` stayed at 0.777778 under the reachable-first revision.
- Real navigation path-cost rows remain 0.

E003 facts:

- E003 first built controlled annotation-proxy noise profiles:
  - `annotation_score_jitter_v0`
  - `annotation_proposal_dropout_v0`
  - `annotation_false_positive_v0`
  - `annotation_centroid_jitter_v0`
  - `annotation_combined_moderate_v0`
- Controlled annotation-proxy claim readiness is true.
- Real RGB-D/open-vocabulary claim readiness remains false.
- Dockerized real proposal route was implemented with image `research2/real-smoke`.
- Selected detector backend: `groundingdino_rgbd_backproject_v0`.
- E003-M33 scaled Docker rerun completed over 8 scans and 192 frames.
- E003-M33 raw / projected / policy-input / spatial-consolidated / final proposal rows: 67639 / 65812 / 60435 / 4284 / 3414.
- E003-M33 matched target rows: 204 / 344.
- E003-M33 false-positive proposal rows: 3210.
- E003-M33 proposal precision: 0.059754.
- E003-M33 scan target recall: 0.593023.
- E003-M33 depth-consistent visible-proxy recall: 0.915584.
- E003-M33 top false-positive labels: plant, shelf, chair, sofa, table, box, cabinet, lamp.
- E003-M34 scaled failure analysis is complete.
- E003-M34 resolves the previous two-scan scale-count blocker.
- E003-M34 visible-proxy missed target rows: 13 / 154.
- E003-M34 keeps false-positive load and true visibility as unresolved claim blockers.
- E003-M34 next recommended unit: `E003-M35 false-positive suppression route decision`.
- E003-M35 false-positive suppression route decision is complete.
- E003-M35 selected route: `recall_preserving_rank_cap_sweep_v0`.
- E003-M35 selected probe: `visible_miss_guarded_labelwise_rank_cap_v0`.
- E003-M35 selected probe keeps matched targets 204 / 204, reduces false-positive rows from 3210 to 1782, and improves diagnostic precision from 0.059754 to 0.102719.
- E003-M36 recall-preserving suppression sweep is complete.
- E003-M36 evaluates 56 offline suppression policies over M33 proposals and re-runs target matching after each filter.
- E003-M36 selected deployable 95pct policy `global_rank_cap_le_20`: matched targets 195 / 204, false-positive rows 2819, precision 0.064698.
- E003-M36 selected diagnostic policy `labelwise_rank_cap_oracle_retain_0p95`: matched targets 204 / 204, false-positive rows 1585, precision 0.114030.
- E003-M36 marks split validation as required before paper-table real RGB-D/open-vocabulary claim.
- E003-M37 suppression split validation is complete.
- E003-M37 split protocol: `balanced_scan_4_4_v0`, with 4 dev scans and 4 heldout scans.
- E003-M37 heldout baseline: matched targets 97, false-positive rows 1523, precision 0.059877.
- E003-M37 dev-selected labelwise policy `dev_selected_visible_miss_guarded_labelwise_rank_cap_v0`: heldout matched targets 81 / 97, false-positive rows 1154, precision 0.065587, matched-target retention 0.835052.
- E003-M37 fixed global policy `global_rank_cap_le_22_selected_on_train`: heldout matched targets 97 / 97, false-positive rows 1433, precision 0.063399.
- E003-M37 heldout oracle `heldout_oracle_visible_miss_guarded_labelwise_rank_cap_v0`: heldout matched targets 97 / 97, false-positive rows 979, precision 0.090149.
- E003-M37 label coverage risk: 24 heldout target labels have no dev matched example.
- E003-M37 keeps runner integration recommended false, paper-table command readiness false, and real RGB-D/open-vocabulary claim readiness false.
- E003-M38 split or temporal-spatial gate is complete.
- E003-M38 enumerates 210 split feasibility rows and finds that the best current 8-scan split still leaves 7 heldout target labels / 7 heldout target rows without dev matched examples.
- E003-M38 marks stronger split feasible with current 8 scans false.
- E003-M38 selected dev support policy `spatial_support_or_rank_guard_r1p5m_min3_rank_guard_le_12`: heldout matched targets 89 / 97, false-positive rows 1406, precision 0.059532, matched-target retention 0.917526.
- E003-M38 heldout oracle support policy `temporal_support_or_rank_guard_r0p75m_min3_rank_guard_le_20`: heldout matched targets 95 / 97, false-positive rows 1336, precision 0.066387.
- E003-M38 selects route `temporal_spatial_evidence_instrumentation_required`.
- E003-M38 keeps runner integration recommended false, paper-table command readiness false, and real RGB-D/open-vocabulary claim readiness false.
- E003-M39 temporal-spatial support instrumentation gate is complete.
- E003-M39 selects route `docker_runner_pre_consolidation_support_evidence_v0`.
- E003-M39 fixes insertion point `select_cap_aware_label_balanced_candidates.after_cleaned_before_grouped`.
- E003-M39 fixes support policy id `temporal_spatial_support_evidence_v0` with radii 0.75m, 1.0m, 1.5m, and 2.0m.
- E003-M39 keeps deterministic post-processing route readiness false, Docker run executed false, paper-table command readiness false, and real RGB-D/open-vocabulary claim readiness false.
- E003-M40 temporal-spatial support runner smoke is complete.
- E003-M40 status: `temporal_spatial_support_runner_smoke_ready`.
- E003-M40 Docker build/run executed: true / true.
- E003-M40 raw predictions / projected candidates / policy input / final predictions: 736 / 662 / 629 / 95.
- E003-M40 support evidence attached to selected rows: 95 / 95.
- E003-M40 selected rows with spatial / temporal support at any configured radius: 93 / 58.
- E003-M40 support row field errors: 0.
- E003-M40 validator errors/warnings: 0 / 0.
- E003-M40 matched proposals / false-positive proposals / proposal precision smoke: 5 / 90 / 0.052632.
- E003-M40 keeps real RGB-D/open-vocabulary claim readiness false because it is a short smoke, not heldout policy evidence.
- E003-M41 support-aware selection policy gate is complete.
- E003-M41 status: `support_aware_selection_policy_gate_ready`.
- E003-M41 selected score mode: `confidence_sqrt_depth_support_temporal_v0`.
- E003-M41 selected route: `support_aware_scoring_before_consolidation_and_final_rank`.
- E003-M41 keeps hard support filtering false and support cap changes false for the next unit.
- E003-M41 keeps long rerun readiness false until the selected score mode passes a short runner smoke.
- E003-M42 support-aware selection runner smoke is complete.
- E003-M42 status: `support_aware_selection_runner_smoke_ready`.
- E003-M42 score mode: `confidence_sqrt_depth_support_temporal_v0`.
- E003-M42 raw predictions / projected candidates / policy input / final predictions: 736 / 662 / 629 / 95.
- E003-M42 support evidence attached to selected rows: 95 / 95.
- E003-M42 validator errors/warnings: 0 / 0.
- E003-M42 matched proposals / false-positive proposals / proposal precision smoke: 5 / 90 / 0.052632.
- E003-M42 matched/false-positive/precision delta vs E003-M40: 0 / 0 / 0.0.
- E003-M42 keeps real RGB-D/open-vocabulary claim readiness false.
- E003-M43 support-aware scaled rerun route gate is complete.
- E003-M43 status: `support_aware_scaled_rerun_route_gate_ready`.
- E003-M43 selected route: `pre_cap_candidate_pool_export_then_offline_replay_v0`.
- E003-M43 M42 vs M40 common selected rows: 94 / 95.
- E003-M43 M42 vs M40 selected symmetric difference rows: 2.
- E003-M43 M42 vs M40 pre-cap rank changed common rows: 68.
- E003-M43 M42 vs M40 selection-score changed common rows: 89.
- E003-M43 existing candidate-pool replay available: false.
- E003-M43 immediate support-aware long rerun recommended: false.
- E003-M43 runner edit required before next scaled run: true.
- E003-M44 pre-cap candidate-pool export and offline replay harness smoke is complete.
- E003-M44 status: `pre_cap_candidate_pool_replay_smoke_ready`.
- E003-M44 Docker smoke status: `pre_cap_candidate_pool_export_smoke_ready`.
- E003-M44 candidate pool rows: 629.
- E003-M44 candidate pool rows with support policy: 629 / 629.
- E003-M44 runner selected rows / offline replay selected rows: 95 / 95.
- E003-M44 ordered / set reproduction for `confidence_sqrt_depth_support_temporal_v0`: true / true.
- E003-M44 validator errors/warnings: 0 / 0.
- E003-M45 scaled candidate-pool export and support-aware replay is complete and verified.
- E003-M45 tmux session `e003_m45_scaled_pool` ended; log `logs/20260508_155219_e003_m45_scaled_candidate_pool_export_replay_tmux.log` recorded `exit_code=0`.
- E003-M45 output: `experiments/E003_perception_noise_expansion/artifacts/E003-M45_scaled_candidate_pool_export_replay_v0/`.
- E003-M45 verification command rerun completed with status `scaled_candidate_pool_replay_ready`.
- E003-M45 frozen interpretation contract verdict: `fail_redesign`.
- E003-M45 result: `confidence` 204 matched / 3210 FP / precision 0.059754, `confidence_sqrt_depth` 198 / 3209 / 0.058116, `confidence_sqrt_depth_support_temporal_v0` 196 / 3211 / 0.057529.
- E003-M46 support-aware score redesign or external proposal baseline gate is complete.
- E003-M46 swept 12 bounded local score policies over the M45 candidate pool.
- E003-M46 found hard pass policy count 0 and weak positive policy count 0.
- E003-M46 selected route: `external_proposal_baseline_gate_first`.
- E003-M47 external proposal/mapping baseline feasibility gate is complete.
- E003-M47 selected route: `Grounded-SAM`.
- E003-M47 route scores: `Grounded-SAM` 39, `OpenMask3D` 24, `ConceptGraphs` 16, `OVIR-3D` 14, `HOV-SG` 6.
- E003-M48 `Grounded-SAM` input/output contract is complete.
- E003-M48 selected backend id: `grounded_sam_mask_backproject_v0`.
- E003-M48 preserves the current `real_proposal_prediction_jsonl_v0` required fields and adds 9 optional mask diagnostic fields.
- E003-M48 did not execute Docker/model inference; it fixes the next implementation contract.
- E003-M49 completed with status `grounded_sam_model_smoke_ready`: 24 mask-depth proposal rows, validator errors/warnings 0 / 0, M21 matcher passed.
- E003-M50 same-subset bbox-depth vs mask-depth comparison is complete.
- E003-M50 bbox-depth result: 31 proposals, 2 matched targets, 29 false positives, proposal precision 0.064516, mean matched centroid error 0.591356m.
- E003-M50 mask-depth result: 24 proposals, 1 matched target, 23 false positives, proposal precision 0.041667, mean matched centroid error 0.916258m.
- E003-M50 selected next route: `do_not_scale_grounded_sam_yet`.
- E003-M51 post-M50 route decision is complete and selected `targeted_mask_failure_analysis_first`.
- E003-M52 `Grounded-SAM` mask failure analysis is complete.
- E003-M52 candidate pairing: common candidate rows 24, bbox-only candidate rows 7, mask-only candidate rows 0.
- E003-M52 `Grounded-SAM` skipped mask projection rows: 16.
- E003-M52 lost-by-mask target count: 1, label `plant`.
- E003-M52 common same-target match-distance delta mask minus bbox: -0.018907m.
- E003-M52 diagnoses target loss as mask projection candidate dropout and aggregate centroid worsening as match-set composition after the easy `plant` target was dropped.
- E003-M52 next recommended unit: `E003-M53 bbox-depth continuation and failure-boundary repair gate`.
- E003-M53 bbox-depth continuation repair gate is complete.
- E003-M53 selected route: `search_critical_bbox_failure_boundary_first`.
- E003-M53 route scores: search-critical bbox boundary 46, deployable bbox suppression repair 30, `OpenMask3D` feasibility 27, `ConceptGraphs` mapping 19, `Open3DSG` mapping 16, `HOV-SG` navigation/mapping 10.
- E003-M53 next recommended unit: `E003-M54 search-critical bbox-depth failure-boundary audit`.
- E003-M53 baseline boundary: `OpenMask3D` remains a later external 3D instance proposal baseline; `Open3DSG`, `ConceptGraphs`, and `HOV-SG` remain later map/scene-graph/navigation baselines.
- E003-M54 search-critical bbox failure-boundary audit is complete.
- E003-M54 finds E001 current `rescan_id` overlap with M33 detector scans: 0.
- E003-M54 exact current query-instance joins: 0.
- E003-M54 reference-memory-only joins: 120, label overlap count: 21.
- E003-M54 existing E001/E002 search failures with label-level detector risk: 7.
- E003-M54 strongest bridge labels: `pillow` priority 8 and `chair` priority 7.
- E003-M54 next recommended unit: `E003-M55 dynamic-pair-aligned real-proposal bridge gate`.
- E003-M55 dynamic-pair bridge gate is complete.
- E003-M55 selected route: `stage_search_failure_current_rescans_first`.
- E003-M55 route scores: direct current-rescan staging 46, detector-aligned search proxy 31, reference-memory-side bridge 18, `OpenMask3D` before bridge 15, label-level stress only 14.
- E003-M55 search-failure current rescans: 4.
- E003-M55 search-failure current rescans with semantic triplet ready: 4 / 4.
- E003-M55 search-failure current rescans already sequence-ready: 0 / 4.
- E003-M55 priority scans: `5555106a-36f1-29c0-8913-df1ba3c3cfd5`, `4731976c-f9f7-2a1a-95cc-31c4d1751d0b`, `ddc73795-765b-241a-9c5d-b97744afe077`, and `10b17957-3938-2467-88a5-9e9254930dad`.
- E003-M55 next recommended unit: `E003-M56 current-rescan sequence payload staging plan`.
- E003-M56 current-rescan sequence staging plan is complete.
- E003-M56 target scan count: 4.
- E003-M56 prelaunch sequence-ready target scan count: 0 / 4.
- E003-M56 download-required target scan count: 4 / 4.
- E003-M56 fixed `wget -c` as the default resumable downloader and the official `download_3rscan.py --type sequence.zip` route as fallback.
- E003-M56 records launch command, log path, run script, download manifest, and verification command in `command_plan.json`.
- E003-M56 prelaunch verifier status: `sequence_payloads_not_ready`.
- E003-M56 next recommended unit: `E003-M57 launch current-rescan sequence staging background job`.
- E003-M57 sequence staging job launch is complete.
- E003-M57 status: `sequence_staging_job_launched`.
- E003-M57 background job status was `running` at launch.
- E003-M57 tmux session: `e003_m56_sequence_stage`.
- E003-M57 log path: `logs/20260510_170443_e003_m56_sequence_staging.log`.
- E003-M57 target scans: `5555106a-36f1-29c0-8913-df1ba3c3cfd5`, `4731976c-f9f7-2a1a-95cc-31c4d1751d0b`, `ddc73795-765b-241a-9c5d-b97744afe077`, and `10b17957-3938-2467-88a5-9e9254930dad`.
- E003-M57 tmux session later ended, and M56 verifier reports `sequence_payloads_ready` with ready rows 4 / 4.
- E003-M58 direct current-rescan detector/evaluation bridge design is complete.
- E003-M58 status: `direct_current_rescan_bridge_design_ready`.
- E003-M58 links 7 search-failure query rows, 5 unique bridge targets, 4 current rescans, 29 same-label object targets, and `chair` / `pillow` prompts.
- E003-M58 fixes an M17-compatible detector manifest, target denominator, prompt set, evaluation contract, and E003-M59 command plan.
- E003-M59 direct current-rescan detector bridge Docker run is launched.
- E003-M59 status: `direct_current_rescan_detector_job_launched`.
- E003-M59 background job status: `running`.
- E003-M59 tmux session: `e003_m59_direct_bridge`.
- E003-M59 log path: `logs/20260511_114356_e003_m59_direct_current_rescan_detector_run.log`.
- E003-M59 target scans: 4.
- E003-M59 bridge query rows: 7.
- E003-M59 output path: `experiments/E003_perception_noise_expansion/artifacts/E003-M59_direct_current_rescan_detector_run_v0/`.

## Remaining Issues

사실:

- Paper-table command readiness is still false for real RGB-D/open-vocabulary robustness.
- Real RGB-D/open-vocabulary claim readiness is still false.
- Real navigation `SR` / `SPL` is unsupported.
- Current visibility denominator is a centroid/depth proxy, not true visibility.
- Match-preserving calibration did not reduce M33 false positives.
- E003-M36 confirms deployable fixed hyperparameters are weak.
- E003-M37 confirms dev-selected labelwise caps do not yet transfer safely to heldout scans.
- E003-M37 confirms label-stratified validation is weak under the current 8-scan split because 24 heldout target labels have no dev matched example.
- E003-M38 confirms stronger split design alone is insufficient with the current 8-scan artifact.
- E003-M38 confirms post-hoc spatial/temporal support filtering is not enough for runner integration.
- E003-M39 confirms support evidence must be instrumented before spatial consolidation and caps, not recovered from final selected proposal artifacts.
- E003-M40 confirms support evidence can be produced by the Docker runner and preserved in selected proposal rows.
- E003-M40 does not show that support evidence improves selection quality yet.
- E003-M41 confirms the next test should be soft support-aware scoring, not hard filtering or labelwise support caps.
- E003-M42 confirms the selected score mode is executable but did not improve proposal-quality metrics in the short smoke.
- E003-M43 confirms the next scaled support-aware evaluation should first export a replayable pre-cap candidate pool rather than run a one-off long support-aware Docker job.
- E003-M44 confirms the replayable candidate-pool route works on the short smoke, so scaled score-mode comparison can avoid repeated detector inference.
- E003-M45 applied the frozen hard-pass / weak-positive / fail-redesign criteria and failed both hard pass and weak positive.
- E003-M45 does not support final real RGB-D/open-vocabulary robustness because it is an 8-scan staged artifact with a depth-consistent visibility proxy, no external detector/proposal baseline, no established heldout transfer, and a failed support-aware score result.
- E003-M46 shows bounded support-aware score redesign is not enough: best policy remains `confidence` at 204 / 3210 / 0.059754, and no support-aware variant reaches weak positive.
- E003-M47 selects `Grounded-SAM` as the first external route because it directly tests whether the current box-based depth projection is causing proposal false positives and target losses.
- E003-M48 fixes the `Grounded-SAM` mask-depth proposal contract.
- E003-M50 shows `Grounded-SAM` mask-depth is not yet a positive replacement for the current bbox-depth route on the same subset.
- E003-M52 shows the current artifacts cannot identify the exact per-skipped mask reason: SAM mask absence, low valid mask depth, and other per-candidate projection conditions are not separated.
- E003-M53 shows immediate `OpenMask3D` feasibility is less urgent than search-critical bbox-depth boundary repair under the current evidence.
- E003-M54 shows current M33/M45 detector failures cannot be causally attached to E001/E002 current search instances because detector-ready scans do not overlap with E001 current rescans.
- E003-M54 supports only label-level bridge risk until a dynamic-pair-aligned real-proposal denominator exists.
- E003-M55 shows the smallest direct bridge is not a new external baseline, but staging sequence payloads for the 4 current rescans that already produce `chair` / `pillow` search failures.
- E003-M55 also confirms `OpenMask3D` should wait until the bridge denominator is fixed; otherwise it remains proposal-quality evidence without downstream search causality.
- E003-M56 turns the bridge denominator blocker into a reproducible background job with explicit verification, which is the right shape for top-tier reproducibility.
- E003-M57 launched the background job and the M56 verifier passed, so direct current-rescan detector/evaluation bridge design can start.
- E003-M58 completes that bridge design, and E003-M59 has launched the detector job; no detector output verification or query-level bridge metric has been completed yet.
- E003-M33 took about 3333 seconds for 8 scans / 192 frames on the current setup.

에이전트 추론:

- The largest current technical bottleneck is false-positive load, not prompt coverage.
- M45 shows the current support-aware score is not sufficient; it loses matched targets and does not reduce false positives.
- M46 suggests the next top-tier-relevant improvement should come from stronger proposal/mapping baselines or richer support evidence, not minor score-weight tuning.
- The temporal/spatial support signal failed because it is saturated for both matched and false-positive rows: many false positives also have high temporal/spatial neighbor counts, so boosting support promotes clutter and repeated detector hallucinations rather than true objects.
- `Grounded-SAM` was the correct first external diagnostic route because it was a controlled proposal-backend change; the negative M52 diagnosis means it should not be scaled as-is.
- `OpenMask3D` is stronger as a later 3D instance proposal baseline because it directly tests 3D instance-mask proposal quality.
- `Open3DSG`, `ConceptGraphs`, and `HOV-SG` are better for map/scene-graph/navigation comparisons after proposal quality and search-critical failure boundaries are stabilized.
- The immediate technical question is now how to create a dynamic-pair-aligned bridge so real proposal failures can be evaluated against downstream stale-memory search decisions.
- The largest claim bottleneck is that real perception evidence is diagnostic but not yet paper-table robust.
- The largest top-tier risk is insufficient integration between perception proposals, stale-memory update, and downstream search/navigation decision in one clean benchmark.
- A reviewer defense should state that M45 is a proposal-quality bridge result; top-tier-level robustness requires external baselines and heldout transfer before claiming real RGB-D/open-vocabulary generality.
- Runtime and reproducibility must be treated as first-class concerns: cached inference, resumable jobs, exact Docker commands, and lightweight verification scripts are needed.

사용자 판단 필요:

- No immediate user decision is required. `OpenMask3D` remains the next external 3D instance proposal baseline candidate after the direct bridge is designed or explicitly blocked.

## Reviewer Defense Audit

사실:

- Current evidence supports controlled/proxy dynamic search and diagnostic real-proposal staging, not a final top-tier paper claim.
- E001/E002 are proxy semantic-pair and search-cost experiments; real navigation `SR` / `SPL` remain unsupported.
- E003 real RGB-D/open-vocabulary evidence is diagnostic. E003-M45 support-aware replay failed, `Grounded-SAM mask-depth` was negative on the same-subset comparison, and the running E003-M59 bridge still needs completion verification plus E003-M60 query-level bridge evaluation before supporting search claims.
- External baselines such as `OpenMask3D`, `ConceptGraphs`, `HOV-SG`, `Open3DSG`, `DualMap`, `VLFM`, `HM3D-OVON`, `GOAT-Bench`, and `3D-Mem` have not yet been run.

논문 주장:

- The defensible current contribution candidate is not a better detector or a deployable navigation policy.
- The defensible current contribution candidate is task/staleness-aware semantic memory update for dynamic object search under stale memory and noisy proposals.
- The paper claim should focus on memory trust, re-observation, and candidate visit order improving `ExpectedSearchCost`, proxy `SR`, `AttemptSPL`, and stale old-location failures before claiming real navigation.

에이전트 추론:

- Contribution clarity has improved, but it is not yet paper-ready for top-tier review.
- Reviewer attack 1: novelty may look like heuristic re-ranking. Defense: formalize the stale semantic memory decision model and include ablations for staleness, task context, memory trust, re-observation, reachable-first ordering, and proposal filtering.
- Reviewer attack 2: benchmark/proxy weakness. Defense: clearly separate proxy evidence from real evidence and complete the direct current-rescan detector/evaluation bridge before claiming real RGB-D/open-vocabulary search robustness.
- Reviewer attack 3: small scale. Defense: expand beyond the 8-scan real-proposal artifact after the direct bridge is verified, and report heldout transfer rather than only diagnostic sweeps.
- Reviewer attack 4: perception pipeline weakness. Defense: present M45/M50 failures honestly, add at least one stronger external proposal path such as `OpenMask3D` or `ConceptGraphs`, and avoid claiming detector contribution.
- Reviewer attack 5: missing baselines. Defense: add one open-vocabulary mapping baseline, one dynamic semantic mapping baseline, one search/navigation baseline, and one scene memory baseline before final submission.
- Reviewer attack 6: weak human intent. Defense: keep structured task context as a controlled memory-trust condition; add LLM parsing later only as an adapter if needed.
- Reviewer attack 7: causality gap. Defense: use M54/M55/M57 to connect detector failures to current-rescan search failures, not only label-level overlap.
- Reviewer attack 8: scope creep. Defense: keep the main contribution centered on stale semantic memory update; perception/noise/navigation should serve as evaluation axes.

사용자 판단 필요:

- Later, decide whether the final paper is a focused semantic memory decision paper or a broader mapping-navigation system paper. The broader version needs much heavier baseline and integration work.

## Experiment Plan

Immediate next:

- E003-M59 completion verification
  - wait for tmux `e003_m59_direct_bridge` to exit
  - verify expected files, validator coverage, and matching coverage
- E003-M60 direct current-rescan query-level bridge evaluation
  - join M59 detector proposals with M58 query rows
  - report query-level bridge metrics before making any real RGB-D/open-vocabulary search claim
  - keep `OpenMask3D` as the next external 3D instance proposal baseline after this bridge denominator is staged or blocked
  - keep `Open3DSG`, `ConceptGraphs`, and `HOV-SG` for E005 map/scene-graph/navigation baseline expansion
  - keep real RGB-D/open-vocabulary claim blocked

Short-term:

- Improve real proposal quality:
  - label-specific false-positive suppression
  - prompt/label canonicalization audit
  - confidence/depth support beyond match-preserving baseline
  - proposal clustering and temporal consistency across frames
- Connect real proposal outputs back to E001/E002 query rows.
- Recompute stale-memory search policies with real proposal availability and failure boundaries.

Mid-term:

- E004 task-context memory trust / re-observation decision:
  - keep task context structured first
  - optionally add LLM parsing as an input adapter after the decision contract is stable
- Add stronger baselines:
  - static memory
  - fixed top-k
  - reachable-first
  - detector-confidence-first
  - oracle / upper bound
  - open-vocabulary map baseline if feasible

Top-tier expansion:

- Add real navigation or simulator-backed path execution before claiming real `SR` / `SPL`.
- Scale beyond the current 8 staged scans when detector runtime and failure analysis are under control.
- Add ablations for:
  - task context
  - staleness score
  - motion threshold
  - proposal filtering
  - path/search-cost term
  - re-observation budget
- Add failure analysis tables:
  - target dropped
  - false-positive target pushed down
  - centroid localization exceeded
  - visible-proxy missed
  - disconnected or unreachable candidate

논문 주장 boundary:

- Current supported claim: controlled annotation-proxy robustness and scaled real-proposal diagnostic readiness.
- Current unsupported claims: final real RGB-D/open-vocabulary robustness, deployable search policy, real navigation `SR` / `SPL`, natural-language intention understanding.
