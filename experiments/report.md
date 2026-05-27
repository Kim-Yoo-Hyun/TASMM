# Experiment Report

Updated: 2026-05-28

이 문서는 현재 `experiments/` 단계에서 확인된 기여점, reviewer가 공격할 핵심 지점, 방어 전략, 최종 논문 방향성을 정리한다. 세부 산출물은 각 experiment folder와 artifact에 둔다.

## Current State

사실:

- Active direction: `CAND-001` / `Intent- and Staleness-Aware Semantic Mapping`.
- Active hypothesis: `H001_stale-object-memory`.
- Main experiment stage has started under `experiments/`.
- E001 provides a semantic-pair dynamic object search proxy benchmark.
- E002 provides path/search-cost bridge fields and `occupancy_grid_astar_v0` proxy path costs.
- E003 provides controlled perception/proposal-noise tests and a Dockerized RGB-D/open-vocabulary proposal route.
- E003-M57 verified 4 / 4 current-rescan `sequence.zip` payloads for direct current-rescan detector/evaluation bridge design.
- E003-M58 fixed the first direct current-rescan detector/evaluation bridge denominator for 7 search-failure query rows, 5 unique bridge targets, 4 current rescans, and `chair` / `pillow` prompts.
- E003-M73 expanded the direct bridge denominator to 96 detector-ready query rows over 4 RGB-D-ready current rescans.
- E003-M74 verified 478 detector proposals, 47 / 62 matched targets, proposal precision 0.098326, scan target recall 0.758065, and false-positive proposal rate 0.901674.
- E003-M75 joined E003-M74 proposals to 96 query rows: target detected 87 / 96, unique target detected 29 / 32, mean target rank 9.034483, and mean false positives before target 8.034483.
- E003-M75 `detector_task_budget_v0` succeeds on 13 / 96 rows; `bounded_old_memory_distance_guard_adaptive_top5_v0` succeeds on 33 / 96 rows with mean `ExpectedSearchCost` 4.937500.
- E004-M01 transition gate is complete with status `e004_transition_ready_with_constraints`.
- E004-M01 task-context-specific effect readiness is false and motivated E004-M02 contract planning.
- E004-M02 metric contract is complete with status `e004_m02_metric_contract_ready`.
- E004-M03 memory trust policy is complete with status `e004_m03_task_context_tradeoff_ready_with_constraints`.
- E004-M03 `static_memory_only_v0` succeeds on 63 / 96 rows, `context_agnostic_memory_trust_reobserve_v0` succeeds on 66 / 96 rows, and `task_context_memory_trust_reobserve_v0` succeeds on 68 / 96 rows.
- E004-M03 task-context-specific gain over context-agnostic memory trust is concentrated in `high_value_fetch`: +2 success rows with +0.500000 mean `ExpectedSearchCost`.
- E004-M04 claim-boundary ablation is complete with status `e004_m04_claim_boundary_ready`.
- E004-M04 `all_high_value_memory_trust_counterfactual_v0` succeeds on 72 / 96 rows with mean `ExpectedSearchCost` 2.687500.
- E004-M04 task-context-specific claim strength is `limited_positive`.
- E004-M05 scale/split stress is complete with status `e004_m05_split_stress_ready_limited_task_context`.
- E004-M05 supports memory-trust claim strength `split_supported`.
- E004-M05 task-context-specific claim strength is `limited_positive_not_label_broad`.
- E004-M05 task-context vs context-agnostic success delta is +2 rows, bootstrap positive rate is 0.872, and positive label groups are `chair` / `pillow`.
- E005-M01 external baseline transition is complete with status `e005_m01_external_baseline_transition_ready`.
- E005-M01 scored 10 candidate baselines and selected `DualMap` as the first external baseline route.
- E005-M01 selected `ConceptGraphs` as the backup route.
- E005-M01 keeps `OpenMask3D` as a later 3D instance proposal baseline because the local Docker/MinkowskiEngine blocker is still present.
- E005-M02 `DualMap` source/interface audit is complete with status `e005_m02_dualmap_interface_audit_ready_with_staging_required`.
- E005-M02 checked official `DualMap` repo commit `157235ec49e6a1f439babbc571c4c02ad1f06aa9` and license `Apache-2.0`.
- E005-M02 confirms direct drop-in to E004 JSONL rows is false.
- E005-M02 confirms Dataset Mode staging route feasible true, adapter contract ready true, and external baseline comparison ready false.
- E005-M03 `DualMap` 3RScan dataset-format staging feasibility is complete with status `e005_m03_dualmap_3rscan_staging_feasibility_ready_with_conversion_required`.
- E005-M03 selected 4 E003-M73 current-rescan scans and found 4 / 4 preflight-ready.
- E005-M03 found 826 RGB-D-pose triplets across selected scans.
- E005-M03 selected adapter `scannet_exported_3rscan_adapter_v0` and keeps materialization/depth conversion required.
- E005-M03 did not launch `DualMap` runtime and did not inspect object `*.pkl` schema.
- E005-M04 `DualMap` staging root materialization is complete with status `e005_m04_dualmap_staging_root_materialized_smoke_ready`.
- E005-M04 staged dataset root is `local_dataset/DualMap_staged/3rscan_scannet_exported/scannet`.
- E005-M04 materialized scans 4 / 4 with 826 color symlinks, 826 depth PNG files, 826 pose symlinks, and 4 intrinsic files.
- E005-M04 runtime command plan is ready for `ddc73795-765b-241a-9c5d-b97744afe077`.
- E005-M04 did not launch `DualMap` runtime and did not inspect object `*.pkl` schema.
- E005-M05 `DualMap` runtime preflight is complete with status `e005_m05_dualmap_runtime_blocked_env_bootstrap_required`.
- E005-M05 official repo head matches audited commit `157235ec49e6a1f439babbc571c4c02ad1f06aa9`.
- E005-M05 smoke scan color/depth/pose frame counts are 93 / 93 / 93.
- E005-M05 Docker daemon and NVIDIA runtime are ready under sudo Docker.
- E005-M05 GPU probe is `NVIDIA GeForce RTX 5090, 32607 MiB, 580.126.09`.
- E005-M05 static object `*.pkl` schema fields are `uid`, `pcd_points`, `pcd_colors`, `clip_ft`, `class_id`, `nav_goal`.
- E005-M05 `mobileclip` submodule ready is false and current Python dependency readiness is false.
- E005-M05 did not launch `DualMap` runtime and did not inspect runtime object `*.pkl`.
- E005-M06 `DualMap` bootstrap launch is complete with status `e005_m06_dualmap_bootstrap_job_launched`.
- E005-M06 tmux session is `e005_m06_dualmap_bootstrap`.
- E005-M06 log path is `logs/20260513_142937_e005_m06_dualmap_bootstrap.log`.
- E005-M06 target Docker image is `research2/dualmap-smoke:latest`.
- E005-M06 initial verifier status is `e005_m06_dualmap_bootstrap_running`.
- E005-M06 local `mobileclip` submodule ready is true.
- E005-M06 Docker image ready at initial verification is false.
- E005-M06 bounded Dockerfile repair uses absolute env Python for `mobileclip` install and import smoke after initial `pip` / `python` PATH failures.
- E005-M06 did not launch the one-scan `DualMap` runtime.
- E005-M07 `DualMap` bootstrap completion verification is complete with status `e005_m06_dualmap_bootstrap_ready`.
- E005-M07 confirms tmux stopped, background status `completed`, Docker image ready true, and dependency import smoke `dualmap_import_smoke_ok`.
- E005-M07 image id is `sha256:7c053613ab51d968f4e70896364af2493595e827fb7605f0fd16c514c5cc0bf4`.
- E005-M07 image size is 7,927,047,638 bytes.
- E005-M07 did not launch the one-scan `DualMap` runtime.
- E005-M08 `DualMap` one-scan runtime smoke launch is complete with status `e005_m08_dualmap_runtime_job_launched`.
- E005-M08 verifier status is `e005_m08_dualmap_runtime_running`.
- E005-M08 tmux session is `e005_m08_dualmap_runtime`.
- E005-M08 log path is `logs/20260513_153046_e005_m08_dualmap_one_scan_runtime.log`.
- E005-M08 output path is `local_dataset/DualMap_outputs/ddc73795-765b-241a-9c5d-b97744afe077`.
- E005-M08 runtime object `*.pkl` count while running is 0.
- E005-M09 `DualMap` runtime completion verification is complete with status `e005_m08_dualmap_runtime_failed`.
- E005-M09 confirms tmux stopped and background returncode is 137.
- E005-M09 output inventory is runtime object `*.pkl` 0, `layout.pcd` 0, `system_time.csv` 0, DualMap log 1.
- E005-M09 failure signals are `cuda_out_of_memory`, `clip_model_init_failed`, `yolo_not_initialized_after_detector_init_failure`, `fastsam_not_initialized_after_detector_init_failure`, and `hydra_job_error`.
- E005-M09 GPU snapshot after cleanup shows only 1510 MiB free because an unrelated `python3` process uses 27714 MiB.
- E005-M10 `DualMap` runtime repair decision is complete with status `e005_m10_dualmap_runtime_repair_decision_ready`.
- E005-M10 current GPU snapshot shows 29045 / 32607 MiB free on `NVIDIA GeForce RTX 5090`.
- E005-M10 selects `detector_enabled_free_gpu_retry` as the next route, with loader-only layout smoke and lower-memory detector retry as fallback before `ConceptGraphs`.
- E005-M11 `DualMap` detector-enabled retry launch is complete with status `e005_m11_dualmap_detector_retry_job_launched`.
- E005-M11 initial verifier status is `e005_m11_dualmap_detector_retry_running`.
- E005-M11 tmux session is `e005_m11_dualmap_detector_retry`, log path is `logs/20260514_110141_e005_m11_dualmap_detector_retry.log`, and expected outputs are runtime object `*.pkl`, `layout.pcd`, and `system_time.csv`.
- E005-M12 verifies the detector-enabled retry failed at `/home/mambauser/.cache/clip` permission during detector initialization.
- E005-M13 fixes the cache route by mounting a writable host cache at `/home/mambauser/.cache`.
- E005-M15 verifies the cache-fixed `DualMap` run completed with `layout.pcd`, `system_time.csv`, and `detector_time.csv`, but object `*.pkl` count is 0.
- E005-M16 diagnoses M14 as an object-output failure: `stride=20` processed 5 keyframes, `stable_num=8`, and local objects went 8 -> 0 before save.
- E005-M18 verifies the denser-stride retry also completed without object `*.pkl`: `stride=5`, 19 processed keyframes, local objects 26 -> 0, `layout.pcd` 1, `system_time.csv` 1, `detector_time.csv` 1.
- E005-M18 means `DualMap` is executable on the staged `3RScan` adapter, but not yet usable as an object-map external baseline.
- E005-M19 selects `ConceptGraphs` fallback source/interface audit and rejects lower-`stable_num` `DualMap` as faithful baseline evidence.
- E005-M20 audits official `ConceptGraphs` source/interface with status `e005_m20_conceptgraphs_interface_audit_ready_with_adapter_required`.
- E005-M20 checks `ConceptGraphs` commit `93277a02bd89171f8121e84203121cf7af9ebb5d`, license `MIT`, and a posed RGB-D input route with `.pkl.gz` detection/map outputs.
- E005-M20 audits 4 local staged scans and finds direct ConceptGraphs-ready scans 0 / 4 because a separate `intrinsic_color.txt` and color/depth resolution alignment are required.
- E005-M20 selects `conceptgraphs_depth_aligned_scannet_smoke` as the next route.
- E005-M21 materializes `local_dataset/ConceptGraphs_staged/3rscan_depth_aligned_scannet/` with status `e005_m21_conceptgraphs_staging_materialized_smoke_ready`.
- E005-M21 staged scans are 4 / 4 ready, with 826 color JPGs, 826 depth PNGs, 826 pose TXTs, and 4 / 4 resolution-aligned scans at `224x172`.
- E005-M21 does not launch `ConceptGraphs` runtime.
- E005-M22 completes `ConceptGraphs` Docker/runtime preflight with status `e005_m22_conceptgraphs_runtime_preflight_ready_with_acquisition_required`.
- E005-M22 verifies Docker ready true, NVIDIA runtime true, GPU `NVIDIA GeForce RTX 5090` with 24008 MiB free, staged scans 4 / 4, and SAM checkpoint ready true.
- E005-M22 finds `ConceptGraphs` repo present false, `Grounded-Segment-Anything` repo present false, `research2/conceptgraphs-smoke:latest` present false, and `groundingdino_swint_ogc.pth` ready false.
- E005-M22 selects first smoke variant `class_set_none_sam_dense_smoke`; `RAM` and `LLaVA` are deferred until object-map feasibility is proven.
- E005-M23 launches repo/checkpoint acquisition in tmux `e005_m23_conceptgraphs_acquisition`.
- E005-M23 log path is `logs/20260514_165555_e005_m23_conceptgraphs_acquisition.log`.
- E005-M23 initial verification status is `e005_m23_conceptgraphs_acquisition_running`; `ConceptGraphs` head matches and `Grounded-Segment-Anything` clone starts.
- E005-M24 verifies acquisition completion with status `e005_m23_conceptgraphs_acquisition_completed_ready`.
- E005-M24 verifies `ConceptGraphs` head match true, `GSA` head match true, SAM symlinks ready true, and `groundingdino_swint_ogc.pth` ready with 693,997,677 bytes.
- E005-M23 does not launch runtime or Docker build.
- E005-M25/M26 build and verify `research2/conceptgraphs-smoke:latest` with import smoke passing.
- E005-M27 verifies one-scan `ConceptGraphs` runtime outputs after bounded command/resource/staging repairs.
- E005-M28/M29 inspect the object-map output schema and fix the output-to-query conversion contract.
- E005-M30/M31 export one-scan object candidates and convert them to query-level diagnostics.
- E005-M32 approves strict/relaxed-boundary 4-scan scaling.
- E005-M33/M34 complete pending 3-scan runtime after staging symlink and permission repairs.
- E005-M35 converts all 4 staged `ConceptGraphs` scans into candidate/query metrics: primary `M60` strict bbox top5 3 / 7, relaxed bbox 1m top3 6 / 7, expanded `M73` strict bbox top5 57 / 96.
- E005-M36 records the failure boundary: primary strict center top5 1 / 7, primary `chair` strict bbox hit 0 / 3, primary `pillow` strict bbox hit 3 / 4.
- E005-M37 completes external baseline comparison: `ConceptGraphs` is the first external mapping baseline to scale, `Open3DSG` is the next reasonable second external map/scene-graph route after scale, and final paper table claim remains false.
- E005-M38 fixes the `ConceptGraphs` heldout/scale contract: 13 scans, 291 eligible query rows after 3 generic rows are excluded, dev existing 4 scans / 96 rows, heldout sequence-required 9 scans / 195 rows.
- E005-M39 launches 9 heldout scan `sequence.zip` acquisition/staging in tmux `e005_m39_conceptgraphs_heldout_sequence`, with log `logs/20260515_174433_e005_m39_conceptgraphs_heldout_sequence.log`.
- E005-M39 is a background data-staging launch, not a heldout performance result.
- E005-M40 verifies heldout sequence staging: ready scans 9 / 9, valid `sequence.zip` rows 9 / 9, total frame triplet lower bound 2,982, minimum triplet count 111, tmux stopped true.
- E005-M40 is still not a heldout performance result.
- E005-M41 completes heldout runtime preflight: sequence-ready scans 9 / 9, staged payload ready 0 / 9, runtime output ready 0 / 9, Docker image ready true, model checkpoints ready true, runtime launch ready now false.
- E005-M41 is still not a heldout runtime result.
- E005-M42 materializes heldout `ConceptGraphs` staging: ready scans 9 / 9, color/depth/pose files 2,982 / 2,982 / 2,982, resolution-aligned scans 9 / 9, errors 0, container read/write smoke passed.
- E005-M42 is still not a heldout runtime result.
- E005-M43 launches `heldout_b01` with 3 staged-ready scans as tmux background job `e005_m43_conceptgraphs_heldout_runtime_b01`.
- E005-M44 verifies `heldout_b01` runtime outputs: ready scans 3 / 3, GSA detections 70 / 58 / 23, full PCD/post PCD ready for all selected scans.
- E005-M45 converts `heldout_b01` into query-level metrics: 3 scans, 66 / 195 heldout query rows, 22 target uids, 8 labels, 70 object rows, and 1,608 candidate rows.
- E005-M45 strict bbox top5 success is 45 / 66 = 0.681818, relaxed bbox 1m top3 success is 57 / 66 = 0.863636, and strict centroid top5 success is 27 / 66 = 0.409091.
- E005-M45 keeps `conceptgraphs_clip_rank_bbox_strict_top5_v0` as the primary strict paper-facing policy and keeps relaxed bbox / centroid metrics as diagnostics.
- E005-M46 interprets `heldout_b01` as a positive batch diagnostic, not a final baseline result, and selects `heldout_b02` / `heldout_b03` as required remaining runtime batches before external-baseline claim.
- E005-M46 fixes the novelty comparison contract: `static_stale_memory`, `detector_confidence_ranking`, `ConceptGraphs-only open-vocabulary map`, `task-agnostic re-observation`, and H001 `task-conditioned memory trust / re-observation / search-cost policy`.
- E005-M48 verifies `heldout_b02` runtime outputs: ready scans 3 / 3, GSA detections 210 / 63 / 33, full PCD/post PCD ready for all selected scans.
- E005-M49 aggregates all 9 heldout `ConceptGraphs` scans: strict bbox top5 114 / 195 = 0.584615, relaxed bbox 1m top3 144 / 195 = 0.738462.
- E005-M52 replays H001 on the same `M38` query contract: H001 172 / 195 = 0.882051, static memory 141 / 195 = 0.723077, context-agnostic memory trust 171 / 195 = 0.876923.
- E005-M53 paired analysis fixes the boundary: H001-vs-`ConceptGraphs` and H001-vs-static memory proxy-search claims are ready, but task context as the main contribution is not ready.
- E005-M54 claim ledger fixes the paper-facing method claim: memory trust, staleness handling, and bounded re-observation are the main claim; human task context is secondary.
- E005-M55 selects the robustness expansion route: first define a two-table robustness denominator and audit `Open3DSG`; keep `OpenMask3D` as a later proposal baseline because it is still Docker/`MinkowskiEngine` blocked.
- E005-M56 fixes the denominator split: Table A proxy-search external map denominator is 195 rows, Table B real RGB-D proposal bridge denominator is 96 rows.
- E005-M56 audits `/home/yoohyun/research/local_dataset/Open3DSG_staged` read-only. Source, checkpoints, feature `.pt` artifacts, `OpenSG_3RScan` view `.pkl` files, and existing eval metrics are present, but `Open3DSG` query-level performance is not ready.
- E005-M57 inspects `Open3DSG` output schema and fixes the conversion contract. Derived results are stored under `/home/yoohyun/research2/local_dataset/Open3DSG_bridge/E005-M57_output_schema_contract_v0/`.
- E005-M57 finds that relation raw dump is ready, but object-search comparison needs an object-candidate score export; aggregate `Open3DSG` eval metrics are not query-convertible.
- E005-M58 fixes the `Open3DSG` object-candidate export plan, read-only Docker command contract, local output path, and verifier.
- E005-M59 initially failed on CUDA OOM during `InstructBLIP` checkpoint loading, then the lower-memory object-only relaunch succeeded with 180 object-candidate rows and 1 completed batch.
- E005-M59 repair route is lower-memory object-only export. This is preferred over blind GPU-exclusive relaunch because object candidate export does not require relation captioning, while `InstructBLIP` loading was the observed failure point.
- E005-M60 fixes and verifies the `Open3DSG` query-level conversion path. It maps object-candidate rows to the same 195-row M38/M45 denominator used by `ConceptGraphs` and H001 replay.
- E005-M60 planned policies are `open3dsg_objects_probs_bbox_strict_top5_v0`, `open3dsg_objects_probs_bbox_relaxed_1m_top3_v0`, and `open3dsg_objects_probs_center_strict_top5_v0`.
- E005-M60 planned metrics are target detected rate, query bridge success rate, target rank, `ExpectedSearchCost`, `AttemptSPL` proxy, old-location dead-end avoidance, and failure classes.
- Corrected E005-M60 rerun over M61 rows has 585 policy rows, 759 query candidate/eval rows, scan overlap 9 / 9, strict bbox top5 81 / 195, relaxed bbox 1m top3 90 / 195, and center strict top5 21 / 195.
- E005-M61 completes denominator-aligned export: all 9 query scans are covered, with 195 query rows, 51 target subgraphs, and 7,600 object-candidate rows.
- E005-M62 interprets `Open3DSG` as bridge-feasible but not a strong main-table performance baseline under the current primary-label adapter.
- E005-M63 selects bounded `Open3DSG` predicted-vocabulary expansion repair: diagnostic strict bbox top5 144 / 195 and relaxed bbox 1m top3 147 / 195.
- E005-M64 implements and verifies the bounded `Open3DSG` predicted-vocabulary adapter leakage-safely: strict bbox top5 144 / 195, relaxed bbox 1m top3 147 / 195, query/eval candidate rows 1,533, policy rows 585.
- E005-M65 fixes table integration: include `Open3DSG` predicted-vocabulary adapter as a bounded external scene-graph baseline row, exclude primary-label adapter from the main table, and keep human intent as structured task-context secondary evidence.
- E005-M66 fixes row-level failure boundaries: H001 vs `ConceptGraphs` both_success 112 / H001-only 60 / `ConceptGraphs`-only 2 / both_fail 21; H001 vs `Open3DSG` vocab both_success 133 / H001-only 39 / `Open3DSG`-only 11 / both_fail 12; human intent task-context-specific gain 1 row.
- E005-M67 selects `scale_real_proposal_bridge_to_m38_heldout_denominator` as the next real RGB-D/open-vocabulary robustness route. The M38/M45 denominator has 195 query rows across 9 scans, while E003-M75 currently covers 96 real-proposal rows, so the immediate gap is denominator scale/alignment rather than another paper-table claim.
- E005-M68 materializes the full-denominator real proposal bridge plan: 195 query rows, 9/9 ready scans, 65 object targets, 22 prompt labels, 214 sampled frames, 3 heldout batches, and 0 row-level overlap with E003-M75.
- E005-M69 launches `heldout_b01` detector batch in tmux `e005_m69_real_proposal_heldout_b01`, with log `logs/20260524_004619_e005_m69_real_proposal_heldout_b01.log` and output path `E005-M69_full_denominator_real_proposal_detector_run_v0/heldout_b01/`.
- E005-M70 verifies `heldout_b01` detector completion: expected files 12/12, prediction rows 261, pre-cap candidate rows 5,310, matched targets 18/22, scan target recall 0.8182, proposal precision 0.0690, false-positive rate 0.9310, and mean matched centroid error 0.5892m.
- E005-M71 converts `heldout_b01` real proposals into query-level metrics: target detected 54/66, mean target rank 8.777778, mean false positives before target 7.777778, real detector task-budget 8/66, real detector top5 21/66, static memory 45/66, context-agnostic memory trust 48/66, H001 real memory-trust 48/66, and `ConceptGraphs` same-batch 45/66.
- E005-M72/M73/M74 complete `heldout_b02` launch, detector verification, and query conversion: detector expected files 12/12, prediction rows 264, pre-cap candidates 6,799, matched targets 14/17, scan target recall 0.8235, proposal precision 0.0530, false-positive rate 0.9470, query target detected 42/69, real detector task-budget 5/69, real detector top5 9/69, H001 54/69, context-agnostic memory trust 54/69, and `ConceptGraphs` same-batch 45/69.
- E005-M73 verifies `heldout_b03` detector completion: expected files 12/12, prediction rows 400, matched targets 16/20, scan target recall 0.8000, proposal precision 0.0400.
- E005-M74 converts `heldout_b03` into query-level metrics: target detected 48/60, H001 55/60, context-agnostic 54/60, `ConceptGraphs` same-batch 24/60, detector task-budget 11/60, detector top5 21/60.
- E005-M75 aggregates b01/b02/b03: query rows 195, target detected 144/195, H001 157/195, context-agnostic memory trust 156/195, `ConceptGraphs` same-batch 114/195, detector task-budget 24/195, detector top5 51/195, selected route `aggregate_diagnostic_ready_review_claim_boundary`.
- E005-M76 fixes the real-proposal claim boundary: M75 is diagnostic-table ready, final real RGB-D/open-vocabulary robustness remains blocked, and the next route is `include_diagnostic_table_then_offline_detector_prompt_repair`.
- E005-M76 detector aggregate precision is 0.051892, detector scan-target recall is 0.813559, mean false positives before target is 8.104167, and human intent main claim readiness is false.
- E005-M77 analyzes existing M69 pre-cap candidate pools without a new detector run: 23,742 pre-cap candidate rows, 65 target rows, 195 query rows.
- E005-M77 finds pre-cap detected targets 54 / 65 versus current selected detected targets 48 / 65.
- E005-M77 repair classes are `rank_or_false_positive_budget_gap` 29, `selection_or_cap_lost_target` 6, `prompt_or_detector_recall_miss` 11, and `already_top5_or_memory_recovered` 19.
- E005-M77 best offline policy is `offline_confidence_log_depth_radius0p5_cap24`, with top5 success 60 / 195 versus current replay/M75 detector top5 51 / 195.
- E005-M77 selects `offline_replay_repair_candidate_then_targeted_detector_rerun` and next `E005-M78 offline repair replay implementation`.
- E005-M78 implements fixed `offline_confidence_log_depth_radius0p5_cap24_fixed_replay_v0` over the same M69 pre-cap candidate pools.
- E005-M78 reproduces M77 best policy with top5 mismatch 0 and target-rank mismatch 0.
- E005-M78 fixed replay selected 926 proposals, matched 98 proposal rows, reached proposal precision 0.105832, scan target recall 49 / 65, query target detected 147 / 195, and top5 success 60 / 195.
- E005-M78 improves over M75 detector top5 by +9 rows but remains -97 rows behind H001 real memory-trust policy.
- E005-M78 selects `fixed_offline_repair_ready_for_runner_insertion_or_targeted_rerun` and next `E005-M79 runner insertion point and targeted repair rerun plan`.
- E005-M79 confirms runner source edit required false and fixes insertion point `select_cap_aware_label_balanced_candidates.score_candidate_before_spatial_consolidation_and_caps`.
- E005-M79 fixes `confidence_log_depth` as the runner score mode and writes 3 targeted rerun command plans.
- E005-M79 selects `heldout_b02` as the first rerun batch because M78 expected top5 gain is largest there: M75 detector top5 9/69 -> M78 fixed top5 15/69.
- E005-M79 selects `gain_batch_first_targeted_rerun_then_remaining_batches_if_reproduction_holds` and next `E005-M80 confidence-log-depth targeted detector rerun launch for heldout_b02`.
- E005-M80 launches `heldout_b02` confidence-log-depth targeted detector rerun in tmux `e005_m80_confidence_log_depth_heldout_b02`, with log `logs/20260526_020840_e005_m80_confidence_log_depth_heldout_b02.log`, output `E005-M80_confidence_log_depth_detector_run_v0/heldout_b02/`, and GPU free at launch 24,421 MiB.
- E005-M81 verifies M80 completion: expected files 14/14, prediction rows 264, pre-cap candidates 6,799, matched targets 14/17, proposal precision 0.053030, scan target recall 0.823529.
- E005-M82 converts M80/M81 into query-level metrics: `heldout_b02` target detected 42/69, detector task-budget 7/69, detector top5 15/69, H001 54/69, context-agnostic memory trust 54/69, `ConceptGraphs` same-batch 45/69.
- E005-M82 reproduces the expected b02 top5 gain over M71/M74 baseline: detector top5 9/69 -> 15/69 and task-budget 5/69 -> 7/69, while target detected stays 42/69.
- E005-M83 interprets the rerun result and stops immediate b01/b03 reruns. b01 expected top5 gain is 0, b03 expected top5 gain is 3 rows, all-batch fixed-policy expectation is 60/195, and H001 real memory-trust policy is 157/195.
- E005-M83 selects `stop_remaining_reruns_record_diagnostic_boundary_then_repair_recall_or_external_proposal`.
- E005-M84 decides the next route after M83: prompt/detector recall-miss targets are 11/65, max query-detection exposure is 33/195, remaining b01/b03 ranking gain is 3 rows, `Grounded-SAM` same-subset weak positive is false, and `OpenMask3D` has 3 hard blockers.
- E005-M84 selects `prompt_label_recall_audit_first_then_external_proposal_baseline_gate`.
- E005-M85 audits the 11 prompt/detector recall-miss targets: no-same-label candidate 5, localization/matcher audit 5, broad/missing label 1.
- E005-M85 fixes a leakage-safe repair contract: repair policy may use prompt labels/aliases, RGB-D frames, and pre-cap candidate fields, but not `target_uid`, `object_instance_id`, target match distance, or query success labels.
- E005-M86 decides prompt repair is not ready: 11 targets / 33 query rows audited; visibility/matcher audit covers 5 targets / 15 rows, zero-written scan audit covers 5 targets / 15 rows, and broad-label contract covers 1 target / 3 rows.
- E005-M86 selects `candidate_survival_match_threshold_and_zero_written_scan_audit_before_prompt_rerun` and does not launch a detector rerun.
- E005-M87 audits candidate survival, match thresholds, and the zero-written scan path: strict pre-cap suppressed targets are 0, selected 1.5m-threshold recovery covers 2 targets / 6 rows, pre-cap 1.5m recovery covers 3 targets / 9 rows, same-label instance ambiguity covers 2 targets / 6 rows, and the `569d8f0f` zero-written cluster covers 5 targets / 15 rows.
- E005-M87 selects `zero_written_raw_label_trace_before_prompt_or_threshold_repair` and keeps prompt repair / detector rerun blocked.
- E005-M88 localizes the `569d8f0f` zero-written cluster: M69/M80 raw/projected/written are 513 / 483 / 0, active scan label is `chair`, prompt has `chair=true`, pre-cap rows are 0, and the likely loss stage is prompt-label cleanup before spatial consolidation/caps.
- E005-M88 cannot prove the exact repair because existing artifacts do not store raw `label_text`, resolved `label_canonical` distributions, or cleanup drop reasons per scan.
- E005-M89 verifies the `569d8f0f` cleanup trace target-independently: 483 trace rows, all dropped, `drop_not_scan_prompt_label` 479, `drop_non_prompt_label` 4, canonical `stool` 479, canonical `a` 4, active scan label `chair`, blocked-field hits 0.
- E005-M89 shows the zero-written cluster is dominated by label-resolution / scan-prompt scope mismatch rather than score ranking, cap, or match-threshold failure.
- E005-M90 selects `active_scan_exact_label_precedence_v0` and rejects `scan_prompt_scope_expand_stool_for_chair_scan_v0`.
- E005-M90 active-exact replay would keep 479 / 483 cleanup-trace rows, with blocked-field hits 0 and worst-case new selected proposal upper bound 24 before matching.
- E005-M91 implements `active_scan_exact_label_precedence_v0` in the real-proposal runner and verifies a one-scan cleanup smoke on `569d8f0f`.
- E005-M91 recovers M89 zero-written output from pre-cap/final 0 / 0 rows to pre-cap/final 479 / 24 rows, with cleanup keep/drop 479 / 4 and selected proposal cap respected.
- E005-M91 matching smoke finds matched target rows 5 / 5, scan target recall 1.0, proposal precision 0.208333, and false positives 19 / 24 on the one-scan smoke.
- E005-M92 converts the one-scan effect into query exposure: affected query rows 15, affected targets 5, M82 target detected 0 / 15, M91 target detected 15 / 15.
- E005-M92 lower-bound affected detector top5 gain is +3 rows and task-budget gain is +2 rows, but H001 success stays 6 / 15 before and after one-scan conversion.
- E005-M92 finds one b02 side-effect-risk scan with 15 `chair`/`stool` conflict-exposed query rows, including 3 `stool` rows.
- E005-M93 completes bounded `heldout_b02` active-label precedence rerun, verification, query conversion, and result analysis.
- E005-M93 target detected rows improve 42 / 69 -> 57 / 69, detector top5 improves 15 / 69 -> 18 / 69, detector task-budget stays 7 / 69, H001 stays 54 / 69, target detection gain/loss is 15 / 0, and observed side-effect loss is 0.
- E005-M93 proposal precision is 0.065972 and scan target recall is 0.863636, so false-positive load remains weak.
- E005-M94 fixes the claim-boundary decision: selected route `stop_and_record_m93_as_batch_level_repair_diagnostic`.
- E005-M94 projected diagnostic aggregate if b02 is replaced by M93 is target detected 159 / 195, detector top5 60 / 195, detector task-budget 26 / 195, and H001 157 / 195.
- E005-M95 fixes the paper-facing real-proposal diagnostic table and final E005 boundary: 7 main diagnostic rows, 4 repair diagnostic rows, 2 allowed diagnostic claims, and 4 blocked claims.
- E005-M95 allowed diagnostic claims are full-denominator H001 comparison against detector-only / `ConceptGraphs` same-batch baselines and active-label precedence as b02 cleanup-failure repair evidence.
- E005-M95 blocked claims are final real RGB-D/open-vocabulary robustness, deployable search policy, real navigation `SR` / `SPL`, and human intent as a main contribution.
- E005-M96 selects `external_proposal_mapping_baseline_first` over `navigation_search_bridge_first`.
- E005-M96 next recommended unit is E005-M97 external proposal/mapping baseline feasibility matrix.
- E005-M97 completes the external proposal/mapping feasibility matrix and selects `conceptgraphs_derived_map_candidate_route` as the first smoke route.
- E005-M97 keeps `Open3DSG` bounded vocab adapter as a supporting row, `OpenMask3D` as environment-blocked, and `HOV-SG` as source-audit required.
- E005-M98 completes the `ConceptGraphs` reliability boundary smoke over 195 rows: `ConceptGraphs` strict top5 114, real detector top5 51, real detector task-budget 24, H001 157.
- E005-M98 finds 54 `h001_recovers_both_map_and_real_top5_failure` rows and 24 `map_success_h001_failure` rows.
- E005-M99 completes row-group / heavier-route decision: H001 failure 38 rows / 13 targets, `ConceptGraphs` map-assisted repair candidate 24 rows / 8 targets, H001-or-`ConceptGraphs` upper bound 181 / 195, selected next `E005-M100`.
- E005-M100 completes `ConceptGraphs`-assisted fallback policy smoke: selected `h001_then_conceptgraphs_top5_on_observed_miss_v0`, H001 success 157 / 195 -> 181 / 195, `AttemptSPL` 0.773932 -> 0.798675, mean `ExpectedSearchCost` 1.758974 -> 2.435897.
- E005-M101 marks M100 as paper-facing query-level table ready with boundary and selects E007-M01 navigation/path-cost bridge contract.
- E007-M01 completes the first navigation/path-cost bridge contract: M100/E002 row overlap 195 / 195, E002 target-grid reachable overlap 186 / 195, `ConceptGraphs` query overlap 195 / 195, real detector proposal rows 925, selected path-cost source `e002_occupancy_grid_astar_v0`.
- E007-M02 materializes 1,170 query-policy rows into 3,814 route rows. Candidate-grid projection-ready route rows are 705; external projection-pending route rows are 3,097; source gap rows are 36.
- E007-M03 projects external candidate coordinates onto the E002 grid and computes route-level path-cost fields. Route projection-ready rows are 3,785 / 3,814, route path-ready rows are 3,331 / 3,814, query-policy eval-ready rows are 928 / 1,170, source-limited query-policy rows are 216, and no-route query-policy rows are 36.
- E007-M04 evaluates policy-level path-cost metrics with source-limited accounting. Source-ready query-policy rows are 972 / 1,170; method full success is 181 / 195; method source-ready success is 163 / 174; mean path cost is 2.996131m; mean `PathAttemptSPLProxy` is 0.824554.
- E007-M04 paired source-ready deltas for method `h001_then_conceptgraphs_top5_on_observed_miss_v0`: vs static success +0.178161 / `PathAttemptSPLProxy` +0.065933; vs `ConceptGraphs` success +0.312925 / `PathAttemptSPLProxy` +0.564378; vs H001-only success +0.054545 / `PathAttemptSPLProxy` +0.004390 / path cost +0.941948m.
- E007-M05 interprets E007-M04 as a paper-facing occupancy-grid path-cost bridge table, not as a main navigation table.
- E007-M05 keeps real navigation `SR` / `SPL` false and `OldLocationDeadEndCostM` as a primary metric false.
- E007-M05 identifies reviewer-critical sensitivity points: 198 / 1,170 source-limited query-policy rows, 47 / 1,170 upstream expected-search-cost stop rows, and the old-memory centroid path-start assumption.
- E007-M06 audits those sensitivity points: source-limited rows 198 / 1,170, stop-rank rows 47 / 1,170, old-first non-target zero-step route rows 153.
- E007-M06 stricter direct/failure source-ready deltas for method remain positive against static memory (+0.111801), detector-confidence ranking (+0.636364), `ConceptGraphs`-only (+0.291045), context-agnostic memory trust (+0.059211), and H001-only (+0.059211).
- E007-M07 packages the final E007 bridge table as `paper_facing_occupancy_grid_path_cost_proxy_table`.
- E007-M07 paper table package ready is true, table rows are 6, allowed claim rows are 3, blocked claim rows are 3, and selected next unit is E008-M01 real navigation benchmark/source preflight and episode contract.
- E007-M07 does not launch a long-running simulator/navigation job.
- E008-M01 completes real navigation source/episode preflight.
- E008-M01 selected source is local read-only `HM3D ObjectNav` + `Habitat` at `/home/yoohyun/research3/local_dataset/data`.
- E008-M01 verifies 1,095 `HM3D` `.glb` files, 910 `.navmesh` files, 10 `minival` `.navmesh` files, 2 `ObjectNav val_mini` content files, and 30 parsed `ObjectNav val_mini` episodes.
- E008-M01 verifies Docker image `research3/habitat-h001:20260508-calib-artifacts` can import `habitat_sim`, `habitat`, `magnum`, and `numpy`.
- E008-M01 selects E008-M02 `HM3D ObjectNav` episode/source adapter smoke and does not launch a long-running navigation job.
- E008-M02 completes `HM3D ObjectNav` episode/source adapter smoke.
- E008-M02 samples 6 `ObjectNav val_mini` episode rows from 2 content files and resolves them to 2 `HM3D` scenes.
- E008-M02 verifies scene/navmesh readiness for 6 / 6 episode rows.
- E008-M02 verifies Docker `Habitat` scene load and pathfinder readiness for `00800-TEEsavR23oF` and `00802-wcojb4TFT35`.
- E008-M02 selects E008-M03 `H001` candidate-to-navigation adapter contract and does not launch a long-running navigation job.
- E008-M03 completes H001 candidate-to-navigation adapter contract.
- E008-M03 prepares 6 / 6 `ObjectNav` eval goal/viewpoint rows and 7 policy adapter rows.
- E008-M03 marks `ObjectNav` goal positions, object ids, viewpoints, and shortest-path distances as evaluation-only blocked policy inputs.
- E008-M03 confirms H001 candidate-source rows ready for `HM3D` execution are 0.
- E008-M03 selects E008-M04 `ObjectNav` goal/viewpoint oracle path smoke and does not launch a long-running navigation job.
- E008-M04 completes `ObjectNav` goal/viewpoint oracle path smoke.
- E008-M04 verifies eval-only viewpoint shortest paths for 6 / 6 episodes and goal-snapped paths for 4 / 6 episodes.
- E008-M04 mean oracle viewpoint path length is 5.738806m.
- E008-M04 keeps oracle rows blocked from policy input and selects E008-M05 `HM3D` candidate-source staging plan.
- E008-M05 completes `HM3D` candidate-source staging plan.
- E008-M05 verifies `HM3D` semantic files for 2 / 2 scenes and semantic category label support for 6 / 6 episode rows.
- E008-M05 selects `hm3d_semantic_annotation_candidate_source_smoke` as E008-M06 and keeps rendered RGB-D detector / `ConceptGraphs` external-map candidate sources deferred.
- E008-M05 does not produce candidate coordinate rows yet; H001 policy execution remains false.
- E008-M06 completes `HM3D` semantic annotation candidate-source smoke.
- E008-M06 confirms semantic label support 6 / 6, Habitat semantic nonzero-AABB scenes 0 / 2, GLB semantic geometry mapping scenes 0 / 2, and candidate rows 0.
- E008-M06 rejects `ObjectNav` goal/viewpoint as a policy candidate source and selects E008-M07 `HM3D` rendered RGB-D detector candidate-source plan.
- E008-M07 completes `HM3D` rendered RGB-D detector candidate-source plan.
- E008-M07 fixes 24 start-pose fixed yaw-sweep render rows, 6 detector manifest rows, 5 detector labels (`bed`, `chair`, `monitor`, `television`, `tv`), and E003 detector compatibility layout under `3RScan/scans/<scan_id>/sequence`.
- E008-M07 verifies `Habitat` image `research3/habitat-h001:20260508-calib-artifacts` and detector image `research2/real-smoke:latest` are ready, but launches no long job.
- E008-M08 completes `HM3D` rendered RGB-D frame staging smoke.
- E008-M08 verifies 24 / 24 rendered RGB-D/pose rows, 6 / 6 detector-compatible sequence dirs, 6 detector manifest rows, and detector input files ready under `local_dataset/HM3D_navigation_bridge/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0/`.
- E008-M08 selects E008-M09 `HM3D` rendered RGB-D detector candidate smoke and launches no long navigation job.
- E008-M09 completes `HM3D` rendered RGB-D detector candidate smoke.
- E008-M09 verifies E003 detector status `pre_cap_candidate_pool_export_smoke_ready`, frame rows 24, raw/written predictions 441 / 137, prediction rows 137, coordinate candidate rows 137, pre-cap candidate rows 409, evaluated scans 6, validator errors/warnings 0 / 0.
- E008-M09 matching status is `detector_matching_smoke_ready`, but `ObjectNav` goal/viewpoint fields are blocked so target recall is not evaluated in this unit.
- E008-M10 completes detector candidate coordinate-frame / snap-to-navmesh validation.
- E008-M10 verifies 137 / 137 frame/scene joins, 137 / 137 coordinate-valid rows, 136 / 137 snapped navigable rows, and 125 / 137 source-to-snapped paths.
- E008-M10 retains 12 warning/failure rows: 11 unreachable snapped points and 1 non-finite snap failure.
- E008-M11 completes reachable-subset detector candidate visit-order path smoke.
- E008-M11 materializes 512 visit-order rows and 28 policy metric rows over 4 policies, with 125 / 137 path-ready candidate rows and 12 explicit failure rows.
- E008-M11 does not use eval-only `ObjectNav` goal/viewpoint fields as policy input.
- E008-M12 completes leakage-safe detector candidate goal-evaluation smoke.
- E008-M12 materializes 512 candidate-goal eval rows, 24 scan-policy metric rows, 4 aggregate policy rows, and 12 primary failure rows.
- E008-M12 primary `any_viewpoint_xz_1p0` `GoalEvalProxySR` is 3 / 6 for all 4 policies; `goal_xz_1p0` proxy success is 1 / 6.
- E008-M12 leakage audit passes: eval-only `ObjectNav` goal/viewpoint fields are used for metrics, not policy input.
- E008-M13 completes detector-goal failure audit over 6 episodes and 12 policy failure rows.
- E008-M13 finds 3 all-policy failure episodes: 2 `target_region_missing_in_precap_detector_pool`, 1 `near_miss_localization_threshold`, and 0 `post_cap_or_snap_suppression`.
- E008-M13 selects `bounded_start_neighborhood_multiview_v0` as the next non-oracle observation-coverage route.
- Real navigation `SR` / `SPL` remains unsupported.
- Final real RGB-D/open-vocabulary robustness claim remains unsupported.

논문 주장:

- The currently defensible paper core is `Task-Conditioned Stale Semantic Memory Update`.
- The current paper should not claim a better detector, deployable navigation policy, or natural-language intention understanding.
- M78/M83 can be used as detector-ranking repair diagnostic evidence, but they should not be merged into the main H001 memory-decision claim.
- M89 can be used as cleanup failure diagnosis evidence, but not as prompt repair or final real RGB-D/open-vocabulary robustness evidence.
- M90 can be used as a leakage-safe repair-route decision, but not as repair performance evidence.
- M91 can be used as failure-specific repair smoke evidence, but not yet as full-denominator real RGB-D/open-vocabulary robustness evidence.
- M92 can be used as a route decision: the repair should be tested with bounded `heldout_b02` rerun before updating the main real-proposal query table.
- M93/M94 can be used as batch-level target-detection repair diagnostic evidence, but not as the main H001 semantic-memory gain.
- M95 can be used as the final E005 paper-facing boundary: M75 is the real-proposal diagnostic table, while M93/M94 are repair/failure-analysis rows.
- M96 can be used only as a route decision: external proposal/mapping baseline feasibility should precede navigation execution.
- M97 can be used only as a feasibility decision: the next smoke should analyze `ConceptGraphs`-derived proposal/map reliability, not claim final robustness.
- M98 can be used as a row-level reliability diagnostic, but it does not make final real RGB-D/open-vocabulary robustness ready.
- E007-M05 can be used as a paper-facing bridge-table boundary: E007-M04 is valid as an occupancy-grid path-cost proxy, not as final navigation evidence.
- E007-M06 can be used as reviewer defense for that bridge table: the result survives direct/failure-only sensitivity, but `OldLocationDeadEndCostM` stays blocked.
- E007-M07 can be used as the final E007 package: the bridge table, claim ledger, and reviewer-defense rows are ready, but E008 evidence is still source/adapter smoke rather than real navigation execution.
- E008-M01/M02/M03/M04/M05/M06/M07 can be used as source/adapter/contract/oracle-metric/staging evidence: a real navigation route is locally available, a tiny `HM3D ObjectNav` adapter is executable, the H001 candidate schema is fixed, oracle metric plumbing works, the semantic annotation coordinate path has been tested and rejected, and the rendered RGB-D detector-source route is planned. This is still not H001 execution evidence and not a stale-memory dynamics result.
- The final paper target is Direction B: `Task-Aware Dynamic Semantic Mapping for Open-Vocabulary Search and Navigation`.

에이전트 추론:

- The strongest current framing is a semantic memory decision problem: when a robot has stale semantic memory and noisy current proposals, task context changes memory trust, re-observation priority, search budget, and candidate visit order.
- The current work is more defensible as semantic mapping for embodied decision-making than as a pure perception or navigation paper.
- The current direction is technically correct for top-tier positioning because M89-M98 follow a defensible chain: failure diagnosis, leakage-safe principle, runner-level repair, batch rerun, claim-boundary decision, route selection, external feasibility gating, and row-level reliability boundary. It will become weak if presented as a detector cleanup contribution rather than as robustness support for the semantic memory decision layer.

## Current Contribution Candidates

사실:

- E001 creates query/candidate rows from `3RScan` / `3DSSG` dynamic scan pairs.
- E001 evaluates static old-location, fixed top-k, task-conditioned, and oracle policies.
- E002 adds path/search-cost fields and separates source-limited rows from policy failures.
- E003 tests controlled noise profiles: `annotation_score_jitter_v0`, `annotation_proposal_dropout_v0`, `annotation_false_positive_v0`, `annotation_centroid_jitter_v0`, and `annotation_combined_moderate_v0`.
- E003 implements Dockerized `groundingdino_rgbd_backproject_v0` proposal generation and matching diagnostics.
- E003-M33 scaled real-proposal diagnostic covers 8 scans / 192 frames with 3,414 final proposal rows, 204 / 344 matched target rows, proposal precision 0.059754, and depth-consistent visible-proxy recall 0.915584.
- E003-M45 support-aware replay failed: `confidence_sqrt_depth_support_temporal_v0` produced 196 matched / 3,211 false positives / precision 0.057529, worse than the `confidence` baseline 204 / 3,210 / 0.059754.
- E003-M50 showed `Grounded-SAM mask-depth` did not beat `bbox-depth` on the same subset.

논문 주장:

- Contribution 1: a task-conditioned stale semantic memory decision formulation for dynamic object search.
- Contribution 2: a query/evaluation harness connecting stale object memory, task context, candidate ranking, search cost, and perception noise.
- Contribution 3: failure-boundary analysis showing when stale memory update fails under proposal dropout, false positives, centroid jitter, support-signal saturation, and detector/search bridge mismatch.
- Contribution 4: a reproducible Dockerized route for real RGB-D/open-vocabulary proposal diagnostics, with explicit claim boundary.

에이전트 추론:

- Contribution 1 is the clearest intellectual contribution.
- Contribution 2 is necessary for paper defensibility because existing semantic mapping papers often stop at map quality or retrieval, not stale-memory decision outcomes.
- Contribution 3 is important because several intuitive improvements failed; this can become a strong paper asset if presented as principled boundary analysis, not as negative clutter.
- Contribution 4 is not yet a main contribution. It is currently infrastructure and diagnostic evidence.

## Reviewer Attack Points

사실:

- `ConceptGraphs` has been run and converted to query-level metrics on all 9 heldout scans. E005-M54 makes this usable as a proxy-search external map baseline, but not as a final real RGB-D/open-vocabulary robustness claim.
- `Open3DSG` has passed source/interface audit, output schema contract, object-candidate export planning, lower-memory object export smoke, denominator-aligned export, query-conversion implementation, route decision, and leakage-safe predicted-vocabulary policy evaluation from an existing staged read-only path. Corrected primary-label metrics are below `ConceptGraphs`, but the bounded predicted-vocabulary adapter reaches strict bbox top5 144 / 195.
- External routes such as `HOV-SG`, `VLFM`, `HM3D-OVON`, `GOAT-Bench`, and `3D-Mem` have not yet been run in this workspace.
- `DualMap` has been staged and executed, but current M14/M17 runs lack object `*.pkl` outputs, so it is not yet a valid object-map baseline result.
- E001/E002 still use proxy search metrics, not real executed navigation.
- E003 real perception evidence is connected to direct current-rescan query rows, and E005-M75/M76 now scales the real-proposal diagnostic to the 195-row heldout denominator.
- The current real-proposal artifact is still diagnostic rather than final robustness evidence because detector precision and false-positive load are weak.
- The current visibility denominator is a centroid/depth-consistent proxy, not true object visibility.

에이전트 추론:

- Attack 1: novelty may look like heuristic top-k re-ranking.
- Attack 2: benchmark may look self-defined and too small.
- Attack 3: proxy `SR` / `AttemptSPL` may be considered insufficient for robotics.
- Attack 4: real RGB-D/open-vocabulary route has weak precision and negative support-aware / `Grounded-SAM` results.
- Attack 5: missing external baselines make the contribution hard to position against current open-vocabulary mapping and embodied navigation work.
- Attack 6: human intent may look shallow because current task context is structured, not natural language.
- Attack 7: current evidence may look like a collection of gates rather than one clean method/evaluation story.
- Attack 8: if broadened too early, the work may become an engineering integration paper without a sharp algorithmic contribution.
- Attack 9: `Open3DSG` may look overclaimed if schema/contract work is presented as baseline performance.
- Attack 10: `ConceptGraphs` may still look like the cleaner external mapper because `Open3DSG` needs a vocabulary adapter to become competitive.

## Reviewer Defense Priorities

논문 주장:

- The main claim should be: task/staleness-aware semantic memory update improves dynamic object search decisions under stale memory and noisy proposals.
- The method should be defended as a semantic mapping decision layer, not as a detector, language parser, or navigation planner.
- The current `Open3DSG` statement should distinguish primary-label evidence from bounded predicted-vocabulary adapter evidence; M64 is a leakage-safe adapter policy, not standalone method novelty.

에이전트 추론:

- Defense 1: formalize stale semantic memory as a decision problem with explicit inputs, forbidden information, outputs, and metrics.
- Defense 2: include ablations for task context, staleness score, memory trust, re-observation budget, reachable-first ordering, proposal filtering, and path/search-cost term.
- Defense 3: separate controlled annotation-proxy evidence, real proposal diagnostic evidence, and real navigation evidence in all tables.
- Defense 4: use E003-M75 as the current bridge evidence, while clearly stating that the bounded repair is not yet a final deployable policy.
- Defense 5: use `ConceptGraphs` as the current converted positive external map baseline and use M64 `Open3DSG` as a bounded vocabulary-adapter external baseline row only after claim-boundary integration.
- Defense 6: keep structured task context as the controlled condition; add LLM parsing only as an adapter after the decision contract is stable.
- Defense 7: report negative results such as E003-M45 and E003-M50 as boundary evidence, not failed side experiments.
- Defense 8: scale from diagnostic scans to heldout splits only after the detector/evaluation bridge is stable.
- Defense 9: treat `ConceptGraphs` heldout scale as baseline rigor, not novelty; the novelty claim must come from H001 improving `ExpectedSearchCost`, proxy `SR`, proxy `SPL`, stale-memory recovery, and failure reduction over static stale memory, detector-confidence ranking, `ConceptGraphs`-only map retrieval, and task-agnostic re-observation.
- Defense 10: report `Open3DSG` primary-label and predicted-vocabulary rows separately, and make clear that the adapter uses only `scan_id`, `query_label`, predicted `candidate_label`, `candidate_score`, and `candidate_rank` before ranking.

## Reviewer Defense Ledger

사실:

| Reviewer concern | Current evidence | Current boundary |
| --- | --- | --- |
| Is this only heuristic top-k reranking? | H001 is compared against static memory, detector top-k, `ConceptGraphs` rank, context-agnostic memory trust, and unbounded detector upper-bound policies on the same 195-row M38 denominator. | Needs a cleaner method description that derives memory trust / re-observation / search-cost decisions from stale-memory failure taxonomy. |
| Is the benchmark self-defined? | Query rows come from dynamic `3RScan` / `3DSSG` scan pairs and are evaluated against external `ConceptGraphs` output on all 9 heldout sequence-required scans. | Still not a standard public navigation benchmark; real `SR` / `SPL` requires simulator or navmesh episodes. |
| Is `ConceptGraphs` enough as an external baseline? | `ConceptGraphs` is fully converted on 195 heldout rows and is a valid proxy-search external map baseline. | Not enough for final real RGB-D/open-vocabulary robustness by itself; `Open3DSG` M64 adds a second bounded external scene-graph row, but it is adapter-based. |
| Can `Open3DSG` be claimed as a baseline? | M56-M66 prove source/interface/schema/export/query-conversion, denominator alignment, corrected query-level metrics, leakage-safe predicted-vocabulary policy evaluation, and row-level failure boundary without modifying the read-only source. | Primary-label baseline is valid but below `ConceptGraphs` at 81 / 195 strict. Predicted-vocabulary adapter is stronger at 144 / 195 strict but should be labeled as a bounded adapter row. |
| Does this prove real RGB-D/open-vocabulary robustness? | E003-M75 gives a real proposal bridge with 87 / 96 target detected rows and 33 / 96 bounded repair success rows. M67 scales this bridge to the M38/M45 195-row denominator. M75 full aggregate has target detected 144 / 195, H001 157 / 195, context-agnostic 156 / 195, `ConceptGraphs` same-batch 114 / 195, detector task-budget 24 / 195, and detector top5 51 / 195. M76 marks the table diagnostic-ready. M77/M78 show offline repair potential from pre-cap pools, with fixed replay top5 60 / 195. M80-M82 reproduce the b02 ranking gain in the runner path: detector top5 9 / 69 -> 15 / 69. M83 stops immediate b01/b03 reruns because remaining expected gains are too small. M84-M90 diagnose recall misses: prompt repair is not ready, strict pre-cap suppressed target count is 0, selected 1.5m-threshold recovery is only 2 targets / 6 rows, and the largest unresolved exposure is the `569d8f0f` zero-written cluster at 5 targets / 15 rows. M90 selects active-label precedence as a leakage-safe repair route and rejects `stool` scan-scope expansion. M91 validates the selected repair on one scan: pre-cap/final 0 / 0 -> 479 / 24 and matched target rows 5 / 5. M93 validates the repair at b02 batch level: target detected 42 / 69 -> 57 / 69 and detector top5 15 / 69 -> 18 / 69, with no side-effect loss. M94 projects b02-replaced aggregate target detected 159 / 195 and detector top5 60 / 195. M95 fixes the paper-facing boundary and keeps this as diagnostic evidence. M96/M97 select external proposal/mapping feasibility and `ConceptGraphs` reliability smoke. M98 shows H001 recovers 54 rows where both map strict top5 and real detector top5 fail, but `ConceptGraphs` succeeds on 24 H001-failure rows. | No. M98 is a diagnostic row-group analysis from existing artifacts. Final robustness remains blocked until the 24 map-success/H001-failure rows and heavier external-route need are resolved. |
| Does this prove real navigation `SR` / `SPL`? | E002/E005 provide `ExpectedSearchCost` and `AttemptSPL` proxy. E007-M07 packages an occupancy-grid path-cost proxy table. E008-M13 verifies a tiny local `HM3D ObjectNav` + `Habitat` route, H001 candidate schema, oracle path plumbing, rendered RGB-D detector-source plan, 24/24 detector-compatible rendered RGB-D/pose rows, 137 detector coordinate candidates, navmesh snapping/path availability for 125/137 candidates, 512 visit-order rows, leakage-safe `GoalEvalProxy` rows, and detector-goal failure audit across 6 scans. | No. `SR` / `SPL` still requires non-oracle observation coverage expansion, H001 candidate-source execution, simulator execution, and trajectory metrics. |
| Is human intent a main contribution? | Structured `task_context_id` is included in H001 memory trust / re-observation policies, and E005-M65 records human intent reflected as structured task context. | H001 beats context-agnostic memory trust by only 1 success row, so do not claim natural-language intent understanding or main human-intent contribution yet. |
| Are failed baselines being hidden? | `DualMap` executed but produced no object `*.pkl`; E003-M45 and E003-M50 negative support/mask routes are documented. | Use them as failure-boundary evidence, not as performance baselines. |

논문 주장:

- The paper-facing claim should be narrow: H001 improves stale semantic memory decisions for dynamic object search on a fixed proxy-search denominator, with `ConceptGraphs` as the current converted external map baseline.
- `Open3DSG` should be described as a second external scene-graph route whose primary-label adapter is weak but whose leakage-safe predicted-vocabulary adapter is a bounded positive baseline candidate.
- The paper should state that real RGB-D/open-vocabulary robustness and real navigation `SR` / `SPL` are planned expansion claims, not current evidence.

에이전트 추론:

- The strongest reviewer defense is not to overclaim. Current results are credible if framed as a semantic memory decision layer with strict leakage control and explicit denominator boundaries.
- The largest remaining risk is not lack of implementation effort; it is claim mismatch. If the paper claims navigation, robust open-vocabulary perception, or human-intent understanding before the required evidence exists, reviewers will correctly reject the claim.
- M60/M62/M63/M64/M65/M66 are useful because they pre-commit and then apply the `Open3DSG` join/metric/leakage rules on denominator-aligned rows, isolate vocabulary-adapter mismatch, verify the repair without using target labels or target geometry before ranking, and state row-level failure boundaries. M67/M68 are useful because they prevent overclaiming from proxy rows by forcing the next step to execute the real RGB-D proposal bridge on the M38/M45 denominator. M83 is useful because it prevents spending more compute on detector reruns whose expected paper-facing gain is too small. M84 is useful because it moves the next question from ranking repair to target-detection recall diagnosis. M85 is useful because it prevents a naive prompt-only repair claim by showing that recall misses mix prompt/broad-label, localization/matcher, and detector/no-candidate causes.

## Final Paper Direction A

논문 주장:

Direction A is a focused semantic memory decision paper.

Working title:

- `Task-Conditioned Stale Semantic Memory for Dynamic Object Search`

Core claim:

- A robot should not treat semantic memory as static object storage; it should update memory trust and search order based on task context, staleness, motion evidence, path/search cost, and proposal uncertainty.

Main contributions:

- Stale semantic memory decision formulation.
- Dynamic-pair object search benchmark from `3RScan` / `3DSSG`.
- Task-conditioned search policy with memory trust and re-observation/search budget.
- Controlled and real-proposal noise evaluation.
- Failure-boundary analysis for stale old-location errors, target dropout, false-positive pushdown, centroid localization error, and proposal bridge mismatch.

Required evidence:

- E001/E002 main table with static memory, fixed top-k, task-conditioned, reachable-first, detector-confidence-first, and oracle.
- E003 controlled noise table.
- E003-M75 direct current-rescan detector/query evaluation table.
- Ablation table for task context, staleness, path/search cost, and proposal filtering.
- At least one external proposal or mapping baseline if claiming real RGB-D/open-vocabulary robustness.

에이전트 추론:

- This direction is coherent and feasible.
- It is more likely to be accepted if framed for robotics / embodied AI venues where task-conditioned memory and dynamic search are central.
- It is less likely to satisfy top-tier CV/ML reviewers if the method remains mostly rule-based and the benchmark remains small or self-defined.

## Final Paper Direction B

논문 주장:

Direction B is a broader mapping-navigation system paper.

Working title:

- `Task-Aware Dynamic Semantic Mapping for Open-Vocabulary Search and Navigation`

Core claim:

- A task-aware semantic mapping system can maintain stale/dynamic object memory, fuse open-vocabulary RGB-D proposals, decide when to trust or re-observe memory, and improve embodied search/navigation under dynamic changes.

Main contributions:

- Dynamic semantic memory representation with stale/current evidence.
- Open-vocabulary proposal integration using `GroundingDINO` plus at least one of `OpenMask3D`, `ConceptGraphs`, or `HOV-SG`.
- Search/navigation policy using memory trust, re-observation, and path cost.
- Evaluation on `3RScan` / `3DSSG` plus a simulator or navigation benchmark such as `HM3D-OVON` or `GOAT-Bench` if real `SR` / `SPL` is claimed.
- Comparisons to open-vocabulary mapping, dynamic semantic mapping, scene memory, and navigation/search baselines.

Required evidence:

- Everything in Direction A.
- External baselines: at least one open-vocabulary mapping baseline, one dynamic mapping baseline, one search/navigation baseline, and one scene memory baseline.
- Real or simulator-backed navigation metrics: `SR`, `SPL`, `ExpectedSearchCost`, stale old-location dead-end cost.
- Heldout transfer across scans/scenes and label groups.
- Runtime/reproducibility report for Dockerized detector and mapping pipelines.

에이전트 추론:

- This direction has higher top-tier potential because it connects representation, perception, memory update, and embodied downstream behavior.
- It also has much higher implementation risk because failures can come from detector quality, mapping baseline compatibility, simulator integration, path planning, and benchmark mismatch.
- Direction B is the final target. Direction A should remain the core method/backbone while the system expands through real proposal/search bridge evidence, external baselines, and navigation/search metrics.

## Top-Tier Potential

에이전트 추론:

- Current state as-is: top-tier full-paper probability is low. The core idea is promising, but evidence is still too proxy-heavy, external baselines are missing, and real RGB-D/open-vocabulary results are diagnostic.
- Direction A after E003-M58, scale-up, ablations, and one external proposal/mapping baseline: low-to-moderate top-tier chance. It can be competitive if the story is sharp and the benchmark is defensible, but it may still be attacked as narrow or heuristic.
- Direction B after successful external baselines and real/simulator navigation evaluation: materially higher top-tier chance. It is the stronger target for `CoRL`, `ICRA`, `IROS`, and possibly CV/AI venues if the perception/mapping component is strong.

Estimated relative lift:

- Direction A is the safer paper path.
- Direction B can plausibly be 1.5x to 2.5x stronger for top-tier review if the full system evidence is clean.
- Direction B can also be 2x to 4x more engineering-heavy and has higher failure risk.

Cold assessment:

- Focused Direction A can become a solid paper, but top-tier acceptance will depend on whether the method is formalized beyond heuristic ranking and whether E003-M58 closes the real-proposal/search causality gap.
- Broader Direction B is the right long-term top-tier direction, but only if it does not dilute the main contribution. The broader paper must show that stale semantic memory decisions improve downstream embodied search/navigation beyond strong mapping and navigation baselines.

## Claim Expansion Requirements

사실:

- E003-M75 is the current strongest real RGB-D/open-vocabulary bridge artifact.
- E003-M75 target detection is 87 / 96 query rows, but `detector_task_budget_v0` success is 13 / 96.
- E003-M75 bounded repair success is 33 / 96, but it increases mean `ExpectedSearchCost` from 2.645833 to 4.937500.
- E003-M75 unbounded upper bound reaches 87 / 96, with mean `ExpectedSearchCost` 9.750000.
- E004-M01 confirms that the E004 transition is ready with constraints, but current task-context-specific effect readiness is false.
- E004-M02 fixes leakage boundaries by blocking target uid, target rank, target match distance, false positives before target, success labels, and evaluation-only dead-end labels from policy inputs.
- E004-M03 shows memory-trust evidence but also shows that task-context-specific gain is narrow: only `high_value_fetch` improves over context-agnostic memory trust.
- E004-M04 shows all-high-value budget can recover more rows than the task-context policy, so current task conditioning should be claimed as a controlled tradeoff, not an optimal policy.
- E004-M05 shows memory trust is split-supported under leave-one-scan and bootstrap stress, while task-context specificity remains positive but not label-broad.
- E005-M01 selects `DualMap` first because it is the closest external challenge to the current dynamic semantic memory claim.
- E005-M02 shows that a fair `DualMap` comparison requires Dataset Mode staging and object map schema inspection, not direct reuse of E004 JSONL rows.
- E005-M03 shows this staging route is practical on the selected 4 current-rescan scans, but the result is still a preflight artifact, not an external baseline result.
- E005-M04 removes the local file-layout blocker, but it also exposes the next reviewer-relevant risk: runtime dependency/model readiness and color/depth resolution alignment must be validated before using `DualMap` as evidence.
- E005-M05 confirms that the remaining `DualMap` blocker is environment/bootstrap, not selected scan file layout. Static object schema is adapter-promising, but runtime map outputs are still required.
- E005-M06 launches the environment/bootstrap route and confirms local `mobileclip` readiness; E005-M07 verifies Docker image and dependency readiness; E005-M08 launches one-scan runtime smoke; E005-M09 verifies failure at `CLIP` model initialization due to GPU memory contention; E005-M10 selects detector-enabled free-GPU retry; E005-M11 launches that retry; E005-M12/M13/M14/M15 repair the cache path and verify cache-fixed runtime completion; E005-M16/M17/M18 show that denser stride still yields no object `*.pkl`.
- E005-M35 converts the 4-scan `ConceptGraphs` subset into query-level metrics; E005-M38 defines the 13-scan / 291-query scale contract; E005-M49 aggregates all 9 heldout `ConceptGraphs` scans; E005-M52/M53/M54 replay H001 and fix the paper-facing claim boundary.
- E005-M91 shows that one major zero-written real-proposal failure mode can be repaired without target-aware leakage on one scan.
- E005-M92 shows this repair is worth a bounded batch rerun, but not because it strengthens H001 yet; it mainly recovers target detection and exposes a side-effect test.
- E005-M93/M94/M95 show the bounded batch rerun recovers target detection without observed side-effect loss, but still does not strengthen H001 success or detector task-budget success.
- E005-M96 selects external proposal/mapping baseline feasibility as the next route and defers navigation/search execution.
- E005-M97 selects the `ConceptGraphs`-derived map candidate route as the first low-burden external reliability smoke and defers `OpenMask3D` / `HOV-SG`.
- E005-M98 confirms `ConceptGraphs` is a strong reliability diagnostic but also exposes 24 map-success/H001-failure rows that must be inspected.
- E005-M99 inspects M98 row groups at target level: H001 failure 38 rows / 13 targets, `ConceptGraphs` map-assisted repair candidate 24 rows / 8 targets, H001-or-`ConceptGraphs` upper bound 181 / 195, H001-or-`ConceptGraphs`-or-real-top5 upper bound 183 / 195.
- E005-M99 selects `map_assisted_h001_repair_first` and defers heavier `OpenMask3D` / `HOV-SG` routes until after map-assisted fallback cost accounting.
- E005-M100 pays that fallback cost explicitly and still improves `AttemptSPL` proxy, so the map-assisted H001 fallback is stronger than a raw union upper bound.
- E005-M101 selects navigation/path-cost bridging as the next top-tier expansion, while keeping `OpenMask3D` / `HOV-SG` as later baseline pressure routes.
- E007-M02 confirms that the 195-row M100 denominator can enter route materialization without row drift.
- E007-M03 removes the external candidate grid-projection blocker, but 216 / 1,170 query-policy rows remain source-limited and must be reported separately in path-cost metrics.
- E007-M04 shows that the map-assisted fallback remains stronger than static memory, detector-confidence ranking, and `ConceptGraphs`-only under paired source-ready path metrics. Against H001-only, the gain is small and cost rises, so the correct claim is repair tradeoff rather than unconditional dominance.
- E007-M05 fixes the table boundary: report full denominator, source-ready subset, source-limited rate, and proxy `PathAttemptSPLProxy` together; do not present this as real navigation `SR` / `SPL`.
- E007-M05 blocks `OldLocationDeadEndCostM` as a primary metric until a robot/start-pose or executed search source exists.
- E007-M06 confirms that the bridge table is not dominated by stop-rank rows or source-ready filtering, but it also confirms old-memory path-start bias: 153 old-first non-target route rows have zero first-step cost.
- E007-M07 packages the final proxy table and claim ledger: allowed claims are limited to occupancy-grid path-cost proxy evidence and map-assisted repair tradeoff; blocked claims remain real navigation `SR` / `SPL`, `OldLocationDeadEndCostM` primary metric, and final real RGB-D/open-vocabulary robustness.
- E008-M12 confirms that leakage-safe goal evaluation is possible, but it also exposes limited target coverage: all current detector policies hit 3/6 under `any_viewpoint_xz_1p0`, while object-center `goal_xz_1p0` succeeds on only 1/6.
- E008-M13 shows the immediate bottleneck is observation/candidate coverage rather than visit-order ranking: all three failed episodes fail across all four policies, two are already target-region misses in the pre-cap detector pool, and one is a near-miss around the localization threshold.
- Current real navigation `SR` / `SPL` remains unsupported because no H001 candidate-source execution rows or trajectory execution metrics have been produced yet.

논문 주장:

- Final real RGB-D/open-vocabulary robustness claim requires heldout scan/label splits, a visibility-aware denominator, prompt/label generalization, detector/proposal baselines, and stress tests under RGB-D/perception noise.
- Deployable search policy claim requires a fixed allowed-input contract, bounded-budget improvement over task-agnostic top-k and confidence baselines, task-context ablations, and failure analysis separating detector recall miss from rank/cost failures.
- Real navigation `SR` / `SPL` claim requires simulator/navmesh/trajectory execution, episode definitions, path execution metrics, and navigation/search baselines such as `VLFM`, `HM3D-OVON`, or `GOAT-Bench` modular baselines.

에이전트 추론:

- Real RGB-D/open-vocabulary robustness is not just higher detector recall. It must show transfer across heldout scenes/labels and robustness to prompt, depth, pose, and proposal noise.
- Deployable search policy is currently the nearest claim to mature, but E004-M05 still supports only a diagnostic memory-trust decision claim, not a final deployable policy claim.
- Real navigation `SR` / `SPL` is the farthest claim because `GoalEvalProxy` success must be connected to actual simulator trajectory execution.
- The correct immediate route is E008-M14: design non-oracle observation coverage expansion before any full simulator benchmark or H001 execution table.

사용자 판단 필요:

- Decide later whether final submission should stop at deployable search policy with real RGB-D/open-vocabulary diagnostics, or continue to full navigation `SR` / `SPL`.

## Recommended Path

에이전트 추론:

- Use Direction A as the backbone now.
- Treat Direction B as the final target, not a separate replacement.
- The next technical step should be E008-M14 non-oracle observation-coverage expansion plan.
- M93 should preserve the current claim boundary: it tests net target-detection recovery and `chair`/`stool` side effects, not final real RGB-D/open-vocabulary robustness.
- E005 should preserve the E004 claim boundary: split-supported memory trust, limited task-context specificity, no final real RGB-D/open-vocabulary robustness, no deployable search policy, and no real navigation `SR` / `SPL`.
- External proposal/mapping baselines such as `OpenMask3D`, `ConceptGraphs`, and `HOV-SG` should be evaluated as claim-expansion routes, not retrofitted as detector improvements.
- Do not claim real navigation `SR` / `SPL` until simulator, navmesh, or trajectory execution is integrated.

사용자 판단 필요:

- The final target is fixed as Direction B.
- A smaller intermediate submission remains possible if Direction A becomes independently strong before the broader mapping-navigation evidence is complete.
