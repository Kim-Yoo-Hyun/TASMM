# E008 Real Navigation Benchmark

Updated: 2026-06-01

## Status

E008 starts after E007-M07 packaged the occupancy-grid path-cost proxy table and selected `E008-M01 real navigation benchmark/source preflight and episode contract`. E008 is the first stage that prepares real navigation `SR` / `SPL` evidence. E008-M01 through E008-M86 are complete as source/adapter/contract/oracle-metric/candidate-source staging, rendered RGB-D detector route, leakage-safe goal evaluation, trajectory execution, H001 fallback execution, dynamic-stale overlay execution, budget-matched repair, source-diverse redesign/materialization/execution, routine-fetch repair, task-context boundary, navigation boundary package, source-gap repair chain, high-path tail-slot materialization, leakage-safe goal-evaluation smoke, Docker trajectory execution, result interpretation/scale decision, scale-up/source-boundary contract, full-val-mini denominator materialization, render/detector contract, full-val-mini detector source chain, source-gap non-oracle source/observation expansion, source-gap render frame staging, and source-gap detector candidate-source verification. E008-M86 verifies 48 final source-gap detector candidates from 1,896 pre-cap candidates and 1,964 raw predictions, with validator errors/warnings 0/0 and matching target rows 0. Final navigation, deployable policy, real RGB-D/open-vocabulary robustness, and human-intent main claims remain blocked pending M87 navmesh/source-readiness validation, later source-gap recovery evaluation, trajectory checks, and external navigation/search baselines.

Next unit: E008-M87 source-gap detector candidate navmesh/source-readiness validation.

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
| conclusion | E008-M01 selects `HM3D ObjectNav` + `Habitat` as the first real navigation source. E008-M02-M42 build and execute the detector/H001/dynamic-stale trajectory smoke chain with final navigation claims blocked. E008-M43 fixes source-diverse policy redesign because detector source-gap rows are recoverable in the full current candidate pool but not under confidence top-5. E008-M44-M82 iterate through source-diverse, routine-fetch, high-path tail-slot, full-val-mini, trajectory, source-gap/SPL repair, and loss-safe source-expansion gates while keeping final navigation claims blocked. E008-M83 fixes the non-oracle source/observation expansion contract. E008-M84 materializes source-gap render/detector inputs. E008-M85 verifies source-gap rendered frame staging. E008-M86 verifies source-gap detector candidate-source generation: 48 final candidates, 1,896 pre-cap candidates, 0 validator errors/warnings, and 0 matching target rows. |

## Claim Boundary

- E008-M01 through E008-M86 do not claim final real navigation `SR` / `SPL`.
- E008-M01 through E008-M86 do not claim final real RGB-D/open-vocabulary robustness.
- E008-M01 through E008-M86 do not make human intent a main contribution.
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
- E008-M46 supports a source-diverse trajectory smoke, but it does not support final navigation improvement because H001 loses to task-agnostic source-diverse on `SR` and `SPL`.
- E008-M47 supports result interpretation and scale decision only; it blocks scale-up and selects E008-M48 repair planning.
- E008-M48 supports repair-contract planning only; it does not materialize repaired rows, execute trajectories, or support a repaired navigation claim.
- E008-M49 supports repaired row materialization only; it does not execute trajectories or support a repaired navigation performance claim.
- E008-M50 supports Docker trajectory contract/preflight only; it does not execute trajectories or support a repaired navigation performance claim.
- E008-M51 supports a repaired trajectory smoke only; it does not support final navigation improvement because repaired H001 v2 ties task-agnostic source-diverse and loses `SPL` to detector/fixed baselines.
- E008-M52 supports result interpretation and scale decision only; it blocks scale-up because only 5/10 gates pass and task-context specificity is not supported against task-agnostic source-diverse.
- E008-M53 supports task-context boundary and next-route decision only; it demotes task context to a secondary condition and selects navigation boundary packaging before any further E008 scale-up.
- E008-M54 supports diagnostic paper-table boundary packaging only; it freezes `navigation_smoke_diagnostic_table_v0` but blocks `main_real_navigation_sr_spl_table` and selects source-gap candidate-generation repair before any scale-up.
- E008-M55 supports source-gap repair feasibility decision only; it blocks rerank-only source-gap repair because remaining failed contexts have no successful executed top-5 candidate, and selects candidate-source expansion before any scale-up.
- E008-M56 supports source-gap candidate-source expansion contract only; it shows full-pool source-gap hits exist outside budget-5 and selects policy-visible full-pool feature audit before any new policy or scale-up.
- E008-M57 supports policy-visible full-pool source-gap feature audit only; it shows a high-path tail slot can surface 2/2 unrecovered source-gap hits diagnostically, but it does not materialize a policy or execute trajectories.
- E008-M58 supports high-path tail-slot policy materialization only; it creates runner-ready rows and diagnostic recovery audit, but it does not compute leakage-safe goal-evaluation or execute trajectories.
- E008-M59 supports leakage-safe goal-evaluation proxy gains for the high-path tail-slot policy, but it does not execute `Habitat` trajectories or support final real navigation `SR` / `SPL`.
- E008-M60 supports high-path tail-slot trajectory contract/Docker preflight only; it creates the M61 runner contract, but it does not execute `Habitat` trajectories or support final real navigation `SR` / `SPL`.
- E008-M61 supports a controlled high-path tail-slot trajectory smoke, but M61 alone does not support final real navigation `SR` / `SPL`.
- E008-M62 supports result interpretation and scale decision only; it allows a bounded diagnostic navigation table and scale-up contract, but final navigation remains blocked by source-ready efficiency warning, denominator scale, heldout transfer, and stronger navigation/search baselines.
- E008-M63 supports scale-up/source-boundary contract only; it fixes `val_mini_full_episode_scale` but does not materialize rows or execute trajectories.
- E008-M64 supports full-val-mini denominator and policy-plan materialization only; candidate rows, rendered frames, detector inference, navmesh validation, and trajectory execution remain future units.
- E008-M65 supports full-val-mini render/detector contract only; it does not launch rendering, run detector inference, validate candidate coordinates, or execute trajectories.
- E008-M66 supports only repaired frame staging verification; it does not run detector inference, validate candidate coordinates, or execute trajectories.
- E008-M67 supports full-val-mini detector candidate-source generation and schema verification only; it does not validate navmesh reachability, execute trajectories, or support final navigation claims.
- E008-M68 supports full-val-mini detector candidate navmesh/source-readiness validation only; it does not materialize visit-order/path rows, run leakage-safe goal evaluation, execute trajectories, or support final navigation claims.
- E008-M69 supports full-val-mini detector candidate visit-order/path smoke only; it does not execute trajectories or support final navigation claims.
- E008-M70 supports full-val-mini leakage-safe goal-evaluation proxy only; it does not resolve detector target-recall matching, execute trajectories, or support final navigation claims.
- E008-M71 supports failure comparison and trajectory-contract decision only; it does not execute trajectories or support final navigation claims.
- E008-M72 supports detector-policy trajectory contract/Docker preflight only; it does not execute trajectories, and its budget-5 proxy weakness blocks deployable fixed-budget policy claims.
- E008-M73 supports executed detector-policy trajectory smoke only; it does not support final real navigation `SR` / `SPL` because policy `SR` ties, detector-confidence `SPL` is stronger than the path-cost policy, and external navigation/search baselines are still absent.
- E008-M74 supports result interpretation and budget-boundary decision only; it confirms M73 is diagnostic evidence, not a positive navigation-policy result, because source-gap `SR` is 0.0, budget-5 proxy `SR` is 0.2667, path-cost policy loses `SPL`, and external navigation/search baselines are absent.
- E008-M76 supports source-gap/SPL repair row materialization only; it does not evaluate repaired `SR` / `SPL` or execute trajectories, and it keeps deployable fixed-budget search and final navigation claims blocked.
- E008-M77 supports leakage-safe repair goal-evaluation only; it blocks trajectory-contract promotion because the guarded repair loses one budget-5 proxy success row and regresses budget-5 proxy `SPL`.
- E008-M78 supports repair result interpretation and next-route decision only; it rejects direct trajectory promotion and rerank-only repair, and it does not support final real navigation `SR` / `SPL`.
- E008-M79 supports a loss-safe candidate-source expansion contract only; it fixes detector-confidence budget-5 top-5 preservation, source/observation expansion planning, and localization-control separation, but it does not materialize rows, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.
- E008-M80 supports loss-safe candidate-source expansion row materialization only; it preserves detector-confidence budget-5 top-5 and prepares M81 proxy evaluation, but it does not evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.
- E008-M81 supports leakage-safe proxy evaluation of the M80 rows; it preserves detector budget-5 behavior and shows append gain only under budget-8 policy scope, but it does not recover source-gap rows, execute trajectories, or support final real navigation `SR` / `SPL`.
- E008-M82 supports result interpretation and route decision only; it blocks direct trajectory promotion and selects M83 source/observation expansion contract, but it does not materialize new source rows, execute trajectories, or support final real navigation `SR` / `SPL`.
- E008-M83 supports a non-oracle source/observation expansion contract only; it fixes source-gap cases, allowed/blocked inputs, M84 output contracts, and long-job policy, but it does not materialize new source rows, run render/detector jobs, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.
- E008-M84 supports source-gap source/observation expansion input materialization only; it writes observation pose plans, render plans, detector manifests, and long-job command rows, but it does not render frames, run detector inference, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.
- E008-M85 supports source-gap rendered frame staging only; it verifies RGB-D/pose files and detector input readiness, but it does not run detector inference, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.
- E008-M86 supports source-gap detector candidate-source availability and schema/coordinate readiness only; it does not validate navmesh reachability, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.
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

## E008-M46

Implementation unit: `E008-M46_source_diverse_redesign_trajectory_execution_smoke_v0`.

Facts:

- Status: `e008_m46_source_diverse_redesign_trajectory_execution_smoke_ready`.
- Inside Docker: true.
- Candidate rows: 468.
- Execution plan rows: 108.
- Expected / actual scan-task-policy rows: 108 / 108.
- Trajectory attempt rows: 346.
- Trajectory success rows: 50.
- Leakage audit pass: true.
- H001 `SR` / `SPL`: 0.611111 / 0.259497.
- Detector-confidence `SR` / `SPL`: 0.500000 / 0.373373.
- Fixed current-observation `SR` / `SPL`: 0.500000 / 0.373373.
- Source-diverse current-observation `SR` / `SPL`: 0.500000 / 0.209064.
- Task-agnostic source-diverse `SR` / `SPL`: 0.666667 / 0.322604.
- Static stale memory `SR` / `SPL`: 0.000000 / 0.000000.
- `ObjectNav` eval goal/viewpoint used for policy input: false.
- Final real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M47 source-diverse redesign result interpretation and scale decision.

Claim boundary:

- M46 is a Docker `Habitat` trajectory smoke, not a final navigation benchmark.
- H001 improves `SR` over detector/fixed/source-diverse-current baselines, but loses to task-agnostic source-diverse on both `SR` and `SPL`.
- This result blocks broader scale-up until M47 explains whether the loss is task-context conditioning, visit-order cost, or source-gap handling.

Command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp \
  -v /home/yoohyun/research3/local_dataset/data:/data:ro \
  -v /home/yoohyun/research2:/work -w /work \
  research3/habitat-h001:20260508-calib-artifacts \
  bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m46_source_diverse_redesign_trajectory_execution_smoke.py"
```

Verification:

```bash
python -m py_compile \
  experiments/E008_real_navigation_benchmark/tools/run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py \
  experiments/E008_real_navigation_benchmark/tools/run_m46_source_diverse_redesign_trajectory_execution_smoke.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M46_source_diverse_redesign_trajectory_execution_smoke_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m46_source_diverse_redesign_trajectory_execution_smoke_ready'
assert c['scan_task_policy_rows']==108
assert c['expected_scan_task_policy_rows']==108
assert c['trajectory_candidate_rows']==468
assert c['trajectory_execution_plan_rows']==108
assert c['leakage_audit_pass'] is True
assert c['uses_objectnav_eval_goal_or_viewpoint_for_policy'] is False
assert c['selected_next_unit']=='E008-M47 source-diverse redesign result interpretation and scale decision'
print('m46 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M46_source_diverse_redesign_trajectory_execution_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M46_source_diverse_redesign_trajectory_execution_smoke_v0/dynamic_stale_trajectory_attempt_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M46_source_diverse_redesign_trajectory_execution_smoke_v0/dynamic_stale_trajectory_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M46_source_diverse_redesign_trajectory_execution_smoke_v0/dynamic_stale_trajectory_failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M46_source_diverse_redesign_trajectory_execution_smoke_v0/pairwise_policy_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M46_source_diverse_redesign_trajectory_execution_smoke_v0/old_location_dead_end_outcome_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M46_source_diverse_redesign_trajectory_execution_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M46_source_diverse_redesign_trajectory_execution_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M46_source_diverse_redesign_trajectory_execution_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M46_source_diverse_redesign_trajectory_execution_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M46_source_diverse_redesign_trajectory_execution_smoke_v0/coverage.json`

## E008-M47

Implementation unit: `E008-M47_source_diverse_result_interpretation_scale_decision_v0`.

Facts:

- Status: `e008_m47_source_diverse_result_interpretation_scale_decision_ready`.
- M46 status: `e008_m46_source_diverse_redesign_trajectory_execution_smoke_ready`.
- Policy result rows: 6.
- Pairwise decision rows: 5.
- Source boundary rows: 12.
- Task context effect rows: 3.
- Regression case rows: 2.
- Scale gate rows / pass rows: 8 / 4.
- Scale-up recommended now: false.
- H001 beats static stale memory and current-observation `SR`.
- H001 fails detector/fixed `SPL`, task-agnostic source-diverse, source-gap task-agnostic, and `routine_fetch` no-regression gates.
- Regression cases: `00800-TEEsavR23oF::10` `routine_fetch` success with extra path cost; `00800-TEEsavR23oF::4` `routine_fetch` source-gap miss that task-agnostic reaches.
- Final real navigation `SR` / `SPL` ready: false.
- Human intent main claim ready: false.
- Selected next unit: E008-M48 routine-fetch task-context regression and source-gap repair contract.

Claim boundary:

- M47 supports only result interpretation and scale decision.
- M46 may be reported as a leakage-safe trajectory smoke with partial `SR` recovery.
- Do not claim final navigation improvement, deployable search policy, or human intent main effect.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m47_source_diverse_result_interpretation_scale_decision.py
```

Verification:

```bash
python -m py_compile experiments/E008_real_navigation_benchmark/tools/plan_m47_source_diverse_result_interpretation_scale_decision.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M47_source_diverse_result_interpretation_scale_decision_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m47_source_diverse_result_interpretation_scale_decision_ready'
assert c['m46_status']=='e008_m46_source_diverse_redesign_trajectory_execution_smoke_ready'
assert c['scale_up_recommended_now'] is False
assert c['scale_gate_rows']==8
assert c['scale_gate_pass_rows']==4
assert c['regression_case_rows']==2
assert c['selected_next_unit']=='E008-M48 routine-fetch task-context regression and source-gap repair contract'
print('m47 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M47_source_diverse_result_interpretation_scale_decision_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M47_source_diverse_result_interpretation_scale_decision_v0/policy_result_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M47_source_diverse_result_interpretation_scale_decision_v0/pairwise_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M47_source_diverse_result_interpretation_scale_decision_v0/source_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M47_source_diverse_result_interpretation_scale_decision_v0/task_context_effect_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M47_source_diverse_result_interpretation_scale_decision_v0/regression_case_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M47_source_diverse_result_interpretation_scale_decision_v0/scale_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M47_source_diverse_result_interpretation_scale_decision_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M47_source_diverse_result_interpretation_scale_decision_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M47_source_diverse_result_interpretation_scale_decision_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M47_source_diverse_result_interpretation_scale_decision_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M47_source_diverse_result_interpretation_scale_decision_v0/coverage.json`

## E008-M48

Implementation unit: `E008-M48_routine_fetch_task_context_regression_source_gap_repair_contract_v0`.

Facts:

- Status: `e008_m48_routine_fetch_task_context_regression_source_gap_repair_contract_ready`.
- Regression diagnosis rows: 2.
- Repair principle rows: 3.
- Repair policy contract rows: 1.
- Selected repair policy: `h001_task_conditioned_safe_source_diverse_budget5_v2`.
- M49 materialization plan rows: 7.
- M49 expected execution plan rows: 126.
- M49 expected candidate rows: 558.
- Readiness gate rows / pass rows: 8 / 8.
- Scale-up recommended now: false.
- Final real navigation `SR` / `SPL` ready: false.
- Human intent main claim ready: false.
- Selected next unit: E008-M49 routine-fetch regression repair row materialization smoke.

Claim boundary:

- M48 is a contract unit only.
- The two known success proposal ids are audit-only diagnostics and are blocked from policy input.
- M49 must preserve all M44 baselines unchanged and add only `h001_task_conditioned_safe_source_diverse_budget5_v2`.
- M50 or later Docker `Habitat` execution is required before any repaired navigation performance claim.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m48_routine_fetch_regression_source_gap_repair_contract.py
```

Verification:

```bash
python -m py_compile experiments/E008_real_navigation_benchmark/tools/plan_m48_routine_fetch_regression_source_gap_repair_contract.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M48_routine_fetch_task_context_regression_source_gap_repair_contract_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m48_routine_fetch_task_context_regression_source_gap_repair_contract_ready'
assert c['regression_case_diagnosis_rows']==2
assert c['repair_principle_rows']==3
assert c['repair_policy_contract_rows']==1
assert c['m49_materialization_plan_rows']==7
assert c['m49_expected_execution_plan_rows']==126
assert c['m49_expected_candidate_rows']==558
assert c['readiness_gate_pass_rows']==c['readiness_gate_rows']==8
assert c['selected_next_unit']=='E008-M49 routine-fetch regression repair row materialization smoke'
print('m48 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M48_routine_fetch_task_context_regression_source_gap_repair_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M48_routine_fetch_task_context_regression_source_gap_repair_contract_v0/regression_case_diagnosis_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M48_routine_fetch_task_context_regression_source_gap_repair_contract_v0/repair_principle_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M48_routine_fetch_task_context_regression_source_gap_repair_contract_v0/repair_policy_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M48_routine_fetch_task_context_regression_source_gap_repair_contract_v0/input_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M48_routine_fetch_task_context_regression_source_gap_repair_contract_v0/m49_materialization_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M48_routine_fetch_task_context_regression_source_gap_repair_contract_v0/regression_repair_target_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M48_routine_fetch_task_context_regression_source_gap_repair_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M48_routine_fetch_task_context_regression_source_gap_repair_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M48_routine_fetch_task_context_regression_source_gap_repair_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M48_routine_fetch_task_context_regression_source_gap_repair_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M48_routine_fetch_task_context_regression_source_gap_repair_contract_v0/coverage.json`

## E008-M49

Implementation unit: `E008-M49_routine_fetch_repair_row_materialization_smoke_v0`.

Facts:

- Status: `e008_m49_routine_fetch_repair_row_materialization_smoke_ready`.
- Selected repair policy: `h001_task_conditioned_safe_source_diverse_budget5_v2`.
- Candidate rows: 558.
- Execution plan rows: 126.
- Policy count: 7.
- M44 baseline preservation rows / pass rows: 108 / 108.
- Regression repair target audit rows / pass rows: 2 / 2.
- Leakage audit pass: true.
- Budget cap compliance pass: true.
- Readiness gate rows / pass rows: 10 / 10.
- Final real navigation `SR` / `SPL` ready: false.
- Human intent main claim ready: false.
- Selected next unit: E008-M50 routine-fetch repair trajectory execution contract and Docker preflight.

Claim boundary:

- M49 is a row materialization smoke only.
- It preserves all M44 baseline orders and adds `h001_task_conditioned_safe_source_diverse_budget5_v2` for paired comparison.
- It does not execute `Habitat` trajectories and does not support a repaired navigation improvement claim.
- M50 must fix the Docker trajectory contract/preflight before any repaired policy execution.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m49_routine_fetch_repair_row_materialization_smoke.py
```

Verification:

```bash
python -m py_compile experiments/E008_real_navigation_benchmark/tools/run_m49_routine_fetch_repair_row_materialization_smoke.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M49_routine_fetch_repair_row_materialization_smoke_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m49_routine_fetch_repair_row_materialization_smoke_ready'
assert c['candidate_rows']==558
assert c['trajectory_execution_plan_rows']==126
assert c['policy_count']==7
assert c['baseline_preservation_pass_rows']==c['baseline_preservation_audit_rows']==108
assert c['regression_repair_target_pass_rows']==c['regression_repair_target_audit_rows']==2
assert c['leakage_audit_pass'] is True
assert c['budget_cap_compliance_pass'] is True
assert c['selected_next_unit']=='E008-M50 routine-fetch repair trajectory execution contract and Docker preflight'
print('m49 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M49_routine_fetch_repair_row_materialization_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M49_routine_fetch_repair_row_materialization_smoke_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M49_routine_fetch_repair_row_materialization_smoke_v0/trajectory_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M49_routine_fetch_repair_row_materialization_smoke_v0/policy_materialization_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M49_routine_fetch_repair_row_materialization_smoke_v0/baseline_preservation_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M49_routine_fetch_repair_row_materialization_smoke_v0/repair_policy_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M49_routine_fetch_repair_row_materialization_smoke_v0/regression_repair_target_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M49_routine_fetch_repair_row_materialization_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M49_routine_fetch_repair_row_materialization_smoke_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M49_routine_fetch_repair_row_materialization_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M49_routine_fetch_repair_row_materialization_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M49_routine_fetch_repair_row_materialization_smoke_v0/m50_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M49_routine_fetch_repair_row_materialization_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M49_routine_fetch_repair_row_materialization_smoke_v0/coverage.json`

## E008-M50

Implementation unit: `E008-M50_routine_fetch_repair_trajectory_contract_v0`.

Facts:

- Status: `e008_m50_routine_fetch_repair_trajectory_contract_ready_runner_next`.
- Selected repair policy: `h001_task_conditioned_safe_source_diverse_budget5_v2`.
- Candidate rows: 558.
- Execution plan rows: 126.
- Execute-in-runner rows: 126.
- Policy count: 7.
- M37 runner py_compile pass: true.
- M51 runner py_compile pass: true.
- Docker preflight pass: true.
- `Habitat` Docker image inspect pass: true.
- `nvidia-smi` pass: true.
- Read-only `HM3D` scene/navmesh ready: 2/2 scenes and 2/2 navmeshes.
- ObjectNav content files ready: 2.
- Final real navigation `SR` / `SPL` ready: false.
- Human intent main claim ready: false.
- Selected next unit: E008-M51 routine-fetch repair trajectory execution smoke.

Claim boundary:

- M50 is a contract and preflight unit only.
- It pins the M51 Docker command and copies the M49 candidate/plan rows into a runner-compatible contract folder.
- It does not execute `Habitat` trajectories and does not support repaired navigation improvement.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m50_routine_fetch_repair_trajectory_contract.py
```

Verification:

```bash
python -m py_compile \
  experiments/E008_real_navigation_benchmark/tools/plan_m50_routine_fetch_repair_trajectory_contract.py \
  experiments/E008_real_navigation_benchmark/tools/run_m51_routine_fetch_repair_trajectory_execution_smoke.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M50_routine_fetch_repair_trajectory_contract_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m50_routine_fetch_repair_trajectory_contract_ready_runner_next'
assert c['trajectory_candidate_rows']==558
assert c['trajectory_execution_plan_rows']==126
assert c['execute_in_next_runner_rows']==126
assert c['policy_count']==7
assert c['runner_py_compile_pass'] is True
assert c['docker_preflight_pass'] is True
assert c['selected_next_unit']=='E008-M51 routine-fetch repair trajectory execution smoke'
print('m50 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M50_routine_fetch_repair_trajectory_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M50_routine_fetch_repair_trajectory_contract_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M50_routine_fetch_repair_trajectory_contract_v0/trajectory_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M50_routine_fetch_repair_trajectory_contract_v0/trajectory_execution_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M50_routine_fetch_repair_trajectory_contract_v0/metric_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M50_routine_fetch_repair_trajectory_contract_v0/runner_compatibility_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M50_routine_fetch_repair_trajectory_contract_v0/docker_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M50_routine_fetch_repair_trajectory_contract_v0/m51_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M50_routine_fetch_repair_trajectory_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M50_routine_fetch_repair_trajectory_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M50_routine_fetch_repair_trajectory_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M50_routine_fetch_repair_trajectory_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M50_routine_fetch_repair_trajectory_contract_v0/coverage.json`

## E008-M51

Implementation unit: `E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0`.

Facts:

- Status: `e008_m51_routine_fetch_repair_trajectory_execution_smoke_ready`.
- Docker inside: true.
- Trajectory candidate rows: 558.
- Trajectory execution plan rows: 126.
- Scan-task-policy rows: 126.
- Trajectory attempt rows: 409.
- Trajectory success rows: 62.
- Overall trajectory `SR`: 0.492063.
- Overall mean `SPL`: 0.265788.
- Leakage audit pass: true.
- Scene error rows: 0.
- Policy count: 7.
- Selected next unit: E008-M52 routine-fetch repair result interpretation and scale decision.

Policy aggregate facts:

| policy_id | success | rows | SR | SPL |
| --- | --- | --- | --- | --- |
| `h001_task_conditioned_safe_source_diverse_budget5_v2` | 12 | 18 | 0.666667 | 0.322604 |
| `task_agnostic_source_diverse_budget5_v1` | 12 | 18 | 0.666667 | 0.322604 |
| `h001_task_conditioned_source_diverse_budget5_v1` | 11 | 18 | 0.611111 | 0.259497 |
| `detector_confidence_budget5_v0` | 9 | 18 | 0.500000 | 0.373373 |
| `fixed_topk_current_observation_budget5_v0` | 9 | 18 | 0.500000 | 0.373373 |
| `source_diverse_current_observation_budget5_v1` | 9 | 18 | 0.500000 | 0.209064 |
| `static_stale_memory_top1_v0` | 0 | 18 | 0.000000 | 0.000000 |

Claim boundary:

- M51 is a trajectory execution smoke, not a final navigation benchmark.
- Repaired H001 v2 improves over H001 v1 and current-source baselines on `SR`, but it ties the task-agnostic source-diverse baseline on `SR` and `SPL`.
- Repaired H001 v2 improves `SR` over detector/fixed current top-k, but loses `SPL` to detector/fixed current top-k.
- M52 must decide whether this is enough for another repair, a scale decision, or a stop-and-record boundary.

Command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp \
  -v /home/yoohyun/research3/local_dataset/data:/data:ro \
  -v /home/yoohyun/research2:/work -w /work \
  research3/habitat-h001:20260508-calib-artifacts \
  bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m51_routine_fetch_repair_trajectory_execution_smoke.py"
```

Verification:

```bash
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m51_routine_fetch_repair_trajectory_execution_smoke_ready'
assert c['scan_task_policy_rows']==126
assert c['expected_scan_task_policy_rows']==126
assert c['policy_count']==7
assert c['leakage_audit_pass'] is True
assert c['uses_objectnav_eval_goal_or_viewpoint_for_policy'] is False
assert c['selected_next_unit']=='E008-M52 routine-fetch repair result interpretation and scale decision'
print('m51 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0/dynamic_stale_trajectory_attempt_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0/dynamic_stale_trajectory_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0/dynamic_stale_trajectory_failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0/pairwise_policy_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0/old_location_dead_end_outcome_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0/coverage.json`

## E008-M52

Implementation unit: `E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0`.

Facts:

- Status: `e008_m52_routine_fetch_repair_result_interpretation_scale_decision_ready`.
- M51 status: `e008_m51_routine_fetch_repair_trajectory_execution_smoke_ready`.
- Scale gates: 5 / 10 pass.
- Scale-up recommended now: false.
- Repaired H001 v2 `SR` / `SPL`: 0.666667 / 0.322604.
- Previous H001 v1 `SR` / `SPL`: 0.611111 / 0.259497.
- `task_agnostic_source_diverse_budget5_v1` `SR` / `SPL`: 0.666667 / 0.322604.
- Detector/fixed delta `SPL`: -0.050769.
- Source-gap H001 v2 `SR`: 0.333333.
- Source-gap task-agnostic `SR`: 0.333333.
- Human intent main claim ready: false.
- Final real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M53 routine-fetch task-context specificity boundary and next-route decision.

Claim boundary:

- M52 is an interpretation/scale-decision unit, not a new navigation benchmark.
- M52 supports only a within-H001 repair claim: repaired H001 v2 improves H001 v1 on the current smoke denominator.
- M52 does not support a task-context or human-intent main claim because task-agnostic source-diverse ties H001 v2 exactly.
- M52 does not support deployable navigation improvement because detector/fixed baselines have higher `SPL`.
- M52 blocks broader scale-up until task-context specificity and source-gap recovery are either repaired or removed from the main claim.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m52_routine_fetch_repair_result_interpretation_scale_decision.py
```

Verification:

```bash
python -m py_compile experiments/E008_real_navigation_benchmark/tools/plan_m52_routine_fetch_repair_result_interpretation_scale_decision.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m52_routine_fetch_repair_result_interpretation_scale_decision_ready'
assert c['m51_status']=='e008_m51_routine_fetch_repair_trajectory_execution_smoke_ready'
assert c['scale_gate_pass_rows']==5
assert c['scale_gate_rows']==10
assert c['scale_up_recommended_now'] is False
assert c['human_intent_main_claim_ready'] is False
assert c['real_navigation_sr_spl_ready'] is False
assert c['selected_next_unit']=='E008-M53 routine-fetch task-context specificity boundary and next-route decision'
print('m52 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0/policy_result_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0/pairwise_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0/source_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0/task_context_effect_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0/regression_or_weakness_case_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0/scale_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0/coverage.json`

## E008-M53

Implementation unit: `E008-M53_routine_fetch_task_context_specificity_boundary_next_route_v0`.

Facts:

- Status: `e008_m53_routine_fetch_task_context_specificity_boundary_ready`.
- M52 status: `e008_m52_routine_fetch_repair_result_interpretation_scale_decision_ready`.
- Evidence gates: 3 / 8 pass.
- Task-context rows: 3.
- Task-context distinct gain rows: 0 / 3.
- No regression vs task-agnostic source-diverse: true.
- Selected route: `demote_task_context_and_package_boundary`.
- Selected next unit: E008-M54 navigation boundary package and paper-table freeze.
- Human intent main claim ready: false.
- Final real navigation `SR` / `SPL` ready: false.

Claim boundary:

- M53 supports the within-H001 repair boundary, not a human-intent or task-context main claim.
- `high_value_fetch`, `noisy_high_value_fetch`, and `routine_fetch` all tie `task_agnostic_source_diverse_budget5_v1` on `SR` and `SPL`.
- Task context may remain as a secondary reported condition, but it should not be written as a main method contribution in the E008 navigation evidence.
- Source-gap recovery remains partial and is not task-context-specific.
- Further E008 scale-up is blocked until boundary packaging is complete and a distinct source-gap/efficiency-positive route exists.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m53_routine_fetch_task_context_specificity_boundary_next_route.py
```

Verification:

```bash
python -m py_compile experiments/E008_real_navigation_benchmark/tools/plan_m53_routine_fetch_task_context_specificity_boundary_next_route.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M53_routine_fetch_task_context_specificity_boundary_next_route_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m53_routine_fetch_task_context_specificity_boundary_ready'
assert c['task_context_any_distinct_gain'] is False
assert c['task_context_no_regression_vs_task_agnostic'] is True
assert c['selected_route']=='demote_task_context_and_package_boundary'
assert c['selected_next_unit']=='E008-M54 navigation boundary package and paper-table freeze'
assert c['human_intent_main_claim_ready'] is False
assert c['real_navigation_sr_spl_ready'] is False
print('m53 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M53_routine_fetch_task_context_specificity_boundary_next_route_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M53_routine_fetch_task_context_specificity_boundary_next_route_v0/task_context_specificity_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M53_routine_fetch_task_context_specificity_boundary_next_route_v0/specificity_evidence_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M53_routine_fetch_task_context_specificity_boundary_next_route_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M53_routine_fetch_task_context_specificity_boundary_next_route_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M53_routine_fetch_task_context_specificity_boundary_next_route_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M53_routine_fetch_task_context_specificity_boundary_next_route_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M53_routine_fetch_task_context_specificity_boundary_next_route_v0/coverage.json`

## E008-M54

Implementation unit: `E008-M54_navigation_boundary_package_paper_table_freeze_v0`.

Facts:

- Status: `e008_m54_navigation_boundary_package_paper_table_freeze_ready`.
- M52 status: `e008_m52_routine_fetch_repair_result_interpretation_scale_decision_ready`.
- M53 status: `e008_m53_routine_fetch_task_context_specificity_boundary_ready`.
- Diagnostic navigation table rows: 7.
- Freeze gates: 6 / 6 pass.
- Allowed claim rows: 4.
- Blocked claim rows: 6.
- H001 v2 `SR` / `SPL`: 0.666667 / 0.322604.
- `task_agnostic_source_diverse_budget5_v1` `SR` / `SPL`: 0.666667 / 0.322604.
- Detector confidence `SR` / `SPL`: 0.500000 / 0.373373.
- H001 v2 source-gap `SR`: 0.333333.
- Diagnostic navigation table frozen: true.
- Main real navigation table frozen: false.
- Human intent main claim ready: false.
- Final real navigation `SR` / `SPL` ready: false.
- Deployable search policy ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Selected next unit: E008-M55 source-gap candidate-generation repair feasibility decision.

Claim boundary:

- M54 freezes E008 as diagnostic navigation evidence, not final benchmark evidence.
- `navigation_smoke_diagnostic_table_v0` may be used as a diagnostic or appendix table.
- `main_real_navigation_sr_spl_table` remains blocked because H001 v2 ties task-agnostic source-diverse, loses `SPL` to detector/fixed baselines, and has weak source-gap recovery.
- Task context remains a secondary condition only because M53 found 0/3 contexts with distinct gain over task-agnostic source-diverse.
- The next technical blocker is source-gap candidate generation, not immediate benchmark scale-up.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m54_navigation_boundary_package_paper_table_freeze.py
```

Verification:

```bash
python -m py_compile experiments/E008_real_navigation_benchmark/tools/plan_m54_navigation_boundary_package_paper_table_freeze.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M54_navigation_boundary_package_paper_table_freeze_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m54_navigation_boundary_package_paper_table_freeze_ready'
assert c['paper_navigation_table_rows']==7
assert c['freeze_gate_pass_rows']==6
assert c['freeze_gate_rows']==6
assert c['diagnostic_navigation_table_frozen'] is True
assert c['main_navigation_table_frozen'] is False
assert c['human_intent_main_claim_ready'] is False
assert c['real_navigation_sr_spl_ready'] is False
assert c['selected_next_unit']=='E008-M55 source-gap candidate-generation repair feasibility decision'
print('m54 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M54_navigation_boundary_package_paper_table_freeze_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M54_navigation_boundary_package_paper_table_freeze_v0/paper_navigation_table_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M54_navigation_boundary_package_paper_table_freeze_v0/paper_navigation_table_rows.csv`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M54_navigation_boundary_package_paper_table_freeze_v0/paper_table_freeze_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M54_navigation_boundary_package_paper_table_freeze_v0/allowed_claim_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M54_navigation_boundary_package_paper_table_freeze_v0/blocked_claim_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M54_navigation_boundary_package_paper_table_freeze_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M54_navigation_boundary_package_paper_table_freeze_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M54_navigation_boundary_package_paper_table_freeze_v0/freeze_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M54_navigation_boundary_package_paper_table_freeze_v0/next_route_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M54_navigation_boundary_package_paper_table_freeze_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M54_navigation_boundary_package_paper_table_freeze_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M54_navigation_boundary_package_paper_table_freeze_v0/paper_navigation_table_rows.jsonl`

## E008-M55

Implementation unit: `E008-M55_source_gap_candidate_generation_repair_feasibility_v0`.

Facts:

- Status: `e008_m55_source_gap_candidate_generation_repair_feasibility_ready`.
- Source-gap episodes: 3.
- Source-gap scan-task contexts: 9.
- H001 v2 source-gap `SR`: 0.333333.
- `task_agnostic_source_diverse_budget5_v1` source-gap `SR`: 0.333333.
- Detector/fixed source-gap `SR`: 0.000000 / 0.000000.
- Remaining H001 failed source-gap contexts: 6.
- Remaining failed contexts with any executed top-5 variant hit: 0.
- Rerank-only repair sufficient: false.
- Candidate-source expansion needed: true.
- Final real navigation `SR` / `SPL` ready: false.
- Human intent main claim ready: false.
- Deployable search policy ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Selected next unit: E008-M56 source-gap candidate-source expansion contract.

Claim boundary:

- M55 supports only a source-gap repair feasibility decision.
- H001 v2 has a positive source-gap case over detector/fixed, but it ties task-agnostic source-diverse and therefore does not support a task-conditioned source-gap claim.
- The remaining source-gap failures should be treated as candidate-source coverage failures, not as a solved ranking-only problem.
- Any full candidate-pool inspection must remain diagnostic unless the policy uses only non-oracle signals.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m55_source_gap_candidate_generation_repair_feasibility.py
```

Verification:

```bash
python -m py_compile experiments/E008_real_navigation_benchmark/tools/plan_m55_source_gap_candidate_generation_repair_feasibility.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M55_source_gap_candidate_generation_repair_feasibility_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m55_source_gap_candidate_generation_repair_feasibility_ready'
assert c['source_gap_episode_rows']==3
assert c['source_gap_scan_task_context_rows']==9
assert c['h001_source_gap_SR']==c['task_agnostic_source_gap_SR']
assert c['h001_remaining_source_gap_failed_context_rows']==6
assert c['remaining_failed_contexts_with_any_top5_variant_hit']==0
assert c['rerank_only_repair_sufficient'] is False
assert c['candidate_source_expansion_needed'] is True
assert c['selected_next_unit']=='E008-M56 source-gap candidate-source expansion contract'
print('m55 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M55_source_gap_candidate_generation_repair_feasibility_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M55_source_gap_candidate_generation_repair_feasibility_v0/source_gap_policy_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M55_source_gap_candidate_generation_repair_feasibility_v0/source_gap_episode_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M55_source_gap_candidate_generation_repair_feasibility_v0/candidate_generation_feasibility_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M55_source_gap_candidate_generation_repair_feasibility_v0/evidence_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M55_source_gap_candidate_generation_repair_feasibility_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M55_source_gap_candidate_generation_repair_feasibility_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M55_source_gap_candidate_generation_repair_feasibility_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M55_source_gap_candidate_generation_repair_feasibility_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M55_source_gap_candidate_generation_repair_feasibility_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M55_source_gap_candidate_generation_repair_feasibility_v0/source_gap_episode_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M55_source_gap_candidate_generation_repair_feasibility_v0/candidate_generation_feasibility_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M55_source_gap_candidate_generation_repair_feasibility_v0/route_decision_rows.jsonl`

## E008-M56

Implementation unit: `E008-M56_source_gap_candidate_source_expansion_contract_v0`.

Facts:

- Status: `e008_m56_source_gap_candidate_source_expansion_contract_ready`.
- Source-gap episodes: 3.
- M19 full-pool hit episodes: 3 / 3.
- Full-pool hits outside budget-5 episodes: 3 / 3.
- Unrecovered budget-surfacing episodes: 2.
- Primary budget: 5 candidate visits.
- Allowed input groups: 5.
- Blocked input groups: 4.
- Budget-5 policy materialized: false.
- Final real navigation `SR` / `SPL` ready: false.
- Human intent main claim ready: false.
- Deployable search policy ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Selected next unit: E008-M57 source-gap full-pool candidate-source feature audit.

Claim boundary:

- M56 supports only a source-gap candidate-source expansion contract.
- M56 does not solve source-gap; it refines the blocker from candidate absence to budgeted source surfacing.
- M19 full-pool hit labels are diagnostic metric evidence only and cannot be used as policy inputs.
- New rendering or external map/proposal sources are deferred until M57 decides whether policy-visible full-pool features can surface deep hits.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m56_source_gap_candidate_source_expansion_contract.py
```

Verification:

```bash
python -m py_compile experiments/E008_real_navigation_benchmark/tools/plan_m56_source_gap_candidate_source_expansion_contract.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M56_source_gap_candidate_source_expansion_contract_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m56_source_gap_candidate_source_expansion_contract_ready'
assert c['source_gap_episode_rows']==3
assert c['m19_full_pool_hit_episode_rows']==3
assert c['full_pool_hit_outside_budget5_episode_rows']==3
assert c['unrecovered_budget_surfacing_episode_rows']==2
assert c['candidate_source_expansion_contract_ready'] is True
assert c['budget5_policy_materialized'] is False
assert c['real_navigation_sr_spl_ready'] is False
assert c['selected_next_unit']=='E008-M57 source-gap full-pool candidate-source feature audit'
print('m56 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M56_source_gap_candidate_source_expansion_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M56_source_gap_candidate_source_expansion_contract_v0/source_gap_case_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M56_source_gap_candidate_source_expansion_contract_v0/full_pool_hit_diagnostic_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M56_source_gap_candidate_source_expansion_contract_v0/candidate_source_route_option_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M56_source_gap_candidate_source_expansion_contract_v0/allowed_input_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M56_source_gap_candidate_source_expansion_contract_v0/blocked_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M56_source_gap_candidate_source_expansion_contract_v0/policy_design_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M56_source_gap_candidate_source_expansion_contract_v0/materialization_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M56_source_gap_candidate_source_expansion_contract_v0/evaluation_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M56_source_gap_candidate_source_expansion_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M56_source_gap_candidate_source_expansion_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M56_source_gap_candidate_source_expansion_contract_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M56_source_gap_candidate_source_expansion_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M56_source_gap_candidate_source_expansion_contract_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M56_source_gap_candidate_source_expansion_contract_v0/source_gap_case_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M56_source_gap_candidate_source_expansion_contract_v0/materialization_plan_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M56_source_gap_candidate_source_expansion_contract_v0/route_decision_rows.jsonl`

## E008-M57

Implementation unit: `E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0`.

Facts:

- Status: `e008_m57_source_gap_full_pool_candidate_source_feature_audit_ready`.
- Full-pool candidate feature rows: 142.
- Source-gap episodes: 3.
- Unrecovered budget-surfacing episodes: 2.
- Detector-confidence budget-5 unrecovered hits: 0 / 2.
- `confidence_top4_plus_high_path_top1` unrecovered hits: 2 / 2.
- `path_cost_descending_budget5` source-gap hits: 2 / 3.
- M58 policy materialization ready: true.
- Budget-5 policy materialized: false.
- Final real navigation `SR` / `SPL` ready: false.
- Human intent main claim ready: false.
- Deployable search policy ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Selected next unit: E008-M58 source-gap high-path tail-slot policy materialization.

Claim boundary:

- M57 supports only a diagnostic feature audit over policy-visible full-pool candidate fields.
- M57 does not use eval labels for policy selection; eval labels are used only to score the audit.
- M57 does not support final real navigation `SR` / `SPL`, deployable policy, or human intent as a main contribution.
- High path-cost should augment H001 as a selective tail slot, not replace the policy, because path-cost descending alone misses the recovered positive source-gap case.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m57_source_gap_full_pool_candidate_source_feature_audit.py
```

Verification:

```bash
python -m py_compile experiments/E008_real_navigation_benchmark/tools/plan_m57_source_gap_full_pool_candidate_source_feature_audit.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m57_source_gap_full_pool_candidate_source_feature_audit_ready'
assert c['full_pool_candidate_feature_rows']==142
assert c['unrecovered_budget_surfacing_episode_rows']==2
assert c['detector_confidence_unrecovered_hit_rows']==0
assert c['high_path_tail_unrecovered_hit_rows']==2
assert c['m58_policy_materialization_ready'] is True
assert c['budget5_policy_materialized'] is False
assert c['real_navigation_sr_spl_ready'] is False
assert c['selected_next_unit']=='E008-M58 source-gap high-path tail-slot policy materialization'
print('m57 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0/source_gap_full_pool_candidate_feature_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0/candidate_feature_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0/source_gap_hit_vs_top5_feature_contrast_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0/source_gap_promoter_rule_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0/source_gap_promoter_feasibility_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0/source_gap_full_pool_candidate_feature_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0/source_gap_promoter_rule_audit_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0/route_decision_rows.jsonl`

## E008-M58

Implementation unit: `E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0`.

Facts:

- Status: `e008_m58_source_gap_high_path_tail_slot_policy_materialization_ready`.
- New policy: `h001_task_conditioned_high_path_tail_slot_budget5_v3`.
- Candidate rows: 648.
- Execution plan rows: 144.
- New policy plan rows: 18.
- New policy candidate rows: 90.
- M49 policy order preservation: 126 / 126.
- Leakage audit pass: true.
- Budget cap compliance pass: true.
- Unrecovered source-gap episodes recovered in diagnostic audit: 2 / 2.
- Unrecovered source-gap contexts recovered in diagnostic audit: 6 / 6.
- Final real navigation `SR` / `SPL` ready: false.
- Human intent main claim ready: false.
- Deployable search policy ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Selected next unit: E008-M59 high-path tail-slot leakage-safe goal-evaluation smoke.

Claim boundary:

- M58 materializes policy rows only.
- The high-path tail-slot rule is applied to all 18 scan-task rows, not only source-gap rows.
- M58 preserves the previous M49 comparison policies and adds one H001-compatible policy row family.
- Diagnostic hit labels are used only in audit outputs, not in policy ordering.
- M58 does not support final real navigation `SR` / `SPL`, deployable policy, or human intent as a main contribution.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m58_source_gap_high_path_tail_slot_policy_materialization.py
```

Verification:

```bash
python -m py_compile experiments/E008_real_navigation_benchmark/tools/run_m58_source_gap_high_path_tail_slot_policy_materialization.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m58_source_gap_high_path_tail_slot_policy_materialization_ready'
assert c['candidate_rows']==648
assert c['trajectory_execution_plan_rows']==144
assert c['new_policy_plan_rows']==18
assert c['new_policy_candidate_rows']==90
assert c['m49_preservation_pass_rows']==126
assert c['leakage_audit_pass'] is True
assert c['budget_cap_compliance_pass'] is True
assert c['unrecovered_source_gap_recovered_episode_rows']==2
assert c['unrecovered_source_gap_recovered_context_rows']==6
assert c['real_navigation_sr_spl_ready'] is False
assert c['selected_next_unit']=='E008-M59 high-path tail-slot leakage-safe goal-evaluation smoke'
print('m58 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/trajectory_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/high_path_tail_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/high_path_tail_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/policy_materialization_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/m49_order_preservation_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/tail_slot_policy_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/source_gap_recovery_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/source_gap_episode_recovery_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/input_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/m59_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/trajectory_execution_plan_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/high_path_tail_candidate_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/route_decision_rows.jsonl`

## E008-M59

Implementation unit: `E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0`.

Facts:

- Status: `e008_m59_high_path_tail_slot_goal_evaluation_smoke_ready`.
- Candidate-goal eval rows: 648.
- Scan-policy rows: 144.
- Aggregate policy rows: 8.
- Source-boundary aggregate rows: 16.
- Primary eval metric: `any_viewpoint_xz_1p0`.
- Eval-only goal/viewpoint policy leakage: false.
- New policy: `h001_task_conditioned_high_path_tail_slot_budget5_v3`.
- New policy full/source-gap `GoalEvalProxySR`: 1.0000 / 1.0000.
- Base H001 v2 full/source-gap `GoalEvalProxySR`: 0.6667 / 0.3333.
- Task-agnostic source-diverse full/source-gap `GoalEvalProxySR`: 0.6667 / 0.3333.
- Detector-confidence full/source-gap `GoalEvalProxySR`: 0.5000 / 0.0000.
- Source-gap contexts recovered vs base H001 v2: 6.
- Source-gap contexts lost vs base H001 v2: 0.
- Ready for M60 trajectory contract: true.
- Final real navigation `SR` / `SPL` ready: false.
- Human intent main claim ready: false.
- Deployable search policy ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Selected next unit: E008-M60 high-path tail-slot trajectory contract and Docker preflight.

Claim boundary:

- M59 uses `ObjectNav` goal/viewpoint fields only after M58 fixed policy order.
- M59 supports a leakage-safe goal-evaluation proxy improvement, not final real navigation `SR` / `SPL`.
- M59 indicates the high-path tail slot is worth trajectory execution because source-gap proxy `SR` improves without full-denominator proxy `SR` loss.
- M59 does not make human intent a main contribution; structured task context remains a secondary memory-trust/re-observation condition.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m59_high_path_tail_slot_goal_evaluation_smoke.py
```

Verification:

```bash
python -m py_compile experiments/E008_real_navigation_benchmark/tools/run_m59_high_path_tail_slot_goal_evaluation_smoke.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m59_high_path_tail_slot_goal_evaluation_smoke_ready'
assert c['candidate_goal_eval_rows']==648
assert c['scan_policy_metric_rows']==144
assert c['leakage_audit_pass'] is True
assert c['m58_full_primary_proxy_sr']==1.0
assert c['m58_source_gap_primary_proxy_sr']==1.0
assert c['base_h001_source_gap_primary_proxy_sr']==0.333333
assert c['source_gap_recovered_vs_base_context_rows']==6
assert c['source_gap_lost_vs_base_context_rows']==0
assert c['ready_for_m60_trajectory_contract'] is True
assert c['real_navigation_sr_spl_ready'] is False
assert c['selected_next_unit']=='E008-M60 high-path tail-slot trajectory contract and Docker preflight'
print('m59 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0/high_path_tail_candidate_goal_eval_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0/high_path_tail_policy_goal_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0/pairwise_policy_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0/source_gap_goal_recovery_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0/m60_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0/high_path_tail_candidate_goal_eval_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0/high_path_tail_policy_goal_metric_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0/route_decision_rows.jsonl`

## E008-M60

Implementation unit: `E008-M60_high_path_tail_slot_trajectory_contract_v0`.

Facts:

- Status: `e008_m60_high_path_tail_slot_trajectory_contract_ready_runner_next`.
- Input M58 status: `e008_m58_source_gap_high_path_tail_slot_policy_materialization_ready`.
- Input M59 status: `e008_m59_high_path_tail_slot_goal_evaluation_smoke_ready`.
- Candidate rows: 648.
- Execution plan rows: 144.
- Execute-in-runner rows: 144.
- Policy count: 8.
- H001 policy: `h001_task_conditioned_high_path_tail_slot_budget5_v3`.
- M59 method full/source-gap `GoalEvalProxySR`: 1.0000 / 1.0000.
- M59 base H001 v2 full/source-gap `GoalEvalProxySR`: 0.6667 / 0.3333.
- M59 source-gap recovered contexts vs base H001 v2: 6.
- M59 source-gap lost contexts vs base H001 v2: 0.
- M37 runner py_compile pass: true.
- M61 runner py_compile pass: true.
- Docker preflight pass: true.
- `nvidia-smi` pass: true.
- Scene files ready: 2 / 2.
- Navmesh files ready: 2 / 2.
- `ObjectNav` content files ready: 2.
- Final real navigation `SR` / `SPL` ready: false.
- Human intent main claim ready: false.
- Deployable search policy ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Selected next unit: E008-M61 high-path tail-slot trajectory execution smoke.

Claim boundary:

- M60 is a contract and preflight unit only.
- M60 carries forward the M59 leakage-safe proxy gain as a trajectory-execution precondition.
- M60 does not execute `Habitat` trajectories and does not report final real navigation `SR` / `SPL`.
- Structured task context remains a memory-trust/re-observation condition, not a natural-language human-intent claim.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m60_high_path_tail_slot_trajectory_contract.py
```

M61 command contract:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp -v /home/yoohyun/research3/local_dataset/data:/data:ro -v /home/yoohyun/research2:/work -w /work research3/habitat-h001:20260508-calib-artifacts bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m61_high_path_tail_slot_trajectory_execution_smoke.py"
```

Verification:

```bash
python -m py_compile \
  experiments/E008_real_navigation_benchmark/tools/plan_m60_high_path_tail_slot_trajectory_contract.py \
  experiments/E008_real_navigation_benchmark/tools/run_m61_high_path_tail_slot_trajectory_execution_smoke.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M60_high_path_tail_slot_trajectory_contract_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m60_high_path_tail_slot_trajectory_contract_ready_runner_next'
assert c['trajectory_candidate_rows']==648
assert c['trajectory_execution_plan_rows']==144
assert c['execute_in_next_runner_rows']==144
assert c['runner_py_compile_pass'] is True
assert c['docker_preflight_pass'] is True
assert c['m59_method_source_gap_GoalEvalProxySR']==1.0
assert c['m59_base_source_gap_GoalEvalProxySR']==0.333333
assert c['m59_source_gap_recovered_context_rows']==6
assert c['m59_source_gap_lost_context_rows']==0
assert c['real_navigation_sr_spl_ready'] is False
assert c['selected_next_unit']=='E008-M61 high-path tail-slot trajectory execution smoke'
print('m60 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M60_high_path_tail_slot_trajectory_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M60_high_path_tail_slot_trajectory_contract_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M60_high_path_tail_slot_trajectory_contract_v0/trajectory_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M60_high_path_tail_slot_trajectory_contract_v0/trajectory_execution_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M60_high_path_tail_slot_trajectory_contract_v0/metric_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M60_high_path_tail_slot_trajectory_contract_v0/m59_goal_eval_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M60_high_path_tail_slot_trajectory_contract_v0/runner_compatibility_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M60_high_path_tail_slot_trajectory_contract_v0/docker_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M60_high_path_tail_slot_trajectory_contract_v0/m61_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M60_high_path_tail_slot_trajectory_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M60_high_path_tail_slot_trajectory_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M60_high_path_tail_slot_trajectory_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M60_high_path_tail_slot_trajectory_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M60_high_path_tail_slot_trajectory_contract_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M60_high_path_tail_slot_trajectory_contract_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M60_high_path_tail_slot_trajectory_contract_v0/trajectory_execution_plan_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M60_high_path_tail_slot_trajectory_contract_v0/m61_command_rows.jsonl`

## E008-M61

Implementation unit: `E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0`.

Facts:

- Status: `e008_m61_high_path_tail_slot_trajectory_execution_smoke_ready`.
- Inside Docker: true.
- Input M60 status: `e008_m60_high_path_tail_slot_trajectory_contract_ready_runner_next`.
- Candidate rows: 648.
- Execution plan rows: 144.
- Expected scan-task-policy rows: 144.
- Scan-task-policy rows: 144.
- Trajectory attempt rows: 472.
- Trajectory success rows: 80.
- Trajectory failure rows: 64.
- Overall trajectory `SR`: 0.5556.
- Overall trajectory `SPL`: 0.2821.
- Leakage audit pass: true.
- Policy count: 8.
- Scene count: 2.
- Scene error rows: 0.
- H001 high-path tail-slot `SR` / `SPL`: 1.0000 / 0.3961.
- Base H001 v2 `SR` / `SPL`: 0.6667 / 0.3226.
- Task-agnostic source-diverse `SR` / `SPL`: 0.6667 / 0.3226.
- Detector-confidence `SR` / `SPL`: 0.5000 / 0.3734.
- Fixed current top-k `SR` / `SPL`: 0.5000 / 0.3734.
- Static stale memory `SR` / `SPL`: 0.0000 / 0.0000.
- H001 high-path tail-slot pairwise delta vs base H001 v2: `SR` +0.3333, `SPL` +0.0735.
- H001 high-path tail-slot pairwise delta vs task-agnostic source-diverse: `SR` +0.3333, `SPL` +0.0735.
- H001 high-path tail-slot pairwise delta vs detector/fixed: `SR` +0.5000, `SPL` +0.0228.
- Final real navigation `SR` / `SPL` ready: false.
- Human intent main claim ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Selected next unit: E008-M62 high-path tail-slot trajectory result interpretation and scale decision.

Claim boundary:

- M61 executes the M60 high-path tail-slot rows in Docker `Habitat`.
- M61 is a controlled 18 scan-task-row trajectory smoke, not a final scaled navigation benchmark.
- `ObjectNav` goal/viewpoints are used only after stops for metric computation.
- Structured task context remains conditional memory trust/re-observation, not natural-language intent.

Command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp -v /home/yoohyun/research3/local_dataset/data:/data:ro -v /home/yoohyun/research2:/work -w /work research3/habitat-h001:20260508-calib-artifacts bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m61_high_path_tail_slot_trajectory_execution_smoke.py"
```

Verification:

```bash
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m61_high_path_tail_slot_trajectory_execution_smoke_ready'
assert c['scan_task_policy_rows']==144
assert c['trajectory_candidate_rows']==648
assert c['trajectory_execution_plan_rows']==144
assert c['leakage_audit_pass'] is True
assert c['uses_objectnav_eval_goal_or_viewpoint_for_policy'] is False
assert c['selected_next_unit']=='E008-M62 high-path tail-slot trajectory result interpretation and scale decision'
print('m61 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0/dynamic_stale_trajectory_attempt_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0/dynamic_stale_trajectory_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0/dynamic_stale_trajectory_failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0/pairwise_policy_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0/old_location_dead_end_outcome_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0/scene_execution_meta.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0/dynamic_stale_trajectory_attempt_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0/dynamic_stale_trajectory_policy_metric_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0/route_decision_rows.jsonl`

## E008-M62

Implementation unit: `E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0`.

Facts:

- Status: `e008_m62_high_path_tail_slot_result_interpretation_scale_decision_ready`.
- Input M61 status: `e008_m61_high_path_tail_slot_trajectory_execution_smoke_ready`.
- M61 scan-task-policy rows: 144.
- Policy result rows: 8.
- Pairwise decision rows: 7.
- Source-boundary rows: 26.
- Task-context effect rows: 3.
- Scale gates: 10 pass / 1 warning / 5 fail.
- H001 high-path tail-slot `SR` / `SPL`: 1.0000 / 0.3961.
- Detector-confidence `SR` / `SPL`: 0.5000 / 0.3734.
- Task-agnostic source-diverse `SR` / `SPL`: 0.6667 / 0.3226.
- Source-gap recovery supported: true.
- Source-ready efficiency warning: true.
- Diagnostic navigation table ready: true.
- Scale-up contract ready: true.
- Final real navigation `SR` / `SPL` ready: false.
- Human intent main claim ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Selected next unit: E008-M63 high-path tail-slot scale-up contract and source-boundary baseline plan.

Claim boundary:

- M62 promotes M61 only to bounded diagnostic navigation evidence.
- M62 does not claim final real navigation `SR` / `SPL`, deployable search policy, final real RGB-D/open-vocabulary robustness, or human intent as a main contribution.
- M63 must preserve source-ready efficiency reporting because H001 high-path `SPL` on source-ready rows is lower than detector/fixed source-ready `SPL`.
- M63 must define scale, heldout transfer, and stronger navigation/search baseline requirements before broader reruns.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m62_high_path_tail_slot_result_interpretation_scale_decision.py
```

Verification:

```bash
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m62_high_path_tail_slot_result_interpretation_scale_decision_ready'
assert c['diagnostic_navigation_table_ready'] is True
assert c['scale_up_contract_ready'] is True
assert c['source_gap_recovery_supported'] is True
assert c['source_ready_efficiency_warning'] is True
assert c['final_real_navigation_sr_spl_ready'] is False
assert c['selected_next_unit']=='E008-M63 high-path tail-slot scale-up contract and source-boundary baseline plan'
print('m62 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0/policy_result_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0/pairwise_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0/source_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0/task_context_effect_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0/scale_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0/paper_navigation_table_rows.csv`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0/coverage.json`
- `local_dataset/HM3D_navigation_bridge/E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0/policy_result_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0/route_decision_rows.jsonl`

## E008-M63

Implementation unit: `E008-M63_high_path_tail_slot_scaleup_contract_v0`.

Facts:

- Status: `e008_m63_high_path_tail_slot_scaleup_contract_ready`.
- Selected denominator: `val_mini_full_episode_scale`.
- Selected episode rows: 30.
- Selected scan-task context rows: 90.
- Selected core scan-task-policy rows: 720.
- Expected render frames: 1,080.
- Holdout episode rows: 24.
- Source-boundary guard rows: 5.
- Baseline plan rows: 11.
- External navigation baselines integrated: false.
- Long job launched: false.
- Final real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M64 full-val-mini high-path scale denominator materialization.

Claim boundary:

- M63 is a contract unit only.
- M63 fixes scale, source-ready/source-gap reporting, heldout split, baseline plan, and M64 materialization route.
- M63 does not materialize full-val-mini rows, render frames, run detector inference, validate candidates, or execute trajectories.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m63_high_path_tail_slot_scaleup_contract.py
```

Verification:

```bash
python -m py_compile experiments/E008_real_navigation_benchmark/tools/plan_m63_high_path_tail_slot_scaleup_contract.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M63_high_path_tail_slot_scaleup_contract_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m63_high_path_tail_slot_scaleup_contract_ready'
assert c['m64_contract_ready'] is True
assert c['selected_denominator_id']=='val_mini_full_episode_scale'
assert c['selected_episode_rows']==30
assert c['selected_scan_task_context_rows']==90
assert c['selected_core_scan_task_policy_rows']==720
assert c['selected_expected_render_frames']==1080
assert c['selected_holdout_episode_rows']==24
assert c['launch_long_job_now'] is False
assert c['final_real_navigation_sr_spl_ready'] is False
assert c['selected_next_unit']=='E008-M64 full-val-mini high-path scale denominator materialization'
print('m63 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M63_high_path_tail_slot_scaleup_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M63_high_path_tail_slot_scaleup_contract_v0/objectnav_source_inventory_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M63_high_path_tail_slot_scaleup_contract_v0/scale_denominator_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M63_high_path_tail_slot_scaleup_contract_v0/split_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M63_high_path_tail_slot_scaleup_contract_v0/policy_suite_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M63_high_path_tail_slot_scaleup_contract_v0/source_boundary_guard_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M63_high_path_tail_slot_scaleup_contract_v0/baseline_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M63_high_path_tail_slot_scaleup_contract_v0/m64_materialization_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M63_high_path_tail_slot_scaleup_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M63_high_path_tail_slot_scaleup_contract_v0/report.md`

## E008-M64

Implementation unit: `E008-M64_full_val_mini_high_path_scale_materialization_v0`.

Facts:

- Status: `e008_m64_full_val_mini_high_path_scale_materialization_ready`.
- Episode rows: 30.
- Episode-task-context rows: 90.
- Observation pose rows: 270.
- Planned render frames: 1,080.
- Detector manifest rows: 30.
- Core policy execution plan rows: 720.
- Seen M61 reference episodes: 6.
- Unseen holdout episodes: 24.
- Prompt labels: 8.
- Leakage audit rows: 5 / blocked-field hits 0.
- Candidate rows materialized now: 0.
- Long job launched: false.
- Final real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M65 full-val-mini render frame staging and detector candidate-source contract.

Claim boundary:

- M64 materializes the full `val_mini` denominator and policy plan only.
- M64 does not render RGB-D frames, run open-vocabulary detector inference, validate candidate coordinates, or execute `Habitat` trajectories.
- The two failing gates, `candidate_source_rows_ready` and `full_val_mini_trajectory_execution_ready`, block final navigation claims but do not block M64 completion.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m64_full_val_mini_high_path_scale_materialization.py
```

Verification:

```bash
python -m py_compile experiments/E008_real_navigation_benchmark/tools/plan_m64_full_val_mini_high_path_scale_materialization.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M64_full_val_mini_high_path_scale_materialization_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m64_full_val_mini_high_path_scale_materialization_ready'
assert c['episode_rows']==30
assert c['episode_task_context_rows']==90
assert c['observation_pose_rows']==270
assert c['render_plan_rows']==1080
assert c['detector_manifest_rows']==30
assert c['policy_execution_plan_rows']==720
assert c['seen_m61_reference_episode_rows']==6
assert c['holdout_episode_rows']==24
assert c['full_val_mini_materialization_ready'] is True
assert c['candidate_rows_materialized_now']==0
assert c['long_job_launched'] is False
assert c['final_real_navigation_sr_spl_ready'] is False
assert c['selected_next_unit']=='E008-M65 full-val-mini render frame staging and detector candidate-source contract'
print('m64 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M64_full_val_mini_high_path_scale_materialization_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M64_full_val_mini_high_path_scale_materialization_v0/val_mini_episode_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M64_full_val_mini_high_path_scale_materialization_v0/episode_task_context_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M64_full_val_mini_high_path_scale_materialization_v0/observation_pose_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M64_full_val_mini_high_path_scale_materialization_v0/render_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M64_full_val_mini_high_path_scale_materialization_v0/detector_manifest_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M64_full_val_mini_high_path_scale_materialization_v0/prompt_set.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M64_full_val_mini_high_path_scale_materialization_v0/core_policy_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M64_full_val_mini_high_path_scale_materialization_v0/source_boundary_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M64_full_val_mini_high_path_scale_materialization_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M64_full_val_mini_high_path_scale_materialization_v0/m65_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M64_full_val_mini_high_path_scale_materialization_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M64_full_val_mini_high_path_scale_materialization_v0/render_inputs/render_plan_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M64_full_val_mini_high_path_scale_materialization_v0/detector_inputs/real_proposal_query_manifest.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M64_full_val_mini_high_path_scale_materialization_v0/detector_inputs/prompt_set.json`

## E008-M65

Implementation unit: `E008-M65_full_val_mini_render_detector_contract_v0`.

Facts:

- Status: `e008_m65_full_val_mini_render_detector_contract_ready`.
- Render plan rows: 1,080.
- Detector manifest rows: 30.
- Detector object target rows: 44.
- Prompt labels: 8.
- Expected render frame files: 3,270.
- Docker direct preflight: pass.
- `research3/habitat-h001:20260508-calib-artifacts` image preflight: pass.
- `research2/real-smoke:latest` image preflight: pass.
- Long job launched: false.
- Render job launched: false.
- Detector job launched: false.
- Final real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M66 full-val-mini render frame staging background launch.

Claim boundary:

- M65 fixes the render/detector input contract and long-job ledger only.
- M65 does not render RGB-D frames, run open-vocabulary detector inference, validate candidate coordinates, or execute `Habitat` trajectories.
- M66 must render and verify all 1,080 RGB-D/pose frames before M67 detector inference starts.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m65_full_val_mini_render_detector_contract.py
```

Verification:

```bash
python -m py_compile \
  experiments/E008_real_navigation_benchmark/tools/plan_m65_full_val_mini_render_detector_contract.py \
  experiments/E008_real_navigation_benchmark/tools/verify_m66_full_val_mini_render_frame_staging.py
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M65_full_val_mini_render_detector_contract_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m65_full_val_mini_render_detector_contract_ready'
assert c['render_plan_rows']==1080
assert c['detector_manifest_rows']==30
assert c['detector_object_target_rows']==44
assert c['prompt_label_count']==8
assert c['expected_render_frame_files']==3270
assert c['long_job_launched'] is False
assert c['render_frames_ready'] is False
assert c['detector_candidate_rows_ready'] is False
assert c['real_navigation_sr_spl_ready'] is False
assert c['selected_next_unit']=='E008-M66 full-val-mini render frame staging background launch'
print('m65 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M65_full_val_mini_render_detector_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M65_full_val_mini_render_detector_contract_v0/render_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M65_full_val_mini_render_detector_contract_v0/detector_manifest_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M65_full_val_mini_render_detector_contract_v0/detector_object_target_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M65_full_val_mini_render_detector_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M65_full_val_mini_render_detector_contract_v0/long_job_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M65_full_val_mini_render_detector_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M65_full_val_mini_render_detector_contract_v0/render_inputs/render_plan_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M65_full_val_mini_render_detector_contract_v0/render_inputs/render_m65.py`
- `local_dataset/HM3D_navigation_bridge/E008-M65_full_val_mini_render_detector_contract_v0/detector_inputs/real_proposal_query_manifest.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M65_full_val_mini_render_detector_contract_v0/detector_inputs/real_proposal_object_targets.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M65_full_val_mini_render_detector_contract_v0/detector_inputs/prompt_set.json`
- `local_dataset/HM3D_navigation_bridge/E008-M65_full_val_mini_render_detector_contract_v0/detector_inputs/proposal_output_schema.json`

## E008-M66

Implementation unit: `E008-M66_full_val_mini_render_frame_staging_v0`.

Facts:

- Initial launch status: `e008_m66_full_val_mini_render_frame_staging_launched`.
- Initial verification status: `e008_m66_full_val_mini_render_frame_staging_verification_failed`.
- Initial ready frames: 1,068 / 1,080.
- Initial ready scans: 27 / 30.
- Repair reason: 12 invalid radius-3.0 shell snaps.
- Repair route: same-scan/yaw ready-shell fallback pose patch.
- Repaired verification status: `e008_m66_full_val_mini_render_frame_staging_verified_with_snap_warnings`.
- Repaired ready frames: 1,080 / 1,080.
- Repaired ready scans: 30 / 30.
- Snap-ready rows: 1,080 / 1,080.
- Large snap warning rows: 20.
- Max snap distance: 3.4857m.
- Detector input files ready: true.
- Final real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M67 full-val-mini detector candidate-source background launch.

Claim boundary:

- M66 verifies frame staging only.
- M66 does not run open-vocabulary detector inference, validate candidate coordinates, or execute `Habitat` trajectories.
- Large snap warnings must stay visible in later candidate/navmesh validation.

Commands:

```bash
python experiments/E008_real_navigation_benchmark/tools/launch_m66_full_val_mini_render_frame_staging.py
python experiments/E008_real_navigation_benchmark/tools/repair_m66_full_val_mini_render_frame_staging.py
python experiments/E008_real_navigation_benchmark/tools/verify_m66_full_val_mini_render_frame_staging.py --require-ready
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M65_full_val_mini_render_detector_contract_v0/verification_coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M65_full_val_mini_render_detector_contract_v0/verification_frame_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M65_full_val_mini_render_detector_contract_v0/verification_scan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M65_full_val_mini_render_detector_contract_v0/verification_issue_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M65_full_val_mini_render_detector_contract_v0/verification_report.md`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M66_full_val_mini_render_frame_staging_repair_v0/repair_coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M66_full_val_mini_render_frame_staging_repair_v0/fallback_repair_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M66_full_val_mini_render_frame_staging_repair_v0/patched_render_plan_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M65_full_val_mini_render_detector_contract_v0/3RScan/scans/*/sequence/frame-*.color.jpg`
- `local_dataset/HM3D_navigation_bridge/E008-M65_full_val_mini_render_detector_contract_v0/3RScan/scans/*/sequence/frame-*.depth.pgm`
- `local_dataset/HM3D_navigation_bridge/E008-M65_full_val_mini_render_detector_contract_v0/3RScan/scans/*/sequence/frame-*.pose.txt`

## E008-M67

Implementation unit: `E008-M67_full_val_mini_detector_candidate_source_v0`.

Facts:

- Status: `e008_m16_non_oracle_observation_expansion_detector_candidate_smoke_ready`.
- tmux session: `e008_m67_full_val_mini_detector`.
- Log: `logs/20260531_230150_e008_m67_full_val_mini_detector.log`.
- Working directory: `/home/yoohyun/research2`.
- Output path: `experiments/E008_real_navigation_benchmark/artifacts/E008-M67_full_val_mini_detector_candidate_source_v0/`.
- Expected files: `coverage.json`, `container_output/real_proposals.jsonl`, `container_output/pre_cap_candidate_pool.jsonl`, `validator/coverage.json`, `matching/coverage.json`.
- Verification command: `python experiments/E008_real_navigation_benchmark/tools/verify_m16_non_oracle_observation_expansion_detector_candidate_smoke.py --m15-artifact-dir /home/yoohyun/research2/experiments/E008_real_navigation_benchmark/artifacts/E008-M65_full_val_mini_render_detector_contract_v0 --m15-data-dir /home/yoohyun/research2/local_dataset/HM3D_navigation_bridge/E008-M65_full_val_mini_render_detector_contract_v0 --m16-dir /home/yoohyun/research2/experiments/E008_real_navigation_benchmark/artifacts/E008-M67_full_val_mini_detector_candidate_source_v0 --tmux-session e008_m67_full_val_mini_detector --require-ready`.
- Raw predictions: 19,061.
- Pre-cap candidate rows: 18,196.
- Final proposal rows: 973.
- Coordinate candidate rows: 973.
- Frames with written predictions: 696 / 1,080.
- Scan coverage: 30 / 30 scans have at least one final proposal.
- Validator errors / warnings: 0 / 0.
- Blocked leakage-field hits in final proposal rows: 0.
- Matching target rows: 0.
- M67 gate verdict: pass to E008-M68 source-readiness/navmesh validation; detector target-recall claim remains blocked because the current matcher has no target rows.
- Final real navigation `SR` / `SPL` ready: false.

Claim boundary:

- M67 launch does not yet prove detector candidate quality.
- Detector completion, matching, navmesh validation, candidate visit-order, and trajectory execution remain future units.
- M67 completion does not prove target recall because `matching_target_rows=0`.
- M67 completion is only a source-generation gate for M68.

Result interpretation gate:

| Verdict | Criteria | Next action |
| --- | --- | --- |
| pass to M68 | Job completes; required files exist; validator errors are 0; detector manifest coverage is 30 / 30 scans; final proposal rows are at least 300; pre-cap candidate rows are at least 3,000; at least 24 / 30 scans have at least one final proposal; at least 4 / 6 target category groups have at least one final proposal; all policy-input rows avoid `ObjectNav` eval goal/viewpoint fields. | Run E008-M68 as the main navmesh validation route. |
| warning to M68 diagnostic | Job completes and validator errors are 0, but final proposal rows are 50-299, or only 12-23 scans have proposals, or fewer than 4 category groups appear, or matching/recall is weak while coordinate fields are finite. | Run E008-M68 as diagnostic-only and record source-gap / detector-recall boundary before trajectory planning. |
| fail / repair first | Job fails; required files are missing; validator errors are nonzero; final proposal rows are 0-49; fewer than 12 scans have proposals; coordinate fields are missing/non-finite for more than 5% of rows; pre-cap pool is missing when final rows are weak; or any policy-input artifact uses `ObjectNav` eval goal/viewpoint, target UID, target instance ID, success label, or candidate-to-target distance. | Do not run M68 as a main route. First repair detector output, label/prompt cleanup, or coordinate export. |

M67 row-count threshold rationale:

- M67 is a bridge to navmesh validation, not a final detector-quality table.
- The 300 final-proposal threshold is a minimum scale gate: it is roughly 10 proposals per full `val_mini` episode and is enough to expose scan/category/source-ready failures in M68.
- The 3,000 pre-cap threshold keeps failure analysis possible if final proposals are over-filtered.
- Even a pass does not support final real RGB-D/open-vocabulary robustness because M68/M69 still need navmesh/path/source-ready and trajectory evidence.

M67 verdict:

- Result: pass to M68 source-readiness/navmesh validation.
- Reason: required files exist, validator errors are 0, final proposal rows 973, pre-cap candidate rows 18,196, scan coverage 30 / 30, target category groups covered 6 / 6, and blocked leakage-field hits are 0.
- Boundary: `matching_target_rows=0`, so M67 cannot support detector target recall, real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.

Launch command:

```bash
tmux new-session -d -s e008_m67_full_val_mini_detector "cd /home/yoohyun/research2 && python /home/yoohyun/research2/experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py --dataset-root /home/yoohyun/research2/local_dataset/HM3D_navigation_bridge/E008-M65_full_val_mini_render_detector_contract_v0 --m17-dir /home/yoohyun/research2/local_dataset/HM3D_navigation_bridge/E008-M65_full_val_mini_render_detector_contract_v0/detector_inputs --out-dir /home/yoohyun/research2/experiments/E008_real_navigation_benchmark/artifacts/E008-M67_full_val_mini_detector_candidate_source_v0 --max-scans 30 --max-frames-per-scan 36 --max-labels 8 --max-predictions 60000 --max-predictions-per-frame 100 --threshold 0.08 --text-threshold 0.08 --candidate-selection-policy cap_aware_label_balanced_ranking_v0 --selection-score-mode confidence_log_depth --pre-cap-per-scan-label-cap 24 --pre-cap-spatial-consolidation-radius-m 0.5 --raw-candidate-collection-cap 300000 --export-pre-cap-candidate-pool > /home/yoohyun/research2/logs/20260531_230150_e008_m67_full_val_mini_detector.log 2>&1"
```

## E008-M68

Implementation unit: `E008-M68_full_val_mini_detector_candidate_navmesh_validation_v0`.

Purpose:

- Validate whether M67 detector candidates are usable as navigation candidates before any visit-order, goal-evaluation, or trajectory execution claim.
- Separate detector absence, coordinate failure, snap failure, path-unreachable cases, and source-ready candidates.

Inputs:

- M67 `container_output/real_proposals.jsonl`.
- M67 `container_output/pre_cap_candidate_pool.jsonl`.
- M67 `validator/coverage.json` and `matching/coverage.json`.
- M65 detector manifest and object target rows.
- M66 frame verification rows and snap-warning rows.
- Read-only `HM3D ObjectNav` / `Habitat` data from `/home/yoohyun/research3/local_dataset/data`.
- Derived E008 bridge root under `local_dataset/HM3D_navigation_bridge/`.

Allowed policy-independent fields:

- `scan_id`, `episode_id`, frame id, prompt/category label, detector confidence, depth/backprojection coordinates, source frame pose, proposal support fields, M66 snap-warning status, episode start pose, scene path, and navmesh path.

Blocked policy/evaluation-leakage fields:

- `ObjectNav` eval goal position.
- `ObjectNav` eval viewpoint list.
- target object UID or instance ID.
- target match distance.
- success/failure label.
- any candidate-to-goal or candidate-to-target distance before policy ranking.

Validation steps:

1. Preserve every M67 final proposal row and attach a validation status; do not silently drop failed candidates.
2. Check coordinate finiteness, frame/scan/episode join, and category/prompt join.
3. Snap each candidate point to the corresponding `HM3D` navmesh.
4. Compute source-to-snapped-candidate path availability from the episode start pose.
5. Record snap distance and flag candidates affected by M66 large snap-warning frames.
6. Aggregate scan-level and episode-task-context source-ready / source-gap rows.
7. Produce failure taxonomy before any visit-order or trajectory unit starts.

Outputs:

- `coverage.json`
- `candidate_navmesh_validation_rows.jsonl`
- `candidate_failure_rows.jsonl`
- `scan_source_boundary_rows.jsonl`
- `episode_task_source_ready_rows.jsonl`
- `snap_warning_overlap_rows.jsonl`
- `failure_taxonomy_rows.jsonl`
- `route_decision_rows.jsonl`
- `claim_boundary_rows.jsonl`
- `report.md`

M68 pass / warning / fail gate:

| Verdict | Criteria | Next action |
| --- | --- | --- |
| pass to visit-order / path smoke | At least 24 / 30 scans have one path-ready candidate; at least 70% of final proposal rows are coordinate-valid; at least 60% are snapped successfully; at least 50% have a source-to-candidate path from the episode start; no single coordinate-frame bug explains most failures; M66 snap-warning rows are reported separately. | Materialize E008-M69 visit-order/path rows. |
| warning diagnostic | 12-23 scans have path-ready candidates, or path-ready row rate is 20-49%, or one/two categories are missing but the failure taxonomy is clear. | Continue only as diagnostic or repair candidate-source before trajectory execution. |
| fail / repair first | Fewer than 12 scans have path-ready candidates; path-ready row rate is below 20%; coordinate convention appears globally wrong; snap failures dominate; or leakage fields are found in policy inputs. | Stop before visit-order/path smoke and repair coordinate projection, frame alignment, or candidate generation. |

Result:

- Status: `e008_m68_full_val_mini_detector_candidate_navmesh_validation_ready`.
- Gate verdict: pass / `m68_pass_source_ready_for_visit_order_path_smoke`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m68_full_val_mini_detector_candidate_navmesh_validation.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M68_full_val_mini_detector_candidate_navmesh_validation_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M68_full_val_mini_detector_candidate_navmesh_validation_v0/`.
- Candidate rows: 973.
- Coordinate-valid rows: 973 / 973.
- Snapped navigable rows: 971 / 973.
- Source-to-snapped path rows: 900 / 973.
- Path-ready scans: 30 / 30.
- Source-ready episode-task rows: 90 / 90.
- Snap-warning candidate rows: 22.
- Failure rows: `blocked_snapped_point_unreachable_from_episode_start` 71, `blocked_snap_failed_non_finite` 2.
- Selected next unit: E008-M69 full-val-mini detector candidate visit-order/path smoke.

Claim boundary:

- M68 can support a source-readiness or source-gap claim only.
- M68 cannot support real navigation `SR` / `SPL`, deployable search policy, or final RGB-D/open-vocabulary robustness.
- Final navigation evidence requires later visit-order, leakage-safe goal evaluation, `Habitat` trajectory execution, and baseline comparison.

## E008-M69

Implementation unit: `E008-M69_full_val_mini_detector_candidate_visit_order_path_smoke_v0`.

Purpose:

- Materialize detector candidate visit-order and source-to-candidate path-cost rows from M68 source-ready candidates.
- Keep non-path-ready candidates as explicit failure/accounting rows.
- Repeat scan-level detector metrics over 90 structured episode-task contexts for denominator accounting only.

Result:

- Status: `e008_m69_full_val_mini_detector_candidate_visit_order_path_smoke_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m69_full_val_mini_detector_candidate_visit_order_path_smoke.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M69_full_val_mini_detector_candidate_visit_order_path_smoke_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M69_full_val_mini_detector_candidate_visit_order_path_smoke_v0/`.
- Query-compatible candidate rows: 973 / 973.
- Path-ready candidate rows: 900 / 973.
- Failure rows retained: 73.
- Visit-order rows: 3,673.
- Policy metric rows: 124.
- Episode-task policy metric rows: 360.
- Eval-goal/viewpoint fields used for policy: false.
- Detector confidence all-candidate top1-ready scans: 28 / 30.
- Detector confidence reachable-subset top1-ready scans: 30 / 30.
- Mean top5 known path cost: detector confidence reachable subset 14.092071m, path-cost ascending reachable subset 2.088110m, confidence/path-cost tradeoff reachable subset 2.762790m.
- Selected next unit: E008-M70 full-val-mini leakage-safe detector candidate goal-evaluation smoke.

Claim boundary:

- M69 supports visit-order/path-cost smoke only.
- M69 does not claim real navigation `SR` / `SPL`.
- M69 does not claim final real RGB-D/open-vocabulary robustness.
- M69 treats task context as denominator accounting only; detector ordering is task-agnostic in this unit.

## E008-M70

Implementation unit: `E008-M70_full_val_mini_detector_candidate_goal_evaluation_smoke_v0`.

Purpose:

- Score M69 visit-order rows against eval-only `ObjectNav` goal/viewpoint labels.
- Keep goal/viewpoint fields out of policy ranking.
- Produce proxy `GoalEvalProxySR` / `GoalEvalProxySPL` diagnostics before deciding whether trajectory execution is worth launching.

Result:

- Status: `e008_m70_full_val_mini_detector_candidate_goal_evaluation_smoke_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m70_full_val_mini_detector_candidate_goal_evaluation_smoke.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M70_full_val_mini_detector_candidate_goal_evaluation_smoke_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M70_full_val_mini_detector_candidate_goal_evaluation_smoke_v0/`.
- Eval episode rows: 30 / 30.
- Candidate-goal eval rows: 3,673.
- Policy goal metric rows: 124.
- Episode-task goal metric rows: 360.
- Primary metric: `any_viewpoint_xz_1p0`.
- Leakage audit pass: true.
- All detector policies primary hits: 24 / 30.
- Primary `GoalEvalProxySR`: 0.800000 for all detector policies.
- Primary `GoalEvalProxySPL`: detector confidence all candidates 0.350587, detector confidence reachable subset 0.350587, path-cost ascending reachable subset 0.497532, confidence/path-cost tradeoff reachable subset 0.480871.
- Selected next unit: E008-M71 full-val-mini detector-goal failure comparison and trajectory-execution decision.

Claim boundary:

- M70 uses `ObjectNav` goal/viewpoint fields only as evaluation labels.
- M70 supports proxy goal-evaluation diagnostics, not final real navigation `SR` / `SPL`.
- M70 does not resolve M67's matching target row gap, so detector target-recall claim remains blocked.
- M70 keeps task context as denominator accounting only; detector visit order is task-agnostic in this unit.

## E008-M71

Implementation unit: `E008-M71_full_val_mini_detector_goal_failure_comparison_trajectory_decision_v0`.

Purpose:

- Compare M70 detector policy failures before spending Docker trajectory execution.
- Separate source/coverage/threshold failures from path-cost policy evidence.
- Decide whether the next step should be a trajectory execution contract or a repair step.

Result:

- Status: `e008_m71_full_val_mini_detector_goal_failure_comparison_trajectory_decision_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/plan_m71_full_val_mini_detector_goal_failure_comparison_trajectory_decision.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M71_full_val_mini_detector_goal_failure_comparison_trajectory_decision_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M71_full_val_mini_detector_goal_failure_comparison_trajectory_decision_v0/`.
- Eval episodes: 30.
- Minimum detector policy `GoalEvalProxySR`: 0.800000.
- All-policy failure episodes: 6.
- Failure classes: `relaxed_viewpoint_or_goal_near_miss` 2, `moderate_localization_near_miss` 2, `candidate_region_gap` 1, `severe_candidate_source_coverage_gap` 1.
- Best SPL proxy policy: `path_cost_ascending_reachable_subset_v0`, `primary_spl_proxy_mean` 0.497532.
- Max SPL proxy gain over `detector_confidence_reachable_subset_v0`: +0.146945.
- Trajectory contract ready: true.
- Trajectory execution ready now: false.
- Selected next unit: E008-M72 full-val-mini detector-policy trajectory execution contract and Docker preflight.

Claim boundary:

- M71 is a decision artifact, not an executed navigation benchmark.
- M71 supports moving to M72 trajectory contract/preflight, but not final real navigation `SR` / `SPL`.
- The six failed episodes are all-policy detector proxy failures, so they should be reported as detector/source/threshold failures rather than H001 memory-decision evidence.
- Detector target-recall claim remains blocked because M67 matching target rows are still 0.

## E008-M72

Implementation unit: `E008-M72_full_val_mini_detector_policy_trajectory_contract_v0`.

Purpose:

- Convert M69 full-val-mini detector policy visit orders into runner-compatible trajectory candidate rows.
- Copy M70 full-val-mini eval goal rows into contract-local eval/oracle files for the future trajectory runner.
- Fix Docker/data preflight and M73 command ledger without launching a long trajectory job.

Result:

- Status: `e008_m72_full_val_mini_detector_policy_trajectory_contract_ready_runner_next`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/plan_m72_full_val_mini_detector_policy_trajectory_contract.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M72_full_val_mini_detector_policy_trajectory_contract_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M72_full_val_mini_detector_policy_trajectory_contract_v0/`.
- Candidate rows: 3,673.
- Execution plan rows: 120.
- Eval goal rows: 30.
- Oracle path rows: 30.
- Policy ids: `detector_confidence_all_candidates_v0`, `detector_confidence_reachable_subset_v0`, `path_cost_ascending_reachable_subset_v0`, `confidence_path_cost_tradeoff_reachable_subset_v0`.
- Docker preflight pass: true.
- Leakage audit pass: true.
- Full-ranked minimum `GoalEvalProxySR`: 0.800000.
- Budget-5 minimum `GoalEvalProxySR`: 0.266667.
- Runner implemented: true.
- Runner `py_compile` pass: true.
- Selected next unit: E008-M73 full-val-mini detector-policy trajectory execution smoke.

Claim boundary:

- M72 supports trajectory contract/preflight only.
- M72 does not execute `Habitat` trajectories or support real navigation `SR` / `SPL`.
- M72 primary execution mode is full-ranked proxy-to-trajectory consistency, not deployable fixed-budget search.
- Budget-5 proxy weakness must be reported before any deployable search policy claim.

## E008-M73 Runner Scaffold

Implementation unit: `E008-M73_full_val_mini_detector_policy_trajectory_execution_runner_scaffold_v0`.

Purpose:

- Wrap the generalized M37 trajectory runner so it reads M72 contract-local goal/oracle rows.
- Fix detector-policy constants for the full-val-mini detector-policy trajectory execution smoke.
- Verify runner CLI and contract recognition without launching a long Docker trajectory job.

Result:

- Implementation file: `experiments/E008_real_navigation_benchmark/tools/run_m73_full_val_mini_detector_policy_trajectory_execution_smoke.py`.
- `py_compile` pass: true.
- `--help` pass: true.
- M72 re-run status: `e008_m72_full_val_mini_detector_policy_trajectory_contract_ready_runner_next`.
- M72 runner implemented: true.
- Docker trajectory launched: false.
- Selected next unit: E008-M73 full-val-mini detector-policy trajectory execution smoke.

Claim boundary:

- M73 runner scaffold is execution-readiness evidence only.
- It does not produce `Habitat` trajectory `SR` / `SPL`.
- The next Docker execution should be reported as full-ranked proxy-to-trajectory consistency unless fixed-budget results pass separately.

## E008-M73 Execution Smoke

Implementation unit: `E008-M73_full_val_mini_detector_policy_trajectory_execution_smoke_v0`.

Purpose:

- Execute M72 full-val-mini detector-policy rows inside Docker `Habitat`.
- Compare `detector_confidence_*`, `path_cost_ascending_reachable_subset_v0`, and `confidence_path_cost_tradeoff_reachable_subset_v0` under the same 30-episode / 120 scan-task-policy denominator.
- Verify proxy-to-trajectory consistency without using `ObjectNav` goal/viewpoint fields as policy input.

Result:

- Status: `e008_m73_full_val_mini_detector_policy_trajectory_execution_smoke_ready`.
- Launch log: `logs/20260601_122034_e008_m73_full_val_mini_trajectory.log`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M73_full_val_mini_detector_policy_trajectory_execution_smoke_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M73_full_val_mini_detector_policy_trajectory_execution_smoke_v0/`.
- Inside Docker: true.
- Trajectory candidate rows: 3,673.
- Trajectory attempt rows: 1,598.
- Scan-task-policy rows: 120.
- Trajectory success rows: 96.
- Aggregate `trajectory_SR`: 0.800000.
- Mean `trajectory_SPL`: 0.194696.
- Leakage audit pass: true.
- Selected next unit: E008-M74 full-val-mini detector-policy trajectory result interpretation and budget-boundary decision.

Policy aggregates:

| Policy | SR | SPL | PathLengthM mean | CandidateVisits mean |
| --- | ---: | ---: | ---: | ---: |
| `detector_confidence_all_candidates_v0` | 0.800000 | 0.231845 | 65.827022 | 12.333333 |
| `detector_confidence_reachable_subset_v0` | 0.800000 | 0.231845 | 65.827022 | 11.200000 |
| `path_cost_ascending_reachable_subset_v0` | 0.800000 | 0.128254 | 58.602448 | 15.633333 |
| `confidence_path_cost_tradeoff_reachable_subset_v0` | 0.800000 | 0.186839 | 65.066255 | 14.100000 |

Claim boundary:

- M73 is an executed full-ranked detector-policy trajectory smoke, not a final navigation benchmark.
- `SR` is tied across policies, so M73 does not support a positive policy-success claim.
- `path_cost_ascending_reachable_subset_v0` lowers mean path length but loses `SPL` and candidate-visit efficiency against detector-confidence baselines.
- Budget-5 deployability remains blocked by M72/M74, and final real navigation `SR` / `SPL` remains blocked pending source-gap/SPL repair, heldout transfer, and stronger navigation/search baselines.

## E008-M74

Implementation unit: `E008-M74_full_val_mini_detector_policy_result_interpretation_v0`.

Purpose:

- Interpret M73 trajectory results before making any navigation or deployability claim.
- Separate `SR`, `SPL`, path length, candidate visits, source-ready/source-gap behavior, and fixed-budget weakness.
- Decide whether to scale, stop, or repair the detector-policy navigation route.

Result:

- Status: `e008_m74_full_val_mini_detector_policy_result_interpretation_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/plan_m74_full_val_mini_detector_policy_result_interpretation.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M74_full_val_mini_detector_policy_result_interpretation_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M74_full_val_mini_detector_policy_result_interpretation_v0/`.
- M73 trajectory `SR`: 0.800000.
- M73 mean `SPL`: 0.194696.
- Path-cost policy `delta_SPL` vs detector confidence: -0.103591.
- Path-cost policy `delta_PathLengthM` vs detector confidence: -7.224574m.
- Source-gap trajectory `SR`: 0.000000.
- Budget-5 minimum `GoalEvalProxySR`: 0.266667.
- Gate rows: pass 4, warning 1, fail 5.
- Positive navigation policy claim ready: false.
- Final real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M75 full-val-mini source-gap/SPL repair contract.

Policy interpretation:

| Policy | Trajectory SR | Trajectory SPL | Interpretation |
| --- | ---: | ---: | --- |
| `detector_confidence_all_candidates_v0` | 0.800000 | 0.231845 | Matches primary detector `SPL` but keeps unreachable-candidate accounting |
| `detector_confidence_reachable_subset_v0` | 0.800000 | 0.231845 | Best current `SPL` and lowest candidate visits |
| `path_cost_ascending_reachable_subset_v0` | 0.800000 | 0.128254 | Shorter mean path length, but worse `SPL` and visit efficiency |
| `confidence_path_cost_tradeoff_reachable_subset_v0` | 0.800000 | 0.186839 | Does not beat detector confidence on `SR` or `SPL` |

Claim boundary:

- M74 confirms M73 is diagnostic executed trajectory evidence only.
- Do not claim positive navigation-policy superiority because all policies tie at `SR` 0.8.
- Do not claim deployable fixed-budget search because budget-5 proxy `SR` bottoms out at 0.266667.
- Do not claim source-gap recovery because source-gap trajectory `SR` is 0.0.
- The next defensible action is a repair contract that targets source-gap failures and `SPL` / candidate-visit regression before any broader navigation claim.

## E008-M75

Implementation unit: `E008-M75_source_gap_spl_repair_contract_v0`.

Purpose:

- Convert M74's diagnostic failures into a leakage-safe repair contract.
- Separate candidate-source repair from path-cost/SPL guard repair.
- Prevent the next step from launching trajectories before repaired rows and leakage checks exist.

Result:

- Status: `e008_m75_source_gap_spl_repair_contract_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/plan_m75_source_gap_spl_repair_contract.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M75_source_gap_spl_repair_contract_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M75_source_gap_spl_repair_contract_v0/`.
- Source-gap failure episodes: 2.
- Source-ready failure episodes: 4.
- Budget-5 minimum proxy `SR`: 0.266667.
- Path-cost helped / hurt / tied `SPL` rows: 10 / 14 / 6.
- Repair problem rows: 4.
- Policy repair contract rows: 4.
- Input guard rows: 11.
- Gate rows: pass 4, fail 3.
- Trajectory execution ready now: false.
- Selected next unit: E008-M76 full-val-mini source-gap/SPL repair row materialization smoke.

Selected repair contracts:

| policy_id | role | materialize in M76 | expected effect |
| --- | --- | --- | --- |
| `detector_confidence_reachable_subset_v0` | primary baseline to preserve | true | Preserve current best `SPL` / candidate-visit baseline |
| `spl_guarded_confidence_path_tail_budget5_v0` | selected repair candidate | true | Preserve detector-confidence top candidates and use path cost only as guarded tail/tie-breaker |
| `candidate_source_expansion_probe_v0` | source-gap probe, not final policy | true | Separate candidate-source absence from ordering / `SPL` failure |
| `localization_threshold_reporting_v0` | evaluation boundary, not policy | false | Keep near-miss / threshold sensitivity out of policy gain claims |

Claim boundary:

- M75 is a repair contract, not a repaired-policy result.
- Do not claim source-gap recovery until M76 materializes rows and later trajectory/proxy checks support it.
- Do not claim improved `SPL` until the guarded policy is evaluated against detector-confidence baselines.
- Do not use `ObjectNav` goal/viewpoint fields, M71 failure classes, M70 first-hit fields, M73 trajectory success, `SR`, `SPL`, or success proposal ids as policy inputs.

## E008-M76

Implementation unit: `E008-M76_source_gap_spl_repair_row_materialization_smoke_v0`.

Purpose:

- Materialize leakage-safe repair rows from the M75 source-gap/SPL contract.
- Preserve `detector_confidence_reachable_subset_v0` as the primary baseline.
- Add `spl_guarded_confidence_path_tail_budget5_v0` that keeps detector-confidence top-4 and uses path cost only as a bounded tail slot.
- Keep `candidate_source_expansion_probe_v0` as probe-only evidence, not a final source-gap recovery policy.

Result:

- Status: `e008_m76_source_gap_spl_repair_row_materialization_smoke_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m76_source_gap_spl_repair_row_materialization_smoke.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M76_source_gap_spl_repair_row_materialization_smoke_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M76_source_gap_spl_repair_row_materialization_smoke_v0/`.
- Repair candidate rows: 2,700.
- Execution plan rows: 90.
- Goal-eval-ready plan rows: 60.
- Probe-only plan rows: 30.
- Leakage audit pass: true.
- Budget compliance pass: true.
- Guarded policy top-4 preserved: 30/30 plan rows.
- Guarded policy tail inserted: 26/30 plan rows.
- Source-gap reporting episodes: 2.
- Source-ready threshold/boundary failure episodes: 4.
- Trajectory execution ready now: false.
- Selected next unit: E008-M77 full-val-mini source-gap/SPL repair leakage-safe goal-evaluation smoke.

Materialized policies:

| policy_id | role | candidate rows | goal eval next | probe only |
| --- | --- | ---: | --- | --- |
| `detector_confidence_reachable_subset_v0` | primary detector-confidence baseline preserved | 900 | true | false |
| `spl_guarded_confidence_path_tail_budget5_v0` | confidence top-4 + guarded path-cost tail | 900 | true | false |
| `candidate_source_expansion_probe_v0` | source-health probe, not final policy | 900 | false | true |

Claim boundary:

- M76 is row materialization evidence only.
- Do not claim repaired `SR` / `SPL` until M77 proxy evaluation and later trajectory rerun support it.
- Do not claim source-gap recovery from `candidate_source_expansion_probe_v0`; it only separates candidate-source absence from ordering/SPL failure.
- Final real navigation `SR` / `SPL`, deployable search policy, real RGB-D/open-vocabulary robustness, and human-intent main claims remain blocked.

## E008-M77

Implementation unit: `E008-M77_source_gap_spl_repair_goal_evaluation_smoke_v0`.

Purpose:

- Evaluate fixed M76 repair rows against `ObjectNav` goal/viewpoint labels without policy leakage.
- Compare `detector_confidence_reachable_subset_v0` and `spl_guarded_confidence_path_tail_budget5_v0` under full-rank and budget-5 scopes.
- Decide whether the guarded repair is strong enough to promote into a Docker trajectory contract.

Result:

- Status: `e008_m77_source_gap_spl_repair_goal_evaluation_smoke_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m77_source_gap_spl_repair_goal_evaluation_smoke.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M77_source_gap_spl_repair_goal_evaluation_smoke_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M77_source_gap_spl_repair_goal_evaluation_smoke_v0/`.
- Repair visit rows evaluated: 1,800.
- Candidate-goal eval rows: 2,100.
- Scan-policy metric rows: 120.
- Aggregate policy rows: 4.
- Leakage audit pass: true.
- Full-rank baseline vs guarded `GoalEvalProxySR`: 0.8000 vs 0.8000.
- Full-rank baseline vs guarded `GoalEvalProxySPL`: 0.3506 vs 0.3506.
- Budget-5 baseline vs guarded `GoalEvalProxySR`: 0.4333 vs 0.4000.
- Budget-5 baseline vs guarded `GoalEvalProxySPL`: 0.2853 vs 0.2734.
- Budget-5 guarded gain/loss rows: 0 / 1.
- Trajectory contract ready: false.
- Selected next unit: E008-M78 full-val-mini source-gap/SPL repair result interpretation and next-route decision.

Policy aggregate:

| scope | policy_id | primary hits | proxy SR | proxy SPL |
| --- | --- | ---: | ---: | ---: |
| full-rank | `detector_confidence_reachable_subset_v0` | 24/30 | 0.8000 | 0.3506 |
| full-rank | `spl_guarded_confidence_path_tail_budget5_v0` | 24/30 | 0.8000 | 0.3506 |
| budget-5 | `detector_confidence_reachable_subset_v0` | 13/30 | 0.4333 | 0.2853 |
| budget-5 | `spl_guarded_confidence_path_tail_budget5_v0` | 12/30 | 0.4000 | 0.2734 |

Claim boundary:

- M77 supports leakage-safe proxy evaluation of the fixed M76 repair rows.
- M77 does not support a positive repaired policy claim because budget-5 success and `SPL` regress against detector-confidence baseline.
- M77 does not support final real navigation `SR` / `SPL`; no `Habitat` trajectory is executed.
- M77 keeps `candidate_source_expansion_probe_v0` probe-only and does not claim source-gap recovery.

## E008-M78

Implementation unit: `E008-M78_source_gap_spl_repair_result_interpretation_v0`.

Purpose:

- Interpret M77 before launching any new trajectory job.
- Diagnose why `spl_guarded_confidence_path_tail_budget5_v0` regressed under budget-5.
- Decide whether the next route is trajectory promotion, more reranking, diagnostic packaging, or candidate-source expansion.

Result:

- Status: `e008_m78_source_gap_spl_repair_result_interpretation_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/plan_m78_source_gap_spl_repair_result_interpretation.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M78_source_gap_spl_repair_result_interpretation_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M78_source_gap_spl_repair_result_interpretation_v0/`.
- Full-rank guarded vs detector-confidence `GoalEvalProxySR` delta: 0.0000.
- Full-rank guarded vs detector-confidence `GoalEvalProxySPL` delta: 0.0000.
- Budget-5 guarded vs detector-confidence `GoalEvalProxySR` delta: -0.0333.
- Budget-5 guarded vs detector-confidence `GoalEvalProxySPL` delta: -0.0118.
- Budget-5 loss rows: 1.
- Source-gap unresolved rows: 2.
- Direct trajectory promotion ready: false.
- Reranking-only repair sufficient: false.
- Selected next unit: E008-M79 full-val-mini source-gap candidate-source expansion and loss-safe policy contract.

Failure diagnosis:

| case | mechanism | lesson |
| --- | --- | --- |
| `00800-TEEsavR23oF::2` / `tv_monitor` | path-cost tail replaces a detector-confidence rank-5 hit with a near-source false candidate | Do not let path cost evict detector-confidence top-5 without a separate policy-visible reliability gate |
| source-gap rows | full-rank and budget-5 reranking do not recover source-gap rows | Candidate-source expansion or observation coverage must come before additional reranking |

Route decision:

| route | decision |
| --- | --- |
| promote guarded repair to trajectory | reject |
| continue tail-slot reranking only | reject |
| freeze detector-confidence budget-5 as baseline | keep |
| candidate-source expansion + loss-safe policy contract | select |
| stop and package diagnostic boundary | defer |

Claim boundary:

- M78 supports a negative repair interpretation: the M76/M77 guarded tail-slot repair is not ready for trajectory promotion.
- M78 does not support a positive repaired-policy claim, source-gap recovery, deployable fixed-budget search, or final real navigation `SR` / `SPL`.
- M79 must preserve detector-confidence budget safety while adding policy-visible candidate-source evidence.

## E008-M79

Implementation unit: `E008-M79_source_gap_candidate_source_expansion_loss_safe_policy_contract_v0`.

Purpose:

- Convert the M78 negative repair result into a loss-safe source-expansion contract.
- Preserve detector-confidence budget-5 top-5 before any candidate-source expansion.
- Separate source-gap expansion cases from localization/threshold boundary controls.

Result:

- Status: `e008_m79_source_gap_candidate_source_expansion_loss_safe_policy_contract_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/plan_m79_source_gap_candidate_source_expansion_loss_safe_policy_contract.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M79_source_gap_candidate_source_expansion_loss_safe_policy_contract_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M79_source_gap_candidate_source_expansion_loss_safe_policy_contract_v0/`.
- Source-gap expansion cases: 2.
- Budget-5 loss sentinel cases: 1.
- Localization boundary controls: 4.
- Policy contract rows: 5.
- M80 materialize policy rows: 3.
- Detector budget-5 preservation required: true.
- Selected next unit: E008-M80 full-val-mini loss-safe candidate-source expansion row materialization smoke.

Policy contract:

| policy | role | M80 |
| --- | --- | --- |
| `detector_confidence_budget5_core_v0` | loss-safe detector-confidence baseline | materialize |
| `loss_safe_append_source_probe_budget8_v0` | append-only candidate-source probe | materialize |
| `loss_safe_observation_source_expansion_probe_v0` | source/observation expansion plan | materialize |
| `path_cost_secondary_tiebreak_only_v0` | guard rule only | no materialization |
| `localization_threshold_reporting_v0` | claim-boundary reporting | no materialization |

Claim boundary:

- M79 supports the contract that source expansion must be loss-safe relative to detector-confidence budget-5.
- M79 does not support source-gap recovery, deployable search policy, trajectory improvement, or final real navigation `SR` / `SPL`.

## E008-M80

Implementation unit: `E008-M80_loss_safe_candidate_source_expansion_row_materialization_smoke_v0`.

Purpose:

- Materialize the M79 loss-safe source-expansion contract.
- Preserve detector-confidence budget-5 top-5 before any append-only source probe.
- Create source/observation expansion plan rows for unresolved source-gap cases without launching a long job or using eval goal/viewpoint fields.

Result:

- Status: `e008_m80_loss_safe_candidate_source_expansion_row_materialization_smoke_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m80_loss_safe_candidate_source_expansion_row_materialization_smoke.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M80_loss_safe_candidate_source_expansion_row_materialization_smoke_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M80_loss_safe_candidate_source_expansion_row_materialization_smoke_v0/`.
- Candidate visit-order rows: 390.
- Detector budget-5 core rows: 150.
- Loss-safe append policy rows: 240.
- Policy plan rows: 60.
- Source/observation expansion plan rows: 6.
- Budget invariant rows: 30.
- Budget invariant pass: true.
- Top-5 preservation pass rows: 30/30.
- Leakage audit pass: true.
- M81 goal-evaluation input ready: true.
- Selected next unit: E008-M81 full-val-mini loss-safe candidate-source expansion leakage-safe goal-evaluation smoke.

Materialized policies:

| policy | role | rows | next |
| --- | --- | ---: | --- |
| `detector_confidence_budget5_core_v0` | loss-safe detector-confidence budget-5 core | 150 | M81 baseline preservation check |
| `loss_safe_append_source_probe_budget8_v0` | append-only source probe after preserved top-5 | 240 | M81 append-only proxy check |
| `loss_safe_observation_source_expansion_probe_v0` | source/observation expansion plan | 6 plan rows | later non-oracle source expansion planning |

Claim boundary:

- M80 supports loss-safe row materialization and detector-confidence top-5 preservation.
- M80 does not support source-gap recovery, deployable search policy, final RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.

## E008-M81

Implementation unit: `E008-M81_loss_safe_candidate_source_expansion_goal_evaluation_smoke_v0`.

Purpose:

- Evaluate fixed M80 loss-safe source-expansion rows against eval-only goal/viewpoint labels without policy leakage.
- Check that append-only source probes do not change detector-confidence budget-5 behavior.
- Decide whether the next step should be trajectory promotion, source/observation expansion, or result-boundary packaging.

Result:

- Status: `e008_m81_loss_safe_candidate_source_expansion_goal_evaluation_smoke_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m81_loss_safe_candidate_source_expansion_goal_evaluation_smoke.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M81_loss_safe_candidate_source_expansion_goal_evaluation_smoke_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M81_loss_safe_candidate_source_expansion_goal_evaluation_smoke_v0/`.
- Eval episode rows: 30.
- Loss-safe visit rows evaluated: 390.
- Candidate-goal eval rows: 690.
- Scan-policy metric rows: 120.
- Aggregate policy rows: 4.
- Leakage audit pass: true.
- Detector budget-5 eval loss-safe: true.
- Policy-budget append gain/loss rows: 2 / 0.
- Source-gap append gain/loss rows: 0 / 0.
- Selected next unit: E008-M82 full-val-mini loss-safe candidate-source expansion result interpretation and trajectory/source-expansion decision.

Policy aggregate:

| scope | policy_id | primary hits | proxy SR | proxy SPL |
| --- | --- | ---: | ---: | ---: |
| detector_budget5 | `detector_confidence_budget5_core_v0` | 13/30 | 0.433333 | 0.285258 |
| detector_budget5 | `loss_safe_append_source_probe_budget8_v0` | 13/30 | 0.433333 | 0.285258 |
| policy_budget | `detector_confidence_budget5_core_v0` | 13/30 | 0.433333 | 0.285258 |
| policy_budget | `loss_safe_append_source_probe_budget8_v0` | 15/30 | 0.500000 | 0.299822 |

Claim boundary:

- M81 supports detector budget-5 preservation under a leakage-safe goal-evaluation proxy.
- M81 supports a policy-budget diagnostic gain from append-only source probes.
- M81 does not support source-gap recovery because source-gap append gain is 0.
- M81 does not support deployable budget-5 policy, final real navigation `SR` / `SPL`, final RGB-D/open-vocabulary robustness, or human intent as a main claim.

## E008-M82

Implementation unit: `E008-M82_loss_safe_candidate_source_expansion_result_interpretation_v0`.

Purpose:

- Interpret M81 before launching any new trajectory or render/detector job.
- Decide whether append budget-8 gain is sufficient for trajectory promotion.
- Decide whether unresolved source-gap rows require a non-oracle source/observation expansion contract.

Result:

- Status: `e008_m82_loss_safe_candidate_source_expansion_result_interpretation_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/plan_m82_loss_safe_candidate_source_expansion_result_interpretation.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M82_loss_safe_candidate_source_expansion_result_interpretation_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M82_loss_safe_candidate_source_expansion_result_interpretation_v0/`.
- Append gain/loss rows: 2 / 0.
- Source-gap append gain/loss rows: 0 / 0.
- Detector budget-5 eval loss-safe: true.
- Direct trajectory promotion ready: false.
- Source/observation expansion contract required: true.
- Selected route: `source_observation_expansion_contract_first`.
- Selected next unit: E008-M83 full-val-mini source-gap non-oracle source/observation expansion contract.

Route decision:

| route | decision | reason |
| --- | --- | --- |
| `promote_append_budget8_policy_to_trajectory` | reject now | append gain is outside detector budget-5 and does not recover source-gap rows |
| `source_observation_expansion_contract_first` | select | existing append rows are loss-safe but insufficient for source-gap; M80 already contains non-oracle expansion plans |
| `package_m81_as_diagnostic_table` | defer | useful boundary evidence but not enough for top-tier navigation |
| `external_navigation_search_baselines_now` | defer | necessary later, but internal source-gap blocker should be resolved first |

Claim boundary:

- M82 supports loss-safe append diagnostics only.
- M82 does not support source-gap recovery, deployable budget-5 policy, final RGB-D/open-vocabulary robustness, final real navigation `SR` / `SPL`, or human intent as a main claim.

## E008-M83

Implementation unit: `E008-M83_source_gap_non_oracle_source_observation_expansion_contract_v0`.

Purpose:

- Convert the M82 route decision into a leakage-aware non-oracle source/observation expansion contract.
- Fix which source-gap cases, allowed inputs, blocked inputs, M84 output files, and future long-job policy must be used before any render/detector job.
- Keep post-hoc source-gap labels as diagnostic case selection only, not as a deployable runtime trigger.

Result:

- Status: `e008_m83_source_gap_non_oracle_source_observation_expansion_contract_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/plan_m83_source_gap_non_oracle_source_observation_expansion_contract.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M83_source_gap_non_oracle_source_observation_expansion_contract_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M83_source_gap_non_oracle_source_observation_expansion_contract_v0/`.
- Source-gap contract cases: 2.
- Source/observation route rows: 6.
- Selected materialization route rows: 4.
- Allowed / blocked input rows: 5 / 4.
- M84 materialization contract rows: 6.
- Readiness gate fail/warning rows: 0 / 1.
- Launch long job now: false.
- Selected next unit: E008-M84 full-val-mini source-gap non-oracle source/observation expansion materialization smoke.

Source-gap cases:

| adapter_episode_id | category | selected routes |
| --- | --- | --- |
| `00800-TEEsavR23oF::22` | sofa | `non_oracle_local_shell_multiview_refresh_v1`, `non_oracle_high_path_source_refresh_v1` |
| `00802-wcojb4TFT35::13` | toilet | `non_oracle_local_shell_multiview_refresh_v1`, `non_oracle_high_path_source_refresh_v1` |

Claim boundary:

- M83 supports only a non-oracle source/observation expansion contract.
- M83 does not support source-gap recovery, deployable search policy, final RGB-D/open-vocabulary robustness, final real navigation `SR` / `SPL`, or human intent as a main claim.

## E008-M84

Implementation unit: `E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0`.

Purpose:

- Materialize M83 source-gap cases into launch-ready observation pose, render, detector manifest, and long-job ledger rows.
- Keep M85/M86 as background jobs; do not run them in M84.

Result:

- Status: `e008_m84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m84_source_gap_non_oracle_source_observation_expansion_materialization_smoke.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0/`.
- Source-gap case rows: 2.
- Observation pose plan rows: 24.
- Render plan rows: 192.
- Detector manifest rows: 2.
- Detector object target rows: 2.
- Selected route materializations: 4.
- Readiness gate fail/warning rows: 0 / 0.
- Long-job command rows: 2.
- Launch long job now: false.
- Selected next unit: E008-M85 full-val-mini source-gap non-oracle render frame staging background launch.

Source-gap cases:

| adapter_episode_id | category | target labels |
| --- | --- | --- |
| `00800-TEEsavR23oF::22` | sofa | sofa |
| `00802-wcojb4TFT35::13` | toilet | toilet |

Route materialization:

| adapter_episode_id | route_id | status | observation rows |
| --- | --- | --- | --- |
| `00800-TEEsavR23oF::22` | `existing_append_probe_audit_v0` | not materialized | 0 |
| `00800-TEEsavR23oF::22` | `non_oracle_high_path_source_refresh_v1` | materialized | 3 |
| `00800-TEEsavR23oF::22` | `non_oracle_local_shell_multiview_refresh_v1` | materialized | 9 |
| `00802-wcojb4TFT35::13` | `existing_append_probe_audit_v0` | not materialized | 0 |
| `00802-wcojb4TFT35::13` | `non_oracle_high_path_source_refresh_v1` | materialized | 3 |
| `00802-wcojb4TFT35::13` | `non_oracle_local_shell_multiview_refresh_v1` | materialized | 9 |

Long-job commands:

| job_id | status | tmux session | output path |
| --- | --- | --- | --- |
| E008-M85 | contract recorded, not launched | `e008_m85_source_gap_render` | `local_dataset/HM3D_navigation_bridge/E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0/` |
| E008-M86 | contract recorded, not launched | `e008_m86_source_gap_detector` | `experiments/E008_real_navigation_benchmark/artifacts/E008-M86_source_gap_detector_candidate_source_v0/` |

Claim boundary:

- M84 supports source-gap source/observation expansion input materialization only.
- M84 does not render frames, run detector inference, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.

## E008-M85

Implementation unit: `E008-M85_source_gap_render_frame_staging_launch_v0` plus M85 verification rows written under the M84 artifact.

Purpose:

- Launch the M84-recorded source-gap render frame staging job in `tmux`.
- Verify that the source-gap RGB-D/pose frames are ready before any detector candidate-source job.

Result:

- Launch status: `e008_m85_source_gap_render_frame_staging_launched`.
- Verification status: `e008_m85_source_gap_render_frame_staging_verified`.
- Launch command: `python experiments/E008_real_navigation_benchmark/tools/launch_m85_source_gap_render_frame_staging.py`.
- Verification command: `python experiments/E008_real_navigation_benchmark/tools/verify_m85_source_gap_render_frame_staging.py --require-ready`.
- Launch artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M85_source_gap_render_frame_staging_launch_v0/`.
- Verification artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0/`.
- Ready frames: 192 / 192.
- Ready scans: 2 / 2.
- Snap-ready rows: 192 / 192.
- Large snap warning rows: 0.
- Max snap distance: 1.797502m.
- Detector input files ready: true.
- Selected next unit: E008-M86 full-val-mini source-gap detector candidate-source background launch.

Claim boundary:

- M85 verifies source-gap rendered RGB-D frame staging only.
- M85 does not support detector candidate quality, source-gap recovery, real navigation `SR` / `SPL`, final RGB-D/open-vocabulary robustness, or human intent as a main claim.

## E008-M86

Implementation unit: `E008-M86_source_gap_detector_candidate_source_launch_v0` plus `E008-M86_source_gap_detector_candidate_source_v0` verification.

Purpose:

- Launch detector candidate-source generation on the verified M85 source-gap rendered frames.
- Verify the completed source-gap detector output before any navmesh/source-readiness or source-gap recovery claim.

Result:

- Launch status: `e008_m86_source_gap_detector_candidate_source_launched`.
- Verification status: `e008_m86_source_gap_detector_candidate_source_verified`.
- Launch command: `python experiments/E008_real_navigation_benchmark/tools/launch_m86_source_gap_detector_candidate_source.py`.
- Verification command: `python experiments/E008_real_navigation_benchmark/tools/verify_m86_source_gap_detector_candidate_source.py --require-ready`.
- tmux session: `e008_m86_source_gap_detector`.
- Log path: `logs/20260601_222320_e008_m86_source_gap_detector.log`.
- Launch artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M86_source_gap_detector_candidate_source_launch_v0/`.
- Output root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M86_source_gap_detector_candidate_source_v0/`.
- Manifest rows: 2.
- Object target rows: 2.
- Preflight blockers: 0.
- Frame rows: 192.
- Frames with written predictions: 48.
- Raw / written predictions: 1,964 / 48.
- Final detector candidate rows: 48.
- Pre-cap candidate rows: 1,896.
- Coordinate candidate rows: 48.
- Validator errors / warnings: 0 / 0.
- Matching target rows: 0.
- Selected next unit: E008-M87 source-gap detector candidate navmesh/source-readiness validation.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M86_source_gap_detector_candidate_source_v0/e008_m86_verification_coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M86_source_gap_detector_candidate_source_v0/e008_m86_candidate_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M86_source_gap_detector_candidate_source_v0/e008_m86_route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M86_source_gap_detector_candidate_source_v0/e008_m86_verification_report.md`

Claim boundary:

- M86 supports source-gap detector candidate-source availability and schema/coordinate readiness.
- M86 does not support detector target-recall quality because matching target rows are 0 in this source-gap verifier.
- M86 does not support source-gap recovery, real navigation `SR` / `SPL`, final RGB-D/open-vocabulary robustness, or human intent as a main claim.
