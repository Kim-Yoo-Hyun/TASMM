# E008 Real Navigation Benchmark

Updated: 2026-05-28

## Status

E008 starts after E007-M07 packaged the occupancy-grid path-cost proxy table and selected `E008-M01 real navigation benchmark/source preflight and episode contract`. E008 is the first stage that prepares real navigation `SR` / `SPL` evidence. E008-M01 through E008-M18 are complete as source/adapter/contract/oracle-metric/candidate-source staging, negative semantic-coordinate smoke, rendered RGB-D detector-source plan, rendered RGB-D frame staging, detector candidate smoke, coordinate-frame/navmesh validation, detector candidate visit-order path smoke, leakage-safe goal-evaluation smoke, detector-goal failure audit, non-oracle observation-coverage planning, expanded frame staging/snap validation, expanded detector candidate smoke, expanded candidate navmesh validation, and expanded visit-order path smoke steps only; they do not execute an H001 policy benchmark.

Next unit: E008-M19 expanded leakage-safe detector candidate goal-evaluation smoke.

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
| command | `python experiments/E008_real_navigation_benchmark/tools/plan_m01_navigation_source_episode_contract.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m02_hm3d_objectnav_adapter_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/plan_m03_h001_candidate_navigation_adapter.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m04_objectnav_oracle_path_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/plan_m05_hm3d_candidate_source_staging.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m06_hm3d_semantic_candidate_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/plan_m07_hm3d_rendered_rgbd_detector_source.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m08_hm3d_rendered_rgbd_frame_staging_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/verify_m09_hm3d_rendered_rgbd_detector_candidate_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m10_detector_candidate_navmesh_validation.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m11_detector_candidate_visit_order_path_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m12_detector_candidate_goal_evaluation_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/plan_m13_detector_goal_failure_audit.py`; `python experiments/E008_real_navigation_benchmark/tools/plan_m14_non_oracle_observation_coverage.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m15_non_oracle_observation_expansion_frame_staging.py`; `python experiments/E008_real_navigation_benchmark/tools/verify_m15_non_oracle_observation_expansion_frame_staging.py`; `python experiments/E008_real_navigation_benchmark/tools/verify_m16_non_oracle_observation_expansion_detector_candidate_smoke.py --require-ready`; `python experiments/E008_real_navigation_benchmark/tools/run_m17_expanded_detector_candidate_navmesh_validation.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m18_expanded_detector_candidate_visit_order_path_smoke.py` |
| output | Source preflight rows, episode schema rows, metric contract rows, baseline contract rows, allowed/blocked input rows, candidate visit-order rows, route decision rows, next action rows, and report. |
| conclusion | E008-M01 selects `HM3D ObjectNav` + `Habitat` as the first real navigation source. E008-M02 verifies tiny `val_mini` episode/source rows and Docker scene/navmesh loading. E008-M03 fixes the H001 candidate-to-navigation schema and leakage guard. E008-M04 verifies oracle path/metric plumbing with eval-only `ObjectNav` viewpoints. E008-M05 selects annotation-derived `HM3D` semantic candidate staging as the next smoke route. E008-M06 shows that semantic labels exist but reliable non-oracle semantic geometry coordinates are not available from the current annotation path. E008-M07 fixes the rendered RGB-D detector-source plan with start-pose fixed yaw sweep observations and E003 detector compatibility layout. E008-M08 stages and verifies 24 rendered RGB-D frames in detector-compatible sequence layout. E008-M09 generates 137 detector candidate rows with valid `centroid_world_m` coordinates. E008-M10 validates that 137/137 candidates join to frames/scenes, 136/137 snap to navigable points, and 125/137 have source-to-snapped paths, with 12 warning/failure rows retained for later policy accounting. E008-M11 materializes 512 detector candidate visit-order rows and 28 policy metric rows over 4 policies without using eval-only `ObjectNav` goal/viewpoint fields as policy input. E008-M12 joins the visit-order rows to eval-only `ObjectNav` goals/viewpoints and reports limited `GoalEvalProxy` success: all 4 policies hit 3/6 under `any_viewpoint_xz_1p0`, while `goal_xz_1p0` is only 1/6. E008-M13 audits those failures and selects non-oracle observation coverage expansion because 3 failures are shared across all policies, with 2 clear pre-cap target-region misses and 1 near-miss localization threshold case. E008-M14 fixes `bounded_start_neighborhood_multiview_v0`: 54 planned observation poses and 216 expanded render rows over all 6 episodes, using start pose, category, scene/navmesh, current candidates, reachable samples, and fixed budget only. E008-M15 renders and verifies those expanded observations: 216/216 ready frames, 6/6 ready scans, 216/216 snap-ready rows, 8 large snap warnings, and no `ObjectNav` eval goal/viewpoint policy input. E008-M16 verifies detector output on the expanded observation set: 216 frame rows, 4,009 raw predictions, 214 coordinate candidate rows, and 3,801 pre-cap candidate rows. E008-M17 validates expanded candidates against the navmesh: 214/214 coordinate-valid, 213/214 snapped navigable, 189/214 source-to-snapped path found, and every scan has at least one path-ready candidate. E008-M18 materializes 781 visit-order rows and 28 policy metric rows; reachable-subset policies have top1-ready candidates on 6/6 scans, while non-path-ready candidates remain explicit accounting rows. |

## Claim Boundary

- E008-M01/M02/M03/M04/M05/M06/M07/M08/M09/M10/M11/M12/M13/M14/M15/M16/M17/M18 do not claim real navigation `SR` / `SPL`.
- E008-M01/M02/M03/M04/M05/M06/M07/M08/M09/M10/M11/M12/M13/M14/M15/M16/M17/M18 do not claim final real RGB-D/open-vocabulary robustness.
- E008-M01/M02/M03/M04/M05/M06/M07/M08/M09/M10/M11/M12/M13/M14/M15/M16/M17/M18 do not make human intent a main contribution.
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
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0/real_proposals.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0/pre_cap_candidate_pool.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0/model_smoke.json`

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
