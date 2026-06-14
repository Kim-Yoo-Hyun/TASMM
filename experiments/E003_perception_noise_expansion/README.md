# E003 Perception Noise Expansion

Updated: 2026-05-13

## Status

`E003-M00_contract_v0`, `E003-M01_source_audit_v0`, `E003-M02_annotation_proxy_noise_v0`, `E003-M03_noisy_policy_eval_v0`, `E003-M04_robustness_failure_analysis_v0`, `E003-M05_route_v0`, `E003-M06_annotation_proposal_dropout_v0`, `E003-M07_dropout_failure_boundary_v0`, `E003-M08_annotation_false_positive_v0`, `E003-M09_false_positive_failure_boundary_v0`, `E003-M10_annotation_centroid_jitter_v0`, `E003-M11_centroid_jitter_failure_boundary_v0`, `E003-M12_combined_noise_route_decision_v0`, `E003-M13_annotation_combined_moderate_v0`, `E003-M14_combined_noise_failure_boundary_v0`, `E003-M15_controlled_perception_claim_summary_v0`, `E003-M16_real_proposal_route_decision_v0`, `E003-M17_real_proposal_denominator_staging_v0`, `E003-M18_dockerized_real_proposal_detector_scaffold_v0`, `E003-M19_real_detector_backend_integration_v0`, `E003-M20_detector_model_smoke_v0`, `E003-M21_detector_proposal_matching_v0`, `E003-M22_frame_scaling_projection_diagnostic_v0`, `E003-M23_proposal_consolidation_calibration_v0`, `E003-M24_visibility_prompt_projection_gate_v0`, `E003-M25_visibility_prompt_rerun_gate_v0`, `E003-M26_prompt_expanded_multiscan_docker_rerun_v0`, `E003-M27_false_positive_cap_bottleneck_v0`, `E003-M28_cap_aware_label_balanced_policy_v0`, `E003-M29_pre_cap_policy_integration_gate_v0`, `E003-M30_pre_cap_policy_docker_rerun_v0`, `E003-M31_pre_cap_policy_tradeoff_analysis_v0`, `E003-M32_scaled_pre_cap_rerun_gate_v0`, `E003-M33_scaled_pre_cap_policy_docker_rerun_v0`, `E003-M34_scaled_pre_cap_failure_analysis_v0`, `E003-M35_false_positive_suppression_route_v0`, `E003-M36_recall_preserving_suppression_sweep_v0`, `E003-M37_suppression_split_validation_v0`, `E003-M38_split_or_temporal_spatial_gate_v0`, `E003-M39_temporal_spatial_support_instrumentation_gate_v0`, `E003-M40_temporal_spatial_support_runner_smoke_v0`, `E003-M41_support_aware_selection_policy_gate_v0`, `E003-M42_support_aware_selection_runner_smoke_v0`, `E003-M43_support_aware_scaled_rerun_route_gate_v0`, `E003-M44_pre_cap_candidate_pool_export_smoke_v0`, `E003-M45_scaled_candidate_pool_export_replay_v0`, `E003-M46_score_redesign_or_external_gate_v0`, `E003-M47_external_baseline_feasibility_gate_v0`, `E003-M48_grounded_sam_contract_v0`, `E003-M49_grounded_sam_smoke_v0`, `E003-M50_same_subset_bbox_vs_mask_v0`, `E003-M51_post_m50_route_decision_v0`, `E003-M52_grounded_sam_mask_failure_v0`, `E003-M53_bbox_continuation_repair_gate_v0`, `E003-M54_search_critical_bbox_failure_boundary_v0`, `E003-M55_dynamic_pair_bridge_gate_v0`, `E003-M56_current_rescan_sequence_staging_plan_v0`, `E003-M57_sequence_staging_job_launch_v0`, `E003-M58_direct_current_rescan_bridge_design_v0`, `E003-M59_direct_current_rescan_detector_run_v0`, `E003-M60_direct_current_rescan_query_bridge_v0`, `E003-M61_direct_bridge_rank_failure_gate_v0`, `E003-M62_offline_rerank_budget_repair_v0`, `E003-M63_bounded_repair_integration_gate_v0`, `E003-M64_openmask3d_feasibility_decision_v0`, `E003-M65_openmask3d_scene_format_model_smoke_plan_v0`, `E003-M66_openmask3d_model_smoke_v0` staging/preflight, `E003-M67_openmask3d_checkpoint_env_route_v0`, `E003-M68_openmask3d_checkpoint_download_launch_v0`, checkpoint verification, `E003-M70_openmask3d_docker_env_build_preflight_v0`, final E003-M71 Docker build failure verification, E003-M72 fallback gate, E003-M73 denominator expansion plan, E003-M74 detector completion verification, and E003-M75 expanded direct query-level evaluation are complete with constraints. The immediate next unit is the E004 transition gate.

## Source

- Source hypothesis: `archive/hypothesis/CAND-001/H001_stale-object-memory/`
- Workflow rule: `docs/experiments.md`
- E001 source: `experiments/E001_semantic_pair_dynamic_search_proxy/`
- E002 source: `experiments/E002_path_cost_bridge/`
- Input query artifact: `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M02_query_construction_v0/query_rows.jsonl`
- Input candidate artifact: `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M02_query_construction_v0/candidate_rows.jsonl`
- Optional grid-path candidate input: `experiments/E002_path_cost_bridge/artifacts/E002-M05_occupancy_grid_astar_v0/`
- Optional reachable-first boundary input: `experiments/E002_path_cost_bridge/artifacts/E002-M09_reachable_first_scoring_v0/`

## 사실

- E001 currently provides annotation-level `3RScan` / `3DSSG` semantic-pair dynamic object search rows.
- E001 query rows: 294.
- E001 candidate rows: 1248.
- E001 rows with `e003_rgbd_ready`: 0.
- E001 rows with `e003_open_vocab_ready`: 0.
- E001 rows with `rgbd_sequence_available`: 0.
- Current E001 candidates come from `semseg.v2.json`, not RGB-D detector output.
- Current E001 rows include placeholders: `perception_profile_id`, `proposal_noise_profile_id`, `open_vocab_proposal_source`, `e003_rgbd_ready`, and `e003_open_vocab_ready`.
- E002 provides grid-path proxy metrics and `reachable_first_task_conditioned_budget_v0`, but no real navigation path-cost source.
- Local `3RScan` scan folders include some `sequence.zip` / `sequence/` payloads, but not for the current E001 query rows.
- E003-M01 confirms all 294 E001 query rows are ready for annotation-proxy noise.
- E003-M01 confirms current E001 query rows have 0 RGB-D sequence-ready rows and 0 open-vocabulary-ready rows.
- E003-M02 generates `clean_annotation_oracle_v0` and `annotation_score_jitter_v0` noisy rows.
- E003-M03 evaluates clean vs `annotation_score_jitter_v0` policy outputs for 588 noisy query rows and 2496 noisy candidate rows.
- E003-M03 attaches E002 occupancy-grid candidate reachability to 2496 / 2496 noisy candidate rows.
- E003-M04 analyzes 2646 clean-vs-noisy transition rows and 29 primary-policy hard failure rows.
- E003-M04 confirms the active profile includes no target-drop condition and uses no real RGB-D, open-vocabulary, or real navigation source.
- E003-M05 audits the real proposal route and finds 0 query rows with rescan RGB-D ready, 0 real RGB-D proposal-ready rows, 0 real open-vocabulary proposal-ready rows, and 0 detector/proposal output files.
- E003-M05 selects `annotation_proposal_dropout_v0` as the next controlled proposal-recall stress profile.
- Docker is now the default execution environment for paper-body experiments that require external repos, detectors, simulators, GPU dependencies, system packages, or compiled extensions.
- E003-M06 generates controlled proposal-dropout rows for seeds 11, 17, and 23.
- E003-M06 creates 1176 noisy query rows, 4208 noisy candidate rows, 10584 prediction rows, and 1191 failure rows.
- E003-M06 target-dropped rows under `annotation_proposal_dropout_v0`: 77 / 882, actual target dropped rate 0.087302.
- E003-M06 forced target-retained rows: 51, because the profile preserves at least one candidate per row.
- E003-M07 creates 7938 boundary rows and 294 hard boundary rows.
- E003-M07 separates `natural_target_retained` 754 rows, `forced_retained` 51 rows, and `target_dropped` 77 rows.
- E003-M07 strict target-retained rate excluding forced rows: 0.854875.
- E003-M07 selects `annotation_false_positive_v0` as the next stress profile.
- E003-M08 generates `annotation_false_positive_v0` rows for seeds 31, 37, and 41.
- E003-M08 creates 1176 noisy query rows, 6810 noisy candidate rows, 10584 prediction rows, and 1067 failure rows.
- E003-M08 adds false positives to 837 / 882 stress rows and pushes target rank down in 96 / 882 rows.
- E003-M08 significant moved `routine_fetch` matched clean `task_conditioned_budget_v0` proxy `SR`: 0.625.
- E003-M08 significant moved `routine_fetch` false-positive `task_conditioned_budget_v0` proxy `SR`: 0.125.
- E003-M08 significant moved `routine_fetch` false-positive `reachable_first_task_conditioned_budget_v0` proxy `SR`: 0.5.
- E003-M09 creates 7938 boundary rows and 231 hard boundary rows.
- E003-M09 target pushed-down rows: 96 / 882, rate 0.108844.
- E003-M09 significant moved `routine_fetch` target-pushed-down `task_conditioned_budget_v0`: clean proxy `SR` 0.571429, false-positive proxy `SR` 0.0.
- E003-M09 significant moved `routine_fetch` target-pushed-down `reachable_first_task_conditioned_budget_v0`: clean proxy `SR` 0.571429, false-positive proxy `SR` 0.428571.
- E003-M09 selects `annotation_centroid_jitter_v0` as the next stress profile.
- E003-M10 generates `annotation_centroid_jitter_v0` rows for seeds 43, 47, and 53.
- E003-M10 creates 1176 noisy query rows, 4992 noisy candidate rows, 10584 prediction rows, and 1654 failure rows.
- E003-M10 target rank changed rows: 139 / 882.
- E003-M10 target jitter exceeds threshold rows: 123 / 882.
- E003-M10 significant moved `routine_fetch` `task_conditioned_budget_v0`: identity proxy `SR` 0.696970, localization proxy `SR` 0.606061, `ExpectedSearchCost` 1.757576, `AttemptSPL` 0.621212, utility 0.433333.
- E003-M10 significant moved `routine_fetch` `reachable_first_task_conditioned_budget_v0`: identity proxy `SR` 0.696970, localization proxy `SR` 0.606061, returned-unreachable rate 0.090909.
- E003-M10 keeps identity/rank success separate from localization success and does not recompute occupancy-grid path costs after centroid jitter.
- E003-M11 creates 7938 boundary rows and 173 hard boundary rows.
- E003-M11 confirms `annotation_centroid_jitter_v0` target jitter exceeds threshold rows: 123 / 882.
- E003-M11 confirms `annotation_centroid_jitter_v0` target rank changed rows: 139 / 882.
- E003-M11 significant moved `routine_fetch` `task_conditioned_budget_v0`: identity proxy `SR` 0.696970, localization proxy `SR` 0.606061, identity-localization gap 0.090909.
- E003-M11 significant moved `routine_fetch` threshold-exceeded `task_conditioned_budget_v0`: identity proxy `SR` 1.000000, localization proxy `SR` 0.000000.
- E003-M11 significant moved `routine_fetch` reachable-first minus task delta: identity proxy `SR` 0.000000, localization proxy `SR` 0.000000, returned-unreachable event delta -0.151515.
- E003-M12 selects `controlled_annotation_proxy_combined_stress` as the immediate next route.
- E003-M12 selects `annotation_combined_moderate_v0` as the next profile and `E003-M13_annotation_combined_moderate_v0` as the next executable unit.
- E003-M12 keeps Dockerized real proposal route blocked as immediate next because real RGB-D proposal-ready rows are 0, real open-vocabulary proposal-ready rows are 0, and proposal output files are 0.
- E003-M12 combined profile seed set: 61, 67, 71.
- E003-M12 combined profile moderate parameters: score jitter sigma 0.08, target drop rate 0.10, non-target drop rate 0.20, false-positive candidates 1 to 2, centroid planar sigma 0.18 m, max planar jitter 0.50 m.
- E003-M13 creates 1176 noisy query rows, 5419 noisy candidate rows, 10584 prediction rows, and 1621 failure rows.
- E003-M13 combined stress target dropped rows: 49 / 882.
- E003-M13 combined stress false-positive added rows: 837 / 882.
- E003-M13 combined stress target pushed-down rows: 120 / 882.
- E003-M13 combined stress target rank changed rows: 185 / 882.
- E003-M13 combined stress target jitter exceeds threshold rows: 23 / 882.
- E003-M13 significant moved `routine_fetch` `task_conditioned_budget_v0`: identity proxy `SR` 0.212121, localization proxy `SR` 0.212121, `ExpectedSearchCost` 2.181818, `AttemptSPL` 0.196970, utility -0.115152.
- E003-M13 significant moved `routine_fetch` `reachable_first_task_conditioned_budget_v0`: identity proxy `SR` 0.606061, localization proxy `SR` 0.606061, `ExpectedSearchCost` 1.757576, `AttemptSPL` 0.575758, utility 0.342424.
- E003-M14 creates 7938 boundary rows and 521 hard boundary rows.
- E003-M14 separates combined-noise groups: `target_dropped` 49, `centroid_localization_exceeded` 23, `false_positive_target_pushed_down` 117, `rank_budget_shift_no_push` 62, `false_positive_added_no_push` 604, and `candidate_dropout_or_score_shift` 27.
- E003-M14 significant moved `routine_fetch` paired comparison: `reachable_first_task_conditioned_budget_v0` improves identity/localization proxy `SR` over `task_conditioned_budget_v0` by +0.393939 / +0.393939, with 13 gain rows and 0 loss rows.
- E003-M15 summarizes 5 controlled profiles and 8 claim-evidence rows.
- E003-M15 marks controlled annotation-proxy claim readiness as true.
- E003-M15 marks real RGB-D/open-vocabulary claim readiness and real navigation claim readiness as false.
- E003-M15 sets the next recommended unit to `E003-M16 Dockerized real-proposal route decision`.
- E003-M16 audits 54 scan payloads and 294 query rows for real proposal readiness.
- E003-M16 finds 8 sequence-ready/proposal-alignment-ready scans, but 0 current E001 rescan sequence-ready query rows.
- E003-M16 selects `sequence_ready_scan_bootstrap` and sets the next recommended unit to `E003-M17 real-proposal denominator staging`.
- E003-M16 fixes `real_proposal_prediction_jsonl_v0` and a planned Docker command, but the Docker command is not paper-table ready until E003-M17 staging exists.
- E003-M17 stages a real-proposal detector input denominator from 8 sequence-ready `3RScan` scans.
- E003-M17 creates 8 real-proposal query manifest rows, 460 object target rows, 344 detector target rows, and 344 evaluation target rows.
- E003-M17 prompt set includes 98 labels; detector target labels cover 85 labels.
- E003-M17 copies the fixed `real_proposal_prediction_jsonl_v0` output schema.
- E003-M17 still has 0 detector prediction rows and keeps real RGB-D/open-vocabulary claim readiness false.
- E003-M17 does not require Docker because it only stages repository-local JSON artifacts; E003-M18 detector execution must use Docker.
- E003-M18 creates a Dockerfile, container-side runner, host-side wrapper, and proposal output validator for the real-proposal route.
- E003-M18 validator smoke passes on an empty scaffold output: prediction rows 0, error rows 0, warning rows 0.
- E003-M18 container runner local smoke passes over 8 manifest rows, 459 sampled frames, 344 detector targets, and 98 prompt labels.
- E003-M18 Docker image build/run succeeds through `--docker-sudo --sudo-password-stdin`.
- E003-M18 image `research2/real-smoke:latest` exists with image id `e06a1c71c950` and size 186MB.
- E003-M18 Docker smoke output validates as empty scaffold output with 0 prediction rows, 0 validation errors, and 0 validation warnings.
- E003-M18 uses empty scaffold output only; it does not generate real detector predictions.
- E003-M18 keeps detector backend integrated false, detector predictions ready false, paper-table command ready false, and real RGB-D/open-vocabulary claim ready false.
- E003-M19 selects `groundingdino_rgbd_backproject_v0` as the real-detector backend contract.
- E003-M19 Docker backend-contract smoke validates 459 / 459 sampled RGB-D/color/depth/pose frame triplets over 8 scans.
- E003-M19 explicitly blocks 3DSSG object instance ids, evaluation target ids, `candidate_is_target`, and `matched_3dssg_instance_id` from detector inference.
- E003-M19 keeps detector backend integrated false, detector predictions ready false, paper-table command ready false, and real RGB-D/open-vocabulary claim ready false.
- E003-M20 installs Docker model dependencies for `groundingdino_rgbd_backproject_v0`.
- E003-M20 uses `IDEA-Research/grounding-dino-tiny` through Hugging Face `transformers`.
- E003-M20 image `research2/real-smoke:latest` exists with image id `03437e313fb3` and size 1.64GB.
- E003-M20 Docker model smoke runs on CPU over one sampled RGB-D frame from scan `280d8ebb-6cc6-2788-9153-98959a2da801`.
- E003-M20 writes 20 non-empty detector proposal rows, with validator error rows 0 and validator warning rows 0.
- E003-M20 label canonical counts: chair 8, table 5, plant 2, pillow 2, picture 1, curtain 1, light 1.
- E003-M20 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false because proposal rows are not yet matched/evaluated against the M17 target denominator.
- E003-M21 evaluates M20 proposal rows against M17 target rows using same-scan, same-label centroid matching with threshold 1.0m.
- E003-M21 input prediction rows: 20.
- E003-M21 evaluated scans: 1 / 8.
- E003-M21 scan-level evaluation target rows: 51.
- E003-M21 label-overlap target rows: 27.
- E003-M21 matched proposal/target rows: 2 / 2.
- E003-M21 proposal precision smoke: 0.100000.
- E003-M21 scan target recall smoke: 0.039216.
- E003-M21 label-overlap target recall smoke: 0.074074.
- E003-M21 false-positive proposal rows: 18.
- E003-M21 mean matched centroid error: 0.303314m.
- E003-M21 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false because the result covers only one sampled frame from one scan and uses a non-visibility-filtered scan-level denominator.
- E003-M22 removes the M20 early stop and evaluates 6 sampled frames from scan `280d8ebb-6cc6-2788-9153-98959a2da801`.
- E003-M22 raw predictions: 1664.
- E003-M22 written predictions: 120.
- E003-M22 skipped no-depth predictions: 15.
- E003-M22 frames with written predictions: 6 / 6.
- E003-M22 matched proposal/target rows: 7 / 7.
- E003-M22 false-positive proposal rows: 113.
- E003-M22 proposal precision smoke: 0.058333.
- E003-M22 scan target recall smoke: 0.137255.
- E003-M22 label-overlap target recall smoke: 0.218750.
- E003-M22 mean matched centroid error: 0.402223m.
- E003-M22 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false because it is still one-scan diagnostic output and not a visibility-aware detector benchmark.
- E003-M23 sweeps 1188 confidence/depth-support/NMS/score configurations over the M22 detector proposals.
- E003-M23 selected config uses confidence threshold 0.3, min depth pixels 500, NMS radius 1.0m, and score mode `confidence`.
- E003-M23 selected config retains 12 proposals, matches 4 target rows, leaves 8 false-positive proposal rows, and has proposal precision 0.333333.
- E003-M23 selected config reduces fixed label-overlap target recall from 0.218750 to 0.125000.
- E003-M23 full-match-preserving config keeps all 7 matched target rows but retains 97 proposals and 90 false-positive rows, with proposal precision 0.072165.
- E003-M23 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false because the sweep is one-scan diagnostic output and uses 3DSSG matching only for evaluation.
- E003-M24 separates scan-level target recall into active prompt, centroid-frustum, depth-valid, and depth-consistent visible-proxy denominators.
- E003-M24 scan-level evaluation target rows: 51.
- E003-M24 active M22 prompt target rows: 32.
- E003-M24 prompt-not-active target rows: 19.
- E003-M24 centroid frustum-visible target rows: 8.
- E003-M24 depth-valid projected target rows: 7.
- E003-M24 depth-consistent visible-proxy target rows: 5.
- E003-M24 M22 matched target rows: 7.
- E003-M24 M23 selected matched target rows: 4.
- E003-M24 M22 recall over scan / active prompt / depth-consistent visible-proxy denominators: 0.137255 / 0.218750 / 1.000000.
- E003-M24 M23 recall over depth-consistent visible-proxy denominator: 0.600000.
- E003-M24 detector/threshold missed depth-consistent visible target rows: 0.
- E003-M24 M22 matched outside centroid frustum proxy rows: 2, so centroid projection is only a diagnostic proxy, not true visibility.
- E003-M24 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false because it covers one scan and uses target centroid projection as a proxy.
- E003-M25 fixes expanded max labels at 32.
- E003-M25 M17 staged scans: 8.
- E003-M25 max target label count: 30.
- E003-M25 current prompt cap 12 covers 239 / 344 evaluation target rows.
- E003-M25 expanded prompt cap 32 covers 344 / 344 evaluation target rows.
- E003-M25 prompt coverage gain: 105 rows.
- E003-M25 primary calibration policy: `m23_full_match_preserving_v0`.
- E003-M25 pilot Docker rerun config: max scans 2, max frames per scan 12, max labels 32, max predictions per frame 60, max predictions 1440, threshold/text-threshold 0.08/0.08.
- E003-M25 adds `run_m23_proposal_calibration.py --selection-policy full_match_preserving`; smoke check preserves 7 matched target rows on M22.
- E003-M25 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false because it fixes the rerun contract but does not execute the rerun.
- E003-M26 executes the prompt-expanded Docker rerun over 2 scans and 24 frames.
- E003-M26 run config: max scans 2, max frames per scan 12, max labels 32, max predictions per frame 60, max predictions 1440, threshold/text-threshold 0.08/0.08.
- E003-M26 raw predictions: 9768.
- E003-M26 written predictions: 1440.
- E003-M26 max predictions reached: true.
- E003-M26 not projected or capped predictions: 8272.
- E003-M26 prompt-not-active target rows: 0 / 99.
- E003-M26 matched target rows: 39.
- E003-M26 scan target recall smoke: 0.393939.
- E003-M26 depth-consistent visible-proxy recall: 0.628571.
- E003-M26 proposal precision smoke: 0.027083.
- E003-M26 match-preserving calibration retained / matched / false-positive rows: 1348 / 39 / 1309.
- E003-M26 match-preserving calibration precision: 0.028932.
- E003-M26 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false.
- E003-M27 lower-bound cap/post-depth rejected rows: 8272.
- E003-M27 saturated frames: 24 / 24.
- E003-M27 selected match-preserving precision: 0.028932.
- E003-M27 selected false-positive rows: 1309.
- E003-M27 same-label over-threshold false-positive rows: 1302.
- E003-M27 no-same-label false-positive rows: 7.
- E003-M27 no-target labels with predictions: 2.
- E003-M27 top selected false-positive labels: box 188, chair 185, table 118, plant 117, light 63.
- E003-M27 selected next detector policy: `cap_aware_label_balanced_ranking_v0`.
- E003-M27 next recommended unit: `E003-M28 cap-aware label-balanced detector policy smoke`.
- E003-M27 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false.
- E003-M28 runs an artifact-replay smoke for `cap_aware_label_balanced_ranking_v0` over M26 written proposals.
- E003-M28 input proposal rows: 1440.
- E003-M28 label-cleaned proposal rows: 1433.
- E003-M28 dropped non-prompt label rows: 7.
- E003-M28 selected score mode: `confidence`.
- E003-M28 selected per-scan-label cap: 24.
- E003-M28 selected spatial consolidation radius: 0.5m.
- E003-M28 selected proposal rows: 407.
- E003-M28 selected matched target rows: 32.
- E003-M28 selected false-positive rows: 375.
- E003-M28 selected precision: 0.078624.
- E003-M28 matched target delta vs baseline: -7.
- E003-M28 false-positive reduction vs baseline: 1026.
- E003-M28 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false because it is replayed after M26's detector cap.
- E003-M29 inspects `run_rgbd_ov_proposals.py` and finds the current global cap check at line 355 and current per-frame cap check at line 358, both inside the detector result loop.
- E003-M29 fixes `cap_aware_label_balanced_ranking_v0` runner args: `--candidate-selection-policy`, `--selection-score-mode`, `--pre-cap-per-scan-label-cap`, `--pre-cap-spatial-consolidation-radius-m`, `--require-scan-prompt-label`, `--raw-candidate-collection-cap`, and `--pre-cap-policy-output`.
- E003-M29 fixes the output contract: keep `real_proposal_prediction_jsonl_v0`, add optional policy fields, write `pre_cap_policy_summary.json`, and mirror key counts into `model_smoke.json` / `run_metadata.json`.
- E003-M29 sets the next recommended unit to `E003-M30 pre-cap policy Docker runner implementation/rerun`.
- E003-M29 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false because it does not execute Docker detector inference.
- E003-M30 implements `cap_aware_label_balanced_ranking_v0` inside `run_rgbd_ov_proposals.py` and passes the policy through `run_m22_frame_scaling_diagnostics.py`.
- E003-M30 executes the fixed M26 two-scan / 24-frame Docker pilot with max labels 32, threshold/text-threshold 0.08/0.08, score mode `confidence`, per-scan-label cap 24, and spatial consolidation radius 0.5m.
- E003-M30 raw predictions: 9768.
- E003-M30 projected candidates: 9496.
- E003-M30 policy input candidates: 8969.
- E003-M30 spatial consolidated candidates: 848.
- E003-M30 final written predictions: 830.
- E003-M30 validator error/warning rows: 0 / 0.
- E003-M30 matched target rows: 48, M26 delta +9.
- E003-M30 false-positive proposal rows: 782, M26 delta -619.
- E003-M30 proposal precision: 0.057831, M26 delta +0.030748.
- E003-M30 depth-consistent visible-proxy recall after post-check: 0.857143.
- E003-M30 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false because it is still a two-scan pilot and needs failure/recall tradeoff analysis.
- E003-M31 compares M26/M28/M30 at target, label, and frame level.
- E003-M31 M26/M28/M30 matched target rows: 39 / 32 / 48.
- E003-M31 M30 gains/losses vs M26: 15 / 6 targets.
- E003-M31 stable matched / stable missed targets: 33 / 45.
- E003-M31 M26/M28/M30 false-positive rows: 1401 / 375 / 782.
- E003-M31 top gain labels: clothes +2, kitchen cabinet +2, backpack +1, bag +1, blanket +1.
- E003-M31 top loss label: plant -6.
- E003-M31 top false-positive labels: table 47, chair 42, box 41, light 41, plant 38.
- E003-M31 scaling blockers: two-scan pilot only, remaining scan-level misses, remaining false-positive load, true visibility not implemented, visible-miss labels, recall-loss label, and top false-positive labels.
- E003-M31 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false.
- E003-M32 fixes the scaled pre-cap rerun route as `staged_8scan_24frame_pre_cap_scaled_pilot`.
- E003-M32 selected scans / frames: 8 / 192, from 459 available sampled frames.
- E003-M32 selected evaluation target rows: 344.
- E003-M32 run config: max labels 32, max predictions 10000, max predictions per frame 60, threshold/text-threshold 0.08/0.08, per-scan-label cap 24, spatial consolidation radius 0.5m, raw candidate collection cap 200000.
- E003-M32 estimates 78144 raw predictions and 6640 final prediction rows from the M30 per-frame rate.
- E003-M32 tracks 7 M31 blockers as required post-rerun diagnostics.
- E003-M32 keeps Docker run executed false, paper-table command readiness false, and real RGB-D/open-vocabulary robustness claim readiness false.
- E003-M33 executes the scaled pre-cap Docker rerun over 8 scans and 192 frames.
- E003-M33 estimated detector wall time is 3333 seconds.
- E003-M33 raw / projected / policy-input / spatial-consolidated / final proposal rows: 67639 / 65812 / 60435 / 4284 / 3414.
- E003-M33 validator error/warning rows: 0 / 0.
- E003-M33 matched target rows: 204 / 344.
- E003-M33 false-positive proposal rows: 3210.
- E003-M33 proposal precision: 0.059754.
- E003-M33 scan target recall: 0.593023.
- E003-M33 depth-consistent visible-proxy target rows: 154.
- E003-M33 recall over depth-consistent visible-proxy denominator: 0.915584.
- E003-M33 detector/threshold missed visible-proxy target rows: 13.
- E003-M33 match-preserving calibration changed selected proposals: false.
- E003-M33 top false-positive labels: plant 176, shelf 133, chair 129, sofa 117, table 116, box 111, cabinet 110, lamp 106.
- E003-M33 keeps paper-table command readiness and real RGB-D/open-vocabulary robustness claim readiness false.
- E003-M34 scaled failure analysis resolves the two-scan scale-count blocker but keeps false-positive load and true visibility unresolved.
- E003-M35 selects `recall_preserving_rank_cap_sweep_v0` and the probe `visible_miss_guarded_labelwise_rank_cap_v0`.
- E003-M36 evaluates 56 offline suppression policies over M33 proposals with re-matching after every filter.
- E003-M36 selected deployable 95pct policy `global_rank_cap_le_20`: matched targets 195 / 204, false-positive rows 2819, precision 0.064698.
- E003-M36 selected diagnostic policy `labelwise_rank_cap_oracle_retain_0p95`: matched targets 204 / 204, false-positive rows 1585, precision 0.114030.
- E003-M37 runs a balanced 4/4 scan split validation gate over M33 proposal artifacts.
- E003-M37 heldout baseline: matched targets 97, false-positive rows 1523, precision 0.059877, depth-consistent visible-proxy recall 0.909091.
- E003-M37 dev-selected labelwise policy `dev_selected_visible_miss_guarded_labelwise_rank_cap_v0`: heldout matched targets 81 / 97, false-positive rows 1154, precision 0.065587, matched-target retention 0.835052.
- E003-M37 fixed policy `global_rank_cap_le_22_selected_on_train`: heldout matched targets 97 / 97, false-positive rows 1433, precision 0.063399.
- E003-M37 heldout oracle `heldout_oracle_visible_miss_guarded_labelwise_rank_cap_v0`: heldout matched targets 97 / 97, false-positive rows 979, precision 0.090149.
- E003-M37 label coverage risk: 24 heldout target labels have no dev matched example, so label-stratified validation is not feasible under the current 8-scan split.
- E003-M37 keeps runner integration recommended false, paper-table command readiness false, and real RGB-D/open-vocabulary claim readiness false.
- E003-M38 enumerates 210 split feasibility rows across current 8-scan artifacts.
- E003-M38 best split still leaves 7 heldout target labels and 7 heldout target rows without dev matched examples.
- E003-M38 marks stronger split feasible with current 8 scans false.
- E003-M38 selected dev support policy `spatial_support_or_rank_guard_r1p5m_min3_rank_guard_le_12`: heldout matched targets 89 / 97, false-positive rows 1406, retention 0.917526, precision 0.059532.
- E003-M38 heldout oracle support policy `temporal_support_or_rank_guard_r0p75m_min3_rank_guard_le_20`: heldout matched targets 95 / 97, false-positive rows 1336, precision 0.066387.
- E003-M38 selected route: `temporal_spatial_evidence_instrumentation_required`.
- E003-M38 keeps runner integration recommended false, paper-table command readiness false, and real RGB-D/open-vocabulary claim readiness false.
- E003-M39 status: `temporal_spatial_support_instrumentation_gate_ready`.
- E003-M39 selected route: `docker_runner_pre_consolidation_support_evidence_v0`.
- E003-M39 selected insertion point: `select_cap_aware_label_balanced_candidates.after_cleaned_before_grouped`.
- E003-M39 support policy id: `temporal_spatial_support_evidence_v0`.
- E003-M39 radii: 0.75m, 1.0m, 1.5m, and 2.0m.
- E003-M39 keeps deterministic post-processing route readiness false, Docker run executed false, paper-table command readiness false, and real RGB-D/open-vocabulary claim readiness false.
- E003-M40 status: `temporal_spatial_support_runner_smoke_ready`.
- E003-M40 Docker build/run executed: true / true.
- E003-M40 scans/frames: 1 / 2.
- E003-M40 raw predictions / projected candidates / policy input / final predictions: 736 / 662 / 629 / 95.
- E003-M40 support evidence attached to selected rows: 95 / 95.
- E003-M40 selected rows with spatial / temporal support at any configured radius: 93 / 58.
- E003-M40 support row field errors: 0.
- E003-M40 validator errors/warnings: 0 / 0.
- E003-M40 matched proposals / false positives / proposal precision smoke: 5 / 90 / 0.052632.
- E003-M40 real RGB-D/open-vocabulary claim readiness: false.
- E003-M41 status: `support_aware_selection_policy_gate_ready`.
- E003-M41 selected score mode: `confidence_sqrt_depth_support_temporal_v0`.
- E003-M41 selected route: `support_aware_scoring_before_consolidation_and_final_rank`.
- E003-M41 support hard filter recommended: false.
- E003-M41 support cap change recommended: false.
- E003-M41 long rerun ready: false.
- E003-M42 status: `support_aware_selection_runner_smoke_ready`.
- E003-M42 score mode: `confidence_sqrt_depth_support_temporal_v0`.
- E003-M42 raw predictions / projected candidates / policy input / final predictions: 736 / 662 / 629 / 95.
- E003-M42 support evidence attached to selected rows: 95 / 95.
- E003-M42 validator errors/warnings: 0 / 0.
- E003-M42 matched proposals / false positives / proposal precision smoke: 5 / 90 / 0.052632.
- E003-M42 matched/false-positive/precision delta vs E003-M40: 0 / 0 / 0.0.
- E003-M42 real RGB-D/open-vocabulary claim readiness: false.
- E003-M43 status: `support_aware_scaled_rerun_route_gate_ready`.
- E003-M43 selected route: `pre_cap_candidate_pool_export_then_offline_replay_v0`.
- E003-M43 M42 vs M40 common selected rows: 94 / 95.
- E003-M43 M42 vs M40 selected symmetric difference rows: 2.
- E003-M43 M42 vs M40 pre-cap rank changed common rows: 68.
- E003-M43 M42 vs M40 selection-score changed common rows: 89.
- E003-M43 existing candidate-pool replay available: false.
- E003-M43 immediate support-aware long rerun recommended: false.
- E003-M43 runner edit required before next scaled run: true.
- E003-M44 status: `pre_cap_candidate_pool_replay_smoke_ready`.
- E003-M44 Docker smoke status: `pre_cap_candidate_pool_export_smoke_ready`.
- E003-M44 candidate pool rows: 629.
- E003-M44 candidate pool rows with support policy: 629 / 629.
- E003-M44 runner selected rows / offline replay selected rows: 95 / 95.
- E003-M44 ordered / set reproduction for `confidence_sqrt_depth_support_temporal_v0`: true / true.
- E003-M44 validator errors/warnings: 0 / 0.
- E003-M45 long-running Docker export/replay job completed from tmux session `e003_m45_scaled_pool`.
- E003-M45 log: `logs/20260508_155219_e003_m45_scaled_candidate_pool_export_replay_tmux.log`.
- E003-M45 output path: `experiments/E003_perception_noise_expansion/artifacts/E003-M45_scaled_candidate_pool_export_replay_v0/`.
- E003-M45 verification status: `scaled_candidate_pool_replay_ready`.
- E003-M45 frozen contract verdict: `fail_redesign`.

## 논문 주장

E003-M00 can support:

- a clear split between controlled annotation-proxy perception noise and real RGB-D / open-vocabulary perception claims.
- a metric contract for testing whether stale-memory update behavior survives proposal noise.
- a staged route from annotation-proxy noise to real perception proposals.

E003-M01 can support:

- starting E003 with controlled annotation-proxy proposal noise.
- using `clean_annotation_oracle_v0` as the reference profile.
- using `annotation_score_jitter_v0` as the first executable stress profile.
- blocking real RGB-D / open-vocabulary robustness claims until aligned proposal sources are available.

E003-M02 can support:

- controlled annotation-proxy score/rank noise input generation.
- target-preserving ranking-noise stress tests.
- clean/noisy profile separation for robustness delta evaluation.

E003-M03 can support:

- controlled annotation-proxy ranking-noise policy evaluation.
- comparing `scene_aligned_static_map`, fixed top-k, `task_conditioned_budget_v0`, `reachable_first_task_conditioned_budget_v0`, and oracle behavior under clean/noisy profiles.
- reporting robustness delta for proxy `SR`, `ExpectedSearchCost`, `AttemptSPL`, task utility, stale old-location FP, and returned-unreachable attempts.

E003-M04 can support:

- clean-vs-noisy transition analysis under `annotation_score_jitter_v0`.
- hard failure boundary separation between rank-noise regression and persistent budget failure.
- the claim that `reachable_first_task_conditioned_budget_v0` can reduce noisy returned-unreachable events relative to `task_conditioned_budget_v0` without recovering the ranking-noise success drop.

E003-M05 can support:

- selecting the next controlled proposal-recall stress route after real RGB-D/open-vocabulary proposal-source audit.
- blocking real RGB-D/open-vocabulary robustness claims until detector/proposal sources are staged.
- choosing `annotation_proposal_dropout_v0` because M04 tested rank-only noise and did not include target-drop/proposal-recall failure.

E003-M06 can support:

- controlled annotation-proxy proposal-recall stress evaluation.
- separating `target_retained_eval` and `target_dropped_eval` denominators.
- reporting how much target-drop failure affects proxy `SR`, `ExpectedSearchCost`, `AttemptSPL`, and task utility.

E003-M07 can support:

- controlled annotation-proxy proposal-recall boundary analysis.
- separating `natural_target_retained`, `forced_retained`, and `target_dropped` denominators.
- treating target-dropped rows as a proposal-recall ceiling rather than a recoverable stale-memory update failure.
- selecting `annotation_false_positive_v0` as the next controlled stress profile because dropout can remove distractors and make retained-denominator ranking easier.

E003-M08 can support:

- controlled annotation-derived false-positive contamination stress evaluation.
- keeping target presence fixed while adding distractors, so failures are ranking/budget contamination failures rather than proposal-recall failures.
- showing that `reachable_first_task_conditioned_budget_v0` is less damaged than `task_conditioned_budget_v0` under the current false-positive stress profile.

E003-M09 can support:

- controlled annotation-derived false-positive failure-boundary analysis.
- separating `target_pushed_down`, `false_positive_added_no_push`, and `no_false_positive_available` rows.
- claiming that `reachable_first_task_conditioned_budget_v0` reduces false-positive damage relative to `task_conditioned_budget_v0` in significant moved `routine_fetch`.
- selecting `annotation_centroid_jitter_v0` before any combined-noise profile.

E003-M10 can support:

- controlled annotation-proxy centroid localization jitter stress evaluation.
- separating identity/rank success from localization success under jittered candidate centroids.
- treating over-jittered correct-target returns as localization failures rather than identity failures.
- selecting centroid-jitter failure-boundary analysis before any combined-noise profile.

E003-M11 can support:

- controlled annotation-proxy centroid-jitter failure-boundary analysis.
- reporting identity retrieval and spatial localization as separate success metrics under centroid noise.
- treating correct-target identity success with over-threshold centroid error as localization failure.
- selecting a combined-noise route decision before any larger perception-noise claim.

E003-M12 can support:

- selecting `annotation_combined_moderate_v0` as the next controlled perception-like stress route.
- keeping real RGB-D/open-vocabulary claims blocked until Dockerized proposal generation and alignment are staged.
- fixing the combined-noise implementation contract without claiming new metric results.

E003-M13 can support:

- controlled annotation-proxy combined perception-like stress evaluation.
- testing interaction between proposal dropout, annotation-derived false positives, score/rank jitter, and centroid jitter.
- reporting identity proxy `SR`, localization proxy `SR`, `ExpectedSearchCost`, `AttemptSPL`, task utility, proposal recall, target-drop rate, false-positive contamination, and target-rank/jitter boundaries in one profile.
- selecting combined-noise failure-boundary analysis before treating this as a paper-level robustness claim.

E003-M14 can support:

- controlled annotation-proxy combined-noise failure-boundary analysis.
- separating proposal-recall ceilings, distractor rank/budget failures, score/rank shifts, and centroid-localization failures.
- claiming that `reachable_first_task_conditioned_budget_v0` improves significant moved `routine_fetch` identity/localization proxy `SR` over `task_conditioned_budget_v0` under combined annotation-proxy stress.

E003-M15 can support:

- writing E003 as a controlled annotation-proxy perception/proposal-noise robustness suite.
- keeping target-drop, false-positive rank/budget, and centroid-localization failures as separate denominator families.
- treating `reachable_first_task_conditioned_budget_v0` as the strongest current method signal under false-positive and combined stress.
- blocking real RGB-D/open-vocabulary and real navigation claims until the Dockerized proposal/navigation routes are staged.

E003-M16 can support:

- selecting `sequence_ready_scan_bootstrap` as the next real-proposal staging route.
- stating that current E001 query rows have 0 current-rescan real RGB-D proposal-ready rows.
- using the fixed `real_proposal_prediction_jsonl_v0` schema and Docker command plan as the contract for later detector execution.
- blocking real RGB-D/open-vocabulary robustness results until E003-M17 denominator staging and a Dockerized detector smoke run are complete.

E003-M17 can support:

- real RGB-D/open-vocabulary detector input staging.
- saying that sequence-ready `3RScan` scans can now be passed to a Dockerized detector using a fixed manifest, prompt set, and output schema.
- blocking real perception robustness results until detector predictions are generated and validated.

E003-M18 can support:

- a Docker execution contract for later real RGB-D/open-vocabulary proposal generation.
- schema validation for future `real_proposal_prediction_jsonl_v0` outputs.
- blocking paper-table use until Docker build/run and non-empty detector predictions are available.
- confirming that the scaffold image can be built and run against the E003-M17 mounted inputs.

E003-M19 can support:

- selecting `groundingdino_rgbd_backproject_v0` as the concrete real-detector backend contract.
- confirming that E003-M17 RGB-D frames, depth frames, poses, intrinsics, and prompt set are consumable inside the Docker route.
- blocking detector performance and real perception robustness claims until model inference produces non-empty validated predictions.

E003-M20 can support:

- a Dockerized non-empty model prediction smoke for the selected real-detector route.
- saying that `groundingdino_rgbd_backproject_v0` can load model dependencies, consume RGB-D sequence inputs, and emit schema-valid proposal rows.
- blocking real perception robustness and proposal-recall claims until detector proposals are matched/evaluated against the target denominator.

E003-M21 can support:

- a first detector-to-denominator matching gate for M20 proposal rows.
- reporting smoke-level proposal precision, target recall, false-positive count, and centroid-localization error.
- blocking real RGB-D/open-vocabulary robustness claims until detector inference covers more frames/scans and uses a visibility-aware denominator.

E003-M22 can support:

- separating frame coverage, projection loss, and matching failure after removing the M20 early stop.
- showing that frame coverage alone is not the current bottleneck: all 6 sampled frames produce predictions, but false positives remain high.
- selecting proposal consolidation/calibration before wider scan scaling.

E003-M23 can support:

- a confidence/depth-support/NMS calibration diagnostic over M22 detector proposals.
- showing that naive calibration can improve proposal precision but trades away target recall under the current one-scan setup.
- selecting visibility-aware target denominator and prompt/projection calibration before paper-table real perception metrics.

E003-M24 can support:

- separating scan-level target recall from active-prompt and visibility-proxy denominators.
- showing that M22 low scan-level recall is partly a denominator/prompt-budget issue, not only detector failure.
- showing that M23 threshold/NMS calibration drops some matched targets and needs match-preserving calibration before paper-table scaling.

E003-M25 can support:

- fixing the prompt-expanded real-detector rerun contract.
- selecting a match-preserving calibration policy before evaluating expanded prompt recall.
- defining the post-rerun denominator and calibration commands that must run before any real RGB-D/open-vocabulary claim.

E003-M26 can support:

- saying that the prompt-expanded Docker route produces non-empty multi-scan RGB-D/open-vocabulary proposal artifacts under the fixed schema.
- saying that prompt coverage is no longer the immediate blocker for the two-scan pilot because prompt-not-active target rows are 0.
- blocking paper-table real RGB-D/open-vocabulary robustness claims until false-positive/cap/projection bottlenecks are separated.

E003-M27 can support:

- diagnosing that M26 is blocked by prediction cap pressure and false-positive domination rather than prompt coverage.
- selecting `cap_aware_label_balanced_ranking_v0` as the next detector policy direction.
- blocking wider paper-table scaling until label mapping cleanup, pre-cap ranking, per-label caps, and same-label spatial consolidation are smoke-tested.

E003-M28 can support:

- an artifact-replay diagnostic that `cap_aware_label_balanced_ranking_v0` can reduce written-proposal false positives under the M26 denominator.
- deciding to move the policy into the Docker runner before the detector's per-frame/global cap.
- blocking real perception robustness claims until the policy is executed pre-cap in Docker and re-evaluated.

E003-M29 can support:

- locating the current pre-policy cap sites in `run_rgbd_ov_proposals.py`.
- fixing the runner args and output contract for pre-cap `cap_aware_label_balanced_ranking_v0`.
- defining the next Docker rerun gate while keeping detector-result claims unsupported.

E003-M30 can support:

- saying the pre-cap policy executes inside the Docker detector runner under fixed M26 pilot conditions.
- saying schema-valid pre-cap policy outputs can be matched against the M17 target denominator.
- reporting a two-scan pilot improvement over M26 in matched targets, false positives, and proposal precision.

E003-M31 can support:

- target/label/frame-level comparison between M26, M28, and M30.
- a two-scan diagnostic claim that M30 improves the M26 recall/precision tradeoff.
- identifying scale and label-specific blockers before wider detector evaluation.

E003-M32 can support:

- fixing the scaled rerun scope and command contract for `cap_aware_label_balanced_ranking_v0`.
- tracking M31 blockers explicitly before treating the pre-cap policy as a paper-table detector result.
- selecting `E003-M33 scaled pre-cap policy Docker rerun` as the next executable unit.

E003-M33 can support:

- saying the Dockerized `cap_aware_label_balanced_ranking_v0` route scales from the two-scan pilot to 8 staged `3RScan` scans under a fixed schema.
- a scaled diagnostic result with detector proposals, match-preserving calibration, and visibility-proxy denominator post-check.
- selecting scaled failure analysis before any paper-table real RGB-D/open-vocabulary claim.

E003-M34 can support:

- saying the previous two-scan scale-count blocker is resolved.
- saying false-positive load remains the main unresolved quality blocker.
- selecting `E003-M35 false-positive suppression route decision` before connecting real proposals to E001/E002 search-policy tables.

E003-M35 can support:

- selecting `recall_preserving_rank_cap_sweep_v0` as the first false-positive suppression route.
- saying an M33-derived visible-miss-guarded labelwise rank-cap probe preserves 204 / 204 matched targets while reducing false-positive rows from 3210 to 1782.
- selecting `E003-M36 recall-preserving suppression sweep smoke` before any Docker rerun or paper-table real RGB-D/open-vocabulary claim.

E003-M36 can support:

- saying an offline suppression sweep was executed over M33 proposal artifacts with re-matching after every filter.
- saying deployable fixed hyperparameters provide only modest recall-preserving gain: `global_rank_cap_le_20` keeps 195 / 204 matched targets and reduces false-positive rows from 3210 to 2819.
- saying labelwise diagnostic caps show a larger ceiling: `labelwise_rank_cap_oracle_retain_0p95` keeps 204 / 204 matched targets and reduces false-positive rows from 3210 to 1585.
- selecting `E003-M37 suppression split validation gate` before Docker runner integration or paper-table real RGB-D/open-vocabulary claim.

E003-M37 can support:

- saying suppression policy selection was tested under a balanced scan-level dev/heldout split.
- saying dev-selected labelwise caps do not yet transfer safely to heldout scans because matched-target retention drops to 0.835052.
- saying fixed global rank caps transfer recall better but provide too little false-positive reduction for runner integration.
- selecting `E003-M38 stronger split or temporal-spatial suppression gate` before Docker runner integration or paper-table real RGB-D/open-vocabulary claim.

E003-M38 can support:

- saying stronger split design alone is not enough with the current 8-scan artifact because every feasible split leaves uncovered heldout target labels.
- saying post-hoc support-feature filtering is not ready for Docker runner integration because dev-selected heldout retention drops to 0.917526.
- selecting `E003-M39 temporal-spatial support instrumentation gate` before another Docker rerun or real RGB-D/open-vocabulary paper-table claim.

E003-M39 can support:

- saying temporal/spatial support evidence should be instrumented before spatial consolidation and caps in the Docker runner.
- saying deterministic post-processing over final selected proposal artifacts is insufficient for this support route.
- selecting `E003-M40 temporal-spatial support runner implementation smoke`.

E003-M40 to E003-M42 can support:

- saying runner-side support evidence and support-aware scoring are executable in the Dockerized proposal path.
- saying `confidence_sqrt_depth_support_temporal_v0` did not improve matched proposals, false positives, or precision in the 1-scan / 2-frame smoke relative to E003-M40.
- selecting `E003-M43 support-aware scaled rerun route gate` before any longer support-aware rerun or real RGB-D/open-vocabulary paper-table claim.

E003-M43 can support:

- saying an immediate support-aware long rerun is not the best next step because it would not preserve a replayable candidate pool for ablations.
- saying existing M40/M42 artifacts cannot support offline score replay because they store final selected proposals, not the cleaned pre-cap candidate pool.
- selecting `E003-M44 pre-cap candidate-pool export and offline replay harness smoke`.

E003-M44 can support:

- saying the runner can export a cleaned, support-instrumented pre-cap candidate pool.
- saying offline replay can reproduce runner-selected stable candidates for `confidence_sqrt_depth_support_temporal_v0`.
- selecting `E003-M45 scaled candidate-pool export and support-aware replay`.

E003-M00 cannot support:

- real RGB-D perception robustness.
- open-vocabulary perception robustness.
- deployable search policy.
- real navigation `SR` / `SPL`.
- natural-language intention understanding.

Target E003 claim after implementation:

- `Task-Conditioned Stale Semantic Memory Update` remains useful under controlled perception/proposal noise by preserving low-motion memories, suppressing stale old-location returns, and adapting candidate budget under task context.

Claim that requires later real perception:

- The method is robust to RGB-D or open-vocabulary perception outputs.

## E003 Contract

| Field | Required content |
| --- | --- |
| question | Does the E001/E002 stale semantic-memory search behavior remain stable when current object proposals are degraded by perception-like noise? |
| hypothesis | `task_conditioned_budget_v0` and `reachable_first_task_conditioned_budget_v0` should degrade gracefully under controlled proposal noise, with lower stale old-location FP and better task utility than fixed baselines. |
| dataset | E001 M02 query/candidate artifacts, E002 M05 occupancy-grid candidate artifacts, E002 M09 reachable-first boundary artifacts, and local `3RScan` / `3DSSG` payloads. |
| method | Generate noisy candidate sets from annotation candidates using declared noise profiles; evaluate existing policies without using target identity except for metric computation and oracle upper bound. |
| comparison | `scene_aligned_static_map`, `always_top1`, `always_top3`, `always_top5`, `fixed_uncertainty_topk_v0`, `task_conditioned_budget_v0`, `reachable_first_task_conditioned_budget_v0`, and oracle upper bound. |
| metrics | proposal recall, candidate contamination, stale old-location FP, low-motion preservation, proxy `SR`, `ExpectedSearchCost`, grid cost when available, `AttemptSPL` proxy, task utility, robustness delta from clean. |
| command | Current executable commands include the E003 toolchain in `experiments/E003_perception_noise_expansion/tools/`, including `run_m22_frame_scaling_diagnostics.py`, `run_m23_proposal_calibration.py`, `run_m24_visibility_prompt_projection_gate.py`, `plan_m32_scaled_pre_cap_rerun.py`, `summarize_m33_scaled_pre_cap_policy_rerun.py`, `run_m36_recall_preserving_suppression_sweep.py`, `run_m37_suppression_split_validation.py`, `plan_m38_split_or_temporal_spatial_gate.py`, and `validate_real_proposal_output.py`. |
| output | noise manifest, noisy candidate rows, noisy predictions, metrics, failure rows, coverage, and report. |
| conclusion | Claim supported only if robustness deltas are reported with explicit noise profile, seed, denominator, dropped-target rate, and non-claims. |

## Noise Profile Contract

### `clean_annotation_oracle_v0`

사실:

- Source candidates are unchanged E001 annotation candidates.
- `proposal_noise_profile_id`: `clean_annotation_oracle_v0`.
- This is the clean reference condition.

논문 주장:

- Can be used as the no-noise upper reference for annotation-proxy experiments.

### `annotation_score_jitter_v0`

사실:

- Perturbs candidate score/rank while preserving target presence.
- Does not change candidate centroids or labels.
- Tests ranking robustness separately from proposal recall.

논문 주장:

- Can support robustness to score/rank uncertainty, not detector recall.

### `annotation_proposal_dropout_v0`

사실:

- Drops candidates with a fixed seed and noise level.
- Can include a target-drop condition, but target-drop rows must be reported separately.
- Tests proposal recall sensitivity.

논문 주장:

- Can support controlled proposal-recall robustness only if target-retained and target-dropped denominators are separated.

### `annotation_false_positive_v0`

사실:

- Adds distractor candidates from same-label or semantically nearby annotation objects.
- Does not use detector hallucinations from images.
- Tests candidate contamination and ambiguity.

논문 주장:

- Can support robustness to annotation-derived false positives, not real open-vocabulary hallucination.

### `annotation_centroid_jitter_v0`

사실:

- Perturbs candidate centroids within a declared distance distribution.
- Uses E002 path/grid cost when available to measure path-cost sensitivity.

논문 주장:

- Can support localization-noise robustness under annotation-proxy assumptions.

### `annotation_combined_moderate_v0`

사실:

- Combines score jitter, candidate dropout, false positives, and centroid jitter.
- Selected by E003-M12 as the next controlled stress profile after individual boundaries.
- Seed set: 61, 67, 71.
- Score jitter sigma: 0.08.
- Target drop rate: 0.10.
- Non-target drop rate: 0.20.
- False-positive candidates per row: 1 to 2.
- Centroid planar sigma: 0.18 m.
- Max planar jitter: 0.50 m.

논문 주장:

- Can support controlled perception-like robustness, not real RGB-D/open-vocabulary robustness.

## Metric Contract

Primary metrics:

- `proposal_recall`: target retained in the noisy candidate set.
- `target_retained_eval_SR`: policy success over target-retained rows.
- `target_dropped_rate`: fraction of rows where the target is unavailable to non-oracle policies.
- stale old-location FP.
- low-motion preservation.
- `ExpectedSearchCost`.
- proxy `SR`.
- grid proxy `SR` when E002 path rows are available.
- `AttemptSPL` proxy.
- task utility.
- robustness delta against `clean_annotation_oracle_v0`.

Secondary diagnostics:

- candidate count delta.
- false-positive count.
- noisy target rank.
- returned false-positive rate.
- hard-label concentration.
- row-band split: `significant_moved`, `mid_motion_review`, `low_motion_control`.
- task-context split: `routine_fetch`, `high_value_fetch`, `noisy_high_value_fetch`.

## Planned Units

| Unit | Goal | Output |
| --- | --- | --- |
| E003-M00 | contract and claim boundary | this README |
| E003-M01 | source audit and executable input plan | complete: sequence/open-vocabulary readiness report, selected first profile |
| E003-M02 | annotation-proxy noise generator | complete: noise manifest, noisy query/candidate rows |
| E003-M03 | noisy policy evaluation | complete: predictions, metrics, failure rows |
| E003-M04 | robustness/failure analysis | complete: claim boundary and next validation requirements |
| E003-M05 | real proposal source or proposal-recall stress route | complete: selected `annotation_proposal_dropout_v0` |
| E003-M06 | controlled proposal-dropout implementation | complete: noisy rows and target-retained/target-dropped metrics |
| E003-M07 | dropout failure-boundary analysis | complete: strict denominator boundary and next `annotation_false_positive_v0` decision |
| E003-M08 | false-positive candidate contamination stress | complete: implementation contract and executable profile |
| E003-M09 | false-positive failure-boundary analysis | complete: matched clean / false-positive transition boundary |
| E003-M10 | centroid localization jitter stress | complete: implementation contract and executable profile |
| E003-M11 | centroid-jitter failure-boundary analysis | complete: identity/localization transition boundary |
| E003-M12 | combined-noise route decision | complete: selected `annotation_combined_moderate_v0`, deferred Dockerized real proposal route |
| E003-M13 | combined moderate implementation | complete: noisy rows, predictions, metrics, failure rows |
| E003-M14 | combined-noise failure-boundary analysis | complete: interaction boundary and claim decision |
| E003-M15 | controlled perception-robustness claim summary | complete: supported claims, non-claims, real-proposal promotion boundary |
| E003-M16 | Dockerized real-proposal route decision | complete: source selection, alignment gate, proposal schema, Docker command plan |
| E003-M17 | real-proposal denominator staging | complete: sequence-ready scan bootstrap query manifest, prompt set, target denominator |
| E003-M18 | Dockerized real-proposal detector scaffold | complete: Dockerfile, container runner, host wrapper, image build, Docker smoke, validator smoke |
| E003-M19 | real detector backend integration | complete: selected backend contract, RGB-D frame access smoke, blocked evaluation-only inputs |
| E003-M20 | detector dependency/model smoke | complete: Docker dependency build, model load, non-empty schema-valid proposal rows |
| E003-M21 | detector proposal matching/evaluation gate | complete: one-frame detector-to-target matching smoke |
| E003-M22 | detector frame-scaling/projection diagnostic gate | complete: multi-frame matching and projection/frame coverage diagnostic |
| E003-M23 | detector proposal consolidation/calibration gate | complete: confidence/depth support/NMS/threshold sweep and recall-precision tradeoff diagnostic |
| E003-M24 | visibility-aware detector denominator / prompt-projection calibration gate | complete: active-prompt / frustum / depth-consistent denominator diagnostic |
| E003-M25 | visibility-aware / prompt-expanded detector rerun gate | complete: prompt cap, denominator contract, match-preserving calibration, and Docker rerun command plan |
| E003-M26 | prompt-expanded multi-scan Docker rerun pilot | complete: Docker rerun, match-preserving calibration, visibility denominator post-check, summary |
| E003-M27 | false-positive / cap bottleneck analysis gate | complete: max prediction cap, false-positive domination, projection/capping loss, calibration limit, and next detector policy decision |
| E003-M28 | cap-aware label-balanced detector policy smoke | complete: written-proposal replay policy sweep and next pre-cap Docker integration decision |
| E003-M29 | Docker pre-cap policy integration rerun gate | complete: runner insertion points, args contract, output contract, and rerun gate |
| E003-M30 | pre-cap policy Docker runner implementation/rerun | complete: runner implementation, wrapper pass-through, Docker rerun, calibration, visibility post-check, summary |
| E003-M31 | pre-cap policy failure/recall tradeoff analysis | complete: target/label/frame tradeoff rows and scaling blockers |
| E003-M32 | scaled pre-cap policy rerun gate | complete: 8-scan / 24-frame scaled rerun scope and command plan |
| E003-M33 | scaled pre-cap policy Docker rerun | complete: detector rerun, match-preserving calibration, visibility post-check, summary |
| E003-M34 | scaled pre-cap failure and label analysis | complete: label failures, visible-proxy misses, and M31 blocker resolution |
| E003-M35 | false-positive suppression route decision | complete: selected `recall_preserving_rank_cap_sweep_v0` |
| E003-M36 | recall-preserving suppression sweep smoke | complete: offline sweep over M33 proposals with re-matching |
| E003-M37 | suppression split validation gate | complete: balanced 4/4 scan split validation and runner integration decision |
| E003-M38 | stronger split or temporal-spatial suppression gate | complete: split feasibility and post-hoc support transfer route decision |
| E003-M39 | temporal-spatial support instrumentation gate | complete: support field contract and runner insertion point fixed |
| E003-M40 | temporal-spatial support runner smoke | complete: support fields implemented and short Docker smoke passed |
| E003-M41 | support-aware selection policy gate | complete: selected `confidence_sqrt_depth_support_temporal_v0` |
| E003-M42 | support-aware selection runner smoke | complete: selected score mode implemented and short Docker smoke passed |
| E003-M43 | support-aware scaled rerun route gate | complete: selected candidate-pool export and offline replay route |
| E003-M44 | pre-cap candidate-pool export and offline replay harness smoke | complete: export/replay contract and short reproduction check passed |
| E003-M45 | scaled candidate-pool export and support-aware replay | complete: replay verified; frozen contract verdict `fail_redesign` |
| E003-M46 | score redesign or external baseline gate | complete: 12 bounded local score policies swept; hard pass 0; weak positive 0; selected `external_proposal_baseline_gate_first` |
| E003-M47 | external baseline feasibility gate | complete: selected `Grounded-SAM` as first route |
| E003-M48 | Grounded-SAM contract | complete: `grounded_sam_mask_backproject_v0` input/output contract fixed |
| E003-M49 | Grounded-SAM Docker/model smoke | complete: Docker runner emitted mask-depth proposal rows and M21 matcher smoke passed |
| E003-M50 | same-subset bbox-depth vs mask-depth comparison | complete: `Grounded-SAM` mask-depth did not beat bbox-depth; do not scale yet |
| E003-M51 | post-M50 route decision | complete: selected `targeted_mask_failure_analysis_first` |
| E003-M52 | Grounded-SAM mask failure analysis | complete: target loss is mask projection dropout; centroid worsening is match-set composition |
| E003-M53 | bbox-depth continuation repair gate | complete: selected search-critical bbox-depth failure-boundary audit |

## Real Perception Gate

사실:

- Current E003 starts with annotation-proxy noise because E001 has no ready RGB-D/open-vocabulary proposal rows.

논문 주장:

- Real RGB-D perception robustness requires actual RGB-D frames, camera poses or frame-to-scene alignment, a proposal/detector pipeline, proposal recall accounting, and detector output schemas.
- Real open-vocabulary robustness requires open-vocabulary proposal generation, text label mapping, confidence calibration, and closed/open label evaluation.

에이전트 추론:

- Annotation-proxy noise is useful as a controlled stress test, but it should be phrased as a bridge experiment.
- Real perception should become a separate M05 or later experiment only after source availability and detector pipeline are verified.

사용자 판단 필요:

- None for M00. E003-M01 source audit is recorded below.

## E003-M01 Source Audit

Implementation unit: `E003-M01_source_audit_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/audit_sources.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/artifacts/E003-M01_source_audit_v0/source_audit_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M01_source_audit_v0/pair_readiness_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M01_source_audit_v0/noise_plan.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M01_source_audit_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M01_source_audit_v0/report.md`

사실:

- Status: `source_audit_ready`.
- Query rows: 294.
- Candidate rows: 1248.
- Annotation-proxy noise ready rows: 294.
- RGB-D sequence available query rows: 0.
- E003 RGB-D ready rows: 0.
- E003 open-vocabulary ready rows: 0.
- Local sequence scan count: 8.
- Ready pair sequence-ready count: 0.
- Open-vocabulary hint count: 0.
- E002-M09 target-reachable eval rows: 267.
- First executable profile: `annotation_score_jitter_v0`.
- Reference profile: `clean_annotation_oracle_v0`.
- Next command fixed for M02: `python experiments/E003_perception_noise_expansion/tools/build_noise_inputs.py`.

논문 주장:

- E003-M01 supports starting with controlled annotation-proxy proposal noise.
- E003-M01 does not support real RGB-D or open-vocabulary perception robustness.
- Real perception claims remain blocked until aligned detector/proposal outputs are generated.

에이전트 추론:

- The first executable profile should preserve target presence and perturb ranking first, because this isolates memory-update robustness from detector recall failure.
- Proposal dropout, false positives, centroid jitter, and combined noise should follow after the clean and score-jitter path is executable.
- Local sequence payloads exist in the dataset, but they are not connected to the current E001 query denominator.

사용자 판단 필요:

- None for E003-M01. E003-M02 is recorded below.

## E003-M02 Annotation-Proxy Noise Generator

Implementation unit: `E003-M02_annotation_proxy_noise_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/build_noise_inputs.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/artifacts/E003-M02_annotation_proxy_noise_v0/noise_manifest.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M02_annotation_proxy_noise_v0/noisy_query_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M02_annotation_proxy_noise_v0/noisy_candidate_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M02_annotation_proxy_noise_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M02_annotation_proxy_noise_v0/report.md`

사실:

- Status: `annotation_proxy_noise_ready`.
- Input query rows: 294.
- Input candidate rows: 1248.
- Profiles: `clean_annotation_oracle_v0`, `annotation_score_jitter_v0`.
- Noisy query rows: 588.
- Noisy candidate rows: 2496.
- Noise manifest rows: 588.
- `clean_annotation_oracle_v0` target retained rate: 1.000000.
- `clean_annotation_oracle_v0` rank changed rate: 0.000000.
- `annotation_score_jitter_v0` target retained rate: 1.000000.
- `annotation_score_jitter_v0` rank changed rows: 121 / 294.
- `annotation_score_jitter_v0` target rank changed rows: 47 / 294.
- `annotation_score_jitter_v0` target rank deltas: -3: 1, -1: 4, 0: 247, 1: 28, 2: 7, 3: 3, 4: 4.

논문 주장:

- E003-M02 supports controlled annotation-proxy score/rank noise input generation.
- E003-M02 preserves target presence, so it tests ranking robustness rather than proposal recall failure.
- E003-M02 does not support real RGB-D or open-vocabulary perception robustness.

에이전트 추론:

- `clean_annotation_oracle_v0` is the reference condition for robustness deltas.
- `annotation_score_jitter_v0` is the first stress condition because it changes ranking without mixing in target dropout.
- E003-M03 evaluates policy robustness on these noisy rows before adding dropout or false-positive profiles.

사용자 판단 필요:

- None for E003-M02. E003-M03 is recorded below.

## E003-M03 Noisy Policy Evaluation

Implementation unit: `E003-M03_noisy_policy_eval_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/evaluate_noisy_policies.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/artifacts/E003-M03_noisy_policy_eval_v0/predictions.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M03_noisy_policy_eval_v0/failure_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M03_noisy_policy_eval_v0/metrics.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M03_noisy_policy_eval_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M03_noisy_policy_eval_v0/report.md`

사실:

- Status: `noisy_policy_eval_ready`.
- Noisy query rows: 588.
- Noisy candidate rows: 2496.
- Prediction rows: 5292.
- Failure rows: 466.
- Candidate grid signal rows: 2496.
- Profiles: `clean_annotation_oracle_v0`, `annotation_score_jitter_v0`.
- Significant moved `routine_fetch` clean `task_conditioned_budget_v0`: proxy `SR` 0.727273, `ExpectedSearchCost` 1.636364, `AttemptSPL` 0.681818, task utility 0.481818.
- Significant moved `routine_fetch` jitter `task_conditioned_budget_v0`: proxy `SR` 0.636364, `ExpectedSearchCost` 1.818182, `AttemptSPL` 0.590909, task utility 0.363636.
- Significant moved `routine_fetch` jitter `reachable_first_task_conditioned_budget_v0`: proxy `SR` 0.636364, `ExpectedSearchCost` 1.818182, `AttemptSPL` 0.590909, task utility 0.363636, returned-unreachable rate 0.090909.

논문 주장:

- E003-M03 supports controlled annotation-proxy ranking-noise robustness evaluation.
- E003-M03 does not support real RGB-D perception robustness, open-vocabulary perception robustness, or real navigation `SR` / `SPL`.

에이전트 추론:

- `annotation_score_jitter_v0` preserves target presence, so the observed degradation is a candidate-order and budget sensitivity signal, not detector recall failure.
- `reachable_first_task_conditioned_budget_v0` currently improves returned-unreachable behavior in the noisy significant moved `routine_fetch` subset, but it does not recover the rank-noise success drop.
- E003-M04 summarizes whether this degradation is acceptable, which failure rows drive it, and whether the next stress profile should be target dropout, false positives, or centroid jitter.

사용자 판단 필요:

- None for E003-M03. E003-M04 is recorded below.

## E003-M04 Robustness Failure Analysis

Implementation unit: `E003-M04_robustness_failure_analysis_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/analyze_robustness_failures.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/artifacts/E003-M04_robustness_failure_analysis_v0/transition_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M04_robustness_failure_analysis_v0/hard_failure_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M04_robustness_failure_analysis_v0/policy_delta_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M04_robustness_failure_analysis_v0/summary.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M04_robustness_failure_analysis_v0/claim_boundary.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M04_robustness_failure_analysis_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M04_robustness_failure_analysis_v0/report.md`

사실:

- Status: `robustness_boundary_ready`.
- Transition rows: 2646.
- Hard failure rows: 29.
- Significant moved `routine_fetch` `task_conditioned_budget_v0`: clean proxy `SR` 0.727273, stress proxy `SR` 0.636364, delta -0.090909, noise regression rows 1.
- Significant moved `routine_fetch` `task_conditioned_budget_v0`: `ExpectedSearchCost` delta +0.181818, `AttemptSPL` delta -0.090909, task utility delta -0.118182.
- Noisy `reachable_first_task_conditioned_budget_v0` vs noisy `task_conditioned_budget_v0`: returned-unreachable event delta -0.181818, proxy `SR` delta 0.0.
- Target-drop profiles included: false.
- Uses real RGB-D perception: false.
- Uses open-vocabulary perception: false.
- Uses real navigation: false.

논문 주장:

- E003-M04 supports controlled annotation-proxy ranking-noise robustness boundary analysis.
- E003-M04 supports saying that `reachable_first_task_conditioned_budget_v0` reduces unreachable returns under the noisy profile relative to `task_conditioned_budget_v0`, but does not recover the proxy `SR` drop.
- E003-M04 does not support detector proposal recall robustness, real RGB-D robustness, open-vocabulary robustness, or real navigation `SR` / `SPL`.

에이전트 추론:

- The current hard boundary is budget sensitivity under noisy candidate ordering: one significant moved `routine_fetch` row flips from success to failure for the primary policies.
- `always_top5` is more robust in this target-preserving noise setting, so the paper needs a cost/utility argument rather than only proxy `SR`.
- The next E003 step should either stage real proposal sources or add a target-drop/false-positive/centroid-jitter profile so perception robustness is not overclaimed from rank-only noise.

사용자 판단 필요:

- None for E003-M04. E003-M05 is recorded below.

## E003-M05 Route Selection

Implementation unit: `E003-M05_route_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/select_m05_route.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/artifacts/E003-M05_route_v0/proposal_source_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M05_route_v0/route_decision.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M05_route_v0/controlled_profile_contract.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M05_route_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M05_route_v0/report.md`

사실:

- Status: `controlled_stress_selected`.
- Query rows: 294.
- Local sequence scan count: 8.
- Local RGB-D triplet scan count: 8.
- Query rows with rescan RGB-D ready: 0.
- Query rows with real RGB-D proposal ready: 0.
- Query rows with real open-vocabulary proposal ready: 0.
- Proposal output files found: 0.
- Selected route: `controlled_annotation_proxy_stress`.
- Selected profile: `annotation_proposal_dropout_v0`.
- Recommended seed set: 11, 17, 23.
- Target drop rate: 0.15.
- Non-target candidate drop rate: 0.25.
- Required denominators: `all_rows`, `target_retained_eval`, `target_dropped_eval`.
- Docker required for selected route: false, because this route is a repository-local artifact transform.
- Docker required for future real detector/open-vocabulary paper-body implementation: true.

논문 주장:

- E003-M05 supports choosing the next controlled proposal-recall stress route after real proposal-source audit.
- E003-M05 does not support real RGB-D or open-vocabulary robustness because no detector/proposal source is ready.

에이전트 추론:

- `annotation_proposal_dropout_v0` is the next profile because M04 already tested rank-only noise and explicitly found no target-drop condition.
- Target-drop stress is closer to detector proposal recall failure than false-positive or centroid-only noise.
- Real detector/open-vocabulary implementation should be Dockerized before it becomes a paper-body experiment command.

사용자 판단 필요:

- None for E003-M05. E003-M06 is recorded below.

## E003-M06 Annotation Proposal Dropout

Implementation unit: `E003-M06_annotation_proposal_dropout_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/run_proposal_dropout.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/artifacts/E003-M06_annotation_proposal_dropout_v0/noise_manifest.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M06_annotation_proposal_dropout_v0/noisy_query_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M06_annotation_proposal_dropout_v0/noisy_candidate_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M06_annotation_proposal_dropout_v0/predictions.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M06_annotation_proposal_dropout_v0/failure_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M06_annotation_proposal_dropout_v0/metrics.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M06_annotation_proposal_dropout_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M06_annotation_proposal_dropout_v0/report.md`

사실:

- Status: `proposal_dropout_eval_ready`.
- Input query rows: 294.
- Input candidate rows: 1248.
- Dropout seeds: 11, 17, 23.
- Configured target drop rate: 0.15.
- Configured non-target candidate drop rate: 0.25.
- Noisy query rows: 1176.
- Noisy candidate rows: 4208.
- Prediction rows: 10584.
- Failure rows: 1191.
- `annotation_proposal_dropout_v0` target-dropped rows: 77 / 882.
- Actual target dropped rate: 0.087302.
- Forced target-retained rows: 51.
- Significant moved `routine_fetch` `task_conditioned_budget_v0` target-retained proxy `SR`: 0.8.
- Significant moved `routine_fetch` `task_conditioned_budget_v0` target-dropped proxy `SR`: 0.0.
- Significant moved `routine_fetch` `task_conditioned_budget_v0` target-retained `ExpectedSearchCost`: 1.533333.
- Significant moved `routine_fetch` `task_conditioned_budget_v0` target-dropped `ExpectedSearchCost`: 3.0.
- Docker required: false, because this is a repository-local artifact transform.

논문 주장:

- E003-M06 supports controlled annotation-proxy proposal-recall stress evaluation.
- E003-M06 supports separating target-retained and target-dropped denominators.
- E003-M06 does not support real RGB-D or open-vocabulary detector robustness.

에이전트 추론:

- Target-dropped rows approximate detector proposal recall failure more directly than score/rank jitter.
- Positive retained-denominator results should not be mixed with target-dropped failures.
- Forced target-retained rows mean the realized target-drop rate is lower than the configured target-drop rate; E003-M07 should report this boundary explicitly.

사용자 판단 필요:

- None for E003-M06. Continue to E003-M07 dropout failure-boundary analysis.

## E003-M07 Dropout Failure Boundary

Implementation unit: `E003-M07_dropout_failure_boundary_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/analyze_dropout_boundaries.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/artifacts/E003-M07_dropout_failure_boundary_v0/boundary_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M07_dropout_failure_boundary_v0/hard_boundary_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M07_dropout_failure_boundary_v0/policy_delta_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M07_dropout_failure_boundary_v0/summary.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M07_dropout_failure_boundary_v0/claim_boundary.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M07_dropout_failure_boundary_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M07_dropout_failure_boundary_v0/report.md`

사실:

- Status: `dropout_boundary_ready`.
- Boundary rows: 7938.
- Hard boundary rows: 294.
- Dropout query rows: 882.
- Natural target-retained rows: 754.
- Forced-retained rows: 51.
- Target-dropped rows: 77.
- Reported target-retained rate: 0.912698.
- Strict target-retained rate excluding forced rows: 0.854875.
- Target-drop attempt rate including forced rows: 0.145125.
- Significant moved `routine_fetch` natural target-retained `task_conditioned_budget_v0`: clean proxy `SR` 0.75, dropout proxy `SR` 0.785714, delta +0.035714.
- Significant moved `routine_fetch` target-dropped `task_conditioned_budget_v0`: clean proxy `SR` 0.333333, dropout proxy `SR` 0.0, delta -0.333333.
- Docker required: false, because this is a repository-local artifact analysis.

논문 주장:

- E003-M07 supports controlled annotation-proxy proposal-recall boundary analysis.
- E003-M07 supports separating `natural_target_retained`, `forced_retained`, and `target_dropped` denominators.
- E003-M07 does not support real RGB-D or open-vocabulary detector robustness.

에이전트 추론:

- Target-dropped rows are a proposal-recall ceiling; stale-memory update cannot recover the target if the current proposal set does not contain it.
- Forced-retained rows create an artificial recall floor and should be excluded from strict proposal-recall robustness claims.
- Target-retained dropout can improve proxy `SR` by removing distractors, so the next controlled stress should test false-positive contamination.

사용자 판단 필요:

- None for E003-M07. Continue to E003-M08 `annotation_false_positive_v0` unless redirected to Dockerized real proposal generation.

## E003-M08 Annotation False Positive Stress

Implementation unit: `E003-M08_annotation_false_positive_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/run_false_positive_stress.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/artifacts/E003-M08_annotation_false_positive_v0/noise_manifest.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M08_annotation_false_positive_v0/noisy_query_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M08_annotation_false_positive_v0/noisy_candidate_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M08_annotation_false_positive_v0/predictions.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M08_annotation_false_positive_v0/failure_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M08_annotation_false_positive_v0/metrics.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M08_annotation_false_positive_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M08_annotation_false_positive_v0/report.md`

사실:

- Status: `false_positive_eval_ready`.
- Input query rows: 294.
- Input candidate rows: 1248.
- False-positive seeds: 31, 37, 41.
- Noisy query rows: 1176.
- Noisy candidate rows: 6810.
- Prediction rows: 10584.
- Failure rows: 1067.
- False-positive added rows: 837 / 882.
- Target pushed-down rows: 96 / 882.
- Same-label false positives: 0.
- Semantic-group false positives: 648.
- Fallback false positives: 1170.
- Significant moved `routine_fetch` matched clean `task_conditioned_budget_v0`: proxy `SR` 0.625, `ExpectedSearchCost` 1.75, `AttemptSPL` 0.625, utility 0.3625.
- Significant moved `routine_fetch` false-positive `task_conditioned_budget_v0`: proxy `SR` 0.125, `ExpectedSearchCost` 2.25, `AttemptSPL` 0.125, utility -0.2125.
- Significant moved `routine_fetch` false-positive `reachable_first_task_conditioned_budget_v0`: proxy `SR` 0.5, `ExpectedSearchCost` 1.875, `AttemptSPL` 0.5, utility 0.21875.
- Docker required: false, because this is a repository-local artifact transform.

논문 주장:

- E003-M08 supports controlled annotation-derived false-positive contamination stress evaluation.
- E003-M08 keeps target presence fixed, so failures are ranking/budget contamination failures rather than proposal-recall failures.
- E003-M08 does not support real RGB-D or open-vocabulary detector hallucination robustness.

에이전트 추론:

- Same-label false positives are 0 because the E001 candidate generator already includes all same-label annotation candidates in each query row.
- The added candidates therefore come from semantic-group or same-scene fallback annotation objects, which is useful for contamination stress but not equivalent to real open-vocabulary hallucination.
- The large drop from matched clean `task_conditioned_budget_v0` proxy `SR` 0.625 to false-positive 0.125 suggests the next unit should analyze which target-rank pushes and budget limits cause the failures.

사용자 판단 필요:

- None for E003-M08. Continue to E003-M09 false-positive failure-boundary analysis unless redirected to Dockerized real proposal generation.

## E003-M09 False Positive Failure Boundary

Implementation unit: `E003-M09_false_positive_failure_boundary_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/analyze_false_positive_boundaries.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/artifacts/E003-M09_false_positive_failure_boundary_v0/boundary_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M09_false_positive_failure_boundary_v0/hard_boundary_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M09_false_positive_failure_boundary_v0/policy_delta_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M09_false_positive_failure_boundary_v0/summary.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M09_false_positive_failure_boundary_v0/claim_boundary.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M09_false_positive_failure_boundary_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M09_false_positive_failure_boundary_v0/report.md`

사실:

- Status: `false_positive_boundary_ready`.
- Boundary rows: 7938.
- Hard boundary rows: 231.
- Stress query rows: 882.
- False-positive added rows: 837.
- Target pushed-down rows: 96.
- Target pushed-down rate: 0.108844.
- Same-label false positives: 0.
- Semantic-group false positives: 648.
- Fallback false positives: 1170.
- Significant moved `routine_fetch` target-pushed-down `task_conditioned_budget_v0`: clean proxy `SR` 0.571429, false-positive proxy `SR` 0.0, delta -0.571429.
- Significant moved `routine_fetch` target-pushed-down `reachable_first_task_conditioned_budget_v0`: clean proxy `SR` 0.571429, false-positive proxy `SR` 0.428571, delta -0.142857.
- Significant moved `routine_fetch` reachable-first minus task false-positive proxy `SR` delta: +0.272727.
- Docker required: false, because this is a repository-local artifact analysis.

논문 주장:

- E003-M09 supports controlled annotation-derived false-positive failure-boundary analysis.
- E003-M09 supports saying that false-positive contamination causes ranking/budget failures while preserving target presence.
- E003-M09 supports saying that `reachable_first_task_conditioned_budget_v0` reduces false-positive damage relative to `task_conditioned_budget_v0` in significant moved `routine_fetch`.
- E003-M09 does not support real RGB-D or open-vocabulary detector hallucination robustness.

에이전트 추론:

- Target-pushed-down rows isolate the hard false-positive failure mode: false positives move the target outside the task budget.
- `reachable_first_task_conditioned_budget_v0` recovers 9 significant moved `routine_fetch` rows relative to `task_conditioned_budget_v0` and has 0 success-loss rows in that subset.
- Since score/rank jitter, proposal dropout, and false-positive contamination now have separate boundaries, the next controlled perception-like stress should be `annotation_centroid_jitter_v0`.

사용자 판단 필요:

- None for E003-M09. Continue to E003-M10 `annotation_centroid_jitter_v0` unless redirected to Dockerized real proposal generation.

## E003-M10 Annotation Centroid Jitter

Implementation unit: `E003-M10_annotation_centroid_jitter_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/run_centroid_jitter.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/artifacts/E003-M10_annotation_centroid_jitter_v0/noise_manifest.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M10_annotation_centroid_jitter_v0/noisy_query_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M10_annotation_centroid_jitter_v0/noisy_candidate_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M10_annotation_centroid_jitter_v0/predictions.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M10_annotation_centroid_jitter_v0/failure_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M10_annotation_centroid_jitter_v0/metrics.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M10_annotation_centroid_jitter_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M10_annotation_centroid_jitter_v0/report.md`

사실:

- Status: `centroid_jitter_eval_ready`.
- Input query rows: 294.
- Input candidate rows: 1248.
- Profiles: `clean_annotation_oracle_v0`, `annotation_centroid_jitter_v0`.
- Centroid jitter seeds: 43, 47, 53.
- Planar sigma: 0.25 m.
- Max planar jitter: 0.75 m.
- Noisy query rows: 1176.
- Noisy candidate rows: 4992.
- Prediction rows: 10584.
- Failure rows: 1654.
- `annotation_centroid_jitter_v0` target retained rate: 1.000000.
- `annotation_centroid_jitter_v0` target rank changed rows: 139 / 882.
- `annotation_centroid_jitter_v0` target jitter exceeds threshold rows: 123 / 882.
- `annotation_centroid_jitter_v0` mean target centroid jitter: 0.313896 m.
- `annotation_centroid_jitter_v0` mean target planar jitter: 0.308592 m.
- Significant moved `routine_fetch` `task_conditioned_budget_v0`: identity proxy `SR` 0.696970, localization proxy `SR` 0.606061, `ExpectedSearchCost` 1.757576, `AttemptSPL` 0.621212, utility 0.433333.
- Significant moved `routine_fetch` `reachable_first_task_conditioned_budget_v0`: identity proxy `SR` 0.696970, localization proxy `SR` 0.606061, returned-unreachable rate 0.090909.
- Significant moved `routine_fetch` `task_conditioned_budget_v0` threshold-exceeded subset: 3 rows, identity proxy `SR` 1.000000, localization proxy `SR` 0.000000.
- Occupancy-grid path costs are not recomputed after centroid jitter.
- Docker required: false, because this is a repository-local artifact transform.

논문 주장:

- E003-M10 supports controlled annotation-proxy centroid localization jitter stress evaluation.
- E003-M10 supports separating correct-target identity retrieval from successful localization under jittered centroids.
- E003-M10 does not support real RGB-D localization noise, open-vocabulary localization noise, or real navigation `SR` / `SPL`.

에이전트 추론:

- Centroid jitter completes the individual controlled-noise profile set after rank jitter, proposal dropout, and false-positive contamination.
- The gap between identity proxy `SR` and localization proxy `SR` shows why the paper should not collapse object identity recovery and spatial localization into one success metric.
- Since grid path costs are reused by instance id rather than recomputed after centroid perturbation, E003-M11 should analyze the identity/localization boundary before any combined-noise profile.

사용자 판단 필요:

- None for E003-M10. Continue to E003-M11 centroid-jitter failure-boundary analysis unless redirected to Dockerized real proposal generation.

## E003-M11 Centroid Jitter Failure Boundary

Implementation unit: `E003-M11_centroid_jitter_failure_boundary_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/analyze_centroid_jitter_boundaries.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/artifacts/E003-M11_centroid_jitter_failure_boundary_v0/boundary_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M11_centroid_jitter_failure_boundary_v0/hard_boundary_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M11_centroid_jitter_failure_boundary_v0/policy_delta_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M11_centroid_jitter_failure_boundary_v0/summary.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M11_centroid_jitter_failure_boundary_v0/claim_boundary.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M11_centroid_jitter_failure_boundary_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M11_centroid_jitter_failure_boundary_v0/report.md`

사실:

- Status: `centroid_jitter_boundary_ready`.
- Boundary rows: 7938.
- Expected boundary rows: 7938.
- Hard boundary rows: 173.
- Stress query rows: 882.
- Target jitter exceeds threshold rows: 123 / 882.
- Target jitter exceeds threshold rate: 0.139456.
- Target rank changed rows: 139 / 882.
- Target rank changed rate: 0.157596.
- Mean target centroid jitter: 0.313896 m.
- Mean target planar jitter: 0.308592 m.
- Primary-policy boundary counts include `identity_success_over_jitter_localization_failure` 112, `rank_jitter_budget_identity_regression` 13, and `persistent_budget_localization_boundary` 46.
- Significant moved `routine_fetch` `task_conditioned_budget_v0`: identity proxy `SR` 0.696970, localization proxy `SR` 0.606061, localization delta -0.121212.
- Significant moved `routine_fetch` `task_conditioned_budget_v0` threshold-exceeded subset: 3 rows, identity proxy `SR` 1.000000, localization proxy `SR` 0.000000.
- Significant moved `routine_fetch` reachable-first minus task: identity proxy `SR` delta 0.000000, localization proxy `SR` delta 0.000000, returned-unreachable event delta -0.151515.
- Occupancy-grid path costs are not recomputed after centroid jitter.
- Docker required: false, because this is a repository-local artifact analysis.

논문 주장:

- E003-M11 supports controlled annotation-proxy centroid-jitter failure-boundary analysis.
- E003-M11 supports reporting identity retrieval and spatial localization as separate success metrics under centroid noise.
- E003-M11 supports treating correct-target identity success with over-threshold centroid error as localization failure.
- E003-M11 does not support real RGB-D localization noise, open-vocabulary localization noise, or real navigation `SR` / `SPL`.

에이전트 추론:

- The identity/localization split is necessary because significant moved `routine_fetch` keeps identity proxy `SR` at 0.696970 while localization proxy `SR` drops to 0.606061.
- The threshold-exceeded subset is the cleanest failure boundary: identity proxy `SR` remains 1.000000, but localization proxy `SR` becomes 0.000000.
- `reachable_first_task_conditioned_budget_v0` reduces returned-unreachable events in this subset but does not improve identity or localization `SR` under centroid jitter.
- Since all individual controlled profiles are now covered, the next unit should decide between `annotation_combined_moderate_v0` and a Dockerized real proposal route.

사용자 판단 필요:

- None for E003-M11. Continue to E003-M12 combined-noise route decision unless redirected to Dockerized real proposal generation.

## E003-M12 Combined-Noise Route Decision

Implementation unit: `E003-M12_combined_noise_route_decision_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/select_m12_combined_route.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/artifacts/E003-M12_combined_noise_route_decision_v0/input_evidence_summary.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M12_combined_noise_route_decision_v0/route_decision.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M12_combined_noise_route_decision_v0/combined_profile_contract.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M12_combined_noise_route_decision_v0/real_proposal_route_requirements.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M12_combined_noise_route_decision_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M12_combined_noise_route_decision_v0/report.md`

사실:

- Status: `combined_controlled_route_selected`.
- Ready annotation-proxy query rows: 294.
- Real RGB-D proposal-ready rows: 0.
- Real open-vocabulary proposal-ready rows: 0.
- Proposal output files found: 0.
- Selected route: `controlled_annotation_proxy_combined_stress`.
- Selected profile: `annotation_combined_moderate_v0`.
- Next action: `E003-M13_annotation_combined_moderate_v0`.
- Docker required for selected route: false.
- Docker required for real proposal route: true.
- Individual controlled profiles complete: `annotation_score_jitter_v0`, `annotation_proposal_dropout_v0`, `annotation_false_positive_v0`, `annotation_centroid_jitter_v0`.
- Combined profile seed set: 61, 67, 71.
- Combined profile score jitter sigma: 0.08.
- Combined profile target drop rate: 0.10.
- Combined profile non-target drop rate: 0.20.
- Combined profile false-positive candidates per row: 1 to 2.
- Combined profile centroid planar sigma: 0.18 m.
- Combined profile max planar jitter: 0.50 m.

논문 주장:

- E003-M12 supports selecting `annotation_combined_moderate_v0` as the next controlled perception-like stress route.
- E003-M12 supports keeping real RGB-D/open-vocabulary claims blocked until Dockerized proposal generation and alignment are staged.
- E003-M12 does not itself support new metric results; it fixes the next implementation contract.

에이전트 추론:

- The combined profile is the correct immediate next step because score/rank jitter, proposal dropout, false-positive contamination, and centroid jitter now have separate boundaries.
- Switching immediately to real proposals would require Dockerized detector generation and a proposal-to-`3DSSG` matching contract while current ready rows remain 0.
- The combined profile should still be framed as annotation-proxy robustness, not real perception robustness.

사용자 판단 필요:

- None for E003-M12. Continue to E003-M13 `annotation_combined_moderate_v0` implementation unless redirected to Dockerized real proposal staging.

## E003-M13 Annotation Combined Moderate

Implementation unit: `E003-M13_annotation_combined_moderate_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/run_combined_moderate.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/artifacts/E003-M13_annotation_combined_moderate_v0/noise_manifest.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M13_annotation_combined_moderate_v0/noisy_query_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M13_annotation_combined_moderate_v0/noisy_candidate_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M13_annotation_combined_moderate_v0/predictions.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M13_annotation_combined_moderate_v0/failure_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M13_annotation_combined_moderate_v0/metrics.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M13_annotation_combined_moderate_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M13_annotation_combined_moderate_v0/report.md`

사실:

- Status: `combined_moderate_eval_ready`.
- Input query rows: 294.
- Input candidate rows: 1248.
- Combined seeds: 61, 67, 71.
- Noisy query rows: 1176.
- Noisy candidate rows: 5419.
- Prediction rows: 10584.
- Failure rows: 1621.
- Target dropped rows: 49 / 882.
- False-positive added rows: 837 / 882.
- Target pushed-down rows: 120 / 882.
- Target rank changed rows: 185 / 882.
- Target jitter exceeds threshold rows: 23 / 882.
- Mean target centroid jitter: 0.233738 m.
- Significant moved `routine_fetch` `task_conditioned_budget_v0`: identity proxy `SR` 0.212121, localization proxy `SR` 0.212121, `ExpectedSearchCost` 2.181818, `AttemptSPL` 0.196970, utility -0.115152.
- Significant moved `routine_fetch` `reachable_first_task_conditioned_budget_v0`: identity proxy `SR` 0.606061, localization proxy `SR` 0.606061, `ExpectedSearchCost` 1.757576, `AttemptSPL` 0.575758, utility 0.342424.
- Significant moved `routine_fetch` `always_top5`: identity proxy `SR` 0.787879, localization proxy `SR` 0.787879.
- Significant moved `routine_fetch` target-dropped `task_conditioned_budget_v0`: 1 row, identity proxy `SR` 0.000000, localization proxy `SR` 0.000000.
- Docker required: false, because this is a repository-local artifact transform and policy evaluation.

논문 주장:

- E003-M13 supports controlled annotation-proxy combined perception-like stress evaluation.
- E003-M13 supports testing interaction between proposal dropout, annotation-derived false positives, score/rank jitter, and centroid jitter.
- E003-M13 does not support real RGB-D perception robustness, open-vocabulary detector robustness, or real navigation `SR` / `SPL`.

에이전트 추론:

- Combined stress is much harder than the individual profiles for `task_conditioned_budget_v0`, dropping significant moved `routine_fetch` identity/localization proxy `SR` to 0.212121.
- `reachable_first_task_conditioned_budget_v0` is materially stronger than `task_conditioned_budget_v0` under combined stress in significant moved `routine_fetch`, but this should be validated with E003-M14 boundary analysis before claiming a paper-level robustness result.
- Target-dropped and jitter-exceeded denominators must stay separate from the all-row aggregate.

사용자 판단 필요:

- None for E003-M13. Continue to E003-M14 combined-noise failure-boundary analysis unless redirected to Dockerized real proposal staging.

## E003-M14 Combined Noise Failure Boundary

Implementation unit: `E003-M14_combined_noise_failure_boundary_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/analyze_combined_boundaries.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/artifacts/E003-M14_combined_noise_failure_boundary_v0/boundary_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M14_combined_noise_failure_boundary_v0/hard_boundary_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M14_combined_noise_failure_boundary_v0/policy_delta_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M14_combined_noise_failure_boundary_v0/summary.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M14_combined_noise_failure_boundary_v0/claim_boundary.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M14_combined_noise_failure_boundary_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M14_combined_noise_failure_boundary_v0/report.md`

사실:

- Status: `combined_noise_boundary_ready`.
- Boundary rows: 7938.
- Expected boundary rows: 7938.
- Hard boundary rows: 521.
- Stress query rows: 882.
- Combined group counts: `target_dropped` 49, `centroid_localization_exceeded` 23, `false_positive_target_pushed_down` 117, `rank_budget_shift_no_push` 62, `false_positive_added_no_push` 604, `candidate_dropout_or_score_shift` 27.
- Significant moved `routine_fetch` `task_conditioned_budget_v0`: identity/localization proxy `SR` 0.212121 / 0.212121.
- Significant moved `routine_fetch` `reachable_first_task_conditioned_budget_v0`: identity/localization proxy `SR` 0.606061 / 0.606061.
- Significant moved `routine_fetch` reachable-first minus task delta: identity/localization proxy `SR` +0.393939 / +0.393939, gain rows 13, loss rows 0.
- Significant moved `routine_fetch` `false_positive_target_pushed_down` subset: `task_conditioned_budget_v0` identity/localization proxy `SR` 0.000000 / 0.000000, `reachable_first_task_conditioned_budget_v0` 0.647059 / 0.647059.
- Uses real RGB-D perception: false.
- Uses open-vocabulary perception: false.
- Uses real navigation: false.
- Docker required: false, because this is repository-local analysis over E003-M13 JSONL artifacts.

논문 주장:

- E003-M14 supports controlled annotation-proxy combined-noise failure-boundary analysis.
- E003-M14 supports separating proposal-recall ceilings, distractor rank/budget failures, score/rank shifts, and centroid-localization failures.
- E003-M14 supports claiming that `reachable_first_task_conditioned_budget_v0` improves significant moved `routine_fetch` identity/localization proxy `SR` over `task_conditioned_budget_v0` under combined annotation-proxy stress.
- E003-M14 does not support real RGB-D perception robustness, open-vocabulary detector robustness, deployable search policy, or real navigation `SR` / `SPL`.

에이전트 추론:

- Target-dropped rows are proposal-recall ceiling cases and should not be treated as recoverable stale-memory policy failures.
- The strongest current method signal is not from generic task conditioning alone; it is from reachable-first ordering under combined distractor/rank/budget stress.
- E003-M15 should consolidate the controlled E003 claim boundary before deciding whether to start Dockerized real proposal generation.

사용자 판단 필요:

- None for E003-M14. E003-M15 completed the controlled perception-robustness claim summary.

## E003-M15 Controlled Perception Claim Summary

Implementation unit: `E003-M15_controlled_perception_claim_summary_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/summarize_controlled_claims.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/artifacts/E003-M15_controlled_perception_claim_summary_v0/profile_summary_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M15_controlled_perception_claim_summary_v0/claim_evidence_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M15_controlled_perception_claim_summary_v0/promotion_gate.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M15_controlled_perception_claim_summary_v0/claim_summary.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M15_controlled_perception_claim_summary_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M15_controlled_perception_claim_summary_v0/report.md`

사실:

- Status: `controlled_perception_claim_summary_ready`.
- Profile summary rows: 5.
- Claim evidence rows: 8.
- Controlled claim ready: true.
- Real RGB-D/open-vocabulary claim ready: false.
- Real navigation claim ready: false.
- Controlled profiles summarized: `annotation_score_jitter_v0`, `annotation_proposal_dropout_v0`, `annotation_false_positive_v0`, `annotation_centroid_jitter_v0`, `annotation_combined_moderate_v0`.
- Main method-signal subset: `significant_moved|routine_fetch`.
- Combined `task_conditioned_budget_v0` identity proxy `SR`: 0.212121.
- Combined `reachable_first_task_conditioned_budget_v0` identity proxy `SR`: 0.606061.
- Reachable-first minus task identity proxy `SR` delta: +0.393939.
- Reachable-first gain/loss rows: 13 / 0.
- Next recommended unit: `E003-M16 Dockerized real-proposal route decision`.

논문 주장:

- E003-M15 supports writing E003 as a controlled annotation-proxy perception/proposal-noise robustness suite.
- E003-M15 supports the claim that H001 can separate proposal-recall, distractor rank/budget, and centroid-localization failures under controlled stress.
- E003-M15 supports treating `reachable_first_task_conditioned_budget_v0` as the current strongest method signal under false-positive and combined stress.
- E003-M15 does not support real RGB-D perception robustness, open-vocabulary detector robustness, real navigation `SR` / `SPL`, deployable search policy, or natural-language intention understanding.

에이전트 추론:

- The controlled suite is now coherent enough for a controlled stress-test table, but not enough for a real perception robustness claim.
- For top-tier positioning, the next useful expansion is not another annotation-proxy profile; it is a Dockerized real-proposal source and proposal-to-`3DSSG` matching gate.
- E004 task-context memory trust can still proceed later, but real perception promotion is the more direct way to strengthen the E003 claim.

사용자 판단 필요:

- Next recommended unit is `E003-M16 Dockerized real-proposal route decision`.
- The main decision is whether to start real RGB-D/open-vocabulary proposal staging now or defer it until after E004 task-context memory trust.

## E003-M16 Real Proposal Route Decision

Implementation unit: `E003-M16_real_proposal_route_decision_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/select_m16_real_proposal_route.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/artifacts/E003-M16_real_proposal_route_decision_v0/proposal_source_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M16_real_proposal_route_decision_v0/scan_alignment_gate_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M16_real_proposal_route_decision_v0/query_alignment_gate_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M16_real_proposal_route_decision_v0/pair_alignment_gate_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M16_real_proposal_route_decision_v0/proposal_output_schema.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M16_real_proposal_route_decision_v0/docker_command_plan.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M16_real_proposal_route_decision_v0/route_decision.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M16_real_proposal_route_decision_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M16_real_proposal_route_decision_v0/report.md`

사실:

- Status: `real_proposal_denominator_staging_required`.
- Scan gate rows: 54.
- Sequence-ready scans: 8.
- Proposal-alignment-ready scans: 8.
- Query alignment rows: 294.
- Query rows with reference sequence ready: 123.
- Query rows with current rescan sequence ready: 0.
- Query rows with current real RGB-D proposal ready: 0.
- Pair rows with current real proposal ready: 0.
- Selected route: `sequence_ready_scan_bootstrap`.
- Next recommended unit: `E003-M17 real-proposal denominator staging`.
- Future detector execution must use Docker.
- Planned Docker image tag: `research2/real-smoke`.
- Planned proposal schema: `real_proposal_prediction_jsonl_v0`.

논문 주장:

- E003-M16 supports saying that the controlled E003 table is ready, but real proposal evaluation is not yet ready.
- E003-M16 supports selecting `sequence_ready_scan_bootstrap` because current E001 rescans have 0 sequence-ready query rows.
- E003-M16 supports a concrete proposal output schema and Docker command plan for later real detector execution.
- E003-M16 does not support real RGB-D/open-vocabulary robustness results yet.

에이전트 추론:

- Current E001 query rows cannot be upgraded to real current-scene proposals without staging current rescan RGB-D frames.
- Reference scan sequences are insufficient as the main proposal source because proposal recall must be measured on the current rescan scene.
- The next top-tier strengthening step is E003-M17 denominator staging, then a Dockerized detector smoke run.

사용자 판단 필요:

- None for E003-M16. Next is `E003-M17 real-proposal denominator staging` unless redirected to E004 task-context memory trust.

## E003-M17 Real Proposal Denominator Staging

Implementation unit: `E003-M17_real_proposal_denominator_staging_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/stage_m17_real_proposal_denominator.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/artifacts/E003-M17_real_proposal_denominator_staging_v0/real_proposal_query_manifest.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M17_real_proposal_denominator_staging_v0/real_proposal_object_targets.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M17_real_proposal_denominator_staging_v0/scan_target_summary.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M17_real_proposal_denominator_staging_v0/prompt_set.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M17_real_proposal_denominator_staging_v0/proposal_output_schema.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M17_real_proposal_denominator_staging_v0/staging_decision.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M17_real_proposal_denominator_staging_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M17_real_proposal_denominator_staging_v0/report.md`

사실:

- Status: `real_proposal_denominator_staged`.
- Source route: `sequence_ready_scan_bootstrap`.
- Ready scan rows: 8.
- Query manifest rows: 8.
- Object target rows: 460.
- Detector target rows: 344.
- Evaluation target rows: 344.
- Prompt label count: 98.
- Detector target label count: 85.
- Proposal schema copied: true.
- Paper-table command ready: false.
- Detector predictions ready: false.
- Real RGB-D/open-vocabulary claim ready: false.
- Docker required for M17: false.
- Docker required for next detector: true.
- Next recommended unit: `E003-M18 Dockerized real-proposal detector scaffold`.

논문 주장:

- E003-M17 supports real RGB-D/open-vocabulary detector input staging.
- E003-M17 supports saying that sequence-ready `3RScan` scans can now be passed to a Dockerized detector using a fixed manifest, prompt set, and output schema.
- E003-M17 does not support real perception robustness results because detector predictions have not been generated.

에이전트 추론:

- This staging intentionally rebuilds the real-proposal denominator from sequence-ready scans because current E001 rescans have no sequence-ready rows.
- Object targets are split into detector targets, structural context, and generic context so prompt labels do not silently define the evaluation denominator.
- The next step should create or select the Dockerized detector scaffold before any paper-table command is considered ready.

사용자 판단 필요:

- None for E003-M17. Next is `E003-M18 Dockerized real-proposal detector scaffold`.

## E003-M18 Dockerized Real-Proposal Detector Scaffold

Implementation unit: `E003-M18_dockerized_real_proposal_detector_scaffold_v0`.

Stage: scaffold files and artifacts generated.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/run_m18_real_proposal_scaffold.py
```

Build/smoke command:

```bash
python experiments/E003_perception_noise_expansion/tools/run_m18_real_proposal_scaffold.py --build --smoke-run --docker-sudo --sudo-password-stdin
```

Artifacts:

- `experiments/E003_perception_noise_expansion/docker/real_proposals/Dockerfile`
- `experiments/E003_perception_noise_expansion/docker/real_proposals/run_rgbd_ov_proposals.py`
- `experiments/E003_perception_noise_expansion/tools/run_m18_real_proposal_scaffold.py`
- `experiments/E003_perception_noise_expansion/tools/validate_real_proposal_output.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M18_dockerized_real_proposal_detector_scaffold_v0/docker_build_plan.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M18_dockerized_real_proposal_detector_scaffold_v0/docker_run_command_plan.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M18_dockerized_real_proposal_detector_scaffold_v0/validator_contract.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M18_dockerized_real_proposal_detector_scaffold_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M18_dockerized_real_proposal_detector_scaffold_v0/report.md`

사실:

- Status: `docker_scaffold_ready`.
- Dockerfile ready: true.
- Container runner ready: true.
- Container runner local smoke ready: true.
- Host wrapper ready: true.
- Proposal output validator ready: true.
- Validator smoke ready: true.
- Docker CLI ready: true.
- Docker daemon ready: true.
- Docker socket: `srw-rw---- 1 root docker 0 May  3 22:28 /var/run/docker.sock`.
- Current user groups: `yoohyun sudo`.
- Docker command uses sudo: true.
- Docker build executed: true.
- Docker smoke executed: true.
- Docker smoke validator ready: true.
- Docker image: `research2/real-smoke:latest`, image id `e06a1c71c950`, size 186MB.
- Detector backend integrated: false.
- Detector predictions ready: false.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M18 supports a Docker execution contract for later real RGB-D/open-vocabulary proposal generation.
- E003-M18 supports schema validation for future `real_proposal_prediction_jsonl_v0` outputs.
- E003-M18 does not support real perception robustness results because no detector backend prediction has been generated.

에이전트 추론:

- E003 should continue to the Dockerized real-proposal route before E004/E005 because real perception evidence is the current top-tier bottleneck.
- The scaffold writes only empty smoke output by default so detector evidence is not fabricated.
- Docker build/smoke validates the execution contract, but a detector backend is still required before paper-table perception metrics.

사용자 판단 필요:

- None for E003-M18 scaffold. Next is E003-M19 real detector backend integration.

## E003-M19 Real Detector Backend Integration

Implementation unit: `E003-M19_real_detector_backend_integration_v0`.

Stage: backend contract connected to Docker runner.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/run_m19_real_detector_backend.py --build --docker-sudo --sudo-password-stdin
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/run_m19_real_detector_backend.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M19_real_detector_backend_integration_v0/backend_decision.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M19_real_detector_backend_integration_v0/docker_backend_run_plan.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M19_real_detector_backend_integration_v0/container_output/backend_contract.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M19_real_detector_backend_integration_v0/container_output/real_proposals.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M19_real_detector_backend_integration_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M19_real_detector_backend_integration_v0/report.md`

사실:

- Status: `real_detector_backend_contract_ready`.
- Selected backend: `groundingdino_rgbd_backproject_v0`.
- Docker image tag: `research2/real-smoke`.
- Docker build executed: true.
- Docker backend contract smoke executed: true.
- Backend contract ready: true.
- RGB-D frame triplets ready: 459.
- RGB-D frame triplets missing: 0.
- Manifest rows: 8.
- Prompt labels: 98.
- Detector backend integrated: false.
- Detector predictions ready: false.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M19 supports selecting a concrete real-detector backend contract and connecting it to the Docker runner.
- E003-M19 supports saying that E003-M17 RGB-D frames, depth, poses, and prompts are consumable by the selected backend route.
- E003-M19 does not support detector performance or real perception robustness because model inference is not integrated yet.

에이전트 추론:

- `groundingdino_rgbd_backproject_v0` is a practical first backend contract because it separates open-vocabulary 2D detection from RGB-D 3D projection.
- The contract explicitly blocks evaluation-only 3DSSG instance ids from detector inference.
- The next unit should add model dependencies and run a small non-empty detector prediction smoke.

사용자 판단 필요:

- None for E003-M19. E003-M20 is recorded below.

## E003-M20 Detector Model Smoke

Implementation unit: `E003-M20_detector_model_smoke_v0`.

Stage: Dockerized model dependency and non-empty prediction smoke.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/run_m20_detector_model_smoke.py --build --docker-sudo --sudo-password-stdin
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/run_m20_detector_model_smoke.py`
- `experiments/E003_perception_noise_expansion/docker/real_proposals/Dockerfile`
- `experiments/E003_perception_noise_expansion/docker/real_proposals/run_rgbd_ov_proposals.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M20_detector_model_smoke_v0/container_output/real_proposals.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M20_detector_model_smoke_v0/container_output/model_smoke.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M20_detector_model_smoke_v0/container_output/backend_contract.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M20_detector_model_smoke_v0/validator/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M20_detector_model_smoke_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M20_detector_model_smoke_v0/report.md`

사실:

- Status: `detector_model_smoke_ready`.
- Selected backend: `groundingdino_rgbd_backproject_v0`.
- Model id: `IDEA-Research/grounding-dino-tiny`.
- Docker image tag: `research2/real-smoke`.
- Docker image id: `03437e313fb3`.
- Docker image size: 1.64GB.
- Docker build executed: true.
- Docker model smoke executed: true.
- Backend contract ready: true.
- Model loaded: true.
- Inference device: `cpu`.
- Scanned frames: 1.
- Prediction rows: 20.
- Validator error rows: 0.
- Validator warning rows: 0.
- Label canonical counts: chair 8, table 5, plant 2, pillow 2, picture 1, curtain 1, light 1.
- Non-empty detector prediction smoke ready: true.
- Detector backend integrated: true.
- Detector predictions ready: true.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M20 supports a Dockerized non-empty model prediction smoke for the selected real-detector route.
- E003-M20 supports saying that `groundingdino_rgbd_backproject_v0` can load model dependencies, consume RGB-D sequence inputs, and emit schema-valid proposal rows.
- E003-M20 does not support real perception robustness or proposal-recall claims because outputs are not yet matched/evaluated against the M17 target denominator.

에이전트 추론:

- The next unit should match detector proposals to M17 target objects and report proposal recall, false positives, and centroid-localization error.
- M20 should stay a smoke gate, not a paper-table result.

사용자 판단 필요:

- None for E003-M20. E003-M21 is recorded below.

## E003-M21 Detector Proposal Matching

Implementation unit: `E003-M21_detector_proposal_matching_v0`.

Stage: detector proposal to target-denominator matching smoke.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/evaluate_m21_detector_matching.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/evaluate_m21_detector_matching.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M21_detector_proposal_matching_v0/matched_proposals.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M21_detector_proposal_matching_v0/target_recall_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M21_detector_proposal_matching_v0/label_metrics.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M21_detector_proposal_matching_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M21_detector_proposal_matching_v0/report.md`

사실:

- Status: `detector_matching_smoke_ready`.
- Matching rule: same scan, same canonical label, centroid distance <= 1.0m.
- Input prediction rows: 20.
- Evaluated scans: 1 / 8.
- Scan-level evaluation target rows: 51.
- Label-overlap target rows: 27.
- Matched proposal rows: 2.
- Matched target rows: 2.
- Proposal precision smoke: 0.100000.
- Scan target recall smoke: 0.039216.
- Label-overlap target recall smoke: 0.074074.
- False-positive proposal rows: 18.
- Mean matched centroid error: 0.303314m.
- Nearest same-label distance mean: 3.043020m.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M21 supports a first detector-to-denominator matching gate for M20 proposal rows.
- E003-M21 can report smoke-level proposal precision, target recall, false-positive count, and centroid-localization error.
- E003-M21 does not support real RGB-D/open-vocabulary robustness because it covers only one sampled frame from one scan.

에이전트 추론:

- Low scan-level recall is expected because the denominator is not visibility-filtered and M20 stopped after one frame.
- False-positive domination and large nearest same-label distances mean the next step should not jump directly to paper-table metrics.
- The next unit should remove early stop, run multi-frame matching, and separate frame coverage from RGB-D projection/matching failures.

사용자 판단 필요:

- None for E003-M21. E003-M22 is recorded below.

## E003-M22 Frame Scaling Projection Diagnostic

Implementation unit: `E003-M22_frame_scaling_projection_diagnostic_v0`.

Stage: multi-frame detector diagnostic, not paper-table evaluation.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py --build --docker-sudo --sudo-password-stdin
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py`
- `experiments/E003_perception_noise_expansion/docker/real_proposals/run_rgbd_ov_proposals.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M22_frame_scaling_projection_diagnostic_v0/container_output/real_proposals.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M22_frame_scaling_projection_diagnostic_v0/container_output/model_smoke.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M22_frame_scaling_projection_diagnostic_v0/frame_diagnostics.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M22_frame_scaling_projection_diagnostic_v0/matching/matched_proposals.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M22_frame_scaling_projection_diagnostic_v0/matching/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M22_frame_scaling_projection_diagnostic_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M22_frame_scaling_projection_diagnostic_v0/report.md`

사실:

- Status: `frame_scaling_projection_diagnostic_ready`.
- Docker image: `research2/real-smoke:latest`, image id `8ada6e0c043e`, size 1.64GB.
- Max scans: 1.
- Max frames per scan: 6.
- Max predictions per frame: 20.
- Scanned frames: 6.
- Frames with written predictions: 6.
- Raw predictions: 1664.
- Written predictions: 120.
- Skipped no-depth predictions: 15.
- Validator error rows: 0.
- Validator warning rows: 0.
- Matched proposal rows: 7.
- Matched target rows: 7.
- False-positive proposal rows: 113.
- Proposal precision smoke: 0.058333.
- Scan target recall smoke: 0.137255.
- Label-overlap target recall smoke: 0.218750.
- Mean matched centroid error: 0.402223m.
- Matched labels: plant 5, box 1, chair 1.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M22 supports separating frame coverage, projection loss, and matching failure after removing the M20 early stop.
- E003-M22 does not support real RGB-D/open-vocabulary robustness because it is still one-scan diagnostic output and not a visibility-aware detector benchmark.

에이전트 추론:

- Frame coverage is not the immediate bottleneck because all 6 sampled frames produce schema-valid predictions.
- Projection no-depth loss is small relative to raw predictions, but same-label over-threshold false positives dominate matching failures.
- The next unit should test proposal consolidation/calibration before scaling this detector route to more scans.

사용자 판단 필요:

- None for E003-M22. E003-M23 is recorded below.

## E003-M23 Proposal Consolidation Calibration

Implementation unit: `E003-M23_proposal_consolidation_calibration_v0`.

Stage: one-scan detector calibration diagnostic, not paper-table evaluation.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/run_m23_proposal_calibration.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/run_m23_proposal_calibration.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M23_proposal_consolidation_calibration_v0/sweep_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M23_proposal_consolidation_calibration_v0/selected_proposals.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M23_proposal_consolidation_calibration_v0/selected_matched_proposals.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M23_proposal_consolidation_calibration_v0/selected_target_recall_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M23_proposal_consolidation_calibration_v0/selected_label_metrics.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M23_proposal_consolidation_calibration_v0/selected_config.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M23_proposal_consolidation_calibration_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M23_proposal_consolidation_calibration_v0/report.md`

사실:

- Status: `proposal_calibration_diagnostic_ready`.
- Input proposal rows: 120.
- Sweep rows: 1188.
- Baseline retained proposal rows: 120.
- Baseline matched target rows: 7.
- Baseline false-positive proposal rows: 113.
- Baseline proposal precision: 0.058333.
- Baseline fixed label-overlap target recall: 0.218750.
- Selected confidence threshold: 0.3.
- Selected min depth pixels: 500.
- Selected NMS radius: 1.0m.
- Selected score mode: `confidence`.
- Selected retained proposal rows: 12.
- Selected matched target rows: 4.
- Selected false-positive proposal rows: 8.
- Selected proposal precision: 0.333333.
- Selected scan target recall: 0.078431.
- Selected fixed label-overlap target recall: 0.125000.
- Selected calibration F1: 0.181818.
- Full-match-preserving config retained proposal rows: 97.
- Full-match-preserving matched target rows: 7.
- Full-match-preserving false-positive proposal rows: 90.
- Full-match-preserving proposal precision: 0.072165.
- Near-match-preserving config matched target rows: 6.
- Near-match-preserving false-positive proposal rows: 40.
- Near-match-preserving proposal precision: 0.130435.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M23 supports a calibration/consolidation diagnostic over M22 detector proposals.
- E003-M23 does not support real perception robustness because the sweep is tuned on one scan and uses 3DSSG matching only for evaluation.

에이전트 추론:

- Calibration can reduce duplicate and low-support false positives, but the selected config trades away target recall.
- Preserving all M22 matches barely improves precision, so threshold/NMS alone is not enough for a paper-table real perception claim.
- The next unit should separate visibility-aware denominator error from prompt/threshold/projection error before scaling to more scans.

사용자 판단 필요:

- None for E003-M23. E003-M24 is recorded below.

## E003-M24 Visibility Prompt Projection Gate

Implementation unit: `E003-M24_visibility_prompt_projection_gate_v0`.

Stage: one-scan visibility/prompt/projection denominator diagnostic, not paper-table evaluation.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/run_m24_visibility_prompt_projection_gate.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/run_m24_visibility_prompt_projection_gate.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M24_visibility_prompt_projection_gate_v0/target_visibility_frame_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M24_visibility_prompt_projection_gate_v0/target_denominator_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M24_visibility_prompt_projection_gate_v0/label_bottleneck_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M24_visibility_prompt_projection_gate_v0/gate_decision.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M24_visibility_prompt_projection_gate_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M24_visibility_prompt_projection_gate_v0/report.md`

사실:

- Status: `visibility_prompt_projection_gate_ready`.
- Evaluated scans: 1.
- Evaluated frames: 6.
- Scan-level evaluation target rows: 51.
- Active M22 prompt target rows: 32.
- Prompt-not-active target rows: 19.
- Centroid frustum-visible target rows: 8.
- Depth-valid projected target rows: 7.
- Depth-consistent visible-proxy target rows: 5.
- M22 matched target rows: 7.
- M23 selected matched target rows: 4.
- M22 matched outside centroid frustum proxy rows: 2.
- Detector/threshold missed depth-consistent visible target rows: 0.
- M22 recall over scan denominator: 0.137255.
- M22 recall over active prompt denominator: 0.218750.
- M22 recall over centroid frustum-visible proxy denominator: 0.625000.
- M22 recall over depth-consistent visible-proxy denominator: 1.000000.
- M23 recall over depth-consistent visible-proxy denominator: 0.600000.
- Dominant bottleneck category: `not_centroid_projected_in_sampled_frames`.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M24 supports separating active-prompt coverage, visibility-proxy denominator, depth/projection support, and detector matching in one diagnostic.
- E003-M24 does not support real RGB-D/open-vocabulary robustness because the visibility proxy uses target centroids and one scan's sampled frames.

에이전트 추론:

- M22 low scan-level recall is partly a denominator/prompt-budget artifact: 19 / 51 targets were not active prompts and only 5 / 51 targets were depth-consistent centroid visible under the sampled frames.
- M22 matched all 5 depth-consistent visible-proxy targets, but 2 matched targets fall outside the centroid-frustum proxy; this means the proxy is useful for debugging, not a final true-visibility metric.
- M23 improves precision but drops matched targets, so the next detector step should use a visibility-aware denominator and match-preserving calibration.

사용자 판단 필요:

- None for E003-M24. E003-M25 is recorded below.

## E003-M25 Visibility Prompt Rerun Gate

Implementation unit: `E003-M25_visibility_prompt_rerun_gate_v0`.

Stage: prompt-expanded rerun contract and command plan, not detector execution.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m25_visibility_prompt_rerun.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m25_visibility_prompt_rerun.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M25_visibility_prompt_rerun_gate_v0/scan_prompt_budget_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M25_visibility_prompt_rerun_gate_v0/denominator_contract.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M25_visibility_prompt_rerun_gate_v0/calibration_policy.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M25_visibility_prompt_rerun_gate_v0/docker_rerun_plan.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M25_visibility_prompt_rerun_gate_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M25_visibility_prompt_rerun_gate_v0/report.md`

사실:

- Status: `visibility_prompt_rerun_gate_ready`.
- M17 staged scans: 8.
- Total evaluation target rows: 344.
- Current max labels: 12.
- Expanded max labels: 32.
- Max target label count: 30.
- Current active eval target rows: 239 / 344.
- Expanded active eval target rows: 344 / 344.
- Prompt coverage gain rows: 105.
- Primary calibration policy: `m23_full_match_preserving_v0`.
- Pilot Docker rerun max scans: 2.
- Pilot Docker rerun max frames per scan: 12.
- Pilot Docker rerun max labels: 32.
- Pilot Docker rerun max predictions per frame: 60.
- Pilot Docker rerun max predictions: 1440.
- Pilot Docker rerun threshold/text-threshold: 0.08 / 0.08.
- Post calibration command uses `run_m23_proposal_calibration.py --selection-policy full_match_preserving`.
- `full_match_preserving` smoke check on M22 keeps 7 matched target rows.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M25 supports fixing the prompt-expanded rerun contract for a later real-detector pilot.
- E003-M25 does not support real RGB-D/open-vocabulary robustness because it does not execute the detector rerun.

에이전트 추론:

- Prompt cap 12 is too small for the staged real-proposal scans because it excludes 105 / 344 evaluation target rows.
- Max labels 32 covers all current staged target labels because the maximum per-scan target label count is 30.
- Match-preserving calibration should be primary for the next run because the M23 precision-selected policy drops matched targets before the visibility denominator is stable.

사용자 판단 필요:

- None for E003-M25. E003-M26 is recorded below.

## E003-M26 Prompt Expanded Multiscan Docker Rerun

Implementation unit: `E003-M26_prompt_expanded_multiscan_docker_rerun_v0`.

Stage: prompt-expanded two-scan Docker detector pilot, match-preserving calibration, and visibility denominator post-check. This is not paper-table evaluation.

Commands:

```bash
python experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py \
  --out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M26_prompt_expanded_multiscan_docker_rerun_v0/detector_rerun \
  --build --docker-sudo --sudo-password-stdin \
  --max-scans 2 --max-frames-per-scan 12 --max-labels 32 \
  --max-predictions 1440 --max-predictions-per-frame 60 \
  --threshold 0.08 --text-threshold 0.08

python experiments/E003_perception_noise_expansion/tools/run_m23_proposal_calibration.py \
  --m22-dir experiments/E003_perception_noise_expansion/artifacts/E003-M26_prompt_expanded_multiscan_docker_rerun_v0/detector_rerun \
  --out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M26_prompt_expanded_multiscan_docker_rerun_v0/match_preserving_calibration \
  --selection-policy full_match_preserving

python experiments/E003_perception_noise_expansion/tools/run_m24_visibility_prompt_projection_gate.py \
  --m22-dir experiments/E003_perception_noise_expansion/artifacts/E003-M26_prompt_expanded_multiscan_docker_rerun_v0/detector_rerun \
  --m23-dir experiments/E003_perception_noise_expansion/artifacts/E003-M26_prompt_expanded_multiscan_docker_rerun_v0/match_preserving_calibration \
  --out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M26_prompt_expanded_multiscan_docker_rerun_v0/visibility_denominator \
  --max-labels 32

python experiments/E003_perception_noise_expansion/tools/summarize_m26_prompt_expanded_rerun.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/summarize_m26_prompt_expanded_rerun.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M26_prompt_expanded_multiscan_docker_rerun_v0/detector_rerun/report.md`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M26_prompt_expanded_multiscan_docker_rerun_v0/match_preserving_calibration/report.md`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M26_prompt_expanded_multiscan_docker_rerun_v0/visibility_denominator/report.md`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M26_prompt_expanded_multiscan_docker_rerun_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M26_prompt_expanded_multiscan_docker_rerun_v0/claim_boundary.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M26_prompt_expanded_multiscan_docker_rerun_v0/report.md`

사실:

- Status: `prompt_expanded_multiscan_docker_rerun_pilot_ready`.
- Docker build executed: true.
- Docker run executed: true.
- Evaluated scans: 2.
- Evaluated frames: 24.
- Raw predictions: 9768.
- Written predictions: 1440.
- Max predictions reached: true.
- Not projected or capped predictions: 8272.
- Validator error / warning rows: 0 / 7.
- Scan eval target rows: 99.
- Active prompt target rows: 99.
- Prompt-not-active target rows: 0.
- Matched target rows: 39.
- Scan target recall smoke: 0.393939.
- Label-overlap target recall smoke: 0.414894.
- Proposal precision smoke: 0.027083.
- False-positive proposal rows: 1401.
- Match-preserving calibration retained / matched / false-positive rows: 1348 / 39 / 1309.
- Match-preserving calibration precision: 0.028932.
- Depth-consistent visible-proxy target rows: 35.
- Recall over depth-consistent visible-proxy denominator: 0.628571.
- Detector/threshold missed visible-proxy target rows: 13.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M26 supports saying that the prompt-expanded Docker route produces non-empty multi-scan detector proposal artifacts under the fixed schema.
- E003-M26 supports saying that prompt coverage is no longer the immediate blocker for the two-scan pilot.
- E003-M26 does not support paper-table real RGB-D/open-vocabulary robustness.

에이전트 추론:

- The bottleneck shifted from prompt budget to proposal quality: recall improved over earlier one-scan smoke, but proposal precision remains very low.
- The detector output is cap-limited, so wider scaling should wait until detector scoring, frame/label caps, projection loss, and false-positive consolidation are separated.
- Match-preserving calibration preserves matched targets but does not solve false-positive domination.

사용자 판단 필요:

- None for E003-M26. E003-M27 is recorded below.

## E003-M27 False Positive Cap Bottleneck

Implementation unit: `E003-M27_false_positive_cap_bottleneck_v0`.

Stage: M26 detector-output bottleneck analysis and next detector policy decision. This is not paper-table evaluation.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/analyze_m27_false_positive_cap_bottleneck.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/analyze_m27_false_positive_cap_bottleneck.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M27_false_positive_cap_bottleneck_v0/frame_cap_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M27_false_positive_cap_bottleneck_v0/false_positive_label_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M27_false_positive_cap_bottleneck_v0/policy_decision.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M27_false_positive_cap_bottleneck_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M27_false_positive_cap_bottleneck_v0/report.md`

사실:

- Status: `false_positive_cap_bottleneck_ready`.
- Evaluated scans: 2.
- Evaluated frames: 24.
- Raw predictions: 9768.
- Written predictions: 1440.
- Skipped no-depth predictions: 56.
- Lower-bound cap/post-depth rejected rows: 8272.
- Saturated frames: 24 / 24.
- Baseline proposal precision: 0.027083.
- Selected match-preserving precision: 0.028932.
- Baseline / selected matched rows: 39 / 39.
- Baseline / selected false-positive rows: 1401 / 1309.
- Calibration false-positive reduction: 92.
- Same-label over-threshold false-positive rows after selected calibration: 1302.
- No-same-label false-positive rows after selected calibration: 7.
- No-target labels with detector predictions: 2.
- Top selected false-positive labels: box 188, chair 185, table 118, plant 117, light 63, sofa 56, picture 53, cabinet 53.
- Selected next detector policy: `cap_aware_label_balanced_ranking_v0`.
- Next recommended unit: `E003-M28 cap-aware label-balanced detector policy smoke`.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M27 supports a diagnostic claim that M26 is blocked by cap pressure and false-positive domination, not prompt coverage.
- E003-M27 does not support real RGB-D/open-vocabulary robustness or a paper-table detector benchmark result.

에이전트 추론:

- Wider scan/frame scaling should wait because every sampled frame saturates the per-frame cap and selected precision remains near 0.03.
- Raising caps first is likely to increase false positives unless ranking and label-balanced caps are fixed first.
- Threshold/depth/NMS-only calibration is insufficient because it preserves 39 matches but removes only 92 false positives.
- The next detector policy should clean label mapping, rank before cap with confidence/depth support, use per-label caps, and apply same-label spatial consolidation.

사용자 판단 필요:

- None for E003-M27. E003-M28 is recorded below.

## E003-M28 Cap Aware Label Balanced Policy

Implementation unit: `E003-M28_cap_aware_label_balanced_policy_v0`.

Stage: artifact-replay smoke over M26 written proposals. This is not Docker pre-cap execution and not paper-table evaluation.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/run_m28_cap_aware_policy_smoke.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/run_m28_cap_aware_policy_smoke.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M28_cap_aware_label_balanced_policy_v0/policy_sweep_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M28_cap_aware_label_balanced_policy_v0/selected_proposals.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M28_cap_aware_label_balanced_policy_v0/selected_matched_proposals.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M28_cap_aware_label_balanced_policy_v0/selected_target_recall_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M28_cap_aware_label_balanced_policy_v0/selected_label_metrics.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M28_cap_aware_label_balanced_policy_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M28_cap_aware_label_balanced_policy_v0/report.md`

사실:

- Status: `cap_aware_label_balanced_policy_smoke_ready`.
- Input proposal rows: 1440.
- Enabled prompt labels: 85.
- Label-cleaned proposal rows: 1433.
- Dropped non-prompt label rows: 7.
- Dropped not-scan-prompt label rows: 0.
- Baseline matched target rows: 39.
- Baseline false-positive rows: 1401.
- Baseline precision: 0.027083.
- Selected score mode: `confidence`.
- Selected per-scan-label cap: 24.
- Selected spatial consolidation radius: 0.5m.
- Selected proposal rows: 407.
- Selected matched target rows: 32.
- Selected false-positive rows: 375.
- Selected precision: 0.078624.
- Selected false-positive reduction vs baseline: 1026.
- Selected matched target delta vs baseline: -7.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M28 supports an artifact-replay diagnostic that label-balanced cap-aware ranking can reduce written-proposal false positives under the M26 denominator.
- E003-M28 does not support a final real RGB-D/open-vocabulary robustness claim because the policy is replayed after M26's detector cap, not inside the detector before cap.

에이전트 추론:

- The selected replay policy is worth integrating into the Docker runner before wider scaling because it reduces false positives substantially while retaining 32 / 39 current matches.
- The 7-match loss must remain visible in the claim boundary; this is a policy candidate, not a final detector setting.
- The next Docker run should apply label mapping cleanup, confidence/depth ranking, per-label caps, and same-label consolidation before the per-frame/global cap.

사용자 판단 필요:

- None for E003-M28. E003-M29 is recorded below.

## E003-M29 Pre Cap Policy Integration Gate

Implementation unit: `E003-M29_pre_cap_policy_integration_gate_v0`.

Stage: runner contract gate. This records where the current Docker runner applies caps and how `cap_aware_label_balanced_ranking_v0` must be exposed as runner args and output diagnostics. It does not rerun Docker detector inference.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m29_pre_cap_policy_integration.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m29_pre_cap_policy_integration.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M29_pre_cap_policy_integration_gate_v0/runner_insertion_points.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M29_pre_cap_policy_integration_gate_v0/runner_args_contract.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M29_pre_cap_policy_integration_gate_v0/output_contract.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M29_pre_cap_policy_integration_gate_v0/integration_contract.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M29_pre_cap_policy_integration_gate_v0/docker_rerun_plan.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M29_pre_cap_policy_integration_gate_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M29_pre_cap_policy_integration_gate_v0/report.md`

사실:

- Status: `pre_cap_policy_integration_gate_ready`.
- Current detector result loop line: 351.
- Current global cap check line: 355.
- Current per-frame cap check line: 358.
- Current proposal row append line: 375.
- Current final JSONL write line: 422.
- Selected policy id: `cap_aware_label_balanced_ranking_v0`.
- Selected score mode: `confidence`.
- Selected per-scan-label cap: 24.
- Selected spatial consolidation radius: 0.5m.
- New runner args contract is ready.
- New output contract is ready.
- Docker rerun plan is ready.
- Runner code updated in M29: false.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M29 supports a reproducible implementation contract for moving `cap_aware_label_balanced_ranking_v0` before detector output caps.
- E003-M29 does not support a detector-result claim because it does not rerun Docker detector inference.

에이전트 추론:

- The current cap site is inside the detector result loop, so M28 post-hoc replay can miss raw candidates that were truncated before replay.
- M30 should collect raw projected candidates first, then apply label cleanup, scoring, same-label spatial consolidation, per-scan-label cap, and final global cap.
- `--max-predictions` should remain the final output cap under the pre-cap policy; `--max-predictions-per-frame` must not truncate raw candidates before policy ranking.

사용자 판단 필요:

- None for E003-M29. E003-M30 is recorded below.

## E003-M30 Pre Cap Policy Docker Rerun

Implementation unit: `E003-M30_pre_cap_policy_docker_rerun_v0`.

Stage: Docker runner implementation and two-scan pilot rerun. This implements `cap_aware_label_balanced_ranking_v0` inside the container runner, passes it through the host wrapper, reruns the fixed M26 detector pilot, and applies the existing matching, calibration, and visibility post-checks.

Command:

```bash
printf 'a\n' | python experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py --out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M30_pre_cap_policy_docker_rerun_v0/detector_rerun --build --docker-sudo --sudo-password-stdin --max-scans 2 --max-frames-per-scan 12 --max-labels 32 --max-predictions 1440 --max-predictions-per-frame 60 --threshold 0.08 --text-threshold 0.08 --candidate-selection-policy cap_aware_label_balanced_ranking_v0 --selection-score-mode confidence --pre-cap-per-scan-label-cap 24 --pre-cap-spatial-consolidation-radius-m 0.5
python experiments/E003_perception_noise_expansion/tools/run_m23_proposal_calibration.py --m22-dir experiments/E003_perception_noise_expansion/artifacts/E003-M30_pre_cap_policy_docker_rerun_v0/detector_rerun --out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M30_pre_cap_policy_docker_rerun_v0/match_preserving_calibration --selection-policy full_match_preserving
python experiments/E003_perception_noise_expansion/tools/run_m24_visibility_prompt_projection_gate.py --m22-dir experiments/E003_perception_noise_expansion/artifacts/E003-M30_pre_cap_policy_docker_rerun_v0/detector_rerun --m23-dir experiments/E003_perception_noise_expansion/artifacts/E003-M30_pre_cap_policy_docker_rerun_v0/match_preserving_calibration --out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M30_pre_cap_policy_docker_rerun_v0/visibility_denominator --max-labels 32
python experiments/E003_perception_noise_expansion/tools/summarize_m30_pre_cap_policy_rerun.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/docker/real_proposals/run_rgbd_ov_proposals.py`
- `experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py`
- `experiments/E003_perception_noise_expansion/tools/summarize_m30_pre_cap_policy_rerun.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M30_pre_cap_policy_docker_rerun_v0/detector_rerun/`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M30_pre_cap_policy_docker_rerun_v0/match_preserving_calibration/`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M30_pre_cap_policy_docker_rerun_v0/visibility_denominator/`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M30_pre_cap_policy_docker_rerun_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M30_pre_cap_policy_docker_rerun_v0/claim_boundary.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M30_pre_cap_policy_docker_rerun_v0/report.md`

사실:

- Status: `pre_cap_policy_docker_rerun_pilot_ready`.
- Docker build executed: true.
- Docker run executed: true.
- Candidate selection policy: `cap_aware_label_balanced_ranking_v0`.
- Pre-cap policy applied: true.
- Raw predictions: 9768.
- Projected candidates: 9496.
- Policy input candidates: 8969.
- Spatial consolidated candidates: 848.
- Final written predictions: 830.
- Max predictions reached after policy: false.
- Validator error/warning rows: 0 / 0.
- M26 matched target rows: 39.
- M30 matched target rows: 48.
- Matched target delta vs M26: +9.
- M26 false-positive proposal rows: 1401.
- M30 false-positive proposal rows: 782.
- False-positive delta vs M26: -619.
- M26 proposal precision: 0.027083.
- M30 proposal precision: 0.057831.
- Precision delta vs M26: +0.030748.
- Depth-consistent visible-proxy target rows: 35.
- Recall over depth-consistent visible-proxy denominator: 0.857143.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M30 supports saying the pre-cap policy can be executed inside the Docker detector runner under the fixed M26 pilot conditions.
- E003-M30 supports a two-scan pilot comparison showing improved matched target count, false-positive count, and proposal precision over M26.
- E003-M30 does not support a final real RGB-D/open-vocabulary robustness claim because this is still a two-scan pilot and needs failure/recall tradeoff analysis.

에이전트 추론:

- The key comparison is M30 vs M26, not M30 alone, because M26 fixed prompt coverage but was cap/false-positive dominated.
- M30 is stronger than the M28 replay because the policy is applied before the final output cap and sees projected candidates that M28 could not replay.
- The next unit should identify which labels, frames, and target rows explain gains and remaining misses before scaling beyond the two-scan pilot.

사용자 판단 필요:

- None for E003-M30. E003-M31 is recorded below.

## E003-M31 Pre Cap Policy Tradeoff Analysis

Implementation unit: `E003-M31_pre_cap_policy_tradeoff_analysis_v0`.

Stage: analysis-only comparison over M26, M28, and M30 artifacts. This does not rerun Docker. It records target-level transitions, label-level tradeoffs, frame-level proposal changes, and scaling blockers.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/analyze_m31_pre_cap_tradeoffs.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/analyze_m31_pre_cap_tradeoffs.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M31_pre_cap_policy_tradeoff_analysis_v0/target_transition_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M31_pre_cap_policy_tradeoff_analysis_v0/label_tradeoff_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M31_pre_cap_policy_tradeoff_analysis_v0/frame_tradeoff_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M31_pre_cap_policy_tradeoff_analysis_v0/scaling_blocker_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M31_pre_cap_policy_tradeoff_analysis_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M31_pre_cap_policy_tradeoff_analysis_v0/report.md`

사실:

- Status: `pre_cap_policy_tradeoff_analysis_ready`.
- Evaluated scans: 2.
- Scan eval target rows: 99.
- M26 / M28 / M30 matched target rows: 39 / 32 / 48.
- M30 gains/losses vs M26: 15 / 6.
- Stable matched / stable missed: 33 / 45.
- M26 / M28 / M30 false-positive rows: 1401 / 375 / 782.
- M26 / M28 / M30 proposal precision: 0.027083 / 0.078624 / 0.057831.
- M30 depth-consistent visible-proxy target rows: 35.
- M30 missed visible-proxy target rows: 5.
- Top gain labels: clothes +2, kitchen cabinet +2, backpack +1, bag +1, blanket +1.
- Top loss label: plant -6.
- Top false-positive labels: table 47, chair 42, box 41, light 41, plant 38.
- Scaling blocker rows: 7.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M31 supports a two-scan diagnostic claim that the pre-cap policy improves the M26 detector pilot's recall/precision tradeoff.
- E003-M31 does not support a final real RGB-D/open-vocabulary robustness claim because scale, true visibility, and remaining false positives are unresolved.

에이전트 추론:

- M30 is better than M26 on matched targets and false positives, while M28 remains a high-precision post-hoc replay with lower matched-target count.
- The recall loss is concentrated in `plant`; this must be inspected before treating M30 as a final policy.
- The next scaled rerun should keep M30's pre-cap policy but track label-specific false positives and visible-proxy misses explicitly.

사용자 판단 필요:

- None for E003-M31. E003-M32 is recorded below.

## E003-M32 Scaled Pre Cap Rerun Gate

Implementation unit: `E003-M32_scaled_pre_cap_rerun_gate_v0`.

Stage: planning-only gate over M17, M30, and M31 artifacts. This does not rerun Docker. It fixes the scaled pre-cap rerun scope, command plan, and required post-rerun blocker diagnostics.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m32_scaled_pre_cap_rerun.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m32_scaled_pre_cap_rerun.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M32_scaled_pre_cap_rerun_gate_v0/scaled_scope_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M32_scaled_pre_cap_rerun_gate_v0/blocker_response_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M32_scaled_pre_cap_rerun_gate_v0/scaled_rerun_plan.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M32_scaled_pre_cap_rerun_gate_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M32_scaled_pre_cap_rerun_gate_v0/report.md`

사실:

- Status: `scaled_pre_cap_rerun_gate_ready`.
- Selected route: `staged_8scan_24frame_pre_cap_scaled_pilot`.
- Staged / selected scans: 8 / 8.
- Selected frame budget: 192 / 459 sampled frames.
- Selected evaluation target rows: 344.
- Run config: max labels 32, max predictions 10000, max predictions per frame 60, threshold/text-threshold 0.08/0.08.
- Pre-cap policy config: `cap_aware_label_balanced_ranking_v0`, score mode `confidence`, per-scan-label cap 24, spatial consolidation radius 0.5m, raw candidate collection cap 200000.
- Estimated raw predictions: 78144.
- Estimated final prediction rows: 6640.
- M31 blocker rows tracked: 7.
- Docker command ready: true.
- Docker run executed: false.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M32 supports fixing a scaled rerun contract for the pre-cap policy.
- E003-M32 does not support a detector-result claim because it does not execute Docker inference.

에이전트 추론:

- The next Docker run should scale across all 8 staged scans while keeping a 24-frame-per-scan budget before full-frame evaluation.
- M31 blockers should be carried into post-rerun diagnostics, especially `plant` recall loss and table/chair/box/light/plant false positives.
- A paper-table detector claim remains blocked until the E003-M33 scaled result has failure and label analysis.

사용자 판단 필요:

- None for E003-M32. E003-M33 is recorded below.

## E003-M33 Scaled Pre Cap Policy Docker Rerun

Implementation unit: `E003-M33_scaled_pre_cap_policy_docker_rerun_v0`.

Stage: Docker detector rerun plus repository-local calibration, visibility post-check, and summary. This executes the M32 scaled command plan.

Commands:

```bash
python experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py --out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M33_scaled_pre_cap_policy_docker_rerun_v0/detector_rerun --build --docker-sudo --sudo-password-stdin --max-scans 8 --max-frames-per-scan 24 --max-labels 32 --max-predictions 10000 --max-predictions-per-frame 60 --threshold 0.08 --text-threshold 0.08 --candidate-selection-policy cap_aware_label_balanced_ranking_v0 --selection-score-mode confidence --pre-cap-per-scan-label-cap 24 --pre-cap-spatial-consolidation-radius-m 0.5 --raw-candidate-collection-cap 200000
python experiments/E003_perception_noise_expansion/tools/run_m23_proposal_calibration.py --m22-dir experiments/E003_perception_noise_expansion/artifacts/E003-M33_scaled_pre_cap_policy_docker_rerun_v0/detector_rerun --out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M33_scaled_pre_cap_policy_docker_rerun_v0/match_preserving_calibration --selection-policy full_match_preserving
python experiments/E003_perception_noise_expansion/tools/run_m24_visibility_prompt_projection_gate.py --m22-dir experiments/E003_perception_noise_expansion/artifacts/E003-M33_scaled_pre_cap_policy_docker_rerun_v0/detector_rerun --m23-dir experiments/E003_perception_noise_expansion/artifacts/E003-M33_scaled_pre_cap_policy_docker_rerun_v0/match_preserving_calibration --out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M33_scaled_pre_cap_policy_docker_rerun_v0/visibility_denominator --max-labels 32
python experiments/E003_perception_noise_expansion/tools/summarize_m33_scaled_pre_cap_policy_rerun.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/summarize_m33_scaled_pre_cap_policy_rerun.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M33_scaled_pre_cap_policy_docker_rerun_v0/detector_rerun/`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M33_scaled_pre_cap_policy_docker_rerun_v0/match_preserving_calibration/`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M33_scaled_pre_cap_policy_docker_rerun_v0/visibility_denominator/`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M33_scaled_pre_cap_policy_docker_rerun_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M33_scaled_pre_cap_policy_docker_rerun_v0/report.md`

사실:

- Status: `scaled_pre_cap_policy_docker_rerun_ready`.
- Selected route: `staged_8scan_24frame_pre_cap_scaled_pilot`.
- Docker build/run executed: true / true.
- Estimated detector wall time seconds: 3333.
- Evaluated scans / frames: 8 / 192.
- Evaluation target rows: 344.
- Raw / projected / policy-input / spatial-consolidated / final proposal rows: 67639 / 65812 / 60435 / 4284 / 3414.
- Raw candidate cap reached: false.
- Max predictions reached after policy: false.
- Validator errors/warnings: 0 / 0.
- Matched target rows: 204.
- False-positive proposal rows: 3210.
- Proposal precision: 0.059754.
- Scan target recall: 0.593023.
- Depth-consistent visible-proxy target rows: 154.
- Recall over depth-consistent visible-proxy denominator: 0.915584.
- Detector/threshold missed visible-proxy target rows: 13.
- Match-preserving calibration changed selected proposals: false.
- Top false-positive labels: plant 176, shelf 133, chair 129, sofa 117, table 116, box 111, cabinet 110, lamp 106.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M33 supports that the Dockerized `cap_aware_label_balanced_ranking_v0` route can scale from the two-scan pilot to 8 staged `3RScan` scans under a fixed output schema.
- E003-M33 supports a scaled diagnostic result, not a final real RGB-D/open-vocabulary robustness claim.
- E003-M33 does not support a deployable perception/search claim because false-positive load remains high and visibility is still a centroid/depth proxy.

에이전트 추론:

- The scaled run improves the denominator size enough for label-level failure analysis, but proposal precision remains low.
- Match-preserving calibration selected the baseline-like config, so simple confidence/depth/NMS filtering did not reduce false positives without risking matched target loss.
- The next unit should analyze M33 false-positive labels, visible-proxy misses, and M31 blocker resolution before any paper-table claim.

사용자 판단 필요:

- None for E003-M33. Next is E003-M34 scaled pre-cap failure and label analysis.

## E003-M34 Scaled Failure Analysis

Implementation unit: `E003-M34_scaled_pre_cap_failure_analysis_v0`.

Stage: repository-local failure analysis over M31 and M33 artifacts. This does not execute Docker. It fixes the label-level false-positive summary, visible-proxy miss rows, and M31 blocker resolution status after the 8-scan scaled rerun.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/analyze_m34_scaled_failures.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/analyze_m34_scaled_failures.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M34_scaled_pre_cap_failure_analysis_v0/label_failure_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M34_scaled_pre_cap_failure_analysis_v0/visible_miss_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M34_scaled_pre_cap_failure_analysis_v0/visible_label_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M34_scaled_pre_cap_failure_analysis_v0/blocker_resolution_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M34_scaled_pre_cap_failure_analysis_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M34_scaled_pre_cap_failure_analysis_v0/report.md`

사실:

- Status: `scaled_pre_cap_failure_analysis_ready`.
- M33 evaluated scans / frames: 8 / 192.
- M33 matched targets / scan targets: 204 / 344.
- M33 false-positive proposal rows: 3210.
- M33 proposal precision: 0.059754.
- M33 scan target recall: 0.593023.
- Depth-consistent visible-proxy target rows: 154.
- Visible-proxy missed target rows: 13.
- Visible-proxy recall: 0.915584.
- Top false-positive labels: plant 176, shelf 133, chair 129, sofa 117, table 116, box 111, cabinet 110, lamp 106.
- Top visible-miss labels: picture 2, pillow 2, basket 1, couch 1, curtain 1, cushion 1, pile of books 1, plant 1.
- M31 blocker status counts after M34: resolved 1, partially resolved 1, reframed 1, analyzed-not-resolved 1, unresolved 2, unresolved claim-boundary 1.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M34 supports a scaled diagnostic failure analysis for the 8-scan real RGB-D/open-vocabulary proposal route.
- E003-M34 does not support a final real RGB-D/open-vocabulary robustness claim because false-positive load remains unresolved and visibility remains a proxy.
- E003-M34 does not support a deployable search-policy claim from real detector proposals yet.

에이전트 추론:

- The previous scale-count blocker is resolved, but the main technical blocker moved to false-positive suppression.
- Scan-level missed targets are mostly not visible under the current sampled-frame proxy; visible-proxy misses are much smaller and should be reported separately.
- The next useful unit is a false-positive suppression route decision before connecting M33 proposals into E001/E002 search-policy tables.

사용자 판단 필요:

- None for E003-M34. Next is E003-M35 false-positive suppression route decision.

## E003-M35 False Positive Suppression Route

Implementation unit: `E003-M35_false_positive_suppression_route_v0`.

Stage: repository-local route decision over M33/M34 artifacts. This does not execute Docker. It selects the first false-positive suppression family and fixes the M36 recall-preserving sweep contract.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m35_false_positive_suppression.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m35_false_positive_suppression.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M35_false_positive_suppression_route_v0/global_rank_probe_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M35_false_positive_suppression_route_v0/label_cap_probe_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M35_false_positive_suppression_route_v0/label_priority_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M35_false_positive_suppression_route_v0/route_candidate_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M35_false_positive_suppression_route_v0/suppression_route_plan.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M35_false_positive_suppression_route_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M35_false_positive_suppression_route_v0/report.md`

사실:

- Status: `false_positive_suppression_route_ready`.
- Baseline proposal rows: 3414.
- Baseline matched targets: 204.
- Baseline false-positive rows: 3210.
- Baseline precision: 0.059754.
- Top false-positive labels: plant 176, shelf 133, chair 129, sofa 117, table 116, box 111, cabinet 110, lamp 106.
- Selected route: `recall_preserving_rank_cap_sweep_v0`.
- Selected probe policy: `visible_miss_guarded_labelwise_rank_cap_v0`.
- Selected probe proposal rows: 1986.
- Selected probe matched targets: 204.
- Selected probe false-positive rows: 1782.
- Selected probe precision: 0.102719.
- Selected probe false-positive reduction vs M33: 1428.
- Selected probe matched target retention: 1.0.
- Best global fixed-rank cap with at least 95% matched target retention: rank <= 20, matched targets 195 / 204, false-positive rows 2819.
- Docker run executed: false.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M35 supports selecting a recall-preserving suppression sweep route for the M33 real-proposal artifacts.
- E003-M35 does not support a final suppression method claim because it does not execute the selected M36 sweep or a held-out validation.
- E003-M35 does not support a paper-table real RGB-D/open-vocabulary robustness claim.

에이전트 추론:

- Rank-cap suppression is the first route because it uses fields already present in M33 outputs and can be tested without another long Docker run.
- The selected probe is promising as a ceiling, but any cap selected using M33 match labels is diagnostic until validated on a split that did not choose the caps.
- Confidence/depth-only filtering should stay as a baseline arm, not the primary route.

사용자 판단 필요:

- None for E003-M35. Next is E003-M36 recall-preserving suppression sweep smoke.

## E003-M36 Recall Preserving Suppression Sweep

Implementation unit: `E003-M36_recall_preserving_suppression_sweep_v0`.

Stage: repository-local offline sweep over M33 proposal artifacts. This does not execute Docker. It filters M33 proposals under fixed/global rank caps, confidence/depth baselines, labelwise diagnostic caps, and the M35 visible-miss-guarded probe, then re-runs target matching after every filter.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/run_m36_recall_preserving_suppression_sweep.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/run_m36_recall_preserving_suppression_sweep.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M36_recall_preserving_suppression_sweep_v0/sweep_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M36_recall_preserving_suppression_sweep_v0/family_summary_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M36_recall_preserving_suppression_sweep_v0/selected_policy_label_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M36_recall_preserving_suppression_sweep_v0/selected_policy_proposals.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M36_recall_preserving_suppression_sweep_v0/selected_policy_target_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M36_recall_preserving_suppression_sweep_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M36_recall_preserving_suppression_sweep_v0/report.md`

사실:

- Status: `recall_preserving_suppression_sweep_ready`.
- Input proposal rows: 3414.
- Evaluation target rows: 344.
- Sweep policy rows: 56.
- Baseline matched targets: 204.
- Baseline false-positive rows: 3210.
- Baseline precision: 0.059754.
- Baseline depth-consistent visible-proxy recall: 0.915584.
- Selected deployable 95pct policy: `global_rank_cap_le_20`.
- `global_rank_cap_le_20` matched targets: 195 / 204.
- `global_rank_cap_le_20` false-positive rows: 2819.
- `global_rank_cap_le_20` precision: 0.064698.
- Selected diagnostic policy: `labelwise_rank_cap_oracle_retain_0p95`.
- `labelwise_rank_cap_oracle_retain_0p95` matched targets: 204 / 204.
- `labelwise_rank_cap_oracle_retain_0p95` false-positive rows: 1585.
- `labelwise_rank_cap_oracle_retain_0p95` precision: 0.114030.
- M35 selected probe after re-matching: `visible_miss_guarded_labelwise_rank_cap_v0`.
- `visible_miss_guarded_labelwise_rank_cap_v0` matched targets / false-positive rows: 204 / 1782.
- Split validation required: true.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M36 supports an offline suppression sweep over the M33 real-proposal artifacts.
- E003-M36 supports a diagnostic ceiling for labelwise rank-cap suppression, not a final method claim.
- E003-M36 does not support a paper-table real RGB-D/open-vocabulary robustness claim because policy selection still needs split validation.

에이전트 추론:

- Deployable fixed hyperparameters give a modest recall-preserving gain, while labelwise diagnostic caps show a much larger ceiling.
- The next step should validate cap selection on a dev/held-out split before adding the policy to the Docker runner.

사용자 판단 필요:

- None for E003-M36. E003-M37 is recorded below.

## E003-M37 Suppression Split Validation Gate

Implementation unit: `E003-M37_suppression_split_validation_v0`.

Stage: repository-local split validation over M33 proposal artifacts. This does not execute Docker. It creates a balanced scan-level dev/heldout split, selects suppression caps on dev scans, applies the selected policy to heldout scans, and compares against heldout baseline and heldout oracle policies.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/run_m37_suppression_split_validation.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/run_m37_suppression_split_validation.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M37_suppression_split_validation_v0/scan_split_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M37_suppression_split_validation_v0/validation_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M37_suppression_split_validation_v0/label_coverage_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M37_suppression_split_validation_v0/split_plan.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M37_suppression_split_validation_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M37_suppression_split_validation_v0/report.md`

사실:

- Status: `suppression_split_validation_gate_ready`.
- Split protocol: `balanced_scan_4_4_v0`.
- Dev / heldout scans: 4 / 4.
- Dev totals: 164 evaluation targets, 107 matched proposals, 1794 proposal rows, 77 visible-proxy target rows.
- Heldout totals: 180 evaluation targets, 97 matched proposals, 1620 proposal rows, 77 visible-proxy target rows.
- Heldout baseline matched targets / false-positive rows / precision: 97 / 1523 / 0.059877.
- Heldout baseline depth-consistent visible-proxy recall: 0.909091.
- Selected candidate policy: `dev_selected_visible_miss_guarded_labelwise_rank_cap_v0`.
- Selected candidate heldout matched targets / false-positive rows / precision: 81 / 1154 / 0.065587.
- Selected candidate matched-target retention: 0.835052.
- Selected fixed policy: `global_rank_cap_le_22_selected_on_train`.
- Selected fixed policy heldout matched targets / false-positive rows / precision: 97 / 1433 / 0.063399.
- Heldout oracle policy: `heldout_oracle_visible_miss_guarded_labelwise_rank_cap_v0`.
- Heldout oracle matched targets / false-positive rows / precision: 97 / 979 / 0.090149.
- Label coverage rows: 85.
- Heldout target labels without dev matched example: 24.
- Label-stratified validation feasible: false.
- Runner integration recommended: false.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M37 supports a split-validation gate for suppression policy selection over M33 real-proposal artifacts.
- E003-M37 does not support Docker runner integration for the dev-selected labelwise policy because heldout matched-target retention drops below the recall-preserving threshold.
- E003-M37 does not support a final real RGB-D/open-vocabulary robustness claim.

에이전트 추론:

- The M36 labelwise oracle ceiling is real as a diagnostic, but it is not yet a deployable method because dev-selected labelwise caps do not transfer under the current split.
- The fixed global cap is safer for recall but too weak for false-positive suppression.
- The next step should test stronger split design or temporal/spatial evidence before touching the Docker runner.

사용자 판단 필요:

- None for E003-M37. E003-M38 is recorded below.

## E003-M38 Split Or Temporal-Spatial Gate

Implementation unit: `E003-M38_split_or_temporal_spatial_gate_v0`.

Stage: repository-local route decision over M33/M37 artifacts. This does not execute Docker. It enumerates feasible scan splits, checks whether stronger split design can cover heldout labels, and tests post-hoc spatial/temporal support filters selected on dev and applied to heldout.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m38_split_or_temporal_spatial_gate.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m38_split_or_temporal_spatial_gate.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M38_split_or_temporal_spatial_gate_v0/split_feasibility_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M38_split_or_temporal_spatial_gate_v0/support_policy_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M38_split_or_temporal_spatial_gate_v0/support_feature_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M38_split_or_temporal_spatial_gate_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M38_split_or_temporal_spatial_gate_v0/report.md`

사실:

- Status: `split_or_temporal_spatial_gate_ready`.
- Split feasibility rows: 210.
- Best split dev / heldout scans: 6 / 2.
- Best split uncovered heldout target labels: 7.
- Best split uncovered heldout target rows: 7.
- Stronger split feasible with current 8 scans: false.
- Support policy rows: 244.
- Selected dev support policy: `spatial_support_or_rank_guard_r1p5m_min3_rank_guard_le_12`.
- Selected support policy heldout matched targets / false-positive rows / precision: 89 / 1406 / 0.059532.
- Selected support policy heldout matched-target retention: 0.917526.
- Heldout oracle support policy: `temporal_support_or_rank_guard_r0p75m_min3_rank_guard_le_20`.
- Heldout oracle support policy matched targets / false-positive rows / precision: 95 / 1336 / 0.066387.
- Selected route: `temporal_spatial_evidence_instrumentation_required`.
- Runner integration recommended: false.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M38 supports a route decision after M37 heldout transfer failure.
- E003-M38 does not support stronger split design as the next solution under the current 8-scan artifact.
- E003-M38 does not support Docker runner integration for the current post-hoc spatial/temporal support filters.
- E003-M38 does not support a final real RGB-D/open-vocabulary robustness claim.

에이전트 추론:

- The current 8-scan artifact is too small and label-sparse for reliable labelwise dev/heldout cap learning.
- Post-hoc support computed after final proposal selection is too weak; temporal/spatial evidence should be instrumented earlier, before or during candidate consolidation.
- The next route should decide which temporal/spatial evidence fields to preserve in the Docker runner or in an immediate post-processing schema before another long detector rerun.

사용자 판단 필요:

- None for E003-M38. Next is E003-M39 temporal-spatial support instrumentation gate.

## E003-M39 Temporal-Spatial Support Instrumentation Gate

Implementation unit: `E003-M39_temporal_spatial_support_instrumentation_gate_v0`.

Stage: repository-local instrumentation contract over M38 route evidence. This does not execute Docker. It fixes where temporal/spatial support evidence should be computed in the real-proposal runner before another long detector rerun.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m39_temporal_spatial_support_instrumentation.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m39_temporal_spatial_support_instrumentation.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M39_temporal_spatial_support_instrumentation_gate_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M39_temporal_spatial_support_instrumentation_gate_v0/instrumentation_contract.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M39_temporal_spatial_support_instrumentation_gate_v0/support_field_contract.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M39_temporal_spatial_support_instrumentation_gate_v0/verification_plan.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M39_temporal_spatial_support_instrumentation_gate_v0/report.md`

사실:

- Status: `temporal_spatial_support_instrumentation_gate_ready`.
- Selected route: `docker_runner_pre_consolidation_support_evidence_v0`.
- Selected insertion point: `select_cap_aware_label_balanced_candidates.after_cleaned_before_grouped`.
- Support policy id: `temporal_spatial_support_evidence_v0`.
- Support radii: 0.75m, 1.0m, 1.5m, and 2.0m.
- Runner instrumentation site ready: true.
- Wrapper pass-through site ready: true.
- Deterministic post-processing route ready: false.
- Docker run executed: false.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M39 supports an implementation decision for where to preserve temporal/spatial proposal support evidence.
- E003-M39 does not support a final real RGB-D/open-vocabulary robustness claim.

에이전트 추론:

- Support evidence should be computed after prompt/label cleanup but before spatial consolidation and caps, because final selected proposal artifacts cannot recover removed raw candidates.
- M40 should implement the runner fields with default behavior preserved, then run a short Docker smoke before any longer rerun.

사용자 판단 필요:

- None for E003-M39. Next is E003-M40 temporal-spatial support runner implementation smoke.

## E003-M40 Temporal-Spatial Support Runner Smoke

Implementation unit: `E003-M40_temporal_spatial_support_runner_smoke_v0`.

Stage: Docker runner implementation smoke. This implements `temporal_spatial_support_evidence_v0` in the real-proposal runner, passes support args through the host wrapper, builds `research2/real-smoke`, and runs a short 1-scan / 2-frame detector smoke.

Command:

```bash
sg docker -c 'python experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py --build --out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M40_temporal_spatial_support_runner_smoke_v0 --max-scans 1 --max-frames-per-scan 2 --max-labels 32 --max-predictions 400 --max-predictions-per-frame 20 --candidate-selection-policy cap_aware_label_balanced_ranking_v0 --selection-score-mode confidence_sqrt_depth --pre-cap-per-scan-label-cap 40 --pre-cap-spatial-consolidation-radius-m 0.5 --raw-candidate-collection-cap 20000 --support-evidence-policy temporal_spatial_support_evidence_v0 --support-evidence-radii-m 0.75,1.0,1.5,2.0'
```

Artifacts:

- `experiments/E003_perception_noise_expansion/docker/real_proposals/run_rgbd_ov_proposals.py`
- `experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M40_temporal_spatial_support_runner_smoke_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M40_temporal_spatial_support_runner_smoke_v0/report.md`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M40_temporal_spatial_support_runner_smoke_v0/container_output/pre_cap_policy_summary.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M40_temporal_spatial_support_runner_smoke_v0/container_output/support_evidence_summary.json`
- `logs/20260508_141745_e003_m40_support_smoke_tmux.log`

사실:

- Status: `temporal_spatial_support_runner_smoke_ready`.
- Docker build/run executed: true / true.
- Scans / frames: 1 / 2.
- Raw predictions / projected candidates / policy input / final predictions: 736 / 662 / 629 / 95.
- Support evidence attached to selected rows: 95 / 95.
- Selected rows with spatial / temporal support at any configured radius: 93 / 58.
- Support row field errors: 0.
- Validator errors/warnings: 0 / 0.
- Matched proposals / false-positive proposals / proposal precision smoke: 5 / 90 / 0.052632.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M40 supports runner-side instrumentation of temporal/spatial proposal support evidence.
- E003-M40 does not support final real RGB-D/open-vocabulary robustness because it is a short smoke, not a heldout policy evaluation.

에이전트 추론:

- Support evidence is now available before downstream support-aware selection or scaled reruns.
- The next unit should decide how support fields affect scoring, consolidation, or caps before another long Docker rerun.

사용자 판단 필요:

- None for E003-M40. Next is E003-M41 support-aware selection policy gate.

## E003-M41 Support-Aware Selection Policy Gate

Implementation unit: `E003-M41_support_aware_selection_policy_gate_v0`.

Stage: repository-local policy gate. This does not execute Docker. It decides how the M40 temporal/spatial support evidence should affect candidate selection before any long rerun.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m41_support_aware_selection_policy.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m41_support_aware_selection_policy.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M41_support_aware_selection_policy_gate_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M41_support_aware_selection_policy_gate_v0/policy_contract.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M41_support_aware_selection_policy_gate_v0/rejected_routes.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M41_support_aware_selection_policy_gate_v0/source_inspection.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M41_support_aware_selection_policy_gate_v0/verification_plan.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M41_support_aware_selection_policy_gate_v0/report.md`

사실:

- Status: `support_aware_selection_policy_gate_ready`.
- Selected score mode: `confidence_sqrt_depth_support_temporal_v0`.
- Selected route: `support_aware_scoring_before_consolidation_and_final_rank`.
- Base score: `confidence * min(1, sqrt(depth_valid_pixel_count) / sqrt(5000))`.
- Temporal factor: `min(1, support_temporal_neighbor_frame_count_r2p0m / 2)`.
- Spatial factor: `min(1, support_spatial_neighbor_count_r1p0m / 8)`.
- Selection score: `base_score * (1 + 0.25 * temporal_factor + 0.10 * spatial_factor)`.
- Hard support filter recommended: false.
- Support cap change recommended: false.
- Long rerun ready: false.

논문 주장:

- E003-M41 supports a policy decision for how to use runner-side temporal/spatial support evidence.
- E003-M41 does not prove proposal-quality improvement because it does not execute Docker or matching.

에이전트 추론:

- M38 makes hard support filtering risky because heldout matched-target retention dropped.
- M40 shows temporal support exists, but selection quality remains weak.
- A soft support-aware score is the lowest-risk next test because it can affect consolidation and ranking without suppressing single-frame candidates.

사용자 판단 필요:

- None for E003-M41. Next is E003-M42 support-aware selection runner smoke.

## E003-M42 Support-Aware Selection Runner Smoke

Implementation unit: `E003-M42_support_aware_selection_runner_smoke_v0`.

Stage: Docker runner smoke. This implements `confidence_sqrt_depth_support_temporal_v0`, rebuilds `research2/real-smoke`, and runs the same 1-scan / 2-frame smoke scope as E003-M40 for a controlled comparison.

Command:

```bash
sg docker -c 'python experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py --build --out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M42_support_aware_selection_runner_smoke_v0 --max-scans 1 --max-frames-per-scan 2 --max-labels 32 --max-predictions 400 --max-predictions-per-frame 20 --candidate-selection-policy cap_aware_label_balanced_ranking_v0 --selection-score-mode confidence_sqrt_depth_support_temporal_v0 --pre-cap-per-scan-label-cap 40 --pre-cap-spatial-consolidation-radius-m 0.5 --raw-candidate-collection-cap 20000 --support-evidence-policy temporal_spatial_support_evidence_v0 --support-evidence-radii-m 0.75,1.0,1.5,2.0'
```

Artifacts:

- `experiments/E003_perception_noise_expansion/docker/real_proposals/run_rgbd_ov_proposals.py`
- `experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M42_support_aware_selection_runner_smoke_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M42_support_aware_selection_runner_smoke_v0/report.md`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M42_support_aware_selection_runner_smoke_v0/container_output/pre_cap_policy_summary.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M42_support_aware_selection_runner_smoke_v0/container_output/support_evidence_summary.json`
- `logs/20260508_145516_e003_m42_support_aware_smoke_tmux.log`

사실:

- Status: `support_aware_selection_runner_smoke_ready`.
- Docker build/run executed: true / true.
- Score mode: `confidence_sqrt_depth_support_temporal_v0`.
- Scans / frames: 1 / 2.
- Raw predictions / projected candidates / policy input / final predictions: 736 / 662 / 629 / 95.
- Support evidence attached to selected rows: 95 / 95.
- Validator errors/warnings: 0 / 0.
- Matched proposals / false-positive proposals / proposal precision smoke: 5 / 90 / 0.052632.
- Delta vs E003-M40 matched / false-positive / precision: 0 / 0 / 0.0.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M42 supports that the selected support-aware score mode is executable in the Docker runner.
- E003-M42 does not support proposal-quality improvement because the short smoke did not change matched proposals, false positives, or precision relative to E003-M40.

에이전트 추론:

- The score mode passed implementation and validation but did not improve proposal-quality metrics under the 1-scan / 2-frame smoke.
- The next unit should decide whether a larger support-instrumented replay is enough to test the score, or whether the support-aware score needs redesign before a long Docker rerun.

사용자 판단 필요:

- None for E003-M42. Next is E003-M43 support-aware scaled rerun route gate.

## E003-M43 Support-Aware Scaled Rerun Route Gate

Implementation unit: `E003-M43_support_aware_scaled_rerun_route_gate_v0`.

Stage: route gate. This compares E003-M40 and E003-M42, checks whether existing artifacts can support offline replay, and decides whether to run an immediate long Docker rerun, replay, or redesign the score first.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m43_support_aware_scaled_rerun_route.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m43_support_aware_scaled_rerun_route.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M43_support_aware_scaled_rerun_route_gate_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M43_support_aware_scaled_rerun_route_gate_v0/report.md`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M43_support_aware_scaled_rerun_route_gate_v0/m40_m42_comparison.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M43_support_aware_scaled_rerun_route_gate_v0/route_decision.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M43_support_aware_scaled_rerun_route_gate_v0/candidate_pool_contract.json`

사실:

- Status: `support_aware_scaled_rerun_route_gate_ready`.
- Selected route: `pre_cap_candidate_pool_export_then_offline_replay_v0`.
- M42 vs M40 matched / false-positive / precision delta: 0 / 0 / 0.0.
- M42 vs M40 common selected rows: 94 / 95.
- M42 vs M40 selected symmetric difference rows: 2.
- M42 vs M40 pre-cap rank changed common rows: 68.
- M42 vs M40 selection-score changed common rows: 89.
- Existing candidate-pool replay available: false.
- Immediate support-aware long rerun recommended: false.
- Runner edit required before next scaled run: true.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M43 supports only a route decision for support-aware proposal evaluation.
- E003-M43 does not support final real RGB-D/open-vocabulary robustness or a paper-table result.

에이전트 추론:

- M42 is a valid runner smoke, but a long support-aware-only rerun would not isolate score-mode ablations.
- The support-aware score is not inert because row ranks and a small part of the selected set changed.
- The next step should export the cleaned, support-instrumented pre-cap candidate pool and replay score modes offline.

사용자 판단 필요:

- None for E003-M43. Next is E003-M44 pre-cap candidate-pool export and offline replay harness smoke.

## E003-M44 Pre-Cap Candidate-Pool Export And Replay Smoke

Implementation unit: `E003-M44_pre_cap_candidate_pool_export_smoke_v0`.

Stage: Docker export smoke plus offline replay. This adds runner-side export of the cleaned pre-cap candidate pool, then checks whether offline replay can reproduce the runner-selected stable candidates for the active support-aware score mode.

Command:

```bash
sg docker -c 'python experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py --build --out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M44_pre_cap_candidate_pool_export_smoke_v0 --max-scans 1 --max-frames-per-scan 2 --max-labels 32 --max-predictions 400 --max-predictions-per-frame 20 --candidate-selection-policy cap_aware_label_balanced_ranking_v0 --selection-score-mode confidence_sqrt_depth_support_temporal_v0 --pre-cap-per-scan-label-cap 40 --pre-cap-spatial-consolidation-radius-m 0.5 --raw-candidate-collection-cap 20000 --support-evidence-policy temporal_spatial_support_evidence_v0 --support-evidence-radii-m 0.75,1.0,1.5,2.0 --export-pre-cap-candidate-pool'
python experiments/E003_perception_noise_expansion/tools/run_m44_pre_cap_replay.py --m44-dir experiments/E003_perception_noise_expansion/artifacts/E003-M44_pre_cap_candidate_pool_export_smoke_v0
```

Artifacts:

- `experiments/E003_perception_noise_expansion/docker/real_proposals/run_rgbd_ov_proposals.py`
- `experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py`
- `experiments/E003_perception_noise_expansion/tools/run_m44_pre_cap_replay.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M44_pre_cap_candidate_pool_export_smoke_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M44_pre_cap_candidate_pool_export_smoke_v0/report.md`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M44_pre_cap_candidate_pool_export_smoke_v0/container_output/pre_cap_candidate_pool.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M44_pre_cap_candidate_pool_export_smoke_v0/offline_replay/coverage.json`
- `logs/20260508_152859_e003_m44_candidate_pool_replay_smoke_tmux.log`

사실:

- Status: `pre_cap_candidate_pool_replay_smoke_ready`.
- Docker smoke status: `pre_cap_candidate_pool_export_smoke_ready`.
- Candidate pool rows: 629.
- Candidate pool rows with support policy: 629 / 629.
- Candidate pool field errors: 0.
- Runner selected rows: 95.
- Offline replay selected rows for `confidence_sqrt_depth_support_temporal_v0`: 95.
- Ordered reproduction match: true.
- Set reproduction match: true.
- Validator errors/warnings: 0 / 0.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M44 supports a short reproducibility smoke for replayable pre-cap proposal candidates.
- E003-M44 does not support final real RGB-D/open-vocabulary robustness because it is not scaled heldout evidence.

에이전트 추론:

- The candidate-pool export gives a stable substrate for score-mode ablations without repeating detector inference.
- The next scaled unit can export one 8-scan candidate pool, then compare support-aware scoring offline.

사용자 판단 필요:

- None for E003-M44. Next is E003-M45 scaled candidate-pool export and support-aware replay.

## E003-M45 Scaled Candidate-Pool Export And Support-Aware Replay

Implementation unit: `E003-M45_scaled_candidate_pool_export_replay_v0`.

Stage: long-running Docker export plus offline score-mode comparison. This reruns the 8-scan / 24-frame scaled detector route with pre-cap candidate-pool export enabled, then replays `confidence`, `confidence_sqrt_depth`, and `confidence_sqrt_depth_support_temporal_v0` over the same candidate pool and matches each replay output against the M17 target denominator.

Command launched:

```bash
sg docker -c 'python experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py --build --out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M45_scaled_candidate_pool_export_replay_v0 --max-scans 8 --max-frames-per-scan 24 --max-labels 32 --max-predictions 10000 --max-predictions-per-frame 60 --candidate-selection-policy cap_aware_label_balanced_ranking_v0 --selection-score-mode confidence_sqrt_depth_support_temporal_v0 --pre-cap-per-scan-label-cap 24 --pre-cap-spatial-consolidation-radius-m 0.5 --raw-candidate-collection-cap 200000 --support-evidence-policy temporal_spatial_support_evidence_v0 --support-evidence-radii-m 0.75,1.0,1.5,2.0 --export-pre-cap-candidate-pool'
python experiments/E003_perception_noise_expansion/tools/run_m45_scaled_replay.py --m45-dir experiments/E003_perception_noise_expansion/artifacts/E003-M45_scaled_candidate_pool_export_replay_v0
```

Job status:

- Launched: true.
- tmux session: `e003_m45_scaled_pool`.
- Log: `logs/20260508_155219_e003_m45_scaled_candidate_pool_export_replay_tmux.log`.
- Output path: `experiments/E003_perception_noise_expansion/artifacts/E003-M45_scaled_candidate_pool_export_replay_v0/`.
- Expected files: `container_output/pre_cap_candidate_pool.jsonl`, `coverage.json`, `offline_replay/coverage.json`.
- Verification command: `python experiments/E003_perception_noise_expansion/tools/run_m45_scaled_replay.py --m45-dir experiments/E003_perception_noise_expansion/artifacts/E003-M45_scaled_candidate_pool_export_replay_v0`.
- Status: complete / verified.
- tmux log exit code: 0.

Result interpretation contract:

- Artifact: `experiments/E003_perception_noise_expansion/artifacts/E003-M45_scaled_candidate_pool_export_replay_v0/interpretation_contract.json`.
- Frozen before final M45 metric inspection: true.
- Baseline: E003-M33 `confidence` route, matched targets 204, false positives 3210, proposal precision 0.059754.
- Primary score mode: `confidence_sqrt_depth_support_temporal_v0`.
- Reference score modes: `confidence`, `confidence_sqrt_depth`.

사실:

- Hard pass requires `scaled_candidate_pool_replay_ready`, validator errors/warnings 0 / 0, support-aware matched targets at least 204, false positives below 3210, proposal precision above 0.059754, and no lexicographic regression against `confidence_sqrt_depth`.
- Weak positive requires clean replay, support-aware matched targets at least 194, false positives at most 3049, and proposal precision above 0.059754.
- Fail/redesign triggers include matched targets below 194, false positives not reduced from 3210, precision not improved over 0.059754, or a strict regression against `confidence_sqrt_depth`.
- Verification status: `scaled_candidate_pool_replay_ready`.
- Candidate pool rows: 60,435.
- Validator errors/warnings: 0 / 0.
- Frozen contract verdict: `fail_redesign`.
- `confidence`: 204 matched targets, 3210 false positives, proposal precision 0.059754.
- `confidence_sqrt_depth`: 198 matched targets, 3209 false positives, proposal precision 0.058116.
- `confidence_sqrt_depth_support_temporal_v0`: 196 matched targets, 3211 false positives, proposal precision 0.057529.
- The support-aware score failed hard pass and weak positive because it lost matched targets, did not reduce false positives, did not improve precision, and regressed against `confidence_sqrt_depth`.

논문 주장:

- E003-M45 supports a scaled offline comparison over one shared detector candidate pool.
- E003-M45 does not support a positive support-aware proposal-quality claim for the current score.
- It does not establish final real RGB-D/open-vocabulary robustness, real navigation `SR`, or real navigation `SPL`.

Reviewer defense boundary:

- Current evidence is an 8-scan staged artifact, not a broad heldout benchmark.
- The visibility denominator is a depth-consistent centroid projection proxy, not ground-truth visibility or embodied observability.
- The detector path currently uses one `GroundingDINO`-based RGB-D backprojection backend; it does not yet compare against external proposal or mapping baselines such as `Grounded-SAM`, `OpenMask3D`, `OVIR-3D`, `ConceptGraphs`, `HOV-SG`, or `Open3DSG`.
- Heldout transfer is not established because current split evidence showed weak label coverage under the 8-scan split.
- Therefore, even if M45 improves matched targets, false positives, and proposal precision, the defensible claim is limited to support-aware proposal-quality evidence under this staged route.

에이전트 추론:

- Freezing these thresholds before final M45 metrics reduces post-hoc interpretation risk.
- The next claim-relevant step should be E003-M46 support-aware score redesign or external proposal baseline gate, not real proposal to stale-memory bridge yet.
- A reviewer could reasonably reject a final robustness claim unless the next stages add larger heldout evaluation and at least one external detector/proposal baseline.

사용자 판단 필요:

- Resolved by E003-M46: prioritize external detector/proposal or mapping baseline feasibility first.

## E003-M46 Score Redesign Or External Baseline Gate

Implementation unit: `E003-M46_score_redesign_or_external_gate_v0`.

Stage: repository-local route gate over the M45 candidate pool. This tests whether bounded local score redesign can repair the failed support-aware result before moving to external proposal or mapping baselines.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m46_score_redesign_or_external_gate.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m46_score_redesign_or_external_gate.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M46_score_redesign_or_external_gate_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M46_score_redesign_or_external_gate_v0/policy_sweep.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M46_score_redesign_or_external_gate_v0/route_decision.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M46_score_redesign_or_external_gate_v0/report.md`

사실:

- Status: `score_redesign_or_external_gate_ready`.
- Candidate pool rows: 60,435.
- Policies swept: 12.
- Hard pass policy count: 0.
- Weak positive policy count: 0.
- Best policy by matched / false-positive / precision: `confidence`, 204 / 3210 / 0.059754.
- `confidence_sqrt_depth` and several weak/guarded support variants produced 198 matched targets, 3209 false positives, precision 0.058116.
- Current support boost produced 196 matched targets, 3211 false positives, precision 0.057529.
- Current support boost lost 2 matched targets relative to `confidence_sqrt_depth` and gained 0.
- Selected route: `external_proposal_baseline_gate_first`.
- Next recommended unit: `E003-M47 external proposal/mapping baseline feasibility gate`.

논문 주장:

- E003-M46 does not create a new paper claim.
- It shows that bounded local support-score redesign is not enough to recover M45 into claim-ready evidence.

에이전트 추론:

- The current temporal/spatial support evidence is too saturated to serve as a discriminative main ranking signal.
- The next top-tier-relevant improvement should prioritize stronger proposal/mapping baselines or richer support evidence, not minor support score-weight tuning.

사용자 판단 필요:

- Resolved by E003-M47: first external route is `Grounded-SAM`.

## E003-M47 External Baseline Feasibility Gate

Implementation unit: `E003-M47_external_baseline_feasibility_gate_v0`.

Stage: external route selection after M45/M46 failure. This ranks candidate external proposal or mapping routes by current harness fit, direct diagnostic value for the M45 failure, schema compatibility, top-tier reviewer value, dependency risk, and data conversion burden.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m47_external_baseline_feasibility.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m47_external_baseline_feasibility.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M47_external_baseline_feasibility_gate_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M47_external_baseline_feasibility_gate_v0/candidate_routes.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M47_external_baseline_feasibility_gate_v0/route_decision.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M47_external_baseline_feasibility_gate_v0/report.md`

사실:

- Status: `external_baseline_feasibility_gate_ready`.
- Selected route: `Grounded-SAM`.
- Route scores: `Grounded-SAM` 39, `OpenMask3D` 24, `ConceptGraphs` 16, `OVIR-3D` 14, `HOV-SG` 6.
- Next recommended unit: `E003-M48 Grounded-SAM mask-backprojection proposal smoke`.

논문 주장:

- E003-M47 does not create a new paper claim.
- It fixes the first external feasibility route needed to separate proposal/backend failure from stale-memory logic.

에이전트 추론:

- `Grounded-SAM` is the best first route because the current runner already uses `GroundingDINO`, posed RGB-D frames, prompt labels, and depth backprojection.
- `Grounded-SAM` directly tests whether M45 false positives and target losses come from box-based depth projection; masks can be backprojected into the existing `real_proposal_prediction_jsonl_v0` schema.
- `OpenMask3D` has stronger 3D baseline value, but the first gate should not be dominated by MinkowskiEngine/checkpoint/scene-format staging.
- `ConceptGraphs` and `HOV-SG` are valuable map/navigation baselines after proposal quality stabilizes, not the first diagnosis tool for M45's proposal failure.
- `OVIR-3D` is retrieval-oriented and needs a less direct proposal-row adapter.

사용자 판단 필요:

- None for E003-M47. Next is `E003-M48 Grounded-SAM mask-backprojection proposal smoke`.

## E003-M48 Grounded-SAM Contract

Implementation unit: `E003-M48_grounded_sam_contract_v0`.

Stage: contract gate for replacing box-depth proposal geometry with `Grounded-SAM` mask-depth proposal geometry. This does not download checkpoints or execute Docker inference; it fixes the implementation boundary for the next smoke.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m48_grounded_sam_contract.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m48_grounded_sam_contract.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M48_grounded_sam_contract_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M48_grounded_sam_contract_v0/contract.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M48_grounded_sam_contract_v0/optional_fields.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M48_grounded_sam_contract_v0/report.md`

사실:

- Status: `grounded_sam_contract_ready`.
- Backend id: `grounded_sam_mask_backproject_v0`.
- Existing schema: `real_proposal_prediction_jsonl_v0`.
- Existing required proposal fields are preserved.
- Optional mask diagnostic fields added: 9.
- Allowed inputs: posed RGB-D frames, camera pose/intrinsics, M17 prompt labels, `GroundingDINO` boxes/scores, and `SAM` masks from the same frame.
- Blocked inputs: `3DSSG` object instance ids, evaluation target ids, `candidate_is_target`, and `matched_3dssg_instance_id` before matching.
- M45 bbox-depth confidence baseline remains 204 matched targets, 3210 false positives, proposal precision 0.059754.
- Docker/model smoke executed: false.
- Real RGB-D/open-vocabulary claim ready: false.
- Next recommended unit: `E003-M49 Grounded-SAM Docker/model smoke implementation`.

논문 주장:

- E003-M48 does not create a new result claim.
- It fixes the contract needed to test whether mask-depth backprojection is better than box-depth backprojection for proposal geometry.

에이전트 추론:

- `Grounded-SAM` remains the correct first external implementation route because it minimally changes the current `GroundingDINO` runner while directly isolating the box-depth projection bottleneck.
- `OpenMask3D` should be the later 3D instance baseline route after this mask-depth route is understood.
- `ConceptGraphs` and `HOV-SG` should remain later mapping/navigation baselines, not immediate proposal-geometry diagnosis routes.

사용자 판단 필요:

- None before E003-M49. The next unit should implement a short Docker/model smoke from this contract.

## E003-M49 Grounded-SAM Docker/Model Smoke

Implementation unit: `E003-M49_grounded_sam_smoke_v0`.

Stage: background Docker/model smoke for the `E003-M48` contract. This builds the current `research2/real-smoke` image, runs `GroundingDINO` plus `SAM` over a small RGB-D subset, writes `grounded_sam_mask_backproject_v0` proposal rows, validates the existing schema, and runs the M21 matcher.

Working directory:

```bash
/home/yoohyun/research2
```

Command launched:

```bash
sg docker -c 'python experiments/E003_perception_noise_expansion/tools/run_m49_grounded_sam_smoke.py --build --out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M49_grounded_sam_smoke_v0 --max-scans 1 --max-frames-per-scan 2 --max-labels 12 --max-predictions 400 --max-predictions-per-frame 20 --threshold 0.08 --text-threshold 0.08'
```

Job status:

- Launched: true.
- Status: complete / verified.
- tmux session: `e003_m49_grounded_sam`.
- Log: `logs/20260510_001637_e003_m49_grounded_sam_smoke_tmux.log`.
- Output path: `experiments/E003_perception_noise_expansion/artifacts/E003-M49_grounded_sam_smoke_v0/`.
- Expected files: `container_output/real_proposals.jsonl`, `container_output/backend_contract.json`, `container_output/model_smoke.json`, `validator/coverage.json`, `matching/coverage.json`, `coverage.json`.
- Verification command: `python -m json.tool experiments/E003_perception_noise_expansion/artifacts/E003-M49_grounded_sam_smoke_v0/coverage.json`.

사실:

- `run_rgbd_ov_proposals.py` now accepts `--detector grounded_sam_mask_backproject_v0`.
- The runner now accepts `--segmentation-backend sam_vit_b`, `--sam-model-id`, `--mask-depth-filter`, `--mask-min-depth-valid-pixels`, and `--mask-point-sample-cap`.
- The `Grounded-SAM` path uses `GroundingDINO` boxes and `facebook/sam-vit-base` masks through `transformers`.
- The output preserves `real_proposal_prediction_jsonl_v0` required fields.
- The output adds mask diagnostic fields including `geometry_source`, `mask_backend_id`, `mask_area_px`, `mask_depth_valid_pixel_count`, `mask_depth_valid_ratio`, `mask_centroid_world_m`, and `bbox_centroid_world_m`.
- Status: `grounded_sam_model_smoke_ready`.
- Docker build/run executed: true / true.
- Prediction rows: 24.
- Mask geometry rows: 24.
- Rows with mask RLE: 24.
- Validator errors/warnings: 0 / 0.
- M21 matcher status: `detector_matching_smoke_ready`.
- Matched proposal/target rows: 1 / 1.
- False-positive proposal rows: 23.
- Proposal precision smoke: 0.041667.
- Scan target recall smoke: 0.019608.
- Label-overlap target recall smoke: 0.043478.
- Mean matched centroid error: 0.916258m.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M49 can support only an implementation smoke if it completes.
- E003-M49 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

에이전트 추론:

- If E003-M49 completes with non-empty mask-depth rows, the next step should be E003-M50 same-subset bbox-depth vs mask-depth comparison.
- The comparison should test whether mask-depth geometry improves matched targets, false positives, or centroid error relative to the current bbox-depth route.

사용자 판단 필요:

- None until E003-M49 finishes or fails.

## E003-M50 Same-Subset Bbox-Depth Vs Mask-Depth

Implementation unit: `E003-M50_same_subset_bbox_vs_mask_v0`.

Stage: same-subset diagnostic comparison. This reruns the current `GroundingDINO` bbox-depth backend with the same scan/frame/label/prediction budget as E003-M49 and compares the M21 matching results against the E003-M49 `Grounded-SAM` mask-depth rows.

Command:

```bash
sg docker -c 'python experiments/E003_perception_noise_expansion/tools/run_m50_same_subset_comparison.py --out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M50_same_subset_bbox_vs_mask_v0'
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/run_m50_same_subset_comparison.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M50_same_subset_bbox_vs_mask_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M50_same_subset_bbox_vs_mask_v0/comparison_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M50_same_subset_bbox_vs_mask_v0/report.md`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M50_same_subset_bbox_vs_mask_v0/bbox_depth_baseline/`

사실:

- Status: `same_subset_comparison_ready`.
- Same-subset config: max scans 1, max frames per scan 2, max labels 12, max predictions 400, max predictions per frame 20.
- Bbox-depth backend: `groundingdino_rgbd_backproject_v0`.
- Mask-depth backend: `grounded_sam_mask_backproject_v0`.
- Bbox-depth: 31 proposals, 2 matched targets, 29 false positives, proposal precision 0.064516, scan target recall 0.039216, mean matched centroid error 0.591356m.
- Mask-depth: 24 proposals, 1 matched target, 23 false positives, proposal precision 0.041667, scan target recall 0.019608, mean matched centroid error 0.916258m.
- Mask minus bbox: matched targets -1, false positives -6, proposal precision -0.022849, scan target recall -0.019608, mean centroid error +0.324903m.
- Weak positive: false.
- Hard positive: false.
- Selected next route: `do_not_scale_grounded_sam_yet`.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M50 is a same-subset diagnostic gate, not a final robustness result.
- E003-M50 does not support scaling `Grounded-SAM` as the next paper-table route.
- It does not support real RGB-D/open-vocabulary robustness, heldout transfer, or navigation/search claims.

에이전트 추론:

- `Grounded-SAM` mask-depth reduced false positives only because it produced fewer proposals, but it also lost a matched target, lowered precision/recall, and worsened centroid error.
- Immediate scaled `Grounded-SAM` rerun would be a weak use of compute.
- The next unit should decide between continuing with the stronger current bbox-depth route, doing targeted mask failure analysis, or moving to a stronger 3D instance baseline such as `OpenMask3D`.

사용자 판단 필요:

- None if `do_not_scale_grounded_sam_yet` is accepted.

## E003-M51 Post-M50 Route Decision

Implementation unit: `E003-M51_post_m50_route_decision_v0`.

Stage: route gate after negative same-subset `Grounded-SAM` evidence. It ranks artifact-local mask failure analysis, current `bbox-depth` continuation, and `OpenMask3D` feasibility.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m51_post_m50_route_decision.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m51_post_m50_route_decision.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M51_post_m50_route_decision_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M51_post_m50_route_decision_v0/route_decision.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M51_post_m50_route_decision_v0/candidate_routes.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M51_post_m50_route_decision_v0/report.md`

사실:

- Status: `post_m50_route_decision_ready`.
- Selected route: `targeted_mask_failure_analysis_first`.
- Route ranking: `targeted_mask_failure_analysis_first` score 43, `bbox_depth_continuation_after_mask_check` score 34, `openmask3d_feasibility_after_mask_failure` score 24.
- Next recommended unit: `E003-M52 Grounded-SAM mask failure analysis`.
- Real RGB-D/open-vocabulary claim ready: false.

논문 주장:

- E003-M51 does not create a paper result claim.
- It fixes the next route after a negative same-subset `Grounded-SAM` comparison.

에이전트 추론:

- Do not scale `Grounded-SAM` immediately because M50 is negative.
- Do not jump straight to `OpenMask3D` before checking whether M50 exposed a simple mask projection or filtering issue.
- Artifact-local mask failure analysis is the cheapest reviewer-defensible next step.

사용자 판단 필요:

- None if the selected diagnostic route is accepted.

## E003-M52 Grounded-SAM Mask Failure Analysis

Implementation unit: `E003-M52_grounded_sam_mask_failure_v0`.

Stage: artifact-local failure analysis over M49/M50. This separates candidate dropout, common-target centroid shift, and match-set composition without another Docker run.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/analyze_m52_grounded_sam_mask_failure.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/analyze_m52_grounded_sam_mask_failure.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M52_grounded_sam_mask_failure_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M52_grounded_sam_mask_failure_v0/diagnosis.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M52_grounded_sam_mask_failure_v0/candidate_pairing_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M52_grounded_sam_mask_failure_v0/target_transition_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M52_grounded_sam_mask_failure_v0/report.md`

사실:

- Status: `grounded_sam_mask_failure_analysis_ready`.
- Bbox-depth proposal rows: 31.
- Mask-depth proposal rows: 24.
- Common candidate rows by scan/frame/raw index: 24.
- Bbox-only candidate rows: 7.
- Mask-only candidate rows: 0.
- `Grounded-SAM` skipped mask projection rows: 16.
- Lost-by-mask targets: 1, label `plant`.
- Matched-by-both targets: 1.
- Common same-target match-distance delta mask minus bbox: -0.018907m.
- Aggregate M50 mean centroid error delta mask minus bbox: +0.3249025m.
- Exact per-skipped mask reason is not observable from current artifacts.

논문 주장:

- E003-M52 does not create a final paper claim.
- E003-M52 supports a route decision: the current `Grounded-SAM` mask-depth path should not be scaled as-is.
- Real RGB-D/open-vocabulary robustness remains unsupported.

에이전트 추론:

- Target loss primary cause is `mask_projection_candidate_dropout_before_matching`.
- Centroid worsening primary cause is `match_set_composition_after_easy_target_dropout`.
- The common matched `box` target is slightly better under mask-depth; the aggregate centroid error worsens because the easy bbox-depth `plant` match is dropped before matching.
- The false-positive reduction is mostly fewer rows without precision gain.
- Next recommended unit: `E003-M53 bbox-depth continuation and failure-boundary repair gate`.

사용자 판단 필요:

- None if bbox-depth continuation is accepted as the next immediate route. `OpenMask3D` remains the next external 3D instance baseline candidate after the current bbox-depth route is stabilized.

## E003-M53 Bbox-Depth Continuation Repair Gate

Implementation unit: `E003-M53_bbox_continuation_repair_gate_v0`.

Stage: route gate after negative `Grounded-SAM` diagnosis. This decides whether to keep repairing the current `bbox-depth` route, jump to `OpenMask3D`, or move to map-level external baselines such as `Open3DSG`, `ConceptGraphs`, and `HOV-SG`.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m53_bbox_continuation_repair_gate.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m53_bbox_continuation_repair_gate.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M53_bbox_continuation_repair_gate_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M53_bbox_continuation_repair_gate_v0/route_decision.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M53_bbox_continuation_repair_gate_v0/candidate_routes.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M53_bbox_continuation_repair_gate_v0/external_baseline_boundary.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M53_bbox_continuation_repair_gate_v0/report.md`

사실:

- Status: `bbox_continuation_repair_gate_ready`.
- Selected route: `search_critical_bbox_failure_boundary_first`.
- Next recommended unit: `E003-M54 search-critical bbox-depth failure-boundary audit`.
- Route ranking: `search_critical_bbox_failure_boundary_first` score 46, `deployable_bbox_suppression_repair_now` score 30, `openmask3d_feasibility_now` score 27, `conceptgraphs_mapping_baseline_now` score 19, `open3dsg_mapping_baseline_now` score 16, `hovsg_navigation_mapping_baseline_now` score 10.
- M33 scaled bbox-depth artifact covers 8 scans and 192 frames.
- M33 matched / FP / precision: 204 / 3210 / 0.059754.
- M52 scaled `Grounded-SAM` recommended: false.
- M36/M37/M38 show generic suppression, split selection, and simple support-aware fixes are not claim-ready.

논문 주장:

- E003-M53 does not create a paper result claim.
- E003-M53 fixes the immediate route after negative `Grounded-SAM` evidence.
- Real RGB-D/open-vocabulary robustness remains unsupported.

에이전트 추론:

- 지금 `OpenMask3D`로 바로 넘어가는 것은 이르다. 현재 best `bbox-depth` route가 search decision에서 어떤 실패를 실제로 만드는지 먼저 좁혀야 한다.
- `OpenMask3D`는 later external 3D instance proposal baseline으로 적합하다. 이유는 2D bbox/mask-depth projection이 아니라 3D instance mask proposal 품질을 비교할 수 있기 때문이다.
- `Open3DSG`, `ConceptGraphs`, `HOV-SG`는 더 넓은 map/scene-graph/navigation baseline이다. 현재 E003의 직접 blocker인 proposal-row false positive / target dropout을 가장 작게 진단하는 baseline은 아니다.
- 따라서 이들은 E005 map/scene-graph/navigation baseline expansion에서 다루는 것이 더 맞다.

사용자 판단 필요:

- None if E003-M54 search-critical bbox-depth failure-boundary audit is accepted as the next immediate unit.

## E003-M54 Search-Critical Bbox Failure Boundary

Implementation unit: `E003-M54_search_critical_bbox_failure_boundary_v0`.

Stage: artifact-local audit linking E001/E002 search rows, M33 scaled `bbox-depth` detector failures, and M45 replay variants. This separates exact current query-instance causality from label-level detector risk.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/audit_m54_search_critical_bbox_boundary.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/audit_m54_search_critical_bbox_boundary.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M54_search_critical_bbox_failure_boundary_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M54_search_critical_bbox_failure_boundary_v0/query_search_boundary_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M54_search_critical_bbox_failure_boundary_v0/label_search_risk_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M54_search_critical_bbox_failure_boundary_v0/m45_label_policy_delta_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M54_search_critical_bbox_failure_boundary_v0/report.md`

사실:

- Status: `search_critical_bbox_failure_boundary_ready`.
- E001 query rows: 294.
- E002 reachable-first rows: 267.
- M33 detector scans / frames: 8 / 192.
- E001 current `rescan_id` overlap with M33 detector scans: 0.
- Exact current query-instance joins: 0.
- Reference-memory-only joins: 120.
- Label overlap count: 21.
- Existing E001/E002 search failures with label-level detector risk: 7.
- Search-critical label candidates: `pillow` priority 8, `chair` priority 7, `plant` / `shelf` / `sofa` priority 6.
- M45 frozen verdict remains `fail_redesign`; support-aware score does not repair the bridge.
- Next recommended unit: `E003-M55 dynamic-pair-aligned real-proposal bridge gate`.

논문 주장:

- E003-M54 does not establish a final real RGB-D/open-vocabulary search robustness claim.
- Current M33/M45 detector failures cannot be causally attached to E001/E002 current search instances because detector-ready scans do not overlap with E001 current rescans.
- Until a dynamic-pair-aligned real-proposal denominator exists, M33/M45 can only support label-level detector stress evidence.

에이전트 추론:

- `chair` and `pillow` are the strongest immediate bridge labels because they already cause E001/E002 search failures and also show M33 detector risk.
- `plant`, `shelf`, `sofa`, `table`, and `box` are detector-pressure risks, but the current artifact alignment does not prove they cause search decision failure.
- Running `OpenMask3D` next would improve proposal-quality coverage but would not by itself fix the missing current-rescan join to E001/E002.

사용자 판단 필요:

- None if `E003-M55 dynamic-pair-aligned real-proposal bridge gate` is accepted as the next route.
- Choose immediate `OpenMask3D` only if the goal is proposal-quality evidence with a weaker search-bridge claim.

## E003-M55 Dynamic-Pair Bridge Gate

Implementation unit: `E003-M55_dynamic_pair_bridge_gate_v0`.

Stage: route gate after M54. This chooses how to connect real RGB-D/open-vocabulary proposal evidence to E001/E002 dynamic-pair search decisions.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m55_dynamic_pair_bridge_gate.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m55_dynamic_pair_bridge_gate.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M55_dynamic_pair_bridge_gate_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M55_dynamic_pair_bridge_gate_v0/route_decision.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M55_dynamic_pair_bridge_gate_v0/candidate_routes.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M55_dynamic_pair_bridge_gate_v0/bridge_target_scan_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M55_dynamic_pair_bridge_gate_v0/report.md`

사실:

- Status: `dynamic_pair_bridge_gate_ready`.
- Selected route: `stage_search_failure_current_rescans_first`.
- Route ranking: direct current-rescan staging score 46, detector-aligned search proxy score 31, reference-memory-side bridge score 18, `OpenMask3D` before bridge score 15, label-level stress only score 14.
- M54 exact current query-instance joins: 0.
- M16 current real RGB-D proposal-ready query rows: 0.
- Search-failure current rescans: 4.
- Search-failure current rescans with semantic triplet ready: 4.
- Search-failure current rescans already sequence-ready: 0.
- Priority scans: `5555106a-36f1-29c0-8913-df1ba3c3cfd5`(`chair`), `4731976c-f9f7-2a1a-95cc-31c4d1751d0b`(`pillow`), `ddc73795-765b-241a-9c5d-b97744afe077`(`pillow`), `10b17957-3938-2467-88a5-9e9254930dad`(`pillow`).
- Next recommended unit: `E003-M56 current-rescan sequence payload staging plan`.

논문 주장:

- E003-M55 does not create a paper result claim.
- E003-M55 fixes the bridge route needed before real RGB-D/open-vocabulary proposal evidence can support downstream search claims.
- Real RGB-D/open-vocabulary search robustness remains blocked until current-rescan detector outputs are available and evaluated against E001/E002 rows.

에이전트 추론:

- The direct route is stronger than an M17 detector-aligned proxy because it preserves dynamic-pair current-rescan identity.
- `OpenMask3D` should wait until the bridge denominator is fixed; otherwise it improves proposal-quality evidence without solving the search-causality gap.
- E003-M56 should plan the 4-scan sequence payload staging under the long-running/background task rule.

사용자 판단 필요:

- None if E003-M56 current-rescan sequence payload staging plan is accepted as the next unit.

## E003-M56 Current-Rescan Sequence Staging Plan

Implementation unit: `E003-M56_current_rescan_sequence_staging_plan_v0`.

Stage: staging plan for the 4 current rescans selected by E003-M55. This records exact download/decompression commands, output paths, log path, and verification command. It does not launch the long-running job.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m56_current_rescan_sequence_staging.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m56_current_rescan_sequence_staging.py`
- `experiments/E003_perception_noise_expansion/tools/verify_m56_sequence_payloads.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M56_current_rescan_sequence_staging_plan_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M56_current_rescan_sequence_staging_plan_v0/command_plan.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M56_current_rescan_sequence_staging_plan_v0/download_manifest.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M56_current_rescan_sequence_staging_plan_v0/run_sequence_staging.sh`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M56_current_rescan_sequence_staging_plan_v0/prelaunch_verification/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M56_current_rescan_sequence_staging_plan_v0/report.md`

사실:

- Status: `current_rescan_sequence_staging_plan_ready`.
- Target scan count: 4.
- Prelaunch sequence-ready target scan count: 0.
- Download-required scan count: 4.
- Decompression-required scan count after zip appears: 4.
- Background job status: `not_launched`.
- Default downloader: `wget -c`.
- Fallback downloader: official `local_dataset/3RScan/download_3rscan.py --type sequence.zip`.
- Launch command is recorded in `command_plan.json`.
- Verification command is recorded in `command_plan.json` and uses `verify_m56_sequence_payloads.py --require-ready`.
- Next recommended unit: `E003-M57 launch current-rescan sequence staging background job`.

논문 주장:

- E003-M56 does not create a paper result claim.
- E003-M56 fixes the reproducible staging plan needed before current-rescan detector outputs can be evaluated against E001/E002 rows.
- Real RGB-D/open-vocabulary search robustness remains blocked until the staging job completes and detector inference/evaluation runs.

에이전트 추론:

- `wget -c` is preferred because it is resumable and matches the long-running/background task rule.
- The job should be launched with `tmux` and logged under `logs/`, not monitored continuously by Codex.
- The next unit should launch the recorded command and then return to other work until verification is needed.

사용자 판단 필요:

- None; E003-M57 has launched the recorded background job.

## E003-M57 Sequence Staging Job Launch

Implementation unit: `E003-M57_sequence_staging_job_launch_v0`.

Stage: background launch for the long-running M56 sequence staging job.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/launch_m57_sequence_staging_job.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/launch_m57_sequence_staging_job.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M57_sequence_staging_job_launch_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M57_sequence_staging_job_launch_v0/report.md`

사실:

- Status: `sequence_staging_job_launched`.
- Background job status at launch: `running`.
- Completion status: M56 verifier reports `sequence_payloads_ready`, ready rows 4 / 4.
- tmux session: `e003_m56_sequence_stage`.
- Log path: `logs/20260510_170443_e003_m56_sequence_staging.log`.
- Target scans: `5555106a-36f1-29c0-8913-df1ba3c3cfd5`, `4731976c-f9f7-2a1a-95cc-31c4d1751d0b`, `ddc73795-765b-241a-9c5d-b97744afe077`, `10b17957-3938-2467-88a5-9e9254930dad`.
- Verification command: `python experiments/E003_perception_noise_expansion/tools/verify_m56_sequence_payloads.py --manifest experiments/E003_perception_noise_expansion/artifacts/E003-M56_current_rescan_sequence_staging_plan_v0/download_manifest.jsonl --out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M56_current_rescan_sequence_staging_plan_v0/verification --require-ready`.

논문 주장:

- E003-M57 does not create a paper result claim.
- It only prepares the payloads needed before direct current-rescan detector evaluation.

에이전트 추론:

- Do not monitor the job continuously.
- Direct current-rescan detector/evaluation bridge design can start from the verified 4-scan payloads.

사용자 판단 필요:

- None; the background job has ended and the payload verifier passed.

## E003-M58 Direct Current-Rescan Detector Bridge Design

Implementation unit: `E003-M58_direct_current_rescan_bridge_design_v0`.

Stage: design contract after E003-M57. This builds the direct detector/evaluation bridge denominator that connects E001/E002 search-failure rows to the verified current-rescan RGB-D sequences.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m58_direct_current_rescan_bridge.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m58_direct_current_rescan_bridge.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M58_direct_current_rescan_bridge_design_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M58_direct_current_rescan_bridge_design_v0/direct_bridge_query_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M58_direct_current_rescan_bridge_design_v0/real_proposal_query_manifest.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M58_direct_current_rescan_bridge_design_v0/real_proposal_object_targets.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M58_direct_current_rescan_bridge_design_v0/prompt_set.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M58_direct_current_rescan_bridge_design_v0/evaluation_contract.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M58_direct_current_rescan_bridge_design_v0/detector_run_command_plan.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M58_direct_current_rescan_bridge_design_v0/report.md`

사실:

- Status: `direct_current_rescan_bridge_design_ready`.
- Direct bridge query rows: 7.
- Direct bridge base rows: 5.
- Direct bridge scans: 4.
- Target labels: `chair`, `pillow`.
- Linked bridge query target uids: 5 / 5.
- Object target rows: 29.
- Same-label distractor object rows: 24.
- Prompt label count: 2.
- Sampled frame count for next detector run: 93.
- Detector run executed: false.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary search claim ready: false.
- Next recommended unit: `E003-M59 direct current-rescan detector bridge Docker run`.

논문 주장:

- E003-M58 supports saying that the direct current-rescan bridge denominator is ready.
- E003-M58 preserves E001/E002 dynamic-pair current-rescan identity, which was the missing causality link in E003-M54.
- E003-M58 does not support a real RGB-D/open-vocabulary search result because no detector run or query-level bridge evaluation has been executed.

에이전트 추론:

- The next detector run should use the M58 artifact as `--m17-dir` so the existing Docker runner and M21 matcher can be reused.
- Query-level bridge evaluation should be a separate E003-M60 step after detector output exists.
- `OpenMask3D` remains a later external baseline; it should not precede the direct bridge detector run unless this route fails.

사용자 판단 필요:

- None. The next unit should launch or execute the recorded E003-M59 detector command if compute is available.

## E003-M59 Direct Current-Rescan Detector Launch

Implementation unit: `E003-M59_direct_current_rescan_detector_launch_v0`.

Stage: long-running Docker detector launch after E003-M58. This starts the direct current-rescan detector bridge run in a background `tmux` session and records the command, log, output path, expected files, and verification command.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/launch_m59_direct_current_rescan_detector.py --sudo-password-stdin
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/launch_m59_direct_current_rescan_detector.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M59_direct_current_rescan_detector_launch_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M59_direct_current_rescan_detector_launch_v0/report.md`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M59_direct_current_rescan_detector_launch_v0/run_m59_detector.sh`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M59_direct_current_rescan_detector_launch_v0/launch_command.txt`

사실:

- Status: `direct_current_rescan_detector_job_launched`.
- Background job status: `completed`.
- tmux session: `e003_m59_direct_bridge`.
- Log path: `logs/20260511_114356_e003_m59_direct_current_rescan_detector_run.log`.
- Output path: `experiments/E003_perception_noise_expansion/artifacts/E003-M59_direct_current_rescan_detector_run_v0/`.
- Target scans: 4.
- Bridge query rows: 7.
- Expected files are recorded in `coverage.json`.
- Verification command is recorded in `coverage.json`.
- Sudo password value is not recorded.
- Completion verification: passed.
- Validator status: `proposal_schema_smoke_valid`.
- Validator errors/warnings: 0 / 0.
- Matching status: `detector_matching_smoke_ready`.
- Scanned frames: 93.
- Raw predictions: 2015.
- Written proposals: 96.
- Candidate pool rows: 1970.
- Matched proposal rows: 21.
- False-positive proposal rows: 75.
- Proposal precision smoke: 0.218750.
- Scan target recall smoke: 0.724138.
- Label-overlap target recall smoke: 0.724138.

논문 주장:

- E003-M59 supports saying that direct current-rescan detector output is now available and schema/matching checks pass.
- E003-M59 alone does not support a query-level real RGB-D/open-vocabulary search claim; E003-M60 below performs the first detector-to-query join.

에이전트 추론:

- E003-M60 below joins the 96 detector proposals with the 7 M58 bridge query rows.
- The M59 aggregate target recall is promising for the direct bridge denominator, but E003-M60 confirms that false positives and target rank still affect search cost and old-location decision metrics.
- Keep final real RGB-D/open-vocabulary robustness claim blocked until query-level bridge repair and external baseline comparisons exist.

사용자 판단 필요:

- None. E003-M60 has been run below.

## E003-M60 Direct Current-Rescan Query Bridge

Implementation unit: `E003-M60_direct_current_rescan_query_bridge_v0`.

Stage: query-level bridge evaluation after E003-M59. This joins M59 detector proposals with M58 search-failure query rows and keeps target detection separate from search-budget success.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/evaluate_m60_direct_query_bridge.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/evaluate_m60_direct_query_bridge.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M60_direct_current_rescan_query_bridge_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M60_direct_current_rescan_query_bridge_v0/metrics.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M60_direct_current_rescan_query_bridge_v0/query_bridge_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M60_direct_current_rescan_query_bridge_v0/policy_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M60_direct_current_rescan_query_bridge_v0/report.md`

사실:

- Status: `direct_query_bridge_budget_rank_gap`.
- Direct bridge query rows: 7.
- Unique bridge targets: 5.
- Query target detected rows/rate: 3 / 0.428571.
- Unique target detected rows/rate: 3 / 0.600000.
- Mean target rank when detected: 5.0.
- Mean false positives before target when detected: 4.0.
- `detector_task_budget_v0` success rows/rate: 0 / 0.000000.
- `detector_top5_v0` success rows/rate: 2 / 0.285714.
- `detector_unbounded_until_target_or_exhausted_v0` success rows/rate: 3 / 0.428571.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary search claim ready: false.

논문 주장:

- E003-M60 supports a direct current-rescan query-level bridge diagnostic.
- E003-M60 shows that target detection and search-budget success are different failure surfaces.
- E003-M60 does not support a final real RGB-D/open-vocabulary search robustness claim because the denominator has 7 query rows, the task-budget policy succeeds on 0 rows, and external baselines are absent.

에이전트 추론:

- The immediate blocker is not only detector recall. For detected targets, ranking and false positives push the target outside the current task-conditioned budget.
- The next unit should split failures into detector miss, false-positive/rank failure, and task-budget mismatch before deciding whether to repair ranking/budget or move to `OpenMask3D`.

사용자 판단 필요:

- None. The next unit is E003-M61 direct bridge rank/failure analysis gate.

## E003-M61 Direct Bridge Rank/Failure Gate

Implementation unit: `E003-M61_direct_bridge_rank_failure_gate_v0`.

Stage: failure taxonomy and route decision after E003-M60. This separates detector recall miss, false-positive/rank failure, and task-budget mismatch before choosing between local repair and external proposal baselines.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/analyze_m61_direct_bridge_failures.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/analyze_m61_direct_bridge_failures.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M61_direct_bridge_rank_failure_gate_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M61_direct_bridge_rank_failure_gate_v0/failure_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M61_direct_bridge_rank_failure_gate_v0/target_summary.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M61_direct_bridge_rank_failure_gate_v0/route_decision.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M61_direct_bridge_rank_failure_gate_v0/report.md`

사실:

- Status: `direct_bridge_rank_failure_gate_ready`.
- Query rows: 7.
- Unique targets: 5.
- Failure class counts: detector recall miss 4, task-budget mismatch 2, false-positive rank failure 1.
- Unique target failure class counts: detector recall miss 2, task-budget mismatch 2, false-positive rank failure 1.
- Detected target rerank upper-bound rows: 3.
- Top-5 budget gain rows: 2.
- Recall miss rows: 4.
- Recall miss unique targets: 2.
- Mean rank gap vs task budget for detected failures: 3.0.
- Selected next route: `proposal_rerank_then_openmask3d_feasibility`.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary search claim ready: false.

논문 주장:

- E003-M61 supports a failure taxonomy for the direct bridge.
- E003-M61 supports saying the current direct bridge failure is mixed: detector recall miss plus rank/budget failure.
- E003-M61 does not support a final real RGB-D/open-vocabulary search claim.

에이전트 추론:

- Current detector misses the largest number of query rows, but detected targets are also outside the task budget.
- Offline rerank/budget repair should come first because it is cheap and defines the upper bound of current proposals.
- `OpenMask3D` remains important after this because current proposals cannot recover detector-recall-miss targets.

사용자 판단 필요:

- None. The next unit is E003-M62 offline proposal rerank/budget repair sweep.

## E003-M62 Offline Rerank/Budget Repair Sweep

Implementation unit: `E003-M62_offline_rerank_budget_repair_v0`.

Stage: offline repair and upper-bound diagnostic after E003-M61. This tests whether current M59 proposals can recover M60 query failures by changing proposal order and search budget before adding an external 3D proposal baseline.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/run_m62_offline_rerank_budget_sweep.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/run_m62_offline_rerank_budget_sweep.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M62_offline_rerank_budget_repair_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M62_offline_rerank_budget_repair_v0/summary_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M62_offline_rerank_budget_repair_v0/prediction_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M62_offline_rerank_budget_repair_v0/route_decision.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M62_offline_rerank_budget_repair_v0/report.md`

사실:

- Status: `offline_rerank_budget_repair_ready`.
- Query rows: 7.
- Sweep policies: 36.
- Best deployable policy: `old_memory_distance_guard` + `unbounded_until_target_or_exhausted`.
- Best deployable success rows/rate: 3 / 0.428571.
- Best deployable mean expected search cost: 16.428571.
- Bounded top-5/adaptive repair success rows/rate: 2 / 0.285714.
- Best oracle policy: `oracle_target_first_upper_bound` + `task_budget`.
- Best oracle success rows/rate: 3 / 0.428571.
- Selected next route: `integrate_deployable_rerank_budget_then_openmask3d`.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary search claim ready: false.

논문 주장:

- E003-M62 supports an offline repair and upper-bound diagnostic for current M59 proposals.
- E003-M62 supports saying rank/budget repair can recover some detected-target failures, but cannot recover detector recall misses.
- E003-M62 does not support a final real RGB-D/open-vocabulary search claim.

에이전트 추론:

- The current proposals have an upper bound of 3/7 query rows on this direct bridge.
- Bounded repair is more paper-safe than unbounded repair because the unbounded policy reaches 3/7 only with high expected search cost.
- The next unit should convert M62 into a bounded method ablation, then run `OpenMask3D` feasibility for remaining recall-miss targets.

사용자 판단 필요:

- None. The next unit is E003-M63 bounded rerank/budget repair integration gate.

## E003-M63 Bounded Repair Integration Gate

Implementation unit: `E003-M63_bounded_repair_integration_gate_v0`.

Stage: paper-safe ablation contract after E003-M62. This separates bounded budget repair, rerank diagnostics, high-cost unbounded upper bound, and non-deployable oracle ordering before deciding whether `OpenMask3D` is justified.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m63_bounded_repair_integration_gate.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m63_bounded_repair_integration_gate.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M63_bounded_repair_integration_gate_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M63_bounded_repair_integration_gate_v0/policy_contract.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M63_bounded_repair_integration_gate_v0/paper_table_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M63_bounded_repair_integration_gate_v0/row_outcomes.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M63_bounded_repair_integration_gate_v0/route_decision.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M63_bounded_repair_integration_gate_v0/report.md`

사실:

- Status: `bounded_repair_integration_gate_ready`.
- Query rows: 7.
- Selected bounded policy: `old_memory_distance_guard+adaptive_uncertainty_top5`.
- Selected bounded success rows/rate: 2 / 0.285714.
- Selected bounded mean expected search cost: 5.428571.
- Original task-budget success rows: 0.
- Best task-budget rerank success rows: 1.
- Unbounded upper-bound success rows: 3.
- Oracle task-budget success rows: 3.
- Bounded budget repair ablation ready: true.
- Bounded rerank unique gain ready: false.
- Selected next route: `openmask3d_feasibility_gate_next`.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary search claim ready: false.

논문 주장:

- E003-M63 supports using bounded budget repair as a small direct-bridge ablation.
- E003-M63 does not support claiming unique bounded rerank gain on the current 7-row denominator.
- E003-M63 keeps unbounded visit-until-target as an upper-bound diagnostic, not a cost-efficient method.
- E003-M63 does not support final real RGB-D/open-vocabulary search or real navigation claims.

에이전트 추론:

- The safest paper use is to report bounded budget repair separately from unbounded upper bound.
- The remaining upper-bound gap and recall-miss rows justify an `OpenMask3D` feasibility decision next.
- If M64 is blocked, the fallback is to expand the direct bridge denominator before another heavy baseline.

사용자 판단 필요:

- None. The next unit is E003-M64 `OpenMask3D` feasibility decision gate.

## E003-M64 OpenMask3D Feasibility Decision

Implementation unit: `E003-M64_openmask3d_feasibility_decision_v0`.

Stage: external 3D instance proposal feasibility decision after M63. This decides whether remaining target-undetected direct-bridge failures justify `OpenMask3D`, while keeping Docker/model work blocked until a scene-format/model smoke plan is fixed.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m64_openmask3d_feasibility_decision.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m64_openmask3d_feasibility_decision.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M64_openmask3d_feasibility_decision_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M64_openmask3d_feasibility_decision_v0/route_decision.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M64_openmask3d_feasibility_decision_v0/smoke_contract.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M64_openmask3d_feasibility_decision_v0/gap_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M64_openmask3d_feasibility_decision_v0/scan_input_status.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M64_openmask3d_feasibility_decision_v0/feasibility_matrix.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M64_openmask3d_feasibility_decision_v0/report.md`

사실:

- Status: `openmask3d_feasibility_decision_ready`.
- Query rows: 7.
- Selected bounded success rows: 2.
- Bounded failure rows: 5.
- Gap class counts after bounded repair: `bounded_repair_success` 2, `detector_recall_miss_after_bounded_repair` 4, `rank_or_budget_gap_after_bounded_repair` 1.
- Gap label counts after bounded repair: `chair` 3, `pillow` 2.
- Bridge scans: 4.
- `OpenMask3D` minimal-input-ready scans: 4 / 4.
- Feasibility matrix status counts: pass 3, conditional 1, warn 1.
- Selected next route: `openmask3d_scene_format_model_smoke_plan_next`.
- Next recommended unit: `E003-M65 OpenMask3D scene-format/model smoke plan`.
- Docker/model run launched: false.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary search claim ready: false.

논문 주장:

- E003-M64 supports moving to an `OpenMask3D` scene-format/model smoke plan as a feasibility step.
- E003-M64 does not support claiming `OpenMask3D` improves search, proposal recall, or false positives yet.
- E003-M64 keeps `Open3DSG`, `ConceptGraphs`, and `HOV-SG` as later map/scene-graph/navigation baselines.

에이전트 추론:

- The direct bridge denominator is now strong enough to justify a constrained external 3D instance proposal baseline check.
- The next step should prepare scene-format, model/checkpoint, adapter, and verification contracts before any long Docker/model job.
- If scene-format conversion is blocked, expand the direct bridge denominator instead of spending compute on an unverified baseline path.

사용자 판단 필요:

- None. The next unit is E003-M65 `OpenMask3D` scene-format/model smoke plan.

## E003-M65 OpenMask3D Smoke Plan

Implementation unit: `E003-M65_openmask3d_scene_format_model_smoke_plan_v0`.

Stage: execution contract before a long-running `OpenMask3D` Docker/model smoke. This fixes the scene layout, adapter output contract, background-job command shape, and verification route without launching model inference.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m65_openmask3d_scene_format_model_smoke.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m65_openmask3d_scene_format_model_smoke.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M65_openmask3d_scene_format_model_smoke_plan_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M65_openmask3d_scene_format_model_smoke_plan_v0/scene_format_manifest.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M65_openmask3d_scene_format_model_smoke_plan_v0/scene_frame_manifest.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M65_openmask3d_scene_format_model_smoke_plan_v0/openmask3d_command_plan.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M65_openmask3d_scene_format_model_smoke_plan_v0/proposal_adapter_contract.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M65_openmask3d_scene_format_model_smoke_plan_v0/verification_command.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M65_openmask3d_scene_format_model_smoke_plan_v0/report.md`

사실:

- Status: `openmask3d_scene_format_model_smoke_plan_ready`.
- Selected scans: 2.
- Selected prompt labels: `chair`, `pillow`.
- Planned frame rows: 48.
- Direct detector-recall-miss rows represented: 4.
- Planned frames per selected scan: 24 / 24.
- Scene-format manifest ready: true.
- Command plan ready: true.
- Adapter contract ready: true.
- Verification command ready: true.
- Docker/model run launched: false.
- Real RGB-D/open-vocabulary search claim ready: false.

논문 주장:

- E003-M65 supports an execution-ready plan for testing `OpenMask3D` on direct recall-miss bridge rows.
- E003-M65 does not support claiming `OpenMask3D` improves proposal recall, search success, or open-vocabulary robustness.

에이전트 추론:

- `OpenMask3D` is useful here because it tests a 3D instance-mask proposal route for current `bbox-depth` target-undetected failures.
- The first M66 implementation unit must stage `3RScan` scene folders into the official `OpenMask3D` single-scene layout and convert local `.pgm` depth files to `.png` while preserving depth-scale semantics.
- The M66 job should run in `tmux` with timestamped logs and verify completion through file counts, schema validation, and M21 matching before any M60-style query bridge claim.

사용자 판단 필요:

- None. The next unit is E003-M66 `OpenMask3D` scene-format staging plus Docker/model smoke background launch.

## E003-M66 OpenMask3D Stage and Preflight

Implementation unit: `E003-M66_openmask3d_model_smoke_v0`.

Stage: scene-format staging, background preflight, and lightweight verification for `OpenMask3D`. This stage converts local `3RScan` inputs to the official single-scene layout, launches a `tmux` preflight job, and records the model-smoke blocker.

Commands:

```bash
python experiments/E003_perception_noise_expansion/tools/stage_m66_openmask3d_scene_format.py --force
python experiments/E003_perception_noise_expansion/tools/launch_m66_openmask3d_smoke.py
python experiments/E003_perception_noise_expansion/tools/verify_m66_openmask3d_smoke.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/stage_m66_openmask3d_scene_format.py`
- `experiments/E003_perception_noise_expansion/tools/launch_m66_openmask3d_smoke.py`
- `experiments/E003_perception_noise_expansion/tools/verify_m66_openmask3d_smoke.py`
- `experiments/E003_perception_noise_expansion/docker/openmask3d_smoke/Dockerfile`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M66_openmask3d_model_smoke_v0/stage/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M66_openmask3d_model_smoke_v0/launch/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M66_openmask3d_model_smoke_v0/verification/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M66_openmask3d_model_smoke_v0/background_status.json`
- `logs/20260512_081828_e003_m66_openmask3d_smoke.log`

사실:

- Stage status: `openmask3d_scene_stage_ready`.
- Verification status: `openmask3d_checkpoints_missing`.
- Selected scans: 2.
- Planned/staged frame rows: 48 / 48.
- Staged color/depth/pose files: 48 / 48 / 48.
- Staged PLY files: 2.
- Staged intrinsic files: 2.
- Missing source files: 0.
- Depth conversion: `.pgm` -> 16-bit grayscale `.png`.
- Official `OpenMask3D` repo cloned at commit `3bc3fc52693b25668d0e91d55a2ea714544a4749`.
- `OpenMask3D` mask checkpoint ready: false.
- `SAM` checkpoint ready: false.
- Model inference launched: false.
- Real RGB-D/open-vocabulary search claim ready: false.

논문 주장:

- E003-M66 supports that the selected direct recall-miss scans can be staged into `OpenMask3D` input format.
- E003-M66 does not support any `OpenMask3D` proposal-quality or search-improvement claim because model outputs do not exist yet.

에이전트 추론:

- The immediate blocker is no longer scene format or local RGB-D payload. It is checkpoint acquisition and environment execution.
- The next unit should decide whether to download/provide the `OpenMask3D` mask checkpoint and `SAM` checkpoint, then run Docker build/model smoke, or fall back to direct bridge denominator expansion.

사용자 판단 필요:

- None yet. The next unit is E003-M67 checkpoint acquisition / Docker env route decision.

## E003-M67 OpenMask3D Checkpoint / Env Route

Implementation unit: `E003-M67_openmask3d_checkpoint_env_route_v0`.

Stage: route decision after E003-M66 stage readiness and checkpoint blocker. This fixes the checkpoint cache path, download script, verification command, Docker env risk, and fallback route before launching any large download.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m67_openmask3d_checkpoint_env_route.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m67_openmask3d_checkpoint_env_route.py`
- `experiments/E003_perception_noise_expansion/tools/verify_m67_openmask3d_checkpoints.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M67_openmask3d_checkpoint_env_route_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M67_openmask3d_checkpoint_env_route_v0/checkpoint_manifest.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M67_openmask3d_checkpoint_env_route_v0/download_command_plan.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M67_openmask3d_checkpoint_env_route_v0/env_route_decision.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M67_openmask3d_checkpoint_env_route_v0/verification_command.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M67_openmask3d_checkpoint_env_route_v0/run_m68_checkpoint_download.sh`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M67_openmask3d_checkpoint_env_route_v0/report.md`

사실:

- Status: `openmask3d_checkpoint_env_route_ready`.
- Selected route: `checkpoint_download_background_launch_next`.
- Fallback route: `direct_bridge_denominator_expansion_if_checkpoint_or_docker_env_blocks`.
- Cache path: `local_dataset/checkpoints/openmask3d/`.
- Checkpoint readiness: false.
- Required checkpoint 1: `OpenMask3D` arbitrary-scene mask checkpoint from the official `OpenMask3D` README.
- Required checkpoint 2: `SAM ViT-H` checkpoint from the official `Segment Anything` model checkpoint list.
- Download script: `run_m68_checkpoint_download.sh`.
- Verification command: `verify_m67_openmask3d_checkpoints.py`.
- Docker probe: ready through sudo.
- GPU probe: `NVIDIA GeForce RTX 5090`, driver `580.126.09`, memory `32607 MiB`.
- Environment risk: high because official `OpenMask3D` uses old `torch` / CUDA / `MinkowskiEngine`, while the current host GPU is RTX 5090.

논문 주장:

- E003-M67 supports only an operational route for checkpoint acquisition and env preflight.
- It does not support `OpenMask3D` proposal-quality or search-improvement claims.

에이전트 추론:

- Because E003-M66 scene staging and repo preflight are ready, checkpoint acquisition is the next smallest blocker.
- Docker build should wait until checkpoint verification passes.
- If Google Drive quota/auth or Docker build blocks, direct bridge denominator expansion is the safer next route than spending unbounded time on environment repair.

사용자 판단 필요:

- None before M68. The next unit is E003-M68 checkpoint download background launch.

## E003-M68 OpenMask3D Checkpoint Download Launch

Implementation unit: `E003-M68_openmask3d_checkpoint_download_launch_v0`.

Stage: long-running checkpoint acquisition launch. This starts the M67 download script in a `tmux` background session and records the exact command, working directory, log path, output cache, expected files, and verification command.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/launch_m68_openmask3d_checkpoint_download.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/launch_m68_openmask3d_checkpoint_download.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M68_openmask3d_checkpoint_download_launch_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M68_openmask3d_checkpoint_download_launch_v0/launch_command.txt`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M68_openmask3d_checkpoint_download_launch_v0/report.md`

사실:

- Status: `openmask3d_checkpoint_download_job_launched`.
- Background job final status: exited; checkpoint verifier passed.
- tmux session: `e003_m68_openmask3d_checkpoints`.
- Final log: `logs/20260512_084954_e003_m68_openmask3d_checkpoints.log`.
- Cache path: `local_dataset/checkpoints/openmask3d/`.
- Expected file 1: `openmask3d_arbitrary_scene_model.ckpt`, minimum size 50 MB.
- Expected file 2: `sam_vit_h_4b8939.pth`, minimum size 2 GB.
- Verification command: `python experiments/E003_perception_noise_expansion/tools/verify_m67_openmask3d_checkpoints.py --cache-dir /home/yoohyun/research2/local_dataset/checkpoints/openmask3d --openmask3d-repo /home/yoohyun/research2/experiments/E003_perception_noise_expansion/external/openmask3d --out-dir /home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M67_openmask3d_checkpoint_env_route_v0`.
- First two launch attempts failed quickly due to PEP 668 `pip --user` blocking and `gdown` v6 CLI syntax. The download script used a local `.venv_tools/gdown` helper and positional `gdown` id syntax. `.venv_tools` is a recreatable operational byproduct and was later deleted.

논문 주장:

- E003-M68 does not support `OpenMask3D` proposal-quality or search-improvement claims.
- It only supports that checkpoint acquisition has been launched reproducibly under the long-running job policy.

에이전트 추론:

- The background launch and verification path are reproducible.
- The job exited with checkpoints ready, so E003-M70 can focus on Docker/env build feasibility.
- If a future rerun hits Google Drive quota/auth or network issues, use the fixed fallback route instead of spending unbounded time on checkpoint acquisition.

사용자 판단 필요:

- None.

## E003-M69 OpenMask3D Checkpoint Completion Verification

Implementation unit: checkpoint completion verification using `verify_m67_openmask3d_checkpoints.py`.

Stage: post-download verification. This verifies cache files and symlink/resource paths after E003-M68 exits.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/verify_m67_openmask3d_checkpoints.py --cache-dir /home/yoohyun/research2/local_dataset/checkpoints/openmask3d --openmask3d-repo /home/yoohyun/research2/experiments/E003_perception_noise_expansion/external/openmask3d --out-dir /home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M67_openmask3d_checkpoint_env_route_v0
```

Artifacts:

- `experiments/E003_perception_noise_expansion/artifacts/E003-M67_openmask3d_checkpoint_env_route_v0/checkpoint_verification.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M67_openmask3d_checkpoint_env_route_v0/checkpoint_verification.md`

사실:

- Status: `openmask3d_checkpoints_ready`.
- Cache ready count: 2 / 2.
- Resource ready count: 2 / 2.
- `openmask3d_arbitrary_scene_model.ckpt`: 952,327,000 bytes.
- `sam_vit_h_4b8939.pth`: 2,564,550,879 bytes.
- `OpenMask3D/resources` paths are ready through symlink/resource checks.

논문 주장:

- E003-M69 supports only checkpoint availability.
- It does not support model execution, proposal quality, or search-improvement claims.

에이전트 추론:

- The next blocker is Docker/env build feasibility, not checkpoint availability.
- Because official `OpenMask3D` uses old `torch` / CUDA / `MinkowskiEngine`, E003-M70 should remain a preflight with logs and fallback, not an unbounded environment-repair effort.

사용자 판단 필요:

- None before E003-M70 Docker env build preflight.

## E003-M70 OpenMask3D Docker Build Preflight

Implementation unit: `E003-M70_openmask3d_docker_env_build_preflight_v0`.

Stage: Docker environment build preflight after checkpoint verification. This starts the `OpenMask3D` Docker image build in a `tmux` background session and records the exact build command, log path, status file, image name, and verification command.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/launch_m70_openmask3d_docker_build_preflight.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/launch_m70_openmask3d_docker_build_preflight.py`
- `experiments/E003_perception_noise_expansion/tools/verify_m70_openmask3d_docker_build.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M70_openmask3d_docker_env_build_preflight_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M70_openmask3d_docker_env_build_preflight_v0/launch_command.txt`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M70_openmask3d_docker_env_build_preflight_v0/run_m70_openmask3d_docker_build.sh`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M70_openmask3d_docker_env_build_preflight_v0/background_status.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M70_openmask3d_docker_env_build_preflight_v0/verification/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M70_openmask3d_docker_env_build_preflight_v0/report.md`

사실:

- Status: `openmask3d_docker_build_failed`.
- Final verification status: `openmask3d_docker_build_failed`.
- tmux session running: false.
- Current build log: `logs/20260512_105700_e003_m70_openmask3d_docker_build.log`.
- Image name: `research2/openmask3d-smoke:latest`.
- Image ready: false.
- Dockerfile: `experiments/E003_perception_noise_expansion/docker/openmask3d_smoke/Dockerfile`.
- Checkpoints ready before launch: true.
- Scene stage ready before launch: true.
- Earlier build attempts failed because the pinned `Miniconda3-py38_24.1.2-0` installer URL returned 404, latest conda required ToS acceptance, and `pytorch-lightning==1.7.2` needs `pip<24.1`; the Dockerfile now uses `Miniconda3-latest`, accepts required channels, still creates the `python=3.8.5` conda env, and pins `pip<24.1`.
- Final relaunch failed while collecting `NVIDIA/MinkowskiEngine`: `Getting requirements to build wheel: finished with status 'error'`.
- Fallback route: `direct_bridge_denominator_expansion`.

논문 주장:

- E003-M70/E003-M71 support only a reproducible Docker env build launch and failure diagnosis.
- It does not support `OpenMask3D` model execution, proposal quality, real RGB-D robustness, or search-improvement claims.

에이전트 추론:

- The build failure is an environment/dependency blocker, not negative evidence about `OpenMask3D` proposal quality.
- The immediate research bottleneck is still the small direct bridge denominator, so more `OpenMask3D` environment repair is deferred.

사용자 판단 필요:

- None for choosing direct denominator expansion next.

## E003-M72 OpenMask3D Blocker Fallback Gate

Implementation unit: `E003-M72_openmask3d_blocker_fallback_gate_v0`.

Stage: route decision after final `OpenMask3D` Docker build failure. This records the blocker and chooses whether to keep repairing the environment or return to direct bridge denominator expansion.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m72_openmask3d_blocker_fallback_gate.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m72_openmask3d_blocker_fallback_gate.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M72_openmask3d_blocker_fallback_gate_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M72_openmask3d_blocker_fallback_gate_v0/route_options.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M72_openmask3d_blocker_fallback_gate_v0/report.md`

사실:

- Status: `openmask3d_blocked_direct_denominator_fallback_selected`.
- E003-M70 verification status: `openmask3d_docker_build_failed`.
- Hard blockers: `docker_build_failed`, `minkowskiengine_build_requirement_error`, `image_not_ready`.
- Current direct bridge query rows: 7.
- Current direct bridge target-detected rows: 3.
- M64 bounded failure rows: 5, including 4 detector-recall-miss rows and 1 rank/budget row.
- Selected next route: `direct_bridge_denominator_expansion`.
- Next recommended unit: `E003-M73 direct bridge denominator expansion plan`.

논문 주장:

- E003-M72 does not support an `OpenMask3D` proposal-quality claim.
- E003-M72 only supports an engineering route decision after Docker environment failure.

에이전트 추론:

- `OpenMask3D` remains useful later as an external 3D instance proposal baseline.
- It should not block E003 because the current search-bridge evidence is still dominated by a 7-row direct denominator.

사용자 판단 필요:

- None for proceeding to E003-M73.

## E003-M73 Direct Bridge Denominator Expansion Plan

Implementation unit: `E003-M73_direct_bridge_denominator_expansion_plan_v0`.

Stage: planning gate after `OpenMask3D` Docker blocker. This expands the direct current-rescan detector bridge from search-failure-only rows to all detector-ready query rows on already RGB-D-ready exact current rescans.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/plan_m73_direct_bridge_denominator_expansion.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/plan_m73_direct_bridge_denominator_expansion.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M73_direct_bridge_denominator_expansion_plan_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M73_direct_bridge_denominator_expansion_plan_v0/direct_bridge_query_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M73_direct_bridge_denominator_expansion_plan_v0/real_proposal_query_manifest.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M73_direct_bridge_denominator_expansion_plan_v0/real_proposal_object_targets.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M73_direct_bridge_denominator_expansion_plan_v0/prompt_set.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M73_direct_bridge_denominator_expansion_plan_v0/detector_run_command_plan.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M73_direct_bridge_denominator_expansion_plan_v0/report.md`

사실:

- Status: `direct_bridge_denominator_expansion_plan_ready`.
- Selected exact current-rescan scans: 4.
- Detector-ready query rows: 96.
- Detector-ready base rows: 32.
- Previous M58 query rows: 7.
- Added query rows over M58: 89.
- Target uids: 32.
- Object target rows: 62.
- Prompt labels: 10 (`bench`, `box`, `chair`, `couch table`, `drum`, `gymnastic ball`, `pillow`, `plant`, `rocking chair`, `trash can`).
- Sampled frame count: 93.
- Excluded query rows: 3 generic `item` rows.
- Detector rerun launched: false.

논문 주장:

- E003-M73 only supports a planned denominator expansion contract.
- It does not support real RGB-D/open-vocabulary search improvement until E003-M74/E003-M75 run and join detector outputs back to query-level metrics.

에이전트 추론:

- This is the right fallback after `OpenMask3D` Docker failure because it increases exact current-rescan bridge coverage without changing the core method claim.
- The expansion gives success/failure and task-context variation over the same 4 RGB-D-ready scans, improving reviewer defense before external baseline integration.

사용자 판단 필요:

- None before launching E003-M74 as a background detector run.

## E003-M74 Direct Bridge Denominator Detector Launch

Implementation unit: `E003-M74_direct_bridge_denominator_detector_launch_v0`.

Stage: background launch for the expanded direct current-rescan detector run. This uses the M73 input directory, starts the Docker detector job in `tmux`, and records the log path, run script, output path, expected files, and verification command.

Command:

```bash
printf 'a\n' | python experiments/E003_perception_noise_expansion/tools/launch_m74_direct_bridge_denominator_detector.py --sudo-password-stdin
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/launch_m74_direct_bridge_denominator_detector.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M74_direct_bridge_denominator_detector_launch_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M74_direct_bridge_denominator_detector_launch_v0/launch_command.txt`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M74_direct_bridge_denominator_detector_launch_v0/run_m74_detector.sh`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M74_direct_bridge_denominator_detector_launch_v0/report.md`

사실:

- Status: `expanded_direct_bridge_detector_job_launched`.
- tmux session: `e003_m74_direct_denominator`.
- Log path: `logs/20260512_121507_e003_m74_direct_bridge_denominator_detector_run.log`.
- Input dir: `experiments/E003_perception_noise_expansion/artifacts/E003-M73_direct_bridge_denominator_expansion_plan_v0/`.
- Output dir: `experiments/E003_perception_noise_expansion/artifacts/E003-M74_direct_bridge_denominator_detector_run_v0/`.
- Detector-ready query rows: 96.
- Prompt labels: 10.
- Target scans: 4.
- Verification command is recorded in the launch coverage artifact.

논문 주장:

- E003-M74 launch does not create a paper result claim.
- It only starts the Docker detector run required before expanded direct bridge evaluation.

에이전트 추론:

- Do not monitor this job continuously.
- Completion should be verified with expected files, schema validation, matching coverage, and targeted log tail.
- Real RGB-D/open-vocabulary search claims remain blocked until E003-M75 joins outputs back to query-level bridge metrics.

사용자 판단 필요:

- None. Completion is recorded in the next section.

## E003-M74 Detector Completion Verification

Implementation unit: `E003-M74_direct_bridge_detector_completion_verification_v0`.

Stage: completion verification after the expanded direct bridge detector background job. This verifies that the `tmux` session exited, expected files exist, schema validator output is clean, matching coverage exists, and the log sample has no relevant error hit.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/verify_m74_direct_bridge_detector_completion.py --require-ready
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/verify_m74_direct_bridge_detector_completion.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M74_direct_bridge_detector_completion_verification_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M74_direct_bridge_detector_completion_verification_v0/report.md`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M74_direct_bridge_denominator_detector_run_v0/`

사실:

- Status: `expanded_direct_bridge_detector_run_ready`.
- tmux session running: false.
- Expected files ready: 4 / 4.
- Validator status: `proposal_schema_smoke_valid`.
- Validator errors/warnings: 0 / 0.
- Prediction rows: 478.
- Pre-cap candidate rows: 12,192.
- Evaluated scans: 4.
- Matched target rows: 47 / 62.
- Proposal precision smoke: 0.098326.
- Scan target recall smoke: 0.758065.
- False-positive proposal rate smoke: 0.901674.
- Mean matched centroid error: 0.528799m.

논문 주장:

- E003-M74 supports that the expanded direct bridge detector run completed and produced schema-valid, matchable real RGB-D/open-vocabulary proposal artifacts.
- E003-M74 does not support a search-improvement, deployable policy, final real RGB-D/open-vocabulary robustness, or real navigation claim.

에이전트 추론:

- E003-M75 must join proposals back to query-level rows because proposal precision/recall alone cannot establish stale-memory search value.
- The high false-positive rate means rank, budget, and `ExpectedSearchCost` are the decisive next checks.

사용자 판단 필요:

- None. E003-M75 is recorded below.

## E003-M75 Expanded Direct Query Bridge

Implementation unit: `E003-M75_expanded_direct_query_bridge_v0`.

Stage: expanded query-level evaluation after E003-M74. This joins detector proposals back to the 96 M73 query rows and recomputes target detection, false positives before target, rank, budgeted success, bounded repair, and candidate-count search-cost proxies.

Command:

```bash
python experiments/E003_perception_noise_expansion/tools/evaluate_m75_expanded_direct_query_bridge.py
```

Artifacts:

- `experiments/E003_perception_noise_expansion/tools/evaluate_m75_expanded_direct_query_bridge.py`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M75_expanded_direct_query_bridge_v0/coverage.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M75_expanded_direct_query_bridge_v0/metrics.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M75_expanded_direct_query_bridge_v0/query_bridge_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M75_expanded_direct_query_bridge_v0/policy_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M75_expanded_direct_query_bridge_v0/policy_summary_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M75_expanded_direct_query_bridge_v0/failure_rows.jsonl`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M75_expanded_direct_query_bridge_v0/route_decision.json`
- `experiments/E003_perception_noise_expansion/artifacts/E003-M75_expanded_direct_query_bridge_v0/report.md`

사실:

- Status: `expanded_direct_query_bridge_ready`.
- Query rows: 96.
- Unique targets: 32.
- Query target detected rows/rate: 87 / 0.906250.
- Unique target detected rows/rate: 29 / 0.906250.
- Mean target rank when detected: 9.034483.
- Mean false positives before target when detected: 8.034483.
- Mean same-label detector proposals per query: 23.187500.
- `detector_task_budget_v0` success rows/rate: 13 / 0.135417.
- `detector_task_budget_v0` mean `ExpectedSearchCost` / `AttemptSPL` proxy: 2.645833 / 0.070833.
- `bounded_old_memory_distance_guard_adaptive_top5_v0` success rows/rate: 33 / 0.343750.
- `bounded_old_memory_distance_guard_adaptive_top5_v0` mean `ExpectedSearchCost` / `AttemptSPL` proxy: 4.937500 / 0.133333.
- `unbounded_old_memory_distance_guard_until_target_v0` success rows/rate: 87 / 0.906250.
- `unbounded_old_memory_distance_guard_until_target_v0` mean `ExpectedSearchCost` / `AttemptSPL` proxy: 9.750000 / 0.190163.
- Stale old-dead-end avoided rows under task budget vs bounded repair: 3 / 12 vs 6 / 12.
- Failure class counts: `unbounded_high_cost_repair_only` 54, `bounded_repair_success` 20, `task_budget_success` 13, `detector_recall_miss` 9.
- Selected next route: `expanded_bridge_bounded_repair_positive_e004_gate_next`.
- Paper-table command ready: false.
- Real RGB-D/open-vocabulary search claim ready: false.

논문 주장:

- E003-M75 supports an expanded direct query-level bridge diagnostic over E003-M74 detector outputs.
- E003-M75 supports that bounded search repair improves query-level success over the original detector task-budget policy on this 96-row denominator.
- E003-M75 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

에이전트 추론:

- The positive part is that the expanded bridge no longer collapses at detector recall: 87 / 96 query rows have detected targets.
- The blocker is ranking/cost: detected targets are late on average, with about 8 false positives before the target.
- Bounded repair is useful evidence for E004, but not yet a final method claim because it raises average search cost and relaxes the original memory-trust behavior.
- E004 should explicitly decide whether task context changes memory trust and re-observation budget without turning the method into a generic top-k search expansion.

사용자 판단 필요:

- None before E004 transition gate.

## Real Navigation Note

사실:

- E002 did not find a ready navmesh, simulator route, or robot trajectory source.
- E002 real navigation path-cost rows remain 0.

논문 주장:

- Real navigation `SR` / `SPL` remains unsupported.

에이전트 추론:

- Real navigation should be handled as a later experiment with simulator/navmesh/trajectory execution, not folded into E003 perception-noise contract.
