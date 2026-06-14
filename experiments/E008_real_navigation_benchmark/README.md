# E008 Real Navigation Benchmark

Updated: 2026-06-14

## Status

Current concise status: E008-M01 through E008-M198 are complete with constraints. M130-M165 exposed and decomposed the proxy-to-trajectory, confidence-preserving, budget-aware, and local-rerank failure pattern. M166-M176 freeze that boundary, reject within-pool source-coverage reranking as a positive navigation-improvement claim, and move source coverage to `source_coverage_triggered_candidate_source_expansion_v1`. M177-M179 materialize, render, and run detector inference for a fixed-budget source-pool branch, yielding 192 coordinate candidate rows from 256 rendered frames. M180 validates 180 / 192 candidates as path-ready over 8 / 8 source-ready scans. M181-M182 materialize 732 visit-order rows and observe leakage-safe proxy recovery on 7 / 8 episodes. M183-M184 execute a Docker `Habitat` trajectory smoke with 32 scan-policy rows, 28 successes, aggregate `SR` 0.875, and mean `SPL` 0.2411. M185-M190 reject direct path-cost and transition-cost reranking as positive claims, keep source-pool candidate-source expansion, and set `detector_confidence_reachable_subset_v0` as the safe execution default before scale-up. M191-M193 fix and preflight the 30-triggered-episode source-pool scale denominator: 240 source poses, 960 render rows, and 30 detector manifests. M194 verifies scale render/detector execution with 960 / 960 ready frames, 552 detector prediction rows, 552 coordinate candidate rows, and 8,867 pre-cap candidate rows. M195 validates 523 / 552 candidates as path-ready with 23 / 30 source-ready scans. M196 materializes 2,121 visit-order rows while retaining 7 source-gap scan rows. M197 evaluates leakage-safe full-denominator proxy metrics: source-pool protected detector confidence reaches 17 / 30 proxy recovery, proxy `SR` 0.5667, proxy `SPL` 0.3235. M198 compares against M70 no-source detector baseline 24 / 30, proxy `SR` 0.8000, proxy `SPL` 0.3506, rejects immediate Docker trajectory promotion, and selects M199 failure decomposition / candidate-generation repair decision.

E008 starts after E007-M07 packaged the occupancy-grid path-cost proxy table and selected `E008-M01 real navigation benchmark/source preflight and episode contract`. E008 is the first stage that prepares real navigation `SR` / `SPL` evidence. E008-M01 through E008-M198 are complete as source/adapter/contract/oracle-metric/candidate-source staging, rendered RGB-D detector route, leakage-safe goal evaluation, trajectory execution, H001 fallback execution, dynamic-stale overlay execution, source-gap repair chains, `ConceptGraphs` HM3D source-gap route, target-free source-coverage expansion, trajectory-aware repair, confidence-preserving full-val-mini execution, policy-family failure decomposition, method-pivot boundary, source-coverage memory-interface method contract, source-coverage trigger/candidate-source expansion, fixed-budget source-pool rendering/detection, source-pool navmesh validation, proxy evaluation, Docker trajectory execution, protected-baseline interpretation, source-pool failure decomposition, repaired row materialization, repaired proxy evaluation, proxy failure decomposition, method-boundary/scale decision, scale-up contract, scale denominator materialization, scale snap/launcher contract, scale detector execution, source-ready/source-gap split, full-denominator proxy evaluation, and no-source baseline comparison. M198 keeps final navigation, deployable policy, real RGB-D/open-vocabulary robustness, and human-intent main claims blocked because source-pool scale proxy `SR` is below the no-source detector baseline.

Next unit: E008-M199 source-pool scale failure decomposition and candidate-generation repair decision.

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
| conclusion | E008-M01 selects `HM3D ObjectNav` + `Habitat` as the first real navigation source. E008-M02-M42 build and execute the detector/H001/dynamic-stale trajectory smoke chain with final navigation claims blocked. E008-M43 fixes source-diverse policy redesign because detector source-gap rows are recoverable in the full current candidate pool but not under confidence top-5. E008-M44-M82 iterate through source-diverse, routine-fetch, high-path tail-slot, full-val-mini, trajectory, source-gap/SPL repair, and loss-safe source-expansion gates while keeping final navigation claims blocked. E008-M83 fixes the non-oracle source/observation expansion contract. E008-M84 materializes source-gap render/detector inputs. E008-M85 verifies source-gap rendered frame staging. E008-M86 verifies source-gap detector candidate-source generation. E008-M87 validates source-gap candidates against navmesh/source-readiness and passes 2/2 source-gap cases. E008-M88 materializes source-gap visit-order/path rows. E008-M89 shows leakage-safe goal-evaluation proxy recovery is still 0/2. E008-M90 rejects trajectory promotion. E008-M91 separates target-coverage failure modes. E008-M92 fixes the two-branch coverage/cap repair contract. E008-M93 materializes coverage-expansion rows and cap-threshold probe rows. E008-M94 rejects the cap branch as immediate recovery and selects coverage launcher adaptation. E008-M95 adapts M93 coverage rows into M96/M97 launcher inputs and command ledger. E008-M96 verifies coverage-expansion rendered frame staging. E008-M97 verifies coverage-expansion detector candidate-source generation. E008-M98 validates coverage-expansion candidates against navmesh/source-readiness. E008-M99 materializes coverage-expansion candidate visit-order/path rows. E008-M100 runs leakage-safe goal evaluation and shows coverage expansion still does not recover the remaining source-gap case. E008-M101 rejects trajectory promotion. E008-M102 closes the current two-branch detector source-gap repair route. E008-M103 selects `ConceptGraphs` HM3D source-gap adapter/preflight as the next alternative proposal-source route. E008-M104 confirms selected source-gap cases are adapter materialization-ready for `ConceptGraphs`. E008-M105 materializes the staged `ConceptGraphs` input layout and passes container-readability smoke. E008-M106 fixes the bounded runtime launch/verification contract and M108 verifier. E008-M107 completes the bounded runtime, E008-M108 verifies runtime outputs ready for 2/2 scans, E008-M109 confirms adapter-ready post-PCD object schemas with 29/42 objects, E008-M110 materializes 71 leakage-safe candidate rows with CLIP text scores, E008-M111 validates 48/71 candidates as path-ready over 2/2 source-ready queries, E008-M112 materializes 215 visit-order/path rows with leakage audit pass, E008-M113 evaluates those rows against `ObjectNav` targets with primary proxy success 0/2 for all policies, E008-M114 rejects trajectory promotion while splitting the failures into one severe source coverage gap and one stop-region/viewpoint alignment gap, E008-M115 fixes M116 as the next audit materialization contract, E008-M116 materializes one source-coverage audit row plus one stop-region alignment audit row, E008-M117 selects M118 stop-region transform smoke while deferring the source-coverage gap to external/visibility preflight, E008-M118 materializes 50 stop-region candidates with 50/50 path-ready rows and budget-5 proxy recovery for the selected `toilet` case, E008-M119 verifies that the remaining `sofa` case is a source-coverage failure because current source poses are far from the target view region, E008-M120 fixes a target-free source-coverage expansion contract with two selected M121 materialization routes, E008-M121 materializes 40 target-free source poses, 320 render-plan rows, and 2 detector manifests with target/viewpoint leakage false, E008-M122 fixes launcher inputs and long-job command ledgers for M123 render and M124 detector execution, E008-M123 verifies a 295-frame depth-filtered detector-usable render subset, E008-M124 verifies 24 detector prediction rows over that subset, E008-M125 validates 15/24 candidates as path-smoke usable, E008-M126 materializes 69 visit-order/path rows with leakage audit pass, E008-M127 observes leakage-safe `any_viewpoint_xz_1p0` proxy recovery 1/1 for all four policies, E008-M128 selects a bounded trajectory contract/preflight gate, E008-M129 materializes 69 runner-compatible trajectory candidate rows, 4 execution plans, 1 eval-goal/oracle row pair, leakage audit pass, and Docker/data/runner preflight pass, and E008-M130 executes 4 policy trajectories with `SR` 1.0. M130 is diagnostic-negative for path-cost improvement because the path-cost policy `SPL` 0.092750 is below detector-confidence `SPL` 0.701267. Real navigation claims remain unsupported until result interpretation, heldout transfer, and baseline comparison pass. |

## Claim Boundary

- E008-M01 through E008-M198 do not claim final real navigation `SR` / `SPL`.
- E008-M01 through E008-M198 do not claim final real RGB-D/open-vocabulary robustness.
- E008-M01 through E008-M198 do not make human intent a main contribution.
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
- E008-M87 supports source-gap detector candidate navmesh/source-readiness validation only; it does not run visit-order/path policy rows, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.
- E008-M88 supports source-gap detector candidate visit-order/path smoke only; it does not evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.
- E008-M89 supports source-gap leakage-safe goal-evaluation proxy only; it does not support source-gap recovery because primary proxy success is 0/2 for all detector policies, and it does not execute trajectories or support final real navigation `SR` / `SPL`.
- E008-M90 supports source-gap result interpretation and route decision only; it rejects trajectory promotion because M89 source-gap proxy recovery is false, and it does not execute trajectories or support final real navigation `SR` / `SPL`.
- E008-M91 supports source-gap target-coverage failure diagnosis only; it does not recover source-gap cases, execute trajectories, or support final real navigation `SR` / `SPL`.
- E008-M92 supports source-gap two-branch repair contract only; it does not materialize repaired rows, run detector/render jobs, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.
- E008-M93 supports two-branch repair row materialization only; it writes coverage-expansion observation/render/detector manifest rows and cap-threshold candidate probe rows, but it does not run render/detector jobs, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.
- E008-M94 supports route selection only; it uses eval-only distances after M93 fixed probe order, keeps the cap branch diagnostic, and does not run render, detector, or trajectory jobs.
- E008-M95 supports launcher adaptation only; it writes render/detector launcher input files and records M96/M97 long-job commands, but it does not run render, detector inference, source-gap recovery evaluation, or trajectory execution.
- E008-M96 supports coverage-expansion rendered frame staging verification only; it does not run detector inference, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.
- E008-M97 supports coverage-expansion detector candidate-source availability and schema/coordinate readiness only; it does not validate navmesh reachability, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.
- E008-M98 supports coverage-expansion detector candidate navmesh/source-readiness validation only; it does not run visit-order/path rows, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.
- E008-M99 supports coverage-expansion detector candidate visit-order/path rows only; it does not evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.
- E008-M100 supports coverage-expansion leakage-safe detector candidate goal-evaluation only; it does not support source-gap recovery because primary proxy success is 0/1 for all policies, and it does not execute trajectories or support final real navigation `SR` / `SPL`.
- E008-M101 supports coverage-expansion result interpretation and trajectory decision only; it rejects trajectory promotion and additional long jobs until failure audit changes the candidate-source principle.
- E008-M102 supports a negative source-gap repair closure only; it closes the current detector route and selects alternative proposal-source feasibility before more long jobs.
- E008-M103 supports alternative proposal-source route selection only; it selects `conceptgraphs_hm3d_map_candidate_adapter` for M104 and does not support source-gap recovery or navigation claims.
- E008-M104 supports `ConceptGraphs` HM3D source-gap adapter/materialization feasibility only; it does not run `ConceptGraphs`, export candidates, evaluate source-gap recovery, execute trajectories, or support final navigation claims.
- E008-M105 supports staged `ConceptGraphs` input layout readiness only; it does not run `ConceptGraphs`, export candidates, evaluate source-gap recovery, execute trajectories, or support final navigation claims.
- E008-M106 supports bounded `ConceptGraphs` runtime launch/verification contract readiness only; it does not launch the runtime because GPU memory is below threshold, does not export candidates, does not evaluate source-gap recovery, and does not support final navigation claims.
- E008-M108 supports `ConceptGraphs` runtime output availability only; it does not export candidates, validate coordinates, evaluate source-gap recovery, execute trajectories, or support final navigation claims.
- E008-M109 supports the `ConceptGraphs` HM3D candidate export adapter contract only; it does not export candidate rows, validate navmesh reachability, evaluate source-gap recovery, execute trajectories, or support final navigation claims.
- E008-M110 supports `ConceptGraphs` HM3D candidate row materialization only; it does not validate navmesh reachability, evaluate source-gap recovery, execute trajectories, or support final navigation claims.
- E008-M111 supports `ConceptGraphs` HM3D candidate navmesh/source-readiness validation only; it does not evaluate source-gap recovery, execute trajectories, support final navigation claims, or claim `ConceptGraphs` class-name recognition.
- E008-M112 supports `ConceptGraphs` HM3D candidate visit-order/path materialization only; it does not evaluate source-gap recovery, execute trajectories, support final navigation claims, or claim `ConceptGraphs` class-name recognition.
- E008-M113 supports `ConceptGraphs` HM3D leakage-safe candidate goal-evaluation proxy only; it does not support source-gap recovery because primary proxy success is 0/2 for all policies, and it does not execute trajectories or support final navigation claims.
- E008-M115 supports case-level failure audit and repair-route selection only; it does not create new candidates, recover source-gap rows, execute trajectories, or support final navigation claims.
- E008-M116 supports stop-region/source-coverage audit materialization only; it does not create transformed candidates, recover source-gap rows, execute trajectories, or support final navigation claims.
- E008-M117 supports route decision only; it selects M118 stop-region transform smoke and defers source-coverage repair to external/visibility preflight, but it does not materialize transformed candidates, recover source-gap rows, execute trajectories, or support final navigation claims.
- E008-M118 supports stop-region transform materialization and leakage-safe posthoc proxy evaluation for the selected `toilet` case only; it does not solve the `sofa` source-coverage gap, provide a deployable trigger, execute trajectories, or support final navigation claims.
- E008-M119 supports source-coverage external/visibility preflight only; it rejects same-source rerank/rerun for the `sofa` case and selects target-free source-coverage expansion, but it does not create new source frames, run external baselines, execute trajectories, or support final navigation claims.
- E008-M120 supports target-free source-coverage expansion contract only; it selects M121 materialization routes and input guards, but it does not materialize source poses, render frames, run detectors/mappers, recover source-gap rows, execute trajectories, or support final navigation claims.
- E008-M121 supports target-free source materialization only; it writes source pose, snap-validation, render-plan, and detector-manifest rows with target/viewpoint leakage false, but it does not render frames, run detectors/mappers, recover source-gap rows, execute trajectories, or support final navigation claims.
- E008-M122 supports target-free render/detector launcher contract only; it writes launcher inputs, expected-file checks, long-job command rows, verification commands, and claim-boundary rows, but it does not launch rendering, run detectors/mappers, recover source-gap rows, execute trajectories, or support final navigation claims.
- E008-M123 verifies target-free detector-usable rendered frame staging after filtering 25 zero-depth frames from the detector manifest; it does not claim all 320 rendered frames are depth-valid.
- E008-M124 verifies target-free detector candidate-source generation only; it does not validate navmesh reachability, evaluate source-gap recovery, execute trajectories, or support final navigation claims.
- E008-M125 validates target-free detector candidates against coordinate/navmesh/source-readiness only; it does not materialize visit-order/path rows, evaluate goal recovery, execute trajectories, or support final navigation claims.
- E008-M126 materializes target-free detector candidate visit-order/path rows only; it does not evaluate goal recovery, execute trajectories, or support final navigation claims.
- E008-M127 evaluates fixed M126 rows against `ObjectNav` goals/viewpoints only as evaluation labels; it does not execute trajectories or support final navigation claims.
- E008-M128 supports moving to a bounded target-free trajectory-contract gate only; it does not execute `Habitat` trajectories or support final navigation claims.
- E008-M129 supports a runner-compatible target-free detector-policy trajectory execution contract and Docker/data/runner preflight only; it does not execute `Habitat` trajectories or support final navigation claims.
- E008-M130 executes one target-free detector-policy trajectory smoke, but it does not support final navigation claims because it is one case and the path-cost method loses `SPL` to detector-confidence baselines.
- E008-M131 supports result interpretation and scale decision only; it rejects current path-cost scale-up because source-to-candidate proxy path cost flips against executed candidate-to-candidate trajectory cost.
- E008-M132 supports trajectory-aware repair contract and allowed/blocked input design only; it does not materialize repaired rows, execute trajectories, or support final navigation claims.
- E008-M133 supports trajectory-aware repair row and cost-matrix materialization only; it does not execute repaired trajectories or support final navigation claims.
- E008-M134 supports trajectory-aware repair execution contract and Docker/data/runner preflight only; it does not execute trajectories or support final navigation claims.
- E008-M135 executes one target-free trajectory-aware repair trajectory smoke, but it does not support final navigation claims because it is one case and selected repair loses `SPL` to detector-confidence / confidence-only baselines.
- E008-M136 supports result interpretation and scale decision only; it rejects current repair scale-up and selects confidence-preserving repair before any broader navigation run.
- E008-M137 supports a confidence-preserving repair contract only; it does not materialize new visit-order rows or execute trajectories.
- E008-M138 supports confidence-preserving row materialization only; it does not execute trajectories or support final navigation claims.
- E008-M139 supports the confidence-preserving trajectory execution contract and Docker/data preflight only; it does not execute trajectories or support final navigation claims.
- E008-M140 supports a one-case confidence-preserving trajectory smoke only; it does not support final navigation claims without M141 interpretation, scale, heldout transfer, and external navigation/search baselines.
- E008-M141 supports result interpretation and controlled scale-up decision only; it authorizes M142 scale-up contract design but does not support final navigation claims.
- E008-M142 supports controlled scale-up contract design only; it does not materialize full-val-mini trajectory cost rows, execute trajectories, or support final navigation claims.
- E008-M143 supports full-val-mini trajectory-cost materialization only; it materializes 33,354 cost-matrix rows, 5,400 candidate-policy rows, and 180 execution plans, but it does not execute trajectories or support final navigation claims.
- E008-M144 supports full-val-mini trajectory execution contract / Docker preflight only; it fixes M145 inputs and readiness, but it does not execute trajectories or support final navigation claims.
- E008-M145 supports a full-val-mini execution result only; it does not support final navigation claims because M146/M147 interpretation, heldout transfer, and external navigation/search baselines are still required.
- E008-M146 supports full-val-mini result interpretation and route decision only; it rejects positive navigation-improvement for the selected policy and selects M147 failure decomposition.
- E008-M147 supports policy-family failure decomposition and redesign contract only; it selects M148 budget-guarded confidence/path redesign and still blocks positive navigation-improvement claims.
- E008-M148 supports pre-execution budget-guarded confidence/path redesign contract only; it selects M149 row materialization and still blocks positive navigation-improvement claims.
- E008-M149 supports budget-guarded row materialization only; it creates runner-compatible candidate/plan rows and audits leakage/budget/order guards, but it does not execute `Habitat` trajectories or support positive navigation-improvement claims.
- E008-M150 supports budget-guarded trajectory execution contract / Docker preflight only; it does not execute `Habitat` trajectories or support positive navigation-improvement claims.
- E008-M151 supports raw full-val-mini budget-guarded trajectory execution only; M152 later rejects positive navigation-improvement for the selected policy.
- E008-M152 supports result interpretation and scale decision only; it rejects selected-policy positive navigation improvement because protected `SPL` and visit-efficiency gates fail, and selects M153 Pareto failure decomposition.
- E008-M153 supports Pareto failure decomposition only; it rejects selected-policy positive navigation improvement because the selected policy is dominated in primary `SR`/`SPL`/candidate-visit space, treats no-visit-guard as a tradeoff witness rather than a selected method, and selects M154 budget-aware utility objective contract.
- E008-M154 supports a pre-execution budget-aware utility contract only; it does not materialize policy rows, execute trajectories, or support navigation performance claims.
- E008-M155 supports budget-aware utility policy materialization and leakage audit only; the selected policy changes 8 episode orders and promotes 17 rows, but it does not execute trajectories or support navigation performance claims.
- E008-M156 supports budget-aware utility trajectory execution contract / Docker preflight only; it writes runner-compatible rows and M157 command ledger but does not execute trajectories or support navigation performance claims.
- E008-M157 supports budget-aware utility trajectory execution only; it still requires M158 protected-baseline interpretation before any positive navigation-improvement claim.
- E008-M158 supports protected-baseline interpretation only; it rejects selected utility positive navigation improvement and does not support final navigation claims.
- E008-M159 supports component failure decomposition only; it keeps confidence floor as supported, rejects current scalar path gain, marks source-gap/visit-penalty terms inert on this denominator, and selects a constrained repair contract before any new execution or claim.
- E008-M160 supports a confidence-first constrained repair contract only; it fixes method rules, input guards, and metric targets, but it does not materialize repaired rows, execute trajectories, or support positive navigation-improvement claims.
- E008-M161 supports confidence-first constrained repair row materialization only; it changes selected visit orders under leakage/order guards, but it does not execute trajectories or support positive navigation-improvement claims.
- E008-M162 supports confidence-first constrained repair trajectory execution contract / Docker preflight only; it writes runner-compatible rows and M163 command ledger, but it does not execute `Habitat` trajectories or support positive navigation-improvement claims.
- E008-M163 supports raw confidence-first constrained repair trajectory execution only; protected-baseline interpretation is deferred to M164, and raw selected-policy `SPL` does not support positive navigation-improvement.
- E008-M164 supports protected-baseline interpretation only; it rejects selected confidence-first repair as a positive navigation-improvement claim and selects M165 failure decomposition before any new scale-up.
- E008-M165 supports failure decomposition only; it blocks local rerank scale-up because selected local swaps change order but not successful target recovery, and selects M166 boundary/method-pivot contract.
- E008-M166 supports failure-boundary packaging and method-pivot selection only; it selects `source_coverage_memory_interface_policy_v1` but does not materialize rows or execute trajectories.
- E008-M167 supports method/input/baseline/metric contract only; it does not materialize rows or execute trajectories.
- E008-M168 supports source-coverage memory-interface row materialization only; it does not execute trajectories or support positive navigation claims.
- E008-M169 supports Docker trajectory execution contract / preflight only; it does not execute trajectories or support positive navigation claims.
- E008-M170 supports raw source-coverage memory-interface trajectory execution only; protected-baseline interpretation is deferred to M171.
- E008-M171 supports protected-baseline interpretation only; it rejects selected-policy positive navigation improvement because selected `SPL` is 0.225556 vs detector-confidence 0.231845 and selected mean visits are 11.666667 vs detector-confidence 11.200000.
- E008-M172 supports source-coverage tradeoff decomposition only; it does not promote source-coverage-only as the main method because it is task-agnostic, not preselected, and requires a precommitted SPL/visit/path utility objective.
- E008-M173 supports source-coverage utility/Pareto contract design only; it does not materialize new rows, execute trajectories, or support performance claims.
- E008-M174 supports source-coverage utility/Pareto row materialization and leakage/order/guard audit only; it blocks the then-planned Docker execution path because the selected policy activity gate fails with 0 / 30 changed episode orders.
- E008-M174b supports failure decomposition and route decision only; it rejects Docker execution/posthoc utility tuning, closes within-pool source-coverage reranking as negative, and selects candidate-source expansion contract next.
- E008-M175 supports source-coverage trigger/candidate-source expansion contract only; it does not materialize trigger rows, launch render/detector jobs, execute trajectories, or support navigation performance claims.
- E008-M176 supports source-trigger row materialization only; it does not materialize source poses, launch render/detector jobs, execute trajectories, or support navigation performance claims. Because trigger requests fire on 30 / 30 rows, M177 must add a fixed budget/priority guard before long jobs.
- E008-M177 supports fixed-budget source-pool pose/render-plan materialization only; it does not run render, detector inference, or trajectories.
- E008-M178 supports navmesh/snap validation and render/detector launcher contract only; it does not run detector inference or trajectories.
- E008-M179 supports bounded render/detector execution only; it does not validate candidate reachability, evaluate goals, or execute trajectories.
- E008-M180 supports candidate navmesh/source-readiness validation only; it does not evaluate goal recovery or execute trajectories.
- E008-M181 supports visit-order/path materialization only; it does not evaluate goal recovery or execute trajectories.
- E008-M182 supports leakage-safe proxy goal evaluation only; it does not execute trajectories or support final `SR` / `SPL`.
- E008-M183 supports Docker trajectory contract/preflight only; it does not execute trajectories.
- E008-M184 supports a bounded Docker `Habitat` trajectory smoke only; it is not a final navigation benchmark.
- E008-M185 supports protected-baseline interpretation only; it rejects direct source-pool scale-up because the selected path-cost method loses `SPL` to `detector_confidence_reachable_subset_v0`.
- E008-M186 supports failure decomposition and repair-contract design only; it does not materialize repaired policy rows or support a positive navigation claim.
- E008-M187 supports confidence-protected transition-cost row materialization only; it does not evaluate goal recovery, execute trajectories, or support a positive navigation claim.
- E008-M188 supports leakage-safe proxy evaluation only; it rejects immediate Docker trajectory promotion because selected proxy `SPL` remains below protected detector confidence.
- E008-M189 supports proxy failure decomposition only; it rejects `confidence_protected_transition_cost_policy_v1` as a positive navigation-improvement policy and does not execute trajectories.
- E008-M190 supports method-boundary and scale-decision only; it keeps source-pool candidate-source expansion, rejects transition repair as a positive claim, sets `detector_confidence_reachable_subset_v0` as the current safe execution default, and blocks immediate Docker launch until M191 scale-up contract.
- E008-M191 supports scale-up contract readiness only; it fixes the denominator, source-pool budget, protected-confidence default, required no-source-pool ablation, leakage audit, and command ledger, but does not materialize source poses, render frames, run detectors, evaluate goals, or execute trajectories.
- E008-M192 supports scale denominator/source-pose/render-plan materialization only; it does not validate navmesh/snap, render frames, run detectors, evaluate goals, or execute trajectories.
- E008-M193 supports scale navmesh/snap validation and render/detector launcher contract only; it does not launch render/detector jobs, evaluate targets, or execute trajectories.
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

## E008-M87

Implementation unit: `E008-M87_source_gap_detector_candidate_navmesh_validation_v0`.

Purpose:

- Validate M86 source-gap detector candidates against `HM3D` / `Habitat` navmeshes.
- Decide whether the two unresolved source-gap cases have path-ready candidates for later visit-order/path smoke.

Result:

- Status: `e008_m87_source_gap_detector_candidate_navmesh_validation_ready`.
- Gate verdict: `pass`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m87_source_gap_detector_candidate_navmesh_validation.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M87_source_gap_detector_candidate_navmesh_validation_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M87_source_gap_detector_candidate_navmesh_validation_v0/`.
- Source-gap case rows: 2.
- Source-ready source-gap cases: 2 / 2.
- Candidate rows: 48.
- Coordinate-valid rows: 48 / 48.
- Snapped navigable rows: 48 / 48.
- Source-to-snapped path rows: 30 / 48.
- Navmesh validation status counts: `candidate_path_ready` 30, `blocked_snapped_point_unreachable_from_episode_start` 18.
- Snap-warning candidate rows: 0.
- Selected next unit: E008-M88 source-gap detector candidate visit-order/path smoke.

Claim boundary:

- M87 validates candidate source-readiness only.
- M87 does not support source-gap recovery because eval-only goal/viewpoint matching is not run here.
- M87 does not support real navigation `SR` / `SPL` because no trajectory is executed.

## E008-M88

Implementation unit: `E008-M88_source_gap_detector_candidate_visit_order_path_smoke_v0`.

Purpose:

- Materialize visit-order/path rows over M87 source-gap detector candidates.
- Keep eval-only `ObjectNav` goal/viewpoint fields out of policy inputs before source-gap recovery scoring.

Result:

- Status: `e008_m88_source_gap_detector_candidate_visit_order_path_smoke_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m88_source_gap_detector_candidate_visit_order_path_smoke.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M88_source_gap_detector_candidate_visit_order_path_smoke_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M88_source_gap_detector_candidate_visit_order_path_smoke_v0/`.
- Source-gap case rows: 2.
- Query-compatible candidate rows: 48.
- Path-ready candidate rows: 30 / 48.
- Failure rows: 18 (`blocked_snapped_point_unreachable_from_episode_start`).
- Visit-order rows: 138.
- Source-gap case policy metric rows: 8.
- Eval-goal/viewpoint policy leakage: false.
- `detector_confidence_all_candidates_v0` mean first-ready rank/cost: 2.000000 / 15.868845m.
- `path_cost_ascending_reachable_subset_v0` mean first-ready rank/cost: 1.000000 / 0.121411m.
- Selected next unit: E008-M89 source-gap leakage-safe detector candidate goal-evaluation smoke.

Claim boundary:

- M88 supports source-gap visit-order/path materialization only.
- M88 does not support source-gap recovery because goal/viewpoint matching is not run here.
- M88 does not support real navigation `SR` / `SPL` because no trajectory is executed.

## E008-M89

Implementation unit: `E008-M89_source_gap_detector_candidate_goal_evaluation_smoke_v0`.

Purpose:

- Evaluate fixed M88 source-gap visit-order rows against `ObjectNav` goals/viewpoints as eval-only labels.
- Decide whether source-gap proxy recovery exists before any trajectory promotion.

Result:

- Status: `e008_m89_source_gap_detector_candidate_goal_evaluation_smoke_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m89_source_gap_detector_candidate_goal_evaluation_smoke.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M89_source_gap_detector_candidate_goal_evaluation_smoke_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M89_source_gap_detector_candidate_goal_evaluation_smoke_v0/`.
- Source-gap case rows: 2.
- Candidate-goal eval rows: 138.
- Source-gap case goal metric rows: 8.
- Leakage audit pass: true.
- Eval-goal/viewpoint policy leakage: false.
- Primary proxy success: 0 / 2 for all detector policies.
- Mean best any-viewpoint XZ distance: 3.968230m.
- Source-gap proxy recovery observed: false.
- Selected next unit: E008-M90 source-gap detector-goal result interpretation and trajectory-execution decision.

Claim boundary:

- M89 supports only leakage-safe source-gap goal-evaluation proxy diagnostics.
- M89 does not support source-gap recovery because all detector policies have 0/2 primary proxy success.
- M89 does not support real navigation `SR` / `SPL` because no trajectory is executed.

## E008-M90

Implementation unit: `E008-M90_source_gap_detector_goal_result_interpretation_trajectory_decision_v0`.

Purpose:

- Interpret M87/M88/M89 source-gap detector candidate results as a route decision.
- Decide whether negative source-gap proxy recovery can be promoted to trajectory execution or should trigger candidate-source failure diagnosis.

Result:

- Status: `e008_m90_source_gap_detector_goal_result_interpretation_trajectory_decision_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/plan_m90_source_gap_detector_goal_result_interpretation_trajectory_decision.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M90_source_gap_detector_goal_result_interpretation_trajectory_decision_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M90_source_gap_detector_goal_result_interpretation_trajectory_decision_v0/`.
- Source-gap case rows: 2.
- M88 path-ready detector candidates: 30 / 48.
- M89 candidate-goal eval rows: 138.
- M89 primary success count max: 0.
- Source-gap proxy recovery observed: false.
- Direct trajectory promotion ready: false.
- Failure classes: 1 severe candidate-source coverage gap, 1 moderate candidate localization gap.
- Selected next unit: E008-M91 source-gap target-coverage and candidate-source failure diagnosis.

Claim boundary:

- M90 supports a negative gate: navmesh/path-ready source-gap candidates can still fail target-near goal evaluation.
- M90 does not support source-gap recovery, deployable search policy, final real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.

## E008-M91

Implementation unit: `E008-M91_source_gap_target_coverage_candidate_source_failure_diagnosis_v0`.

Purpose:

- Diagnose whether M90 source-gap failures come from target visibility, prompt/category mapping, coordinate projection, observation coverage, cap/ranking, or trajectory execution.
- Decide whether a single repair route is sufficient before any new long-running detector or trajectory job.

Result:

- Status: `e008_m91_source_gap_target_coverage_candidate_source_failure_diagnosis_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/plan_m91_source_gap_target_coverage_candidate_source_failure_diagnosis.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M91_source_gap_target_coverage_candidate_source_failure_diagnosis_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M91_source_gap_target_coverage_candidate_source_failure_diagnosis_v0/`.
- Render-ready frames: 192 / 192.
- Pre-cap candidates: 1,896.
- Final candidates: 48.
- Cases with pre-cap primary target-near hit: 0 / 2.
- Cases with pre-cap relaxed target-near hit: 1 / 2.
- Cases with final primary hit: 0 / 2.
- `hm3dnav_00800_TEEsavR23oF_ep22` / `sofa`: observation-or-detector target coverage gap. Nearest pre-cap any-viewpoint XZ distance is 3.850614m.
- `hm3dnav_00802_wcojb4TFT35_ep13` / `toilet`: localization-threshold / low-confidence cap-suppression gap. Nearest pre-cap any-viewpoint XZ distance is 1.082507m, but confidence rank is 941 and final primary hit remains false.
- Selected next unit: E008-M92 source-gap two-branch coverage/cap repair contract.

Claim boundary:

- M91 supports only post-hoc failure taxonomy using `ObjectNav` eval-only goal/viewpoint labels.
- M91 does not support source-gap recovery, deployable search policy, final real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.

## E008-M92

Implementation unit: `E008-M92_source_gap_two_branch_coverage_cap_repair_contract_v0`.

Purpose:

- Convert the M91 source-gap failure taxonomy into two leakage-safe repair branches.
- Fix branch-specific allowed/blocked inputs, M93 output contracts, and long-job boundaries before materializing rows.

Result:

- Status: `e008_m92_source_gap_two_branch_coverage_cap_repair_contract_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/plan_m92_source_gap_two_branch_coverage_cap_repair_contract.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M92_source_gap_two_branch_coverage_cap_repair_contract_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M92_source_gap_two_branch_coverage_cap_repair_contract_v0/`.
- Repair branch rows: 2.
- Case repair assignments: 2.
- Coverage-expansion branch cases: 1.
- Cap/threshold-rescue branch cases: 1.
- Allowed / blocked input rows: 7 / 8.
- M93 materialization contract rows: 6.
- M93 materialization ready: true.
- Long job launched: false.
- Direct trajectory promotion ready: false.
- Selected next unit: E008-M93 source-gap two-branch repair row materialization smoke.

Branch assignment:

| scan_id | category | M91 failure | M92 branch |
| --- | --- | --- | --- |
| `hm3dnav_00800_TEEsavR23oF_ep22` | `sofa` | `observation_or_detector_target_coverage_gap` | `coverage_expansion_branch` |
| `hm3dnav_00802_wcojb4TFT35_ep13` | `toilet` | `localization_threshold_gap_with_low_confidence_cap_suppression` | `cap_threshold_rescue_branch` |

Claim boundary:

- M92 supports only the repair contract that separates absent target coverage from cap/threshold suppression.
- M92 does not materialize repaired rows, run render/detector jobs, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.

## E008-M93

Implementation unit: `E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0`.

Purpose:

- Materialize the M92 two-branch repair contract into concrete rows without launching render, detector, or trajectory jobs.
- Keep coverage-expansion input staging and cap/threshold probe rows separate so M94 can decide the next evaluation route.

Result:

- Status: `e008_m93_source_gap_two_branch_repair_row_materialization_smoke_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m93_source_gap_two_branch_repair_row_materialization_smoke.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0/`.
- Case repair assignments: 2.
- Coverage-expansion observation / render / detector manifest rows: 12 / 96 / 1.
- Cap-threshold candidate probe rows: 72.
- Budget loss sentinel rows: 5.
- Contract checks: 6 / 6 pass.
- Leakage audits: 4 / 4 pass.
- Long job launched: false.
- Source-gap recovery supported: false.
- Selected next unit: E008-M94 source-gap two-branch repair evaluation route decision.

Claim boundary:

- M93 supports only leakage-safe row materialization for the two repair branches.
- M93 does not run the coverage render/detector branch, evaluate cap-threshold probe success, execute trajectories, or support final real navigation `SR` / `SPL`.

## E008-M94

Implementation unit: `E008-M94_source_gap_two_branch_repair_evaluation_route_decision_v0`.

Purpose:

- Evaluate the fixed M93 cap-branch probe rows with M91 eval-only target distances after ranking.
- Decide whether to evaluate cap repair first, launch coverage render/detector, or stop and record the source-gap repair boundary.

Result:

- Status: `e008_m94_source_gap_two_branch_repair_evaluation_route_decision_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/plan_m94_source_gap_two_branch_repair_evaluation_route_decision.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M94_source_gap_two_branch_repair_evaluation_route_decision_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M94_source_gap_two_branch_repair_evaluation_route_decision_v0/`.
- Cap probe eval rows: 72.
- Cap probe policy metric rows: 3.
- Cap primary-supported policy rows: 0.
- Cap relaxed-supported policy rows: 0.
- Selected route: `coverage_expansion_launcher_adaptation_first`.
- Selected next unit: E008-M95 coverage-expansion render/detector launcher adaptation contract.
- Long job launched: false.

Claim boundary:

- M94 supports only route selection after fixed-order cap probe evaluation.
- M94 does not support source-gap recovery because the cap branch has no primary or relaxed recovery and the coverage branch has not run render/detector inference.
- M94 does not execute trajectories or support final real navigation `SR` / `SPL`.

## E008-M95

Implementation unit: `E008-M95_coverage_expansion_render_detector_launcher_adaptation_contract_v0`.

Purpose:

- Adapt the M93 coverage-expansion rows into concrete M96 render and M97 detector launcher inputs.
- Record long-job commands, expected files, output paths, and verification commands without launching render or detector jobs.

Result:

- Status: `e008_m95_coverage_expansion_render_detector_launcher_adaptation_contract_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/plan_m95_coverage_expansion_render_detector_launcher_adaptation_contract.py`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M95_coverage_expansion_render_detector_launcher_adaptation_contract_v0/`.
- Derived root: `local_dataset/HM3D_navigation_bridge/E008-M95_coverage_expansion_render_detector_launcher_adaptation_contract_v0/`.
- Data-bearing launcher root: `local_dataset/HM3D_navigation_bridge/E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0/`.
- Coverage render rows: 96.
- Coverage detector manifest rows: 1.
- Launcher input rows: 3.
- Long-job command rows: 2.
- Readiness gate failures / warnings: 0 / 0.
- Render script syntax check: pass.
- Render launch ready next: true.
- Detector launch deferred until M96 verification.
- Selected next unit: E008-M96 coverage-expansion render frame staging background launch.
- Long job launched: false.

Launcher inputs:

- `local_dataset/HM3D_navigation_bridge/E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0/render_inputs/render_plan_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0/render_inputs/render_m95_coverage.py`
- `local_dataset/HM3D_navigation_bridge/E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0/detector_inputs/real_proposal_query_manifest.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0/detector_inputs/real_proposal_object_targets.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0/detector_inputs/prompt_set.json`
- `local_dataset/HM3D_navigation_bridge/E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0/detector_inputs/proposal_output_schema.json`

Recorded long-job ledger:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M95_coverage_expansion_render_detector_launcher_adaptation_contract_v0/long_job_command_rows.jsonl`
- The ledger records the exact command, working directory, log path, output path, expected files, and verification command for M96 and M97.

Claim boundary:

- M95 supports launcher adaptation and preflight only.
- M95 does not render RGB-D frames, run detector inference, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.

## E008-M96

Implementation unit: `E008-M96_coverage_expansion_render_frame_staging_launch_v0`.

Purpose:

- Launch and verify coverage-expansion RGB-D/pose frame staging for the remaining source-gap case.
- Keep detector inference and source-gap recovery evaluation as the next dependent unit.

Result:

- Status: `e008_m96_coverage_expansion_render_frame_staging_verified`.
- Launch command source: `experiments/E008_real_navigation_benchmark/artifacts/E008-M95_coverage_expansion_render_detector_launcher_adaptation_contract_v0/long_job_command_rows.jsonl`.
- Verification command: `python experiments/E008_real_navigation_benchmark/tools/verify_m96_coverage_expansion_render_frame_staging.py --require-ready`.
- Artifact root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M96_coverage_expansion_render_frame_staging_launch_v0/`.
- Data-bearing output root: `local_dataset/HM3D_navigation_bridge/E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0/`.
- tmux session: `e008_m96_coverage_render`, stopped after completion.
- Log path: `logs/20260602_103900_e008_m96_coverage_render.log`.
- Expected / ready frames: 96 / 96.
- Ready scans: 1 / 1.
- Snap validation / snap-ready rows: 96 / 96.
- Large snap warning rows: 0.
- Max / mean snap distance: 1.797502m / 0.402737m.
- Detector input files ready: true.
- `ObjectNav` eval goal/viewpoint used for policy: false.
- Selected next unit: E008-M97 coverage-expansion detector candidate-source background launch.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M96_coverage_expansion_render_frame_staging_launch_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M96_coverage_expansion_render_frame_staging_launch_v0/job_status_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M96_coverage_expansion_render_frame_staging_launch_v0/verification_frame_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M96_coverage_expansion_render_frame_staging_launch_v0/verification_scan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M96_coverage_expansion_render_frame_staging_launch_v0/verification_issue_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M96_coverage_expansion_render_frame_staging_launch_v0/report.md`

Claim boundary:

- M96 verifies coverage-expansion rendered frame staging only.
- M96 does not run open-vocabulary detector inference, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.

## E008-M97

Implementation unit: `E008-M97_coverage_expansion_detector_candidate_source_v0`.

Purpose:

- Run open-vocabulary detector candidate-source generation on the E008-M96 coverage-expansion frames.
- Keep verification, navmesh validation, source-gap recovery scoring, and trajectory execution as later dependent units.

Result:

- Status: `e008_m97_coverage_expansion_detector_candidate_source_verified`.
- Launch command source: `experiments/E008_real_navigation_benchmark/artifacts/E008-M95_coverage_expansion_render_detector_launcher_adaptation_contract_v0/long_job_command_rows.jsonl`.
- Verification command: `python experiments/E008_real_navigation_benchmark/tools/verify_m97_coverage_expansion_detector_candidate_source.py --require-ready`.
- tmux session: `e008_m97_coverage_detector`.
- Log path: `logs/20260602_103900_e008_m97_coverage_detector.log`.
- Output root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M97_coverage_expansion_detector_candidate_source_v0/`.
- Input dataset root: `local_dataset/HM3D_navigation_bridge/E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0/`.
- Input manifest: `local_dataset/HM3D_navigation_bridge/E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0/detector_inputs/real_proposal_query_manifest.jsonl`.
- Input render frames: 96.
- Prompt labels: 1 (`sofa`).
- Frames with written predictions: 24 / 96.
- Raw / written predictions: 875 / 24.
- Final / pre-cap candidate rows: 24 / 853.
- Coordinate candidate rows: 24.
- Validator errors / warnings: 0 / 0.
- Matching target rows: 0.
- Selected next unit: E008-M98 coverage-expansion detector candidate navmesh/source-readiness validation.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M97_coverage_expansion_detector_candidate_source_v0/e008_m97_verification_coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M97_coverage_expansion_detector_candidate_source_v0/e008_m97_candidate_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M97_coverage_expansion_detector_candidate_source_v0/e008_m97_route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M97_coverage_expansion_detector_candidate_source_v0/e008_m97_verification_report.md`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M97_coverage_expansion_detector_candidate_source_v0/container_output/real_proposals.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M97_coverage_expansion_detector_candidate_source_v0/container_output/pre_cap_candidate_pool.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M97_coverage_expansion_detector_candidate_source_v0/validator/coverage.json`

Claim boundary:

- M97 supports coverage-expansion detector candidate-source availability and schema/coordinate readiness.
- M97 does not validate navmesh reachability, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.

## E008-M98

Implementation unit: `E008-M98_coverage_expansion_detector_candidate_navmesh_validation_v0`.

Purpose:

- Validate E008-M97 coverage-expansion detector candidates against `HM3D` / `Habitat` navmesh source-readiness.
- Preserve unreachable candidates as explicit failure rows before any visit-order/path or source-gap recovery claim.

Result:

- Status: `e008_m98_coverage_expansion_detector_candidate_navmesh_validation_ready`.
- Gate verdict: `pass` / `coverage_expansion_candidates_source_ready_for_visit_order_path_smoke`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m98_coverage_expansion_detector_candidate_navmesh_validation.py`.
- Output root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M98_coverage_expansion_detector_candidate_navmesh_validation_v0/`.
- Derived output root: `local_dataset/HM3D_navigation_bridge/E008-M98_coverage_expansion_detector_candidate_navmesh_validation_v0/`.
- Input proposal rows: 24.
- Join-ready rows: 24 / 24.
- Coordinate-valid rows: 24 / 24.
- Snapped navigable rows: 24 / 24.
- Source-to-snapped path rows: 11 / 24.
- Unreachable candidate rows: 13.
- Mean source-to-snapped geodesic: 6.394865m.
- Eval goal/viewpoint policy leakage: false.
- Selected next unit: E008-M99 coverage-expansion detector candidate visit-order/path smoke.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M98_coverage_expansion_detector_candidate_navmesh_validation_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M98_coverage_expansion_detector_candidate_navmesh_validation_v0/candidate_navmesh_validation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M98_coverage_expansion_detector_candidate_navmesh_validation_v0/candidate_failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M98_coverage_expansion_detector_candidate_navmesh_validation_v0/scan_source_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M98_coverage_expansion_detector_candidate_navmesh_validation_v0/failure_taxonomy_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M98_coverage_expansion_detector_candidate_navmesh_validation_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M98_coverage_expansion_detector_candidate_navmesh_validation_v0/report.md`

Claim boundary:

- M98 validates coordinate/navmesh/source-readiness for coverage-expansion candidates only.
- M98 does not evaluate source-gap recovery because leakage-safe goal-evaluation is not run here.
- M98 does not execute trajectories or support final real navigation `SR` / `SPL`.

## E008-M99

Implementation unit: `E008-M99_coverage_expansion_detector_candidate_visit_order_path_smoke_v0`.

Purpose:

- Materialize coverage-expansion detector candidate visit-order/path rows after M98 navmesh/source-readiness validation.
- Keep the 13 non-path-ready candidates as explicit failure/accounting rows instead of silently filtering them.

Result:

- Status: `e008_m99_coverage_expansion_detector_candidate_visit_order_path_smoke_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m99_coverage_expansion_detector_candidate_visit_order_path_smoke.py`.
- Output root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M99_coverage_expansion_detector_candidate_visit_order_path_smoke_v0/`.
- Derived output root: `local_dataset/HM3D_navigation_bridge/E008-M99_coverage_expansion_detector_candidate_visit_order_path_smoke_v0/`.
- Input / query-compatible candidates: 24 / 24.
- Path-ready candidates: 11 / 24.
- Failure rows: 13, all `blocked_snapped_point_unreachable_from_episode_start`.
- Visit-order rows: 57.
- Policy metric rows: 8.
- Coverage scan policy metric rows: 4.
- Eval goal/viewpoint policy leakage: false.
- `detector_confidence_all_candidates_v0`: first path-ready rank 3, top1 path-ready false, mean first-ready cost 28.490437m.
- `path_cost_ascending_reachable_subset_v0`: first path-ready rank 1, top1 path-ready true, mean first-ready cost 0.051931m.
- `confidence_path_cost_tradeoff_reachable_subset_v0`: first path-ready rank 1, top1 path-ready true, mean first-ready cost 0.051931m.
- Selected next unit: E008-M100 coverage-expansion leakage-safe detector candidate goal-evaluation smoke.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M99_coverage_expansion_detector_candidate_visit_order_path_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M99_coverage_expansion_detector_candidate_visit_order_path_smoke_v0/candidate_visit_order_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M99_coverage_expansion_detector_candidate_visit_order_path_smoke_v0/policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M99_coverage_expansion_detector_candidate_visit_order_path_smoke_v0/coverage_scan_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M99_coverage_expansion_detector_candidate_visit_order_path_smoke_v0/failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M99_coverage_expansion_detector_candidate_visit_order_path_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M99_coverage_expansion_detector_candidate_visit_order_path_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M99_coverage_expansion_detector_candidate_visit_order_path_smoke_v0/report.md`

Claim boundary:

- M99 supports coverage-expansion visit-order/path-cost materialization only.
- M99 does not evaluate source-gap recovery because eval-only goal/viewpoint matching is not run here.
- M99 does not execute trajectories or support final real navigation `SR` / `SPL`.

## E008-M100

Implementation unit: `E008-M100_coverage_expansion_detector_candidate_goal_evaluation_smoke_v0`.

Purpose:

- Evaluate M99 coverage-expansion detector visit-order rows against `ObjectNav` goal/viewpoint labels after policy order is frozen.
- Confirm that eval-only goal/viewpoint fields are used only for metrics, not for policy ranking.
- Decide whether coverage expansion provides enough proxy recovery to justify trajectory execution.

Result:

- Status: `e008_m100_coverage_expansion_detector_candidate_goal_evaluation_smoke_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m100_coverage_expansion_detector_candidate_goal_evaluation_smoke.py`.
- Output root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M100_coverage_expansion_detector_candidate_goal_evaluation_smoke_v0/`.
- Derived output root: `local_dataset/HM3D_navigation_bridge/E008-M100_coverage_expansion_detector_candidate_goal_evaluation_smoke_v0/`.
- Coverage target rows: 1.
- Eval episode rows: 1.
- Candidate-goal eval rows: 57.
- Scan-policy rows: 4.
- Aggregate policy rows: 4.
- Leakage audit rows: 4 / 4 pass.
- Primary metric: `any_viewpoint_xz_1p0`.
- Primary proxy success: 0 / 1 for all policies.
- Best any-vp XZ mean: 5.484739m for all policies.
- Coverage-expansion proxy recovery observed: false.
- Selected next unit: E008-M101 coverage-expansion detector-goal result interpretation and trajectory-execution decision.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M100_coverage_expansion_detector_candidate_goal_evaluation_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M100_coverage_expansion_detector_candidate_goal_evaluation_smoke_v0/coverage_expansion_eval_goal_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M100_coverage_expansion_detector_candidate_goal_evaluation_smoke_v0/candidate_goal_eval_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M100_coverage_expansion_detector_candidate_goal_evaluation_smoke_v0/policy_goal_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M100_coverage_expansion_detector_candidate_goal_evaluation_smoke_v0/coverage_scan_goal_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M100_coverage_expansion_detector_candidate_goal_evaluation_smoke_v0/failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M100_coverage_expansion_detector_candidate_goal_evaluation_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M100_coverage_expansion_detector_candidate_goal_evaluation_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M100_coverage_expansion_detector_candidate_goal_evaluation_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M100_coverage_expansion_detector_candidate_goal_evaluation_smoke_v0/report.md`

Claim boundary:

- M100 supports leakage-safe proxy goal evaluation for the coverage-expanded case.
- M100 does not support source-gap recovery because no policy reaches the primary eval threshold.
- M100 does not execute trajectories or support final real navigation `SR` / `SPL`.

## E008-M101

Implementation unit: `E008-M101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision_v0`.

Purpose:

- Interpret M100 coverage-expansion goal-evaluation results together with the M94 cap-branch result.
- Decide whether to promote the coverage-expanded detector policies to trajectory execution.
- Decide whether another long coverage render/detector job is justified.

Result:

- Status: `e008_m101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/plan_m101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision.py`.
- Output root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision_v0/`.
- Derived output root: `local_dataset/HM3D_navigation_bridge/E008-M101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision_v0/`.
- Coverage target rows: 1.
- M98 path-ready candidates: 11 / 24.
- M100 candidate-goal eval rows: 57.
- M100 primary success count max: 0.
- M100 best any-vp XZ min: 5.484739m.
- M94 cap primary / relaxed supported policy rows: 0 / 0.
- Current two-branch repair route failed: true.
- Direct trajectory promotion ready: false.
- Additional long job recommended now: false.
- Selected next unit: E008-M102 coverage-expansion failure audit and source-gap repair closure package.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision_v0/coverage_expansion_case_interpretation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision_v0/policy_interpretation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision_v0/repair_branch_closure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision_v0/trajectory_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision_v0/report.md`

Claim boundary:

- M101 supports a negative coverage-expansion gate only.
- M101 does not support source-gap recovery because both cap-threshold and coverage-expansion branches have no primary proxy recovery.
- M101 rejects trajectory promotion and does not support final real navigation `SR` / `SPL`.

## E008-M102

Implementation unit: `E008-M102_coverage_expansion_failure_audit_source_gap_repair_closure_v0`.

Purpose:

- Close the M91-M101 source-gap repair chain after both current-detector repair branches fail.
- Explain why more same-route render/detector work is low-value without changing the candidate-source principle.
- Select the next contract-level route before any additional long job or trajectory execution.

Result:

- Status: `e008_m102_coverage_expansion_failure_audit_source_gap_repair_closure_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/plan_m102_coverage_expansion_failure_audit_source_gap_repair_closure.py`.
- Output root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M102_coverage_expansion_failure_audit_source_gap_repair_closure_v0/`.
- Derived output root: `local_dataset/HM3D_navigation_bridge/E008-M102_coverage_expansion_failure_audit_source_gap_repair_closure_v0/`.
- Source-gap case rows / closed rows: 2 / 2.
- M97 final proposals / pre-cap candidates: 24 / 853.
- M98 path-ready candidates: 11 / 24.
- M100 primary success count max: 0.
- Current detector source-gap repair route closed: true.
- Source-gap recovery supported: false.
- Direct trajectory promotion ready: false.
- Additional long job recommended now: false.
- Selected next unit: E008-M103 alternative proposal-source feasibility and source-gap recovery contract.

Case closure:

| scan_id | category | failure type | closed branch | pre-cap best any-vp m | post-repair best any-vp m | primary hits |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `hm3dnav_00800_TEEsavR23oF_ep22` | sofa | `observation_or_detector_target_coverage_gap` | coverage-expansion branch | 3.850614 | 5.484739 | 0 |
| `hm3dnav_00802_wcojb4TFT35_ep13` | toilet | `localization_threshold_gap_with_low_confidence_cap_suppression` | cap-threshold branch | 1.082507 | 2.399363 | 0 |

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M102_coverage_expansion_failure_audit_source_gap_repair_closure_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M102_coverage_expansion_failure_audit_source_gap_repair_closure_v0/source_gap_case_closure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M102_coverage_expansion_failure_audit_source_gap_repair_closure_v0/failure_mechanism_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M102_coverage_expansion_failure_audit_source_gap_repair_closure_v0/repair_route_closure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M102_coverage_expansion_failure_audit_source_gap_repair_closure_v0/next_route_option_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M102_coverage_expansion_failure_audit_source_gap_repair_closure_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M102_coverage_expansion_failure_audit_source_gap_repair_closure_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M102_coverage_expansion_failure_audit_source_gap_repair_closure_v0/report.md`

Claim boundary:

- M102 supports a negative reviewer-defense claim: the current `GroundingDINO` bbox-depth source-gap repair route failed under leakage-safe fixed-order evaluation.
- M102 supports changing the candidate-source principle before more long detector/render jobs.
- M102 does not support source-gap recovery, deployable policy, real navigation `SR` / `SPL`, final RGB-D/open-vocabulary robustness, or human-intent contribution.

## E008-M103

Implementation unit: `E008-M103_alternative_proposal_source_feasibility_source_gap_recovery_contract_v0`.

Purpose:

- Decide which alternative proposal-source principle should be tested after M102 closed the current detector route.
- Separate deployable source candidates from diagnostic upper-bound sources.
- Fix the M104 pass/warning/fail gate before any long map-construction or trajectory job.

Result:

- Status: `e008_m103_alternative_proposal_source_feasibility_source_gap_recovery_contract_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/plan_m103_alternative_proposal_source_feasibility_source_gap_recovery_contract.py`.
- Output root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M103_alternative_proposal_source_feasibility_source_gap_recovery_contract_v0/`.
- Derived output root: `local_dataset/HM3D_navigation_bridge/E008-M103_alternative_proposal_source_feasibility_source_gap_recovery_contract_v0/`.
- Source-gap case rows: 2.
- Same-detector rerun selected: false.
- `HM3D` semantic candidate coordinate ready: false.
- `ConceptGraphs` image ready: true.
- `ConceptGraphs` E005 route ready: true.
- `OpenMask3D` checkpoints ready: true.
- `OpenMask3D` image ready: false.
- Selected route: `conceptgraphs_hm3d_map_candidate_adapter`.
- Selected next unit: E008-M104 `ConceptGraphs` HM3D source-gap adapter/preflight contract.
- Launch long job now: false.

Route decision:

| route | decision | reason |
| --- | --- | --- |
| `conceptgraphs_hm3d_map_candidate_adapter` | select preflight first | changes the failed bbox-depth proposal principle, has a ready Docker image, and has positive E005 map-candidate evidence |
| `openmask3d_hm3d_3d_instance_proposal` | defer blocked fallback | directly relevant but local Docker/`MinkowskiEngine` blocker remains and no image is ready |
| `hov_sg_hierarchical_map_navigation_baseline` | defer source/runtime audit | useful for broader system baseline, but too heavy for the immediate source-gap gate |
| `hm3d_semantic_object_upper_bound` | diagnostic ceiling only | semantic labels exist, but non-oracle coordinate extraction is blocked and ObjectNav goal/viewpoint leakage must stay metric-only |
| same `GroundingDINO` bbox-depth rerun | reject | M102 already closed both cap-threshold and coverage-expansion branches |

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M103_alternative_proposal_source_feasibility_source_gap_recovery_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M103_alternative_proposal_source_feasibility_source_gap_recovery_contract_v0/source_gap_requirement_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M103_alternative_proposal_source_feasibility_source_gap_recovery_contract_v0/route_feasibility_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M103_alternative_proposal_source_feasibility_source_gap_recovery_contract_v0/input_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M103_alternative_proposal_source_feasibility_source_gap_recovery_contract_v0/m104_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M103_alternative_proposal_source_feasibility_source_gap_recovery_contract_v0/candidate_output_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M103_alternative_proposal_source_feasibility_source_gap_recovery_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M103_alternative_proposal_source_feasibility_source_gap_recovery_contract_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M103_alternative_proposal_source_feasibility_source_gap_recovery_contract_v0/report.md`

Claim boundary:

- M103 supports selecting `ConceptGraphs` HM3D adapter/preflight as the next alternative proposal-source route.
- M103 does not support source-gap recovery, deployable policy, real navigation `SR` / `SPL`, final RGB-D/open-vocabulary robustness, or human-intent contribution.

## E008-M104

Implementation unit: `E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0`.

Purpose:

- Verify whether the two M102 source-gap cases have non-oracle RGB-D/pose inputs that can be materialized for `ConceptGraphs`.
- Separate direct runtime layout readiness from adapter materialization readiness.
- Fix the M105 staging materialization output contract before running any map-construction or candidate-export job.

Result:

- Status: `e008_m104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/plan_m104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract.py`.
- Output root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0/`.
- Derived output root: `local_dataset/HM3D_navigation_bridge/E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0/`.
- Source-gap case rows: 2.
- Selected cases materialization-ready: 2 / 2.
- Direct `ConceptGraphs`-ready cases: 0 / 2.
- Source leakage rows: 0.
- `ConceptGraphs` image ready: true.
- `Habitat` image ready: true.
- Staging materialization required: true.
- Launch long job now: false.
- Candidate rows ready: false.
- Source-gap recovery supported: false.
- Selected next unit: E008-M105 `ConceptGraphs` HM3D source-gap staging materialization smoke.

Case staging:

| scan_id | category | selected bundle | frames | direct ready | materialization ready |
| --- | --- | --- | ---: | --- | --- |
| `hm3dnav_00800_TEEsavR23oF_ep22` | sofa | `m93_coverage_expansion_sofa` | 96 | false | true |
| `hm3dnav_00802_wcojb4TFT35_ep13` | toilet | `m84_source_gap_non_oracle` | 96 | false | true |

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0/source_bundle_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0/scan_layout_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0/case_staging_selection_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0/staging_materialization_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0/future_runtime_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0/candidate_output_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0/m105_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0/report.md`

Claim boundary:

- M104 supports only adapter/materialization feasibility for `ConceptGraphs` HM3D source-gap inputs.
- M104 does not run `ConceptGraphs`, export 3D/map candidates, validate candidate coordinates, evaluate source-gap recovery, execute trajectories, or support real navigation `SR` / `SPL`.

## E008-M105

Implementation unit: `E008-M105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0`.

Purpose:

- Materialize the two M104-selected source-gap cases into a `ConceptGraphs`-compatible staged RGB-D/pose/intrinsic layout.
- Use regular host files rather than host-absolute symlinks to avoid the prior Docker readability failure mode.
- Verify container readability before any bounded `ConceptGraphs` runtime launch.

Result:

- Status: `e008_m105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke.py`.
- Output root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0/`.
- Derived output root: `local_dataset/HM3D_navigation_bridge/E008-M105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0/`.
- Staged root: `local_dataset/HM3D_navigation_bridge/E008-M105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0/conceptgraphs_hm3d_source_gap_staged/`.
- Dataset config: `local_dataset/HM3D_navigation_bridge/E008-M105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0/conceptgraphs_hm3d_source_gap_staged/config/conceptgraphs_hm3d_source_gap.yaml`.
- Ready staged scans: 2 / 2.
- Total frames: 192.
- Color/depth/pose files: 192 / 192 / 192.
- Regular input files: 576 / 576.
- Container readability smoke: true.
- Symlink count under staged root: 0.
- Leakage rows: 0.
- Runtime launched: false.
- Candidate rows ready: false.
- Source-gap recovery supported: false.
- Selected next unit: E008-M106 `ConceptGraphs` HM3D source-gap runtime launch/verification contract.

Case staging:

| scan_id | category | selected bundle | frames | staged ready |
| --- | --- | --- | ---: | --- |
| `hm3dnav_00800_TEEsavR23oF_ep22` | sofa | `m93_coverage_expansion_sofa` | 96 | true |
| `hm3dnav_00802_wcojb4TFT35_ep13` | toilet | `m84_source_gap_non_oracle` | 96 | true |

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0/materialization_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0/frame_materialization_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0/runtime_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0/container_readability_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0/m106_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0/report.md`

Claim boundary:

- M105 supports only staged input layout readiness for a future bounded `ConceptGraphs` runtime.
- M105 does not run `ConceptGraphs`, export 3D/map candidates, validate candidate coordinates, evaluate source-gap recovery, execute trajectories, or support real navigation `SR` / `SPL`.

## E008-M106

Implementation unit: `E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0`.

Purpose:

- Fix the bounded `ConceptGraphs` runtime command for the two M105-staged source-gap cases.
- Record the exact tmux session, log path, output expectations, and completion verifier before launch.
- Keep the long-running job gated on GPU memory rather than blocking Codex or launching under known memory pressure.

Result:

- Status: `e008_m106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_ready_waiting_gpu`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/plan_m106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract.py`.
- Output root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/`.
- Staged root: `local_dataset/HM3D_navigation_bridge/E008-M105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0/conceptgraphs_hm3d_source_gap_staged/`.
- Scan count: 2.
- Docker image ready: true.
- Checkpoints ready: true.
- GPU free memory at contract time: 13,403MiB.
- Launch threshold: 24,000MiB free.
- Blocker: `gpu_memory_below_contract_threshold`.
- Launch now: false.
- tmux session: `e008_m107_conceptgraphs_hm3d_source_gap_runtime`.
- Log path: `logs/20260602_165543_e008_m107_conceptgraphs_hm3d_source_gap_runtime.log`.
- Run script: `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/run_m107_conceptgraphs_hm3d_source_gap_runtime.sh`.
- Verification command: `python experiments/E008_real_navigation_benchmark/tools/verify_m108_conceptgraphs_hm3d_source_gap_runtime_outputs.py --m106-root experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0`.
- M108 verifier status before launch: `e008_m108_conceptgraphs_hm3d_source_gap_runtime_waiting_gpu`.
- Runtime output ready before launch: false.
- Candidate rows ready: false.
- Source-gap recovery supported: false.
- Selected next unit: E008-M107 `ConceptGraphs` HM3D source-gap runtime background launch.
- Selected verification unit: E008-M108 `ConceptGraphs` HM3D source-gap runtime completion verification.

M107 gate:

| gate | condition | current interpretation | next action |
| --- | --- | --- | --- |
| pass | no contract blockers and GPU free memory >= 24,000MiB | false | launch M107 in tmux using the recorded launch command |
| warning | only GPU memory is below threshold while data/image/checkpoint contracts pass | true | wait for GPU memory and then launch without changing data or command |
| fail | staged data, Docker image, or checkpoints are not ready | false | repair blocker before launch |

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/runtime_scan_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/checkpoint_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/expected_output_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/launch_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/verification_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/long_job_policy_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/m107_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/run_m107_conceptgraphs_hm3d_source_gap_runtime.sh`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/verification/m108/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/verification/m108/runtime_inventory_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/verification/m108/report.md`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/report.md`

Claim boundary:

- M106 supports only runtime launch/verification contract readiness.
- M106 does not launch `ConceptGraphs`, export 3D/map candidates, validate candidate coordinates, evaluate source-gap recovery, execute trajectories, or support real navigation `SR` / `SPL`.
- M106's current blocker is operational GPU memory pressure, not data, image, checkpoint, or source-leakage failure.

## E008-M108

Implementation unit: E008-M108 `ConceptGraphs` HM3D source-gap runtime completion verification.

Result:

- Status: `e008_m108_conceptgraphs_hm3d_source_gap_runtime_outputs_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/verify_m108_conceptgraphs_hm3d_source_gap_runtime_outputs.py --m106-root experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0`.
- Output root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/verification/m108/`.
- Background status: `completed`.
- tmux running: false.
- Runtime-ready scans: 2 / 2.
- GSA detections per scan: 20 / 20.
- Full/post PCD ready: true / true for both scans.
- Candidate rows ready: false.
- Source-gap recovery supported: false.
- Real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M109 `ConceptGraphs` HM3D candidate export adapter contract.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/verification/m108/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/verification/m108/runtime_inventory_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0/verification/m108/report.md`

Claim boundary:

- M108 verifies runtime output availability only.
- M108 does not export candidate rows, validate coordinates, evaluate source-gap recovery, execute trajectories, or support final navigation claims.

## E008-M109

Implementation unit: `E008-M109_conceptgraphs_hm3d_candidate_export_adapter_contract_v0`.

Result:

- Status: `e008_m109_conceptgraphs_hm3d_candidate_export_adapter_contract_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/plan_m109_conceptgraphs_hm3d_candidate_export_adapter_contract.py`.
- Output root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M109_conceptgraphs_hm3d_candidate_export_adapter_contract_v0/`.
- Derived output root for future rows: `local_dataset/HM3D_navigation_bridge/E008-M109_conceptgraphs_hm3d_candidate_export_adapter_contract_v0/`.
- M108 status: `e008_m108_conceptgraphs_hm3d_source_gap_runtime_outputs_ready`.
- Runtime-ready scans: 2 / 2.
- Post-PCD object counts: 29 / 42.
- Required object fields checked in `ConceptGraphs` Docker: `bbox_np`, `class_name`, `clip_ft`, `conf`, `pcd_np`.
- Adapter materialization ready: true.
- Candidate rows ready: false.
- Source-gap recovery supported: false.
- Real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M110 `ConceptGraphs` HM3D candidate export materialization smoke.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M109_conceptgraphs_hm3d_candidate_export_adapter_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M109_conceptgraphs_hm3d_candidate_export_adapter_contract_v0/pcd_object_schema_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M109_conceptgraphs_hm3d_candidate_export_adapter_contract_v0/adapter_schema_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M109_conceptgraphs_hm3d_candidate_export_adapter_contract_v0/allowed_blocked_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M109_conceptgraphs_hm3d_candidate_export_adapter_contract_v0/candidate_export_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M109_conceptgraphs_hm3d_candidate_export_adapter_contract_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M109_conceptgraphs_hm3d_candidate_export_adapter_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M109_conceptgraphs_hm3d_candidate_export_adapter_contract_v0/next_action_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M109_conceptgraphs_hm3d_candidate_export_adapter_contract_v0/report.md`

Claim boundary:

- M109 fixes candidate export schema and allowed/blocked inputs only.
- M109 does not materialize candidate rows, validate navmesh reachability, evaluate source-gap recovery, execute trajectories, or support final navigation claims.

## E008-M110

Implementation unit: `E008-M110_conceptgraphs_hm3d_candidate_export_materialization_smoke_v0`.

Purpose:

- Materialize the M109 `ConceptGraphs` HM3D source-gap adapter contract into leakage-safe object/candidate rows.
- Join the two M104-selected source-gap queries to M108 runtime outputs without using eval goal/viewpoint or success labels.
- Attach CLIP text-query scores so the rows can feed M111 navmesh/source-readiness validation.

Result:

- Status: `e008_m110_conceptgraphs_hm3d_candidate_export_materialization_smoke_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m110_conceptgraphs_hm3d_candidate_export_materialization_smoke.py`.
- Output root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M110_conceptgraphs_hm3d_candidate_export_materialization_smoke_v0/`.
- Derived output root: `local_dataset/HM3D_navigation_bridge/E008-M110_conceptgraphs_hm3d_candidate_export_materialization_smoke_v0/`.
- Query rows: 2.
- Object rows: 71.
- Candidate rows: 71.
- Semantic-scored rows: 71 / 71.
- Labels: `sofa`, `toilet`.
- Scan count: 2.
- Candidate rows ready: true.
- Coordinate fields ready: true.
- Semantic scoring ready: true.
- Leakage audit pass: true.
- Source-gap recovery supported: false.
- Real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M111 `ConceptGraphs` HM3D candidate navmesh/source-readiness validation.

Important boundary:

- The `ConceptGraphs` runtime used `class_set none`, so exported `source_class_name` values are generic `item`.
- M110 ranking evidence is therefore CLIP feature/text scoring against the query text, not a class-name recognition claim.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M110_conceptgraphs_hm3d_candidate_export_materialization_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M110_conceptgraphs_hm3d_candidate_export_materialization_smoke_v0/query_join_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M110_conceptgraphs_hm3d_candidate_export_materialization_smoke_v0/object_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M110_conceptgraphs_hm3d_candidate_export_materialization_smoke_v0/candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M110_conceptgraphs_hm3d_candidate_export_materialization_smoke_v0/pcd_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M110_conceptgraphs_hm3d_candidate_export_materialization_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M110_conceptgraphs_hm3d_candidate_export_materialization_smoke_v0/docker_meta.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M110_conceptgraphs_hm3d_candidate_export_materialization_smoke_v0/report.md`

Claim boundary:

- M110 supports candidate row materialization only.
- M110 does not validate navmesh reachability, evaluate source-gap recovery, execute trajectories, or support final real navigation claims.

## E008-M111

Implementation unit: `E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0`.

Purpose:

- Validate M110 `ConceptGraphs` HM3D candidate coordinates against `HM3D` / `Habitat` navmesh reachability.
- Split M110's two source-gap queries into source-ready vs still-source-gap rows before any visit-order/path or goal-evaluation step.
- Keep eval goal/viewpoint fields blocked from policy inputs.

Result:

- Status: `e008_m111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation.py`.
- Output root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0/`.
- Derived output root: `local_dataset/HM3D_navigation_bridge/E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0/`.
- Gate verdict: `pass` / `all_queries_have_path_ready_conceptgraphs_candidate`.
- Candidate rows: 71.
- Join-ready rows: 71 / 71.
- Coordinate-valid rows: 71 / 71.
- Snapped navigable rows: 71 / 71.
- Source-to-snapped path rows: 48 / 71.
- Path-ready candidate rows: 48 / 71.
- Source-ready query rows: 2 / 2.
- Source-ready scan rows: 2 / 2.
- Mean source-to-snapped geodesic: 4.109622647054493m.
- Navmesh status counts: `candidate_path_ready` 48, `blocked_snapped_point_unreachable_from_episode_start` 23.
- Top path-ready semantic rank: sofa rank 3, toilet rank 1.
- Eval goal/viewpoint used for policy: false.
- Source-gap recovery supported: false.
- Real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M112 `ConceptGraphs` HM3D candidate visit-order/path smoke.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0/candidate_navmesh_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0/candidate_navmesh_validation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0/candidate_failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0/query_source_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0/scan_source_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0/failure_taxonomy_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0/docker_navmesh_meta.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0/report.md`

Claim boundary:

- M111 supports candidate coordinate/navmesh/source-readiness validation only.
- M111 does not evaluate source-gap recovery, execute trajectories, support final real navigation claims, or support final RGB-D/open-vocabulary robustness claims.
- M111 does not claim `ConceptGraphs` class-name recognition because M110 source class names are generic `item`; the ranking signal remains CLIP feature/text scoring.

## E008-M112

Implementation unit: `E008-M112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_v0`.

Purpose:

- Materialize M111 `ConceptGraphs` HM3D candidates into leakage-safe visit-order/path-cost rows.
- Compare semantic-score ranking with reachable-subset and path-cost-aware ordering.
- Keep non-path-ready rows as explicit failure/accounting rows rather than silently dropping them.

Result:

- Status: `e008_m112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m112_conceptgraphs_hm3d_candidate_visit_order_path_smoke.py`.
- Output root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_v0/`.
- Derived output root: `local_dataset/HM3D_navigation_bridge/E008-M112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_v0/`.
- Input candidate rows: 71.
- Query-compatible candidate rows: 71.
- Path-ready candidate rows: 48 / 71.
- Failure rows: 23, all `blocked_snapped_point_unreachable_from_episode_start`.
- Visit-order rows: 215.
- Policy metric rows: 12.
- Query-source policy metric rows: 8.
- Leakage audit pass: true.
- Eval goal/viewpoint used for policy: false.
- `conceptgraphs_semantic_all_candidates_v0`: top1-ready queries 1 / 2, mean first-ready rank 2.0, mean first-ready cost 4.511095m.
- `conceptgraphs_semantic_reachable_subset_v0`: top1-ready queries 2 / 2, mean first-ready cost 4.511095m.
- `path_cost_ascending_reachable_subset_v0`: top1-ready queries 2 / 2, mean first-ready cost 0.557376m.
- `semantic_path_cost_tradeoff_reachable_subset_v0`: top1-ready queries 2 / 2, mean first-ready cost 0.599800m.
- Source-gap recovery evaluated: false.
- Real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M113 `ConceptGraphs` HM3D leakage-safe candidate goal-evaluation smoke.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_v0/candidate_visit_order_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_v0/policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_v0/query_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_v0/query_source_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_v0/failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_v0/report.md`

Claim boundary:

- M112 supports `ConceptGraphs` candidate visit-order/path-cost materialization only.
- M112 does not evaluate source-gap recovery because eval-only goal/viewpoint scoring is not run here.
- M112 does not execute trajectories or support final real navigation `SR` / `SPL`.
- M112 does not support final real RGB-D/open-vocabulary robustness.
- M112 does not claim `ConceptGraphs` class-name recognition because M110 source class names are generic `item`; the ranking signal remains CLIP feature/text scoring.

## E008-M113

Implementation unit: `E008-M113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_v0`.

Purpose:

- Evaluate fixed M112 `ConceptGraphs` visit-order rows against `ObjectNav` goals/viewpoints as eval-only labels.
- Decide whether the `ConceptGraphs` alternative source-gap route supports source-gap recovery before trajectory promotion.
- Keep `ObjectNav` goal/viewpoint fields out of policy inputs.

Result:

- Status: `e008_m113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_ready`.
- Command: `python experiments/E008_real_navigation_benchmark/tools/run_m113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke.py`.
- Output root: `experiments/E008_real_navigation_benchmark/artifacts/E008-M113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_v0/`.
- Derived output root: `local_dataset/HM3D_navigation_bridge/E008-M113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_v0/`.
- Query rows: 2.
- Eval episode rows: 2.
- Candidate-goal eval rows: 215.
- Query-policy metric rows: 8.
- Aggregate policy rows: 4.
- Policy goal metric rows: 12.
- Primary eval metric: `any_viewpoint_xz_1p0`.
- Primary proxy success: 0 / 2 for all policies.
- `any_viewpoint_xz_1p5_proxy_sr`: 0.0 for all policies.
- `goal_xz_1p0_proxy_sr`: 0.0 for all policies.
- Mean best any-viewpoint XZ distance: 3.468193m.
- Best any-viewpoint XZ by case: sofa 5.204041m, toilet 1.732344m.
- Leakage audit pass: true.
- Eval goal/viewpoint used for policy: false.
- Source-gap proxy recovery observed: false.
- Real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M114 `ConceptGraphs` HM3D goal-evaluation result interpretation and trajectory decision.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_v0/conceptgraphs_eval_goal_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_v0/candidate_goal_eval_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_v0/policy_goal_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_v0/conceptgraphs_query_goal_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_v0/failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_v0/report.md`

Claim boundary:

- M113 supports leakage-safe `GoalEvalProxySR` / `GoalEvalProxySPL` diagnostics only.
- M113 does not support source-gap recovery because primary proxy success is 0 / 2 for all policies.
- M113 does not execute trajectories or support final real navigation `SR` / `SPL`.
- M113 does not support final real RGB-D/open-vocabulary robustness.
- M113 does not claim `ConceptGraphs` class-name recognition because M110 source class names are generic `item`; the ranking signal remains CLIP feature/text scoring.

## E008-M114

Implementation unit: `E008-M114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision.py
```

Facts:

- Status: `e008_m114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision_ready`.
- Input M111/M112/M113 statuses are ready.
- Query rows: 2.
- M111 candidate rows: 71.
- M111 path-ready candidates: 48.
- M112 visit-order rows: 215.
- M113 candidate-goal eval rows: 215.
- M113 primary success count max: 0.
- Failure split: `severe_candidate_source_coverage_gap` 1, `stop_region_viewpoint_alignment_gap` 1.
- Goal-center 1.5m diagnostic case rows: 1.
- Direct trajectory promotion ready: false.
- Additional long job recommended now: false.
- Selected next unit: E008-M115 `ConceptGraphs` HM3D case-level failure audit and repair route contract.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision_v0/conceptgraphs_case_interpretation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision_v0/policy_interpretation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision_v0/trajectory_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision_v0/repair_route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision_v0/report.md`

Claim boundary:

- M114 supports a negative diagnostic gate: path-ready `ConceptGraphs` candidates are not sufficient for source-gap recovery.
- M114 does not support source-gap recovery, trajectory promotion, final real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, or human-intent contribution.
- M114 does not launch another render, mapping, or trajectory job.

## E008-M115

Implementation unit: `E008-M115_conceptgraphs_hm3d_case_level_failure_audit_repair_route_contract_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m115_conceptgraphs_hm3d_case_failure_audit_repair_route_contract.py
```

Facts:

- Status: `e008_m115_conceptgraphs_hm3d_case_level_failure_audit_repair_route_contract_ready`.
- Input M112/M113/M114 statuses are ready.
- Case audit rows: 2.
- Failure split: `severe_candidate_source_coverage_gap` 1, `stop_region_viewpoint_alignment_gap` 1.
- Selected repair families: `alternative_candidate_source_or_visibility_audit` 1, `stop_region_viewpoint_alignment_audit` 1.
- Source-gap recovery supported: false.
- Direct trajectory promotion ready: false.
- Additional long job recommended now: false.
- Selected next unit: E008-M116 `ConceptGraphs` HM3D stop-region/source-coverage audit materialization contract.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M115_conceptgraphs_hm3d_case_level_failure_audit_repair_route_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M115_conceptgraphs_hm3d_case_level_failure_audit_repair_route_contract_v0/case_failure_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M115_conceptgraphs_hm3d_case_level_failure_audit_repair_route_contract_v0/repair_route_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M115_conceptgraphs_hm3d_case_level_failure_audit_repair_route_contract_v0/route_selection_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M115_conceptgraphs_hm3d_case_level_failure_audit_repair_route_contract_v0/allowed_blocked_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M115_conceptgraphs_hm3d_case_level_failure_audit_repair_route_contract_v0/m116_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M115_conceptgraphs_hm3d_case_level_failure_audit_repair_route_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M115_conceptgraphs_hm3d_case_level_failure_audit_repair_route_contract_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M115_conceptgraphs_hm3d_case_level_failure_audit_repair_route_contract_v0/report.md`

Claim boundary:

- M115 supports case-specific failure split and repair-route contract only.
- M115 does not support source-gap recovery, trajectory promotion, final real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, or human-intent contribution.
- M115 does not launch another render, mapping, or trajectory job.

## E008-M116

Implementation unit: `E008-M116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract.py
```

Facts:

- Status: `e008_m116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_ready`.
- Input M110/M111/M112/M113/M114/M115 statuses are ready.
- Source-coverage audit rows: 1.
- Stop-region alignment audit rows: 1.
- Blocked-input audit rows: 6; blocked-input audit pass: true.
- `sofa` source-coverage audit: path-ready eval candidates 20, min any-viewpoint XZ 5.204041m, primary target-near rows 0, relaxed target-near rows 0.
- `toilet` stop-region audit: goal XZ 1.388981m, nearest viewpoint XZ 1.732344m, min policy rank 23, `candidate_exists_but_not_budget5_visible`.
- Source-gap recovery supported: false.
- Direct trajectory promotion ready: false.
- Additional long job recommended now: false.
- Selected next unit: E008-M117 `ConceptGraphs` HM3D stop-region transform and source-coverage route decision contract.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_v0/source_coverage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_v0/stop_region_alignment_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_v0/case_audit_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_v0/blocked_input_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_v0/repair_route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_v0/m117_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_v0/report.md`

Claim boundary:

- M116 supports leakage-safe audit materialization and repair-route preconditions only.
- M116 does not support source-gap recovery, trajectory promotion, final real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, or human-intent contribution.
- M116 does not launch another render, mapping, or trajectory job.

## E008-M117

Implementation unit: `E008-M117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision.py
```

Facts:

- Status: `e008_m117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_ready`.
- Input M116 status is ready and blocked-input audit pass is true.
- Stop-region transform contract rows: 1.
- Source-coverage route decision rows: 1.
- M117 selects E008-M118 `ConceptGraphs` HM3D non-oracle stop-region transform materialization smoke as the immediate next unit.
- `toilet`: transform input ready true, budget repair required true, selected route `select_m118_stop_region_transform_smoke`.
- `sofa`: current source recoverable without new source false, same-source rerank/re-run rejected, source-coverage external/visibility route deferred but required.
- Source-gap recovery supported: false.
- Direct trajectory promotion ready: false.
- Additional long job recommended now: false.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_v0/stop_region_transform_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_v0/source_coverage_route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_v0/route_priority_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_v0/allowed_blocked_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_v0/m118_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_v0/report.md`

Claim boundary:

- M117 supports route selection only.
- M117 does not materialize transformed stop-region candidates, recover source-gap cases, execute trajectories, or support final real navigation `SR` / `SPL`.

## E008-M118

Implementation unit: `E008-M118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke.py
```

Facts:

- Status: `e008_m118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_ready`.
- Input M117 status is ready.
- Stop-region candidate rows: 50.
- Path-ready stop-region rows: 50 / 50.
- Visit-order rows: 150.
- Candidate-goal eval rows: 150.
- Leakage audit pass: true.
- `stop_region_cardinal_first_budgeted_v0`: budget-5 primary hit true, first hit rank 2, best any-viewpoint XZ 0.135963m.
- `stop_region_path_cost_budgeted_v0` and `stop_region_semantic_path_cost_budgeted_v0`: primary hit true only after rank 28, so budget-5 primary hit false.
- Remaining source-coverage gap rows: 1.
- Source-gap recovery supported: false.
- Direct trajectory promotion ready: false.
- Selected next unit: E008-M119 `ConceptGraphs/HM3D` source-coverage external-or-visibility preflight.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_v0/stop_region_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_v0/stop_region_navmesh_validation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_v0/stop_region_visit_order_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_v0/stop_region_candidate_goal_eval_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_v0/budget_visibility_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_v0/m119_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_v0/report.md`

Claim boundary:

- M118 supports stop-region transform materialization and posthoc proxy recovery for the selected `toilet` stop-region/viewpoint-alignment case.
- M118 does not support a deployable stop-region trigger because the case/source candidate came from the M116/M117 failure audit.
- M118 does not solve the `sofa` source-coverage gap, execute `Habitat` trajectories, or support final real navigation `SR` / `SPL`.

## E008-M119

Implementation unit: `E008-M119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight.py
```

Facts:

- Status: `e008_m119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight_ready`.
- Input M118 status is ready.
- Source-coverage case rows: 1.
- Visibility proxy rows: 2.
- External/source route preflight rows: 6.
- Allowed/blocked input rows: 4.
- Allowed/blocked input audit pass: true.
- Leakage audit pass: true.
- Visibility policy leakage: false.
- Existing source poses far from target view region: true.
- Current source case: `hm3dnav_00800_TEEsavR23oF_ep22` / `sofa`, 29 candidates, 20 path-ready candidates, min any-viewpoint XZ 5.204041m, recoverable now false.
- M84 source route min source-pose to any target viewpoint XZ: 5.551349m.
- M93 source route min source-pose to any target viewpoint XZ: 5.221712m.
- Selected route: `target_free_source_coverage_expansion`.
- Selected next unit: E008-M120 `HM3D` target-free source-coverage expansion contract.
- Source-gap recovery supported: false.
- Direct trajectory promotion ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Long job launch now: false.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight_v0/source_coverage_case_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight_v0/visibility_proxy_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight_v0/external_source_route_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight_v0/allowed_blocked_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight_v0/m120_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight_v0/`

Claim boundary:

- M119 supports source-coverage diagnosis for the remaining `sofa` case.
- M119 supports rejecting same-source `ConceptGraphs` rerank/rerun for source-gap recovery because the source poses are far from the target view region.
- M119 selects target-free source-coverage expansion before trajectory promotion or external-map result claims.
- M119 does not run `VLMaps`, `HOV-SG`, `OpenMask3D`, or another external baseline.
- M119 does not create new observation/source frames, execute trajectories, or support final real navigation `SR` / `SPL`.

## E008-M120

Implementation unit: `E008-M120_hm3d_target_free_source_coverage_expansion_contract_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m120_hm3d_target_free_source_coverage_expansion_contract.py
```

Facts:

- Status: `e008_m120_hm3d_target_free_source_coverage_expansion_contract_ready`.
- Input M119 status is ready.
- Source-coverage case rows: 1.
- Target-free source-expansion route rows: 3.
- Selected route rows: 2.
- M121 materialization contract rows: 2.
- Allowed/blocked input rows: 4.
- Allowed/blocked audit pass: true.
- Uses ObjectNav target/viewpoint for source placement: false.
- Selected primary route: `target_free_navigable_coverage_sweep_v0`, pose budget 24, yaw samples per pose 8.
- Selected secondary route: `target_free_path_prefix_diversity_sweep_v0`, pose budget 16, yaw samples per pose 8.
- Rejected recovery route: `same_source_external_mapper_audit_v0`.
- Launch long job now: false.
- Source-gap recovery supported: false.
- Direct trajectory promotion ready: false.
- Real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M121 `HM3D` target-free source-coverage expansion materialization smoke.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M120_hm3d_target_free_source_coverage_expansion_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M120_hm3d_target_free_source_coverage_expansion_contract_v0/target_free_source_coverage_case_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M120_hm3d_target_free_source_coverage_expansion_contract_v0/target_free_source_expansion_route_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M120_hm3d_target_free_source_coverage_expansion_contract_v0/m121_materialization_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M120_hm3d_target_free_source_coverage_expansion_contract_v0/allowed_blocked_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M120_hm3d_target_free_source_coverage_expansion_contract_v0/m121_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M120_hm3d_target_free_source_coverage_expansion_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M120_hm3d_target_free_source_coverage_expansion_contract_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M120_hm3d_target_free_source_coverage_expansion_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M120_hm3d_target_free_source_coverage_expansion_contract_v0/`

Claim boundary:

- M120 fixes the target-free source-coverage expansion contract and M121 pass/warning/fail gates.
- M120 blocks ObjectNav eval goal, target viewpoints, target object id, candidate-to-target distance, and success labels for source placement.
- M120 does not materialize source poses, render frames, run detector/mapper jobs, recover the `sofa` case, execute trajectories, or support final real navigation `SR` / `SPL`.

## E008-M121

Implementation unit: `E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m121_hm3d_target_free_source_coverage_expansion_materialization_smoke.py
```

Facts:

- Status: `e008_m121_hm3d_target_free_source_coverage_expansion_materialization_smoke_ready_with_snap_warnings`.
- Input M120 status: `e008_m120_hm3d_target_free_source_coverage_expansion_contract_ready`.
- Source-coverage case rows: 1.
- Observation pose rows: 40.
- Snap validation rows: 40.
- Snap-ready rows: 30 / 40.
- Unique snapped XZ cells: 38.
- Render plan rows: 320.
- Detector manifest rows: 2.
- Uses ObjectNav target/viewpoint for source placement: false.
- M122 launcher contract ready: true.
- Launch long job now: false.
- Source-gap recovery supported: false.
- Real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M122 `HM3D` target-free source-coverage render/detector launcher contract.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0/target_free_observation_pose_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0/target_free_snap_validation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0/target_free_render_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0/target_free_detector_manifest_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0/allowed_blocked_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0/m122_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0/`

Claim boundary:

- M121 supports target-free source materialization and M122 launcher readiness only.
- M121 snap readiness is partial: 30 / 40 source poses are path-ready after navmesh snap, so M122 must keep snap warning rows visible.
- M121 does not render RGB-D frames, run open-vocabulary detector/mapping inference, recover the `sofa` source-gap case, execute trajectories, or support final real navigation `SR` / `SPL`.

## E008-M122

Implementation unit: `E008-M122_hm3d_target_free_source_coverage_render_detector_launcher_contract_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m122_hm3d_target_free_source_coverage_render_detector_launcher_contract.py
```

Facts:

- Status: `e008_m122_hm3d_target_free_source_coverage_render_detector_launcher_contract_ready_with_snap_warnings`.
- Input M121 status: `e008_m121_hm3d_target_free_source_coverage_expansion_materialization_smoke_ready_with_snap_warnings`.
- Target-free render rows: 320.
- Target-free detector manifest rows: 2.
- Object target rows: 1.
- Launcher input materialization rows: 6.
- Long-job command rows: 2.
- Readiness gate fail / warning rows: 0 / 1.
- Uses ObjectNav target/viewpoint for source placement: false.
- Launch long job now: false.
- Source-gap recovery supported: false.
- Real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M123 `HM3D` target-free source-coverage render frame staging background launch.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M122_hm3d_target_free_source_coverage_render_detector_launcher_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M122_hm3d_target_free_source_coverage_render_detector_launcher_contract_v0/target_free_render_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M122_hm3d_target_free_source_coverage_render_detector_launcher_contract_v0/target_free_detector_manifest_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M122_hm3d_target_free_source_coverage_render_detector_launcher_contract_v0/target_free_object_target_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M122_hm3d_target_free_source_coverage_render_detector_launcher_contract_v0/launcher_input_materialization_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M122_hm3d_target_free_source_coverage_render_detector_launcher_contract_v0/long_job_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M122_hm3d_target_free_source_coverage_render_detector_launcher_contract_v0/m123_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M122_hm3d_target_free_source_coverage_render_detector_launcher_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M122_hm3d_target_free_source_coverage_render_detector_launcher_contract_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M122_hm3d_target_free_source_coverage_render_detector_launcher_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0/render_inputs/`
- `local_dataset/HM3D_navigation_bridge/E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0/detector_inputs/`

Long-job ledger:

- E008-M123 render session: `e008_m123_target_free_render`, latest successful log `logs/20260606_025834_e008_m123_target_free_render.log`, output under `local_dataset/HM3D_navigation_bridge/E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0/`.
- E008-M124 detector session: `e008_m124_target_free_detector`, latest successful log `logs/20260606_094032_e008_m124_target_free_detector.log`, output under `experiments/E008_real_navigation_benchmark/artifacts/E008-M124_target_free_source_coverage_detector_candidate_source_v0/`.
- E008-M124 completed after E008-M123 depth-filtered render verification.

Claim boundary:

- M122 supports launcher/readiness evidence only.
- M122 does not launch rendering, run open-vocabulary detector/mapping inference, recover the `sofa` source-gap case, execute trajectories, or support final real navigation `SR` / `SPL`.
- M122 keeps the M121 snap-warning boundary visible; M123 has verified a depth-filtered detector-usable frame subset before M124 detector execution.

## E008-M123

Implementation unit: `E008-M123_target_free_source_coverage_render_frame_staging_launch_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/launch_m123_target_free_render_frame_staging.py
python experiments/E008_real_navigation_benchmark/tools/verify_m123_target_free_render_frame_staging.py --require-ready
```

Facts:

- Launch status after GPU-available relaunch: `e008_m123_target_free_render_frame_staging_launched`.
- Verification status after depth repair: `e008_m123_target_free_render_frame_staging_verified_with_depth_filtered_frames`.
- tmux session: `e008_m123_target_free_render`.
- Log path: `logs/20260606_025834_e008_m123_target_free_render.log`.
- Render plan rows: 320.
- Generated color/depth/pose files: 320 / 320 / 320.
- Ready frames after verification: 295 / 320.
- Frame issue rows: 25.
- Failure type: depth files exist, but `depth_positive` is false for 25 frames.
- Depth repair status: `e008_m123_target_free_render_depth_validity_repair_ready`.
- Original / repaired detector sampled frames: 320 / 295.
- Detector sampled ready frames after repair: 295 / 295.
- Detector sampled invalid frames after repair: 0.
- Repaired manifest counts by route: 174 and 121 sampled frames.
- Detector input files ready: true.
- `tmux` running after verification: false.
- Full render-frame staging ready: false.
- Depth-filtered detector manifest ready: true.
- GPU free memory observed before relaunch: 31,282MiB / 32,607MiB.
- Container smoke with `research3/habitat-h001:20260508-calib-artifacts` passed for `habitat_sim` import and render script visibility.
- Selected next unit: E008-M124 target-free source-coverage detector candidate-source background launch.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M123_target_free_source_coverage_render_frame_staging_launch_v0/launch_coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M123_target_free_source_coverage_render_frame_staging_launch_v0/preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M123_target_free_source_coverage_render_frame_staging_launch_v0/long_job_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M123_target_free_source_coverage_render_frame_staging_launch_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M123_target_free_source_coverage_render_frame_staging_launch_v0/job_status_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M123_target_free_source_coverage_render_frame_staging_launch_v0/report.md`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M123_target_free_source_coverage_render_frame_staging_launch_v0/depth_repair_coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M123_target_free_source_coverage_render_frame_staging_launch_v0/depth_repair_dropped_frame_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M123_target_free_source_coverage_render_frame_staging_launch_v0/depth_repair_manifest_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0/detector_inputs/real_proposal_query_manifest.m122_pre_m123_depth_repair.jsonl`

Claim boundary:

- M123 is complete only as detector-input frame staging with depth-filtered frames.
- M123 does not support full 320-frame render validity, detector candidate quality, source-gap recovery, real navigation `SR` / `SPL`, deployable search policy, or final RGB-D/open-vocabulary robustness.
- M124 is complete; its detector output carries the 295-frame detector-subset boundary.

## E008-M124

Implementation unit: `E008-M124_target_free_source_coverage_detector_candidate_source_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/launch_m124_target_free_detector_candidate_source.py
python experiments/E008_real_navigation_benchmark/tools/verify_m124_target_free_detector_candidate_source.py --require-ready
```

Facts:

- Initial launch status: `e008_m124_target_free_detector_candidate_source_failed_or_needs_review`.
- Initial failure cause: `HF_CACHE` permission error under `local_dataset/ConceptGraphs_model_cache/huggingface`.
- Repair: launcher now uses writable cache `local_dataset/HM3D_navigation_bridge/model_cache/huggingface`.
- Relaunch status: `e008_m124_target_free_detector_candidate_source_launched`.
- Final verifier status: `e008_m124_target_free_detector_candidate_source_ready`.
- tmux session: `e008_m124_target_free_detector`.
- tmux running after verification: false.
- Latest log path: `logs/20260606_094032_e008_m124_target_free_detector.log`.
- Detector manifest rows: 2.
- Detector sampled frames: 295.
- Prediction rows: 24.
- Raw prediction count: 2,986.
- Pre-cap candidate rows: 2,910.
- Validator errors/warnings: 0/0.
- Source frames: M123 depth-filtered detector manifest.
- Output path: `experiments/E008_real_navigation_benchmark/artifacts/E008-M124_target_free_source_coverage_detector_candidate_source_v0/`.
- Selected next unit: E008-M125 target-free detector candidate navmesh/source-readiness validation.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M124_target_free_source_coverage_detector_candidate_source_v0/e008_m124_launch_coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M124_target_free_source_coverage_detector_candidate_source_v0/e008_m124_verification_coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M124_target_free_source_coverage_detector_candidate_source_v0/long_job_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M124_target_free_source_coverage_detector_candidate_source_v0/launch_report.md`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M124_target_free_source_coverage_detector_candidate_source_v0/e008_m124_verification_report.md`

Claim boundary:

- M124 supports target-free detector candidate-source generation over the M123 depth-filtered subset only.
- M124 does not support source-gap recovery, real navigation `SR` / `SPL`, deployable search policy, or final RGB-D/open-vocabulary robustness.

## E008-M125

Implementation unit: `E008-M125_target_free_detector_candidate_navmesh_validation_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m125_target_free_detector_candidate_navmesh_validation.py
```

Facts:

- Status: `e008_m125_target_free_detector_candidate_navmesh_validation_ready`.
- Gate verdict: `pass`.
- Gate reason: `target_free_detector_candidates_source_ready_for_visit_order_path_smoke`.
- Input candidates: 24.
- Coordinate-valid candidates: 24/24.
- Snapped navigable candidates: 24/24.
- Source-to-snapped path found: 15/24.
- Candidate usable for path smoke: 15.
- Blocked snapped point unreachable from episode start: 9.
- Source-ready scans: 1/1.
- Label counts: `sofa` 24.
- Selected next unit: E008-M126 target-free detector candidate visit-order/path smoke.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M125_target_free_detector_candidate_navmesh_validation_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M125_target_free_detector_candidate_navmesh_validation_v0/candidate_navmesh_validation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M125_target_free_detector_candidate_navmesh_validation_v0/candidate_failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M125_target_free_detector_candidate_navmesh_validation_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M125_target_free_detector_candidate_navmesh_validation_v0/`

Claim boundary:

- M125 supports candidate coordinate/navmesh/source-readiness validation only.
- M125 does not support source-gap recovery, leakage-safe goal recovery, trajectory execution, deployable search policy, real navigation `SR` / `SPL`, or final RGB-D/open-vocabulary robustness.

## E008-M126

Implementation unit: `E008-M126_target_free_detector_candidate_visit_order_path_smoke_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m126_target_free_detector_candidate_visit_order_path_smoke.py
```

Facts:

- Status: `e008_m126_target_free_detector_candidate_visit_order_path_smoke_ready`.
- Input M125 status: `e008_m125_target_free_detector_candidate_navmesh_validation_ready`.
- Input candidates: 24.
- Query-compatible candidates: 24.
- Path-ready candidates: 15/24.
- Failure rows: 9, all `blocked_snapped_point_unreachable_from_episode_start`.
- Visit-order rows: 69.
- Policy count: 4.
- Leakage audit pass: true.
- Eval-only `ObjectNav` goal/viewpoint fields used for policy: false.
- `detector_confidence_all_candidates_v0`: first path-ready rank 2, first path-ready cost 2.273105m, top1 path-ready false.
- `path_cost_ascending_reachable_subset_v0`: first path-ready rank 1, first path-ready cost 0.050025m.
- `confidence_path_cost_tradeoff_reachable_subset_v0`: first path-ready rank 1, first path-ready cost 0.083614m.
- Selected next unit: E008-M127 target-free leakage-safe detector candidate goal-evaluation smoke.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M126_target_free_detector_candidate_visit_order_path_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M126_target_free_detector_candidate_visit_order_path_smoke_v0/candidate_visit_order_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M126_target_free_detector_candidate_visit_order_path_smoke_v0/policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M126_target_free_detector_candidate_visit_order_path_smoke_v0/scan_source_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M126_target_free_detector_candidate_visit_order_path_smoke_v0/failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M126_target_free_detector_candidate_visit_order_path_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M126_target_free_detector_candidate_visit_order_path_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M126_target_free_detector_candidate_visit_order_path_smoke_v0/`

Claim boundary:

- M126 supports target-free detector candidate visit-order/path-cost materialization only.
- M126 does not support source-gap recovery, leakage-safe goal recovery, trajectory execution, deployable search policy, real navigation `SR` / `SPL`, or final RGB-D/open-vocabulary robustness.

## E008-M127

Implementation unit: `E008-M127_target_free_detector_candidate_goal_evaluation_smoke_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m127_target_free_detector_candidate_goal_evaluation_smoke.py
```

Facts:

- Status: `e008_m127_target_free_detector_candidate_goal_evaluation_smoke_ready`.
- Input M126 status: `e008_m126_target_free_detector_candidate_visit_order_path_smoke_ready`.
- Scan-source rows: 1.
- Eval episode rows: 1.
- Candidate-goal eval rows: 69.
- Leakage audit pass: true.
- Eval-only `ObjectNav` goal/viewpoint fields used for policy: false.
- Primary metric: `any_viewpoint_xz_1p0`.
- Primary proxy recovery observed: true.
- Primary proxy SR: 1/1 for all 4 policies.
- `detector_confidence_all_candidates_v0`: primary hit rank 5, proxy SPL 0.357073.
- `detector_confidence_reachable_subset_v0`: primary hit rank 3, proxy SPL 0.357073.
- `path_cost_ascending_reachable_subset_v0`: primary hit rank 10, proxy SPL 0.779043.
- `confidence_path_cost_tradeoff_reachable_subset_v0`: primary hit rank 12, proxy SPL 0.779043.
- `goal_xz_1p0` proxy SR: 0 for all policies.
- Selected next unit: E008-M128 target-free detector-goal result interpretation and trajectory-execution decision.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M127_target_free_detector_candidate_goal_evaluation_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M127_target_free_detector_candidate_goal_evaluation_smoke_v0/target_free_eval_goal_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M127_target_free_detector_candidate_goal_evaluation_smoke_v0/candidate_goal_eval_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M127_target_free_detector_candidate_goal_evaluation_smoke_v0/policy_goal_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M127_target_free_detector_candidate_goal_evaluation_smoke_v0/target_free_scan_goal_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M127_target_free_detector_candidate_goal_evaluation_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M127_target_free_detector_candidate_goal_evaluation_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M127_target_free_detector_candidate_goal_evaluation_smoke_v0/`

Claim boundary:

- M127 supports leakage-safe target-free goal-evaluation proxy only.
- M127 does not support trajectory execution, deployable search policy, real navigation `SR` / `SPL`, or final RGB-D/open-vocabulary robustness.

## E008-M128

Implementation unit: `E008-M128_target_free_detector_goal_result_interpretation_trajectory_decision_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m128_target_free_detector_goal_result_interpretation_trajectory_decision.py
```

Facts:

- Status: `e008_m128_target_free_detector_goal_result_interpretation_trajectory_decision_ready`.
- Input M125 status: `e008_m125_target_free_detector_candidate_navmesh_validation_ready`.
- Input M126 status: `e008_m126_target_free_detector_candidate_visit_order_path_smoke_ready`.
- Input M127 status: `e008_m127_target_free_detector_candidate_goal_evaluation_smoke_ready`.
- Target-free scan rows: 1.
- M125 path-ready candidates: 15 / 24.
- M126 visit-order rows: 69.
- M127 candidate-goal eval rows: 69.
- Best any-viewpoint XZ distance: 0.856516m.
- Best goal-center XZ distance: 2.857646m.
- Primary proxy success: 1 / 1 for all four policies.
- `goal_xz_1p0` proxy success: 0 / 1 for all policies.
- Trajectory contract promotion ready: true.
- Direct trajectory execution ready: false.
- Long job launch now: false.
- Selected next unit: E008-M129 target-free detector-policy trajectory execution contract and Docker preflight.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M128_target_free_detector_goal_result_interpretation_trajectory_decision_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M128_target_free_detector_goal_result_interpretation_trajectory_decision_v0/target_free_case_interpretation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M128_target_free_detector_goal_result_interpretation_trajectory_decision_v0/policy_interpretation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M128_target_free_detector_goal_result_interpretation_trajectory_decision_v0/trajectory_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M128_target_free_detector_goal_result_interpretation_trajectory_decision_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M128_target_free_detector_goal_result_interpretation_trajectory_decision_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M128_target_free_detector_goal_result_interpretation_trajectory_decision_v0/`

Claim boundary:

- M128 supports a bounded trajectory-contract gate because M127 recovered the selected target-free case under a leakage-safe viewpoint proxy.
- M128 does not support real navigation `SR` / `SPL`, deployable search policy, final RGB-D/open-vocabulary robustness, or human intent as a main claim.
- The result remains one target-free case; M129/M130 must separate executed navigation behavior from proxy goal-evaluation behavior.

## E008-M129

Implementation unit: `E008-M129_target_free_detector_policy_trajectory_contract_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m129_target_free_detector_policy_trajectory_contract.py
```

Facts:

- Status: `e008_m129_target_free_detector_policy_trajectory_contract_ready_runner_next`.
- Trajectory candidate rows: 69.
- Trajectory execution plan rows: 4.
- Eval goal rows: 1.
- Oracle path rows: 1.
- Policy count: 4.
- Full-ranked min `GoalEvalProxySR`: 1.000000.
- Budget-5 min `GoalEvalProxySR`: 0.000000.
- Leakage audit pass: true.
- Docker preflight pass: true.
- `Habitat` Docker image inspect: true.
- `nvidia-smi` preflight: true.
- M37 generalized runner compile pass: true.
- M130 runner wrapper compile pass: true.
- Selected next unit: E008-M130 target-free detector-policy trajectory execution smoke.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M129_target_free_detector_policy_trajectory_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M129_target_free_detector_policy_trajectory_contract_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M129_target_free_detector_policy_trajectory_contract_v0/trajectory_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M129_target_free_detector_policy_trajectory_contract_v0/episode_goal_eval_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M129_target_free_detector_policy_trajectory_contract_v0/oracle_path_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M129_target_free_detector_policy_trajectory_contract_v0/trajectory_execution_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M129_target_free_detector_policy_trajectory_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M129_target_free_detector_policy_trajectory_contract_v0/docker_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M129_target_free_detector_policy_trajectory_contract_v0/m130_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M129_target_free_detector_policy_trajectory_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M129_target_free_detector_policy_trajectory_contract_v0/`

Claim boundary:

- M129 supports only the runner-compatible target-free trajectory execution contract and Docker/data/runner preflight.
- M129 does not execute `Habitat` trajectories and does not produce real navigation `SR` / `SPL`.
- The next unit must run M130 before any trajectory result interpretation.

## E008-M130

Implementation unit: `E008-M130_target_free_detector_policy_trajectory_execution_smoke_v0`.

Command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp \
  -v /home/yoohyun/research3/local_dataset/data:/data:ro \
  -v /home/yoohyun/research2:/work -w /work \
  research3/habitat-h001:20260508-calib-artifacts bash -lc \
  "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m130_target_free_detector_policy_trajectory_execution_smoke.py \
  --m129-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M129_target_free_detector_policy_trajectory_contract_v0 \
  --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M130_target_free_detector_policy_trajectory_execution_smoke_v0 \
  --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M130_target_free_detector_policy_trajectory_execution_smoke_v0"
```

Facts:

- Status: `e008_m130_target_free_detector_policy_trajectory_execution_smoke_ready`.
- Inside Docker: true.
- Trajectory candidate rows: 69.
- Trajectory attempt rows: 30.
- Scan-policy metric rows: 4.
- Trajectory success rows: 4.
- Aggregate trajectory `SR`: 1.000000.
- Mean trajectory `SPL`: 0.398100.
- Leakage audit pass: true.
- `path_cost_ascending_reachable_subset_v0` `SR` / `SPL`: 1.000000 / 0.092750.
- `detector_confidence_reachable_subset_v0` `SR` / `SPL`: 1.000000 / 0.701267.
- `detector_confidence_all_candidates_v0` `SR` / `SPL`: 1.000000 / 0.701267.
- `confidence_path_cost_tradeoff_reachable_subset_v0` `SR` / `SPL`: 1.000000 / 0.097119.
- Path-cost method pairwise `delta_SPL` vs detector-confidence baselines: -0.608517.
- Selected next unit: E008-M131 target-free detector-policy trajectory result interpretation and scale decision.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M130_target_free_detector_policy_trajectory_execution_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M130_target_free_detector_policy_trajectory_execution_smoke_v0/dynamic_stale_trajectory_attempt_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M130_target_free_detector_policy_trajectory_execution_smoke_v0/dynamic_stale_trajectory_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M130_target_free_detector_policy_trajectory_execution_smoke_v0/pairwise_policy_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M130_target_free_detector_policy_trajectory_execution_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M130_target_free_detector_policy_trajectory_execution_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M130_target_free_detector_policy_trajectory_execution_smoke_v0/`

Claim boundary:

- M130 supports executed one-case target-free trajectory smoke and metric plumbing.
- M130 does not support a positive navigation-policy claim because all policies tie on `SR` and path-cost ordering loses `SPL` to detector-confidence baselines.
- M130 does not support final real navigation `SR` / `SPL`, deployable search policy, final RGB-D/open-vocabulary robustness, or human intent as a main claim.

## E008-M131

Implementation unit: `E008-M131_target_free_detector_policy_trajectory_result_interpretation_scale_decision_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m131_target_free_detector_policy_trajectory_result_interpretation_scale_decision.py
```

Facts:

- Status: `e008_m131_target_free_detector_policy_trajectory_result_interpretation_scale_decision_ready`.
- M130 trajectory `SR` / mean `SPL`: 1.000000 / 0.398100.
- Method policy: `path_cost_ascending_reachable_subset_v0`.
- Method `SR` / `SPL`: 1.000000 / 0.092750.
- Primary detector baseline: `detector_confidence_reachable_subset_v0`.
- Primary detector `SR` / `SPL`: 1.000000 / 0.701267.
- Method `delta_SPL` vs detector-confidence: -0.608517.
- Method `delta_PathLengthM` vs detector-confidence: +94.858374.
- Proxy-to-trajectory flip detected: true.
- Scale current path-cost policy ready: false.
- Selected next unit: E008-M132 target-free trajectory-aware visit-order repair contract.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M131_target_free_detector_policy_trajectory_result_interpretation_scale_decision_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M131_target_free_detector_policy_trajectory_result_interpretation_scale_decision_v0/policy_result_interpretation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M131_target_free_detector_policy_trajectory_result_interpretation_scale_decision_v0/proxy_trajectory_consistency_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M131_target_free_detector_policy_trajectory_result_interpretation_scale_decision_v0/failure_diagnosis_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M131_target_free_detector_policy_trajectory_result_interpretation_scale_decision_v0/gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M131_target_free_detector_policy_trajectory_result_interpretation_scale_decision_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M131_target_free_detector_policy_trajectory_result_interpretation_scale_decision_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M131_target_free_detector_policy_trajectory_result_interpretation_scale_decision_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M131_target_free_detector_policy_trajectory_result_interpretation_scale_decision_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M131_target_free_detector_policy_trajectory_result_interpretation_scale_decision_v0/`

Claim boundary:

- M131 makes M130 usable as a diagnostic execution table, not a positive navigation result.
- M131 rejects scaling the current source-to-candidate path-cost policy because it accumulates target-far visits in executed trajectory space.
- M131 does not support final real navigation `SR` / `SPL`, deployable search policy, final RGB-D/open-vocabulary robustness, or human intent as a main claim.

## E008-M132

Implementation unit: `E008-M132_target_free_trajectory_aware_visit_order_repair_contract_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m132_target_free_trajectory_aware_visit_order_repair_contract.py
```

Facts:

- Status: `e008_m132_target_free_trajectory_aware_visit_order_repair_contract_ready`.
- Path-ready candidate rows for repair: 15.
- Selected repair policy: `trajectory_greedy_confidence_path_repair_v0`.
- Selected pairwise matrix: `candidate_to_candidate_geodesic_matrix_v0`.
- Allowed input rows: 12.
- Blocked input rows: 15.
- Policy repair contract rows: 5.
- M133 materialization plan rows: 1.
- Selected next unit: E008-M133 target-free trajectory-aware visit-order repair materialization smoke.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M132_target_free_trajectory_aware_visit_order_repair_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M132_target_free_trajectory_aware_visit_order_repair_contract_v0/failure_to_repair_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M132_target_free_trajectory_aware_visit_order_repair_contract_v0/allowed_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M132_target_free_trajectory_aware_visit_order_repair_contract_v0/blocked_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M132_target_free_trajectory_aware_visit_order_repair_contract_v0/trajectory_cost_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M132_target_free_trajectory_aware_visit_order_repair_contract_v0/policy_repair_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M132_target_free_trajectory_aware_visit_order_repair_contract_v0/m133_materialization_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M132_target_free_trajectory_aware_visit_order_repair_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M132_target_free_trajectory_aware_visit_order_repair_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M132_target_free_trajectory_aware_visit_order_repair_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M132_target_free_trajectory_aware_visit_order_repair_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M132_target_free_trajectory_aware_visit_order_repair_contract_v0/`

Claim boundary:

- M132 fixes a repair contract only. It does not create repaired rows or execute trajectories.
- M132 blocks scale-up of the current source-to-candidate path-cost policy and selects M133 pairwise/current-pose cost materialization.
- M132 does not support final real navigation `SR` / `SPL`, deployable search policy, final RGB-D/open-vocabulary robustness, or human intent as a main claim.

## E008-M133

Implementation unit: `E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0`.

Command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp \
  -v /home/yoohyun/research3/local_dataset/data:/data:ro \
  -v /home/yoohyun/research2:/work -w /work \
  research3/habitat-h001:20260508-calib-artifacts bash -lc \
  "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m133_target_free_trajectory_aware_visit_order_repair_materialization.py \
  --m129-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M129_target_free_detector_policy_trajectory_contract_v0 \
  --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0 \
  --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0"
```

Facts:

- Status: `e008_m133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_ready`.
- Path-ready candidate universe rows: 15.
- Cost matrix rows: 225 / 225 expected.
- Cost matrix path-found rows: 171; path-missing rows: 54.
- Repair candidate rows: 75.
- Repair execution plan rows: 5.
- Leakage audit pass: true.
- Runner alias files ready: `dynamic_stale_overlay_trajectory_candidate_rows.jsonl`, `trajectory_execution_plan_rows.jsonl`.
- Selected next unit: E008-M134 target-free trajectory-aware repair trajectory execution contract / Docker preflight.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0/trajectory_cost_matrix_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0/trajectory_repair_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0/trajectory_repair_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0/trajectory_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0/policy_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0/`

Claim boundary:

- M133 materializes repaired visit-order rows only. It does not execute trajectories.
- `ObjectNav` goal/viewpoint fields are copied only for metric use by the next runner and are not present in policy rows.
- M133 does not support final real navigation `SR` / `SPL`, deployable search policy, final RGB-D/open-vocabulary robustness, or human intent as a main claim.

## E008-M134

Implementation unit: `E008-M134_target_free_trajectory_aware_repair_trajectory_contract_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m134_target_free_trajectory_aware_repair_trajectory_contract.py
```

Facts:

- Status: `e008_m134_target_free_trajectory_aware_repair_trajectory_contract_ready_runner_next`.
- Candidate rows: 75.
- Execution plan rows: 5.
- Eval goal rows / oracle path rows: 1 / 1.
- Trajectory cost matrix rows: 225.
- Leakage audit pass: true.
- Docker preflight pass: true.
- Runner compile pass: true.
- Selected next unit: E008-M135 target-free trajectory-aware repair trajectory execution smoke.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M134_target_free_trajectory_aware_repair_trajectory_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M134_target_free_trajectory_aware_repair_trajectory_contract_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M134_target_free_trajectory_aware_repair_trajectory_contract_v0/trajectory_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M134_target_free_trajectory_aware_repair_trajectory_contract_v0/episode_goal_eval_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M134_target_free_trajectory_aware_repair_trajectory_contract_v0/oracle_path_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M134_target_free_trajectory_aware_repair_trajectory_contract_v0/trajectory_cost_matrix_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M134_target_free_trajectory_aware_repair_trajectory_contract_v0/trajectory_execution_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M134_target_free_trajectory_aware_repair_trajectory_contract_v0/docker_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M134_target_free_trajectory_aware_repair_trajectory_contract_v0/m135_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M134_target_free_trajectory_aware_repair_trajectory_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M134_target_free_trajectory_aware_repair_trajectory_contract_v0/`

Claim boundary:

- M134 supports only execution contract / Docker preflight.
- M134 does not execute trajectories or support final real navigation `SR` / `SPL`, deployable search policy, final RGB-D/open-vocabulary robustness, or human intent as a main claim.

## E008-M135

Implementation unit: `E008-M135_target_free_trajectory_aware_repair_trajectory_execution_smoke_v0`.

Command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp \
  -v /home/yoohyun/research3/local_dataset/data:/data:ro \
  -v /home/yoohyun/research2:/work -w /work \
  research3/habitat-h001:20260508-calib-artifacts bash -lc \
  "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m135_target_free_trajectory_aware_repair_trajectory_execution_smoke.py \
  --m134-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M134_target_free_trajectory_aware_repair_trajectory_contract_v0 \
  --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M135_target_free_trajectory_aware_repair_trajectory_execution_smoke_v0 \
  --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M135_target_free_trajectory_aware_repair_trajectory_execution_smoke_v0"
```

Facts:

- Status: `e008_m135_target_free_trajectory_aware_repair_trajectory_execution_smoke_ready`.
- Trajectory candidate rows: 75.
- Trajectory attempt rows: 31.
- Scan-policy metric rows: 5.
- Leakage audit pass: true.
- Aggregate `SR`: 1.0.
- Mean aggregate `SPL`: 0.422187.
- Selected repair policy `trajectory_greedy_confidence_path_repair_v0`: `SR` 1.0, `SPL` 0.329622, path length 30.759799m, candidate visits 5.
- Detector-confidence / confidence-only baselines: `SR` 1.0, `SPL` 0.701267, path length 14.458268m, candidate visits 3.
- Path-only baseline: `SPL` 0.286028.
- Path-cost ascending baseline: `SPL` 0.092750.
- Selected next unit: E008-M136 target-free trajectory-aware repair trajectory result interpretation and scale decision.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M135_target_free_trajectory_aware_repair_trajectory_execution_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M135_target_free_trajectory_aware_repair_trajectory_execution_smoke_v0/dynamic_stale_trajectory_attempt_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M135_target_free_trajectory_aware_repair_trajectory_execution_smoke_v0/dynamic_stale_trajectory_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M135_target_free_trajectory_aware_repair_trajectory_execution_smoke_v0/pairwise_policy_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M135_target_free_trajectory_aware_repair_trajectory_execution_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M135_target_free_trajectory_aware_repair_trajectory_execution_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M135_target_free_trajectory_aware_repair_trajectory_execution_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M135_target_free_trajectory_aware_repair_trajectory_execution_smoke_v0/`

Claim boundary:

- M135 supports only a one-case executed trajectory-aware repair smoke.
- M135 does not support final real navigation `SR` / `SPL` because the selected repair policy loses `SPL` to detector-confidence / confidence-only baselines.
- M135 does not support final RGB-D/open-vocabulary robustness, deployable search policy, or human intent as a main claim.

## E008-M136

Implementation unit: `E008-M136_target_free_trajectory_aware_repair_result_interpretation_scale_decision_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m136_target_free_trajectory_aware_repair_result_interpretation_scale_decision.py
```

Facts:

- Status: `e008_m136_target_free_trajectory_aware_repair_result_interpretation_scale_decision_ready`.
- M135 scan-policy rows: 5.
- M135 trajectory attempts: 31.
- Selected repair policy: `trajectory_greedy_confidence_path_repair_v0`.
- Selected repair `SPL`: 0.329622.
- Detector-confidence / confidence-only `SPL`: 0.701267.
- Path-family repair diagnostic ready: true.
- Scale current repair ready: false.
- Gate fail count: 6.
- Selected next unit: E008-M137 target-free confidence-preserving trajectory-aware repair contract.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M136_target_free_trajectory_aware_repair_result_interpretation_scale_decision_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M136_target_free_trajectory_aware_repair_result_interpretation_scale_decision_v0/policy_result_interpretation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M136_target_free_trajectory_aware_repair_result_interpretation_scale_decision_v0/pairwise_result_interpretation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M136_target_free_trajectory_aware_repair_result_interpretation_scale_decision_v0/repair_diagnosis_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M136_target_free_trajectory_aware_repair_result_interpretation_scale_decision_v0/gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M136_target_free_trajectory_aware_repair_result_interpretation_scale_decision_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M136_target_free_trajectory_aware_repair_result_interpretation_scale_decision_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M136_target_free_trajectory_aware_repair_result_interpretation_scale_decision_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M136_target_free_trajectory_aware_repair_result_interpretation_scale_decision_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M136_target_free_trajectory_aware_repair_result_interpretation_scale_decision_v0/`

Claim boundary:

- M136 supports an executed repair diagnostic, not a positive navigation-improvement claim.
- Current repair should not be scaled as a main result because it loses `SPL` to detector-confidence / confidence-only baselines.
- M136 selects confidence-preserving trajectory repair before any scale-up.

## E008-M137

Implementation unit: `E008-M137_target_free_confidence_preserving_trajectory_repair_contract_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m137_target_free_confidence_preserving_trajectory_repair_contract.py
```

Facts:

- Status: `e008_m137_target_free_confidence_preserving_trajectory_repair_contract_ready`.
- Base path-ready candidate rows: 15.
- M135 selected repair `SPL`: 0.329622.
- M135 detector-confidence `SPL`: 0.701267.
- Selected policy: `confidence_band_trajectory_tiebreak_v0`.
- Confidence band: 0.03.
- Minimum path advantage inside confidence band: 1.0m.
- Top-band candidate rows: 2.
- Gate fail count: 0.
- M138 materialization ready: true.
- Selected next unit: E008-M138 target-free confidence-preserving trajectory repair materialization smoke.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M137_target_free_confidence_preserving_trajectory_repair_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M137_target_free_confidence_preserving_trajectory_repair_contract_v0/policy_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M137_target_free_confidence_preserving_trajectory_repair_contract_v0/confidence_band_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M137_target_free_confidence_preserving_trajectory_repair_contract_v0/policy_guardrail_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M137_target_free_confidence_preserving_trajectory_repair_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M137_target_free_confidence_preserving_trajectory_repair_contract_v0/m138_materialization_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M137_target_free_confidence_preserving_trajectory_repair_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M137_target_free_confidence_preserving_trajectory_repair_contract_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M137_target_free_confidence_preserving_trajectory_repair_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M137_target_free_confidence_preserving_trajectory_repair_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M137_target_free_confidence_preserving_trajectory_repair_contract_v0/`

Claim boundary:

- M137 supports a confidence-preserving repair contract only.
- M137 does not materialize new visit-order rows or execute trajectories.
- Final real navigation `SR` / `SPL`, final RGB-D/open-vocabulary robustness, deployable search policy, and human intent as a main claim remain unsupported.

## E008-M138

Implementation unit: `E008-M138_target_free_confidence_preserving_repair_materialization_smoke_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m138_target_free_confidence_preserving_repair_materialization.py --m133-root experiments/E008_real_navigation_benchmark/artifacts/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0 --m137-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M137_target_free_confidence_preserving_trajectory_repair_contract_v0 --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M138_target_free_confidence_preserving_repair_materialization_smoke_v0 --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M138_target_free_confidence_preserving_repair_materialization_smoke_v0
```

Facts:

- Status: `e008_m138_target_free_confidence_preserving_repair_materialization_smoke_ready`.
- Base candidate rows: 15.
- Materialized candidate rows: 90.
- Execution plan rows: 6.
- Selected policy: `confidence_band_trajectory_tiebreak_v0`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- Confidence band: 0.03.
- Minimum path advantage inside confidence band: 1.0m.
- Selected policy hard-veto rows: 13.
- Selected policy confidence-band violations: 0.
- Leakage audit pass: true.
- Selected next unit: E008-M139 target-free confidence-preserving repair trajectory execution contract / Docker preflight.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M138_target_free_confidence_preserving_repair_materialization_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M138_target_free_confidence_preserving_repair_materialization_smoke_v0/confidence_preserving_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M138_target_free_confidence_preserving_repair_materialization_smoke_v0/confidence_preserving_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M138_target_free_confidence_preserving_repair_materialization_smoke_v0/policy_order_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M138_target_free_confidence_preserving_repair_materialization_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M138_target_free_confidence_preserving_repair_materialization_smoke_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M138_target_free_confidence_preserving_repair_materialization_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M138_target_free_confidence_preserving_repair_materialization_smoke_v0/`

Claim boundary:

- M138 supports confidence-preserving row materialization only.
- M138 does not execute `Habitat` trajectories or support final real navigation `SR` / `SPL`.
- The high hard-veto count is diagnostic and must be tested by M139 before any navigation-improvement claim.

## E008-M139

Implementation unit: `E008-M139_target_free_confidence_preserving_repair_trajectory_contract_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m139_target_free_confidence_preserving_repair_trajectory_contract.py
```

Facts:

- Status: `e008_m139_target_free_confidence_preserving_repair_trajectory_contract_ready_runner_next`.
- Candidate rows: 90.
- Execution plan rows: 6.
- Eval goal rows: 1.
- Oracle path rows: 1.
- Docker preflight pass: true.
- Runner implemented: true.
- Method policy: `confidence_band_trajectory_tiebreak_v0`.
- Primary baseline: `detector_confidence_reachable_subset_v0`.
- Selected hard-veto rows: 13.
- Confidence-band violations: 0.
- Selected next unit: E008-M140 target-free confidence-preserving repair trajectory execution smoke.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M139_target_free_confidence_preserving_repair_trajectory_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M139_target_free_confidence_preserving_repair_trajectory_contract_v0/trajectory_execution_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M139_target_free_confidence_preserving_repair_trajectory_contract_v0/docker_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M139_target_free_confidence_preserving_repair_trajectory_contract_v0/m140_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M139_target_free_confidence_preserving_repair_trajectory_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M139_target_free_confidence_preserving_repair_trajectory_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M139_target_free_confidence_preserving_repair_trajectory_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M139_target_free_confidence_preserving_repair_trajectory_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M139_target_free_confidence_preserving_repair_trajectory_contract_v0/`

Claim boundary:

- M139 supports the confidence-preserving repair execution contract and Docker/data preflight only.
- M139 does not execute `Habitat` trajectories or support final real navigation `SR` / `SPL`.
- M140 must test whether hard-veto-heavy confidence preservation keeps or improves `SPL` against detector-confidence.

## E008-M140

Implementation unit: `E008-M140_target_free_confidence_preserving_repair_trajectory_execution_smoke_v0`.

Command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp -v /home/yoohyun/research3/local_dataset/data:/data:ro -v /home/yoohyun/research2:/work -w /work research3/habitat-h001:20260508-calib-artifacts bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m140_target_free_confidence_preserving_repair_trajectory_execution_smoke.py --m139-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M139_target_free_confidence_preserving_repair_trajectory_contract_v0 --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M140_target_free_confidence_preserving_repair_trajectory_execution_smoke_v0 --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M140_target_free_confidence_preserving_repair_trajectory_execution_smoke_v0"
```

Facts:

- Status: `e008_m140_target_free_confidence_preserving_repair_trajectory_execution_smoke_ready`.
- Inside Docker: true.
- Trajectory candidate rows: 90.
- Trajectory execution plan rows: 6.
- Trajectory attempt rows: 25.
- Scan-policy metric rows: 6.
- Leakage audit pass: true.
- Selected policy `SR`: 1.0.
- Selected policy `SPL`: 0.701267.
- Detector-confidence baseline `SPL`: 0.701267.
- Selected policy candidate visits: 2.
- Detector-confidence candidate visits: 3.
- Negative prior repair `SPL`: 0.329622.
- Path-cost-only baseline `SPL`: 0.092750.
- Selected next unit: E008-M141 target-free confidence-preserving repair trajectory result interpretation / scale decision.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M140_target_free_confidence_preserving_repair_trajectory_execution_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M140_target_free_confidence_preserving_repair_trajectory_execution_smoke_v0/dynamic_stale_trajectory_attempt_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M140_target_free_confidence_preserving_repair_trajectory_execution_smoke_v0/dynamic_stale_trajectory_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M140_target_free_confidence_preserving_repair_trajectory_execution_smoke_v0/pairwise_policy_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M140_target_free_confidence_preserving_repair_trajectory_execution_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M140_target_free_confidence_preserving_repair_trajectory_execution_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M140_target_free_confidence_preserving_repair_trajectory_execution_smoke_v0/`

Claim boundary:

- M140 supports a one-case executed confidence-preserving repair smoke.
- M140 shows selected policy ties detector-confidence `SPL` and reduces candidate visits on this case.
- M140 does not support final real navigation `SR` / `SPL`, deployable search policy, final RGB-D/open-vocabulary robustness, or human intent as a main claim.
- M141 must decide whether this is scale-up-worthy or only a bounded diagnostic repair.

## E008-M141

Implementation unit: `E008-M141_target_free_confidence_preserving_repair_result_interpretation_scale_decision_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m141_target_free_confidence_preserving_repair_result_interpretation_scale_decision.py
```

Facts:

- Status: `e008_m141_target_free_confidence_preserving_repair_result_interpretation_scale_decision_ready`.
- Controlled scale-up ready: true.
- Selected policy: `confidence_band_trajectory_tiebreak_v0`.
- Selected policy `SR` / `SPL`: 1.0 / 0.701267.
- Detector-confidence `SR` / `SPL`: 1.0 / 0.701267.
- Candidate visits delta vs detector-confidence: -1.0.
- Prior repair `SPL`: 0.329622.
- Path-cost baseline `SPL`: 0.092750.
- Final real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M142 target-free confidence-preserving controlled scale-up contract.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M141_target_free_confidence_preserving_repair_result_interpretation_scale_decision_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M141_target_free_confidence_preserving_repair_result_interpretation_scale_decision_v0/policy_result_interpretation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M141_target_free_confidence_preserving_repair_result_interpretation_scale_decision_v0/pairwise_result_interpretation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M141_target_free_confidence_preserving_repair_result_interpretation_scale_decision_v0/principle_trace_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M141_target_free_confidence_preserving_repair_result_interpretation_scale_decision_v0/gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M141_target_free_confidence_preserving_repair_result_interpretation_scale_decision_v0/scale_up_seed_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M141_target_free_confidence_preserving_repair_result_interpretation_scale_decision_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M141_target_free_confidence_preserving_repair_result_interpretation_scale_decision_v0/`

Claim boundary:

- M141 supports controlled scale-up contract design, not final real navigation claims.
- M141 records the novelty trace: motivation -> protected detector-confidence baseline -> M130/M135 failure diagnosis -> confidence-preserving method form -> M140 one-case evidence -> disconfirmation rule.
- M142 must freeze the selected policy and predefine pass/warning/fail gates before any broader run.

## E008-M142

Implementation unit: `E008-M142_target_free_confidence_preserving_controlled_scaleup_contract_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m142_target_free_confidence_preserving_controlled_scaleup_contract.py
```

Facts:

- Status: `e008_m142_target_free_confidence_preserving_controlled_scaleup_contract_ready`.
- Selected policy: `confidence_band_trajectory_tiebreak_v0`.
- First scale denominator: `full_val_mini_source_ready_confidence_preserving_scale`.
- Scale episode rows: 30.
- Path-ready candidate rows: 900.
- Expected policy candidate rows upper bound: 5,400.
- Expected trajectory cost matrix rows upper bound: 33,354.
- Expected execution plan rows: 180.
- Launch long job now: false.
- Final real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M143 full-val-mini confidence-preserving trajectory-cost materialization.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M142_target_free_confidence_preserving_controlled_scaleup_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M142_target_free_confidence_preserving_controlled_scaleup_contract_v0/denominator_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M142_target_free_confidence_preserving_controlled_scaleup_contract_v0/policy_freeze_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M142_target_free_confidence_preserving_controlled_scaleup_contract_v0/input_guard_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M142_target_free_confidence_preserving_controlled_scaleup_contract_v0/pass_warning_fail_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M142_target_free_confidence_preserving_controlled_scaleup_contract_v0/m143_materialization_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M142_target_free_confidence_preserving_controlled_scaleup_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M142_target_free_confidence_preserving_controlled_scaleup_contract_v0/`

Claim boundary:

- M142 supports only controlled scale-up contract design.
- M142 freezes the policy suite and pass/warning/fail gates before any broader materialization or execution, so the next scale run is not fitted after seeing results.

## E008-M143

Implementation unit: `E008-M143_full_val_mini_confidence_preserving_trajectory_cost_materialization_v0`.

Command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp -v /home/yoohyun/research3/local_dataset/data:/data:ro -v /home/yoohyun/research2:/work -w /work research3/habitat-h001:20260508-calib-artifacts bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m143_full_val_mini_confidence_preserving_trajectory_cost_materialization.py"
```

Facts:

- Status: `e008_m143_full_val_mini_confidence_preserving_trajectory_cost_materialization_ready`.
- Base path-ready candidate rows: 900.
- Episode rows: 30.
- Trajectory cost matrix rows: 33,354 / expected 33,354.
- Candidate-policy rows: 5,400.
- Execution plan rows: 180.
- Selected policy: `confidence_band_trajectory_tiebreak_v0`.
- Selected policy hard-veto rows: 19.
- Selected policy confidence-band violations: 0.
- Leakage audit pass: true.
- Selected next unit: E008-M144 full-val-mini confidence-preserving trajectory execution contract / Docker preflight.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M143_full_val_mini_confidence_preserving_trajectory_cost_materialization_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M143_full_val_mini_confidence_preserving_trajectory_cost_materialization_v0/trajectory_cost_matrix_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M143_full_val_mini_confidence_preserving_trajectory_cost_materialization_v0/confidence_preserving_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M143_full_val_mini_confidence_preserving_trajectory_cost_materialization_v0/trajectory_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M143_full_val_mini_confidence_preserving_trajectory_cost_materialization_v0/policy_order_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M143_full_val_mini_confidence_preserving_trajectory_cost_materialization_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M143_full_val_mini_confidence_preserving_trajectory_cost_materialization_v0/`

Claim boundary:

- M143 supports full-val-mini trajectory-cost and runner-input materialization only.
- M143 does not execute trajectories, compute `SR` / `SPL`, or support final navigation claims.
- M143 keeps the scale-up principle-driven: detector confidence remains protected, and trajectory cost is limited to confidence-band tie-break / hard feasibility veto behavior fixed before execution.

## E008-M144

Implementation unit: `E008-M144_full_val_mini_confidence_preserving_trajectory_contract_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m144_full_val_mini_confidence_preserving_trajectory_contract.py
```

Facts:

- Status: `e008_m144_full_val_mini_confidence_preserving_trajectory_contract_ready_runner_next`.
- Base path-ready candidate rows: 900.
- Trajectory candidate rows: 5,400.
- Execution plan rows: 180.
- Eval goal rows: 30.
- Oracle path rows: 30.
- Docker/data/runner preflight pass: true.
- Runner implemented / `py_compile` pass: true / true.
- Selected policy hard-veto rows: 19.
- Selected policy confidence-band violations: 0.
- Selected next unit: E008-M145 full-val-mini confidence-preserving trajectory execution.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M144_full_val_mini_confidence_preserving_trajectory_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M144_full_val_mini_confidence_preserving_trajectory_contract_v0/trajectory_execution_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M144_full_val_mini_confidence_preserving_trajectory_contract_v0/docker_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M144_full_val_mini_confidence_preserving_trajectory_contract_v0/m145_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M144_full_val_mini_confidence_preserving_trajectory_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M144_full_val_mini_confidence_preserving_trajectory_contract_v0/`

Claim boundary:

- M144 supports trajectory execution contract and Docker preflight only.
- M144 does not execute trajectories, compute full-val-mini `SR` / `SPL`, or support final navigation claims.
- M145 must execute the frozen 180-plan full-val-mini policy suite before M146 can interpret scale evidence.

## E008-M145

Implementation unit: `E008-M145_full_val_mini_confidence_preserving_trajectory_execution_v0`.

Command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp -v /home/yoohyun/research3/local_dataset/data:/data:ro -v /home/yoohyun/research2:/work -w /work research3/habitat-h001:20260508-calib-artifacts bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m145_full_val_mini_confidence_preserving_trajectory_execution.py --m144-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M144_full_val_mini_confidence_preserving_trajectory_contract_v0 --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M145_full_val_mini_confidence_preserving_trajectory_execution_v0 --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M145_full_val_mini_confidence_preserving_trajectory_execution_v0"
```

Launch log:

- `logs/20260611_034154_e008_m145_full_val_mini.log`

Facts:

- Status: `e008_m145_full_val_mini_confidence_preserving_trajectory_execution_ready`.
- Inside Docker: true.
- Trajectory candidate rows: 5,400.
- Execution plan rows: 180.
- Scan-policy metric rows: 180.
- Trajectory attempt rows: 2,202.
- Aggregate success rows / failure rows: 144 / 36.
- Aggregate `SR`: 0.800000.
- Aggregate mean `SPL`: 0.214639.
- Leakage audit pass: true.
- Selected policy `confidence_band_trajectory_tiebreak_v0`: `SR` 0.800000, `SPL` 0.227289, `CandidateVisits_mean` 11.900000.
- Protected detector-confidence baseline: `SR` 0.800000, `SPL` 0.231845, `CandidateVisits_mean` 11.200000.
- Best observed policy by `SPL`: `trajectory_greedy_confidence_path_repair_v0`, `SR` 0.800000, `SPL` 0.236760.
- Selected next unit: E008-M146 full-val-mini confidence-preserving trajectory result interpretation / scale decision.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M145_full_val_mini_confidence_preserving_trajectory_execution_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M145_full_val_mini_confidence_preserving_trajectory_execution_v0/dynamic_stale_trajectory_attempt_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M145_full_val_mini_confidence_preserving_trajectory_execution_v0/dynamic_stale_trajectory_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M145_full_val_mini_confidence_preserving_trajectory_execution_v0/pairwise_policy_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M145_full_val_mini_confidence_preserving_trajectory_execution_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M145_full_val_mini_confidence_preserving_trajectory_execution_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M145_full_val_mini_confidence_preserving_trajectory_execution_v0/`

Claim boundary:

- M145 supports full-val-mini execution evidence, not final real navigation claims.
- M145 does not by itself support `confidence_band_trajectory_tiebreak_v0` as a positive navigation-improvement claim because its `SPL` is below the protected detector-confidence baseline on this 30-episode execution.
- M146 interpreted pass/warning/fail gates and rejected selected-policy scale-up before M147 failure decomposition.

## E008-M146

Implementation unit: `E008-M146_full_val_mini_confidence_preserving_trajectory_result_interpretation_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m146_full_val_mini_confidence_preserving_trajectory_result_interpretation.py
```

Facts:

- Status: `e008_m146_full_val_mini_confidence_preserving_trajectory_result_interpretation_ready`.
- Selected policy: `confidence_band_trajectory_tiebreak_v0`.
- Selected policy `SR` / `SPL`: 0.800000 / 0.227289.
- Detector-confidence `SR` / `SPL`: 0.800000 / 0.231845.
- Selected policy delta `SPL` vs detector-confidence: -0.004556.
- Selected policy delta candidate visits vs detector-confidence: +0.700000.
- Best `SPL` policy: `trajectory_greedy_confidence_path_repair_v0`, `SPL` 0.236760.
- Gate counts: pass 6, warning 1, fail 5.
- Positive navigation-improvement ready: false.
- Diagnostic table ready: true.
- Selected next unit: E008-M147 full-val-mini policy-family failure decomposition / redesign contract.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M146_full_val_mini_confidence_preserving_trajectory_result_interpretation_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M146_full_val_mini_confidence_preserving_trajectory_result_interpretation_v0/policy_result_interpretation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M146_full_val_mini_confidence_preserving_trajectory_result_interpretation_v0/pairwise_delta_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M146_full_val_mini_confidence_preserving_trajectory_result_interpretation_v0/episode_delta_profile_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M146_full_val_mini_confidence_preserving_trajectory_result_interpretation_v0/gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M146_full_val_mini_confidence_preserving_trajectory_result_interpretation_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M146_full_val_mini_confidence_preserving_trajectory_result_interpretation_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M146_full_val_mini_confidence_preserving_trajectory_result_interpretation_v0/`

Claim boundary:

- M146 rejects a positive navigation-improvement claim for the selected confidence-band policy.
- M145 remains a full-val-mini diagnostic execution table.
- M147 must diagnose why confidence-band loses `SPL`, why prior repair wins `SPL`, and which precommitted policy family is defensible before any further scale-up.

## E008-M147

Implementation unit: `E008-M147_full_val_mini_policy_family_failure_decomposition_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m147_full_val_mini_policy_family_failure_decomposition.py
```

Facts:

- Status: `e008_m147_full_val_mini_policy_family_failure_decomposition_ready`.
- Case delta rows: 30.
- Policy family rows: 4.
- Failure diagnosis rows: 4.
- Redesign contract rows: 4.
- Selected policy remains not positive: `confidence_band_trajectory_tiebreak_v0` `SPL` 0.227289 vs detector-confidence `SPL` 0.231845, delta visits +0.700000.
- Best observed policy remains diagnostic only: `trajectory_greedy_confidence_path_repair_v0` `SPL` 0.236760, delta visits +1.066667.
- Case profiles vs detector-confidence: clean `SPL` gain 4, `SPL` gain with visit cost 7, neutral/tie 15, `SPL` loss with more visits 4.
- Selected redesign family: `budget_guarded_confidence_path_repair_v1`.
- Selected next unit: E008-M148 full-val-mini budget-guarded confidence/path redesign contract.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M147_full_val_mini_policy_family_failure_decomposition_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M147_full_val_mini_policy_family_failure_decomposition_v0/policy_family_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M147_full_val_mini_policy_family_failure_decomposition_v0/case_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M147_full_val_mini_policy_family_failure_decomposition_v0/profile_decomposition_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M147_full_val_mini_policy_family_failure_decomposition_v0/failure_diagnosis_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M147_full_val_mini_policy_family_failure_decomposition_v0/redesign_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M147_full_val_mini_policy_family_failure_decomposition_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M147_full_val_mini_policy_family_failure_decomposition_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M147_full_val_mini_policy_family_failure_decomposition_v0/`

Claim boundary:

- M147 does not claim real navigation improvement.
- M147 explains why the current selected policy is not paper-facing as a positive method.
- M148 must freeze a budget-guarded confidence/path policy before any new execution.
- External navigation/search baselines remain required after the internal policy form is stable.

## E008-M148

Implementation unit: `E008-M148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m148_full_val_mini_budget_guarded_confidence_path_redesign_contract.py
```

Facts:

- Status: `e008_m148_full_val_mini_budget_guarded_confidence_path_redesign_contract_ready`.
- Selected policy: `budget_guarded_confidence_path_repair_v1`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- M143 candidate rows: 5,400.
- M143 policy counts: 6 policies x 900 rows.
- Policy contract rows: 5.
- Trigger contract rows: 4.
- Allowed input rows: 14.
- Blocked input rows: 12.
- Budget guard rows: 4.
- Confidence band: 0.03.
- Max rank displacement: 1.
- Positive navigation-improvement ready: false.
- Selected next unit: E008-M149 full-val-mini budget-guarded confidence/path row materialization smoke.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0/policy_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0/trigger_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0/allowed_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0/blocked_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0/budget_guard_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0/m149_materialization_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0/`

Claim boundary:

- M148 does not claim real navigation improvement.
- M148 prevents posthoc policy selection by freezing the selected policy and ablations before M149.
- M149 must materialize rows and audit leakage/budget guards before any Docker trajectory execution.

## E008-M149

Implementation unit: `E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m149_full_val_mini_budget_guarded_confidence_path_materialization.py \
  --m143-root experiments/E008_real_navigation_benchmark/artifacts/E008-M143_full_val_mini_confidence_preserving_trajectory_cost_materialization_v0 \
  --m148-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0 \
  --out-root /home/yoohyun/research2/experiments/E008_real_navigation_benchmark/artifacts/E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0 \
  --derived-out-root /home/yoohyun/research2/local_dataset/HM3D_navigation_bridge/E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0
```

Facts:

- Status: `e008_m149_full_val_mini_budget_guarded_confidence_path_materialization_ready`.
- Episode rows: 30.
- Base path-ready candidate rows: 900.
- Budget-guarded candidate rows: 5,400.
- Execution plan rows: 180.
- Selected policy: `budget_guarded_confidence_path_repair_v1`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- Candidate rows by policy: 900 each for selected policy, protected baseline, `budget_guarded_confidence_only_v1`, `budget_guarded_no_visit_guard_v1`, `budget_guarded_no_confidence_floor_v1`, and `budget_guarded_source_gap_only_v1`.
- Selected policy path-repair trigger rows: 394.
- Selected policy hard-feasibility veto rows: 6.
- Selected policy max rank displacement: 1.
- Selected policy confidence-band violations: 0.
- Selected policy rank-displacement violations: 0.
- Leakage audit pass: true.
- Budget guard audit pass: true.
- Policy order audit pass: true.
- Runner aliases ready: `dynamic_stale_overlay_trajectory_candidate_rows.jsonl`, `trajectory_execution_plan_rows.jsonl`.
- Selected next unit: E008-M150 full-val-mini budget-guarded confidence/path trajectory execution contract / Docker preflight.

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0/budget_guarded_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0/budget_guarded_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0/trajectory_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0/policy_order_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0/budget_guard_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0/`

Claim boundary:

- M149 does not claim real navigation improvement.
- M149 shows only that the budget-guarded policy family is materialized on the fixed denominator with leakage/budget/order audits passing.
- M150 must create the Docker execution contract before any trajectory rerun.

## E008-M150

Implementation unit: `E008-M150_full_val_mini_budget_guarded_confidence_path_trajectory_contract_v0`.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m150_full_val_mini_budget_guarded_confidence_path_trajectory_contract.py
```

Facts:

- Status: `e008_m150_full_val_mini_budget_guarded_confidence_path_trajectory_contract_ready_runner_next`.
- Base candidate rows: 900.
- Trajectory candidate rows: 5,400.
- Trajectory execution plan rows: 180.
- Eval goal rows: 30.
- Oracle path rows: 30.
- Policy count: 6.
- Selected policy: `budget_guarded_confidence_path_repair_v1`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- Selected policy path-repair trigger rows: 394.
- Selected policy hard-feasibility veto rows: 6.
- Selected policy max rank displacement: 1.
- Docker preflight pass: true.
- `docker --version`: pass.
- `research3/habitat-h001:20260508-calib-artifacts` image inspect: pass.
- `nvidia-smi`: pass, free memory tail `22124`.
- Read-only `HM3D` data root: pass.
- Scene files: 2 / 2 ready.
- Navmesh files: 2 / 2 ready.
- `ObjectNav val_mini` content files: 2.
- M37 runner compile: pass.
- M151 runner compile: pass.
- Selected next unit: E008-M151 full-val-mini budget-guarded confidence/path trajectory execution.

M151 command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp \
  -v /home/yoohyun/research3/local_dataset/data:/data:ro \
  -v /home/yoohyun/research2:/work -w /work \
  research3/habitat-h001:20260508-calib-artifacts bash -lc \
  "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m151_full_val_mini_budget_guarded_confidence_path_execution.py \
  --m150-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M150_full_val_mini_budget_guarded_confidence_path_trajectory_contract_v0 \
  --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0 \
  --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0"
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M150_full_val_mini_budget_guarded_confidence_path_trajectory_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M150_full_val_mini_budget_guarded_confidence_path_trajectory_contract_v0/trajectory_execution_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M150_full_val_mini_budget_guarded_confidence_path_trajectory_contract_v0/docker_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M150_full_val_mini_budget_guarded_confidence_path_trajectory_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M150_full_val_mini_budget_guarded_confidence_path_trajectory_contract_v0/m151_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M150_full_val_mini_budget_guarded_confidence_path_trajectory_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M150_full_val_mini_budget_guarded_confidence_path_trajectory_contract_v0/`

Claim boundary:

- M150 does not claim real navigation improvement.
- M150 is a Docker/data/runner preflight and command-ledger unit only.
- M151 must execute trajectories before `SR` / `SPL` can be interpreted.

## E008-M151

Implementation unit: `E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0`.

- Status: `e008_m151_full_val_mini_budget_guarded_confidence_path_execution_ready`.
- Launch session: `e008_m151_20260611_110132` completed.
- Log: `logs/20260611_110132_e008_m151_full_val_mini_budget_guarded_confidence_path.log`.
- Inside Docker: true.
- Trajectory candidate rows: 5,400.
- Trajectory execution plan rows: 180.
- Scan-task-policy rows: 180.
- Trajectory attempt rows: 2,185.
- Trajectory success/failure rows: 144 / 36.
- Aggregate `SR`: 0.800000.
- Aggregate mean `SPL`: 0.215140.
- Pairwise policy delta rows: 150.
- Leakage audit pass: true.
- Selected next unit: E008-M152 full-val-mini budget-guarded confidence/path trajectory result interpretation / scale decision.

Command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp \
  -v /home/yoohyun/research3/local_dataset/data:/data:ro \
  -v /home/yoohyun/research2:/work \
  -w /work \
  research3/habitat-h001:20260508-calib-artifacts \
  bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m151_full_val_mini_budget_guarded_confidence_path_execution.py \
  --m150-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M150_full_val_mini_budget_guarded_confidence_path_trajectory_contract_v0 \
  --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0 \
  --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0"
```

Verification:

```bash
python - <<'PY'
import json
from pathlib import Path
p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0/coverage.json')
c=json.loads(p.read_text())
assert c['status']=='e008_m151_full_val_mini_budget_guarded_confidence_path_execution_ready'
assert c['scan_task_policy_rows'] == 180
print('m151 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0/dynamic_stale_trajectory_attempt_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0/dynamic_stale_trajectory_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0/pairwise_policy_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0/`

Claim boundary:

- M151 is a raw full-val-mini trajectory execution result, not final interpretation.
- Positive navigation-improvement remains blocked because M152 rejects `budget_guarded_confidence_path_repair_v1` against protected `detector_confidence_reachable_subset_v0` and ablations.
- Final real navigation `SR` / `SPL`, deployable policy, final RGB-D/open-vocabulary robustness, and human intent as a main claim remain blocked.

## E008-M152

Implementation unit: `E008-M152_full_val_mini_budget_guarded_confidence_path_result_interpretation_v0`.

- Status: `e008_m152_full_val_mini_budget_guarded_confidence_path_result_interpretation_ready`.
- Selected policy: `budget_guarded_confidence_path_repair_v1`.
- Selected policy `SR` / `SPL`: 0.800000 / 0.230290.
- Detector-confidence `SR` / `SPL`: 0.800000 / 0.231845.
- Selected policy delta `SPL` vs detector-confidence: -0.001555.
- Selected policy delta candidate visits vs detector-confidence: +0.133333.
- Selected policy delta path length vs detector-confidence: -8.239214 m.
- Best `SPL` policy: `budget_guarded_no_visit_guard_v1`, `SPL` 0.236760.
- Gate pass/warning/fail: 6 / 3 / 6.
- Positive navigation-improvement ready: false.
- Diagnostic table ready: true.
- Selected next unit: E008-M153 full-val-mini budget/SPL Pareto failure decomposition / next-route decision.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m152_full_val_mini_budget_guarded_confidence_path_result_interpretation.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M152_full_val_mini_budget_guarded_confidence_path_result_interpretation_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M152_full_val_mini_budget_guarded_confidence_path_result_interpretation_v0/policy_result_interpretation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M152_full_val_mini_budget_guarded_confidence_path_result_interpretation_v0/pairwise_delta_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M152_full_val_mini_budget_guarded_confidence_path_result_interpretation_v0/episode_delta_profile_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M152_full_val_mini_budget_guarded_confidence_path_result_interpretation_v0/gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M152_full_val_mini_budget_guarded_confidence_path_result_interpretation_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M152_full_val_mini_budget_guarded_confidence_path_result_interpretation_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M152_full_val_mini_budget_guarded_confidence_path_result_interpretation_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M152_full_val_mini_budget_guarded_confidence_path_result_interpretation_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M152_full_val_mini_budget_guarded_confidence_path_result_interpretation_v0/`

Claim boundary:

- M152 rejects a positive navigation-improvement claim for the selected budget-guarded policy.
- M151 remains a full-val-mini diagnostic execution table.
- Confidence floor remains necessary because the no-confidence-floor ablation is much worse.
- The current path repair form is not supported as a positive method because it reduces path length but loses `SPL` and visit efficiency against detector-confidence.
- M153 decomposed the budget/SPL Pareto failure before any new scale-up or external-baseline push.

## E008-M153

Implementation unit: `E008-M153_full_val_mini_budget_spl_pareto_failure_decomposition_v0`.

- Status: `e008_m153_full_val_mini_budget_spl_pareto_failure_decomposition_ready`.
- Scan-task-policy rows: 180.
- Selected policy: `budget_guarded_confidence_path_repair_v1`.
- Selected primary dominated by: `budget_guarded_confidence_only_v1`, `budget_guarded_source_gap_only_v1`, `detector_confidence_reachable_subset_v0`.
- Selected expanded path-length Pareto member: true.
- Best `SPL` ablation: `budget_guarded_no_visit_guard_v1`, `SPL` 0.236760, `CandidateVisits` 12.266667.
- No-confidence-floor ablation: `SPL` 0.128254, `CandidateVisits` 15.633333.
- Positive navigation-improvement ready: false.
- Final real navigation claim ready: false.
- Selected next unit: E008-M154 budget-aware utility objective contract / policy-selection rule.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m153_full_val_mini_budget_spl_pareto_failure_decomposition.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M153_full_val_mini_budget_spl_pareto_failure_decomposition_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M153_full_val_mini_budget_spl_pareto_failure_decomposition_v0/pareto_policy_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M153_full_val_mini_budget_spl_pareto_failure_decomposition_v0/episode_tradeoff_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M153_full_val_mini_budget_spl_pareto_failure_decomposition_v0/pareto_case_profile_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M153_full_val_mini_budget_spl_pareto_failure_decomposition_v0/failure_diagnosis_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M153_full_val_mini_budget_spl_pareto_failure_decomposition_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M153_full_val_mini_budget_spl_pareto_failure_decomposition_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M153_full_val_mini_budget_spl_pareto_failure_decomposition_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M153_full_val_mini_budget_spl_pareto_failure_decomposition_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M153_full_val_mini_budget_spl_pareto_failure_decomposition_v0/`

Claim boundary:

- M153 supports a diagnostic statement about the budget/SPL Pareto failure.
- M153 does not support a positive selected-policy navigation claim because the selected policy is dominated in primary `SR`/`SPL`/candidate-visit space.
- `budget_guarded_no_visit_guard_v1` is a tradeoff witness, not a selected method, because it is posthoc and visit-expensive.
- Confidence floor remains supported as necessary by the no-confidence-floor negative control.
- M154 precommitted a budget-aware utility objective before any new scale-up, heldout transfer, or external navigation/search baseline run.

## E008-M154

Implementation unit: `E008-M154_budget_aware_utility_objective_contract_v0`.

- Status: `e008_m154_budget_aware_utility_objective_contract_ready`.
- Selected objective: `budget_aware_confidence_path_utility_v0`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- Input contract rows: 20.
- Guard contract rows: 5.
- Utility objective rows: 2.
- Blocked input fields: 7.
- Performance claim ready: false.
- Trajectory execution ready: false.
- Selected next unit: E008-M155 budget-aware utility policy materialization smoke.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m154_budget_aware_utility_objective_contract.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M154_budget_aware_utility_objective_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M154_budget_aware_utility_objective_contract_v0/prior_policy_audit_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M154_budget_aware_utility_objective_contract_v0/utility_objective_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M154_budget_aware_utility_objective_contract_v0/guard_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M154_budget_aware_utility_objective_contract_v0/policy_selection_rule_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M154_budget_aware_utility_objective_contract_v0/input_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M154_budget_aware_utility_objective_contract_v0/ablation_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M154_budget_aware_utility_objective_contract_v0/evaluation_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M154_budget_aware_utility_objective_contract_v0/materialization_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M154_budget_aware_utility_objective_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M154_budget_aware_utility_objective_contract_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M154_budget_aware_utility_objective_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M154_budget_aware_utility_objective_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M154_budget_aware_utility_objective_contract_v0/`

Claim boundary:

- M154 supports method precommitment and reviewer defense only.
- M154 does not support positive navigation performance because no policy rows or trajectories are executed.
- `budget_guarded_no_visit_guard_v1` remains a required ablation / tradeoff witness, not a selected method.
- M155 materialized the utility rows without eval leakage; M156 must fix the Docker trajectory contract before any new execution claim.

## E008-M155

Implementation unit: `E008-M155_budget_aware_utility_policy_materialization_smoke_v0`.

- Status: `e008_m155_budget_aware_utility_policy_materialization_smoke_ready`.
- Source candidate rows: 5,400.
- Materialized candidate rows: 6,300.
- Utility component rows: 3,600.
- Policy plan rows: 210.
- Policy order audit rows: 210.
- Leakage audit rows: 7.
- Selected policy: `budget_aware_confidence_path_utility_v0`.
- Selected changed episode rows: 8.
- Selected utility-promoted rows: 17.
- Materialization ready: true.
- Trajectory execution ready: true.
- Performance claim ready: false.
- Selected next unit: E008-M156 budget-aware utility trajectory execution contract / Docker preflight.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m155_budget_aware_utility_policy_materialization.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M155_budget_aware_utility_policy_materialization_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M155_budget_aware_utility_policy_materialization_smoke_v0/budget_aware_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M155_budget_aware_utility_policy_materialization_smoke_v0/utility_component_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M155_budget_aware_utility_policy_materialization_smoke_v0/policy_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M155_budget_aware_utility_policy_materialization_smoke_v0/policy_order_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M155_budget_aware_utility_policy_materialization_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M155_budget_aware_utility_policy_materialization_smoke_v0/materialization_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M155_budget_aware_utility_policy_materialization_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M155_budget_aware_utility_policy_materialization_smoke_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M155_budget_aware_utility_policy_materialization_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M155_budget_aware_utility_policy_materialization_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M155_budget_aware_utility_policy_materialization_smoke_v0/`

Claim boundary:

- M155 supports row materialization, policy-order audit, leakage audit, and Docker-execution readiness only.
- M155 does not execute `Habitat` trajectories and does not support real navigation `SR` / `SPL` improvement.
- `budget_aware_confidence_path_utility_v0` is now a materialized and executed candidate policy; M158 rejects it as a positive navigation-improvement claim.
- Human intent remains a secondary conditioning / ablation axis; M155 is target-free and does not change the E006-M08 decision.

## E008-M156

Implementation unit: `E008-M156_budget_aware_utility_trajectory_contract_v0`.

- Status: `e008_m156_budget_aware_utility_trajectory_contract_ready_runner_next`.
- Method policy: `budget_aware_confidence_path_utility_v0`.
- Primary baseline: `detector_confidence_reachable_subset_v0`.
- Candidate rows: 6,300.
- Execution plan rows: 210.
- Eval goal rows: 30.
- Oracle path rows: 30.
- Scene count: 2.
- Policy count: 7.
- Selected policy changed episode rows: 8.
- Selected policy utility-promoted rows: 17.
- Docker preflight pass: true.
- `M37` runner compile pass: true.
- `M157` runner compile pass: true.
- Trajectory execution contract ready: true.
- Trajectory execution result ready: false.
- Final real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M157 budget-aware utility trajectory execution.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m156_budget_aware_utility_trajectory_contract.py
```

M157 command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp \
  -v /home/yoohyun/research3/local_dataset/data:/data:ro \
  -v /home/yoohyun/research2:/work -w /work \
  research3/habitat-h001:20260508-calib-artifacts bash -lc \
  "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m157_budget_aware_utility_trajectory_execution.py \
  --m156-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M156_budget_aware_utility_trajectory_contract_v0 \
  --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M157_budget_aware_utility_trajectory_execution_v0 \
  --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M157_budget_aware_utility_trajectory_execution_v0"
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M156_budget_aware_utility_trajectory_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M156_budget_aware_utility_trajectory_contract_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M156_budget_aware_utility_trajectory_contract_v0/trajectory_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M156_budget_aware_utility_trajectory_contract_v0/budget_aware_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M156_budget_aware_utility_trajectory_contract_v0/trajectory_execution_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M156_budget_aware_utility_trajectory_contract_v0/docker_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M156_budget_aware_utility_trajectory_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M156_budget_aware_utility_trajectory_contract_v0/m157_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M156_budget_aware_utility_trajectory_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M156_budget_aware_utility_trajectory_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M156_budget_aware_utility_trajectory_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M156_budget_aware_utility_trajectory_contract_v0/`

Claim boundary:

- M156 supports runner-compatible trajectory input rows, Docker/data preflight, and the M157 command ledger only.
- M156 does not execute `Habitat` trajectories and does not support real navigation `SR` / `SPL` improvement.
- M157 executed the selected method and ablation/reference policies; M158 interprets them against the protected baseline and rejects a positive navigation-improvement claim.
- Human intent remains a secondary conditioning / ablation axis; M156 is target-free and does not change the E006-M08 decision.

## E008-M157

Implementation unit: `E008-M157_budget_aware_utility_trajectory_execution_v0`.

- Status: `e008_m157_budget_aware_utility_trajectory_execution_ready`.
- Inside Docker: true.
- Method policy: `budget_aware_confidence_path_utility_v0`.
- Primary baseline: `detector_confidence_reachable_subset_v0`.
- Trajectory candidate rows: 6,300.
- Trajectory execution plan rows: 210.
- Scan-task-policy metric rows: 210.
- Trajectory attempt rows: 2,523.
- Trajectory success rows: 168.
- Trajectory failure rows: 42.
- Aggregate `SR`: 0.800000.
- Aggregate mean `SPL`: 0.217651.
- Selected method `SR` / `SPL`: 0.800000 / 0.231619.
- Primary detector-confidence baseline `SR` / `SPL`: 0.800000 / 0.231845.
- Leakage audit pass: true.
- Final real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M158 budget-aware utility trajectory result interpretation / protected-baseline gate.

Command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp \
  -v /home/yoohyun/research3/local_dataset/data:/data:ro \
  -v /home/yoohyun/research2:/work -w /work \
  research3/habitat-h001:20260508-calib-artifacts bash -lc \
  "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m157_budget_aware_utility_trajectory_execution.py \
  --m156-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M156_budget_aware_utility_trajectory_contract_v0 \
  --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M157_budget_aware_utility_trajectory_execution_v0 \
  --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M157_budget_aware_utility_trajectory_execution_v0"
```

Verification:

```bash
python - <<'PY'
import json
from pathlib import Path
p = Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M157_budget_aware_utility_trajectory_execution_v0/coverage.json')
c = json.loads(p.read_text())
assert c['status'] == 'e008_m157_budget_aware_utility_trajectory_execution_ready'
assert c['scan_task_policy_rows'] == 210
print('m157 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M157_budget_aware_utility_trajectory_execution_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M157_budget_aware_utility_trajectory_execution_v0/dynamic_stale_trajectory_attempt_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M157_budget_aware_utility_trajectory_execution_v0/dynamic_stale_trajectory_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M157_budget_aware_utility_trajectory_execution_v0/pairwise_policy_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M157_budget_aware_utility_trajectory_execution_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M157_budget_aware_utility_trajectory_execution_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M157_budget_aware_utility_trajectory_execution_v0/`

Claim boundary:

- M157 is an execution result, not final interpretation.
- M158 rejects a positive navigation-improvement claim for this selected method.
- `ObjectNav` goal/viewpoints are used only after stops for metric computation.
- Final `SR` / `SPL`, deployable policy, final RGB-D/open-vocabulary robustness, and human intent as a main claim remain blocked.

## E008-M158

Implementation unit: `E008-M158_budget_aware_utility_trajectory_result_interpretation_v0`.

- Status: `e008_m158_budget_aware_utility_trajectory_result_interpretation_ready`.
- M157 status: `e008_m157_budget_aware_utility_trajectory_execution_ready`.
- Selected policy: `budget_aware_confidence_path_utility_v0`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- Selected policy `SR` / `SPL`: 0.800000 / 0.231619.
- Detector-confidence `SR` / `SPL`: 0.800000 / 0.231845.
- Selected policy delta `SPL` vs detector-confidence: -0.000226.
- Selected policy delta candidate visits vs detector-confidence: +0.066667.
- Selected policy delta path length vs detector-confidence: +0.308625m.
- Best `SPL` policy: `budget_guarded_no_visit_guard_v1`, `SPL` 0.236760.
- Gate pass / warning / fail: 6 / 2 / 8.
- Positive navigation-improvement ready: false.
- Component failure decomposition ready: true.
- Final real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M159 budget-aware utility component failure decomposition / next-route decision.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m158_budget_aware_utility_trajectory_result_interpretation.py
```

Verification:

```bash
python - <<'PY'
import json
from pathlib import Path
p = Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M158_budget_aware_utility_trajectory_result_interpretation_v0/coverage.json')
c = json.loads(p.read_text())
assert c['status'] == 'e008_m158_budget_aware_utility_trajectory_result_interpretation_ready'
assert c['positive_navigation_improvement_ready'] is False
assert c['selected_next_unit'] == 'E008-M159 budget-aware utility component failure decomposition / next-route decision'
print('m158 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M158_budget_aware_utility_trajectory_result_interpretation_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M158_budget_aware_utility_trajectory_result_interpretation_v0/policy_result_interpretation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M158_budget_aware_utility_trajectory_result_interpretation_v0/pairwise_delta_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M158_budget_aware_utility_trajectory_result_interpretation_v0/episode_delta_profile_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M158_budget_aware_utility_trajectory_result_interpretation_v0/gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M158_budget_aware_utility_trajectory_result_interpretation_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M158_budget_aware_utility_trajectory_result_interpretation_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M158_budget_aware_utility_trajectory_result_interpretation_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M158_budget_aware_utility_trajectory_result_interpretation_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M158_budget_aware_utility_trajectory_result_interpretation_v0/`

Claim boundary:

- M158 rejects selected utility positive navigation improvement.
- The selected utility ties detector-confidence on `SR` but loses mean `SPL`, path length, and candidate visits.
- `budget_aware_utility_without_path_gain_v0` matches detector-confidence and is better than the selected utility on aggregate, so current path gain is not supported.
- Source-gap bonus and visit-penalty terms are inert on this denominator.
- Confidence floor remains necessary because `budget_guarded_no_confidence_floor_v1` is strongly worse.
- `budget_guarded_no_visit_guard_v1` has the best `SPL` but is visit-budget expensive, so it is a tradeoff witness, not a posthoc selected method.
- Final `SR` / `SPL`, deployable policy, final RGB-D/open-vocabulary robustness, and human intent as a main claim remain blocked.

## E008-M159

Implementation unit: `E008-M159_budget_aware_utility_component_failure_decomposition_v0`.

- Status: `e008_m159_budget_aware_utility_component_failure_decomposition_ready`.
- M155 status: `e008_m155_budget_aware_utility_policy_materialization_smoke_ready`.
- M157 status: `e008_m157_budget_aware_utility_trajectory_execution_ready`.
- M158 status: `e008_m158_budget_aware_utility_trajectory_result_interpretation_ready`.
- Component failure rows: 6.
- Supported component: `confidence_floor_guard`.
- Rejected / inert components: `scalar_path_gain`, `source_gap_bonus`, `visit_penalty_scalar`.
- Tradeoff witness: `visit_guard`.
- Positive navigation-improvement ready: false.
- Component repair contract required: true.
- Final real navigation `SR` / `SPL` ready: false.
- Selected next unit: E008-M160 confidence-first constrained utility repair contract / metric target decision.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m159_budget_aware_utility_component_failure_decomposition.py
```

Verification:

```bash
python - <<'PY'
import json
from pathlib import Path
p = Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M159_budget_aware_utility_component_failure_decomposition_v0/coverage.json')
c = json.loads(p.read_text())
assert c['status'] == 'e008_m159_budget_aware_utility_component_failure_decomposition_ready'
assert c['positive_navigation_improvement_ready'] is False
assert c['selected_next_unit'] == 'E008-M160 confidence-first constrained utility repair contract / metric target decision'
print('m159 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M159_budget_aware_utility_component_failure_decomposition_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M159_budget_aware_utility_component_failure_decomposition_v0/component_failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M159_budget_aware_utility_component_failure_decomposition_v0/failure_mechanism_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M159_budget_aware_utility_component_failure_decomposition_v0/principle_revision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M159_budget_aware_utility_component_failure_decomposition_v0/m160_contract_seed_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M159_budget_aware_utility_component_failure_decomposition_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M159_budget_aware_utility_component_failure_decomposition_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M159_budget_aware_utility_component_failure_decomposition_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M159_budget_aware_utility_component_failure_decomposition_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M159_budget_aware_utility_component_failure_decomposition_v0/`

Claim boundary:

- M159 supports component-level failure diagnosis only.
- M159 does not support a positive selected utility navigation claim.
- The supported component is the confidence floor; current scalar path gain is harmful, source-gap bonus and visit penalty are inert on this denominator, and no-visit-guard is a tradeoff witness rather than a selected method.
- E008-M160 must precommit a confidence-first constrained repair contract before any new execution.
- Final `SR` / `SPL`, deployable policy, final RGB-D/open-vocabulary robustness, and human intent as a main claim remain blocked.

## E008-M160

Implementation unit: `E008-M160_confidence_first_constrained_utility_repair_contract_v0`.

- Status: `e008_m160_confidence_first_constrained_utility_repair_contract_ready`.
- M159 status: `e008_m159_budget_aware_utility_component_failure_decomposition_ready`.
- Selected policy contract: `confidence_first_path_veto_tiebreak_repair_v1`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- Primary metric target: `protected_spl_no_extra_visits_v0`.
- Method contract rows: 4.
- Repair rule rows: 6.
- Metric target rows: 4.
- Allowed / blocked input rows: 8 / 9.
- Ablation contract rows: 4.
- Row materialization ready: true.
- Trajectory execution ready: false.
- Positive navigation-improvement ready: false.
- Selected next unit: E008-M161 confidence-first constrained repair row materialization smoke.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m160_confidence_first_constrained_utility_repair_contract.py
```

Verification:

```bash
python - <<'PY'
import json
from pathlib import Path
p = Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M160_confidence_first_constrained_utility_repair_contract_v0/coverage.json')
c = json.loads(p.read_text())
assert c['status'] == 'e008_m160_confidence_first_constrained_utility_repair_contract_ready'
assert c['selected_next_unit'] == 'E008-M161 confidence-first constrained repair row materialization smoke'
assert c['positive_navigation_improvement_ready'] is False
print('m160 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M160_confidence_first_constrained_utility_repair_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M160_confidence_first_constrained_utility_repair_contract_v0/method_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M160_confidence_first_constrained_utility_repair_contract_v0/repair_rule_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M160_confidence_first_constrained_utility_repair_contract_v0/metric_target_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M160_confidence_first_constrained_utility_repair_contract_v0/allowed_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M160_confidence_first_constrained_utility_repair_contract_v0/blocked_input_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M160_confidence_first_constrained_utility_repair_contract_v0/ablation_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M160_confidence_first_constrained_utility_repair_contract_v0/materialization_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M160_confidence_first_constrained_utility_repair_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M160_confidence_first_constrained_utility_repair_contract_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M160_confidence_first_constrained_utility_repair_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M160_confidence_first_constrained_utility_repair_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M160_confidence_first_constrained_utility_repair_contract_v0/`

Claim boundary:

- M160 is a contract-only unit.
- M160 does not materialize repaired candidate rows or execute `Habitat` trajectories.
- The selected repair must start from detector-confidence order, keep a confidence floor, use path cost only as hard feasibility veto / confidence-band tie-break / bounded local repair, and keep source-gap as a trigger only.
- Positive navigation-improvement requires later M161 materialization, execution, `delta_SR >= 0`, `delta_SPL > 0`, and `delta_CandidateVisits <= 0` against `detector_confidence_reachable_subset_v0`.
- Final `SR` / `SPL`, deployable policy, final RGB-D/open-vocabulary robustness, and human intent as a main claim remain blocked.

## E008-M161

Implementation unit: `E008-M161_confidence_first_constrained_repair_materialization_smoke_v0`.

- Status: `e008_m161_confidence_first_constrained_repair_materialization_smoke_ready`.
- M155 status: `e008_m155_budget_aware_utility_policy_materialization_smoke_ready`.
- M156 status: `e008_m156_budget_aware_utility_trajectory_contract_ready_runner_next`.
- M160 status: `e008_m160_confidence_first_constrained_utility_repair_contract_ready`.
- Selected policy: `confidence_first_path_veto_tiebreak_repair_v1`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- Primary metric target: `protected_spl_no_extra_visits_v0`.
- Source candidate rows: 6,300.
- Base detector candidate rows: 900.
- Materialized candidate rows: 5,400.
- Candidate rows by policy: 900 each for selected, protected baseline, `confidence_first_no_path_tiebreak_v1`, `source_gap_trigger_only_v1`, `budget_guarded_no_confidence_floor_v1`, and `budget_guarded_no_visit_guard_v1`.
- Repair component rows: 765.
- Selected changed episode rows: 24 / 30.
- Selected local-swap promoted rows: 106.
- Max selected rank displacement: 1.
- Leakage/order audits: pass.
- Positive navigation-improvement ready: false.
- Selected next unit: E008-M162 confidence-first constrained repair trajectory execution contract / Docker preflight.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m161_confidence_first_constrained_repair_materialization.py
```

Verification:

```bash
python - <<'PY'
import json
from pathlib import Path
p = Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M161_confidence_first_constrained_repair_materialization_smoke_v0/coverage.json')
c = json.loads(p.read_text())
assert c['status'] == 'e008_m161_confidence_first_constrained_repair_materialization_smoke_ready'
assert c['selected_next_unit'] == 'E008-M162 confidence-first constrained repair trajectory execution contract / Docker preflight'
assert c['materialization_ready'] is True
assert c['positive_navigation_improvement_ready'] is False
print('m161 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M161_confidence_first_constrained_repair_materialization_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M161_confidence_first_constrained_repair_materialization_smoke_v0/confidence_first_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M161_confidence_first_constrained_repair_materialization_smoke_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M161_confidence_first_constrained_repair_materialization_smoke_v0/repair_component_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M161_confidence_first_constrained_repair_materialization_smoke_v0/policy_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M161_confidence_first_constrained_repair_materialization_smoke_v0/policy_order_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M161_confidence_first_constrained_repair_materialization_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M161_confidence_first_constrained_repair_materialization_smoke_v0/materialization_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M161_confidence_first_constrained_repair_materialization_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M161_confidence_first_constrained_repair_materialization_smoke_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M161_confidence_first_constrained_repair_materialization_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M161_confidence_first_constrained_repair_materialization_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M161_confidence_first_constrained_repair_materialization_smoke_v0/`

Claim boundary:

- M161 is row materialization only.
- M161 operationalizes M160 without reintroducing additive path gain: detector-confidence remains the base order, path cost acts only as adjacent confidence-band tie-break, and rank displacement is capped at 1.
- M161 supports only pre-execution visit-order changes, not navigation performance.
- Positive navigation-improvement still requires Docker trajectory execution and protected `SR` / `SPL` / candidate-visit gates.
- Final `SR` / `SPL`, deployable policy, final RGB-D/open-vocabulary robustness, and human intent as a main claim remain blocked.

## E008-M162

Implementation unit: `E008-M162_confidence_first_constrained_repair_trajectory_contract_v0`.

- Status: `e008_m162_confidence_first_constrained_repair_trajectory_contract_ready_runner_next`.
- M161 status: `e008_m161_confidence_first_constrained_repair_materialization_smoke_ready`.
- Selected policy: `confidence_first_path_veto_tiebreak_repair_v1`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- Runner candidate rows: 5,400.
- Candidate rows by policy: 900 each for selected, protected baseline, `confidence_first_no_path_tiebreak_v1`, `source_gap_trigger_only_v1`, `budget_guarded_no_confidence_floor_v1`, and `budget_guarded_no_visit_guard_v1`.
- Execution plan rows: 180.
- Eval goal rows: 30.
- Oracle path rows: 30.
- Trajectory cost matrix rows: 33,354.
- Selected changed episode rows: 24 / 30.
- Selected local-swap promoted rows: 106.
- Max selected rank displacement: 1.
- Leakage audit: pass.
- Docker/data/runner preflight: pass.
- M163 runner compile: pass.
- Trajectory execution result ready: false.
- Positive navigation-improvement ready: false.
- Selected next unit: E008-M163 confidence-first constrained repair trajectory execution.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m162_confidence_first_constrained_repair_trajectory_contract.py
```

Verification:

```bash
python - <<'PY'
import json
from pathlib import Path
p = Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M162_confidence_first_constrained_repair_trajectory_contract_v0/coverage.json')
c = json.loads(p.read_text())
assert c['status'] == 'e008_m162_confidence_first_constrained_repair_trajectory_contract_ready_runner_next'
assert c['trajectory_execution_contract_ready'] is True
assert c['trajectory_execution_result_ready'] is False
assert c['selected_next_unit'] == 'E008-M163 confidence-first constrained repair trajectory execution'
assert c['trajectory_candidate_rows'] == 5400
assert c['trajectory_execution_plan_rows'] == 180
assert c['docker_preflight_pass'] is True
print('m162 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M162_confidence_first_constrained_repair_trajectory_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M162_confidence_first_constrained_repair_trajectory_contract_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M162_confidence_first_constrained_repair_trajectory_contract_v0/confidence_first_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M162_confidence_first_constrained_repair_trajectory_contract_v0/trajectory_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M162_confidence_first_constrained_repair_trajectory_contract_v0/confidence_first_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M162_confidence_first_constrained_repair_trajectory_contract_v0/episode_goal_eval_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M162_confidence_first_constrained_repair_trajectory_contract_v0/oracle_path_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M162_confidence_first_constrained_repair_trajectory_contract_v0/input_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M162_confidence_first_constrained_repair_trajectory_contract_v0/trajectory_execution_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M162_confidence_first_constrained_repair_trajectory_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M162_confidence_first_constrained_repair_trajectory_contract_v0/docker_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M162_confidence_first_constrained_repair_trajectory_contract_v0/m163_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M162_confidence_first_constrained_repair_trajectory_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M162_confidence_first_constrained_repair_trajectory_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M162_confidence_first_constrained_repair_trajectory_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M162_confidence_first_constrained_repair_trajectory_contract_v0/`

Claim boundary:

- M162 is trajectory contract and Docker/data/runner preflight only.
- M162 preserves M161's selected visit-order changes but does not execute `Habitat` trajectories.
- M162 supports only readiness for M163 execution, not positive navigation-improvement.
- Positive navigation-improvement requires M163 execution and M164 protected-baseline interpretation.
- Final `SR` / `SPL`, deployable policy, final RGB-D/open-vocabulary robustness, and human intent as a main claim remain blocked.

## E008-M163

Implementation unit: `E008-M163_confidence_first_constrained_repair_trajectory_execution_v0`.

- Status: `e008_m163_confidence_first_constrained_repair_trajectory_execution_ready`.
- Launched at: 2026-06-11 21:58 KST.
- Completed at: 2026-06-11 21:58 KST.
- tmux session: `e008_m163_confidence_repair`.
- Log: `logs/20260611_215822_e008_m163_confidence_first_repair_trajectory.log`.
- Input contract: `experiments/E008_real_navigation_benchmark/artifacts/E008-M162_confidence_first_constrained_repair_trajectory_contract_v0/`.
- Output path: `experiments/E008_real_navigation_benchmark/artifacts/E008-M163_confidence_first_constrained_repair_trajectory_execution_v0/`.
- Derived output path: `local_dataset/HM3D_navigation_bridge/E008-M163_confidence_first_constrained_repair_trajectory_execution_v0/`.
- Scan-task-policy rows: 180.
- Trajectory attempt rows: 2,187.
- Success rows: 144 / 180.
- Aggregate `SR`: 0.800000.
- Aggregate mean `SPL`: 0.214863.
- Selected policy `SR` / `SPL`: 0.800000 / 0.228632.
- Protected detector-confidence `SR` / `SPL`: 0.800000 / 0.231845.
- Selected policy candidate visits: 11.400000.
- Protected detector-confidence candidate visits: 11.200000.
- Leakage audit: pass.
- Scene error rows: 0.
- Positive navigation-improvement ready: false until M164 interpretation.
- Selected next unit: E008-M164 confidence-first constrained repair trajectory result interpretation / protected-baseline gate.

Command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp \
  -v /home/yoohyun/research3/local_dataset/data:/data:ro \
  -v /home/yoohyun/research2:/work -w /work \
  research3/habitat-h001:20260508-calib-artifacts bash -lc \
  "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m163_confidence_first_constrained_repair_trajectory_execution.py \
  --m162-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M162_confidence_first_constrained_repair_trajectory_contract_v0 \
  --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M163_confidence_first_constrained_repair_trajectory_execution_v0 \
  --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M163_confidence_first_constrained_repair_trajectory_execution_v0"
```

Verification:

```bash
python - <<'PY'
import json
from pathlib import Path
p = Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M163_confidence_first_constrained_repair_trajectory_execution_v0/coverage.json')
c = json.loads(p.read_text())
assert c['status'] == 'e008_m163_confidence_first_constrained_repair_trajectory_execution_ready'
assert c['scan_task_policy_rows'] == 180
print('m163 ready')
PY
```

Expected artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M163_confidence_first_constrained_repair_trajectory_execution_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M163_confidence_first_constrained_repair_trajectory_execution_v0/dynamic_stale_trajectory_attempt_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M163_confidence_first_constrained_repair_trajectory_execution_v0/dynamic_stale_trajectory_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M163_confidence_first_constrained_repair_trajectory_execution_v0/pairwise_policy_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M163_confidence_first_constrained_repair_trajectory_execution_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M163_confidence_first_constrained_repair_trajectory_execution_v0/report.md`

Claim boundary:

- M163 is an execution unit; it is not final interpretation.
- Raw execution does not support positive navigation-improvement: selected policy ties detector-confidence on `SR` but has lower `SPL` and higher candidate visits.
- Positive navigation-improvement requires M164 protected-baseline interpretation.
- Final `SR` / `SPL`, deployable policy, final RGB-D/open-vocabulary robustness, and human intent as a main claim remain blocked until later gates.

## E008-M164

Implementation unit: `E008-M164_confidence_first_constrained_repair_result_interpretation_v0`.

- Status: `e008_m164_confidence_first_constrained_repair_result_interpretation_ready`.
- M163 status: `e008_m163_confidence_first_constrained_repair_trajectory_execution_ready`.
- Selected policy: `confidence_first_path_veto_tiebreak_repair_v1`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- Selected policy `SR` / `SPL`: 0.800000 / 0.228632.
- Protected detector-confidence `SR` / `SPL`: 0.800000 / 0.231845.
- Selected policy delta `SPL`: -0.003213.
- Selected policy delta candidate visits: +0.200000.
- Best `SPL` policy: `budget_guarded_no_visit_guard_v1` with `SPL` 0.236760.
- Gate pass / warning / fail: 6 / 2 / 7.
- Positive navigation-improvement ready: false.
- Diagnostic table ready: true.
- Selected next unit: E008-M165 confidence-first constrained repair failure decomposition / next-route decision.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m164_confidence_first_constrained_repair_result_interpretation.py
```

Verification:

```bash
python - <<'PY'
import json
from pathlib import Path
p = Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M164_confidence_first_constrained_repair_result_interpretation_v0/coverage.json')
c = json.loads(p.read_text())
assert c['status'] == 'e008_m164_confidence_first_constrained_repair_result_interpretation_ready'
assert c['positive_navigation_improvement_ready'] is False
assert c['selected_next_unit'] == 'E008-M165 confidence-first constrained repair failure decomposition / next-route decision'
print('m164 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M164_confidence_first_constrained_repair_result_interpretation_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M164_confidence_first_constrained_repair_result_interpretation_v0/policy_result_interpretation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M164_confidence_first_constrained_repair_result_interpretation_v0/pairwise_delta_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M164_confidence_first_constrained_repair_result_interpretation_v0/episode_delta_profile_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M164_confidence_first_constrained_repair_result_interpretation_v0/gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M164_confidence_first_constrained_repair_result_interpretation_v0/component_interpretation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M164_confidence_first_constrained_repair_result_interpretation_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M164_confidence_first_constrained_repair_result_interpretation_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M164_confidence_first_constrained_repair_result_interpretation_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M164_confidence_first_constrained_repair_result_interpretation_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M164_confidence_first_constrained_repair_result_interpretation_v0/`

Claim boundary:

- M164 rejects a positive navigation-improvement claim for the selected confidence-first constrained repair policy.
- `confidence_floor_guard` remains diagnostic-supported because no-confidence-floor is much worse.
- `local_path_tiebreak_repair` is rejected in its current form because selected repair loses `SPL` and candidate-visit efficiency to detector-confidence / no-path.
- `source_gap_trigger` is inert on the current denominator because source-gap-only equals detector-confidence.
- `budget_guarded_no_visit_guard_v1` is a tradeoff witness, not a posthoc selected method, because it has best `SPL` but more visits than detector-confidence.
- Final `SR` / `SPL`, deployable policy, final RGB-D/open-vocabulary robustness, and human intent as a main claim remain blocked until later gates.

## E008-M165

Implementation unit: `E008-M165_confidence_first_repair_failure_decomposition_v0`.

- Status: `e008_m165_confidence_first_repair_failure_decomposition_ready`.
- M161 status: `e008_m161_confidence_first_constrained_repair_materialization_ready`.
- M163 status: `e008_m163_confidence_first_constrained_repair_trajectory_execution_ready`.
- M164 status: `e008_m164_confidence_first_constrained_repair_result_interpretation_ready`.
- Changed episodes: 24 / 30.
- Selected success proposal changes vs detector-confidence: 0.
- Selected failure type changes vs detector-confidence: 0.
- Mean delta `SPL` / candidate visits / path length: -0.003213 / +0.200000 / +0.249997.
- Selected better / worse / tie `SPL` rows: 5 / 6 / 19.
- Selected more / fewer visit rows: 7 / 1.
- Supported components: `protected_detector_confidence_base`, `confidence_floor_guard`.
- Rejected/exhausted components: `local_path_tiebreak_repair`, `source_gap_trigger`, `ranking_only_navigation_repair`.
- Tradeoff component: `no_visit_guard_route`.
- Positive navigation-improvement ready: false.
- Local rerank scale-up ready: false.
- Selected next unit: E008-M166 navigation failure-boundary package and method-pivot contract.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m165_confidence_first_repair_failure_decomposition.py
```

Verification:

```bash
python - <<'PY'
import json
from pathlib import Path
p = Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M165_confidence_first_repair_failure_decomposition_v0/coverage.json')
c = json.loads(p.read_text())
assert c['status'] == 'e008_m165_confidence_first_repair_failure_decomposition_ready'
assert c['positive_navigation_improvement_ready'] is False
assert c['selected_success_proposal_changed_rows'] == 0
assert c['changed_episode_rows'] == 24
assert c['selected_next_unit'] == 'E008-M166 navigation failure-boundary package and method-pivot contract'
print('m165 ready')
PY
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M165_confidence_first_repair_failure_decomposition_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M165_confidence_first_repair_failure_decomposition_v0/episode_failure_profile_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M165_confidence_first_repair_failure_decomposition_v0/component_failure_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M165_confidence_first_repair_failure_decomposition_v0/failure_mechanism_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M165_confidence_first_repair_failure_decomposition_v0/principle_revision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M165_confidence_first_repair_failure_decomposition_v0/m166_route_seed_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M165_confidence_first_repair_failure_decomposition_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M165_confidence_first_repair_failure_decomposition_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M165_confidence_first_repair_failure_decomposition_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M165_confidence_first_repair_failure_decomposition_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M165_confidence_first_repair_failure_decomposition_v0/`

Claim boundary:

- M165 decomposes the M163/M164 negative gate; it is not a positive navigation result.
- Local path tie-break should not be scaled as the main method in its current form.
- Confidence floor remains a necessary guard only.
- Source-gap trigger must be evaluated only on source-gap/source-coverage or external proposal-source rows.
- M166 must decide the failure-boundary package and method-pivot / external-baseline contract.

## E008-M166

Implementation unit: `E008-M166_navigation_failure_boundary_method_pivot_contract_v0`.

- Status: `e008_m166_navigation_failure_boundary_method_pivot_contract_ready`.
- Selected method family: `source_coverage_memory_interface`.
- Selected policy id: `source_coverage_memory_interface_policy_v1`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- Local path tie-break as main method: false.
- Confidence floor guard retained: true.
- Source-gap claim ready on current denominator: false.
- Selected next unit: E008-M167 source-coverage memory-interface method contract.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m166_navigation_failure_boundary_method_pivot_contract.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M166_navigation_failure_boundary_method_pivot_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M166_navigation_failure_boundary_method_pivot_contract_v0/failure_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M166_navigation_failure_boundary_method_pivot_contract_v0/method_pivot_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M166_navigation_failure_boundary_method_pivot_contract_v0/comparison_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M166_navigation_failure_boundary_method_pivot_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M166_navigation_failure_boundary_method_pivot_contract_v0/`

Claim boundary:

- M166 is a boundary/contract step, not a positive navigation result.
- M166 excludes local path tie-break from the main method family.
- M166 keeps `confidence_floor_guard` as a necessary guard.

## E008-M167

Implementation unit: `E008-M167_source_coverage_memory_interface_method_contract_v0`.

- Status: `e008_m167_source_coverage_memory_interface_method_contract_ready`.
- Selected policy id: `source_coverage_memory_interface_policy_v1`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- Method contract rows: 2.
- Input contract rows: 18.
- Comparison contract rows: 5.
- Ablation contract rows: 3.
- Metric target rows: 3.
- Posthoc threshold change allowed: false.
- Denominator change allowed: false.
- Selected next unit: E008-M168 source-coverage memory-interface row materialization.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m167_source_coverage_memory_interface_method_contract.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M167_source_coverage_memory_interface_method_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M167_source_coverage_memory_interface_method_contract_v0/method_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M167_source_coverage_memory_interface_method_contract_v0/input_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M167_source_coverage_memory_interface_method_contract_v0/comparison_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M167_source_coverage_memory_interface_method_contract_v0/metric_target_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M167_source_coverage_memory_interface_method_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M167_source_coverage_memory_interface_method_contract_v0/`

Claim boundary:

- M167 is a pre-materialization contract step.
- `ConceptGraphs-only` and static stale memory stay in the comparison ledger but are not mixed into the M168 detector denominator.

## E008-M168

Implementation unit: `E008-M168_source_coverage_memory_interface_materialization_v0`.

- Status: `e008_m168_source_coverage_memory_interface_materialization_ready`.
- Selected policy id: `source_coverage_memory_interface_policy_v1`.
- Candidate rows: 4,500.
- Policy plan rows: 150.
- Policies: `source_coverage_memory_interface_policy_v1`, `detector_confidence_reachable_subset_v0`, `source_coverage_only_task_agnostic_v1`, `confidence_floor_only_v1`, `path_cost_only_reachable_subset_v1`.
- Selected changed episode rows: 30.
- Selected promoted rows: 268.
- Selected mean coverage gain in first 10 candidates: 0.200000.
- Source-gap prelabel rows: 0.
- Leakage audit pass: true.
- Selected next unit: E008-M169 source-coverage memory-interface Docker trajectory execution contract / preflight.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m168_source_coverage_memory_interface_materialization.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M168_source_coverage_memory_interface_materialization_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M168_source_coverage_memory_interface_materialization_v0/source_coverage_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M168_source_coverage_memory_interface_materialization_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M168_source_coverage_memory_interface_materialization_v0/policy_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M168_source_coverage_memory_interface_materialization_v0/policy_order_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M168_source_coverage_memory_interface_materialization_v0/source_ready_split_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M168_source_coverage_memory_interface_materialization_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M168_source_coverage_memory_interface_materialization_v0/`

Claim boundary:

- M168 materializes rows only; it does not execute `Habitat` trajectories.
- Source-gap trigger remains inactive on this denominator.

## E008-M169

Implementation unit: `E008-M169_source_coverage_memory_interface_trajectory_contract_v0`.

- Status: `e008_m169_source_coverage_memory_interface_trajectory_contract_ready_runner_next`.
- Selected policy id: `source_coverage_memory_interface_policy_v1`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- Trajectory candidate rows: 4,500.
- Trajectory execution plan rows: 150.
- Eval goal rows: 30.
- Oracle path rows: 30.
- Trajectory cost matrix rows: 33,354.
- Docker preflight pass: true.
- Runner implemented: true.
- Runner py_compile pass: true.
- Selected next unit: E008-M170 source-coverage memory-interface trajectory execution.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m169_source_coverage_memory_interface_trajectory_contract.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M169_source_coverage_memory_interface_trajectory_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M169_source_coverage_memory_interface_trajectory_contract_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M169_source_coverage_memory_interface_trajectory_contract_v0/trajectory_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M169_source_coverage_memory_interface_trajectory_contract_v0/trajectory_execution_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M169_source_coverage_memory_interface_trajectory_contract_v0/docker_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M169_source_coverage_memory_interface_trajectory_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M169_source_coverage_memory_interface_trajectory_contract_v0/m170_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M169_source_coverage_memory_interface_trajectory_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M169_source_coverage_memory_interface_trajectory_contract_v0/`

Claim boundary:

- M169 is a contract/preflight step and does not execute `Habitat` trajectories.
- M170 should be launched as a background Docker job if execution is requested.
- At the M169 contract stage, positive navigation claims still required M170 execution and M171 protected-baseline interpretation.

## E008-M170

Implementation unit: `E008-M170_source_coverage_memory_interface_trajectory_execution_v0`.

- Status: `e008_m170_source_coverage_memory_interface_trajectory_execution_ready`.
- Docker image: `research3/habitat-h001:20260508-calib-artifacts`.
- Source mount: `/home/yoohyun/research3/local_dataset/data:/data:ro`.
- Trajectory candidate rows: 4,500.
- Trajectory execution plan rows: 150.
- Scan-task-policy rows: 150.
- Trajectory attempt rows: 1,862.
- Trajectory success rows: 120 / 150.
- Aggregate `SR`: 0.800000.
- Aggregate mean `SPL`: 0.213581.
- Leakage audit pass: true.
- Log: `logs/20260612_021937_e008_m170_source_coverage_memory_interface_trajectory.log`.
- Selected next unit: E008-M171 source-coverage memory-interface trajectory result interpretation / protected-baseline gate.

Command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp \
  -v /home/yoohyun/research3/local_dataset/data:/data:ro \
  -v /home/yoohyun/research2:/work \
  -w /work research3/habitat-h001:20260508-calib-artifacts \
  bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m170_source_coverage_memory_interface_trajectory_execution.py --m169-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M169_source_coverage_memory_interface_trajectory_contract_v0 --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M170_source_coverage_memory_interface_trajectory_execution_v0 --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M170_source_coverage_memory_interface_trajectory_execution_v0"
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M170_source_coverage_memory_interface_trajectory_execution_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M170_source_coverage_memory_interface_trajectory_execution_v0/dynamic_stale_trajectory_attempt_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M170_source_coverage_memory_interface_trajectory_execution_v0/dynamic_stale_trajectory_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M170_source_coverage_memory_interface_trajectory_execution_v0/pairwise_policy_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M170_source_coverage_memory_interface_trajectory_execution_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M170_source_coverage_memory_interface_trajectory_execution_v0/`

Claim boundary:

- M170 executes `Habitat` trajectories, but it does not by itself support positive navigation improvement.
- Protected-baseline interpretation is fixed in M171.

## E008-M171

Implementation unit: `E008-M171_source_coverage_memory_interface_result_interpretation_v0`.

- Status: `e008_m171_source_coverage_memory_interface_result_interpretation_ready`.
- Selected policy: `source_coverage_memory_interface_policy_v1`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- Selected `SR` / `SPL`: 0.800000 / 0.225556.
- Protected `SR` / `SPL`: 0.800000 / 0.231845.
- Source-coverage-only `SR` / `SPL`: 0.800000 / 0.234605.
- Selected delta `SPL` vs protected: -0.006289.
- Selected delta candidate visits vs protected: +0.466667.
- Gate rows: 7, fail rows: 4.
- Positive navigation-improvement ready: false.
- Selected next unit: E008-M172 source-coverage ablation tradeoff decomposition and policy decision.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m171_source_coverage_memory_interface_result_interpretation.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M171_source_coverage_memory_interface_result_interpretation_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M171_source_coverage_memory_interface_result_interpretation_v0/policy_result_interpretation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M171_source_coverage_memory_interface_result_interpretation_v0/pairwise_delta_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M171_source_coverage_memory_interface_result_interpretation_v0/gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M171_source_coverage_memory_interface_result_interpretation_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M171_source_coverage_memory_interface_result_interpretation_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M171_source_coverage_memory_interface_result_interpretation_v0/`

Claim boundary:

- M171 rejects the selected source-coverage memory-interface policy as a positive navigation-improvement claim.
- The result is still useful because it isolates a tradeoff witness: `source_coverage_only_task_agnostic_v1` has higher `SPL` but uses more candidate visits.
- M172 later fixes source-coverage-only as a Pareto/budget tradeoff witness rather than a precommitted main method.

## E008-M172

Implementation unit: `E008-M172_source_coverage_ablation_tradeoff_decomposition_v0`.

- Status: `e008_m172_source_coverage_ablation_tradeoff_decomposition_ready`.
- Selected policy: `source_coverage_memory_interface_policy_v1`.
- Selected policy primary Pareto member: false.
- Selected policy primary dominated by: `confidence_floor_only_v1`, `detector_confidence_reachable_subset_v0`.
- Source-coverage-only policy: `source_coverage_only_task_agnostic_v1`.
- Source-coverage-only primary Pareto member: true.
- Source-coverage-only delta `SPL` vs detector: +0.002761.
- Source-coverage-only delta candidate visits vs detector: +0.766667.
- Source-coverage-only delta path length vs detector: -13.116417m.
- Source-coverage-only better/worse/tie `SPL` rows vs detector: 12 / 12 / 6.
- Source-coverage-only changed successful proposal rows vs detector: 12.
- Promote source-coverage-only as main method now: false.
- Selected next unit: E008-M173 source-coverage utility/Pareto contract and bounded method redesign.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m172_source_coverage_ablation_tradeoff_decomposition.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M172_source_coverage_ablation_tradeoff_decomposition_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M172_source_coverage_ablation_tradeoff_decomposition_v0/policy_pareto_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M172_source_coverage_ablation_tradeoff_decomposition_v0/episode_tradeoff_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M172_source_coverage_ablation_tradeoff_decomposition_v0/comparison_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M172_source_coverage_ablation_tradeoff_decomposition_v0/failure_diagnosis_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M172_source_coverage_ablation_tradeoff_decomposition_v0/policy_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M172_source_coverage_ablation_tradeoff_decomposition_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M172_source_coverage_ablation_tradeoff_decomposition_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M172_source_coverage_ablation_tradeoff_decomposition_v0/`

Claim boundary:

- M172 supports a diagnostic statement that source coverage creates a Pareto tradeoff, not a clean method win.
- `source_coverage_only_task_agnostic_v1` is not promoted as the main method because it is task-agnostic, not the preselected method, and spends more candidate visits.
- M173 should precommit whether the next method optimizes fixed-budget `SPL`, expected search cost, or a Pareto utility before any new long trajectory execution.

## E008-M173

Implementation unit: `E008-M173_source_coverage_utility_pareto_contract_v0`.

- Status: `e008_m173_source_coverage_utility_pareto_contract_ready`.
- Selected policy contract: `source_coverage_budgeted_utility_policy_v1`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- Previous selected policy: `source_coverage_memory_interface_policy_v1`.
- Source-coverage witness: `source_coverage_only_task_agnostic_v1`.
- Candidate rows audited: 4,500.
- Required fields ready: true.
- Method contract rows: 2.
- Utility objective rows: 2.
- Guard contract rows: 5.
- Metric target rows: 4.
- Ablation contract rows: 6.
- Source-coverage-only delta `SPL` vs detector: +0.002761.
- Source-coverage-only delta candidate visits vs detector: +0.766667.
- Performance claim ready: false.
- Trajectory execution ready: false.
- Selected next unit: E008-M174 source-coverage utility/Pareto row materialization smoke.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m173_source_coverage_utility_pareto_contract.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M173_source_coverage_utility_pareto_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M173_source_coverage_utility_pareto_contract_v0/field_availability_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M173_source_coverage_utility_pareto_contract_v0/method_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M173_source_coverage_utility_pareto_contract_v0/utility_objective_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M173_source_coverage_utility_pareto_contract_v0/guard_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M173_source_coverage_utility_pareto_contract_v0/input_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M173_source_coverage_utility_pareto_contract_v0/metric_target_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M173_source_coverage_utility_pareto_contract_v0/ablation_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M173_source_coverage_utility_pareto_contract_v0/disconfirmation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M173_source_coverage_utility_pareto_contract_v0/materialization_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M173_source_coverage_utility_pareto_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M173_source_coverage_utility_pareto_contract_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M173_source_coverage_utility_pareto_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M173_source_coverage_utility_pareto_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M173_source_coverage_utility_pareto_contract_v0/`

Claim boundary:

- M173 is a pre-materialization method contract, not a performance result.
- `source_coverage_only_task_agnostic_v1` remains a Pareto witness, not the selected method.
- `source_coverage_budgeted_utility_policy_v1` must be materialized in M174 under the fixed utility formula, detector-confidence fallback, and leakage/order guards before any Docker trajectory execution.

## E008-M174

Implementation unit: `E008-M174_source_coverage_utility_pareto_materialization_smoke_v0`.

- Status: `e008_m174_source_coverage_utility_pareto_materialization_blocked`.
- Selected policy: `source_coverage_budgeted_utility_policy_v1`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- Source-coverage witness: `source_coverage_only_task_agnostic_v1`.
- Candidate rows: 6,300.
- Policy plan rows: 210.
- Utility component rows: 2,215.
- Leakage audit pass: true.
- Order audit pass: true.
- Guard audit pass: true.
- Selected policy changed episode rows: 0 / 30.
- Selected policy promoted rows: 0.
- Source-coverage witness changed episode rows: 30 / 30.
- Selected policy activity gate pass: false.
- Trajectory contract ready next: false.
- Docker trajectory execution launched: false.
- Selected next unit: E008-M174b source-coverage utility conservatism failure decomposition.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m174_source_coverage_utility_pareto_materialization.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174_source_coverage_utility_pareto_materialization_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174_source_coverage_utility_pareto_materialization_smoke_v0/source_coverage_utility_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174_source_coverage_utility_pareto_materialization_smoke_v0/dynamic_stale_overlay_trajectory_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174_source_coverage_utility_pareto_materialization_smoke_v0/policy_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174_source_coverage_utility_pareto_materialization_smoke_v0/utility_component_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174_source_coverage_utility_pareto_materialization_smoke_v0/policy_order_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174_source_coverage_utility_pareto_materialization_smoke_v0/guard_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174_source_coverage_utility_pareto_materialization_smoke_v0/leakage_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174_source_coverage_utility_pareto_materialization_smoke_v0/materialization_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174_source_coverage_utility_pareto_materialization_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174_source_coverage_utility_pareto_materialization_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174_source_coverage_utility_pareto_materialization_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M174_source_coverage_utility_pareto_materialization_smoke_v0/`

Claim boundary:

- M174 materializes rows and audits them; it does not execute `Habitat` trajectories.
- Leakage/order/guard audits pass, but selected policy activity fails because the precommitted utility is too conservative to change detector-confidence ordering.
- The then-planned Docker execution path remains blocked; M174b later closes within-pool source-coverage reranking as negative and selects a candidate-source expansion contract.

## E008-M174b

Implementation unit: `E008-M174b_source_coverage_utility_conservatism_failure_decomposition_v0`.

- Status: `e008_m174b_source_coverage_utility_conservatism_failure_decomposition_ready`.
- Selected policy: `source_coverage_budgeted_utility_policy_v1`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- Component rows: 2,215.
- Selected changed episode rows: 0 / 30.
- Selected promoted rows: 0.
- Selected positive utility rows: 0.
- Selected utility max: -0.008847.
- Selected utility mean: -0.081486.
- Selected confidence guard fail rows: 304.
- Selected prefix path guard fail rows: 99.
- Selected coverage positive rows: 55.
- Selected path-saving positive rows: 84.
- Selected source-gap prelabel rows: 0.
- No-confidence-guard positive utility rows: 0.
- Docker trajectory execution ready: false.
- Posthoc tuning allowed: false.
- Source-coverage rerank branch closed negative: true.
- Selected next unit: E008-M175 source-coverage trigger/candidate-source expansion contract.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m174b_source_coverage_utility_conservatism_failure_decomposition.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174b_source_coverage_utility_conservatism_failure_decomposition_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174b_source_coverage_utility_conservatism_failure_decomposition_v0/policy_component_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174b_source_coverage_utility_conservatism_failure_decomposition_v0/selected_utility_factor_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174b_source_coverage_utility_conservatism_failure_decomposition_v0/failure_mechanism_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174b_source_coverage_utility_conservatism_failure_decomposition_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174b_source_coverage_utility_conservatism_failure_decomposition_v0/next_contract_seed_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174b_source_coverage_utility_conservatism_failure_decomposition_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174b_source_coverage_utility_conservatism_failure_decomposition_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M174b_source_coverage_utility_conservatism_failure_decomposition_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M174b_source_coverage_utility_conservatism_failure_decomposition_v0/`

Claim boundary:

- M174b does not support real navigation `SR` / `SPL`.
- Within-pool source-coverage utility reranking is closed as a negative branch under the current fixed denominator and guards.
- The next method form must use source coverage as a candidate-source expansion / re-observation trigger before detector-confidence ranking, not as posthoc weight tuning.

## E008-M175

Implementation unit: `E008-M175_source_coverage_trigger_candidate_source_expansion_contract_v0`.

- Status: `e008_m175_source_coverage_trigger_candidate_source_expansion_contract_ready`.
- Selected method family: `source_coverage_triggered_candidate_source_expansion_v1`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- M174b selected changed episode rows: 0.
- M174b selected positive utility rows: 0.
- M121 target-free source-pool template rows: 40 observation poses / 320 render-plan rows.
- M124 target-free detector prediction rows available as diagnostic template: 24.
- Trigger rows fixed for M176: 4.
- Candidate-source routes fixed for M176: 4.
- M176 materialization ready next: true.
- Docker trajectory execution ready: false.
- Render/detector long job ready now: false.
- Posthoc tuning allowed: false.
- Selected next unit: E008-M176 source-coverage trigger row materialization smoke.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m175_source_coverage_trigger_candidate_source_expansion_contract.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M175_source_coverage_trigger_candidate_source_expansion_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M175_source_coverage_trigger_candidate_source_expansion_contract_v0/method_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M175_source_coverage_trigger_candidate_source_expansion_contract_v0/trigger_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M175_source_coverage_trigger_candidate_source_expansion_contract_v0/input_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M175_source_coverage_trigger_candidate_source_expansion_contract_v0/candidate_source_route_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M175_source_coverage_trigger_candidate_source_expansion_contract_v0/m176_materialization_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M175_source_coverage_trigger_candidate_source_expansion_contract_v0/pre_execution_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M175_source_coverage_trigger_candidate_source_expansion_contract_v0/disconfirmation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M175_source_coverage_trigger_candidate_source_expansion_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M175_source_coverage_trigger_candidate_source_expansion_contract_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M175_source_coverage_trigger_candidate_source_expansion_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M175_source_coverage_trigger_candidate_source_expansion_contract_v0/`

Claim boundary:

- M175 does not support real navigation `SR` / `SPL`.
- M175 does not launch Docker, render, detector, or trajectory jobs.
- M175 keeps within-pool source-coverage reranking closed negative and moves source coverage to the map/source acquisition interface.
- M176 must materialize non-leaky trigger/source-expansion rows before downstream execution is justified.

## E008-M176

Implementation unit: `E008-M176_source_coverage_trigger_row_materialization_smoke_v0`.

- Status: `e008_m176_source_coverage_trigger_row_materialization_smoke_ready`.
- Selected method family: `source_coverage_triggered_candidate_source_expansion_v1`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- Trigger rows: 30.
- Trigger request rows: 30.
- Trigger request rate: 1.0.
- Source sparse trigger rows: 16.
- Detector uncertainty trigger rows: 7.
- Path/source-ready gap trigger rows: 23.
- Candidate-source expansion plan rows: 30.
- Policy-visible source request changed rows: 30.
- Blocked input hit rows: 0.
- Trigger selectivity warning: true.
- Budget/priority guard required next: true.
- Render/detector long job ready now: false.
- Docker trajectory execution ready: false.
- Selected next unit: E008-M177 source-pool pose/render-plan materialization contract.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m176_source_coverage_trigger_row_materialization_smoke.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M176_source_coverage_trigger_row_materialization_smoke_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M176_source_coverage_trigger_row_materialization_smoke_v0/source_coverage_trigger_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M176_source_coverage_trigger_row_materialization_smoke_v0/candidate_source_expansion_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M176_source_coverage_trigger_row_materialization_smoke_v0/allowed_input_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M176_source_coverage_trigger_row_materialization_smoke_v0/blocked_input_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M176_source_coverage_trigger_row_materialization_smoke_v0/policy_visible_change_probe_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M176_source_coverage_trigger_row_materialization_smoke_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M176_source_coverage_trigger_row_materialization_smoke_v0/next_verification_sequence_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M176_source_coverage_trigger_row_materialization_smoke_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M176_source_coverage_trigger_row_materialization_smoke_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M176_source_coverage_trigger_row_materialization_smoke_v0/`

Next verification sequence if M176 proceeds normally:

1. E008-M177: materialize target-free source-pose/render-plan rows with fixed budget/priority guard.
2. E008-M178: validate source pose navmesh/snap readiness and write render/detector launcher contract.
3. E008-M179: run and verify bounded render/detector candidate generation.
4. E008-M180: validate candidate coordinates, navmesh readiness, and source-ready/source-gap split.
5. E008-M181: materialize expanded candidate visit-order/path rows and verify selected method changes candidate order or candidate-source availability.
6. E008-M182: run leakage-safe goal-evaluation proxy and failure taxonomy before trajectory execution.
7. E008-M183: write Docker trajectory execution contract/preflight only if M182 shows a policy-visible gain worth executing.
8. E008-M184: execute Docker trajectories and collect `SR`, `SPL`, path length, visits, and failure type.
9. E008-M185: interpret against protected `detector_confidence_reachable_subset_v0` and decide scale/claim boundary.
10. Post-M185: run heldout transfer, ablations, and external baselines such as `ConceptGraphs`, `Open3DSG`, `HOV-SG`, or navigation baselines.

Claim boundary:

- M176 does not support real navigation `SR` / `SPL`.
- M176 does not launch render, detector, external-map, or Docker trajectory jobs.
- M176 confirms source-expansion requests can be materialized without blocked-input leakage, but the trigger is too broad for a deployable policy without M177 budget/priority guard.

## E008-M177

Implementation unit: `E008-M177_source_pool_pose_render_plan_materialization_contract_v0`.

- Status: `e008_m177_source_pool_pose_render_plan_materialization_contract_ready`.
- Input M176 trigger request rows: 30.
- Selected request rows after fixed budget/priority guard: 8.
- Source pose rows: 64.
- Render plan rows: 256 / budget 256.
- Selected scenes: 2.
- Selected categories: 4.
- Missing source-anchor rows: 0.
- Blocked input hit rows: 0.
- Render/detector long job launched: false.
- Selected next unit: E008-M178 navmesh/snap validation and render/detector launcher contract.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m177_source_pool_pose_render_plan_materialization_contract.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M177_source_pool_pose_render_plan_materialization_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M177_source_pool_pose_render_plan_materialization_contract_v0/budget_priority_guard_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M177_source_pool_pose_render_plan_materialization_contract_v0/selected_source_request_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M177_source_pool_pose_render_plan_materialization_contract_v0/source_pool_observation_pose_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M177_source_pool_pose_render_plan_materialization_contract_v0/source_pool_render_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M177_source_pool_pose_render_plan_materialization_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M177_source_pool_pose_render_plan_materialization_contract_v0/`

Claim boundary:

- M177 supports only leakage-audited, budgeted source-pool pose/render-plan materialization.
- M177 does not render frames, run detector inference, evaluate targets, execute trajectories, or support real navigation `SR` / `SPL`.

## E008-M178

Implementation unit: `E008-M178_navmesh_snap_render_detector_launcher_contract_v0`.

- Status: `e008_m178_navmesh_snap_render_detector_launcher_contract_ready`.
- Selected request rows: 8.
- Source pose rows: 64.
- Snap-ready rows: 64 / 64.
- Source-ready rows for M180: 64 / 64.
- Render plan rows: 256.
- Detector manifest rows: 8.
- Readiness gate fail/warning rows: 0 / 0.
- Long-job command rows: 2.
- Render/detector jobs launched in M178: false.
- Selected next unit: E008-M179 bounded render/detector execution and verification.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m178_navmesh_snap_render_detector_launcher_contract.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M178_navmesh_snap_render_detector_launcher_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M178_navmesh_snap_render_detector_launcher_contract_v0/snap_validation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M178_navmesh_snap_render_detector_launcher_contract_v0/source_pool_render_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M178_navmesh_snap_render_detector_launcher_contract_v0/source_pool_detector_manifest_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M178_navmesh_snap_render_detector_launcher_contract_v0/long_job_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M178_navmesh_snap_render_detector_launcher_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M178_navmesh_snap_render_detector_launcher_contract_v0/`

Claim boundary:

- M178 validates source-pool pose feasibility and records render/detector launcher inputs only.
- M178 does not run detector inference, evaluate ObjectNav goals, execute trajectories, or support real navigation `SR` / `SPL`.

## E008-M179

Implementation unit: `E008-M179_bounded_render_detector_execution_verification_v0`.

- Status: `e008_m179_bounded_render_detector_execution_ready`.
- Render status: `e008_m179_render_ready`.
- Detector status: `e008_m179_detector_candidate_source_ready`.
- Render plan rows: 256.
- Ready render frames: 256 / 256.
- Detector manifest ready rows: 8.
- Detector prediction rows: 192.
- Coordinate candidate rows: 192.
- Pre-cap candidate rows: 2,519.
- Detector tmux session: completed `e008_m179_source_pool_detector`.
- Detector log: `logs/20260613_004908_e008_m179_source_pool_detector.log`.
- Detector output path: `experiments/E008_real_navigation_benchmark/artifacts/E008-M179_bounded_render_detector_execution_verification_v0/detector`.
- Selected next unit: E008-M180 candidate navmesh/source-readiness validation.

Commands:

```bash
python experiments/E008_real_navigation_benchmark/tools/launch_m179_bounded_render_detector_execution.py --stage render
python experiments/E008_real_navigation_benchmark/tools/verify_m179_bounded_render_detector_execution.py --require-render-ready
python experiments/E008_real_navigation_benchmark/tools/launch_m179_bounded_render_detector_execution.py --stage detector
python experiments/E008_real_navigation_benchmark/tools/verify_m179_bounded_render_detector_execution.py --require-ready
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M179_bounded_render_detector_execution_verification_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M179_bounded_render_detector_execution_verification_v0/render_verification_coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M179_bounded_render_detector_execution_verification_v0/render_verification_frame_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M179_bounded_render_detector_execution_verification_v0/detector_manifest_repair_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M179_bounded_render_detector_execution_verification_v0/detector_verification_coverage.json`

Claim boundary:

- M179 verifies bounded render/detector execution only.
- M179 does not validate candidate reachability, evaluate ObjectNav goals, execute trajectories, or support real navigation `SR` / `SPL`.

## E008-M180

Implementation unit: `E008-M180_candidate_navmesh_source_readiness_validation_v0`.

- Status: `e008_m180_candidate_navmesh_source_readiness_validation_ready`.
- Candidate rows: 192.
- Path-ready candidates: 180.
- Source-ready scans: 8 / 8.
- Coordinate-valid rows: 192 / 192.
- Selected next unit: E008-M181 expanded candidate visit-order/path materialization.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m180_candidate_navmesh_source_readiness_validation.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M180_candidate_navmesh_source_readiness_validation_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M180_candidate_navmesh_source_readiness_validation_v0/candidate_navmesh_validation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M180_candidate_navmesh_source_readiness_validation_v0/scan_source_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M180_candidate_navmesh_source_readiness_validation_v0/report.md`

## E008-M181

Implementation unit: `E008-M181_expanded_candidate_visit_order_path_materialization_v0`.

- Status: `e008_m181_expanded_candidate_visit_order_path_materialization_ready`.
- Visit-order rows: 732.
- Scan-policy metric rows: 32.
- Path-ready candidates: 180.
- Leakage audit pass: true.
- Selected next unit: E008-M182 leakage-safe goal-evaluation proxy.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m181_expanded_candidate_visit_order_path_materialization.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M181_expanded_candidate_visit_order_path_materialization_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M181_expanded_candidate_visit_order_path_materialization_v0/candidate_visit_order_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M181_expanded_candidate_visit_order_path_materialization_v0/policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M181_expanded_candidate_visit_order_path_materialization_v0/report.md`

## E008-M182

Implementation unit: `E008-M182_leakage_safe_goal_evaluation_proxy_v0`.

- Status: `e008_m182_leakage_safe_goal_evaluation_proxy_ready`.
- Eval episode rows: 8.
- Candidate goal-eval rows: 732.
- Proxy recovery observed: true, 7 / 8 for all four policies.
- Leakage audit pass: true.
- Selected next unit: E008-M183 Docker trajectory execution contract/preflight.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m182_leakage_safe_goal_evaluation_proxy.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M182_leakage_safe_goal_evaluation_proxy_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M182_leakage_safe_goal_evaluation_proxy_v0/candidate_goal_eval_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M182_leakage_safe_goal_evaluation_proxy_v0/policy_goal_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M182_leakage_safe_goal_evaluation_proxy_v0/report.md`

## E008-M183

Implementation unit: `E008-M183_docker_trajectory_execution_contract_preflight_v0`.

- Status: `e008_m183_docker_trajectory_execution_contract_preflight_ready_runner_next`.
- Trajectory candidate rows: 732.
- Execution plan rows: 32.
- Eval goal / oracle rows: 8 / 8.
- Docker preflight pass: true.
- Selected next unit: E008-M184 Docker trajectory execution with `SR`, `SPL`, path length, visits.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m183_docker_trajectory_execution_contract_preflight.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M183_docker_trajectory_execution_contract_preflight_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M183_docker_trajectory_execution_contract_preflight_v0/trajectory_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M183_docker_trajectory_execution_contract_preflight_v0/docker_preflight_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M183_docker_trajectory_execution_contract_preflight_v0/report.md`

## E008-M184

Implementation unit: `E008-M184_docker_trajectory_execution_sr_spl_v0`.

- Status: `e008_m184_docker_trajectory_execution_sr_spl_ready`.
- Scan-policy rows: 32.
- Success rows: 28.
- Aggregate `SR`: 0.875.
- Mean `SPL`: 0.2411.
- Leakage audit pass: true.
- Selected next unit: E008-M185 protected detector-confidence interpretation and scale decision.

Command:

```bash
docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp -v /home/yoohyun/research3/local_dataset/data:/data:ro -v /home/yoohyun/research2:/work -w /work research3/habitat-h001:20260508-calib-artifacts bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m184_docker_trajectory_execution_sr_spl.py --m129-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M183_docker_trajectory_execution_contract_preflight_v0 --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M184_docker_trajectory_execution_sr_spl_v0 --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M184_docker_trajectory_execution_sr_spl_v0"
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M184_docker_trajectory_execution_sr_spl_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M184_docker_trajectory_execution_sr_spl_v0/dynamic_stale_trajectory_policy_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M184_docker_trajectory_execution_sr_spl_v0/pairwise_policy_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M184_docker_trajectory_execution_sr_spl_v0/report.md`

## E008-M185

Implementation unit: `E008-M185_protected_detector_confidence_interpretation_scale_decision_v0`.

- Status: `e008_m185_protected_detector_confidence_interpretation_scale_decision_ready`.
- Scale-up recommended: false.
- Method: `path_cost_ascending_reachable_subset_v0`, `SR` 0.875, `SPL` 0.1716.
- Protected baseline: `detector_confidence_reachable_subset_v0`, `SR` 0.875, `SPL` 0.2926.
- Decision: `method_not_yet_better_than_protected_baseline`.
- Selected next unit: repair source-pool policy before scale-up.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/interpret_m185_protected_detector_confidence_scale_decision.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M185_protected_detector_confidence_interpretation_scale_decision_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M185_protected_detector_confidence_interpretation_scale_decision_v0/policy_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M185_protected_detector_confidence_interpretation_scale_decision_v0/pairwise_delta_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M185_protected_detector_confidence_interpretation_scale_decision_v0/report.md`

## E008-M186

Implementation unit: `E008-M186_source_pool_protected_baseline_failure_decomposition_v0`.

- Status: `e008_m186_source_pool_protected_baseline_failure_decomposition_ready`.
- Method worse `SPL` rows: 6 / 8.
- Mean delta `SPL`: -0.1210.
- Mean delta `PathLengthM`: +19.81m.
- Mean delta `CandidateVisits`: +5.125.
- Root cause: `source_proxy_cost_is_not_execution_cost`.
- Repair policy: `confidence_protected_transition_cost_policy_v1`.
- Selected next unit: E008-M187 source-pool confidence-protected transition-cost repair row materialization.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m186_source_pool_protected_baseline_failure_decomposition.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M186_source_pool_protected_baseline_failure_decomposition_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M186_source_pool_protected_baseline_failure_decomposition_v0/episode_delta_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M186_source_pool_protected_baseline_failure_decomposition_v0/root_cause_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M186_source_pool_protected_baseline_failure_decomposition_v0/repair_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M186_source_pool_protected_baseline_failure_decomposition_v0/report.md`

Claim boundary:

- M186 diagnoses why direct source-pool scale-up is blocked.
- M186 does not materialize repaired rows, execute trajectories, or support final real navigation `SR` / `SPL`.

## E008-M187

Implementation unit: `E008-M187_source_pool_confidence_protected_transition_cost_materialization_v0`.

- Status: `e008_m187_source_pool_confidence_protected_transition_cost_materialization_ready`.
- Base source-pool candidate rows: 180.
- Transition matrix rows: 4,072 / 4,072.
- Candidate-policy rows: 900.
- Execution plan rows: 40.
- Selected policy: `confidence_protected_transition_cost_policy_v1`.
- Confidence bin width: 0.05.
- Selected changed episode orders: 8 / 8.
- Selected confidence-bin violations: 0.
- Leakage audit pass: true.
- Selected next unit: E008-M188 source-pool repaired policy leakage-safe goal-evaluation proxy.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m187_source_pool_confidence_protected_transition_cost_materialization.py
```

The command self-runs in Docker when `habitat_sim` is unavailable on the host:

```bash
docker run --rm --user 1001:1001 -e HOME=/tmp -v /home/yoohyun/research3/local_dataset/data:/data:ro -v /home/yoohyun/research2:/work -w /work research3/habitat-h001:20260508-calib-artifacts bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m187_source_pool_confidence_protected_transition_cost_materialization.py --inside-docker"
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M187_source_pool_confidence_protected_transition_cost_materialization_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M187_source_pool_confidence_protected_transition_cost_materialization_v0/transition_cost_matrix_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M187_source_pool_confidence_protected_transition_cost_materialization_v0/confidence_protected_candidate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M187_source_pool_confidence_protected_transition_cost_materialization_v0/trajectory_execution_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M187_source_pool_confidence_protected_transition_cost_materialization_v0/policy_order_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M187_source_pool_confidence_protected_transition_cost_materialization_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M187_source_pool_confidence_protected_transition_cost_materialization_v0/`

Claim boundary:

- M187 materializes repaired rows only.
- M187 does not compute goal recovery, `SR`, `SPL`, or final navigation performance.
- The selected policy may reorder candidates only inside a fixed 0.05 confidence bin.

## E008-M188

Implementation unit: `E008-M188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_v0`.

- Status: `e008_m188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_ready`.
- Candidate-goal eval rows: 900.
- Scan-policy rows: 40.
- Aggregate policy rows: 5.
- Selected policy: `confidence_protected_transition_cost_policy_v1`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- Selected proxy `SR` / `SPL`: 0.875 / 0.2449.
- Protected proxy `SR` / `SPL`: 0.875 / 0.2926.
- Leakage audit pass: true.
- Trajectory promotion gate pass: false.
- Selected next unit: E008-M189 source-pool repaired policy proxy failure decomposition.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_v0/candidate_goal_eval_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_v0/aggregate_policy_goal_metric_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_v0/pairwise_policy_delta_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_v0/`

Claim boundary:

- M188 uses `ObjectNav` goal/viewpoint fields only as evaluation labels.
- M188 reports leakage-safe proxy `SR`/`SPL`, not executed navigation `SR`/`SPL`.
- M188 does not support Docker trajectory promotion because the selected repaired policy ties protected `SR` but loses proxy `SPL`.

## E008-M189

Implementation unit: `E008-M189_source_pool_repaired_policy_proxy_failure_decomposition_v0`.

- Status: `e008_m189_source_pool_repaired_policy_proxy_failure_decomposition_ready`.
- Selected policy: `confidence_protected_transition_cost_policy_v1`.
- Protected baseline: `detector_confidence_reachable_subset_v0`.
- Selected/protected proxy `SR`: 0.875 / 0.875.
- Selected/protected proxy `SPL`: 0.2449 / 0.2926.
- Same success proposal rows: 7.
- Same-success delayed/costlier rows: 2.
- Same-success cheaper route rows: 1.
- Same-success tie rows: 4.
- Shared source-coverage/localization gap rows: 1.
- Method decision: reject transition repair as main policy, keep source-pool candidate generation, use protected detector confidence as current execution default.
- Selected next unit: E008-M190 source-pool protected-confidence method boundary and scale decision.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m189_source_pool_repaired_policy_proxy_failure_decomposition.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M189_source_pool_repaired_policy_proxy_failure_decomposition_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M189_source_pool_repaired_policy_proxy_failure_decomposition_v0/episode_decomposition_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M189_source_pool_repaired_policy_proxy_failure_decomposition_v0/root_cause_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M189_source_pool_repaired_policy_proxy_failure_decomposition_v0/method_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M189_source_pool_repaired_policy_proxy_failure_decomposition_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M189_source_pool_repaired_policy_proxy_failure_decomposition_v0/`

Claim boundary:

- M189 rejects `confidence_protected_transition_cost_policy_v1` as a positive navigation-improvement claim.
- M189 keeps source-pool candidate generation as useful, but ranking defaults to protected detector confidence until stronger success-likelihood evidence exists.
- M189 does not execute trajectories or support final real navigation `SR` / `SPL`.

## E008-M190

Implementation unit: `E008-M190_source_pool_protected_confidence_method_boundary_scale_decision_v0`.

- Status: `e008_m190_source_pool_protected_confidence_method_boundary_scale_decision_ready`.
- Kept method component: `fixed_budget_source_pool_candidate_generation`.
- Safe execution default: `detector_confidence_reachable_subset_v0`.
- Rejected repair policy: `confidence_protected_transition_cost_policy_v1`.
- Protected Docker `SR` / `SPL`: 0.875 / 0.2926.
- Selected repair proxy `SR` / `SPL`: 0.875 / 0.2449.
- Protected proxy `SR` / `SPL`: 0.875 / 0.2926.
- Transition repair positive claim supported: false.
- Immediate Docker trajectory launch: false.
- Selected next unit: E008-M191 source-pool protected-confidence scale-up contract.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m190_source_pool_protected_confidence_method_boundary_scale_decision.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M190_source_pool_protected_confidence_method_boundary_scale_decision_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M190_source_pool_protected_confidence_method_boundary_scale_decision_v0/method_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M190_source_pool_protected_confidence_method_boundary_scale_decision_v0/claim_evidence_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M190_source_pool_protected_confidence_method_boundary_scale_decision_v0/scale_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M190_source_pool_protected_confidence_method_boundary_scale_decision_v0/baseline_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M190_source_pool_protected_confidence_method_boundary_scale_decision_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M190_source_pool_protected_confidence_method_boundary_scale_decision_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M190_source_pool_protected_confidence_method_boundary_scale_decision_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M190_source_pool_protected_confidence_method_boundary_scale_decision_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M190_source_pool_protected_confidence_method_boundary_scale_decision_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M190_source_pool_protected_confidence_method_boundary_scale_decision_v0/`

Claim boundary:

- M190 supports only a method-boundary claim: source-pool candidate-source expansion remains useful, but execution should default to protected detector confidence until a stronger success-likelihood policy is proven.
- M190 rejects transition-cost repair as a positive navigation/search claim.
- M190 does not support final real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, deployable search policy, or human intent as a main claim.

## E008-M191

Implementation unit: `E008-M191_source_pool_protected_confidence_scaleup_contract_v0`.

- Status: `e008_m191_source_pool_protected_confidence_scaleup_contract_ready`.
- Selected scale denominator: `hm3d_val_mini_all_triggered_source_pool_scale_v1`.
- Triggered episode rows: 30.
- Scale scenes / categories: 2 / 6.
- Planned source poses / render rows: 240 / 960.
- Scale batches: 3.
- Selected method: `source_pool_plus_detector_confidence_reachable_subset_v1`.
- Primary ablation: `no_source_pool_detector_confidence_reachable_subset_v0`.
- Safe execution default: `detector_confidence_reachable_subset_v0`.
- Render/detector long job launch now: false.
- Docker trajectory execution now: false.
- Selected next unit: E008-M192 source-pool protected-confidence scale denominator materialization.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m191_source_pool_protected_confidence_scaleup_contract.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M191_source_pool_protected_confidence_scaleup_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M191_source_pool_protected_confidence_scaleup_contract_v0/scale_denominator_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M191_source_pool_protected_confidence_scaleup_contract_v0/m192_materialization_seed_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M191_source_pool_protected_confidence_scaleup_contract_v0/source_pool_budget_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M191_source_pool_protected_confidence_scaleup_contract_v0/baseline_ablation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M191_source_pool_protected_confidence_scaleup_contract_v0/metric_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M191_source_pool_protected_confidence_scaleup_contract_v0/leakage_audit_contract_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M191_source_pool_protected_confidence_scaleup_contract_v0/command_ledger_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M191_source_pool_protected_confidence_scaleup_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M191_source_pool_protected_confidence_scaleup_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M191_source_pool_protected_confidence_scaleup_contract_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M191_source_pool_protected_confidence_scaleup_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M191_source_pool_protected_confidence_scaleup_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M191_source_pool_protected_confidence_scaleup_contract_v0/`

Claim boundary:

- M191 supports only a scale-up contract/readiness claim.
- M191 does not support source-pool navigation improvement until M192+ materialization, leakage-safe proxy comparison, Docker trajectory execution, and no-source-pool ablation pass.
- M191 keeps transition-cost repair as a rejected/optional negative ablation, not a positive claim.

## E008-M192

Implementation unit: `E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0`.

- Status: `e008_m192_source_pool_protected_confidence_scale_denominator_materialization_ready`.
- Scale denominator: `hm3d_val_mini_all_triggered_source_pool_scale_v1`.
- Seed request rows: 30.
- Source pose rows: 240 / expected 240.
- Render plan rows: 960 / expected 960.
- Scale batches: 3.
- Source anchor request rows available: 30 / 30.
- Missing source-anchor rows: 0.
- Blocked input hit rows: 0.
- Render/detector long job launched: false.
- Selected next unit: E008-M193 source-pool scale navmesh/snap validation and render/detector launcher contract.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m192_source_pool_protected_confidence_scale_denominator_materialization.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0/source_pool_scale_request_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0/source_pool_observation_pose_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0/source_pool_render_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0/source_anchor_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0/missing_source_anchor_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0/blocked_input_audit_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0/scale_batch_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0/expected_render_file_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0/command_ledger_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0/`

Claim boundary:

- M192 supports only scale denominator/source-pose/render-plan materialization.
- M192 freezes the source-pool acquisition rows needed to compare `source_pool_plus_detector_confidence_reachable_subset_v1` against `no_source_pool_detector_confidence_reachable_subset_v0` after downstream gates.
- M192 does not support render/detector recovery, real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, deployable search policy, or human intent as a main claim.

## E008-M193

Implementation unit: `E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0`.

- Status: `e008_m193_source_pool_scale_navmesh_snap_launcher_contract_ready`.
- Scale request rows: 30.
- Source pose rows: 240.
- Snap-ready rows: 240 / 240.
- Source-ready rows for downstream validation: 238 / 240.
- Render plan rows: 960 / expected 960.
- Detector manifest rows: 30.
- Launcher input materialization rows: 6.
- Long-job command rows: 2.
- M194 gate ready: true.
- Render/detector jobs launched: false.
- Selected next unit: E008-M194 source-pool scale render/detector execution launch and verification.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m193_source_pool_scale_navmesh_snap_launcher_contract.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/snap_validation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/request_snap_render_coverage_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/source_pool_render_plan_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/source_pool_detector_manifest_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/source_pool_object_target_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/expected_file_summary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/launcher_input_materialization_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/readiness_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/long_job_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/m194_gate_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/reviewer_defense_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/route_decision_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/next_action_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/`

Claim boundary:

- M193 supports only snap validation and launcher/preflight readiness for the M192 scale denominator.
- M193 does not support detector candidate recovery, real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, deployable search policy, or human intent as a main claim.

## E008-M194

Implementation unit: `E008-M194_source_pool_scale_render_detector_execution_v0`.

- Status: `e008_m194_source_pool_scale_render_detector_execution_ready`.
- Render launch status: `e008_m194_render_launched`.
- Render verification status: `e008_m194_render_ready`.
- Ready render frames: 960 / 960.
- Detector manifests ready after render repair: 30 / 30.
- Detector launch status: `e008_m194_detector_launched`.
- Detector status: `e008_m194_detector_candidate_source_ready`.
- Detector prediction rows: 552.
- Coordinate candidate rows: 552.
- Pre-cap candidate rows: 8,867.
- Detector tmux session: completed.
- Detector log: `logs/20260613_111110_e008_m194_source_pool_detector.log`.
- Detector output: `experiments/E008_real_navigation_benchmark/artifacts/E008-M194_source_pool_scale_render_detector_execution_v0/detector`.
- Render/detector verification command: `python experiments/E008_real_navigation_benchmark/tools/verify_m194_source_pool_scale_render_detector_execution.py --require-ready`.
- Selected next unit: E008-M195 source-pool scale candidate navmesh/source-readiness validation.

Launch commands:

```bash
python experiments/E008_real_navigation_benchmark/tools/launch_m194_source_pool_scale_render_detector_execution.py --stage render
python experiments/E008_real_navigation_benchmark/tools/verify_m194_source_pool_scale_render_detector_execution.py --require-render-ready
python experiments/E008_real_navigation_benchmark/tools/launch_m194_source_pool_scale_render_detector_execution.py --stage detector
```

Exact tmux commands and expected files:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/long_job_command_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M194_source_pool_scale_render_detector_execution_v0/render_launch_coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M194_source_pool_scale_render_detector_execution_v0/detector_launch_coverage.json`

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M194_source_pool_scale_render_detector_execution_v0/render_launch_coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M194_source_pool_scale_render_detector_execution_v0/render_verification_coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M194_source_pool_scale_render_detector_execution_v0/render_verification_frame_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M194_source_pool_scale_render_detector_execution_v0/detector_manifest_repair_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M194_source_pool_scale_render_detector_execution_v0/detector_launch_coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M194_source_pool_scale_render_detector_execution_v0/detector_verification_coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M194_source_pool_scale_render_detector_execution_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M194_source_pool_scale_render_detector_execution_v0/report.md`
- `local_dataset/HM3D_navigation_bridge/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/rendered_frame_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/render_summary.json`

Claim boundary:

- M194 supports render/detector execution readiness for the source-pool scale denominator.
- Candidate navmesh validation, goal evaluation, real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, deployable search policy, and human-intent main claim remain blocked until downstream gates pass.

## E008-M195

Implementation unit: `E008-M195_source_pool_scale_candidate_navmesh_source_readiness_validation_v0`.

- Status: `e008_m195_source_pool_scale_candidate_navmesh_source_readiness_validation_ready_with_source_warnings`.
- Candidate rows: 552.
- Path-ready candidate rows: 523.
- Source-ready scans: 23 / 30.
- Source-gap scan rows: 7 (`source_gap_no_detector_candidate`).
- Coordinate-valid rows: 552 / 552.
- Selected next unit: E008-M196 source-pool scale candidate visit-order/path materialization.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m195_source_pool_scale_candidate_navmesh_source_readiness_validation.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M195_source_pool_scale_candidate_navmesh_source_readiness_validation_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M195_source_pool_scale_candidate_navmesh_source_readiness_validation_v0/candidate_navmesh_validation_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M195_source_pool_scale_candidate_navmesh_source_readiness_validation_v0/scan_source_boundary_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M195_source_pool_scale_candidate_navmesh_source_readiness_validation_v0/`

Claim boundary:

- M195 validates candidate coordinate/navmesh/source-readiness only.
- M195 does not evaluate ObjectNav goals or execute trajectories.

## E008-M196

Implementation unit: `E008-M196_source_pool_scale_candidate_visit_order_path_materialization_v0`.

- Status: `e008_m196_source_pool_scale_candidate_visit_order_path_materialization_ready_with_source_warnings`.
- Denominator scan rows: 30.
- Evaluated/source-ready scan rows: 23.
- Source-gap scan rows: 7.
- Visit-order rows: 2,121.
- Path-ready candidate rows: 523.
- Leakage audit pass: true.
- Selected next unit: E008-M197 source-pool scale leakage-safe goal-evaluation proxy.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m196_source_pool_scale_candidate_visit_order_path_materialization.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M196_source_pool_scale_candidate_visit_order_path_materialization_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M196_source_pool_scale_candidate_visit_order_path_materialization_v0/candidate_visit_order_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M196_source_pool_scale_candidate_visit_order_path_materialization_v0/policy_metric_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M196_source_pool_scale_candidate_visit_order_path_materialization_v0/`

Claim boundary:

- M196 materializes visit-order/path rows only; source-gap scan rows stay in the denominator.
- M196 does not claim source-gap recovery or real navigation `SR` / `SPL`.

## E008-M197

Implementation unit: `E008-M197_source_pool_scale_leakage_safe_goal_evaluation_proxy_v0`.

- Status: `e008_m197_source_pool_scale_leakage_safe_goal_evaluation_proxy_ready`.
- Full denominator scan rows: 30.
- Source-ready/source-gap scan rows: 23 / 7.
- Candidate-goal eval rows: 2,121.
- Source-pool protected detector-confidence proxy recovery: 17 / 30.
- Source-pool protected detector-confidence proxy `SR` / `SPL`: 0.5667 / 0.3235.
- Path-cost source-pool proxy `SR` / `SPL`: 0.5667 / 0.3830.
- Leakage audit pass: true.
- Selected next unit: E008-M198 source-pool scale proxy result interpretation and trajectory-execution decision.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/run_m197_source_pool_scale_leakage_safe_goal_evaluation_proxy.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M197_source_pool_scale_leakage_safe_goal_evaluation_proxy_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M197_source_pool_scale_leakage_safe_goal_evaluation_proxy_v0/candidate_goal_eval_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M197_source_pool_scale_leakage_safe_goal_evaluation_proxy_v0/source_pool_scale_scan_goal_metric_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M197_source_pool_scale_leakage_safe_goal_evaluation_proxy_v0/`

Claim boundary:

- M197 uses ObjectNav goal/viewpoint fields only as evaluation labels after policy rows are frozen.
- M197 reports proxy diagnostics, not executed navigation `SR` / `SPL`.

## E008-M198

Implementation unit: `E008-M198_source_pool_scale_proxy_result_interpretation_v0`.

- Status: `e008_m198_source_pool_scale_proxy_result_interpretation_ready`.
- Baseline artifact: `E008-M70_full_val_mini_detector_candidate_goal_evaluation_smoke_v0`.
- Protected no-source baseline proxy `SR` / `SPL`: 0.8000 / 0.3506.
- Source-pool protected detector-confidence proxy `SR` / `SPL`: 0.5667 / 0.3235.
- Delta proxy `SR` / `SPL`: -0.2333 / -0.0271.
- Path-cost source-pool proxy `SPL`: 0.3830, but proxy `SR` remains 0.5667.
- Docker trajectory execution promoted: false.
- Selected next unit: E008-M199 source-pool scale failure decomposition and candidate-generation repair decision.

Command:

```bash
python experiments/E008_real_navigation_benchmark/tools/plan_m198_source_pool_scale_proxy_result_interpretation.py
```

Artifacts:

- `experiments/E008_real_navigation_benchmark/artifacts/E008-M198_source_pool_scale_proxy_result_interpretation_v0/coverage.json`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M198_source_pool_scale_proxy_result_interpretation_v0/policy_comparison_rows.jsonl`
- `experiments/E008_real_navigation_benchmark/artifacts/E008-M198_source_pool_scale_proxy_result_interpretation_v0/decision_rows.jsonl`
- `local_dataset/HM3D_navigation_bridge/E008-M198_source_pool_scale_proxy_result_interpretation_v0/`

Claim boundary:

- M198 supports a negative scale boundary: source-pool scale candidate generation is not ready for trajectory promotion.
- M198 does not support source-pool navigation improvement, final real navigation `SR` / `SPL`, or final real RGB-D/open-vocabulary robustness.
