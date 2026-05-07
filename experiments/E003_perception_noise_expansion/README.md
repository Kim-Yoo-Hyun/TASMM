# E003 Perception Noise Expansion

Updated: 2026-05-08

## Status

`E003-M00_contract_v0`, `E003-M01_source_audit_v0`, `E003-M02_annotation_proxy_noise_v0`, `E003-M03_noisy_policy_eval_v0`, `E003-M04_robustness_failure_analysis_v0`, `E003-M05_route_v0`, `E003-M06_annotation_proposal_dropout_v0`, `E003-M07_dropout_failure_boundary_v0`, `E003-M08_annotation_false_positive_v0`, `E003-M09_false_positive_failure_boundary_v0`, `E003-M10_annotation_centroid_jitter_v0`, `E003-M11_centroid_jitter_failure_boundary_v0`, `E003-M12_combined_noise_route_decision_v0`, `E003-M13_annotation_combined_moderate_v0`, `E003-M14_combined_noise_failure_boundary_v0`, `E003-M15_controlled_perception_claim_summary_v0`, `E003-M16_real_proposal_route_decision_v0`, `E003-M17_real_proposal_denominator_staging_v0`, `E003-M18_dockerized_real_proposal_detector_scaffold_v0`, `E003-M19_real_detector_backend_integration_v0`, `E003-M20_detector_model_smoke_v0`, `E003-M21_detector_proposal_matching_v0`, `E003-M22_frame_scaling_projection_diagnostic_v0`, `E003-M23_proposal_consolidation_calibration_v0`, `E003-M24_visibility_prompt_projection_gate_v0`, `E003-M25_visibility_prompt_rerun_gate_v0`, `E003-M26_prompt_expanded_multiscan_docker_rerun_v0`, `E003-M27_false_positive_cap_bottleneck_v0`, and `E003-M28_cap_aware_label_balanced_policy_v0` are complete. Next unit is E003-M29 Docker pre-cap policy integration rerun gate.

## Source

- Source hypothesis: `hypothesis/CAND-001/H001_stale-object-memory/`
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
| command | Current executable commands are `python experiments/E003_perception_noise_expansion/tools/build_noise_inputs.py`, `python experiments/E003_perception_noise_expansion/tools/evaluate_noisy_policies.py`, `python experiments/E003_perception_noise_expansion/tools/run_proposal_dropout.py`, `python experiments/E003_perception_noise_expansion/tools/analyze_dropout_boundaries.py`, `python experiments/E003_perception_noise_expansion/tools/run_false_positive_stress.py`, `python experiments/E003_perception_noise_expansion/tools/analyze_false_positive_boundaries.py`, `python experiments/E003_perception_noise_expansion/tools/run_centroid_jitter.py`, `python experiments/E003_perception_noise_expansion/tools/analyze_centroid_jitter_boundaries.py`, `python experiments/E003_perception_noise_expansion/tools/select_m12_combined_route.py`, `python experiments/E003_perception_noise_expansion/tools/run_combined_moderate.py`, `python experiments/E003_perception_noise_expansion/tools/analyze_combined_boundaries.py`, `python experiments/E003_perception_noise_expansion/tools/summarize_controlled_claims.py`, `python experiments/E003_perception_noise_expansion/tools/select_m16_real_proposal_route.py`, `python experiments/E003_perception_noise_expansion/tools/stage_m17_real_proposal_denominator.py`, `python experiments/E003_perception_noise_expansion/tools/run_m18_real_proposal_scaffold.py`, `python experiments/E003_perception_noise_expansion/tools/run_m19_real_detector_backend.py`, `python experiments/E003_perception_noise_expansion/tools/run_m20_detector_model_smoke.py`, `python experiments/E003_perception_noise_expansion/tools/evaluate_m21_detector_matching.py`, `python experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py`, `python experiments/E003_perception_noise_expansion/tools/run_m23_proposal_calibration.py`, `python experiments/E003_perception_noise_expansion/tools/run_m24_visibility_prompt_projection_gate.py`, `python experiments/E003_perception_noise_expansion/tools/plan_m25_visibility_prompt_rerun.py`, `python experiments/E003_perception_noise_expansion/tools/summarize_m26_prompt_expanded_rerun.py`, `python experiments/E003_perception_noise_expansion/tools/analyze_m27_false_positive_cap_bottleneck.py`, `python experiments/E003_perception_noise_expansion/tools/run_m28_cap_aware_policy_smoke.py`, and `python experiments/E003_perception_noise_expansion/tools/validate_real_proposal_output.py`. |
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
| E003-M29 | Docker pre-cap policy integration rerun gate | next: integrate policy into detector runner command path and define rerun contract |

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

- None for E003-M28. Next is E003-M29 Docker pre-cap policy integration rerun gate.

## Real Navigation Note

사실:

- E002 did not find a ready navmesh, simulator route, or robot trajectory source.
- E002 real navigation path-cost rows remain 0.

논문 주장:

- Real navigation `SR` / `SPL` remains unsupported.

에이전트 추론:

- Real navigation should be handled as a later experiment with simulator/navmesh/trajectory execution, not folded into E003 perception-noise contract.
