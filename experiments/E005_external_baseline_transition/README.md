# E005 External Baseline Transition

Updated: 2026-05-21

## Status

`E005-M01` through `E005-M58` are complete through 4-scan scale decision, pending-scan runtime verification, staging/permission repair, 4-scan candidate/query metric conversion, failure/claim-boundary analysis, external baseline next-route decision, heldout/scale contract planning, heldout sequence acquisition/staging launch, heldout sequence staging verification, heldout runtime preflight, heldout staged-layout materialization, all `heldout_b01/b02/b03` runtime completion verification, all heldout query-metric conversion, full 9-scan heldout aggregation, H001-vs-`ConceptGraphs` comparison readiness gate, H001 heldout replay contract, H001 heldout policy replay, paired failure analysis / paper-table decision, paper-table claim ledger / method claim rewrite, real RGB-D/open-vocabulary robustness expansion gate, robustness denominator + `Open3DSG` source/interface audit, `Open3DSG` output schema / query-conversion contract, and `Open3DSG` object-candidate export smoke plan. E005-M59 `Open3DSG` object-candidate export smoke launched but failed on CUDA OOM during `InstructBLIP` checkpoint loading. The selected repair route is a lower-memory object-only export patch, not a blind GPU-exclusive relaunch. The selected first external baseline route was `DualMap`; the backup route is `ConceptGraphs`. `DualMap` Dataset Mode staging, Docker bootstrap, cache-fixed detector initialization, and one-scan runtime completion are verified, but M14/M17 produce `layout.pcd` / timing files without object `*.pkl` outputs. `ConceptGraphs` is now the active external mapping baseline route. Full heldout strict bbox top5 is 114 / 195 = 0.584615, relaxed bbox 1m top3 is 144 / 195 = 0.738462, and centroid strict top5 is 75 / 195 = 0.384615. E005-M52 replays H001 on the same `M38` query contract: H001 `task_context_memory_trust_reobserve_v0` is 172 / 195 = 0.882051, `static_memory_only_v0` is 141 / 195 = 0.723077, and `context_agnostic_memory_trust_reobserve_v0` is 171 / 195 = 0.876923. E005-M56 fixes the two-table robustness denominator and audits `/home/yoohyun/research/local_dataset/Open3DSG_staged` read-only. E005-M57 stores derived schema/contract results under `/home/yoohyun/research2/local_dataset/Open3DSG_bridge/`; relation raw dump and feature/checkpoint route are feasible. E005-M58 stores the object-candidate export schema, read-only Docker command contract, and verifier under the same bridge root. E005-M59 used local runtime patching under `research2`, kept `Open3DSG_staged` mounted read-only, and targeted `/home/yoohyun/research2/local_dataset/Open3DSG_bridge/E005-M59_object_candidate_export_smoke_v0/`. As of 2026-05-21 04:59 KST, lower-memory patch is implemented, source modified is false, no candidate rows have been written, and relaunch is waiting for GPU free memory >= 24GB. Keep `OpenMask3D` as a later proposal baseline because Docker/`MinkowskiEngine` remains blocked. Final real RGB-D/open-vocabulary robustness and real navigation `SR` / `SPL` remain blocked.

## E005-M59 Open3DSG Object Candidate Export Smoke

사실:

- Status: `e005_m59_open3dsg_object_export_smoke_failed`.
- tmux session: `e005_m59_open3dsg_object_export`.
- Log: `logs/20260521_044206_e005_m59_open3dsg_object_export.log`.
- Output: `local_dataset/Open3DSG_bridge/E005-M59_object_candidate_export_smoke_v0/`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M59_object_candidate_export_smoke_v0/`.
- Verification command: `python experiments/E005_external_baseline_transition/tools/verify_m59_open3dsg_object_export_smoke.py --require-ready`.
- Last check: 2026-05-21 04:54 KST; tmux running false, source modified false, candidate row file missing.
- Failure reason: CUDA OOM while loading `InstructBLIP`; log reports GPU 0 had 93 MiB free at failure and the Open3DSG process used about 16.35 GiB.
- Repair decision: prefer lower-memory object-only export patch over blind GPU-exclusive relaunch.
- Repair patch: `OPEN3DSG_OBJECT_DUMP_SKIP_BLIP_LOAD=1` skips pretrained `InstructBLIP` loading; `OPEN3DSG_OBJECT_DUMP_OBJECT_ONLY=1` stubs relation prediction because object candidates do not require relation captioning.
- Relaunch preflight: default `--min-gpu-free-mib 24000`.
- Latest GPU check: 2026-05-21 04:59 KST, 16,839 MiB free, relaunch deferred.

논문 주장:

- This step does not yet establish `Open3DSG` query-level object-search performance.
- `Open3DSG` remains a second external map/scene-graph baseline candidate until object-candidate rows exist and query-level conversion passes.

에이전트 추론:

- The next dependent action is M59 relaunch when the GPU satisfies the 24GB preflight. If the lower-memory patch still fails, then use a GPU-exclusive relaunch as the second repair path.

## E005-M58 Open3DSG Object Candidate Export Plan

사실:

- Status: `e005_m58_open3dsg_object_candidate_export_plan_ready_hook_smoke_needed`.
- Verification: `e005_m58_open3dsg_object_candidate_plan_ready_no_rows_yet`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M58_object_candidate_export_plan_v0/`.
- Data output: `local_dataset/Open3DSG_bridge/E005-M58_object_candidate_export_plan_v0/`.
- Existing staged source modified: false.
- Selected checkpoint exists: true.
- Feature dir exists: true.
- Object candidate schema, query candidate schema, export hook contract, Docker command contract, and verifier are ready.
- One-batch smoke executed: false.
- Candidate rows exist: false.

논문 주장:

- This step does not establish `Open3DSG` query-level object-search performance.
- `Open3DSG` remains a second external map/scene-graph baseline candidate until one-batch object candidate export and query conversion pass.

에이전트 추론:

- The next unit should implement a local runtime patch under `research2`, run one-batch Docker smoke, and keep `/home/yoohyun/research/local_dataset/Open3DSG_staged` read-only.
- GT labels and `id2name` must remain eval-only diagnostics, not ranking inputs.

## E005-M57 Open3DSG Schema Contract

사실:

- Status: `e005_m57_open3dsg_output_schema_contract_ready_object_candidate_export_needed`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M57_open3dsg_output_schema_contract_v0/`.
- Data output: `local_dataset/Open3DSG_bridge/E005-M57_output_schema_contract_v0/`.
- Existing staged source modified: false.
- Preprocessed `data_dict_*.pkl`: 377.
- `object2image` `.pkl`: 127.
- Feature `.pt` files: 1131.
- MLflow checkpoints: 8.
- Relation raw dump ready: true.
- Object candidate dump ready: false.
- Query-level conversion ready without new export: false.

논문 주장:

- This step does not establish `Open3DSG` query-level object-search performance.
- `Open3DSG` can be pursued as a second external map/scene-graph baseline only after object candidate export and H001 query conversion are implemented.

에이전트 추론:

- Aggregate `Open3DSG` eval metrics are useful for source sanity, but not directly comparable to H001 search metrics.
- E005-M58 completed the object-candidate dump/export smoke plan; E005-M59 attempted one-batch export and now needs CUDA OOM repair.

## E005-M56 Robustness Denominator + Open3DSG Audit

사실:

- Status: `e005_m56_robustness_denominator_open3dsg_audit_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M56_robustness_denominator_open3dsg_audit_v0/`.
- Table A proxy-search external map denominator: 195 rows.
- Table B real RGB-D proposal bridge denominator: 96 rows.
- `Open3DSG_staged` path: `/home/yoohyun/research/local_dataset/Open3DSG_staged`.
- Existing staged data modified: false.
- Runtime `3RScan` entries/symlinks/broken symlinks: 133 / 127 / 0.
- Checkpoint files: 7; feature `.pt` files: 1131; `OpenSG_3RScan` view `.pkl` files: 127.
- Existing `Open3DSG` eval metrics are present.

논문 주장:

- This step supports source/interface feasibility for `Open3DSG` as a second external map/scene-graph route.
- This step does not support an `Open3DSG` query-level performance claim.
- Final real RGB-D/open-vocabulary robustness remains blocked until at least one more external route is converted and failure taxonomy is aligned.

에이전트 추론:

- `Open3DSG` can be used read-only for audit and later conversion without modifying the other research workspace data.
- The next unit should inspect output/eval schemas and define how `Open3DSG` object/relation predictions map to H001 query candidates.

## E005-M55 Robustness Gate

사실:

- Status: `e005_m55_real_rgbd_ov_robustness_gate_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M55_real_rgbd_ov_robustness_gate_v0/`.
- M54 proxy-search rows: 195.
- E003-M75 real proposal bridge rows: 96.
- E003-M75 target detected rows: 87.
- E003-M75 bounded repair success rows: 33.
- `OpenMask3D` blocked: true.
- Selected route: `robustness_denominator_contract_then_open3dsg_audit`.

논문 주장:

- This gate does not make final real RGB-D/open-vocabulary robustness ready.
- The next step should define a two-table robustness denominator and audit `Open3DSG` as a second external semantic mapping / 3D scene graph route.
- Real navigation `SR` / `SPL` remains later than robustness expansion.

에이전트 추론:

- `OpenMask3D` remains valuable for proposal-quality evidence, but it is not the immediate route because the current blocker is environment compatibility rather than research logic.
- `Open3DSG` is a better next audit target because it is closer to semantic mapping and scene graph evidence, and it can strengthen the claim beyond a single `ConceptGraphs` external map route.

## E005-M54 Claim Ledger

사실:

- Status: `e005_m54_paper_table_claim_ledger_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M54_paper_table_claim_ledger_v0/`.
- Main table rows: 8 policies.
- H001 success: 172 / 195 = 0.882051.
- `ConceptGraphs` success: 114 / 195 = 0.584615.
- Static memory success: 141 / 195 = 0.723077.
- Context-agnostic memory trust success: 171 / 195 = 0.876923.

논문 주장:

- Allowed main claim: H001 improves heldout proxy search over `ConceptGraphs`-only map retrieval and static stale memory.
- Allowed framing: H001 is a semantic memory decision layer for memory trust, staleness handling, and bounded re-observation.
- Blocked claim: human intent / task context is the main contribution.
- Blocked claim: final real RGB-D/open-vocabulary robustness.
- Blocked claim: real navigation `SR` / `SPL`.

에이전트 추론:

- The paper should not be framed as a human-intent understanding paper at this point.
- E005-M55 should decide the next real RGB-D/open-vocabulary robustness expansion route before adding navigation `SR` / `SPL`.

## E005-M53 Paper-Table Decision

사실:

- Status: `e005_m53_paired_failure_table_decision_ready_memory_trust_supported_task_context_limited`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M53_paired_failure_table_decision_v0/`.
- Query rows: 195.
- H001 success: 172 / 195 = 0.882051.
- `ConceptGraphs` strict bbox top5 success: 114 / 195 = 0.584615.
- Static memory success: 141 / 195 = 0.723077.
- Context-agnostic memory trust success: 171 / 195 = 0.876923.
- H001 vs `ConceptGraphs`: both success 112, H001-only 60, `ConceptGraphs`-only 2, both fail 21.
- H001 over `ConceptGraphs` gain source: 60 rows are static memory preservation.

논문 주장:

- The main proxy-search table is ready with a bounded claim: H001 improves heldout proxy search over `ConceptGraphs`-only open-vocabulary mapping and static memory.
- This result does not support human task context as the main contribution because the gain over context-agnostic memory trust is only 1 row.
- This result does not support final real navigation `SR` / `SPL` or final real RGB-D/open-vocabulary robustness.

에이전트 추론:

- The paper should frame the current contribution around memory trust, staleness handling, and bounded re-observation, not around natural-language or human-intent understanding.
- E005-M54 turned this result into a claim ledger and method-claim rewrite before adding another heavy baseline.

## E005-M26 Docker Image Result

사실:

- Status: `e005_m25_conceptgraphs_docker_build_ready`.
- Working directory: `/home/yoohyun/research2`.
- Exact command: `docker build --progress=plain -t research2/conceptgraphs-smoke:latest --build-arg CONCEPTGRAPHS_COMMIT=93277a02bd89171f8121e84203121cf7af9ebb5d --build-arg GSA_COMMIT=a4d76a2b55e348943cba4cd57d7553c354296223 -f /home/yoohyun/research2/experiments/E005_external_baseline_transition/docker/conceptgraphs_smoke/Dockerfile /home/yoohyun/research2/experiments/E005_external_baseline_transition/docker/conceptgraphs_smoke`.
- Background wrapper: `tmux new -d -s e005_m25_conceptgraphs_docker_build 'cd /home/yoohyun/research2 && /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M25_conceptgraphs_docker_build_preflight_v0/run_m25_conceptgraphs_docker_build.sh > /home/yoohyun/research2/logs/20260515_013221_e005_m25_conceptgraphs_docker_build.log 2>&1'`.
- Log: `logs/20260515_013221_e005_m25_conceptgraphs_docker_build.log`.
- Expected image: `research2/conceptgraphs-smoke:latest`.
- Expected smoke file: `experiments/E005_external_baseline_transition/docker/conceptgraphs_smoke/import_smoke.py`.
- Verification command: `python experiments/E005_external_baseline_transition/tools/verify_m25_conceptgraphs_docker_build.py`.
- Result: image `research2/conceptgraphs-smoke:latest`, import smoke `conceptgraphs_import_smoke_ok`.

논문 주장:

- This is not a performance claim.
- This gate only decides whether `ConceptGraphs` can become a reproducible external open-vocabulary mapping baseline route.

에이전트 추론:

- The repair is narrower than dropping `chamferdist`, because the official `ConceptGraphs` setup includes `chamferdist` and `gradslam`.
- The NumPy repair is an ABI compatibility pin: `faiss-cpu=1.7.4` imports against NumPy 1.x, while latest `opencv-python` packages pulled NumPy 2.x.
- RTX 5090 runtime compatibility is smoke-supported for the current one-scan `ConceptGraphs` route, but not yet a scaled baseline claim.

## E005-M27 Runtime Smoke Result

사실:

- Status: `e005_m27_conceptgraphs_runtime_smoke_outputs_ready`.
- Working directory: `/home/yoohyun/research2`.
- tmux session: `e005_m27_conceptgraphs_runtime_smoke` stopped after completion.
- Log: `logs/20260515_103016_e005_m27_conceptgraphs_runtime_smoke.log`.
- Smoke scan: `ddc73795-765b-241a-9c5d-b97744afe077`.
- GSA detections: 19 files under `local_dataset/ConceptGraphs_staged/3rscan_depth_aligned_scannet/ddc73795-765b-241a-9c5d-b97744afe077/gsa_detections_none/`.
- Full PCD exists: true.
- Full PCD post exists: true.
- Verification command: `python experiments/E005_external_baseline_transition/tools/verify_m27_conceptgraphs_runtime_smoke.py`.

에이전트 추론:

- Initial M27 failure was a container command issue, not a `ConceptGraphs` method failure.
- The second M27 failure was a script argument-contract issue: the parser default is `sam`, but explicit `--sam_variant sam` is rejected by the choices list.
- The third M27 failure was a resource issue: SAM failed while moving to CUDA because global GPU free memory was too low.
- Current runtime smoke still does not support a baseline performance claim until output-to-query export, semantic scoring, and query-level metric evaluation are complete.

## E005-M28/M29/M30/M31/M32/M33/M34/M35/M36/M37/M38/M39/M40/M41/M42/M43/M45/M46/M47/M48/M49 Current Conversion State

사실:

- E005-M28 status: `e005_m28_conceptgraphs_output_schema_ready`.
- GSA sample schema has `xyxy`, `confidence`, `class_id`, `mask`, `image_feats`, and `text_feats`.
- `full_pcd` has 146 raw objects; `full_pcd_post` has 6 post-processed objects.
- Post object fields include `pcd_np`, `bbox_np`, `clip_ft`, `text_ft`, `conf`, `n_points`, `image_idx`, `mask_idx`, and `xyxy`.
- E005-M29 status: `e005_m29_conceptgraphs_output_to_query_conversion_plan_ready_with_clip_text_gate`.
- E005-M30 status: `e005_m30_conceptgraphs_candidate_export_ready`.
- The smoke scan links to 1 E003-M60 query row with label `pillow`.
- M30 exports 6 object rows and 6 query-candidate rows.
- CLIP-text scoring is ready on CPU; CUDA text-model execution is not used because the current `PyTorch 2.0.1` / CUDA 11.8 image does not support RTX 5090 `sm_120` cleanly.
- E005-M31 status: `e005_m31_conceptgraphs_query_metric_strict_near_miss_ready`.
- Strict 0.5m center hit rows: 0.
- Strict 0.5m bbox hit rows: 0.
- Relaxed 1.0m bbox hit rows: 2; first relaxed hit is rank 3.
- Selected next route: `scale_conceptgraphs_with_geometry_threshold_boundary`.
- E005-M32 status: `e005_m32_conceptgraphs_scale_decision_approved`.
- E005-M33 initial status: `e005_m33_conceptgraphs_pending_scan_runtime_failed`.
- Initial M33 failure signal: `FileNotFoundError` for container path `/data/ConceptGraphs_staged/.../pose/000000.txt`.
- First repair relaunch failure signal: `PermissionError` creating `/data/ConceptGraphs_staged/.../gsa_vis_none`.
- E005-M34 status: `e005_m34_conceptgraphs_pending_scan_staging_repair_ready`.
- E005-M34 materialized pending-scan `depth/pose` symlinks into regular files: 1,466 files.
- E005-M34 permission repair latest run changed dirs/files: 15 / 2,205.
- Pending scan staging readiness after repair: 3 / 3.
- Container read smoke after repair: passed.
- Container write smoke after permission repair: passed.
- E005-M33 relaunch completion status: `e005_m33_conceptgraphs_pending_scan_runtime_outputs_ready`.
- Pending ready scans: 3 / 3.
- Pending GSA detections: 40 / 77 / 32.
- Pending full PCD and post PCD outputs: ready for all 3 scans.
- Output ownership: normalized to `yoohyun:yoohyun` where checked.
- E005-M35 status: `e005_m35_conceptgraphs_4scan_query_metric_ready_with_strict_hits`.
- E005-M35 object rows: 126.
- E005-M35 candidate rows: 3,308.
- Primary `M60` strict bbox top5 success: 3 / 7.
- Primary `M60` relaxed bbox 1m top3 success: 6 / 7.
- Expanded `M73` strict bbox top5 success: 57 / 96.
- Expanded `M73` relaxed bbox 1m top3 success: 60 / 96.
- E005-M36 status: `e005_m36_conceptgraphs_failure_boundary_ready`.
- Primary `M60` strict center top5 success: 1 / 7.
- Primary failure classes: `relaxed_top3_only_no_strict` 4, `strict_bbox_top5_success` 1, `strict_bbox_top5_success_centroid_miss` 2.
- Expanded failure classes: `no_relaxed_candidate` 12, `relaxed_candidate_rank_gt3_no_strict` 3, `relaxed_top3_only_no_strict` 12, `strict_bbox_top5_success` 42, `strict_bbox_top5_success_centroid_miss` 15, `strict_candidate_rank_gt5` 12.
- Label boundary: primary `chair` has no strict bbox top5 hit, primary `pillow` has 3 / 4 strict bbox top5 hits.
- E005-M37 status: `e005_m37_external_baseline_comparison_ready`.
- E005-M37 baseline rows: 6.
- E005-M37 selected next route: `conceptgraphs_scale_heldout_first`.
- E005-M37 next recommended unit: `E005-M38 ConceptGraphs heldout/scale expansion plan`.
- E005-M37 paper table claim ready: false.
- E005-M38 status: `e005_m38_conceptgraphs_heldout_scale_plan_ready`.
- E005-M38 target scale: `all_query_rescan_universe_13scan_v0`.
- E005-M38 eligible query rows: 291.
- E005-M38 excluded generic query rows: 3.
- E005-M38 dev existing split: 4 scans / 96 eligible query rows.
- E005-M38 heldout sequence-required split: 9 scans / 195 eligible query rows.
- E005-M38 heldout labels seen in dev: 6; not seen in dev: 17.
- E005-M38 missing `sequence.zip` scan count: 9.
- E005-M38 next recommended unit: `E005-M39 ConceptGraphs heldout sequence acquisition / staging launch`.
- E005-M39 status: `e005_m39_heldout_sequence_job_launched`.
- E005-M39 tmux session: `e005_m39_conceptgraphs_heldout_sequence`.
- E005-M39 log: `logs/20260515_174433_e005_m39_conceptgraphs_heldout_sequence.log`.
- E005-M39 target scans: 9.
- E005-M39 prelaunch sequence-ready scans: 0.
- E005-M39 download/decompression required scans: 9 / 9.
- E005-M39 output path: `experiments/E005_external_baseline_transition/artifacts/E005-M39_conceptgraphs_heldout_sequence_launch_v0/`.
- E005-M39 verification command: `python experiments/E003_perception_noise_expansion/tools/verify_m56_sequence_payloads.py --manifest experiments/E005_external_baseline_transition/artifacts/E005-M39_conceptgraphs_heldout_sequence_launch_v0/download_manifest.jsonl --out-dir experiments/E005_external_baseline_transition/artifacts/E005-M39_conceptgraphs_heldout_sequence_launch_v0/verification --require-ready`.
- E005-M39 next recommended unit: `E005-M40 ConceptGraphs heldout sequence staging completion verification`.
- E005-M40 status: `e005_m40_heldout_sequence_staging_ready`.
- E005-M40 ready scans: 9 / 9.
- E005-M40 valid `sequence.zip` rows: 9 / 9.
- E005-M40 total frame triplet lower bound: 2,982.
- E005-M40 minimum frame triplet lower bound: 111.
- E005-M40 heldout query rows after exclusion: 195.
- E005-M40 tmux session stopped: true.
- E005-M40 next recommended unit: `E005-M41 ConceptGraphs heldout runtime preflight / launch plan`.
- E005-M41 status: `e005_m41_heldout_runtime_preflight_ready_with_staging_required`.
- E005-M41 heldout scans: 9.
- E005-M41 M40 sequence-ready scans: 9 / 9.
- E005-M41 staged payload ready scans: 0 / 9.
- E005-M41 runtime output ready scans: 0 / 9.
- E005-M41 raw frame triplet lower bound total: 2,982.
- E005-M41 Docker image ready: true.
- E005-M41 model checkpoints ready: true.
- E005-M41 runtime launch ready now: false.
- E005-M41 next recommended unit: `E005-M42 ConceptGraphs heldout staging materialization`.
- E005-M42 status: `e005_m42_conceptgraphs_heldout_staging_materialized_ready`.
- E005-M42 ready scans: 9 / 9.
- E005-M42 color/depth/pose files: 2,982 / 2,982 / 2,982.
- E005-M42 resolution-aligned scans: 9 / 9.
- E005-M42 errors: 0.
- E005-M42 runtime launched: false.
- E005-M42 container read/write smoke: passed.
- E005-M42 next recommended unit: `E005-M43 ConceptGraphs heldout runtime batch launch`.
- E005-M43 status: `e005_m43_conceptgraphs_heldout_runtime_batch_launched`.
- E005-M43 batch id: `heldout_b01`.
- E005-M43 selected scans: 3.
- E005-M43 staged payload readiness: 3 / 3 selected scans.
- E005-M43 GPU free memory before launch: 25,817 MiB.
- E005-M43 GPU memory gate: 24,000 MiB.
- E005-M43 launch executed: true.
- E005-M43 tmux running after launch: false after completion verification.
- E005-M43 tmux session: `e005_m43_conceptgraphs_heldout_runtime_b01`.
- E005-M44 verification status: `e005_m43_conceptgraphs_heldout_runtime_batch_outputs_ready`.
- E005-M44 ready scans: 3 / 3.
- E005-M44 GSA detections: 70 / 58 / 23.
- E005-M44 next recommended unit: `E005-M45 heldout ConceptGraphs output-to-query metric conversion`.
- M33 completion log: `logs/20260515_131945_e005_m33_conceptgraphs_pending_scans.log`.
- M33 verification command: `python experiments/E005_external_baseline_transition/tools/verify_m33_conceptgraphs_pending_scans.py`.
- M43 launch command: `python experiments/E005_external_baseline_transition/tools/launch_m43_conceptgraphs_heldout_runtime_batch.py`.
- M43 working directory: `/home/yoohyun/research2`.
- M43 artifact path: `experiments/E005_external_baseline_transition/artifacts/E005-M43_conceptgraphs_heldout_runtime_batch_launch_v0/`.
- M43 log path: `logs/20260518_011510_e005_m43_conceptgraphs_heldout_runtime_heldout_b01.log`.
- M43 expected runtime outputs per selected scan: `gsa_detections_none/`, `pcd_saves/full_pcd_none_overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub.pkl.gz`, and `pcd_saves/full_pcd_none_overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub_post.pkl.gz`.
- M43 verification command: `python experiments/E005_external_baseline_transition/tools/verify_m43_conceptgraphs_heldout_runtime_batch.py --batch-id heldout_b01`.
- E005-M45 contract status: `e005_m45_conceptgraphs_heldout_metric_contract_ready_waiting_m44`.
- E005-M45 query-metric status: `e005_m45_conceptgraphs_heldout_query_metric_ready_with_strict_hits`.
- E005-M45 selected batch: `heldout_b01`.
- E005-M45 selected scans/query rows/target uids/labels: 3 / 66 / 22 / 8.
- E005-M45 heldout-all query rows: 195.
- E005-M45 object rows / candidate rows: 70 / 1,608.
- E005-M45 strict bbox top5 success rows/rate: 45 / 0.681818.
- E005-M45 relaxed bbox 1m top3 success rows/rate: 57 / 0.863636.
- E005-M45 strict centroid top5 success rows/rate: 27 / 0.409091.
- E005-M45 metric contract reuses M35 `object_rows`, `candidate_rows`, `candidate_eval_rows`, `policy_rows`, and `metrics` schemas.
- E005-M45 primary policy for paper-facing strict result: `conceptgraphs_clip_rank_bbox_strict_top5_v0`.
- E005-M45 diagnostics remain separate: centroid strict, relaxed bbox 1m top3/top5, and strict bbox unbounded.
- E005-M45 contract artifact path: `experiments/E005_external_baseline_transition/artifacts/E005-M45_conceptgraphs_heldout_metric_contract_v0/`.
- E005-M45 query metric artifact path: `experiments/E005_external_baseline_transition/artifacts/E005-M45_conceptgraphs_heldout_query_metric_v0/`.
- E005-M46 status: `e005_m46_conceptgraphs_heldout_interpretation_ready`.
- E005-M46 completed heldout batches: 1.
- E005-M46 remaining heldout batches: `heldout_b02`, `heldout_b03`.
- E005-M46 selected route: `run_remaining_heldout_batches_before_external_baseline_claim`.
- E005-M46 top-tier novelty contract compares `static_stale_memory`, `detector_confidence_ranking`, `ConceptGraphs-only open-vocabulary map`, `task-agnostic re-observation`, and H001 `task-conditioned memory trust / re-observation / search-cost policy`.
- E005-M46 next recommended unit: `E005-M47 launch remaining ConceptGraphs heldout runtime batch`.
- E005-M47 status: `e005_m43_conceptgraphs_heldout_runtime_batch_launched`.
- E005-M47 launched batch: `heldout_b02`.
- E005-M47 scans: `38770ca3-86d7-27b8-85a7-7d840ffdec6a`, `569d8f0f-72aa-2f24-89a6-77f8b8779ae9`, `74ef846e-9dce-2d66-83d5-294aac7b1b0f`.
- E005-M47 tmux session: `e005_m43_conceptgraphs_heldout_runtime_b02`.
- E005-M47 log: `logs/20260518_084811_e005_m43_conceptgraphs_heldout_runtime_heldout_b02.log`.
- E005-M47 initial verifier status: `e005_m43_conceptgraphs_heldout_runtime_batch_running`.
- E005-M47 next recommended unit: `E005-M48 heldout_b02 runtime completion verification`.
- E005-M48 verification status: `e005_m43_conceptgraphs_heldout_runtime_batch_outputs_ready`.
- E005-M48 ready scans: 3 / 3.
- E005-M48 `heldout_b02` GSA detections: 210 / 63 / 33.
- E005-M48 full PCD and post PCD outputs: ready for all 3 selected scans.
- E005-M49 batch-aware contract generated `heldout_b01/b02/b03_query_rows.jsonl`.
- E005-M49 heldout query row split: `heldout_b01` 66, `heldout_b02` 69, `heldout_b03` 60, total 195.
- E005-M49 `heldout_b02` query-metric status: `e005_m45_conceptgraphs_heldout_query_metric_ready_with_strict_hits`.
- E005-M49 `heldout_b02` object rows / candidate rows: 199 / 4,614.
- E005-M49 `heldout_b02` strict bbox top5 success rows/rate: 45 / 0.652174.
- E005-M49 `heldout_b02` relaxed bbox 1m top3 success rows/rate: 51 / 0.739130.
- E005-M49 next gate: launch `heldout_b03` when GPU free memory is >= 24GB.

논문 주장:

- E005-M35 supports a 4-scan staged `ConceptGraphs` query-level baseline conversion result.
- E005-M36 supports a bounded claim: `ConceptGraphs` can be evaluated as a query-level external map baseline on a 4-scan staged subset, with strict bbox hits on part of the primary set.
- E005-M36 does not support a final `ConceptGraphs` baseline claim because it is still a small staged subset with depth-aligned adapter constraints and label/scan-specific failure modes.
- E005-M37 supports a route decision: `ConceptGraphs` is the first external mapping baseline to scale, while `Open3DSG` is the next reasonable second external map/scene-graph route after scale.
- E005-M37 does not support a final paper table claim yet.
- E005-M38 supports a heldout/scale contract for `ConceptGraphs`.
- E005-M38 does not support heldout runtime performance or final paper table claim yet.
- E005-M39 supports only the launch of heldout data acquisition/staging.
- E005-M39 does not support heldout runtime performance, final external baseline performance, final real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.
- E005-M40 supports heldout sequence staging readiness for `ConceptGraphs` runtime planning.
- E005-M40 does not support heldout runtime performance, final external baseline performance, final real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.
- E005-M41 supports a heldout runtime preflight decision: runtime launch should wait until heldout staged-layout materialization is complete.
- E005-M41 does not support heldout runtime performance, final external baseline performance, final real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.
- E005-M42 supports heldout staged-layout readiness for `ConceptGraphs` runtime.
- E005-M42 does not support heldout runtime performance, final external baseline performance, final real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.
- E005-M43 supports only a runtime launch decision.
- E005-M44 supports heldout batch runtime-output readiness for 3 selected scans.
- E005-M45 supports a 3-scan heldout batch diagnostic for `ConceptGraphs` query-level external mapping baseline conversion.
- E005-M45 does not support final external baseline performance, all-9-scan heldout transfer, final real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.
- E005-M46 supports the decision to run remaining heldout batches before external-baseline claim.
- E005-M46 does not support novelty by itself; novelty must come from H001 improving `ExpectedSearchCost`, proxy `SR`, proxy `SPL`, stale-memory recovery, and failure reduction over the fixed comparison rows.
- E005-M47 supports only a runtime launch decision for `heldout_b02`.
- E005-M48 supports runtime-output readiness for `heldout_b02`.
- E005-M49 supports `heldout_b02` batch diagnostic metric conversion.
- E005-M49 does not support final external baseline performance, all-9-scan heldout transfer, final real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.

에이전트 추론:

- Geometry candidate export is ready because `pcd_np` and `bbox_np` are present.
- Open-vocabulary ranking is not ready from class names because this run uses `class_set none`; M30 verifies CLIP-text scoring against `clip_ft`.
- M31 shows a useful near-miss: strict 0.5m recovery fails, but relaxed 1.0m bbox distance finds a rank-3 candidate. Scaling is reasonable only if this boundary is preserved.
- Initial M33 failures were container-visible staging and write-permission adapter failures, not evidence that `ConceptGraphs` object-map output is impossible.
- M35 changes the `ConceptGraphs` route from feasibility-only to small-subset query-level evidence.
- M36 shows that bbox success is materially stronger than centroid success, so object extent alignment is carrying part of the result.
- M36 also shows that relaxed success is much higher than strict success on primary `M60`; map-object coverage exists, but strict localization/ranking remains the key weakness.
- M37 chooses `ConceptGraphs` scale/heldout before another heavy baseline launch because the current reviewer bottleneck is external-baseline rigor, not baseline count alone.
- `OpenMask3D` remains useful for proposal quality, but it should not block the map-level comparison path before `ConceptGraphs` is scaled.
- M38 shows that the blocker is no longer query schema: it is 9 heldout scan `sequence.zip` acquisition/staging plus later `ConceptGraphs` runtime.
- The 9 heldout scans include many labels not seen in the 4-scan dev result, so the split can expose label-transfer weakness instead of hiding it.
- M39 completed as a background I/O task and M40 verified the staged sequence payloads.
- M40 moves the blocker from data acquisition to heldout `ConceptGraphs` runtime planning and metric conversion.
- M41 moves the immediate blocker from runtime planning to heldout staged-layout materialization.
- M42 moves the immediate blocker from staged-layout materialization to heldout runtime execution.
- M43/M44 show the immediate blocker has moved from runtime output generation to heldout-result interpretation and remaining-batch scale.
- M45 confirms that bbox-based object extent alignment is much stronger than centroid-only localization on `heldout_b01`.
- `heldout_b01` can only be a batch diagnostic because it covers 66 / 195 heldout query rows.
- M46 makes the next direction explicit: finish `ConceptGraphs` heldout for baseline rigor, then compare H001 against the fixed naive/external/ablation baselines.
- `heldout_b03` should not be launched below the 24GB GPU-free gate unless the user explicitly accepts higher OOM risk.

## Source

- Workflow rule: `docs/experiments.md`
- Source hypothesis: `hypothesis/CAND-001/H001_stale-object-memory/`
- E004 source: `experiments/E004_task_context_memory_trust/`
- Immediate input artifact: `experiments/E004_task_context_memory_trust/artifacts/E004-M05_scale_split_stress_v0/`

## Contract

사실:

- E004-M05 memory-trust decision claim strength is `split_supported`.
- E004-M05 task-context-specific claim strength is `limited_positive_not_label_broad`.
- E004-M05 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.
- E003-M72 records the local `OpenMask3D` Docker/MinkowskiEngine blocker.

논문 주장:

- E005 is not a new method-result stage yet.
- E005 selects external baseline routes needed to defend the E004 memory-trust decision claim.
- E005 must keep the E004 claim boundary fixed until external baselines and heldout/navigation evidence are added.

에이전트 추론:

- The first baseline should be closest to the current claim, not merely easiest to run.
- `DualMap` is the best first route because it directly targets online open-vocabulary semantic mapping in dynamic changing scenes.
- `ConceptGraphs` is the best fallback route because it is a strong open-vocabulary graph mapping baseline over posed RGB-D observations.
- `OpenMask3D` remains important, but it should not be the immediate E005 blocker because the local environment route already failed at `MinkowskiEngine`.

사용자 판단 필요:

- None before E005-M37 external baseline comparison table / next-route decision.

## E005-M30 ConceptGraphs Candidate Export

Implementation unit: `E005-M30_conceptgraphs_candidate_export_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/run_m30_conceptgraphs_candidate_export.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/run_m30_conceptgraphs_candidate_export.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M30_conceptgraphs_candidate_export_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M30_conceptgraphs_candidate_export_v0/object_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M30_conceptgraphs_candidate_export_v0/candidate_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M30_conceptgraphs_candidate_export_v0/docker_meta.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M30_conceptgraphs_candidate_export_v0/report.md`

사실:

- Status: `e005_m30_conceptgraphs_candidate_export_ready`.
- Scan: `ddc73795-765b-241a-9c5d-b97744afe077`.
- Device: `cpu` for CLIP-text encoding.
- Object rows: 6.
- Candidate rows: 6.
- Linked query rows: 1.
- Linked label: `pillow`.
- Top semantic score: 0.238026.
- Query-level baseline result ready: false.

논문 주장:

- E005-M30 supports one-scan candidate export and open-vocabulary semantic scoring feasibility for the `ConceptGraphs` route.
- E005-M30 does not support a `ConceptGraphs` baseline metric claim because target matching and query-level metrics are deferred to M31.

에이전트 추론:

- CPU CLIP-text scoring is the correct smoke route on the current image because moving `ViT-H-14` to CUDA can hang under RTX 5090 / `sm_120` with the official `PyTorch 2.0.1` / CUDA 11.8 stack.
- The candidate rows preserve policy/eval separation: target identity and match distance remain absent before M31.

사용자 판단 필요:

- Resolved by E005-M31.

## E005-M31 ConceptGraphs Query Metric

Implementation unit: `E005-M31_conceptgraphs_query_metric_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/evaluate_m31_conceptgraphs_query_metrics.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/evaluate_m31_conceptgraphs_query_metrics.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M31_conceptgraphs_query_metric_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M31_conceptgraphs_query_metric_v0/candidate_eval_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M31_conceptgraphs_query_metric_v0/policy_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M31_conceptgraphs_query_metric_v0/metrics.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M31_conceptgraphs_query_metric_v0/route_decision.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M31_conceptgraphs_query_metric_v0/report.md`

사실:

- Status: `e005_m31_conceptgraphs_query_metric_strict_near_miss_ready`.
- Query rows: 1.
- Candidate rows: 6.
- Min center distance: 1.345793m.
- Min bbox distance: 0.662517m.
- Strict center hit rows: 0.
- Strict bbox hit rows: 0.
- Relaxed bbox 1m hit rows: 2.
- Relaxed bbox 1m top3 success rows/rate: 1 / 1.0.
- Selected next route: `scale_conceptgraphs_with_geometry_threshold_boundary`.

논문 주장:

- E005-M31 supports a one-scan query-level diagnostic for the `ConceptGraphs` external mapping route.
- E005-M31 does not support a final `ConceptGraphs` baseline performance claim.

에이전트 추론:

- The useful signal is not strict success. The useful signal is that `ConceptGraphs` produces target-near map objects, but the strict 0.5m metric and object extent/centroid alignment are not yet resolved.
- Scaling to 4 staged scans is still reasonable, but only with strict and relaxed geometry metrics reported separately.

사용자 판단 필요:

- Resolved by E005-M32/M33.

## E005-M32 ConceptGraphs Scale Decision

Implementation unit: `E005-M32_conceptgraphs_scale_decision_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/plan_m32_conceptgraphs_scale_decision.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/plan_m32_conceptgraphs_scale_decision.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M32_conceptgraphs_scale_decision_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M32_conceptgraphs_scale_decision_v0/scan_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M32_conceptgraphs_scale_decision_v0/metric_boundary.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M32_conceptgraphs_scale_decision_v0/route_decision.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M32_conceptgraphs_scale_decision_v0/report.md`

사실:

- Status: `e005_m32_conceptgraphs_scale_decision_approved`.
- Ready staged scans: 4 / 4.
- Completed runtime scans before M33: 1.
- Pending runtime scans: 3.
- M60 query rows over staged scans: 7.
- M73 expanded query rows over staged scans: 96.
- GPU free at decision: 23445 MiB.
- Selected next route: `approve_background_scale_runtime_for_pending_scans`.

논문 주장:

- E005-M32 supports the decision to scale `ConceptGraphs` runtime under an explicit strict/relaxed geometry boundary.
- It does not support a baseline result claim.

에이전트 추론:

- Scaling is justified because M31 produced a measurable near-hit, not a dead route.
- The scale pass must keep `strict_bbox_0p5m`, `strict_center_0p5m`, and `relaxed_bbox_1p0m` separate.

사용자 판단 필요:

- None before E005-M33.

## E005-M33 ConceptGraphs Pending Scan Runtime Launch / Relaunch

Implementation unit: `E005-M33_conceptgraphs_pending_scan_runtime_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/launch_m33_conceptgraphs_pending_scans.py
python experiments/E005_external_baseline_transition/tools/verify_m33_conceptgraphs_pending_scans.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/launch_m33_conceptgraphs_pending_scans.py`
- `experiments/E005_external_baseline_transition/tools/verify_m33_conceptgraphs_pending_scans.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M33_conceptgraphs_pending_scan_runtime_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M33_conceptgraphs_pending_scan_runtime_v0/expected_outputs.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M33_conceptgraphs_pending_scan_runtime_v0/docker_command.txt`
- `experiments/E005_external_baseline_transition/artifacts/E005-M33_conceptgraphs_pending_scan_runtime_v0/run_m33_conceptgraphs_pending_scans.sh`
- `experiments/E005_external_baseline_transition/artifacts/E005-M33_conceptgraphs_pending_scan_runtime_v0/verification/coverage.json`

사실:

- Initial status: `e005_m33_conceptgraphs_pending_scan_runtime_job_launched`.
- Initial verifier status after first launch: `e005_m33_conceptgraphs_pending_scan_runtime_running`.
- Initial completion verification status: `e005_m33_conceptgraphs_pending_scan_runtime_failed`.
- Initial failure cause: Docker container could not read host-absolute symlinked `pose/000000.txt`.
- Relaunch status after E005-M34 repair: `e005_m33_conceptgraphs_pending_scan_runtime_job_launched`.
- Initial verifier status after relaunch: `e005_m33_conceptgraphs_pending_scan_runtime_running`.
- tmux session: `e005_m33_conceptgraphs_pending_scans`.
- Initial log: `logs/20260515_115722_e005_m33_conceptgraphs_pending_scans.log`.
- Current relaunch log: `logs/20260515_131945_e005_m33_conceptgraphs_pending_scans.log`.
- Pending scans: `10b17957-3938-2467-88a5-9e9254930dad`, `4731976c-f9f7-2a1a-95cc-31c4d1751d0b`, `5555106a-36f1-29c0-8913-df1ba3c3cfd5`.
- Verification command: `python experiments/E005_external_baseline_transition/tools/verify_m33_conceptgraphs_pending_scans.py`.

논문 주장:

- E005-M33 does not support a baseline result claim.
- It only launches the long-running runtime needed before 4-scan schema/conversion/metrics.

에이전트 추론:

- The initial failure is a staging adapter bug, not a method-performance result.
- This job should remain backgrounded. Do not continuously monitor the log; use E005-M34 or explicit user request to check progress.

사용자 판단 필요:

- None before E005-M34 completion verification.

## E005-M34 ConceptGraphs Pending Scan Staging Repair

Implementation unit: `E005-M34_conceptgraphs_pending_scan_staging_repair_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/repair_m34_conceptgraphs_pending_scan_staging.py
docker run --rm -v /home/yoohyun/research2/local_dataset/ConceptGraphs_staged/3rscan_depth_aligned_scannet:/data/ConceptGraphs_staged/3rscan_depth_aligned_scannet:ro research2/conceptgraphs-smoke:latest bash -lc 'test -f /data/ConceptGraphs_staged/3rscan_depth_aligned_scannet/10b17957-3938-2467-88a5-9e9254930dad/pose/000000.txt && test -f /data/ConceptGraphs_staged/3rscan_depth_aligned_scannet/10b17957-3938-2467-88a5-9e9254930dad/depth/000000.png && echo container_read_ok'
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/repair_m34_conceptgraphs_pending_scan_staging.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M34_conceptgraphs_pending_scan_staging_repair_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M34_conceptgraphs_pending_scan_staging_repair_v0/scan_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M34_conceptgraphs_pending_scan_staging_repair_v0/report.md`

사실:

- Status: `e005_m34_conceptgraphs_pending_scan_staging_repair_ready`.
- Previous failures: M33 first launch failed because staged `depth/pose` files were host-absolute symlinks that broke inside Docker; first repair relaunch failed because pending scan roots were not writable to the Docker runtime user.
- Pending scans repaired: 3 / 3.
- Materialized files: 1,466 on first repair run.
- Permission-changed dirs/files: 15 / 2,205 on latest repair run.
- Container read smoke: passed.
- Container write smoke: passed.
- M33 relaunched after repair: true.
- Current relaunch log: `logs/20260515_131945_e005_m33_conceptgraphs_pending_scans.log`.
- Completion status after relaunch: `e005_m33_conceptgraphs_pending_scan_runtime_outputs_ready`.
- Ready scans after relaunch: 3 / 3.

논문 주장:

- E005-M34 does not support a `ConceptGraphs` performance claim.
- It supports only the runtime validity of the staged input adapter.

에이전트 추론:

- This repair keeps the baseline route alive because the blockers were file visibility and output write permission, not output schema or query-level failure.
- The next evidence must still come from completed runtime outputs and E005-M35 query metric conversion.

사용자 판단 필요:

- Resolved by E005-M35.

## E005-M35 ConceptGraphs 4-Scan Query Metric

Implementation unit: `E005-M35_conceptgraphs_4scan_query_metric_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/run_m35_conceptgraphs_4scan_query_metrics.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/run_m35_conceptgraphs_4scan_query_metrics.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M35_conceptgraphs_4scan_query_metric_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M35_conceptgraphs_4scan_query_metric_v0/metrics.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M35_conceptgraphs_4scan_query_metric_v0/object_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M35_conceptgraphs_4scan_query_metric_v0/candidate_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M35_conceptgraphs_4scan_query_metric_v0/candidate_eval_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M35_conceptgraphs_4scan_query_metric_v0/policy_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M35_conceptgraphs_4scan_query_metric_v0/report.md`

사실:

- Status: `e005_m35_conceptgraphs_4scan_query_metric_ready_with_strict_hits`.
- Scans: 4.
- Object rows: 126.
- Candidate rows: 3,308.
- Primary `M60` query rows: 7.
- Expanded `M73` query rows: 96.
- Primary `M60` strict bbox top5 success: 3 / 7 = 0.428571.
- Primary `M60` relaxed bbox 1m top3 success: 6 / 7 = 0.857143.
- Expanded `M73` strict bbox top5 success: 57 / 96 = 0.59375.
- Expanded `M73` relaxed bbox 1m top3 success: 60 / 96 = 0.625.
- Final baseline claim ready: false.

논문 주장:

- E005-M35 supports a small-subset external `ConceptGraphs` query-level conversion result.
- It does not support final real RGB-D/open-vocabulary robustness or real navigation `SR` / `SPL`.

에이전트 추론:

- Compared with M31 one-scan near-hit-only behavior, M35 shows that strict bbox hits exist at 4-scan scale.
- The result is useful for reviewer defense because `ConceptGraphs` is no longer only an executable baseline route; it has measurable query-level behavior.
- The next required step is failure analysis: which query labels/scans succeed, which fail, and whether strict-hit success is driven by a narrow subset.

사용자 판단 필요:

- None before E005-M36 failure analysis / claim boundary.

## E005-M36 ConceptGraphs Failure Boundary

Implementation unit: `E005-M36_conceptgraphs_failure_boundary_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/analyze_m36_conceptgraphs_failure_boundary.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/analyze_m36_conceptgraphs_failure_boundary.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M36_conceptgraphs_failure_boundary_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M36_conceptgraphs_failure_boundary_v0/aggregate.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M36_conceptgraphs_failure_boundary_v0/query_failure_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M36_conceptgraphs_failure_boundary_v0/primary_failure_examples.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M36_conceptgraphs_failure_boundary_v0/report.md`

사실:

- Status: `e005_m36_conceptgraphs_failure_boundary_ready`.
- Primary `M60` strict bbox top5: 3 / 7 = 0.428571.
- Primary `M60` relaxed bbox 1m top3: 6 / 7 = 0.857143.
- Primary `M60` strict center top5: 1 / 7 = 0.142857.
- Expanded `M73` strict bbox top5: 57 / 96 = 0.59375.
- Expanded `M73` relaxed bbox 1m top3: 60 / 96 = 0.625.
- Primary failure classes: `relaxed_top3_only_no_strict` 4, `strict_bbox_top5_success` 1, `strict_bbox_top5_success_centroid_miss` 2.
- Primary label boundary: `chair` strict bbox top5 0 / 3, `pillow` strict bbox top5 3 / 4.
- Final baseline claim ready: false.

논문 주장:

- E005-M36 supports a small-subset claim that `ConceptGraphs` map outputs can be evaluated in the same query-level search metric interface as the proposed route.
- E005-M36 does not support final `ConceptGraphs` baseline performance, final real RGB-D/open-vocabulary robustness, generality across unseen scenes/labels, or real navigation `SR` / `SPL`.

에이전트 추론:

- Bbox success is much stronger than centroid success, so the current evidence is object-extent coverage evidence more than precise centroid localization evidence.
- Primary `chair` failures are all `relaxed_top3_only_no_strict`, which means coverage is close but strict 0.5m localization is not met.
- Primary `pillow` is the main source of strict hits, so label-specific overclaiming is a reviewer risk.
- Expanded `M73` has better strict bbox rate than primary `M60`, so expanded results should remain diagnostic rather than the main claim.

사용자 판단 필요:

- None before E005-M38 `ConceptGraphs` heldout/scale expansion plan.

## E005-M37 External Baseline Comparison

Implementation unit: `E005-M37_external_baseline_comparison_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/plan_m37_external_baseline_comparison.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/plan_m37_external_baseline_comparison.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M37_external_baseline_comparison_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M37_external_baseline_comparison_v0/route_decision.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M37_external_baseline_comparison_v0/baseline_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M37_external_baseline_comparison_v0/report.md`

사실:

- Status: `e005_m37_external_baseline_comparison_ready`.
- Baseline rows: 6.
- `ConceptGraphs` query-level metric ready: true.
- `ConceptGraphs` final baseline claim ready: false.
- `DualMap` query-level metric ready: false.
- `OpenMask3D` query-level metric ready: false.
- Selected next route: `conceptgraphs_scale_heldout_first`.
- Next recommended unit: `E005-M38 ConceptGraphs heldout/scale expansion plan`.

논문 주장:

- E005-M37 supports a bounded baseline-comparison claim: `ConceptGraphs` is currently the only external mapping route with 4-scan query-level metrics in this workspace.
- E005-M37 does not support final external baseline performance, final real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.

에이전트 추론:

- The next highest-value step is scaling `ConceptGraphs` with a heldout scan/label contract, not launching another heavy baseline immediately.
- `Open3DSG` is the next reasonable second external map/scene-graph route after `ConceptGraphs` scale.
- `OpenMask3D` should stay deferred as a proposal-quality branch because the current blocker is environment-heavy and not map-level.

사용자 판단 필요:

- None before E005-M38.

## E005-M38 ConceptGraphs Heldout Scale

Implementation unit: `E005-M38_conceptgraphs_heldout_scale_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/plan_m38_conceptgraphs_heldout_scale.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/plan_m38_conceptgraphs_heldout_scale.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M38_conceptgraphs_heldout_scale_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M38_conceptgraphs_heldout_scale_v0/heldout_contract.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M38_conceptgraphs_heldout_scale_v0/scale_query_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M38_conceptgraphs_heldout_scale_v0/excluded_query_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M38_conceptgraphs_heldout_scale_v0/scan_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M38_conceptgraphs_heldout_scale_v0/report.md`

사실:

- Status: `e005_m38_conceptgraphs_heldout_scale_plan_ready`.
- Target scale: `all_query_rescan_universe_13scan_v0`.
- Source query rows: 294.
- Eligible query rows after generic-label exclusion: 291.
- Excluded query rows: 3.
- Scan count: 13.
- Dev existing split: 4 scans / 96 eligible query rows.
- Heldout sequence-required split: 9 scans / 195 eligible query rows.
- Heldout labels seen in dev: 6.
- Heldout labels not seen in dev: 17.
- Missing `sequence.zip` scan count: 9.
- Next recommended unit: `E005-M39 ConceptGraphs heldout sequence acquisition / staging launch`.

논문 주장:

- E005-M38 supports a heldout/scale contract for turning `ConceptGraphs` from a 4-scan diagnostic into a larger external baseline route.
- E005-M38 does not support heldout runtime performance, final external baseline performance, final real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.

에이전트 추론:

- The current 4-scan result should be treated as the dev/diagnostic split.
- The next scale target should cover all 13 E001 current-rescan query scans and 291 eligible query rows.
- The immediate blocker is data/runtime scale, not query schema: 9 heldout scans need `sequence.zip` acquisition/staging before `ConceptGraphs` runtime.
- The heldout split is useful because it includes both dev-seen and dev-unseen labels.

사용자 판단 필요:

- None before E005-M39.

## E005-M39 ConceptGraphs Heldout Sequence Launch

Implementation unit: `E005-M39_conceptgraphs_heldout_sequence_launch_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/launch_m39_conceptgraphs_heldout_sequence.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/launch_m39_conceptgraphs_heldout_sequence.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M39_conceptgraphs_heldout_sequence_launch_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M39_conceptgraphs_heldout_sequence_launch_v0/download_manifest.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M39_conceptgraphs_heldout_sequence_launch_v0/run_heldout_sequence_staging.sh`
- `experiments/E005_external_baseline_transition/artifacts/E005-M39_conceptgraphs_heldout_sequence_launch_v0/command_plan.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M39_conceptgraphs_heldout_sequence_launch_v0/report.md`

사실:

- Status: `e005_m39_heldout_sequence_job_launched`.
- Background status at launch: `running`.
- Completion status: verified by E005-M40.
- tmux session: `e005_m39_conceptgraphs_heldout_sequence`.
- Log: `logs/20260515_174433_e005_m39_conceptgraphs_heldout_sequence.log`.
- Target heldout scans: 9.
- Prelaunch sequence-ready scans: 0.
- Download required scans: 9.
- Decompression required scans: 9.
- Verification command: `python experiments/E003_perception_noise_expansion/tools/verify_m56_sequence_payloads.py --manifest experiments/E005_external_baseline_transition/artifacts/E005-M39_conceptgraphs_heldout_sequence_launch_v0/download_manifest.jsonl --out-dir experiments/E005_external_baseline_transition/artifacts/E005-M39_conceptgraphs_heldout_sequence_launch_v0/verification --require-ready`.
- Next recommended unit: `E005-M40 ConceptGraphs heldout sequence staging completion verification`.

논문 주장:

- E005-M39 is a data acquisition/staging launch only.
- E005-M39 does not support `ConceptGraphs` heldout performance, final external baseline performance, final real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.

에이전트 추론:

- The job should run in background because it is I/O-heavy and resumable enough through `wget -c`.
- Completion should be checked by file counts, `sequence.zip` integrity, and the manifest verifier, not by printing the full log.

사용자 판단 필요:

- Resolved by E005-M40.

## E005-M40 Heldout Sequence Staging Verification

Implementation unit: `E005-M40_heldout_sequence_staging_verification_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/verify_m40_conceptgraphs_heldout_sequence_staging.py --require-ready
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/verify_m40_conceptgraphs_heldout_sequence_staging.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M40_heldout_sequence_staging_verification_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M40_heldout_sequence_staging_verification_v0/sequence_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M40_heldout_sequence_staging_verification_v0/report.md`

사실:

- Status: `e005_m40_heldout_sequence_staging_ready`.
- Manifest rows: 9.
- Ready rows: 9.
- Sequence zip valid rows: 9.
- Total frame triplet lower bound: 2,982.
- Minimum frame triplet lower bound: 111.
- Heldout query rows after exclusion: 195.
- tmux session stopped: true.
- Next recommended unit: `E005-M41 ConceptGraphs heldout runtime preflight / launch plan`.

논문 주장:

- E005-M40 supports only heldout sequence staging readiness for the external baseline runtime route.
- E005-M40 does not support `ConceptGraphs` heldout runtime performance, final external baseline performance, final real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.

에이전트 추론:

- Heldout runtime can be planned next because all 9 heldout scans have valid `sequence.zip` files and extracted color/depth/pose triplets.
- The next bottleneck is not data acquisition; it is materializing the `ConceptGraphs` staged layout for these scans, running runtime, and converting outputs to strict/relaxed query metrics.

사용자 판단 필요:

- Resolved by E005-M41.

## E005-M41 Heldout Runtime Preflight

Implementation unit: `E005-M41_conceptgraphs_heldout_runtime_preflight_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/plan_m41_conceptgraphs_heldout_runtime_preflight.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/plan_m41_conceptgraphs_heldout_runtime_preflight.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M41_conceptgraphs_heldout_runtime_preflight_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M41_conceptgraphs_heldout_runtime_preflight_v0/heldout_runtime_scan_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M41_conceptgraphs_heldout_runtime_preflight_v0/runtime_batch_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M41_conceptgraphs_heldout_runtime_preflight_v0/staging_materialization_plan.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M41_conceptgraphs_heldout_runtime_preflight_v0/runtime_launch_plan.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M41_conceptgraphs_heldout_runtime_preflight_v0/report.md`

사실:

- Status: `e005_m41_heldout_runtime_preflight_ready_with_staging_required`.
- Heldout scans: 9.
- M40 sequence-ready scans: 9 / 9.
- `ConceptGraphs` staged payload ready scans: 0 / 9.
- Runtime output ready scans: 0 / 9.
- Raw frame triplet lower bound total: 2,982.
- Docker image ready: true.
- Model checkpoints ready: true.
- Runtime launch ready now: false.
- Planned runtime strategy after staging: bounded 3-scan batches.
- Next recommended unit: `E005-M42 ConceptGraphs heldout staging materialization`.

논문 주장:

- E005-M41 supports only a heldout runtime preflight / launch-plan decision.
- E005-M41 does not support heldout performance, final external baseline performance, final real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.

에이전트 추론:

- The immediate blocker is not `sequence.zip`, Docker image, or checkpoint availability.
- The immediate blocker is converting 9 raw `3RScan` sequence folders into the `ConceptGraphs` depth-aligned Scannet-style layout: resized color JPG, depth PNG, pose TXT, and intrinsic files.
- Runtime should be launched only after E005-M42 verifies the heldout staged layout.

사용자 판단 필요:

- Resolved by E005-M42.

## E005-M43/M48/M49 Heldout Runtime And Metric Batches

Implementation unit: `E005-M43_conceptgraphs_heldout_runtime_batch_launch_v0`.

사실:

- Latest status: `heldout_b01`, `heldout_b02`, and `heldout_b03` runtime outputs and query metrics are ready.
- `heldout_b01` selected scans: 3, query rows 66 / 195 heldout.
- `heldout_b01` strict bbox top5: 45 / 66 = 0.681818.
- `heldout_b01` relaxed bbox 1m top3: 57 / 66 = 0.863636.
- `heldout_b02` selected scans: 3, query rows 69 / 195 heldout.
- `heldout_b02` GSA detections: 210 / 63 / 33.
- `heldout_b02` object rows / candidate rows: 199 / 4,614.
- `heldout_b02` strict bbox top5: 45 / 69 = 0.652174.
- `heldout_b02` relaxed bbox 1m top3: 51 / 69 = 0.739130.
- `heldout_b03` query rows: 60 / 195 heldout.
- `heldout_b03` strict bbox top5: 24 / 60 = 0.400000.
- `heldout_b03` relaxed bbox 1m top3: 36 / 60 = 0.600000.
- Full heldout strict bbox top5: 114 / 195 = 0.584615.
- Full heldout relaxed bbox 1m top3: 144 / 195 = 0.738462.
- Artifact path: `experiments/E005_external_baseline_transition/artifacts/E005-M43_conceptgraphs_heldout_runtime_batch_launch_v0/`.
- Metric artifact path: `experiments/E005_external_baseline_transition/artifacts/E005-M45_conceptgraphs_heldout_query_metric_v0/`.
- Verification command template: `python experiments/E005_external_baseline_transition/tools/verify_m43_conceptgraphs_heldout_runtime_batch.py --batch-id <heldout_bXX>`.
- Metric command template: `python experiments/E005_external_baseline_transition/tools/run_m45_conceptgraphs_heldout_query_metrics.py --batch-id <heldout_bXX>`.

논문 주장:

- E005-M49 supports a full heldout `ConceptGraphs` query-level external map baseline.
- E005-M49 alone does not support final real RGB-D/open-vocabulary robustness or real navigation `SR` / `SPL`.

에이전트 추론:

- The full heldout `ConceptGraphs` table is sufficient for proxy-search comparison after H001 replay, but real RGB-D/open-vocabulary robustness still needs another external route or robustness denominator.

사용자 판단 필요:

- Resolved by E005-M49/M52/M53/M54.

## E005-M42 Heldout Staging Materialization

Implementation unit: `E005-M42_conceptgraphs_heldout_staging_materialization_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/materialize_m42_conceptgraphs_heldout_staging.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/materialize_m42_conceptgraphs_heldout_staging.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M42_conceptgraphs_heldout_staging_materialization_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M42_conceptgraphs_heldout_staging_materialization_v0/materialization_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M42_conceptgraphs_heldout_staging_materialization_v0/verification_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M42_conceptgraphs_heldout_staging_materialization_v0/report.md`

사실:

- Status: `e005_m42_conceptgraphs_heldout_staging_materialized_ready`.
- Target scans: 9.
- Ready scans: 9 / 9.
- Color JPGs: 2,982.
- Depth PNGs: 2,982.
- Pose TXTs: 2,982.
- Resolution-aligned scans: 9 / 9.
- Error count: 0.
- Container read/write smoke: passed.
- Runtime launched: false.
- Next recommended unit: `E005-M43 ConceptGraphs heldout runtime batch launch`.

논문 주장:

- E005-M42 supports heldout staged-layout readiness for the external `ConceptGraphs` runtime route.
- E005-M42 does not support heldout `ConceptGraphs` runtime performance, final external baseline performance, final real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.

에이전트 추론:

- The blocker after E005-M42 was no longer heldout staged-layout availability.
- E005-M43 launched heldout runtime in a bounded batch after enough GPU memory was available because `GSA` and `cfslam` are GPU-heavy.

사용자 판단 필요:

- None before E005-M43 launch.

## E005-M01 External Baseline Transition

Implementation unit: `E005-M01_external_baseline_transition_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/plan_m01_external_baseline_transition.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/plan_m01_external_baseline_transition.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M01_external_baseline_transition_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M01_external_baseline_transition_v0/decision.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M01_external_baseline_transition_v0/candidate_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M01_external_baseline_transition_v0/report.md`

사실:

- Status: `e005_m01_external_baseline_transition_ready`.
- Candidate baselines scored: 10.
- Selected first route: `DualMap`.
- Backup route: `ConceptGraphs`.
- `OpenMask3D` local blocker present: true.
- Top candidates by score: `DualMap` 45, `ConceptGraphs` 44, `DualMap-light ablation` 42, `Open3DSG` 39, `HOV-SG` 38.

논문 주장:

- E005-M01 does not add a performance claim.
- It fixes the first external-baseline route needed to defend E004 against dynamic semantic mapping and open-vocabulary mapping baselines.
- Final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.

에이전트 추론:

- `DualMap` should be audited first because it is the closest external baseline to task/staleness-aware dynamic semantic memory.
- `ConceptGraphs` should be the immediate fallback because it can be framed as an open-vocabulary graph mapping baseline over posed RGB-D scans.
- `VLFM`, `HM3D-OVON`, and `GOAT-Bench` are later navigation baselines; they require simulator-backed episodes before they can fairly test `SR` / `SPL`.

사용자 판단 필요:

- None before E005-M02.

## E005-M02 DualMap Interface Audit

Implementation unit: `E005-M02_dualmap_interface_audit_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/plan_m02_dualmap_interface_audit.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/plan_m02_dualmap_interface_audit.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M02_dualmap_interface_audit_v0/source_audit.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M02_dualmap_interface_audit_v0/adapter_contract.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M02_dualmap_interface_audit_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M02_dualmap_interface_audit_v0/decision.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M02_dualmap_interface_audit_v0/report.md`

사실:

- Status: `e005_m02_dualmap_interface_audit_ready_with_staging_required`.
- Official repo: `https://github.com/Eku127/DualMap`.
- Checked main commit: `157235ec49e6a1f439babbc571c4c02ad1f06aa9`.
- License: `Apache-2.0`.
- Official input modes: Dataset Mode, ROS streams / rosbags, `Record3D`, and online simulation via `Habitat Data Collector`.
- Dataset Mode supports `Replica`, `ScanNet`, `TUM RGB-D`, and self-collected `Habitat Data Collector` data.
- Documented Dataset Mode outputs include object `*.pkl`, `layout.pcd`, optional detections, `detector_time.csv`, and `system_time.csv`.
- Direct drop-in to current E004 JSONL rows: false.
- Dataset Mode staging route feasible: true.
- Adapter contract ready: true.
- External baseline comparison ready: false.

논문 주장:

- E005-M02 does not support a `DualMap` performance claim.
- E005-M02 supports an adapter contract and confirms that a fair official `DualMap` comparison requires dataset-format staging.
- Final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.

에이전트 추론:

- `DualMap` is not a direct JSONL baseline because it expects RGB-D streams or dataset layouts and emits map artifacts.
- The defensible route is to stage selected `3RScan` current-rescan sequences into a `DualMap`-compatible Dataset Mode layout, then convert `DualMap` map/query outputs into E004 candidate rows.
- If object `*.pkl` schema or model dependencies block this route, `ConceptGraphs` remains the fallback external mapping baseline.

사용자 판단 필요:

- None before E005-M03.

## E005-M03 DualMap 3RScan Staging Feasibility

Implementation unit: `E005-M03_dualmap_3rscan_staging_feasibility_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/plan_m03_dualmap_staging_feasibility.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/plan_m03_dualmap_staging_feasibility.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M03_dualmap_3rscan_staging_feasibility_v0/scan_preflight_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M03_dualmap_3rscan_staging_feasibility_v0/staging_plan.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M03_dualmap_3rscan_staging_feasibility_v0/dualmap_3rscan_scannet.yaml`
- `experiments/E005_external_baseline_transition/artifacts/E005-M03_dualmap_3rscan_staging_feasibility_v0/decision.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M03_dualmap_3rscan_staging_feasibility_v0/report.md`

사실:

- Status: `e005_m03_dualmap_3rscan_staging_feasibility_ready_with_conversion_required`.
- Selected scans from E003-M73: 4.
- Preflight-ready scans: 4 / 4.
- RGB-D-pose triplets across selected scans: 826.
- Selected adapter: `scannet_exported_3rscan_adapter_v0`.
- Materialization executed: false.
- Depth conversion `.pgm` -> `.png` required: true.
- `DualMap` runtime launched: false.
- Object `*.pkl` schema inspection ready: false.

논문 주장:

- E005-M03 does not support a `DualMap` performance claim.
- E005-M03 supports a dataset-format feasibility claim: selected `3RScan` scans contain enough RGB-D-pose payload to be staged for a `DualMap` Dataset Mode smoke.
- Final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.

에이전트 추론:

- The `ScanNetDataset` adapter is the lowest-change route because it preserves per-frame pose files and color JPG files.
- The next practical blocker is not dataset download; it is bounded materialization: color symlink, depth conversion, pose symlink, and `intrinsic_depth.txt` generation.
- Object `*.pkl` schema inspection should follow a one-scan `DualMap` loader/runtime smoke or official serialization-source inspection.

사용자 판단 필요:

- None before E005-M04.

## E005-M04 DualMap Staging Root Materialization

Implementation unit: `E005-M04_dualmap_staging_root_materialization_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/materialize_m04_dualmap_staging_root.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/materialize_m04_dualmap_staging_root.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M04_dualmap_staging_root_materialization_v0/materialization_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M04_dualmap_staging_root_materialization_v0/runtime_smoke_plan.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M04_dualmap_staging_root_materialization_v0/schema_inspection_plan.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M04_dualmap_staging_root_materialization_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M04_dualmap_staging_root_materialization_v0/decision.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M04_dualmap_staging_root_materialization_v0/report.md`

사실:

- Status: `e005_m04_dualmap_staging_root_materialized_smoke_ready`.
- Staged dataset root: `local_dataset/DualMap_staged/3rscan_scannet_exported/scannet`.
- Materialized scans: 4 / 4.
- Color symlinks: 826.
- Depth PNG files: 826.
- Pose symlinks: 826.
- Intrinsic files: 4.
- Runtime smoke scan id: `ddc73795-765b-241a-9c5d-b97744afe077`.
- Runtime command plan ready: true.
- `DualMap` runtime launched: false.
- Object `*.pkl` schema inspected: false.

논문 주장:

- E005-M04 does not support a `DualMap` performance claim.
- E005-M04 supports a staging-root materialization claim: selected `3RScan` scans can be represented as a `DualMap` `ScanNetDataset`-style folder with image/depth/pose/intrinsic files present.
- External baseline comparison, final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.

에이전트 추론:

- Local file-layout blocker is resolved for the selected four scans.
- The next blocker is `DualMap` repo/dependency/model readiness plus object `*.pkl` schema inspection.
- Color/depth resolution alignment remains a runtime validation risk because local `3RScan` color is 960x540 while depth is 224x172.

사용자 판단 필요:

- None before E005-M05.

## E005-M05 DualMap Runtime Preflight

Implementation unit: `E005-M05_dualmap_runtime_preflight_v0`.

Command:

```bash
printf '<sudo-password>\n' | python experiments/E005_external_baseline_transition/tools/preflight_m05_dualmap_runtime.py --docker-sudo-password-stdin
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/preflight_m05_dualmap_runtime.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M05_dualmap_runtime_preflight_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M05_dualmap_runtime_preflight_v0/decision.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M05_dualmap_runtime_preflight_v0/dependency_rows.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M05_dualmap_runtime_preflight_v0/static_object_pkl_schema.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M05_dualmap_runtime_preflight_v0/runtime_command_plan.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M05_dualmap_runtime_preflight_v0/bootstrap_plan.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M05_dualmap_runtime_preflight_v0/report.md`

사실:

- Status: `e005_m05_dualmap_runtime_blocked_env_bootstrap_required`.
- Official repo path: `local_dataset/external_repos/DualMap`.
- Repo head matches audited commit `157235ec49e6a1f439babbc571c4c02ad1f06aa9`: true.
- Smoke scan id: `ddc73795-765b-241a-9c5d-b97744afe077`.
- Smoke scan color/depth/pose frame counts: 93 / 93 / 93.
- Docker daemon ready: true.
- NVIDIA runtime detected: true.
- GPU probe: `NVIDIA GeForce RTX 5090, 32607 MiB, 580.126.09`.
- Static object `*.pkl` schema inspected: true.
- Static schema fields: `uid`, `pcd_points`, `pcd_colors`, `clip_ft`, `class_id`, `nav_goal`.
- `mobileclip` submodule ready: false.
- Current Python runtime dependency ready: false.
- `DualMap` runtime launched: false.
- Runtime object `*.pkl` inspected: false.

논문 주장:

- E005-M05 does not support a `DualMap` performance claim.
- E005-M05 supports a runtime-readiness claim: source, staged scan, Docker/GPU access, and static object schema are ready enough to justify environment bootstrap.
- External baseline comparison, final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.

에이전트 추론:

- The blocker is now environment/bootstrap, not selected-scan file layout.
- The next unit should initialize `mobileclip` and build or launch a Docker-compatible runtime route before attempting one-scan mapping.
- Static object schema is promising for adapter conversion, but runtime `*.pkl` outputs must be inspected before any metric integration.

사용자 판단 필요:

- None before E005-M06.

## E005-M06 DualMap Bootstrap Launch

Implementation unit: `E005-M06_dualmap_bootstrap_launch_v0`.

Launch command:

```bash
printf '<sudo-password>\n' | python experiments/E005_external_baseline_transition/tools/launch_m06_dualmap_bootstrap.py --sudo-password-stdin
```

Verification command:

```bash
printf '<sudo-password>\n' | python experiments/E005_external_baseline_transition/tools/verify_m06_dualmap_bootstrap.py --sudo-password-stdin
```

Artifacts:

- `experiments/E005_external_baseline_transition/docker/dualmap_smoke/Dockerfile`
- `experiments/E005_external_baseline_transition/tools/launch_m06_dualmap_bootstrap.py`
- `experiments/E005_external_baseline_transition/tools/verify_m06_dualmap_bootstrap.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M06_dualmap_bootstrap_launch_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M06_dualmap_bootstrap_launch_v0/decision.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M06_dualmap_bootstrap_launch_v0/report.md`
- `experiments/E005_external_baseline_transition/artifacts/E005-M06_dualmap_bootstrap_launch_v0/verification/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M06_dualmap_bootstrap_launch_v0/verification/report.md`

사실:

- Status: `e005_m06_dualmap_bootstrap_job_launched`.
- tmux session: `e005_m06_dualmap_bootstrap`.
- Log path: `logs/20260513_142937_e005_m06_dualmap_bootstrap.log`.
- Docker image: `research2/dualmap-smoke:latest`.
- Dockerfile route clones official `DualMap`, checks out commit `157235ec49e6a1f439babbc571c4c02ad1f06aa9`, initializes `mobileclip`, creates the `dualmap` environment, installs `mobileclip`, and runs dependency import smoke.
- Initial verifier status: `e005_m06_dualmap_bootstrap_running`.
- Local `mobileclip` submodule ready: true.
- Docker image ready at initial verification: false.
- Bounded Dockerfile repair applied after initial failure: use absolute env Python `/opt/conda/envs/dualmap/bin/python` for `mobileclip` install and import smoke.
- Runtime one-scan smoke launched: false.

논문 주장:

- E005-M06 does not support a `DualMap` performance claim.
- E005-M06 only launches the environment/bootstrap job required before one-scan runtime smoke and runtime `*.pkl` schema inspection.
- External baseline comparison, final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.

에이전트 추론:

- Do not monitor the Docker build continuously.
- The next unit should verify whether the background build completed, failed, or still runs.
- If image readiness passes, E005 can move to one-scan `DualMap` runtime smoke; if it fails on dependency resolution, use targeted log tail to choose bounded repair or `ConceptGraphs` fallback.

사용자 판단 필요:

- None before E005-M08.

## E005-M07 DualMap Bootstrap Completion Verification

Implementation unit: `E005-M07_dualmap_bootstrap_completion_verification_v0`.

Command:

```bash
printf '<sudo-password>\n' | python experiments/E005_external_baseline_transition/tools/verify_m06_dualmap_bootstrap.py --sudo-password-stdin
```

Artifacts:

- `experiments/E005_external_baseline_transition/artifacts/E005-M06_dualmap_bootstrap_launch_v0/verification/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M06_dualmap_bootstrap_launch_v0/verification/report.md`

사실:

- Status: `e005_m06_dualmap_bootstrap_ready`.
- tmux session `e005_m06_dualmap_bootstrap` stopped: true.
- Background status: `completed`.
- Docker image ready: true.
- Docker image: `research2/dualmap-smoke:latest`.
- Docker image id: `sha256:7c053613ab51d968f4e70896364af2493595e827fb7605f0fd16c514c5cc0bf4`.
- Docker image size: 7,927,047,638 bytes.
- Local `mobileclip` ready: true.
- Dependency import smoke: `dualmap_import_smoke_ok`.
- Log path: `logs/20260513_142937_e005_m06_dualmap_bootstrap.log`.
- One-scan `DualMap` runtime launched: false.

논문 주장:

- E005-M07 does not support a `DualMap` performance claim.
- E005-M07 only removes the environment/bootstrap blocker before one-scan runtime smoke.
- External baseline comparison, final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.

에이전트 추론:

- The next useful unit is E005-M08 one-scan runtime smoke on `ddc73795-765b-241a-9c5d-b97744afe077`.
- If runtime map outputs are produced, inspect runtime object `*.pkl` schema before writing any E004/E005 adapter.
- If runtime execution fails on code/data mismatch, record the exact blocker and decide between bounded adapter repair and `ConceptGraphs` fallback.

사용자 판단 필요:

- None before E005-M08.

## E005-M08 DualMap One-Scan Runtime Smoke Launch

Implementation unit: `E005-M08_dualmap_one_scan_runtime_smoke_v0`.

Launch command:

```bash
printf '<sudo-password>\n' | python experiments/E005_external_baseline_transition/tools/launch_m08_dualmap_runtime_smoke.py --sudo-password-stdin
```

Verification command:

```bash
python experiments/E005_external_baseline_transition/tools/verify_m08_dualmap_runtime_smoke.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/launch_m08_dualmap_runtime_smoke.py`
- `experiments/E005_external_baseline_transition/tools/verify_m08_dualmap_runtime_smoke.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M08_dualmap_one_scan_runtime_smoke_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M08_dualmap_one_scan_runtime_smoke_v0/decision.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M08_dualmap_one_scan_runtime_smoke_v0/runtime_command.txt`
- `experiments/E005_external_baseline_transition/artifacts/E005-M08_dualmap_one_scan_runtime_smoke_v0/run_m08_dualmap_one_scan_runtime.sh`
- `experiments/E005_external_baseline_transition/artifacts/E005-M08_dualmap_one_scan_runtime_smoke_v0/verification/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M08_dualmap_one_scan_runtime_smoke_v0/verification/report.md`

사실:

- Launch status: `e005_m08_dualmap_runtime_job_launched`.
- Verifier status: `e005_m08_dualmap_runtime_running`.
- tmux session: `e005_m08_dualmap_runtime`.
- Log path: `logs/20260513_153046_e005_m08_dualmap_one_scan_runtime.log`.
- Docker image: `research2/dualmap-smoke:latest`.
- Smoke scan id: `ddc73795-765b-241a-9c5d-b97744afe077`.
- Output path: `local_dataset/DualMap_outputs/ddc73795-765b-241a-9c5d-b97744afe077`.
- Staged color/depth/pose counts: 93 / 93 / 93.
- Runtime object `*.pkl` count while running: 0.
- Runtime completion verified: false.

논문 주장:

- E005-M08 does not support a `DualMap` performance claim.
- E005-M08 only launches the one-scan runtime smoke needed before runtime output verification, object schema inspection, and adapter design.
- External baseline comparison, final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.

에이전트 추론:

- Do not monitor the runtime continuously.
- The next useful unit is E005-M09 completion verification using file counts, expected output layout, and targeted log tail.
- If runtime outputs are ready, inspect runtime object `*.pkl` schema before writing any E004/E005 adapter.
- If runtime fails on model download, GPU compatibility, or code/data mismatch, record the blocker before choosing bounded repair or `ConceptGraphs` fallback.

사용자 판단 필요:

- None before E005-M09.

## E005-M09 DualMap Runtime Completion Verification

Implementation unit: `E005-M09_dualmap_runtime_completion_verification_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/verify_m08_dualmap_runtime_smoke.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/artifacts/E005-M08_dualmap_one_scan_runtime_smoke_v0/verification/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M08_dualmap_one_scan_runtime_smoke_v0/verification/report.md`

사실:

- Status: `e005_m08_dualmap_runtime_failed`.
- tmux session `e005_m08_dualmap_runtime` running: false.
- Background status: `failed`.
- Background returncode: 137.
- Output path exists: true.
- Runtime object `*.pkl` count: 0.
- `layout.pcd` count: 0.
- `system_time.csv` count: 0.
- DualMap log count: 1.
- Failure signals: `cuda_out_of_memory`, `clip_model_init_failed`, `yolo_not_initialized_after_detector_init_failure`, `fastsam_not_initialized_after_detector_init_failure`, `hydra_job_error`.
- GPU snapshot after cleanup: 1510 MiB free, with an unrelated `python3` process using 27714 MiB.

논문 주장:

- E005-M09 does not support a `DualMap` performance claim.
- E005-M09 is a failure diagnosis: the staged dataset and Docker image reached runtime entry, but detector/model initialization failed before map outputs were produced.
- External baseline comparison, final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.

에이전트 추론:

- The failure should be treated as runtime resource/model-init blocker, not evidence against `DualMap` or the dataset-format adapter.
- The next useful unit is E005-M10 repair/relaunch decision: free-GPU retry, loader-only layout smoke, lower-memory detector configuration, or `ConceptGraphs` fallback.
- Do not stop unrelated GPU processes without explicit user approval.

사용자 판단 필요:

- None before E005-M10.

## E005-M10 DualMap Runtime Repair Decision

Implementation unit: `E005-M10_dualmap_runtime_repair_decision_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/plan_m10_dualmap_runtime_repair_decision.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/plan_m10_dualmap_runtime_repair_decision.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M10_dualmap_runtime_repair_decision_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M10_dualmap_runtime_repair_decision_v0/decision.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M10_dualmap_runtime_repair_decision_v0/route_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M10_dualmap_runtime_repair_decision_v0/detector_enabled_retry_command_plan.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M10_dualmap_runtime_repair_decision_v0/loader_only_layout_command_plan.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M10_dualmap_runtime_repair_decision_v0/report.md`

사실:

- Status: `e005_m10_dualmap_runtime_repair_decision_ready`.
- Previous runtime verifier status: `e005_m08_dualmap_runtime_failed`.
- Previous failure signals include `cuda_out_of_memory` and `clip_model_init_failed`.
- Current GPU snapshot at decision time: `NVIDIA GeForce RTX 5090`, 29045 / 32607 MiB free.
- Staged smoke scan counts remain color/depth/pose 93 / 93 / 93.
- Selected route: `detector_enabled_free_gpu_retry`.
- Next recommended unit: `E005-M11 DualMap detector-enabled free-GPU retry launch`.

논문 주장:

- E005-M10 does not support a `DualMap` performance claim.
- E005-M10 only fixes the relaunch route after separating resource failure from dataset-format failure.
- A detector-enabled retry can become external-baseline evidence only after object `*.pkl` schema inspection and E004-compatible adapter evaluation.
- Loader-only layout smoke remains fallback compatibility evidence only.

에이전트 추론:

- Because the current GPU has enough free memory, the most useful next action is a detector-enabled retry rather than a loader-only run.
- If detector-enabled retry blocks again, use loader-only layout smoke or lower-memory detector configuration before switching to `ConceptGraphs`.
- Do not stop unrelated GPU processes without explicit user approval.

사용자 판단 필요:

- None before E005-M11.

## E005-M11 DualMap Detector-Enabled Retry Launch

Implementation unit: `E005-M11_dualmap_detector_enabled_free_gpu_retry_v0`.

Launch command:

```bash
python experiments/E005_external_baseline_transition/tools/launch_m11_dualmap_detector_retry.py --sudo-password-stdin --allow-low-gpu-free
```

Verification command:

```bash
python experiments/E005_external_baseline_transition/tools/verify_m11_dualmap_detector_retry.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/launch_m11_dualmap_detector_retry.py`
- `experiments/E005_external_baseline_transition/tools/verify_m11_dualmap_detector_retry.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M11_dualmap_detector_enabled_free_gpu_retry_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M11_dualmap_detector_enabled_free_gpu_retry_v0/decision.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M11_dualmap_detector_enabled_free_gpu_retry_v0/runtime_command.txt`
- `experiments/E005_external_baseline_transition/artifacts/E005-M11_dualmap_detector_enabled_free_gpu_retry_v0/run_m11_dualmap_detector_retry.sh`
- `experiments/E005_external_baseline_transition/artifacts/E005-M11_dualmap_detector_enabled_free_gpu_retry_v0/verification/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M11_dualmap_detector_enabled_free_gpu_retry_v0/verification/report.md`

사실:

- Launch status: `e005_m11_dualmap_detector_retry_job_launched`.
- Initial verifier status: `e005_m11_dualmap_detector_retry_running`.
- tmux session: `e005_m11_dualmap_detector_retry`.
- Log path: `logs/20260514_110141_e005_m11_dualmap_detector_retry.log`.
- Docker image: `research2/dualmap-smoke:latest`.
- Smoke scan id: `ddc73795-765b-241a-9c5d-b97744afe077`.
- Output path: `local_dataset/DualMap_outputs/E005-M11_detector_enabled_free_gpu_retry_v0/ddc73795-765b-241a-9c5d-b97744afe077`.
- Launch GPU free: 23082 MiB, with `allow_low_gpu_free=true`.
- Expected runtime outputs: object `*.pkl`, `layout.pcd`, `system_time.csv`.
- Initial runtime output counts: object `*.pkl` 0, `layout.pcd` 0, `system_time.csv` 0 while running.

논문 주장:

- E005-M11 does not support a `DualMap` performance claim.
- E005-M11 only launches the detector-enabled retry needed before runtime output verification and object schema inspection.
- External baseline comparison, final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.

에이전트 추론:

- Do not monitor the job continuously.
- The next useful unit at launch time was E005-M12 completion verification using file counts, targeted log tail, and runtime output layout.
- E005-M12 later exposed a cache-permission blocker, which was repaired in E005-M13/M14.

사용자 판단 필요:

- None before E005-M19.

## E005-M12 Through E005-M18 DualMap Runtime Output Diagnosis

Implementation units:

- `E005-M12`: detector-enabled retry completion verification.
- `E005-M13`: cache-permission repair plan.
- `E005-M14`: cache-fixed detector retry launch.
- `E005-M15`: cache-fixed detector retry completion verification.
- `E005-M16`: object-output diagnosis and denser-stride repair plan.
- `E005-M17`: denser-stride object retry launch.
- `E005-M18`: denser-stride retry completion verification.

Commands:

```bash
python experiments/E005_external_baseline_transition/tools/verify_m11_dualmap_detector_retry.py
python experiments/E005_external_baseline_transition/tools/plan_m13_dualmap_cache_permission_repair.py
python experiments/E005_external_baseline_transition/tools/verify_m14_dualmap_cache_fixed_retry.py
python experiments/E005_external_baseline_transition/tools/plan_m16_dualmap_object_output_diagnosis.py
python experiments/E005_external_baseline_transition/tools/verify_m17_dualmap_denser_stride_retry.py
```

Launch commands:

```bash
python experiments/E005_external_baseline_transition/tools/launch_m14_dualmap_cache_fixed_retry.py --sudo-password-stdin
python experiments/E005_external_baseline_transition/tools/launch_m17_dualmap_denser_stride_retry.py --sudo-password-stdin
```

사실:

- E005-M12 status: `e005_m11_dualmap_detector_retry_failed`.
- E005-M12 failure signals: `yolo_model_init_failed`, `permission_denied`, `fastsam_not_initialized_after_detector_init_failure`, `hydra_job_error`.
- E005-M13 selected route: `cache_fixed_detector_retry`, with writable host cache mounted at `/home/mambauser/.cache`.
- E005-M15 status: `e005_m14_dualmap_cache_fixed_retry_completed_missing_expected_outputs`.
- E005-M15 output inventory: object `*.pkl` 0, `layout.pcd` 1, `system_time.csv` 1, `detector_time.csv` 1.
- E005-M16 diagnosis: M14 processed 5 keyframes with `stride=20`, `stable_num=8`, and local objects went 8 -> 0 before save.
- E005-M17 changed only `stride=20` -> `stride=5` while keeping `stable_num=8`.
- E005-M18 status: `e005_m17_dualmap_denser_stride_retry_completed_missing_expected_outputs`.
- E005-M18 output inventory: processed keyframes 19, local objects 26 -> 0, object `*.pkl` 0, `layout.pcd` 1, `system_time.csv` 1, `detector_time.csv` 1.

논문 주장:

- These steps do not support a `DualMap` performance claim.
- They support a bounded external-baseline feasibility statement: `DualMap` can run on the staged `3RScan` adapter, but current outputs are insufficient for object-map baseline evaluation.
- Final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.

에이전트 추론:

- The immediate blocker is no longer GPU memory, Docker bootstrap, or cache permission.
- The current blocker is object retention / output compatibility under the staged `3RScan` Dataset Mode adapter.
- A lower-`stable_num` retry can be useful only as schema/serialization evidence; it should not be reported as faithful `DualMap` baseline performance.
- `ConceptGraphs` should become the next external mapping baseline route if a faithful `DualMap` object-map output cannot be recovered with one bounded diagnostic.

사용자 판단 필요:

- Resolved by E005-M19: move to `ConceptGraphs`.

## E005-M19 DualMap Fallback Decision

Implementation unit: `E005-M19_dualmap_fallback_decision_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/plan_m19_dualmap_fallback_decision.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/plan_m19_dualmap_fallback_decision.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M19_dualmap_fallback_decision_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M19_dualmap_fallback_decision_v0/decision.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M19_dualmap_fallback_decision_v0/route_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M19_dualmap_fallback_decision_v0/report.md`

사실:

- Status: `e005_m19_dualmap_fallback_decision_ready`.
- M18 verifier status: `e005_m17_dualmap_denser_stride_retry_completed_missing_expected_outputs`.
- M18 processed keyframes: 19.
- M18 local object count: 26 -> 0.
- M18 object `*.pkl` count: 0.
- M18 `layout.pcd` / `system_time.csv` / `detector_time.csv`: 1 / 1 / 1.
- Selected route: `conceptgraphs_fallback_source_interface_audit`.
- Lower-`stable_num` retry selected: false.

논문 주장:

- E005-M19 does not support a `ConceptGraphs` or `DualMap` performance claim.
- E005-M19 fixes the next external-baseline route after bounded `DualMap` object-output repairs fail.

에이전트 추론:

- A lower-`stable_num` `DualMap` retry would be schema-only diagnostic evidence and should not be reported as faithful baseline performance.
- `ConceptGraphs` is now the better next route because it preserves external open-vocabulary mapping pressure without modifying `DualMap` internals.

사용자 판단 필요:

- None before E005-M23.

## E005-M23 ConceptGraphs Acquisition Launch

Implementation unit: `E005-M23_conceptgraphs_acquisition_launch_v0`.

Launch command:

```bash
python experiments/E005_external_baseline_transition/tools/launch_m23_conceptgraphs_acquisition.py
```

Initial verification command:

```bash
python experiments/E005_external_baseline_transition/tools/verify_m23_conceptgraphs_acquisition.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/launch_m23_conceptgraphs_acquisition.py`
- `experiments/E005_external_baseline_transition/tools/verify_m23_conceptgraphs_acquisition.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M23_conceptgraphs_acquisition_launch_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M23_conceptgraphs_acquisition_launch_v0/decision.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M23_conceptgraphs_acquisition_launch_v0/run_m23_conceptgraphs_acquisition.sh`
- `experiments/E005_external_baseline_transition/artifacts/E005-M23_conceptgraphs_acquisition_launch_v0/background_status.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M23_conceptgraphs_acquisition_launch_v0/report.md`

사실:

- Launch status: `e005_m23_conceptgraphs_acquisition_job_launched`.
- Initial verifier status: `e005_m23_conceptgraphs_acquisition_running`.
- tmux session: `e005_m23_conceptgraphs_acquisition`.
- Log path: `logs/20260514_165555_e005_m23_conceptgraphs_acquisition.log`.
- Background status path: `experiments/E005_external_baseline_transition/artifacts/E005-M23_conceptgraphs_acquisition_launch_v0/background_status.json`.
- Initial background step: `clone_gsa`.
- `ConceptGraphs` head already matched `93277a02bd89171f8121e84203121cf7af9ebb5d`.
- Runtime launched: false.
- Docker build launched: false.

논문 주장:

- E005-M23 does not support a `ConceptGraphs` performance claim.
- E005-M23 only launches repo/checkpoint acquisition.
- `ConceptGraphs` object-map baseline comparison still requires acquisition completion verification, Docker build, one-scan runtime smoke, and object-map schema inspection.

에이전트 추론:

- Do not continuously monitor this job.
- The next active unit is E005-M24 completion verification using file counts, commit hashes, checkpoint size, and status JSON.

사용자 판단 필요:

- Resolved by E005-M24: acquisition completed.

## E005-M24 ConceptGraphs Acquisition Completion Verification

Implementation unit: `E005-M24_conceptgraphs_acquisition_completion_verification`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/verify_m23_conceptgraphs_acquisition.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/artifacts/E005-M23_conceptgraphs_acquisition_launch_v0/verification/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M23_conceptgraphs_acquisition_launch_v0/verification/report.md`

사실:

- Status: `e005_m23_conceptgraphs_acquisition_completed_ready`.
- tmux running: false.
- Background status: `completed`.
- `ConceptGraphs` commit match: true.
- `Grounded-Segment-Anything` commit match: true.
- SAM cache symlink ready: true.
- SAM repo symlink ready: true.
- `groundingdino_swint_ogc.pth` ready: true.
- `groundingdino_swint_ogc.pth` size: 693,997,677 bytes.

논문 주장:

- E005-M24 does not support a `ConceptGraphs` performance claim.
- E005-M24 only verifies acquisition readiness before Docker build/runtime work.

에이전트 추론:

- The next blocker is Docker build/runtime dependency resolution, not repo/checkpoint acquisition.

사용자 판단 필요:

- None before E005-M26.

## E005-M25 ConceptGraphs Docker Build Preflight

Implementation unit: `E005-M25_conceptgraphs_docker_build_preflight_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/launch_m25_conceptgraphs_docker_build.py
python experiments/E005_external_baseline_transition/tools/verify_m25_conceptgraphs_docker_build.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/docker/conceptgraphs_smoke/Dockerfile`
- `experiments/E005_external_baseline_transition/docker/conceptgraphs_smoke/import_smoke.py`
- `experiments/E005_external_baseline_transition/tools/launch_m25_conceptgraphs_docker_build.py`
- `experiments/E005_external_baseline_transition/tools/verify_m25_conceptgraphs_docker_build.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M25_conceptgraphs_docker_build_preflight_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M25_conceptgraphs_docker_build_preflight_v0/verification/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M25_conceptgraphs_docker_build_preflight_v0/report.md`
- `logs/20260514_173224_e005_m25_conceptgraphs_docker_build.log`

사실:

- Status: `e005_m25_conceptgraphs_docker_build_job_launched`.
- Initial verification status: `e005_m25_conceptgraphs_docker_build_running`.
- tmux session: `e005_m25_conceptgraphs_docker_build`.
- Docker image: `research2/conceptgraphs-smoke:latest`.
- Build basis: Python 3.10 / PyTorch 2.0.1 / CUDA 11.8 / `Grounded-Segment-Anything` commit `a4d76a2b55e348943cba4cd57d7553c354296223`.
- Initial verifier did not run import smoke because the image is still building.

논문 주장:

- E005-M25 does not support a `ConceptGraphs` runtime or performance claim.
- E005-M25 supports only environment-build launch readiness for an external mapping baseline route.

에이전트 추론:

- The Dockerfile follows the official `ConceptGraphs` dependency family first, even though RTX 5090 runtime compatibility may require a later compatibility route.
- Import smoke and one-scan runtime smoke must remain separate so a dependency failure is not mistaken for a mapping-method failure.

사용자 판단 필요:

- None before E005-M26.

## E005-M26 ConceptGraphs Build Verification And Repair

Command:

```bash
python experiments/E005_external_baseline_transition/tools/verify_m25_conceptgraphs_docker_build.py
python experiments/E005_external_baseline_transition/tools/launch_m25_conceptgraphs_docker_build.py
```

사실:

- Initial verification status: `e005_m25_conceptgraphs_docker_build_failed`.
- Failure log: `logs/20260514_173224_e005_m25_conceptgraphs_docker_build.log`.
- Failure cause: `micromamba install` treated the direct `pytorch3d` tarball URL as a channel-style source and requested missing `noarch/repodata.json`.
- Bounded repair: split Dockerfile into base conda environment install plus `wget` tarball download and local package install.
- Relaunch log: `logs/20260514_222954_e005_m25_conceptgraphs_docker_build.log`.
- Second failure cause: `micromamba` also treated the local tarball path as a channel-style source and requested `/tmp/noarch/repodata.json`.
- Second bounded repair: manual-extract the official `pytorch3d` conda tarball into `/opt/conda` and immediately import `pytorch3d.ops`.
- Second relaunch log: `logs/20260514_224052_e005_m25_conceptgraphs_docker_build.log`.
- Third failure cause: manual `pytorch3d` extract passed, but `micromamba run -n base` exposed no `python` executable in the next Dockerfile step.
- Third bounded repair: create an explicit `conceptgraph` conda environment and use `/opt/conda/envs/conceptgraph/bin/python` for all pip/install/import smoke commands.
- Third relaunch log: `logs/20260514_225603_e005_m25_conceptgraphs_docker_build.log`.
- Fourth failure cause: `transformers==4.15.0` pulled an old `tokenizers` package that had to build from source under Python 3.10, but Rust compiler was missing.
- Fourth bounded repair: add `cargo` and `rustc` to the Docker image while keeping the official `ConceptGraphs` dependency family.
- Fourth relaunch log: `logs/20260514_233827_e005_m25_conceptgraphs_docker_build.log`.
- Fifth failure cause: Debian `cargo` was too old for a Rust 2024-edition crate while building old `tokenizers`.
- Fifth bounded repair: replace Debian `cargo` / `rustc` with stable Rust installed through `rustup`, while keeping the official `ConceptGraphs` dependency family.
- Fifth relaunch log: `logs/20260514_235454_e005_m25_conceptgraphs_docker_build.log`.
- Sixth failure cause: old `tokenizers` source hit Rust `invalid_reference_casting` deny-by-default lint under stable Rust.
- Sixth bounded repair: set `RUSTFLAGS="-A invalid_reference_casting"` for the Docker build, without changing the `ConceptGraphs` method code or baseline interface.
- Sixth relaunch log: `logs/20260515_000551_e005_m25_conceptgraphs_docker_build.log`.
- Seventh failure cause: old `tokenizers` passed after `RUSTFLAGS` repair, but repo clone failed because `/workspace` was not writable by `mambauser`.
- Seventh bounded repair: create `/workspace` as root and transfer ownership to `mambauser` before cloning the official repos.
- Seventh relaunch log: `logs/20260515_001217_e005_m25_conceptgraphs_docker_build.log`.
- Eighth failure cause: repo clone passed, but `chamferdist` metadata generation failed because `torch.utils.cpp_extension` could not import `pkg_resources` under `setuptools 82`.
- Eighth bounded repair: pin `setuptools==69.5.1` in the Docker image before installing source-built packages.
- Eighth relaunch log: `logs/20260515_001258_e005_m25_conceptgraphs_docker_build.log`.
- Ninth failure cause: `pkg_resources` repair passed, but `chamferdist` CUDA extension build failed because CUDA 11.7 rejected host `g++ 12.2.0`.
- Ninth bounded repair: install `gcc-11` / `g++-11` and pin `CC=/usr/bin/gcc-11`, `CXX=/usr/bin/g++-11` for source-built extensions.
- Ninth relaunch log: `logs/20260515_002915_e005_m25_conceptgraphs_docker_build.log`.
- Current verification status after ninth relaunch: `e005_m25_conceptgraphs_docker_build_running`.

논문 주장:

- E005-M26 still does not support a `ConceptGraphs` runtime or performance claim.
- This step only repairs build reproducibility for the external-baseline route.

에이전트 추론:

- This is an environment-packaging failure, not evidence against `ConceptGraphs` as a baseline.
- Completion verification should be rerun after the background build stops.

사용자 판단 필요:

- None before the next E005-M26 completion check.

## E005-M27 ConceptGraphs Runtime Smoke Contract

Implementation unit: `E005-M27_conceptgraphs_runtime_smoke_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/launch_m27_conceptgraphs_runtime_smoke.py
python experiments/E005_external_baseline_transition/tools/verify_m27_conceptgraphs_runtime_smoke.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/launch_m27_conceptgraphs_runtime_smoke.py`
- `experiments/E005_external_baseline_transition/tools/verify_m27_conceptgraphs_runtime_smoke.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M27_conceptgraphs_runtime_smoke_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M27_conceptgraphs_runtime_smoke_v0/docker_command.txt`
- `experiments/E005_external_baseline_transition/artifacts/E005-M27_conceptgraphs_runtime_smoke_v0/report.md`

사실:

- Status: `e005_m27_conceptgraphs_runtime_smoke_outputs_ready`.
- Blocker: none.
- Smoke scan: `ddc73795-765b-241a-9c5d-b97744afe077`.
- Staged frame payload: color/depth/pose `93/93/93`.
- Dataset config exists: true.
- SAM checkpoint exists: true.
- `GroundingDINO` checkpoint exists: true.
- Runtime command and expected output paths are recorded.
- GSA detection files: 19.
- Full PCD exists: true.
- Full PCD post exists: true.

논문 주장:

- E005-M27 supports one-scan `ConceptGraphs` runtime/output feasibility.
- It does not support a `ConceptGraphs` performance claim because query-level conversion and evaluation are separate gates.

에이전트 추론:

- The observed repair sequence was environment/adapter related, not evidence against the baseline method.
- Runtime smoke, output schema inspection, and query-level metric conversion should remain separate gates.

사용자 판단 필요:

- None before E005-M28/M29.

## E005-M28 ConceptGraphs Output Schema Inspection Contract

Implementation unit: `E005-M28_conceptgraphs_output_schema_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/inspect_m28_conceptgraphs_output_schema.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/inspect_m28_conceptgraphs_output_schema.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M28_conceptgraphs_output_schema_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M28_conceptgraphs_output_schema_v0/schema_summary.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M28_conceptgraphs_output_schema_v0/report.md`

사실:

- Status: `e005_m28_conceptgraphs_output_schema_ready`.
- `gsa_detections_none/*.pkl.gz` count: 19.
- Full PCD output exists: true.
- Full PCD post output exists: true.
- Full PCD raw object count: 146.
- Full PCD post object count: 6.

논문 주장:

- E005-M28 does not support a `ConceptGraphs` result claim.
- It only prepares the schema inspection gate needed before query-level metric conversion.

에이전트 추론:

- M28 confirms that geometry (`pcd_np`, `bbox_np`) and feature (`clip_ft`, `text_ft`) fields exist for conversion.
- M28 had to be run in the `ConceptGraphs` Docker image because host Python lacks `numpy` for pickle loading.

사용자 판단 필요:

- None before E005-M29/M30.

## E005-M29 ConceptGraphs Output-To-Query Conversion Plan

Implementation unit: `E005-M29_conceptgraphs_output_to_query_conversion_plan_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/plan_m29_conceptgraphs_output_to_query_conversion.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/plan_m29_conceptgraphs_output_to_query_conversion.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M29_conceptgraphs_output_to_query_conversion_plan_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M29_conceptgraphs_output_to_query_conversion_plan_v0/candidate_schema.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M29_conceptgraphs_output_to_query_conversion_plan_v0/conversion_contract.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M29_conceptgraphs_output_to_query_conversion_plan_v0/query_join_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M29_conceptgraphs_output_to_query_conversion_plan_v0/readiness_gates.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M29_conceptgraphs_output_to_query_conversion_plan_v0/report.md`

사실:

- Status: `e005_m29_conceptgraphs_output_to_query_conversion_plan_ready_with_clip_text_gate`.
- Smoke scan: `ddc73795-765b-241a-9c5d-b97744afe077`.
- Linked query rows: 1.
- Linked label: `pillow`.
- Map candidate export ready: true.
- Query join ready: true.
- Open-vocabulary semantic score ready: false.
- Query-level baseline result ready: false.

논문 주장:

- E005-M29 supports the conversion contract needed to fairly compare an external open-vocabulary mapping baseline.
- E005-M29 does not support a `ConceptGraphs` performance result.

에이전트 추론:

- Because M27 used `class_set none`, direct class-name ranking is not defensible.
- The next defensible gate is one-scan object candidate export plus CLIP-text scoring against `clip_ft`, without target identity before ranking.

사용자 판단 필요:

- None before E005-M30.

## E005-M20 ConceptGraphs Source/Interface Audit

Implementation unit: `E005-M20_conceptgraphs_interface_audit_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/plan_m20_conceptgraphs_interface_audit.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/plan_m20_conceptgraphs_interface_audit.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M20_conceptgraphs_interface_audit_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M20_conceptgraphs_interface_audit_v0/source_audit.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M20_conceptgraphs_interface_audit_v0/adapter_contract.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M20_conceptgraphs_interface_audit_v0/local_scan_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M20_conceptgraphs_interface_audit_v0/route_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M20_conceptgraphs_interface_audit_v0/report.md`

사실:

- Status: `e005_m20_conceptgraphs_interface_audit_ready_with_adapter_required`.
- Official repo: `https://github.com/concept-graphs/concept-graphs`.
- Checked head commit: `93277a02bd89171f8121e84203121cf7af9ebb5d`.
- License: `MIT`.
- `ConceptGraphs` route expects posed RGB-D sequences with color/depth/pose/intrinsic files and writes detection/map outputs as `.pkl.gz` artifacts.
- Local staged scans audited: 4.
- Local direct ConceptGraphs-ready scans: 0 / 4.
- Current local staged scans have color/depth/pose and `intrinsic_depth.txt`, but do not have `intrinsic_color.txt`.
- Selected route: `conceptgraphs_depth_aligned_scannet_smoke`.
- Next unit: `E005-M21 ConceptGraphs 3RScan staging materialization smoke`.

논문 주장:

- E005-M20 does not support a `ConceptGraphs` performance claim.
- E005-M20 supports only a source/interface and adapter feasibility claim.
- Final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.

에이전트 추론:

- `ConceptGraphs` is a defensible fallback because it is an open-vocabulary graph mapping baseline over posed RGB-D observations.
- The immediate route should create a separate `ConceptGraphs` staging root rather than mutating the existing `DualMap` staging root.
- The first smoke should use depth-aligned color images to avoid color/depth tensor mismatch; this is feasibility evidence, not final full-resolution performance evidence.

사용자 판단 필요:

- Resolved by E005-M21: materialize the `ConceptGraphs` staging root.

## E005-M21 ConceptGraphs Staging Materialization

Implementation unit: `E005-M21_conceptgraphs_staging_materialization_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/materialize_m21_conceptgraphs_staging_root.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/materialize_m21_conceptgraphs_staging_root.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M21_conceptgraphs_staging_materialization_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M21_conceptgraphs_staging_materialization_v0/materialization_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M21_conceptgraphs_staging_materialization_v0/verification_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M21_conceptgraphs_staging_materialization_v0/runtime_preflight_plan.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M21_conceptgraphs_staging_materialization_v0/stage_manifest.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M21_conceptgraphs_staging_materialization_v0/report.md`

사실:

- Status: `e005_m21_conceptgraphs_staging_materialized_smoke_ready`.
- Source root: `local_dataset/DualMap_staged/3rscan_scannet_exported/scannet/exported/`.
- Target root: `local_dataset/ConceptGraphs_staged/3rscan_depth_aligned_scannet/`.
- Dataset config: `local_dataset/ConceptGraphs_staged/3rscan_depth_aligned_scannet/config/conceptgraphs_3rscan_depth_aligned_scannet.yaml`.
- Materialized scans: 4 / 4.
- Total frames: 826.
- Color / depth / pose files: 826 / 826 / 826.
- Resolution-aligned scans: 4 / 4 at `224x172`.
- Runtime launched: false.

논문 주장:

- E005-M21 does not support a `ConceptGraphs` performance claim.
- E005-M21 supports only staging/materialization readiness for a later runtime smoke.
- Final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.

에이전트 추론:

- The `DualMap` staging root stays untouched; `ConceptGraphs` gets a separate depth-aligned staging root.
- E005-M22 should audit Docker/runtime feasibility before launching a long dependency-heavy run.

사용자 판단 필요:

- Resolved by E005-M22: fix the `ConceptGraphs` Docker/runtime preflight contract.

## E005-M22 ConceptGraphs Docker/Runtime Preflight

Implementation unit: `E005-M22_conceptgraphs_runtime_preflight_v0`.

Command:

```bash
python experiments/E005_external_baseline_transition/tools/plan_m22_conceptgraphs_runtime_preflight.py
```

Artifacts:

- `experiments/E005_external_baseline_transition/tools/plan_m22_conceptgraphs_runtime_preflight.py`
- `experiments/E005_external_baseline_transition/artifacts/E005-M22_conceptgraphs_runtime_preflight_v0/coverage.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M22_conceptgraphs_runtime_preflight_v0/host_preflight.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M22_conceptgraphs_runtime_preflight_v0/acquisition_plan.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M22_conceptgraphs_runtime_preflight_v0/runtime_contract.json`
- `experiments/E005_external_baseline_transition/artifacts/E005-M22_conceptgraphs_runtime_preflight_v0/dependency_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M22_conceptgraphs_runtime_preflight_v0/checkpoint_rows.jsonl`
- `experiments/E005_external_baseline_transition/artifacts/E005-M22_conceptgraphs_runtime_preflight_v0/report.md`

사실:

- Status: `e005_m22_conceptgraphs_runtime_preflight_ready_with_acquisition_required`.
- Docker ready: true.
- NVIDIA runtime detected: true.
- GPU: `NVIDIA GeForce RTX 5090`, free memory 24008 MiB at preflight.
- Staged scans ready: 4 / 4.
- `ConceptGraphs` repo present: false.
- `Grounded-Segment-Anything` repo present: false.
- `research2/conceptgraphs-smoke:latest` image present: false.
- `sam_vit_h_4b8939.pth` ready: true, reused from `OpenMask3D` checkpoint cache.
- `groundingdino_swint_ogc.pth` ready: false.
- First smoke variant: `class_set_none_sam_dense_smoke`.
- Runtime launched: false.

논문 주장:

- E005-M22 does not support a `ConceptGraphs` performance claim.
- E005-M22 supports only runtime preflight and acquisition planning.
- `ConceptGraphs` object-map baseline comparison still requires repo/checkpoint acquisition, Docker build, one-scan runtime smoke, and object-map schema inspection.
- Final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.

에이전트 추론:

- First smoke should use `class_set none` to avoid `RAM` / `LLaVA` before object-map feasibility is proven.
- `generate_gsa_results.py` still initializes `GroundingDINO` before `class_set` branching, so `groundingdino_swint_ogc.pth` is required unless we patch official source.
- The next step should be a background acquisition job with resumable downloads and timestamped logs.

사용자 판단 필요:

- None before E005-M23.
