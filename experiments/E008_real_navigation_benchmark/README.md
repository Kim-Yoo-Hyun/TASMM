# E008 Real Navigation Benchmark

Updated: 2026-05-30

## Status

E008 starts after E007-M07 packaged the occupancy-grid path-cost proxy table and selected `E008-M01 real navigation benchmark/source preflight and episode contract`. E008 is the first stage that prepares real navigation `SR` / `SPL` evidence. E008-M01 through E008-M45 are complete as source/adapter/contract/oracle-metric/candidate-source staging, rendered RGB-D detector route, leakage-safe goal evaluation, trajectory execution, H001 fallback execution, dynamic-stale overlay execution, M38 baseline-aligned result interpretation, M39 budget-matched repair/source-gap contract, M40 repaired row materialization, M41 repaired trajectory execution, M42 result interpretation/scale decision, M43 source-diverse policy redesign contract, M44 source-diverse row materialization, and M45 source-diverse trajectory execution contract/Docker preflight. M45 fixes a Docker-ready execution contract for `h001_task_conditioned_source_diverse_budget5_v1` and matched baselines because detector source-gap rows have full-candidate `SR` 1.0 but cap5 `SR` 0.0 under confidence order.

Next unit: E008-M46 source-diverse redesign trajectory execution smoke.

## Source Rule

- `/home/yoohyun/research3/local_dataset/data` is treated as an external read-only candidate source for `HM3D` / `ObjectNav` / `Habitat` preflight.
- Do not modify, decompress into, or write generated files under `/home/yoohyun/research3/local_dataset/data`.
- Store derived E008 bridge data under `/home/yoohyun/research2/local_dataset/HM3D_navigation_bridge/`.
- Store experiment reports and lightweight artifacts under `experiments/E008_real_navigation_benchmark/artifacts/`.

## E008 Contract

| Field | Required content |
| --- | --- |
| question | Can E007's proxy path-cost table be promoted toward real navigation `SR` / `SPL` without confusing proxy search evidence with executed navigation evidence? |
| hypothesis | A real navigation source should be selected only after scene files, navmesh files, episode files, Docker runtime, allowed inputs, metrics, and baseline rows are fixed. |
| dataset | First selected source is local read-only `HM3D` / `ObjectNav` data from `/home/yoohyun/research3/local_dataset/data`; `3RScan` remains a dynamic-memory/proxy source unless a simulator/navmesh adapter is built. |
| method | Define episode schema, candidate visit order interface, allowed/blocked inputs, and metric mapping from H001 policy rows to executed navigation episodes. |
| comparison | Static stale memory, detector-confidence ranking, `ConceptGraphs`-only map, task-agnostic memory trust, H001 task-conditioned memory trust, and H001 + `ConceptGraphs` fallback. |
| metrics | `SR`, `SPL`, path length, candidate visits, `ExpectedSearchCost`, `OldLocationDeadEndCostM`, failure type, and E007 proxy-to-execution consistency. |
| command | `python experiments/E008_real_navigation_benchmark/tools/plan_m01_navigation_source_episode_contract.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m02_hm3d_objectnav_adapter_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/plan_m03_h001_candidate_navigation_adapter.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m04_objectnav_oracle_path_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/plan_m05_hm3d_candidate_source_staging.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m06_hm3d_semantic_candidate_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/plan_m07_hm3d_rendered_rgbd_detector_source.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m08_hm3d_rendered_rgbd_frame_staging_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/verify_m09_hm3d_rendered_rgbd_detector_candidate_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m10_detector_candidate_navmesh_validation.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m11_detector_candidate_visit_order_path_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m12_detector_candidate_goal_evaluation_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/plan_m13_detector_goal_failure_audit.py`; `python experiments/E008_real_navigation_benchmark/tools/plan_m14_non_oracle_observation_coverage.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m15_non_oracle_observation_expansion_frame_staging.py`; `python experiments/E008_real_navigation_benchmark/tools/verify_m15_non_oracle_observation_expansion_frame_staging.py`; `python experiments/E008_real_navigation_benchmark/tools/verify_m16_non_oracle_observation_expansion_detector_candidate_smoke.py --require-ready`; `python experiments/E008_real_navigation_benchmark/tools/run_m17_expanded_detector_candidate_navmesh_validation.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m18_expanded_detector_candidate_visit_order_path_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m19_expanded_detector_candidate_goal_evaluation_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/plan_m20_expanded_detector_goal_failure_comparison_navigation_decision.py`; `python experiments/E008_real_navigation_benchmark/tools/plan_m21_expanded_detector_policy_trajectory_execution_contract.py`; `python experiments/E008_real_navigation_benchmark/tools/plan_m23_trajectory_proxy_consistency_h001_source_decision.py`; `python experiments/E008_real_navigation_benchmark/tools/plan_m24_h001_candidate_source_instantiation_contract.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m25_h001_candidate_source_materialization_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m26_h001_visit_order_path_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m27_h001_goal_evaluation_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/plan_m28_h001_goal_evaluation_comparison_trajectory_decision.py`; `python experiments/E008_real_navigation_benchmark/tools/plan_m29_h001_current_observation_fallback_source_repair.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m30_h001_current_observation_fallback_replay_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/plan_m31_h001_fallback_trajectory_contract_source_gap_boundary.py`; `docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp -v /home/yoohyun/research3/local_dataset/data:/data:ro -v /home/yoohyun/research2:/work -w /work research3/habitat-h001:20260508-calib-artifacts bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m32_h001_fallback_trajectory_execution_smoke.py --m31-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0 --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M32_h001_fallback_trajectory_execution_smoke_v0 --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M32_h001_fallback_trajectory_execution_smoke_v0"`; `python experiments/E008_real_navigation_benchmark/tools/plan_m33_h001_trajectory_result_interpretation_baseline_alignment.py`; `python experiments/E008_real_navigation_benchmark/tools/plan_m34_dynamic_stale_navigation_contract.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m35_dynamic_stale_overlay_materialization_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/plan_m36_dynamic_stale_overlay_trajectory_contract.py` |
| output | Source preflight rows, episode schema rows, metric contract rows, baseline contract rows, allowed/blocked input rows, candidate visit-order rows, route decision rows, next action rows, and report. |
| conclusion | E008-M01 selects `HM3D ObjectNav` + `Habitat` as the first real navigation source. E008-M02-M42 build and execute the detector/H001/dynamic-stale trajectory smoke chain with final navigation claims blocked. E008-M43 fixes source-diverse policy redesign because detector source-gap rows are recoverable in the full current candidate pool but not under confidence top-5. E008-M44 materializes 108 source-diverse execution plan rows and 468 candidate rows with policy leakage pass and budget cap compliance pass. E008-M45 fixes the Docker-ready trajectory contract and runner wrapper. E008-M46 must execute these rows before any broader scale-up decision. |

## Claim Boundary

- E008-M01 through E008-M45 do not claim final real navigation `SR` / `SPL`.
- E008-M01 through E008-M45 do not claim final real RGB-D/open-vocabulary robustness.
- E008-M01/M02/M03/M04/M05/M06/M07/M08/M09/M10/M11/M12/M13/M14/M15/M16/M17/M18/M19/M20/M21/M22/M23/M24/M25/M26/M27/M28/M29/M30/M31/M32/M33/M34/M35/M36/M37/M38/M39/M40/M41/M42/M43 do not make human intent a main contribution.
- E008-M33 explicitly blocks scaling the current H001 fallback trajectory as a main navigation result because it underperforms detector trajectories and lacks controlled stale-memory intervention.
- E008-M34 is a contract/design unit only; it does not produce trajectory results or dynamic-stale navigation performance.
- E008-M35 is an input materialization unit only; it does not produce trajectory results or dynamic-stale navigation performance.
- E008-M36 is a contract/runner-adaptation unit only; it does not execute trajectories or produce dynamic-stale navigation performance.
- E008-M37 executes a 6-episode counterfactual dynamic-stale overlay smoke; it does not support final real navigation `SR` / `SPL`.
- E008-M38 supports only result interpretation and baseline alignment; it recommends repair-before-scale and does not support a final H001 navigation claim.
- E008-M39 supports only a budget-matched policy/source-gap contract; it does not materialize repaired rows, execute trajectories, or support a final H001 navigation claim.
- E008-M40 supports only repaired row materialization; it does not execute trajectories or support final navigation improvement.
- E008-M41 executes repaired rows as a smoke test; it does not support final navigation improvement because H001 does not beat detector/fixed current top-k or task-agnostic memory trust on `SR`/`SPL`.
- E008-M42 supports result interpretation and scale decision only; it blocks scale-up and selects policy redesign before broader navigation reruns.
- E008-M43 supports policy redesign contract and M44 row plan only; it does not materialize rows, execute trajectories, or support final navigation improvement.
- E008-M44 supports source-diverse row materialization only; it does not execute trajectories or support final navigation improvement.
- E008-M45 supports trajectory execution contract and Docker preflight only; it does not execute trajectories or support final navigation improvement.
- `3RScan` / `3DSSG` remains the dynamic stale-memory source, but the first real navigation execution source is `HM3D ObjectNav` because local `Habitat` runtime and navmesh-backed scenes are available.
- Any `HM3D ObjectNav` result must be described as a navigation-source transfer/adapter experiment unless stale-memory state injection is explicitly implemented.

## E008-M01

Implementation unit: `E008-M01_navigation_source_episode_contract_v0`.

- Status: `e008_m01_navigation_source_episode_contract_ready`.
- Selected source: `hm3d_objectnav_habitat_local_research3`.
- Habitat image: `research3/habitat-h001:20260508-calib-artifacts`.
- Habitat import ready: true.
- `HM3D` total `.glb` files: 1,095.
- `HM3D` total `.navmesh` files: 910.
- `HM3D` minival `.navmesh` files: 10.
- `ObjectNav` `val_mini` content files: 2.
- `ObjectNav` `val_mini` parsed episode rows: 30.
- Real navigation `SR` / `SPL` ready: false.
- Full navigation execution launched: false.
- Selected next unit: E008-M02 `HM3D ObjectNav` episode/source adapter smoke.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m01_navigation_source_episode_contract.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M01_navigation_source_episode_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M01_navigation_source_episode_contract_v0/source_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M01_navigation_source_episode_contract_v0/episode_schema_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M01_navigation_source_episode_contract_v0/metric_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M01_navigation_source_episode_contract_v0/baseline_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M01_navigation_source_episode_contract_v0/input_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M01_navigation_source_episode_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M01_navigation_source_episode_contract_v0/next_action_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M01_navigation_source_episode_contract_v0/report.md`

## E008-M02

Implementation unit: `E008-M02_hm3d_objectnav_adapter_smoke_v0`.

- Status: `e008_m02_hm3d_objectnav_adapter_smoke_ready`.
- Sampled `ObjectNav val_mini` episode rows: 6.
- Unique `HM3D` scenes: 2.
- Scene/navmesh ready rows: 6 / 6.
- Docker `Habitat` scene smoke success: true.
- Loaded scenes: `00800-TEEsavR23oF`, `00802-wcojb4TFT35`.
- Real navigation `SR` / `SPL` ready: false.
- Full navigation execution launched: false.
- Selected next unit: E008-M03 `H001` candidate-to-navigation adapter contract.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m02_hm3d_objectnav_adapter_smoke.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M02_hm3d_objectnav_adapter_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M02_hm3d_objectnav_adapter_smoke_v0/docker_smoke_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M02_hm3d_objectnav_adapter_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M02_hm3d_objectnav_adapter_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M02_hm3d_objectnav_adapter_smoke_v0/episode_adapter_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M02_hm3d_objectnav_adapter_smoke_v0/scene_resolution_rows.jsonl`

## E008-M03

Implementation unit: `E008-M03_h001_candidate_navigation_adapter_contract_v0`.

- Status: `e008_m03_h001_candidate_navigation_adapter_contract_ready`.
- M02 episode rows: 6.
- Eval goal rows ready: 6 / 6.
- Candidate schema rows: 18.
- Input guard rows: 21.
- Policy adapter rows: 7.
- H001 candidate-source rows ready for `HM3D`: 0.
- `ObjectNav` oracle upper-bound smoke ready: true.
- H001 navigation policy execution ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M04 `ObjectNav` goal/viewpoint oracle path smoke.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m03_h001_candidate_navigation_adapter.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M03_h001_candidate_navigation_adapter_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M03_h001_candidate_navigation_adapter_contract_v0/candidate_schema_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M03_h001_candidate_navigation_adapter_contract_v0/input_guard_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M03_h001_candidate_navigation_adapter_contract_v0/policy_adapter_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M03_h001_candidate_navigation_adapter_contract_v0/candidate_source_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M03_h001_candidate_navigation_adapter_contract_v0/episode_goal_eval_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M03_h001_candidate_navigation_adapter_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M03_h001_candidate_navigation_adapter_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M03_h001_candidate_navigation_adapter_contract_v0/episode_goal_eval_rows.jsonl`

## E008-M04

Implementation unit: `E008-M04_objectnav_oracle_path_smoke_v0`.

- Status: `e008_m04_objectnav_oracle_path_smoke_ready`.
- Episode rows: 6.
- Viewpoint paths found: 6 / 6.
- Goal-snapped paths found: 4 / 6.
- Mean oracle viewpoint path length: 5.738806m.
- Mean goal snap distance: 0.902920m.
- Oracle metric plumbing ready: true.
- H001 navigation policy execution ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M05 `HM3D` candidate-source staging plan.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m04_objectnav_oracle_path_smoke.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M04_objectnav_oracle_path_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M04_objectnav_oracle_path_smoke_v0/oracle_path_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M04_objectnav_oracle_path_smoke_v0/metric_smoke_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M04_objectnav_oracle_path_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M04_objectnav_oracle_path_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M04_objectnav_oracle_path_smoke_v0/oracle_path_rows.jsonl`

## E008-M05

Implementation unit: `E008-M05_hm3d_candidate_source_staging_plan_v0`.

- Status: `e008_m05_hm3d_candidate_source_staging_plan_ready`.
- Episode rows: 6.
- `HM3D` semantic files ready: 2 / 2 scenes.
- Semantic category label support: 6 / 6 episode rows.
- Policy candidate source rows ready now: 0.
- Selected route: `hm3d_semantic_annotation_candidate_source_smoke`.
- Selected next unit: E008-M06 `HM3D` semantic annotation candidate-source smoke.
- H001 navigation policy execution ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Long job launched: false.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m05_hm3d_candidate_source_staging.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M05_hm3d_candidate_source_staging_plan_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M05_hm3d_candidate_source_staging_plan_v0/source_gap_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M05_hm3d_candidate_source_staging_plan_v0/semantic_scene_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M05_hm3d_candidate_source_staging_plan_v0/episode_category_support_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M05_hm3d_candidate_source_staging_plan_v0/candidate_source_route_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M05_hm3d_candidate_source_staging_plan_v0/selected_route_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M05_hm3d_candidate_source_staging_plan_v0/staging_input_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M05_hm3d_candidate_source_staging_plan_v0/blocked_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M05_hm3d_candidate_source_staging_plan_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M05_hm3d_candidate_source_staging_plan_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M05_hm3d_candidate_source_staging_plan_v0/coverage.json`

## E008-M06

Implementation unit: `E008-M06_hm3d_semantic_candidate_source_smoke_v0`.

- Status: `e008_m06_hm3d_semantic_candidate_source_smoke_ready_blocked_coordinate_extraction`.
- Episode rows: 6.
- Semantic label support rows ready: 6 / 6.
- Habitat semantic nonzero-AABB scenes: 0 / 2.
- GLB semantic geometry mapping scenes ready: 0 / 2.
- Candidate rows ready: 0.
- H001 navigation policy execution ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Selected next unit: E008-M07 `HM3D` rendered RGB-D detector candidate-source plan.
- Long job launched: false.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m06_hm3d_semantic_candidate_smoke.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M06_hm3d_semantic_candidate_source_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M06_hm3d_semantic_candidate_source_smoke_v0/semantic_label_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M06_hm3d_semantic_candidate_source_smoke_v0/habitat_semantic_aabb_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M06_hm3d_semantic_candidate_source_smoke_v0/semantic_glb_geometry_probe_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M06_hm3d_semantic_candidate_source_smoke_v0/candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M06_hm3d_semantic_candidate_source_smoke_v0/candidate_blocker_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M06_hm3d_semantic_candidate_source_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M06_hm3d_semantic_candidate_source_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M06_hm3d_semantic_candidate_source_smoke_v0/coverage.json`

## E008-M07

Implementation unit: `E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0`.

- Status: `e008_m07_hm3d_rendered_rgbd_detector_candidate_source_plan_ready`.
- Episode rows: 6.
- Render plan rows: 24.
- Detector manifest rows: 6.
- Detector labels: 5 (`bed`, `chair`, `monitor`, `television`, `tv`).
- Render strategy: `episode_start_pose_fixed_yaw_sweep`.
- Yaw offsets: 0, 90, 180, 270 degrees.
- `Habitat` image ready: true.
- `real-smoke` detector image ready: true.
- H001 navigation policy execution ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Selected next unit: E008-M08 `HM3D` rendered RGB-D frame staging smoke.
- Long job launched: false.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m07_hm3d_rendered_rgbd_detector_source.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0/render_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0/real_proposal_query_manifest.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0/real_proposal_object_targets.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0/prompt_set.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0/candidate_output_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0/blocked_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0/detector_run_command_plan.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0/coverage.json`

## E008-M08

Implementation unit: `E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0`.

- Status: `e008_m08_hm3d_rendered_rgbd_frame_staging_smoke_ready`.
- Render plan rows: 24.
- Rendered frame rows: 24.
- Ready frame rows: 24 / 24.
- Ready scan rows: 6 / 6.
- Detector manifest rows: 6.
- Detector input files ready: true.
- Output layout: `local_dataset/HM3D_navigation_bridge/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0/3RScan/scans/<scan_id>/sequence/`.
- Files per staged scan: `_info.txt`, `frame-000000..000003.color.jpg`, `frame-000000..000003.depth.pgm`, `frame-000000..000003.pose.txt`.
- H001 navigation policy execution ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Selected next unit: E008-M09 `HM3D` rendered RGB-D detector candidate smoke.
- Long job launched: false.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m08_hm3d_rendered_rgbd_frame_staging_smoke.py
python experiments/E008_real_navigation_benchmark/tools/verify_m08_hm3d_rendered_rgbd_frame_staging.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0/verification_coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0/verification_frame_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0/verification_scan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0/docker_render_meta.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0/detector_inputs/real_proposal_query_manifest.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0/detector_inputs/real_proposal_object_targets.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0/detector_inputs/prompt_set.json`
- `local_dataset/HM3D_navigation_bridge/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0/detector_inputs/proposal_output_schema.json`

## E008-M09

Implementation unit: `E008-M09_hm3d_rendered_rgbd_detector_candidate_smoke_v0`.

- Status: `e008_m09_hm3d_rendered_rgbd_detector_candidate_smoke_ready`.
- tmux session: `e008_m09_hm3d_rgbd_detector`.
- Log: `logs/20260527_200722_e008_m09_hm3d_rgbd_detector.log`.
- Output root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M09_hm3d_rendered_rgbd_detector_candidate_smoke_v0/`.
- Input dataset root: `local_dataset/HM3D_navigation_bridge/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0/`.
- Input manifest: `local_dataset/HM3D_navigation_bridge/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0/detector_inputs/real_proposal_query_manifest.jsonl`.
- E003 detector status: `pre_cap_candidate_pool_export_smoke_ready`.
- Frame rows: 24.
- Raw / written predictions: 441 / 137.
- Prediction rows: 137.
- Coordinate candidate rows: 137.
- Pre-cap candidate rows: 409.
- Evaluated scans: 6.
- Validator errors / warnings: 0 / 0.
- Matching status: `detector_matching_smoke_ready`.
- Matching note: `ObjectNav` goal/viewpoint fields are blocked, so E008-M09 does not evaluate target recall; matching target rows are 0 by design.
- H001 navigation policy execution ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Selected next unit: E008-M10 detector candidate coordinate-frame and snap-to-navmesh validation.

Launch command:

```bash
tmux new-session -d -s e008_m09_hm3d_rgbd_detector \
  'cd /home/yoohyun/research2 && python experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py \
  --dataset-root /home/yoohyun/research2/local_dataset/HM3D_navigation_bridge/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0 \
  --m17-dir /home/yoohyun/research2/local_dataset/HM3D_navigation_bridge/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0/detector_inputs \
  --out-dir /home/yoohyun/research2/experiments/E008_real_navigation_benchmark/artifacts/E008-M09_hm3d_rendered_rgbd_detector_candidate_smoke_v0 \
  --max-scans 6 --max-frames-per-scan 4 --max-labels 5 \
  --max-predictions 12000 --max-predictions-per-frame 100 \
  --threshold 0.08 --text-threshold 0.08 \
  --candidate-selection-policy cap_aware_label_balanced_ranking_v0 \
  --selection-score-mode confidence_log_depth \
  --pre-cap-per-scan-label-cap 24 \
  --pre-cap-spatial-consolidation-radius-m 0.5 \
  --raw-candidate-collection-cap 50000 \
  --export-pre-cap-candidate-pool > logs/20260527_200722_e008_m09_hm3d_rgbd_detector.log 2>&1'
```

Verification command:

```bash
python experiments/E008_real_navigation_benchmark/tools/verify_m09_hm3d_rendered_rgbd_detector_candidate_smoke.py
python experiments/E008_real_navigation_benchmark/tools/verify_m09_hm3d_rendered_rgbd_detector_candidate_smoke.py --require-ready
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M09_hm3d_rendered_rgbd_detector_candidate_smoke_v0/e008_m09_verification_coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M09_hm3d_rendered_rgbd_detector_candidate_smoke_v0/e008_m09_candidate_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M09_hm3d_rendered_rgbd_detector_candidate_smoke_v0/e008_m09_route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M09_hm3d_rendered_rgbd_detector_candidate_smoke_v0/e008_m09_verification_report.md`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M09_hm3d_rendered_rgbd_detector_candidate_smoke_v0/container_output/real_proposals.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M09_hm3d_rendered_rgbd_detector_candidate_smoke_v0/container_output/pre_cap_candidate_pool.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M09_hm3d_rendered_rgbd_detector_candidate_smoke_v0/validator/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M09_hm3d_rendered_rgbd_detector_candidate_smoke_v0/matching/coverage.json`

## E008-M10

Implementation unit: `E008-M10_detector_candidate_navmesh_validation_v0`.

- Status: `e008_m10_detector_candidate_navmesh_validation_ready_with_path_warnings`.
- Input proposal rows: 137.
- Frame/scene join-ready rows: 137 / 137.
- Coordinate-valid rows: 137 / 137.
- Source navigable rows: 137 / 137.
- Centroid navigable rows: 0 / 137.
- Snapped navigable rows: 136 / 137.
- Source-to-snapped path found rows: 125 / 137.
- Candidate usable for path smoke rows: 125 / 137.
- Mean / P90 snap distance: 1.032252m / 1.641360m.
- Navmesh validation status counts: `candidate_path_ready` 125, `blocked_snapped_point_unreachable_from_episode_start` 11, `blocked_snap_failed_non_finite` 1.
- Coordinate-frame snap ready: true.
- Path reachability ready with warnings: true.
- H001 navigation policy execution ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Selected next unit: E008-M11 reachable-subset detector candidate visit-order path smoke.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m10_detector_candidate_navmesh_validation.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M10_detector_candidate_navmesh_validation_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M10_detector_candidate_navmesh_validation_v0/candidate_navmesh_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M10_detector_candidate_navmesh_validation_v0/candidate_navmesh_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M10_detector_candidate_navmesh_validation_v0/scan_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M10_detector_candidate_navmesh_validation_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M10_detector_candidate_navmesh_validation_v0/docker_navmesh_meta.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M10_detector_candidate_navmesh_validation_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M10_detector_candidate_navmesh_validation_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M10_detector_candidate_navmesh_validation_v0/candidate_navmesh_rows.jsonl`

## E008-M11

Implementation unit: `E008-M11_detector_candidate_visit_order_path_smoke_v0`.

- Status: `e008_m11_detector_candidate_visit_order_path_smoke_ready`.
- Input M10 candidate rows: 137.
- Query-compatible candidate rows: 137.
- Path-ready candidate rows: 125 / 137.
- Failure rows retained for policy accounting: 12.
- Failure status counts: `blocked_snapped_point_unreachable_from_episode_start` 11, `blocked_snap_failed_non_finite` 1.
- Policies evaluated: 4.
- Visit-order rows: 512.
- Policy metric rows: 28.
- `detector_confidence_all_candidates_v0`: top1 path-ready scans 5 / 6, blocked ranked rows 12, mean first-ready cost 4.355265m, mean top5 known cost 14.136482m.
- `detector_confidence_reachable_subset_v0`: top1 path-ready scans 6 / 6, mean first-ready cost 4.355265m, mean top5 known cost 15.470477m.
- `path_cost_ascending_reachable_subset_v0`: top1 path-ready scans 6 / 6, mean first-ready cost 0.791484m, mean top5 known cost 6.513382m.
- `confidence_path_cost_tradeoff_reachable_subset_v0`: top1 path-ready scans 6 / 6, mean first-ready cost 1.381810m, mean top5 known cost 10.237169m.
- Eval-only `ObjectNav` goal/viewpoint used for policy: false.
- H001 navigation policy execution ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Selected next unit: E008-M12 leakage-safe detector candidate goal-evaluation smoke.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m11_detector_candidate_visit_order_path_smoke.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M11_detector_candidate_visit_order_path_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M11_detector_candidate_visit_order_path_smoke_v0/candidate_visit_order_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M11_detector_candidate_visit_order_path_smoke_v0/policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M11_detector_candidate_visit_order_path_smoke_v0/failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M11_detector_candidate_visit_order_path_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M11_detector_candidate_visit_order_path_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M11_detector_candidate_visit_order_path_smoke_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M11_detector_candidate_visit_order_path_smoke_v0/candidate_visit_order_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M11_detector_candidate_visit_order_path_smoke_v0/policy_metric_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M11_detector_candidate_visit_order_path_smoke_v0/failure_rows.jsonl`

## E008-M12

Implementation unit: `E008-M12_detector_candidate_goal_evaluation_smoke_v0`.

- Status: `e008_m12_detector_candidate_goal_evaluation_smoke_ready_with_limited_proxy_success`.
- Input M11 candidate visit-order rows: 512.
- Candidate-goal eval rows: 512.
- Scan-policy metric rows: 24.
- Aggregate policy rows: 4.
- Eval-only `ObjectNav` all-viewpoint rows loaded: 6 / 6 episodes.
- Primary eval metric: `any_viewpoint_xz_1p0`.
- Leakage audit pass: true.
- Eval-only `ObjectNav` goal/viewpoint used for policy: false.
- Eval-only `ObjectNav` goal/viewpoint used for metric: true.
- Primary `GoalEvalProxySR`:
  - `detector_confidence_all_candidates_v0`: 3 / 6, proxy `SPL` 0.189695, mean first-hit rank 4.666667.
  - `detector_confidence_reachable_subset_v0`: 3 / 6, proxy `SPL` 0.189695, mean first-hit rank 4.666667.
  - `confidence_path_cost_tradeoff_reachable_subset_v0`: 3 / 6, proxy `SPL` 0.224124, mean first-hit rank 8.666667.
  - `path_cost_ascending_reachable_subset_v0`: 3 / 6, proxy `SPL` 0.356196, mean first-hit rank 9.333333.
- `goal_xz_1p0` proxy success: 1 / 6 for all 4 policies.
- H001 navigation policy execution ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Selected next unit: E008-M13 detector-goal failure audit and observation-coverage expansion decision.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m12_detector_candidate_goal_evaluation_smoke.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M12_detector_candidate_goal_evaluation_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M12_detector_candidate_goal_evaluation_smoke_v0/candidate_goal_eval_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M12_detector_candidate_goal_evaluation_smoke_v0/policy_goal_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M12_detector_candidate_goal_evaluation_smoke_v0/failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M12_detector_candidate_goal_evaluation_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M12_detector_candidate_goal_evaluation_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M12_detector_candidate_goal_evaluation_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M12_detector_candidate_goal_evaluation_smoke_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M12_detector_candidate_goal_evaluation_smoke_v0/candidate_goal_eval_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M12_detector_candidate_goal_evaluation_smoke_v0/policy_goal_metric_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M12_detector_candidate_goal_evaluation_smoke_v0/failure_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M12_detector_candidate_goal_evaluation_smoke_v0/leakage_audit_rows.jsonl`

## E008-M13

Implementation unit: `E008-M13_detector_goal_failure_audit_v0`.

- Status: `e008_m13_detector_goal_failure_audit_ready_observation_expansion_selected`.
- Input M12 status: `e008_m12_detector_candidate_goal_evaluation_smoke_ready_with_limited_proxy_success`.
- Episode audit rows: 6.
- Policy failure audit rows: 12.
- Episodes failing all policies under `any_viewpoint_xz_1p0`: 3 / 6.
- Failure classes: `target_region_missing_in_precap_detector_pool` 2, `near_miss_localization_threshold` 1, `not_primary_failure` 3.
- Post-cap or snap suppression failure rows: 0.
- Mean failed pre-cap best any-viewpoint XZ distance: 2.614360m.
- Mean failed M12 snapped best any-viewpoint XZ distance: 2.635818m.
- Eval-only `ObjectNav` goal/viewpoint used for policy: false.
- Eval-only `ObjectNav` goal/viewpoint used for audit: true.
- Selected route: `bounded_start_neighborhood_multiview_v0`.
- Selected next unit: E008-M14 non-oracle observation-coverage expansion plan.
- H001 navigation policy execution ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Long job launched: false.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m13_detector_goal_failure_audit.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M13_detector_goal_failure_audit_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M13_detector_goal_failure_audit_v0/episode_failure_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M13_detector_goal_failure_audit_v0/precap_final_coverage_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M13_detector_goal_failure_audit_v0/policy_failure_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M13_detector_goal_failure_audit_v0/coverage_expansion_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M13_detector_goal_failure_audit_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M13_detector_goal_failure_audit_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M13_detector_goal_failure_audit_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M13_detector_goal_failure_audit_v0/episode_failure_audit_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M13_detector_goal_failure_audit_v0/precap_final_coverage_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M13_detector_goal_failure_audit_v0/policy_failure_audit_rows.jsonl`

## E008-M14

Implementation unit: `E008-M14_non_oracle_observation_coverage_plan_v0`.

- Status: `e008_m14_non_oracle_observation_coverage_plan_ready`.
- Input M13 status: `e008_m13_detector_goal_failure_audit_ready_observation_expansion_selected`.
- Episode rows: 6.
- Observation pose rows: 54.
- Expanded render plan rows: 216.
- Frames per episode: 36.
- Pose types: `start_pose` 6, `local_shell_pose` 48.
- Local shell radii: 1.5m, 3.0m.
- Local shell bearings: 0, 90, 180, 270 degrees.
- Yaw offsets per pose: 0, 90, 180, 270 degrees.
- Detector manifest rows: 6.
- Object target rows: 10.
- Prompt label count: 5.
- Selected route: `bounded_start_neighborhood_multiview_v0`.
- Uses `ObjectNav` eval goal/viewpoint for policy: false.
- Uses eval failure labels to select episode subset: false.
- Requires M15 navmesh snap validation: true.
- Requires M15 frame staging: true.
- Requires detector rerun after M15: true.
- H001 navigation policy execution ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Long job launched: false.
- Selected next unit: E008-M15 non-oracle observation expansion frame staging smoke.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m14_non_oracle_observation_coverage.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M14_non_oracle_observation_coverage_plan_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M14_non_oracle_observation_coverage_plan_v0/observation_pose_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M14_non_oracle_observation_coverage_plan_v0/expanded_render_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M14_non_oracle_observation_coverage_plan_v0/expanded_detector_manifest_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M14_non_oracle_observation_coverage_plan_v0/expanded_real_proposal_object_targets.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M14_non_oracle_observation_coverage_plan_v0/coverage_route_policy_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M14_non_oracle_observation_coverage_plan_v0/input_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M14_non_oracle_observation_coverage_plan_v0/next_action_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M14_non_oracle_observation_coverage_plan_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M14_non_oracle_observation_coverage_plan_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M14_non_oracle_observation_coverage_plan_v0/observation_pose_plan_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M14_non_oracle_observation_coverage_plan_v0/expanded_render_plan_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M14_non_oracle_observation_coverage_plan_v0/expanded_detector_manifest_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M14_non_oracle_observation_coverage_plan_v0/expanded_real_proposal_object_targets.jsonl`

## E008-M15

Implementation unit: `E008-M15_non_oracle_observation_expansion_frame_staging_v0`.

- Status: `e008_m15_non_oracle_observation_expansion_frame_staging_smoke_ready`.
- Verification status: `e008_m15_non_oracle_observation_expansion_frame_staging_verified_with_snap_warnings`.
- Input M14 status: `e008_m14_non_oracle_observation_coverage_plan_ready`.
- Render plan rows: 216.
- Rendered frame rows: 216.
- Ready frame rows: 216.
- Ready scan rows: 6 / 6.
- Detector manifest rows: 6.
- Detector input files ready: true.
- Snap validation rows: 216.
- Snap required rows: 192.
- Snap-ready rows: 216.
- Large snap warning rows: 8.
- Mean snap distance: 0.421799m.
- Max snap distance: 3.485701m.
- Uses `ObjectNav` eval goal/viewpoint for policy: false.
- H001 navigation policy execution ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Long job launched: false.
- Selected next unit: E008-M16 non-oracle observation expansion detector candidate smoke.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m15_non_oracle_observation_expansion_frame_staging.py
python experiments/E008_real_navigation_benchmark/tools/verify_m15_non_oracle_observation_expansion_frame_staging.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M15_non_oracle_observation_expansion_frame_staging_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M15_non_oracle_observation_expansion_frame_staging_v0/verification_coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M15_non_oracle_observation_expansion_frame_staging_v0/verification_frame_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M15_non_oracle_observation_expansion_frame_staging_v0/verification_scan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M15_non_oracle_observation_expansion_frame_staging_v0/verification_issue_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M15_non_oracle_observation_expansion_frame_staging_v0/detector_input_copy_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M15_non_oracle_observation_expansion_frame_staging_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M15_non_oracle_observation_expansion_frame_staging_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M15_non_oracle_observation_expansion_frame_staging_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M15_non_oracle_observation_expansion_frame_staging_v0/render_inputs/render_plan_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M15_non_oracle_observation_expansion_frame_staging_v0/rendered_frame_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M15_non_oracle_observation_expansion_frame_staging_v0/snap_validation_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M15_non_oracle_observation_expansion_frame_staging_v0/detector_inputs/real_proposal_query_manifest.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M15_non_oracle_observation_expansion_frame_staging_v0/detector_inputs/real_proposal_object_targets.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M15_non_oracle_observation_expansion_frame_staging_v0/detector_inputs/prompt_set.json`
- `local_dataset/HM3D_navigation_bridge/E008-M15_non_oracle_observation_expansion_frame_staging_v0/detector_inputs/proposal_output_schema.json`

## E008-M16

Implementation unit: `E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0`.

- Status: `e008_m16_non_oracle_observation_expansion_detector_candidate_smoke_ready`.
- Launcher status: `e008_m16_detector_candidate_smoke_launched`.
- tmux session: `e008_m16_hm3d_expanded_detector`.
- Log: `logs/20260528_161152_e008_m16_hm3d_expanded_detector.log`.
- Output root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0/`.
- Input dataset root: `local_dataset/HM3D_navigation_bridge/E008-M15_non_oracle_observation_expansion_frame_staging_v0/`.
- M16 detector input manifest: `experiments/E008_real_navigation_benchmark/artifacts/E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0/detector_inputs/real_proposal_query_manifest.jsonl`.
- Detector input manifest rows: 6.
- Repaired sampled frame indices: 216.
- Target rows: 10.
- Frame rows: 216.
- Frames with written predictions: 145.
- Raw predictions: 4,009.
- Prediction rows: 214.
- Coordinate candidate rows: 214.
- Pre-cap candidate rows: 3,801.
- Validator errors / warnings: 0 / 0.
- Initial failure note: first launch used copied M15 detector inputs without `sampled_frame_indices`, so the detector runner scanned 0 frames. The M16 launcher now materializes an explicit M16 detector input directory before launch.
- Verification status: completed.
- Selected next unit: E008-M17 expanded detector candidate navmesh validation.
- H001 navigation policy execution ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.

Launch command:

```bash
python experiments/E008_real_navigation_benchmark/tools/launch_m16_non_oracle_observation_expansion_detector.py --force
```

Verification command:

```bash
python experiments/E008_real_navigation_benchmark/tools/verify_m16_non_oracle_observation_expansion_detector_candidate_smoke.py --require-ready
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0/e008_m16_launch_coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0/long_job_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0/detector_inputs/real_proposal_query_manifest.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0/detector_inputs/real_proposal_object_targets.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0/detector_inputs/prompt_set.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0/detector_inputs/proposal_output_schema.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0/e008_m16_verification_coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0/container_output/real_proposals.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0/container_output/pre_cap_candidate_pool.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0/container_output/model_smoke.json`

## E008-M17

Implementation unit: `E008-M17_expanded_detector_candidate_navmesh_validation_v0`.

- Status: `e008_m17_expanded_detector_candidate_navmesh_validation_ready_with_path_warnings`.
- Input M16 status: `e008_m16_non_oracle_observation_expansion_detector_candidate_smoke_ready`.
- Candidate rows: 214.
- Join-ready rows: 214 / 214.
- Coordinate-valid rows: 214 / 214.
- Source navigable rows: 214 / 214.
- Snapped navigable rows: 213 / 214.
- Source-to-snapped path found rows: 189 / 214.
- Source-to-snapped path found rate: 0.883178.
- Candidate usable for path smoke rows: 189.
- Every scan has path-ready candidate: true.
- Navmesh status counts: `candidate_path_ready` 189 / `blocked_snapped_point_unreachable_from_episode_start` 24 / `blocked_snap_failed_non_finite` 1.
- Source basis: E008-M15 `snap_validation_rows.render_position_m`; this avoids treating unsnapped render-plan local shell poses as policy start points.
- Selected next unit: E008-M18 expanded detector candidate visit-order path smoke.
- H001 navigation policy execution ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m17_expanded_detector_candidate_navmesh_validation.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M17_expanded_detector_candidate_navmesh_validation_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M17_expanded_detector_candidate_navmesh_validation_v0/candidate_navmesh_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M17_expanded_detector_candidate_navmesh_validation_v0/scan_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M17_expanded_detector_candidate_navmesh_validation_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M17_expanded_detector_candidate_navmesh_validation_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M17_expanded_detector_candidate_navmesh_validation_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M17_expanded_detector_candidate_navmesh_validation_v0/candidate_navmesh_rows.jsonl`

## E008-M18

Implementation unit: `E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0`.

- Status: `e008_m18_expanded_detector_candidate_visit_order_path_smoke_ready`.
- Input M17 status: `e008_m17_expanded_detector_candidate_navmesh_validation_ready_with_path_warnings`.
- Input candidate rows: 214.
- Query-compatible candidate rows: 214.
- Path-ready candidate rows: 189 / 214.
- Failure rows retained for policy accounting: 25.
- Visit-order rows: 781.
- Policy metric rows: 28.
- Policy count: 4.
- Reachable-subset top1-ready scans: 6 / 6.
- `ObjectNav` eval goal/viewpoint fields used for policy: false.
- Selected next unit: E008-M19 expanded leakage-safe detector candidate goal-evaluation smoke.
- H001 navigation policy execution ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.

Policy aggregate:

| policy_id | ranked rows | path-ready rows | blocked rows | top1-ready scans | mean first-ready cost m | mean top5 known cost m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `detector_confidence_all_candidates_v0` | 214 | 189 | 25 | 5 | 1.648578 | 11.152889 |
| `detector_confidence_reachable_subset_v0` | 189 | 189 | 0 | 6 | 1.648578 | 12.662480 |
| `path_cost_ascending_reachable_subset_v0` | 189 | 189 | 0 | 6 | 0.153562 | 1.978676 |
| `confidence_path_cost_tradeoff_reachable_subset_v0` | 189 | 189 | 0 | 6 | 0.224944 | 3.038404 |

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m18_expanded_detector_candidate_visit_order_path_smoke.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0/candidate_visit_order_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0/policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0/failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0/candidate_visit_order_rows.jsonl`

## E008-M19

Implementation unit: `E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0`.

- Status: `e008_m19_expanded_detector_candidate_goal_evaluation_smoke_ready`.
- Input M18 status: `e008_m18_expanded_detector_candidate_visit_order_path_smoke_ready`.
- Candidate-goal eval rows: 781.
- Scan-policy rows: 24.
- Aggregate policy rows: 4.
- Primary eval metric: `any_viewpoint_xz_1p0`.
- Primary proxy hit rows: 6 / 6 for all 4 policies.
- `goal_xz_1p0` proxy hit rows: 4 / 6 for all 4 policies.
- Primary failure rows: 0.
- Leakage audit pass: true.
- `ObjectNav` eval goal/viewpoint fields used for policy: false.
- Selected next unit: E008-M20 expanded detector-goal failure comparison and navigation-execution decision.
- H001 navigation policy execution ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.

Policy aggregate:

| policy_id | primary hits | primary proxy SR | primary proxy SPL | mean hit rank | any-vp 1.5m proxy SR | goal 1.0m proxy SR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `detector_confidence_all_candidates_v0` | 6/6 | 1.000000 | 0.456966 | 13.000000 | 1.000000 | 0.666667 |
| `detector_confidence_reachable_subset_v0` | 6/6 | 1.000000 | 0.456966 | 10.500000 | 1.000000 | 0.666667 |
| `path_cost_ascending_reachable_subset_v0` | 6/6 | 1.000000 | 0.535389 | 20.333333 | 1.000000 | 0.666667 |
| `confidence_path_cost_tradeoff_reachable_subset_v0` | 6/6 | 1.000000 | 0.374943 | 18.166667 | 1.000000 | 0.666667 |

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m19_expanded_detector_candidate_goal_evaluation_smoke.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0/candidate_goal_eval_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0/policy_goal_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0/failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0/candidate_goal_eval_rows.jsonl`

## E008-M20

Implementation unit: `E008-M20_expanded_detector_goal_failure_comparison_navigation_decision_v0`.

- Status: `e008_m20_expanded_detector_goal_failure_comparison_navigation_decision_ready`.
- M12 primary failure rows: 12.
- M19 primary failure rows: 0.
- Episodes with resolved primary proxy failures: 3.
- Policies with 6/6 primary proxy success after expansion: 4 / 4.
- Gate status counts: pass 3 / warning 4 / fail 2.
- Key pass gates: leakage-safe goal evaluation, expanded goal proxy coverage, path-ready candidates.
- Key warning gates: object-center proxy, path warning accounting, rank/cost warning accounting, scale.
- Key fail gates: H001 navigation candidate sources, trajectory execution metrics.
- Selected next unit: E008-M21 expanded detector-policy trajectory execution contract and Docker preflight.
- H001 navigation policy execution ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m20_expanded_detector_goal_failure_comparison_navigation_decision.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M20_expanded_detector_goal_failure_comparison_navigation_decision_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M20_expanded_detector_goal_failure_comparison_navigation_decision_v0/policy_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M20_expanded_detector_goal_failure_comparison_navigation_decision_v0/scan_comparison_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M20_expanded_detector_goal_failure_comparison_navigation_decision_v0/episode_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M20_expanded_detector_goal_failure_comparison_navigation_decision_v0/navigation_readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M20_expanded_detector_goal_failure_comparison_navigation_decision_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M20_expanded_detector_goal_failure_comparison_navigation_decision_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M20_expanded_detector_goal_failure_comparison_navigation_decision_v0/coverage.json`

## E008-M21

Implementation unit: `E008-M21_expanded_detector_policy_trajectory_execution_contract_v0`.

- Status: `e008_m21_expanded_detector_policy_trajectory_execution_contract_ready_runner_missing`.
- Trajectory execution contract ready: true.
- Docker/data preflight ready: true.
- Docker preflight status counts: pass 6 / warning 1.
- Policy execution contracts: 4.
- Policy execution plan rows: 24.
- Candidate visit-order rows under contract: 781.
- Candidate navmesh rows under contract: 214.
- Blocked eval policy fields: 9.
- M22 runner implemented: false.
- Selected next unit: E008-M22 expanded detector-policy trajectory execution runner scaffold.
- H001 navigation policy execution ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m21_expanded_detector_policy_trajectory_execution_contract.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M21_expanded_detector_policy_trajectory_execution_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M21_expanded_detector_policy_trajectory_execution_contract_v0/execution_input_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M21_expanded_detector_policy_trajectory_execution_contract_v0/policy_execution_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M21_expanded_detector_policy_trajectory_execution_contract_v0/trajectory_policy_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M21_expanded_detector_policy_trajectory_execution_contract_v0/trajectory_metric_schema_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M21_expanded_detector_policy_trajectory_execution_contract_v0/runner_output_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M21_expanded_detector_policy_trajectory_execution_contract_v0/docker_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M21_expanded_detector_policy_trajectory_execution_contract_v0/docker_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M21_expanded_detector_policy_trajectory_execution_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M21_expanded_detector_policy_trajectory_execution_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M21_expanded_detector_policy_trajectory_execution_contract_v0/coverage.json`

## E008-M22

Implementation unit: `E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0`.

- Status: `e008_m22_expanded_detector_policy_trajectory_execution_smoke_ready_h001_blocked`.
- Trajectory execution rows: 372.
- Scan-policy metric rows: 24.
- Aggregate policy metric rows: 4.
- Trajectory failure rows: 15.
- Leakage audit pass: true.
- Detector-policy smoke `SR`: 1.0 for 4 / 4 policies over 6 episodes.
- Aggregate `SPL` range: 0.303595-0.410800.
- Best aggregate `SPL`: `detector_confidence_all_candidates_v0` and `detector_confidence_reachable_subset_v0` at 0.410800.
- Real navigation `SR` / `SPL` smoke rows ready: true.
- Final real navigation `SR` / `SPL` ready: false.
- H001 navigation policy execution ready: false.
- Selected next unit: E008-M23 trajectory-vs-proxy consistency and H001 candidate-source decision.

Command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp \
  -v /home/yoohyun/research3/local_dataset/data:/data:ro \
  -v /home/yoohyun/research2:/work \
  -w /work \
  research3/habitat-h001:20260508-calib-artifacts \
  bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m22_expanded_detector_policy_trajectory_execution_smoke.py --m21-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M21_expanded_detector_policy_trajectory_execution_contract_v0 --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0 --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0"
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0/trajectory_attempt_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0/trajectory_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0/trajectory_failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0/scene_execution_meta.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0/coverage.json`

## E008-M23

Implementation unit: `E008-M23_trajectory_proxy_consistency_h001_source_decision_v0`.

- Status: `e008_m23_trajectory_proxy_consistency_ready_h001_source_missing`.
- Scan-policy consistency rows: 24.
- Policy consistency rows: 4.
- Proxy/trajectory success agreement: 24 / 24.
- Proxy `SPL` order consistency: 0 / 4 policies.
- Path inflation warning rows: 8.
- H001 candidate-source rows ready: 0.
- Selected next unit: E008-M24 H001 candidate-source instantiation contract.
- Real navigation `SR` / `SPL` smoke rows ready: true.
- Final real navigation `SR` / `SPL` ready: false.
- H001 navigation policy execution ready: false.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m23_trajectory_proxy_consistency_h001_source_decision.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M23_trajectory_proxy_consistency_h001_source_decision_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M23_trajectory_proxy_consistency_h001_source_decision_v0/scan_consistency_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M23_trajectory_proxy_consistency_h001_source_decision_v0/policy_consistency_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M23_trajectory_proxy_consistency_h001_source_decision_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M23_trajectory_proxy_consistency_h001_source_decision_v0/h001_candidate_source_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M23_trajectory_proxy_consistency_h001_source_decision_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M23_trajectory_proxy_consistency_h001_source_decision_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M23_trajectory_proxy_consistency_h001_source_decision_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M23_trajectory_proxy_consistency_h001_source_decision_v0/coverage.json`

## E008-M24

Implementation unit: `E008-M24_h001_candidate_source_instantiation_contract_v0`.

- Status: `e008_m24_h001_candidate_source_contract_ready_materialization_next`.
- Initial memory-proxy candidate rows: 137.
- Initial memory-proxy path-ready rows: 125.
- Current-observation candidate rows: 214.
- Current-observation path-ready rows: 189.
- Detector visit-order rows available: 781.
- Task-context rows planned: 18.
- Policy contract rows: 5.
- Policy contracts with source inputs ready: 4 / 5.
- Source input leakage pass: true.
- H001 candidate-source materialization inputs ready: true.
- H001 candidate-source rows ready: 0.
- Selected next unit: E008-M25 H001 candidate-source materialization smoke.
- Dynamic stale-memory claim ready on `HM3D`: false.
- Final real navigation `SR` / `SPL` ready: false.

Source boundary:

| Source role | Rows | Path-ready | Boundary |
| --- | ---: | ---: | --- |
| `initial_memory_proxy` | 137 | 125 | Initial non-oracle observation memory proxy, not true dynamic stale memory. |
| `current_observation` | 214 | 189 | Non-oracle expanded detector observations, not final robustness evidence. |
| `external_map` | 0 | 0 | `ConceptGraphs` / `Open3DSG` / `HOV-SG` style `HM3D` map candidates are missing. |
| `runtime_event` | 0 | 0 | Observed miss must come from execution, not `ObjectNav` goal labels. |

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m24_h001_candidate_source_instantiation_contract.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M24_h001_candidate_source_instantiation_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M24_h001_candidate_source_instantiation_contract_v0/candidate_source_schema_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M24_h001_candidate_source_instantiation_contract_v0/source_availability_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M24_h001_candidate_source_instantiation_contract_v0/task_context_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M24_h001_candidate_source_instantiation_contract_v0/policy_instantiation_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M24_h001_candidate_source_instantiation_contract_v0/leakage_guard_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M24_h001_candidate_source_instantiation_contract_v0/source_materialization_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M24_h001_candidate_source_instantiation_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M24_h001_candidate_source_instantiation_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M24_h001_candidate_source_instantiation_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M24_h001_candidate_source_instantiation_contract_v0/coverage.json`

## E008-M25

Implementation unit: `E008-M25_h001_candidate_source_materialization_smoke_v0`.

- Status: `e008_m25_h001_candidate_source_materialization_smoke_ready_policy_path_next`.
- H001 candidate-source rows: 1,053.
- Query context rows: 18.
- Policy execution plan rows: 90.
- Materialized-ready policy plan rows: 72.
- Blocked policy plan rows: 18.
- Initial memory-proxy materialized rows: 411.
- Initial memory-proxy path-ready rows: 375.
- Current-observation materialized rows: 642.
- Current-observation path-ready rows: 567.
- Source pair summary rows: 18.
- Source pair ready rows: 18.
- Source input leakage pass: true.
- Selected next unit: E008-M26 H001 visit-order/path smoke.
- H001 policy execution plan ready: true.
- H001 navigation policy execution ready: false.
- Dynamic stale-memory claim ready on `HM3D`: false.
- Final real navigation `SR` / `SPL` ready: false.

Policy plan summary:

| Policy | Plan rows | Ready rows | Blocked rows | Status |
| --- | ---: | ---: | ---: | --- |
| `real_static_memory_proxy_v0` | 18 | 18 | 0 | `ready_for_h001_visit_order_path_smoke` |
| `real_detector_confidence_expanded_v0` | 18 | 18 | 0 | `ready_for_h001_visit_order_path_smoke` |
| `real_context_agnostic_memory_trust_reobserve_v0` | 18 | 18 | 0 | `ready_for_h001_visit_order_path_smoke` |
| `h001_real_task_context_memory_trust_v0` | 18 | 18 | 0 | `ready_for_h001_visit_order_path_smoke` |
| `h001_then_external_map_after_observed_miss_v0` | 18 | 0 | 18 | `blocked_or_partial` |

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m25_h001_candidate_source_materialization_smoke.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M25_h001_candidate_source_materialization_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M25_h001_candidate_source_materialization_smoke_v0/h001_candidate_source_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M25_h001_candidate_source_materialization_smoke_v0/h001_query_context_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M25_h001_candidate_source_materialization_smoke_v0/h001_source_pair_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M25_h001_candidate_source_materialization_smoke_v0/h001_policy_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M25_h001_candidate_source_materialization_smoke_v0/policy_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M25_h001_candidate_source_materialization_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M25_h001_candidate_source_materialization_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M25_h001_candidate_source_materialization_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M25_h001_candidate_source_materialization_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M25_h001_candidate_source_materialization_smoke_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M25_h001_candidate_source_materialization_smoke_v0/h001_candidate_source_rows.jsonl`

## E008-M26

Implementation unit: `E008-M26_h001_visit_order_path_smoke_v0`.

- Status: `e008_m26_h001_visit_order_path_smoke_ready_goal_eval_next`.
- H001 candidate-source rows input: 1,053.
- Policy execution plan rows input: 90.
- Evaluated ready policy plan rows: 72.
- Blocked external-map/runtime-event policy plan rows: 18.
- H001 candidate visit-order rows: 252.
- Policy path metric rows: 77.
- Source filter accounting rows: 180.
- Selected visit rows path-ready: 252 / 252.
- Source input leakage pass: true.
- Selected next unit: E008-M27 H001 leakage-safe goal-evaluation smoke.
- H001 visit-order/path smoke ready: true.
- H001 navigation policy execution ready: false.
- Dynamic stale-memory claim ready on `HM3D`: false.
- Final real navigation `SR` / `SPL` ready: false.

Policy path aggregate:

| Policy | Scan rows | Ready rows | Visit rows | Mean first path m | Mean known path sum m |
| --- | ---: | ---: | ---: | ---: | ---: |
| `real_static_memory_proxy_v0` | 18 | 18 | 18 | 4.355265 | 4.355264 |
| `real_detector_confidence_expanded_v0` | 18 | 18 | 90 | 1.648578 | 12.662480 |
| `real_context_agnostic_memory_trust_reobserve_v0` | 18 | 18 | 72 | 4.355265 | 12.113443 |
| `h001_real_task_context_memory_trust_v0` | 18 | 18 | 72 | 2.967776 | 6.419191 |
| `h001_then_external_map_after_observed_miss_v0` | 0 | 0 | 0 | null | null |

Claim boundary:

- M26 materializes H001 visit order and known source-to-candidate path-cost proxy rows only.
- M26 does not execute a `Habitat` navigation policy and does not compute final `SR` / `SPL`.
- `initial_memory_proxy` is still an `HM3D` static-memory proxy, not true dynamic stale memory.
- Structured `task_context_id` changes memory trust/re-observation budget, but natural-language human intent is not tested.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m26_h001_visit_order_path_smoke.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M26_h001_visit_order_path_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M26_h001_visit_order_path_smoke_v0/h001_candidate_visit_order_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M26_h001_visit_order_path_smoke_v0/h001_policy_path_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M26_h001_visit_order_path_smoke_v0/source_filter_accounting_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M26_h001_visit_order_path_smoke_v0/blocked_policy_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M26_h001_visit_order_path_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M26_h001_visit_order_path_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M26_h001_visit_order_path_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M26_h001_visit_order_path_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M26_h001_visit_order_path_smoke_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M26_h001_visit_order_path_smoke_v0/h001_candidate_visit_order_rows.jsonl`

## E008-M27

Implementation unit: `E008-M27_h001_goal_evaluation_smoke_v0`.

- Status: `e008_m27_h001_goal_evaluation_smoke_ready`.
- Candidate-goal eval rows: 252.
- Scan-policy metric rows: 72.
- Aggregate policy-task rows: 12.
- Aggregate policy rows: 4.
- Blocked external-map/runtime-event policy plan rows retained: 18.
- Primary eval metric: `any_viewpoint_xz_1p0`.
- Leakage audit pass: true.
- Eval-only `ObjectNav` goal/viewpoint fields used for policy: false.
- Selected next unit: E008-M28 H001 goal-evaluation comparison and trajectory-execution decision.
- H001 goal-evaluation proxy ready: true.
- H001 navigation policy execution ready: false.
- Dynamic stale-memory claim ready on `HM3D`: false.
- Final real navigation `SR` / `SPL` ready: false.

Policy goal-evaluation aggregate:

| Policy | Primary hits | `GoalEvalProxySR` | `GoalEvalProxySPL` | `goal_xz_1p0` proxy SR |
| --- | ---: | ---: | ---: | ---: |
| `real_static_memory_proxy_v0` | 0 / 18 | 0.000000 | 0.000000 | 0.000000 |
| `real_detector_confidence_expanded_v0` | 9 / 18 | 0.500000 | 0.381619 | 0.333333 |
| `real_context_agnostic_memory_trust_reobserve_v0` | 6 / 18 | 0.333333 | 0.194209 | 0.166667 |
| `h001_real_task_context_memory_trust_v0` | 6 / 18 | 0.333333 | 0.257070 | 0.055556 |

Claim boundary:

- M27 is a leakage-safe `GoalEvalProxy` smoke, not a `Habitat` trajectory execution.
- H001 is not better than detector-confidence ranking on the current 6-episode `HM3D ObjectNav` goal proxy.
- `initial_memory_proxy` is still an `HM3D` static-memory proxy, not true dynamic stale memory.
- The next step must compare failure rows before deciding whether H001 trajectory execution is meaningful.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m27_h001_goal_evaluation_smoke.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M27_h001_goal_evaluation_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M27_h001_goal_evaluation_smoke_v0/h001_candidate_goal_eval_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M27_h001_goal_evaluation_smoke_v0/h001_policy_goal_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M27_h001_goal_evaluation_smoke_v0/h001_goal_failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M27_h001_goal_evaluation_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M27_h001_goal_evaluation_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M27_h001_goal_evaluation_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M27_h001_goal_evaluation_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M27_h001_goal_evaluation_smoke_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M27_h001_goal_evaluation_smoke_v0/h001_candidate_goal_eval_rows.jsonl`

## E008-M28

Implementation unit: `E008-M28_h001_goal_evaluation_comparison_trajectory_decision_v0`.

- Status: `e008_m28_h001_goal_eval_comparison_decision_ready_repair_first`.
- Episode-task comparison rows: 18.
- H001 primary success rows: 6 / 18.
- Detector-confidence primary success rows: 9 / 18.
- Context-agnostic primary success rows: 6 / 18.
- Static-memory primary success rows: 0 / 18.
- H001-vs-detector detector-only rows: 3.
- H001-vs-detector H001-only rows: 0.
- H001 failure rows: 12.
- Failure taxonomy: `all_policy_miss_candidate_source_gap` 9, `detector_only_success_h001_near_miss` 2, `detector_only_success_h001_candidate_gap` 1.
- Trajectory gate: pass 2 / warning 1 / fail 4.
- H001 trajectory execution recommended now: false.
- Repair recommended before trajectory execution: true.
- Selected next unit: E008-M29 H001 current-observation fallback/source repair contract.
- Final real navigation `SR` / `SPL` ready: false.

Baseline deltas:

| Baseline | Success delta | `GoalEvalProxySR` delta | `GoalEvalProxySPL` delta |
| --- | ---: | ---: | ---: |
| `real_static_memory_proxy_v0` | +6 | +0.333333 | +0.257070 |
| `real_detector_confidence_expanded_v0` | -3 | -0.166667 | -0.124549 |
| `real_context_agnostic_memory_trust_reobserve_v0` | 0 | 0.000000 | +0.062861 |

Claim boundary:

- M28 supports a leakage-safe comparison and route decision only.
- M28 does not support positive H001 real navigation `SR` / `SPL`.
- H001 is better than static memory but not better than detector-confidence ranking in this 6-episode proxy.
- Structured task context remains secondary because H001 does not improve success over context-agnostic memory trust.
- The next step is H001 current-observation fallback/source repair, not immediate H001 trajectory execution.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m28_h001_goal_evaluation_comparison_trajectory_decision.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M28_h001_goal_evaluation_comparison_trajectory_decision_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M28_h001_goal_evaluation_comparison_trajectory_decision_v0/h001_baseline_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M28_h001_goal_evaluation_comparison_trajectory_decision_v0/episode_task_comparison_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M28_h001_goal_evaluation_comparison_trajectory_decision_v0/pair_outcome_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M28_h001_goal_evaluation_comparison_trajectory_decision_v0/failure_taxonomy_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M28_h001_goal_evaluation_comparison_trajectory_decision_v0/trajectory_execution_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M28_h001_goal_evaluation_comparison_trajectory_decision_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M28_h001_goal_evaluation_comparison_trajectory_decision_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M28_h001_goal_evaluation_comparison_trajectory_decision_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M28_h001_goal_evaluation_comparison_trajectory_decision_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M28_h001_goal_evaluation_comparison_trajectory_decision_v0/episode_task_comparison_rows.jsonl`

## E008-M29

Implementation unit: `E008-M29_h001_current_observation_fallback_source_repair_contract_v0`.

- Status: `e008_m29_h001_current_observation_fallback_source_repair_contract_ready_replay_next`.
- Backstop plan rows: 18.
- Repair contract rows: 2.
- Repair opportunity rows: 12.
- Detector-only recoverable rows: 3.
- All-policy source-gap rows: 9.
- Allowed / blocked policy input rows: 28 / 22.
- Source input leakage pass: true.
- `ObjectNav` eval goal/viewpoint used for policy input: false.
- Fallback replay recommended: true.
- Trajectory execution recommended now: false.
- Selected next unit: E008-M30 H001 current-observation fallback replay smoke.
- Final real navigation `SR` / `SPL` ready: false.

Claim boundary:

- M29 supports a leakage-safe replay contract and diagnostic opportunity taxonomy only.
- M29 does not report a repaired H001 score.
- Detector-only failures are testable by `h001_current_observation_backstop_top5_v0`; all-policy failures remain candidate-source expansion blockers.
- Immediate next step is M30 replay, not Docker trajectory execution.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m29_h001_current_observation_fallback_source_repair.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M29_h001_current_observation_fallback_source_repair_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M29_h001_current_observation_fallback_source_repair_contract_v0/allowed_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M29_h001_current_observation_fallback_source_repair_contract_v0/blocked_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M29_h001_current_observation_fallback_source_repair_contract_v0/repair_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M29_h001_current_observation_fallback_source_repair_contract_v0/backstop_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M29_h001_current_observation_fallback_source_repair_contract_v0/repair_opportunity_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M29_h001_current_observation_fallback_source_repair_contract_v0/repair_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M29_h001_current_observation_fallback_source_repair_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M29_h001_current_observation_fallback_source_repair_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M29_h001_current_observation_fallback_source_repair_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M29_h001_current_observation_fallback_source_repair_contract_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M29_h001_current_observation_fallback_source_repair_contract_v0/backstop_plan_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M29_h001_current_observation_fallback_source_repair_contract_v0/repair_opportunity_rows.jsonl`

## E008-M30

Implementation unit: `E008-M30_h001_current_observation_fallback_replay_smoke_v0`.

- Status: `e008_m30_h001_current_observation_fallback_replay_smoke_ready_trajectory_contract_next`.
- Repaired candidate-goal eval rows: 141.
- Repaired primary success rows: 9 / 18.
- Base H001 primary success rows: 6 / 18.
- Detector-confidence primary success rows: 9 / 18.
- Recovered H001 failure rows: 3.
- H001 success-loss rows: 0.
- Remaining all-policy source-gap rows: 9.
- Repaired `GoalEvalProxySPL`: 0.291005.
- Detector-confidence `GoalEvalProxySPL`: 0.381619.
- `ObjectNav` eval goal/viewpoint used for policy input: false.
- Selected next unit: E008-M31 H001 fallback trajectory-execution contract and source-gap boundary.
- Final real navigation `SR` / `SPL` ready: false.

Claim boundary:

- M30 supports a leakage-safe replay result only.
- M30 recovers the 3 detector-only M28 rows without losing prior H001 successes.
- M30 matches detector-confidence `GoalEvalProxySR` but does not beat detector-confidence `GoalEvalProxySPL`.
- H001 trajectory execution, source-gap expansion, scale, and navigation/search baselines are still required before final claim.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m30_h001_current_observation_fallback_replay_smoke.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M30_h001_current_observation_fallback_replay_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M30_h001_current_observation_fallback_replay_smoke_v0/fallback_replay_candidate_goal_eval_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M30_h001_current_observation_fallback_replay_smoke_v0/fallback_replay_policy_goal_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M30_h001_current_observation_fallback_replay_smoke_v0/aggregate_policy_comparison_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M30_h001_current_observation_fallback_replay_smoke_v0/fallback_replay_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M30_h001_current_observation_fallback_replay_smoke_v0/failure_transition_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M30_h001_current_observation_fallback_replay_smoke_v0/fallback_replay_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M30_h001_current_observation_fallback_replay_smoke_v0/replay_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M30_h001_current_observation_fallback_replay_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M30_h001_current_observation_fallback_replay_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M30_h001_current_observation_fallback_replay_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M30_h001_current_observation_fallback_replay_smoke_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M30_h001_current_observation_fallback_replay_smoke_v0/fallback_replay_candidate_goal_eval_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M30_h001_current_observation_fallback_replay_smoke_v0/fallback_replay_policy_goal_metric_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M30_h001_current_observation_fallback_replay_smoke_v0/failure_transition_rows.jsonl`

## E008-M31

Implementation unit: `E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0`.

- Status: `e008_m31_h001_fallback_trajectory_contract_source_gap_boundary_ready_runner_next`.
- Sanitized H001 fallback candidate visit rows: 141.
- Trajectory execution plan rows: 18.
- Source-gap boundary rows: 9.
- Proxy-success / proxy-failure plan rows: 9 / 9.
- Source roles: `current_observation` 123, `initial_memory_proxy` 18.
- Policy input leakage pass: true.
- Sanitized policy eval-field hits: 0.
- Execute all episode-task rows next: true.
- Filtering to proxy-success rows allowed: false.
- Docker preflight status: pass 5 / warning 1.
- Selected next unit: E008-M32 H001 fallback trajectory-execution runner scaffold.
- Final real navigation `SR` / `SPL` ready: false.

Claim boundary:

- M31 supports a leakage-safe H001 fallback trajectory-input contract.
- M31 records the 9 all-policy source-gap rows as post-hoc diagnostics, not as execution filters.
- M31 does not execute H001 trajectories and does not support final real navigation `SR` / `SPL`.
- M31 does not support final real RGB-D/open-vocabulary robustness.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m31_h001_fallback_trajectory_contract_source_gap_boundary.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0/h001_fallback_candidate_visit_order_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0/trajectory_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0/source_gap_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0/blocked_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0/metric_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0/baseline_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0/docker_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0/docker_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0/h001_fallback_candidate_visit_order_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0/source_gap_boundary_rows.jsonl`

## E008-M32

Implementation unit: `E008-M32_h001_fallback_trajectory_execution_smoke_v0`.

- Status: `e008_m32_h001_fallback_trajectory_execution_smoke_ready`.
- Docker `Habitat` execution: true.
- M31 candidate visit rows: 141.
- M31 execution plan rows: 18.
- Trajectory attempt rows: 104.
- Scan-task metric rows: 18.
- Trajectory success rows: 9 / 18.
- H001 fallback trajectory `SR`: 0.500000.
- H001 fallback trajectory `SPL`: 0.141996.
- Mean `PathLengthM`: 24.136379.
- Mean `CandidateVisits`: 5.777778.
- Proxy/trajectory success agreement: 18 / 18.
- Proxy-success trajectory-failure rows: 0.
- Proxy-failure trajectory-success rows: 0.
- Source-gap trajectory success rows: 0 / 9.
- Leakage audit pass: true.
- Eval-only `ObjectNav` goal/viewpoint fields used for policy: false.
- Selected next unit: E008-M33 H001 trajectory result interpretation and baseline alignment decision.
- Final real navigation `SR` / `SPL` ready: false.

Claim boundary:

- M32 supports a bounded H001 fallback trajectory smoke over the current 6-episode `HM3D ObjectNav` transfer setup.
- M32 does not support final real navigation `SR` / `SPL`.
- M32 does not support dynamic stale-memory navigation because `initial_memory_proxy` is not true dynamic stale-memory state injection in `HM3D`.
- M32 does not support final real RGB-D/open-vocabulary robustness.

Command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp \
  -v /home/yoohyun/research3/local_dataset/data:/data:ro \
  -v /home/yoohyun/research2:/work \
  -w /work \
  research3/habitat-h001:20260508-calib-artifacts \
  bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m32_h001_fallback_trajectory_execution_smoke.py \
    --m31-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0 \
    --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M32_h001_fallback_trajectory_execution_smoke_v0 \
    --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M32_h001_fallback_trajectory_execution_smoke_v0"
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M32_h001_fallback_trajectory_execution_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M32_h001_fallback_trajectory_execution_smoke_v0/trajectory_attempt_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M32_h001_fallback_trajectory_execution_smoke_v0/trajectory_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M32_h001_fallback_trajectory_execution_smoke_v0/trajectory_failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M32_h001_fallback_trajectory_execution_smoke_v0/proxy_trajectory_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M32_h001_fallback_trajectory_execution_smoke_v0/source_gap_outcome_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M32_h001_fallback_trajectory_execution_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M32_h001_fallback_trajectory_execution_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M32_h001_fallback_trajectory_execution_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M32_h001_fallback_trajectory_execution_smoke_v0/scene_execution_meta.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M32_h001_fallback_trajectory_execution_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M32_h001_fallback_trajectory_execution_smoke_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M32_h001_fallback_trajectory_execution_smoke_v0/trajectory_policy_metric_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M32_h001_fallback_trajectory_execution_smoke_v0/proxy_trajectory_delta_rows.jsonl`

## E008-M33

Implementation unit: `E008-M33_h001_trajectory_result_interpretation_baseline_alignment_v0`.

- Status: `e008_m33_h001_trajectory_result_interpretation_baseline_alignment_ready`.
- Baseline alignment ready: true.
- M32 H001 scan-task metric rows: 18.
- M22 detector scan-policy metric rows: 24.
- Primary detector baseline: `detector_confidence_reachable_subset_v0`.
- H001 trajectory `SR` / `SPL`: 0.500000 / 0.141996.
- Primary detector replicated `SR` / `SPL`: 1.000000 / 0.410800.
- H001 minus primary detector `SR` / `SPL`: -0.500000 / -0.268804.
- Source-ready H001 subset `SR` / `SPL`: 1.000000 / 0.283993.
- Source-gap H001 subset `SR` / `SPL`: 0.000000 / 0.000000.
- Source-gap primary detector `SR`: 1.000000.
- Proxy/trajectory success agreement: 18 / 18.
- H001 navigation improvement claim ready: false.
- Dynamic-stale navigation benchmark needed: true.
- Selected next unit: E008-M34 dynamic-stale navigation benchmark contract and source-intervention design.
- Final real navigation `SR` / `SPL` ready: false.

Claim boundary:

- M33 supports a bounded claim that H001 fallback trajectory rows can be executed without policy leakage.
- M33 blocks the current H001 real-navigation improvement claim because detector trajectories dominate on aligned `SR` and `SPL`.
- M33 treats source-gap rows as candidate-source / task-construction failures, not as navigation execution failures.
- M33 says the current `HM3D ObjectNav` setup tests navigation plumbing, not controlled dynamic stale-memory semantic mapping.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m33_h001_trajectory_result_interpretation_baseline_alignment.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M33_h001_trajectory_result_interpretation_baseline_alignment_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M33_h001_trajectory_result_interpretation_baseline_alignment_v0/denominator_alignment_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M33_h001_trajectory_result_interpretation_baseline_alignment_v0/aligned_navigation_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M33_h001_trajectory_result_interpretation_baseline_alignment_v0/pairwise_baseline_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M33_h001_trajectory_result_interpretation_baseline_alignment_v0/proxy_execution_interpretation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M33_h001_trajectory_result_interpretation_baseline_alignment_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M33_h001_trajectory_result_interpretation_baseline_alignment_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M33_h001_trajectory_result_interpretation_baseline_alignment_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M33_h001_trajectory_result_interpretation_baseline_alignment_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M33_h001_trajectory_result_interpretation_baseline_alignment_v0/aligned_navigation_metric_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M33_h001_trajectory_result_interpretation_baseline_alignment_v0/pairwise_baseline_delta_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M33_h001_trajectory_result_interpretation_baseline_alignment_v0/claim_boundary_rows.jsonl`

## E008-M34

Implementation unit: `E008-M34_dynamic_stale_navigation_contract_v0`.

- Status: `e008_m34_dynamic_stale_navigation_contract_ready`.
- Selected route: `hm3d_counterfactual_stale_overlay_v0`.
- Selected next unit: E008-M35 dynamic-stale overlay row materialization smoke.
- Planned intervention rows: 18.
- Source-gap diagnostic rows: 9.
- Current H001 vs primary detector `SR` / `SPL` delta from M33: -0.500000 / -0.268804.
- True `3RScan` / `3DSSG` dynamic-pair query rows available as proxy source: 294.
- Contract ready: true.
- Materialization ready next: true.
- Dynamic-stale navigation result ready: false.
- True temporal dynamic navigation ready: false.
- Final real navigation `SR` / `SPL` ready: false.
- Launch long job now: false.

Claim boundary:

- M34 supports only a leakage-safe benchmark/source-intervention contract.
- M34 rejects scaling the current HM3D H001 fallback trajectory as a main navigation claim.
- M34 selects a counterfactual stale overlay route because it can use existing `Habitat` executable rows while adding explicit stale-memory intervention.
- M34 does not support true temporal dynamic navigation, final H001 real-navigation improvement, final real RGB-D/open-vocabulary robustness, or human intent as a main claim.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m34_dynamic_stale_navigation_contract.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M34_dynamic_stale_navigation_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M34_dynamic_stale_navigation_contract_v0/source_intervention_option_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M34_dynamic_stale_navigation_contract_v0/dynamic_stale_intervention_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M34_dynamic_stale_navigation_contract_v0/policy_baseline_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M34_dynamic_stale_navigation_contract_v0/metric_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M34_dynamic_stale_navigation_contract_v0/blocked_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M34_dynamic_stale_navigation_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M34_dynamic_stale_navigation_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M34_dynamic_stale_navigation_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M34_dynamic_stale_navigation_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M34_dynamic_stale_navigation_contract_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M34_dynamic_stale_navigation_contract_v0/dynamic_stale_intervention_plan_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M34_dynamic_stale_navigation_contract_v0/policy_baseline_contract_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M34_dynamic_stale_navigation_contract_v0/metric_contract_rows.jsonl`

## E008-M35

Implementation unit: `E008-M35_dynamic_stale_overlay_materialization_smoke_v0`.

- Status: `e008_m35_dynamic_stale_overlay_materialization_smoke_ready_runner_next`.
- Selected route: `hm3d_counterfactual_stale_overlay_v0`.
- Intervention rows: 18.
- Materialized policy ids: `static_stale_memory_top1_v0`, `fixed_topk_current_observation_v0`, `detector_confidence_reachable_subset_v0`, `task_agnostic_memory_trust_navigation_v0`, `h001_task_conditioned_memory_trust_navigation_v0`.
- Policy execution plan rows: 90.
- Candidate rows: 924.
- Candidate source roles: current observation 870, stale old memory 54.
- Source-gap policy plan rows: 45.
- Blocked field hits: 0.
- Policy input leakage pass: true.
- Dynamic stale overlay materialized: true.
- Trajectory execution ready: false.
- Generalized runner required: true.
- Selected next unit: E008-M36 dynamic-stale overlay trajectory execution contract and runner adaptation.
- Final real navigation `SR` / `SPL` ready: false.

Policy materialization summary:

| Policy | Plans | Candidates | Stale-first plans | Current-first plans |
| --- | ---: | ---: | ---: | ---: |
| `static_stale_memory_top1_v0` | 18 | 18 | 18 | 0 |
| `fixed_topk_current_observation_v0` | 18 | 90 | 0 | 18 |
| `detector_confidence_reachable_subset_v0` | 18 | 567 | 0 | 18 |
| `task_agnostic_memory_trust_navigation_v0` | 18 | 108 | 18 | 0 |
| `h001_task_conditioned_memory_trust_navigation_v0` | 18 | 141 | 12 | 6 |

Claim boundary:

- M35 supports only leakage-safe counterfactual stale overlay input materialization.
- M35 does not execute trajectories and does not produce `SR` / `SPL`.
- M35 does not prove true temporal dynamic navigation because the overlay is counterfactual on `HM3D ObjectNav`.
- M36 must generalize the H001-specific M32 runner before any dynamic-stale overlay trajectory result is valid.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m35_dynamic_stale_overlay_materialization_smoke.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M35_dynamic_stale_overlay_materialization_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M35_dynamic_stale_overlay_materialization_smoke_v0/dynamic_stale_overlay_policy_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M35_dynamic_stale_overlay_materialization_smoke_v0/dynamic_stale_overlay_policy_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M35_dynamic_stale_overlay_materialization_smoke_v0/policy_materialization_status_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M35_dynamic_stale_overlay_materialization_smoke_v0/materialization_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M35_dynamic_stale_overlay_materialization_smoke_v0/policy_materialization_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M35_dynamic_stale_overlay_materialization_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M35_dynamic_stale_overlay_materialization_smoke_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M35_dynamic_stale_overlay_materialization_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M35_dynamic_stale_overlay_materialization_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M35_dynamic_stale_overlay_materialization_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M35_dynamic_stale_overlay_materialization_smoke_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M35_dynamic_stale_overlay_materialization_smoke_v0/dynamic_stale_overlay_policy_candidate_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M35_dynamic_stale_overlay_materialization_smoke_v0/dynamic_stale_overlay_policy_execution_plan_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M35_dynamic_stale_overlay_materialization_smoke_v0/policy_materialization_summary_rows.jsonl`

## E008-M36

Implementation unit: `E008-M36_dynamic_stale_overlay_trajectory_contract_v0`.

- Status: `e008_m36_dynamic_stale_overlay_trajectory_contract_ready_runner_next`.
- M35 status: `e008_m35_dynamic_stale_overlay_materialization_smoke_ready_runner_next`.
- Trajectory candidate rows: 924.
- Trajectory execution plan rows: 90.
- Execute-in-next-runner rows: 90.
- Intervention rows: 18.
- Policy count: 5.
- Source-gap plan rows: 45.
- Blocked field hits: 0.
- Blocked flag hits: 0.
- Leakage audit pass: true.
- Runner script: `experiments/E008_real_navigation_benchmark/tools/run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py`.
- Runner py_compile pass: true.
- `Habitat` Docker image inspect pass: true.
- Trajectory execution contract ready: true.
- Runner adaptation ready: true.
- Trajectory execution result ready: false.
- Final real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M37 dynamic-stale overlay trajectory execution smoke.

Runner adaptation summary:

| Adaptation | Purpose |
| --- | --- |
| `generalize_policy_id` | M32's H001-only policy id is replaced by row-level `policy_id` / `policy_role`. |
| `generalize_input_files` | M37 reads M36 trajectory candidate rows and plan rows instead of M31-specific files. |
| `multi_policy_aggregation` | M37 aggregates five materialized policies by policy, task context, and source-gap boundary. |
| `dynamic_stale_metrics` | M37 reports stale/current source role, old-location dead-end cost, and H001-vs-baseline deltas. |

Claim boundary:

- M36 supports only trajectory contract readiness and generalized runner scaffold readiness.
- M36 does not execute `Habitat` trajectories and does not produce `SR` / `SPL`.
- Dynamic-stale navigation claims require M37 execution and post-run interpretation.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m36_dynamic_stale_overlay_trajectory_contract.py
```

Next Docker command is recorded in `docker_command_rows.jsonl`; it is not launched by M36.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M36_dynamic_stale_overlay_trajectory_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M36_dynamic_stale_overlay_trajectory_contract_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M36_dynamic_stale_overlay_trajectory_contract_v0/trajectory_execution_plan_rows.jsonl`

## E008-M37

Implementation unit: `E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0`.

- Status: `e008_m37_dynamic_stale_overlay_trajectory_execution_smoke_ready`.
- Docker inside: true.
- M36 status: `e008_m36_dynamic_stale_overlay_trajectory_contract_ready_runner_next`.
- Trajectory candidate rows: 924.
- Trajectory execution plan rows: 90.
- Trajectory attempt rows: 467.
- Scan-task-policy metric rows: 90.
- Aggregate metric rows: 10.
- Pairwise policy delta rows: 72.
- Old-location outcome rows: 48.
- Trajectory success rows: 45 / 90.
- Overall smoke `SR`: 0.500000.
- Overall mean `SPL`: 0.218178.
- Mean `PathLengthM`: 27.602670.
- Mean candidate visits: 5.188889.
- Mean `OldLocationDeadEndCostM`: 1.552844.
- Leakage audit pass: true.
- Uses `ObjectNav` eval goal/viewpoint for policy: false.
- Dynamic-stale overlay trajectory smoke ready: true.
- Final real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M38 dynamic-stale overlay result interpretation and baseline alignment.

Policy aggregates:

| Policy | Success | SR | SPL | Mean path | Mean old-dead-end |
| --- | ---: | ---: | ---: | ---: | ---: |
| `detector_confidence_reachable_subset_v0` | 18 / 18 | 1.000000 | 0.407894 | 73.336223 | 0.000000 |
| `fixed_topk_current_observation_v0` | 9 / 18 | 0.500000 | 0.373373 | 16.926073 | 0.000000 |
| `h001_task_conditioned_memory_trust_navigation_v0` | 9 / 18 | 0.500000 | 0.141996 | 24.136379 | 1.941056 |
| `static_stale_memory_top1_v0` | 0 / 18 | 0.000000 | 0.000000 | 2.911583 | 2.911583 |
| `task_agnostic_memory_trust_navigation_v0` | 9 / 18 | 0.500000 | 0.167627 | 20.703090 | 2.911583 |

H001 pairwise boundary:

- H001 vs `static_stale_memory_top1_v0`: `SR` +0.500000, `SPL` +0.141996.
- H001 vs `fixed_topk_current_observation_v0`: `SR` +0.000000, `SPL` -0.231377.
- H001 vs `task_agnostic_memory_trust_navigation_v0`: `SR` +0.000000, `SPL` -0.025631.
- H001 vs `detector_confidence_reachable_subset_v0`: `SR` -0.500000, `SPL` -0.265897.

Claim boundary:

- M37 supports only a counterfactual dynamic-stale overlay trajectory smoke.
- M37 does not support final real navigation `SR` / `SPL` because scale is 6 episodes, the overlay is counterfactual on `HM3D ObjectNav`, and navigation/search baselines still need alignment.
- H001 is better than static stale memory but not better than detector confidence and not better than task-agnostic memory trust on `SR`.

Command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp \
  -v /home/yoohyun/research3/local_dataset/data:/data:ro \
  -v /home/yoohyun/research2:/work \
  -w /work research3/habitat-h001:20260508-calib-artifacts \
  bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py --m36-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M36_dynamic_stale_overlay_trajectory_contract_v0 --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0 --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0"
```

Verification:

```bash
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0/coverage.json')
c=json.loads(p.read_text())
assert c['dynamic_stale_overlay_trajectory_smoke_ready'] is True
assert c['scan_task_policy_rows'] == 90
print('m37 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0/dynamic_stale_trajectory_attempt_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0/dynamic_stale_trajectory_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0/dynamic_stale_trajectory_failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0/pairwise_policy_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0/old_location_dead_end_outcome_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M36_dynamic_stale_overlay_trajectory_contract_v0/input_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M36_dynamic_stale_overlay_trajectory_contract_v0/runner_adaptation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M36_dynamic_stale_overlay_trajectory_contract_v0/docker_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M36_dynamic_stale_overlay_trajectory_contract_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M36_dynamic_stale_overlay_trajectory_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M36_dynamic_stale_overlay_trajectory_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M36_dynamic_stale_overlay_trajectory_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M36_dynamic_stale_overlay_trajectory_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M36_dynamic_stale_overlay_trajectory_contract_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M36_dynamic_stale_overlay_trajectory_contract_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M36_dynamic_stale_overlay_trajectory_contract_v0/trajectory_execution_plan_rows.jsonl`

## E008-M38

Implementation unit: `E008-M38_dynamic_stale_overlay_result_interpretation_baseline_alignment_v0`.

Facts:

- Status: `e008_m38_dynamic_stale_overlay_result_interpretation_baseline_alignment_ready`.
- Input M37 status: `e008_m37_dynamic_stale_overlay_trajectory_execution_smoke_ready`.
- Policy result rows: 5.
- Pairwise baseline summary rows: 4.
- Failure diagnosis rows: 7.
- Claim boundary rows: 6.
- H001 `SR` / `SPL`: 0.500000 / 0.141996.
- Detector confidence `SR` / `SPL`: 1.000000 / 0.407894.
- Fixed current top-k `SR` / `SPL`: 0.500000 / 0.373373.
- Task-agnostic memory trust `SR` / `SPL`: 0.500000 / 0.167627.
- Static stale memory `SR` / `SPL`: 0.000000 / 0.000000.
- H001 beats static memory: true.
- H001 beats detector confidence: false.
- H001 beats fixed current top-k success: false.
- H001 beats task-agnostic success: false.
- Budget-matched policy repair needed: true.
- Source-gap repair needed: true.
- Scale-up recommended now: false.
- Selected next unit: E008-M39 budget-matched dynamic-stale policy repair and source-gap contract.

Interpretation:

- Static stale memory is a valid naive failure, but beating it is only a lower-bound claim.
- Detector confidence is not rebutted in the current smoke: `SR`/`SPL` 1.000000 / 0.407894 vs H001 0.500000 / 0.141996.
- Fixed current top-k matches H001 success and has higher `SPL`, so H001 does not yet prove a better bounded search policy.
- Task-agnostic memory trust matches H001 `SR` and has higher `SPL`, so structured task context remains an ablation, not a human-intent main claim.
- Source-gap rows must stay visible because source-gap subset H001 `SR` is 0.000000 while detector confidence `SR` is 1.000000.

Claim boundary:

- M38 supports only baseline-aligned interpretation of the M37 smoke.
- M38 does not support final real navigation `SR` / `SPL`.
- M38 does not support final real RGB-D/open-vocabulary robustness.
- M38 does not support human intent as a main contribution.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m38_dynamic_stale_overlay_result_interpretation_baseline_alignment.py
```

Verification:

```bash
python -m py_compile experiments/E008_real_navigation_benchmark/tools/plan_m38_dynamic_stale_overlay_result_interpretation_baseline_alignment.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M38_dynamic_stale_overlay_result_interpretation_baseline_alignment_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status'] == 'e008_m38_dynamic_stale_overlay_result_interpretation_baseline_alignment_ready'
assert c['scale_up_recommended_now'] is False
assert c['selected_next_unit'] == 'E008-M39 budget-matched dynamic-stale policy repair and source-gap contract'
print('m38 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M38_dynamic_stale_overlay_result_interpretation_baseline_alignment_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M38_dynamic_stale_overlay_result_interpretation_baseline_alignment_v0/policy_result_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M38_dynamic_stale_overlay_result_interpretation_baseline_alignment_v0/pairwise_baseline_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M38_dynamic_stale_overlay_result_interpretation_baseline_alignment_v0/task_context_effect_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M38_dynamic_stale_overlay_result_interpretation_baseline_alignment_v0/source_gap_diagnosis_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M38_dynamic_stale_overlay_result_interpretation_baseline_alignment_v0/failure_diagnosis_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M38_dynamic_stale_overlay_result_interpretation_baseline_alignment_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M38_dynamic_stale_overlay_result_interpretation_baseline_alignment_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M38_dynamic_stale_overlay_result_interpretation_baseline_alignment_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M38_dynamic_stale_overlay_result_interpretation_baseline_alignment_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M38_dynamic_stale_overlay_result_interpretation_baseline_alignment_v0/coverage.json`

## E008-M39

Implementation unit: `E008-M39_budget_matched_policy_repair_source_gap_contract_v0`.

Facts:

- Status: `e008_m39_budget_matched_policy_repair_source_gap_contract_ready`.
- Input M38 status: `e008_m38_dynamic_stale_overlay_result_interpretation_baseline_alignment_ready`.
- Primary budget cap: 5 stops.
- Budget alignment rows: 15.
- Repair policy contract rows: 7.
- Source-gap contract rows: 3.
- M40 materialization plan rows: 90.
- Source-ready rows: 9.
- Source-gap rows: 9.
- Budget-matched policy repair contract ready: true.
- Source-gap contract ready: true.
- Scale-up recommended now: false.
- Trajectory execution launched: false.
- Final real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Human intent main claim ready: false.
- Selected next unit: E008-M40 budget-matched repair row materialization smoke.

Budget alignment:

- Source-ready rows are eligible for primary policy comparison after M40/M41 execution. On this subset, detector cap5 `SR` is 1.000000, fixed current top-k cap5 `SR` is 1.000000, task-agnostic cap5 `SR` is 1.000000, and H001 full/cap5 `SR` is 1.000000 / 0.777778.
- Source-gap rows are separated from primary policy failure. Detector full `SR` is 1.000000 but cap5 `SR` is 0.000000 with mean visits 20.333333, so this is a source-expansion / over-budget diagnostic rather than a fair budget-matched win.
- H001 source-ready failure is a delayed visit-order problem, not a pure target absence problem.

Repair policies for M40:

- `static_stale_memory_top1_v0`
- `fixed_topk_current_observation_budget5_v0`
- `detector_confidence_budget5_v0`
- `task_agnostic_dead_end_penalized_budget5_v0`
- `h001_dead_end_penalized_budget5_v0`

Claim boundary:

- M39 supports a policy/source-gap contract for row materialization only.
- M39 does not support H001 navigation improvement.
- M39 does not solve source-gap policy failure.
- M39 does not support human intent as a main contribution.
- M39 does not support final real navigation `SR` / `SPL`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m39_budget_matched_dynamic_stale_policy_repair_source_gap_contract.py
```

Verification:

```bash
python -m py_compile experiments/E008_real_navigation_benchmark/tools/plan_m39_budget_matched_dynamic_stale_policy_repair_source_gap_contract.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M39_budget_matched_policy_repair_source_gap_contract_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m39_budget_matched_policy_repair_source_gap_contract_ready'
assert c['primary_budget_cap']==5
assert c['m40_materialization_plan_rows']==90
assert c['scale_up_recommended_now'] is False
assert c['selected_next_unit']=='E008-M40 budget-matched repair row materialization smoke'
print('m39 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M39_budget_matched_policy_repair_source_gap_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M39_budget_matched_policy_repair_source_gap_contract_v0/budget_alignment_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M39_budget_matched_policy_repair_source_gap_contract_v0/repair_policy_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M39_budget_matched_policy_repair_source_gap_contract_v0/source_gap_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M39_budget_matched_policy_repair_source_gap_contract_v0/m40_materialization_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M39_budget_matched_policy_repair_source_gap_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M39_budget_matched_policy_repair_source_gap_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M39_budget_matched_policy_repair_source_gap_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M39_budget_matched_policy_repair_source_gap_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M39_budget_matched_policy_repair_source_gap_contract_v0/coverage.json`

## E008-M40

Implementation unit: `E008-M40_budget_matched_repair_row_materialization_smoke_v0`.

Facts:

- Status: `e008_m40_budget_matched_repair_row_materialization_smoke_ready`.
- Input M39 status: `e008_m39_budget_matched_policy_repair_source_gap_contract_ready`.
- M40 materialization plan rows: 90.
- Materialized policy plan rows: 90.
- Trajectory candidate rows: 378.
- Policy count: 5.
- Intervention rows: 18.
- Source-ready/source-gap plan rows: 45 / 45.
- Policy input leakage pass: true.
- Budget cap compliance pass: true.
- M41 runner input ready: true.
- Trajectory execution launched: false.
- Final real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Human intent main claim ready: false.
- Selected next unit: E008-M41 budget-matched repair trajectory execution smoke.

Policy materialization summary:

- `static_stale_memory_top1_v0`: 18 candidate rows, stale-first 18 / 18.
- `fixed_topk_current_observation_budget5_v0`: 90 candidate rows, current-first 18 / 18.
- `detector_confidence_budget5_v0`: 90 candidate rows, current-first 18 / 18.
- `task_agnostic_dead_end_penalized_budget5_v0`: 90 candidate rows, stale-first 3 / 18.
- `h001_dead_end_penalized_budget5_v0`: 90 candidate rows, stale-first 1 / 18.

Claim boundary:

- M40 supports repaired row materialization only.
- M40 does not produce trajectory `SR` / `SPL`.
- M40 keeps source-gap rows as a separate boundary.
- M40 uses structured task context only as memory-trust/re-observation conditioning, not as a natural-language human-intent claim.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m40_budget_matched_repair_row_materialization_smoke.py
```

Verification:

```bash
python -m py_compile experiments/E008_real_navigation_benchmark/tools/run_m40_budget_matched_repair_row_materialization_smoke.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M40_budget_matched_repair_row_materialization_smoke_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m40_budget_matched_repair_row_materialization_smoke_ready'
assert c['m40_plan_rows']==90
assert c['materialized_policy_plan_rows']==90
assert c['trajectory_candidate_rows']==378
assert c['policy_count']==5
assert c['policy_input_leakage_pass'] is True
assert c['budget_cap_compliance_pass'] is True
assert c['m41_runner_input_ready'] is True
assert c['trajectory_execution_launched'] is False
assert c['selected_next_unit']=='E008-M41 budget-matched repair trajectory execution smoke'
print('m40 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M40_budget_matched_repair_row_materialization_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M40_budget_matched_repair_row_materialization_smoke_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M40_budget_matched_repair_row_materialization_smoke_v0/trajectory_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M40_budget_matched_repair_row_materialization_smoke_v0/repair_policy_materialization_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M40_budget_matched_repair_row_materialization_smoke_v0/source_gap_materialization_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M40_budget_matched_repair_row_materialization_smoke_v0/policy_design_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M40_budget_matched_repair_row_materialization_smoke_v0/input_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M40_budget_matched_repair_row_materialization_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M40_budget_matched_repair_row_materialization_smoke_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M40_budget_matched_repair_row_materialization_smoke_v0/m41_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M40_budget_matched_repair_row_materialization_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M40_budget_matched_repair_row_materialization_smoke_v0/coverage.json`

## E008-M41

Implementation unit: `E008-M41_budget_matched_repair_trajectory_execution_smoke_v0`.

Facts:

- Status: `e008_m41_budget_matched_repair_trajectory_execution_smoke_ready`.
- Input M40 status: `e008_m40_budget_matched_repair_row_materialization_smoke_ready`.
- Docker inside: true.
- Trajectory candidate rows: 378.
- Trajectory execution plan rows: 90.
- Scan-task-policy metric rows: 90.
- Trajectory attempt rows: 270.
- Success rows: 36.
- Overall trajectory `SR`: 0.400000.
- Overall mean `SPL`: 0.298698.
- Leakage audit pass: true.
- ObjectNav eval goal/viewpoint used for policy: false.
- Final real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Human intent main claim ready: false.
- Selected next unit: E008-M42 budget-matched repair result interpretation and scale decision.

Policy aggregates:

- `static_stale_memory_top1_v0`: `SR` 0.000000, `SPL` 0.000000, mean `OldLocationDeadEndCostM` 2.911583.
- `fixed_topk_current_observation_budget5_v0`: `SR` 0.500000, `SPL` 0.373373.
- `detector_confidence_budget5_v0`: `SR` 0.500000, `SPL` 0.373373.
- `task_agnostic_dead_end_penalized_budget5_v0`: `SR` 0.500000, `SPL` 0.373373, mean `OldLocationDeadEndCostM` 0.210660.
- `h001_dead_end_penalized_budget5_v0`: `SR` 0.500000, `SPL` 0.373373, mean `OldLocationDeadEndCostM` 0.070220.

Claim boundary:

- M41 is a budget-matched repaired trajectory smoke, not a final navigation benchmark.
- H001 repaired policy beats static stale memory but does not beat detector/fixed current top-k or task-agnostic memory trust on `SR` / `SPL`.
- Source-gap rows remain a separate source-expansion boundary: source-gap aggregate `SR` is 0.000000.
- M41 does not support final real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, or human intent as a main claim.

Command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp \
  -v /home/yoohyun/research3/local_dataset/data:/data:ro \
  -v /home/yoohyun/research2:/work \
  -w /work research3/habitat-h001:20260508-calib-artifacts \
  bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m41_budget_matched_repair_trajectory_execution_smoke.py"
```

Verification:

```bash
python -m py_compile \
  experiments/E008_real_navigation_benchmark/tools/run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py \
  experiments/E008_real_navigation_benchmark/tools/run_m41_budget_matched_repair_trajectory_execution_smoke.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M41_budget_matched_repair_trajectory_execution_smoke_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m41_budget_matched_repair_trajectory_execution_smoke_ready'
assert c['inside_docker'] is True
assert c['scan_task_policy_rows']==90
assert c['trajectory_candidate_rows']==378
assert c['leakage_audit_pass'] is True
assert c['uses_objectnav_eval_goal_or_viewpoint_for_policy'] is False
assert c['selected_next_unit']=='E008-M42 budget-matched repair result interpretation and scale decision'
print('m41 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M41_budget_matched_repair_trajectory_execution_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M41_budget_matched_repair_trajectory_execution_smoke_v0/dynamic_stale_trajectory_attempt_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M41_budget_matched_repair_trajectory_execution_smoke_v0/dynamic_stale_trajectory_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M41_budget_matched_repair_trajectory_execution_smoke_v0/dynamic_stale_trajectory_failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M41_budget_matched_repair_trajectory_execution_smoke_v0/pairwise_policy_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M41_budget_matched_repair_trajectory_execution_smoke_v0/old_location_dead_end_outcome_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M41_budget_matched_repair_trajectory_execution_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M41_budget_matched_repair_trajectory_execution_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M41_budget_matched_repair_trajectory_execution_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M41_budget_matched_repair_trajectory_execution_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M41_budget_matched_repair_trajectory_execution_smoke_v0/coverage.json`

## E008-M42

Implementation unit: `E008-M42_budget_matched_repair_result_interpretation_scale_decision_v0`.

Facts:

- Status: `e008_m42_budget_matched_repair_result_interpretation_scale_decision_ready`.
- Input M41 status: `e008_m41_budget_matched_repair_trajectory_execution_smoke_ready`.
- Policy result rows: 5.
- Source boundary rows: 10.
- Pairwise decision rows: 4.
- Task-context effect rows: 3.
- Scale gate rows: 6.
- H001 source-ready `SR`: 1.000000.
- H001 source-gap `SR`: 0.000000.
- H001 vs detector/fixed/task-agnostic mean `delta_SR`: 0.000000.
- H001 vs detector/fixed/task-agnostic mean `delta_SPL`: 0.000000.
- Scale-up recommended now: false.
- Final real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Human intent main claim ready: false.
- Selected route: `policy_redesign_before_scale`.
- Selected next unit: E008-M43 dynamic-stale navigation policy redesign contract.

Claim boundary:

- M42 supports only result interpretation and scale decision.
- H001 beats static stale memory only; this is a lower-bound failure diagnosis, not a final navigation claim.
- H001 does not beat detector/fixed current top-k or task-agnostic memory trust on `SR` / `SPL`.
- Source-gap rows are not solved by ranking or dead-end penalty.
- Human intent/task context remains a conditioning variable, not a main contribution.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m42_budget_matched_repair_result_interpretation_scale_decision.py
```

Verification:

```bash
python -m py_compile \
  experiments/E008_real_navigation_benchmark/tools/plan_m42_budget_matched_repair_result_interpretation_scale_decision.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M42_budget_matched_repair_result_interpretation_scale_decision_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m42_budget_matched_repair_result_interpretation_scale_decision_ready'
assert c['m41_status']=='e008_m41_budget_matched_repair_trajectory_execution_smoke_ready'
assert c['policy_result_rows']==5
assert c['source_boundary_rows']==10
assert c['scale_up_recommended_now'] is False
assert c['real_navigation_sr_spl_ready'] is False
assert c['source_gap_unsolved'] is True
assert c['selected_next_unit']=='E008-M43 dynamic-stale navigation policy redesign contract'
print('m42 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M42_budget_matched_repair_result_interpretation_scale_decision_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M42_budget_matched_repair_result_interpretation_scale_decision_v0/policy_result_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M42_budget_matched_repair_result_interpretation_scale_decision_v0/source_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M42_budget_matched_repair_result_interpretation_scale_decision_v0/pairwise_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M42_budget_matched_repair_result_interpretation_scale_decision_v0/task_context_effect_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M42_budget_matched_repair_result_interpretation_scale_decision_v0/scale_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M42_budget_matched_repair_result_interpretation_scale_decision_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M42_budget_matched_repair_result_interpretation_scale_decision_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M42_budget_matched_repair_result_interpretation_scale_decision_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M42_budget_matched_repair_result_interpretation_scale_decision_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M42_budget_matched_repair_result_interpretation_scale_decision_v0/coverage.json`

## E008-M43

Implementation unit: `E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0`.

Facts:

- Status: `e008_m43_dynamic_stale_navigation_policy_redesign_contract_ready`.
- Input M42 status: `e008_m42_budget_matched_repair_result_interpretation_scale_decision_ready`.
- Selected policy: `h001_task_conditioned_source_diverse_budget5_v1`.
- Selected source expansion route: `source_diverse_current_candidate_pool_rerank_v1`.
- Detector source-gap full `SR`: 1.000000.
- Detector source-gap cap5 `SR`: 0.000000.
- Detector source-gap mean stop rank: 20.333333.
- Unique scan-task rows: 18.
- Source-gap scan-task rows: 9.
- M44 materialization plan rows: 108.
- M44 policy rows: static stale memory, detector confidence budget5, fixed current top-k budget5, source-diverse current observation, task-agnostic source-diverse, H001 task-conditioned source-diverse.
- M44 materialization ready: true.
- M45 trajectory execution ready: false.
- Final real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Human intent main claim ready: false.
- Selected next unit: E008-M44 source-diverse redesign row materialization smoke.

Claim boundary:

- M43 fixes a redesign contract; it is not a new trajectory result.
- Source-diverse top-5 is selected because source-gap rows are recoverable only when the full current candidate pool is allowed, but not under confidence top-5.
- Structured task context remains a conditioning variable until `h001_task_conditioned_source_diverse_budget5_v1` beats `task_agnostic_source_diverse_budget5_v1`.
- M43 does not support final real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, or human intent as a main contribution.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m43_dynamic_stale_navigation_policy_redesign_contract.py
```

Verification:

```bash
python -m py_compile \
  experiments/E008_real_navigation_benchmark/tools/plan_m43_dynamic_stale_navigation_policy_redesign_contract.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m43_dynamic_stale_navigation_policy_redesign_contract_ready'
assert c['m42_status']=='e008_m42_budget_matched_repair_result_interpretation_scale_decision_ready'
assert c['detector_source_gap_full_SR']==1.0
assert c['detector_source_gap_cap5_SR']==0.0
assert c['unique_scan_task_rows']==18
assert c['source_gap_scan_task_rows']==9
assert c['m44_materialization_plan_rows']==108
assert c['selected_policy_id']=='h001_task_conditioned_source_diverse_budget5_v1'
assert c['selected_next_unit']=='E008-M44 source-diverse redesign row materialization smoke'
print('m43 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0/failed_gate_diagnosis_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0/redesign_principle_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0/policy_redesign_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0/source_expansion_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0/task_context_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0/input_guard_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0/m44_materialization_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0/evaluation_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0/coverage.json`

## E008-M44

Implementation unit: `E008-M44_source_diverse_redesign_row_materialization_smoke_v0`.

Facts:

- Status: `e008_m44_source_diverse_redesign_row_materialization_smoke_ready`.
- Input M36 status: `e008_m36_dynamic_stale_overlay_trajectory_contract_ready_runner_next`.
- Input M40 status: `e008_m40_budget_matched_repair_row_materialization_smoke_ready`.
- Input M43 status: `e008_m43_dynamic_stale_navigation_policy_redesign_contract_ready`.
- M43 materialization plan rows: 108.
- Execution plan rows: 108.
- Candidate rows: 468.
- Policies: `static_stale_memory_top1_v0`, `detector_confidence_budget5_v0`, `fixed_topk_current_observation_budget5_v0`, `source_diverse_current_observation_budget5_v1`, `task_agnostic_source_diverse_budget5_v1`, `h001_task_conditioned_source_diverse_budget5_v1`.
- Source-ready/source-gap plan rows: 54 / 54.
- Policy input leakage pass: true.
- Budget cap compliance pass: true.
- M45 runner input ready: true.
- Final real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Human intent main claim ready: false.
- Selected next unit: E008-M45 source-diverse redesign trajectory execution contract and Docker preflight.

Claim boundary:

- M44 is materialization only; it does not produce trajectory `SR` / `SPL`.
- Source-diverse policies are distinct from detector-confidence order, but this is only a pre-execution audit.
- `diagnostic_source_gap_boundary_for_reporting` is retained for later analysis and is not a policy input.
- Structured task context remains a memory-trust/re-observation condition, not natural-language intent understanding.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m44_source_diverse_redesign_row_materialization_smoke.py
```

Verification:

```bash
python -m py_compile \
  experiments/E008_real_navigation_benchmark/tools/run_m44_source_diverse_redesign_row_materialization_smoke.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M44_source_diverse_redesign_row_materialization_smoke_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m44_source_diverse_redesign_row_materialization_smoke_ready'
assert c['m43_m44_plan_rows']==108
assert c['source_diverse_execution_plan_rows']==108
assert c['source_diverse_candidate_rows']==468
assert c['policy_input_leakage_pass'] is True
assert c['budget_cap_compliance_pass'] is True
assert c['m45_runner_input_ready'] is True
assert c['selected_next_unit']=='E008-M45 source-diverse redesign trajectory execution contract and Docker preflight'
print('m44 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M44_source_diverse_redesign_row_materialization_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M44_source_diverse_redesign_row_materialization_smoke_v0/source_diverse_redesign_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M44_source_diverse_redesign_row_materialization_smoke_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M44_source_diverse_redesign_row_materialization_smoke_v0/source_diverse_redesign_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M44_source_diverse_redesign_row_materialization_smoke_v0/trajectory_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M44_source_diverse_redesign_row_materialization_smoke_v0/policy_materialization_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M44_source_diverse_redesign_row_materialization_smoke_v0/candidate_pool_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M44_source_diverse_redesign_row_materialization_smoke_v0/source_diversity_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M44_source_diverse_redesign_row_materialization_smoke_v0/policy_distinctness_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M44_source_diverse_redesign_row_materialization_smoke_v0/input_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M44_source_diverse_redesign_row_materialization_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M44_source_diverse_redesign_row_materialization_smoke_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M44_source_diverse_redesign_row_materialization_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M44_source_diverse_redesign_row_materialization_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M44_source_diverse_redesign_row_materialization_smoke_v0/m45_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M44_source_diverse_redesign_row_materialization_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M44_source_diverse_redesign_row_materialization_smoke_v0/coverage.json`

## E008-M45

Implementation unit: `E008-M45_source_diverse_redesign_trajectory_contract_v0`.

Facts:

- Status: `e008_m45_source_diverse_redesign_trajectory_contract_ready_runner_next`.
- Input M44 status: `e008_m44_source_diverse_redesign_row_materialization_smoke_ready`.
- Candidate rows: 468.
- Execution plan rows: 108.
- Source-gap/source-ready reporting plan rows: 54 / 54.
- H001 policy id: `h001_task_conditioned_source_diverse_budget5_v1`.
- Baseline policy ids: `static_stale_memory_top1_v0`, `detector_confidence_budget5_v0`, `fixed_topk_current_observation_budget5_v0`, `source_diverse_current_observation_budget5_v1`, `task_agnostic_source_diverse_budget5_v1`.
- Docker CLI/image/data/navmesh/ObjectNav checks: pass.
- `nvidia-smi` check: pass.
- M37 runner `py_compile`: pass.
- M46 runner wrapper `py_compile`: pass.
- Source-gap reporting fallback in M37: ready.
- Final real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Human intent main claim ready: false.
- Selected next unit: E008-M46 source-diverse redesign trajectory execution smoke.

Claim boundary:

- M45 is contract and Docker preflight only; it does not produce trajectory `SR` / `SPL`.
- M45 formalizes E008-M46 execution through `run_m46_source_diverse_redesign_trajectory_execution_smoke.py`.
- `diagnostic_source_gap_boundary_for_reporting` remains reporting-only and is not a policy input.
- Structured task context remains a memory-trust/re-observation condition, not natural-language intent understanding.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m45_source_diverse_redesign_trajectory_contract.py
```

Verification:

```bash
python -m py_compile \
  experiments/E008_real_navigation_benchmark/tools/plan_m45_source_diverse_redesign_trajectory_contract.py \
  experiments/E008_real_navigation_benchmark/tools/run_m46_source_diverse_redesign_trajectory_execution_smoke.py \
  experiments/E008_real_navigation_benchmark/tools/run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M45_source_diverse_redesign_trajectory_contract_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m45_source_diverse_redesign_trajectory_contract_ready_runner_next'
assert c['trajectory_candidate_rows']==468
assert c['trajectory_execution_plan_rows']==108
assert c['docker_preflight_pass'] is True
assert c['runner_py_compile_pass'] is True
assert c['m37_source_gap_reporting_fallback_ready'] is True
assert c['selected_next_unit']=='E008-M46 source-diverse redesign trajectory execution smoke'
print('m45 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M45_source_diverse_redesign_trajectory_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M45_source_diverse_redesign_trajectory_contract_v0/trajectory_execution_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M45_source_diverse_redesign_trajectory_contract_v0/metric_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M45_source_diverse_redesign_trajectory_contract_v0/runner_compatibility_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M45_source_diverse_redesign_trajectory_contract_v0/docker_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M45_source_diverse_redesign_trajectory_contract_v0/m46_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M45_source_diverse_redesign_trajectory_contract_v0/input_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M45_source_diverse_redesign_trajectory_contract_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M45_source_diverse_redesign_trajectory_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M45_source_diverse_redesign_trajectory_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M45_source_diverse_redesign_trajectory_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M45_source_diverse_redesign_trajectory_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M45_source_diverse_redesign_trajectory_contract_v0/coverage.json`
