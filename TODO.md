# TODO

Last updated: 2026-05-08

이 파일은 에이전트가 다음 작업 계획과 진행 상태를 관리하는 루트 작업판이다. 자세한 문헌 조사 내용은 `literature/`에 기록하고, 이 파일에는 다음 행동과 상태만 남긴다.

## Rules

- 작업을 시작할 때 이 파일을 먼저 확인한다.
- 작업 중 새 task가 생기면 이 파일에 추가한다.
- 완료한 task는 체크하고, 필요한 상세 내용은 `literature/` 또는 해당 workflow 문서에 기록한다.
- 이 파일은 긴 설명을 담지 않는다. 계획, 상태, 다음 행동만 관리한다.

## Current Phase

Main experiment implementation.

CAND-001은 H001 main experiment implementation 트랙이다. 연구 제약은 6개월~1년으로 수정했고, 최종 목표는 top-tier full paper다. 중간에 독립적인 contribution이 성립하면 workshop, short paper, 또는 관련 venue에 먼저 투고할 수 있다. H001은 `ready_with_constraints`로 main experiment transition을 수락했고, E001 내용은 `experiments/E001_semantic_pair_dynamic_search_proxy/`로 이동했다. E003-M28 cap-aware label-balanced detector policy smoke까지 완료했다. 다음은 E003-M29 Docker pre-cap policy integration rerun gate다. 논문 본문용 실제 구현 실험은 Docker를 기본 실행 환경으로 둔다.

CAND-002와 CAND-003은 parallel backup candidate 트랙이다. 현재 active task는 없고, CAND-001 feasibility가 약해질 때 다시 승격 여부를 판단한다.

## Active Objective

- CAND-001: E003-M29 Docker pre-cap policy integration rerun gate를 준비한다.
- CAND-002: `Common-Ground Semantic Mapping`은 benchmark 설계 부담을 보류 상태로 둔다.
- CAND-003: `Functional Semantic Memory`는 annotation/manipulation evaluation 부담을 보류 상태로 둔다.

## Now

### CAND-001

- No active task.

### CAND-002

- No active task.

### CAND-003

- No active task.

## Next

### CAND-001

- [ ] E003-M29 Docker pre-cap policy integration rerun gate: `cap_aware_label_balanced_ranking_v0`를 detector runner 내부 pre-cap 단계에 통합할 command plan과 rerun 조건 고정

### CAND-002

- [ ] CAND-001 feasibility가 약할 경우 human/robot viewpoint benchmark 가능성을 재검토한다.

### CAND-003

- [ ] CAND-001 feasibility가 약할 경우 FunGraph3D / SceneFun3D 접근성과 annotation 부담을 재검토한다.

## Recently Completed

- [x] Root `.gitignore` 생성 완료: `local_dataset/`, Python cache, env, log/temp/editor byproducts 제외
- [x] Local initial git commit 완료: `Initialize TASMM research workspace`
- [x] E003-M28 cap-aware label-balanced detector policy smoke 완료: `experiments/E003_perception_noise_expansion/tools/run_m28_cap_aware_policy_smoke.py`, status `cap_aware_label_balanced_policy_smoke_ready`, input proposals 1440, label-cleaned proposals 1433, dropped non-prompt labels 7, selected policy `confidence` / per-scan-label cap 24 / spatial consolidation 0.5m, selected proposals 407, matched targets 32 vs baseline 39, false positives 375 vs baseline 1401, precision 0.078624 vs 0.027083, paper-table command ready false, real RGB-D/open-vocabulary claim ready false, next `E003-M29 Docker pre-cap policy integration rerun gate`
- [x] Workspace git repository 연결 완료: local repo initialized on `main`, `origin` set to `https://github.com/Kim-Yoo-Hyun/TASMM.git`, remote fetch checked
- [x] E003-M27 false-positive / cap bottleneck analysis gate 완료: `experiments/E003_perception_noise_expansion/tools/analyze_m27_false_positive_cap_bottleneck.py`, status `false_positive_cap_bottleneck_ready`, evaluated scans/frames 2/24, raw/written predictions 9768/1440, lower-bound cap/post-depth rejected rows 8272, saturated frames 24/24, selected precision 0.028932, selected false-positive rows 1309, same-label over-threshold false positives 1302, calibration false-positive reduction 92, next policy `cap_aware_label_balanced_ranking_v0`, next `E003-M28 cap-aware label-balanced detector policy smoke`
- [x] E003-M26 prompt-expanded multi-scan Docker rerun pilot 완료: `experiments/E003_perception_noise_expansion/tools/summarize_m26_prompt_expanded_rerun.py`, status `prompt_expanded_multiscan_docker_rerun_pilot_ready`, Docker build/run executed true, max scans 2 / max frames per scan 12 / max labels 32, evaluated scans/frames 2/24, raw/written predictions 9768/1440, max predictions reached true, prompt-not-active targets 0/99, matched target rows 39, scan target recall 0.393939, depth-consistent visible-proxy recall 0.628571, proposal precision 0.027083, selected match-preserving calibration precision 0.028932, paper-table command ready false, real RGB-D/open-vocabulary claim ready false
- [x] E003-M25 visibility-aware / prompt-expanded detector rerun gate 완료: `experiments/E003_perception_noise_expansion/tools/plan_m25_visibility_prompt_rerun.py`, status `visibility_prompt_rerun_gate_ready`, M17 staged scans 8, max target label count 30, current max labels 12, expanded max labels 32, current active eval target rows 239/344, expanded active eval target rows 344/344, prompt coverage gain 105 rows, primary calibration policy `m23_full_match_preserving_v0`, pilot Docker config max scans 2 / max frames per scan 12 / max labels 32 / max predictions per frame 60 / max predictions 1440, `run_m23_proposal_calibration.py --selection-policy full_match_preserving` smoke matched target rows 7, paper-table command ready false, real RGB-D/open-vocabulary claim ready false
- [x] E003-M24 visibility-aware detector denominator / prompt-projection calibration gate 완료: `experiments/E003_perception_noise_expansion/tools/run_m24_visibility_prompt_projection_gate.py`, status `visibility_prompt_projection_gate_ready`, evaluated scans/frames 1/6, scan eval targets 51, active M22 prompt target rows 32, prompt-not-active rows 19, centroid frustum-visible rows 8, depth-valid projected rows 7, depth-consistent visible-proxy rows 5, M22 matched target rows 7, M23 selected matched target rows 4, M22 recall over scan/active/depth-consistent denominators 0.137255/0.218750/1.000000, M23 recall over depth-consistent denominator 0.600000, detector/threshold missed depth-consistent visible targets 0, paper-table command ready false, real RGB-D/open-vocabulary claim ready false
- [x] E003-M23 detector proposal consolidation/calibration gate 완료: `experiments/E003_perception_noise_expansion/tools/run_m23_proposal_calibration.py`, status `proposal_calibration_diagnostic_ready`, sweep rows 1188, baseline retained proposals 120, baseline matched target rows 7, baseline false-positive proposal rows 113, baseline proposal precision 0.058333, selected config confidence 0.3 / min depth pixels 500 / NMS radius 1.0m / score mode `confidence`, selected retained proposals 12, selected matched target rows 4, selected false-positive rows 8, selected proposal precision 0.333333, selected fixed label-overlap target recall 0.125000, full-match-preserving precision 0.072165 with 90 false-positive rows, paper-table command ready false, real RGB-D/open-vocabulary claim ready false
- [x] E003-M22 detector frame-scaling/projection diagnostic gate 완료: `experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py`, status `frame_scaling_projection_diagnostic_ready`, Docker build/run executed true, image `research2/real-smoke:latest`, image id `8ada6e0c043e`, max scans 1, max frames per scan 6, max predictions per frame 20, scanned frames 6, frames with written predictions 6, raw predictions 1664, written predictions 120, skipped no-depth predictions 15, validator error/warning rows 0/0, matched proposal/target rows 7/7, false-positive proposal rows 113, proposal precision smoke 0.058333, scan target recall smoke 0.137255, label-overlap target recall smoke 0.218750, mean matched centroid error 0.402223m, paper-table command ready false, real RGB-D/open-vocabulary claim ready false
- [x] E003-M21 detector proposal matching/evaluation gate 완료: `experiments/E003_perception_noise_expansion/tools/evaluate_m21_detector_matching.py`, status `detector_matching_smoke_ready`, input prediction rows 20, evaluated scans 1/8, scan-level evaluation target rows 51, label-overlap target rows 27, matched proposal/target rows 2/2, proposal precision smoke 0.100000, scan target recall smoke 0.039216, label-overlap target recall smoke 0.074074, false-positive proposal rows 18, mean matched centroid error 0.303314m, threshold 1.0m, paper-table command ready false, real RGB-D/open-vocabulary claim ready false
- [x] E003-M20 detector dependency/model smoke 완료: `experiments/E003_perception_noise_expansion/tools/run_m20_detector_model_smoke.py`, image `research2/real-smoke:latest`, image id `03437e313fb3`, size 1.64GB, selected backend `groundingdino_rgbd_backproject_v0`, model `IDEA-Research/grounding-dino-tiny`, status `detector_model_smoke_ready`, Docker build/model smoke executed true, backend contract ready true, model loaded true, inference device `cpu`, scanned frames 1, prediction rows 20, validator error/warning rows 0/0, non-empty detector prediction smoke ready true, detector backend integrated true, detector predictions ready true, paper-table command ready false, real RGB-D/open-vocabulary claim ready false
- [x] E003-M19 real detector backend contract integration 완료: `experiments/E003_perception_noise_expansion/tools/run_m19_real_detector_backend.py`, selected backend `groundingdino_rgbd_backproject_v0`, image `research2/real-smoke:latest`, image id `e06a1c71c950`, status `real_detector_backend_contract_ready`, Docker backend contract smoke executed true, backend contract ready true, RGB-D frame triplets ready 459, missing 0, manifest rows 8, prompt labels 98, detector backend integrated false, detector predictions ready false, paper-table command ready false, real RGB-D/open-vocabulary claim ready false
- [x] E003-M18 Docker image rename/build/run 완료: `python experiments/E003_perception_noise_expansion/tools/run_m18_real_proposal_scaffold.py --build --smoke-run --docker-sudo --sudo-password-stdin`, image `research2/real-smoke:latest`, image id `e06a1c71c950`, size 186MB, status `docker_scaffold_ready`, Docker daemon ready true, build executed true, smoke executed true, Docker smoke validator ready true, prediction rows 0, detector backend integrated false, detector predictions ready false, paper-table command ready false, real RGB-D/open-vocabulary claim ready false
- [x] E003-M18 Dockerized real-proposal detector scaffold 파일 준비 완료: `experiments/E003_perception_noise_expansion/docker/real_proposals/Dockerfile`, `docker/real_proposals/run_rgbd_ov_proposals.py`, `tools/run_m18_real_proposal_scaffold.py`, `tools/validate_real_proposal_output.py`, container runner local smoke ready true, validator smoke ready true
- [x] E003-M17 real-proposal denominator staging 완료: `experiments/E003_perception_noise_expansion/tools/stage_m17_real_proposal_denominator.py`, status `real_proposal_denominator_staged`, ready scans 8, query manifest rows 8, object target rows 460, detector/evaluation target rows 344/344, prompt labels 98, detector target labels 85, detector predictions ready false, real RGB-D/open-vocabulary claim ready false, next `E003-M18 Dockerized real-proposal detector scaffold`
- [x] E003-M16 Dockerized real-proposal route decision 완료: `experiments/E003_perception_noise_expansion/tools/select_m16_real_proposal_route.py`, status `real_proposal_denominator_staging_required`, scan gate rows 54, sequence-ready scans 8, proposal-alignment-ready scans 8, query alignment rows 294, current E001 rescan sequence-ready rows 0, current real RGB-D proposal-ready rows 0, selected route `sequence_ready_scan_bootstrap`, next `E003-M17 real-proposal denominator staging`, proposal schema `real_proposal_prediction_jsonl_v0`, Docker command plan fixed but not paper-table ready
- [x] E003-M15 controlled perception-robustness claim summary 완료: `experiments/E003_perception_noise_expansion/tools/summarize_controlled_claims.py`, profile summary rows 5, claim evidence rows 8, controlled annotation-proxy claim ready true, real RGB-D/open-vocabulary claim ready false, real navigation claim ready false, combined significant moved `routine_fetch` reachable-first identity proxy `SR` 0.606061 vs task-conditioned 0.212121, next `E003-M16 Dockerized real-proposal route decision`
- [x] E003-M14 combined-noise failure-boundary analysis 완료: `experiments/E003_perception_noise_expansion/tools/analyze_combined_boundaries.py`, boundary rows 7938, hard boundary rows 521, target dropped 49, centroid localization exceeded 23, false-positive target pushed-down 117, rank/budget shift no-push 62, false-positive added no-push 604, candidate dropout/score shift 27, significant moved `routine_fetch` reachable-first minus task identity/localization proxy `SR` +0.393939/+0.393939, gain 13, loss 0
- [x] E003-M13 `annotation_combined_moderate_v0` implementation 완료: `experiments/E003_perception_noise_expansion/tools/run_combined_moderate.py`, noisy query rows 1176, noisy candidate rows 5419, prediction rows 10584, failure rows 1621, target dropped rows 49/882, false-positive added rows 837/882, target pushed-down rows 120/882, target rank changed rows 185/882, target jitter exceeds threshold rows 23/882, significant moved `routine_fetch` `task_conditioned_budget_v0` identity/localization proxy `SR` 0.212121/0.212121, `reachable_first_task_conditioned_budget_v0` identity/localization proxy `SR` 0.606061/0.606061
- [x] E003-M12 combined-noise route decision 완료: `experiments/E003_perception_noise_expansion/tools/select_m12_combined_route.py`, selected route `controlled_annotation_proxy_combined_stress`, selected profile `annotation_combined_moderate_v0`, next action `E003-M13_annotation_combined_moderate_v0`, real RGB-D proposal-ready rows 0, real open-vocabulary proposal-ready rows 0, proposal output files 0, Dockerized real proposal route blocked as immediate next
- [x] E003-M11 centroid-jitter failure-boundary analysis 완료: `experiments/E003_perception_noise_expansion/tools/analyze_centroid_jitter_boundaries.py`, boundary rows 7938, hard boundary rows 173, target jitter exceeds threshold rows 123/882, target rank changed rows 139/882, significant moved `routine_fetch` `task_conditioned_budget_v0` identity proxy `SR` 0.696970 / localization proxy `SR` 0.606061, threshold-exceeded subset identity proxy `SR` 1.000000 / localization proxy `SR` 0.000000
- [x] E003-M10 `annotation_centroid_jitter_v0` stress profile 완료: `experiments/E003_perception_noise_expansion/tools/run_centroid_jitter.py`, noisy query rows 1176, noisy candidate rows 4992, prediction rows 10584, target rank changed rows 139/882, target jitter exceeds threshold rows 123/882, significant moved `routine_fetch` `task_conditioned_budget_v0` identity proxy `SR` 0.696970 / localization proxy `SR` 0.606061
- [x] E003-M09 false-positive failure-boundary analysis 완료: `experiments/E003_perception_noise_expansion/tools/analyze_false_positive_boundaries.py`, boundary rows 7938, hard boundary rows 231, target pushed-down rows 96/882, significant moved `routine_fetch` target-pushed-down `task_conditioned_budget_v0` proxy `SR` 0.0, `reachable_first_task_conditioned_budget_v0` proxy `SR` 0.428571, reachable-first success gain 9 / loss 0, next stress profile `annotation_centroid_jitter_v0`
- [x] E003-M08 `annotation_false_positive_v0` stress profile 완료: `experiments/E003_perception_noise_expansion/tools/run_false_positive_stress.py`, noisy query rows 1176, noisy candidate rows 6810, prediction rows 10584, false-positive added rows 837/882, target pushed-down rows 96/882, significant moved `routine_fetch` matched clean `task_conditioned_budget_v0` proxy `SR` 0.625 -> false-positive 0.125, `reachable_first_task_conditioned_budget_v0` false-positive proxy `SR` 0.5
- [x] E003-M07 dropout failure-boundary analysis 완료: `experiments/E003_perception_noise_expansion/tools/analyze_dropout_boundaries.py`, boundary rows 7938, hard boundary rows 294, natural target-retained 754, forced-retained 51, target-dropped 77, strict target-retained rate excluding forced rows 0.854875, next stress profile `annotation_false_positive_v0`
- [x] E003-M06 controlled proposal-dropout implementation 완료: `experiments/E003_perception_noise_expansion/tools/run_proposal_dropout.py`, noisy query rows 1176, noisy candidate rows 4208, prediction rows 10584, target dropped rows 77/882, significant moved `routine_fetch` target-retained `task_conditioned_budget_v0` proxy `SR` 0.8, target-dropped proxy `SR` 0.0
- [x] E003-M05 route selection 완료: `experiments/E003_perception_noise_expansion/tools/select_m05_route.py`, real proposal route blocked, query rows with rescan RGB-D ready 0, proposal output files 0, selected profile `annotation_proposal_dropout_v0`, next `E003-M06_annotation_proposal_dropout_v0`
- [x] Paper-body experiment Docker rule 추가: `AGENTS.md`, `docs/experiments.md`
- [x] E003-M04 robustness/failure analysis 완료: `experiments/E003_perception_noise_expansion/tools/analyze_robustness_failures.py`, transition rows 2646, hard failure rows 29, significant moved `routine_fetch` `task_conditioned_budget_v0` clean-to-jitter proxy `SR` delta -0.090909, noisy `reachable_first` vs noisy task returned-unreachable event delta -0.181818
- [x] E003-M03 noisy policy evaluation 완료: `experiments/E003_perception_noise_expansion/tools/evaluate_noisy_policies.py`, prediction rows 5292, failure rows 466, candidate grid signal rows 2496/2496, significant moved `routine_fetch` jitter `task_conditioned_budget_v0` proxy `SR` 0.636364 / `ExpectedSearchCost` 1.818182 / `AttemptSPL` 0.590909
- [x] E003-M02 annotation-proxy noise generator 완료: `experiments/E003_perception_noise_expansion/tools/build_noise_inputs.py`, noisy query rows 588, noisy candidate rows 2496, target retained 1.000000 for both profiles, `annotation_score_jitter_v0` rank changed 121/294, target rank changed 47/294
- [x] E003-M01 source audit and annotation-proxy noise plan 완료: `experiments/E003_perception_noise_expansion/tools/audit_sources.py`, annotation-proxy ready 294/294 rows, RGB-D sequence query rows 0, E003 open-vocabulary ready rows 0, first profile `annotation_score_jitter_v0`, M02 command/output contract 고정
- [x] E003 perception-noise expansion contract 완료: `experiments/E003_perception_noise_expansion/README.md`, annotation-proxy noise profiles, metric contract, real RGB-D/open-vocabulary gate, real navigation note 정리
- [x] E002 reachable-first semantic grid scoring revision gate 완료: `experiments/E002_path_cost_bridge/tools/evaluate_reachable_first_scoring.py`, target-reachable eval 267 rows, success loss 0, success gain 0, returned-unreachable delta -6, significant `routine_fetch` `SR` 0.777778 유지, returned-unreachable rate 0.111111 -> 0.000000
- [x] E002 source-quality mask and filtered grid-path evaluation 완료: `experiments/E002_path_cost_bridge/tools/evaluate_source_quality_filtered_grid.py`, target-reachable eval 267 rows, source-limited 27 rows, strict all-candidates-reachable 198 rows, target-reachable significant `routine_fetch` `task_conditioned_budget_v0` grid proxy `SR` 0.777778 / oracle 1.000000, naive grid-aware routine `SR` delta -0.111111
- [x] E002 grid-path failure/source analysis 완료: `experiments/E002_path_cost_bridge/tools/analyze_grid_failures.py`, target-unreachable 27 query / 9 base rows, source failures `disconnected_free_space` 15 / `candidate_unprojectable` 6 / `start_unprojectable` 6, returned-unreachable predictions 331, grid-aware success gain 0 / success loss 2, significant moved success gain 0 / success loss 1
- [x] E002 grid-path policy evaluation 완료: `experiments/E002_path_cost_bridge/tools/evaluate_grid_path_policies.py`, 294 query rows, 2646 prediction rows, significant moved `routine_fetch` `task_conditioned_budget_v0` grid proxy `SR` 0.636364 / grid cost 1.339705 / grid `AttemptSPL` proxy 0.622032, `always_top5` `SR` 0.727273, oracle `SR` 0.818182, real navigation path-cost 0 rows
- [x] E002 `occupancy_grid_astar_v0` smoke implementation 완료: `experiments/E002_path_cost_bridge/tools/build_occupancy_grid_paths.py`, 294 query rows, 1248 candidate rows, scan grids 13/13 ready, candidate reachable 1029/1248, target reachable 267/294, real navigation path-cost 0 rows
- [x] E002 claim-boundary summary와 real path-cost source planning 완료: safe claim은 path-cost proxy comparison으로 고정, real navigation claim은 보류, 다음 path source는 `occupancy_grid_astar_v0`
- [x] E002 path-cost policy evaluation 완료: `experiments/E002_path_cost_bridge/tools/evaluate_path_policies.py`, 294 query rows, 2646 prediction rows, 191 failure rows, significant moved `routine_fetch` `task_conditioned_budget_v0` proxy `SR` 0.727273 / path cost 1.718859 / `AttemptSPL` proxy 0.688026, real navigation path-cost 0 rows
- [x] E002 path-cost bridge 준비 완료: `experiments/E002_path_cost_bridge/tools/build_path_cost_inputs.py`, 294 query rows, 1248 candidate rows, `candidate_path_cost_m`, old-location dead-end cost, path-aware candidate visit order 생성, real navigation path cost 0 rows
- [x] Additional pair staging 완료: `5630cfcb` -> `d7d40d75`, rescan semantic triplet staged, ready pairs 12 -> 13, base query rows 94 -> 98, significant moved base rows 10 -> 11, target significant label `vacuum`
- [x] E001 rerun after staging 완료: M01-M04 재실행, status `baseline_ready` / `claim_boundary_ready`, significant moved `task_conditioned_budget_v0` routine `SR` 0.727273 / high-value `SR` 0.909091
- [x] E001 failure analysis / claim-boundary summary 작성 완료: `experiments/E001_semantic_pair_dynamic_search_proxy/tools/analyze_failures.py`, status `claim_boundary_ready`, method failure 7/294, hard cases 7, safe/unsupported claims 고정
- [x] E001 baseline evaluation script / artifact 구현 완료: `experiments/E001_semantic_pair_dynamic_search_proxy/tools/evaluate_baselines.py`, status `baseline_ready`, 2352 predictions, 184 failure rows, significant moved `task_conditioned_budget_v0` routine `SR` 0.727273 / high-value `SR` 0.909091
- [x] E001-M02 query construction script / artifact 구현 완료: `experiments/E001_semantic_pair_dynamic_search_proxy/tools/build_queries.py`, 98 base query rows, 294 context-expanded query rows, 1248 candidate rows, E002/E003/E004-ready fields 포함
- [x] E001-M01 pair manifest script / artifact 구현 완료: `experiments/E001_semantic_pair_dynamic_search_proxy/tools/build_pair_manifest.py`, 1004 manifest rows, 13 `ready_minimal`, 991 blocked, artifacts in `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M01_pair_manifest_v0/`
- [x] E001-M02 query construction 구현 단위 결정 완료: `experiments/E001_semantic_pair_dynamic_search_proxy/README.md`, thresholds / query schema / E002 path-cost / E003 perception / E004 task-context fields 고정
- [x] 연구 방향 업데이트 완료: 6개월~1년 top-tier target, 중간 투고 ladder, E001-E004 확장 경로, beyond-scope 부담 정리
- [x] `experiments/` 생성 및 E001 내용 이동 완료: `docs/experiments.md`는 workflow/rules만 관리, E001 내용은 `experiments/E001_semantic_pair_dynamic_search_proxy/README.md`
- [x] E001 pair manifest 구현 단위 결정 완료: `experiments/E001_semantic_pair_dynamic_search_proxy/README.md`, `E001-M01_pair_manifest_v0`, 1004 metadata pairs / initial 12 minimal-ready pairs, eligibility와 exclusion reasons 고정
- [x] H001 `ready_with_constraints` 수락 및 main experiment implementation 전환 완료: `experiments/E001_semantic_pair_dynamic_search_proxy/`
- [x] H001 main experiment readiness gate 완료: `06_summary.md`, status `ready_with_constraints`, proxy semantic-pair benchmark boundary 고정
- [x] H001 experiment promotion contract 고정 완료: `04_method.md`, `06_summary.md`, target claim / baselines / metrics / non-claims 정리
- [x] H001 budget baseline gate 설계/실행 완료: `artifacts/budget_baseline_gate/`, status `budget_baseline_pass`, `routine_fetch` success/returned-location 0.381112 vs `always_top5` 0.275362, `high_value_fetch`는 `always_top5`와 동일 success 0.988000
- [x] H001 task-context conditioning gate 설계/실행 완료: `artifacts/task_context_gate/`, status `conditioning_pass`, `high_value_fetch` observable-target success 0.988000, utility delta +0.265350, `heavy_noise_stress` / `noisy_high_value_fetch` observable-target success 0.930387
- [x] H001 perception-noise robustness gate 설계/실행 완료: `artifacts/perception_noise_gate/`, status `robustness_pass`, `ranking_noise_moderate` observable-target success 0.904000, `AttemptSPL` proxy 0.644833, low-motion static preserved 1.000000
- [x] H001 search-cost bridge gate 설계/실행 완료: `artifacts/search_cost_bridge_gate/`, status `bridge_pass`, proxy search success 1.000000, `AttemptSPL` proxy 0.883333, mean checked locations 1.300000
- [x] H001 Markdown 병합/정리 완료: 전체 md 7개로 축소, 핵심 파일은 `01_setup.md`~`06_summary.md`와 `README.md`
- [x] H001 strict-pass hypothesis value summary / claim-boundary 정리 완료: `06_summary.md`, safe claim은 `Task-Conditioned Stale Semantic Memory Update`
- [x] H001 12-pair strict rerun 완료: 12 validated pairs, 94 query rows, 10 significant moved rows, `uncertainty_topk_v0` Recall@returned K 1.0000, mean `ExpectedSearchCost` 1.3000
- [x] H001 multi-pair staging / uncertainty top-k / hard-case 분석 완료: 세부 내용은 `03_gates.md`, `05_results.md`
- [x] H001 `non_persistent_anchor_v0`와 `instance_evidence_v0` 계열 hypothesis gate 완료: 세부 내용은 `03_gates.md`, `04_method.md`
- [x] H001 data probe / stale-label schema / value smoke / control / re-observation / pair gate 계열 완료: 세부 내용은 `01_setup.md`, `02_data.md`, `03_gates.md`
- [x] H001 real-pair query / search-region / high-displacement pair smoke 계열 완료: 세부 내용은 `03_gates.md`, `05_results.md`
- [x] `literature/CAND-001.md`에 H001 local feasibility gate partial pass 반영
- [x] `AGENTS.md` 생성 및 Working Language rule 추가
- [x] `docs/hypothesis.md` 생성 및 hypothesis workflow rule 추가
- [x] `docs/index.md` 생성
- [x] `hypothesis/README.md`와 `hypothesis/CAND-001/README.md` 생성
- [x] CAND-001 benchmark shortlist 작성: `hypothesis/CAND-001/01_benchmark_shortlist.md`
- [x] H001 draft 생성: `hypothesis/CAND-001/H001_stale-object-memory/`
- [x] H001 Route B 선택: hypothesis 단계는 full reproduction이 아니라 small probe로 진행
- [x] H001 Route B probe contract 작성: 현재 내용은 `hypothesis/CAND-001/H001_stale-object-memory/01_setup.md`와 `03_gates.md`로 병합
- [x] `DualMap`, `OpenIN`, `OGScene3D`, `LangMap` evaluation notes 보강
- [x] `docs/literature.md`를 새 문헌조사 workflow로 업데이트
- [x] `docs/experiments.md`로 experiment harness 초안 이동
- [x] `docs/paper.md`로 paper protocol 초안 이동
- [x] `literature/README.md`를 field map / trend synthesis / cross-paper insights / open questions 인덱스로 재작성
- [x] `literature/PAPER.md` 생성: paper registry와 reading queue 정리
- [x] `literature/Contribution Candidates.md` 생성
- [x] `literature/CAND-001.md`, `literature/CAND-002.md`, `literature/CAND-003.md` 생성
- [x] 28개 paper folder를 `README.md` 중심 구조로 정리
- [x] 핵심 paper folder 일부에 `01_metadata.md`, `02_paper_card.md`, `03_evaluation.md`, `04_insights.md` 작성
- [x] `literature/research_direction.md`에 current leading candidate 링크와 판단 위치 반영

## Pending / Blocked

- [ ] CAND-001을 최종 thesis direction으로 확정하지 않는다. benchmark/metric/baseline gate가 먼저 필요하다.
- [ ] H001은 main experiment implementation으로 전환됐지만 최종 thesis direction은 아직 확정하지 않는다.
- [ ] `paper/`, `decisions/` 폴더를 아직 만들지 않는다.
- [ ] `experiments/`는 활성화됐지만, 공용 `src/`, `configs/`, `outputs/` 구조는 필요해질 때 만든다.
- [ ] `docs/paper.md`는 논문 작성 단계 전까지 초안 상태로 둔다.
- [ ] Real navigation `SR` / `SPL`은 navmesh, simulator, 또는 trajectory execution source가 준비될 때까지 claim하지 않는다.
- [ ] Direct `docker` command는 현재 사용자에게 daemon permission이 없어 실패한다. E003 Docker command는 필요 시 `--docker-sudo --sudo-password-stdin` 경로를 사용한다.
- [ ] Git push to `origin/main` is blocked until GitHub authentication is available for HTTPS credentials or an authorized SSH key.
