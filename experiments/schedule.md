# Schedule

Last updated: 2026-05-30

이 문서는 H001 main experiment implementation을 top-tier submission path로 확장하기 위한 실행 순서를 관리한다. 세부 실험 결과는 `experiments/`에 기록하고, 이 문서는 단계, gate, baseline 확장 방향만 관리한다.

## Current Direction

사실:

- Active direction: `CAND-001` / `Intent- and Staleness-Aware Semantic Mapping`.
- Active hypothesis: `H001_stale-object-memory`.
- Current stage: main experiment implementation.
- Final paper target: Direction B `Task-Aware Dynamic Semantic Mapping for Open-Vocabulary Search and Navigation`.
- Current path: use Direction A `Task-Conditioned Stale Semantic Memory` as the core method/backbone, then expand through real proposal/search bridge, external baselines, and search/navigation metrics.
- Current E003 status: E003-M75 direct current-rescan bridge is ready over 96 query rows; real RGB-D/open-vocabulary claim readiness remains false.
- Current E004 status: E004-M05 supports memory-trust claim strength `split_supported`; task-context-specific claim strength remains `limited_positive_not_label_broad`.
- Current E005/E007/E008 status: `ConceptGraphs` is the active converted positive external mapping baseline route. All 9 heldout scans have runtime output and query-level conversion, and H001 has been replayed on the same M38 heldout query contract. E005-M56-M101 completed the two-table robustness denominator contract through map-assisted fallback claim-boundary decision. E007-M01-M07 packaged the path-cost bridge as a paper-facing occupancy-grid proxy table. E008-M01-M45 completed real navigation source preflight through dynamic-stale overlay trajectory execution smoke, result interpretation / baseline alignment, budget-matched repair/source-gap contract, repaired row materialization/execution, result interpretation/scale decision, source-diverse policy redesign contract, source-diverse row materialization, and source-diverse trajectory execution contract/Docker preflight. E008-M45 fixes Docker-ready execution for `h001_task_conditioned_source_diverse_budget5_v1` and matched baselines; scale-up is blocked and E008-M46 trajectory execution smoke is next.

에이전트 추론:

- Current core direction is aligned with recent work on open-vocabulary semantic mapping, 3D scene memory, task-driven mapping, and embodied navigation.
- Direction B is the correct final top-tier target, but the immediate implementation should remain focused on Direction A's memory-decision core to avoid an unfocused system paper.
- Human intent should remain a controlled task-context condition unless a dedicated context-sensitive utility benchmark shows broad gains over context-agnostic memory trust.
- Top-tier competitiveness requires moving beyond `3RScan` / `3DSSG` proxy evidence into stronger external baselines and downstream search/navigation evaluation.

## Top-Tier Target Claim

논문 주장 후보:

- `Task-Conditioned Stale Semantic Memory Update` improves dynamic object search/navigation by modulating memory trust, re-observation priority, and candidate visit order under object movement and perception noise.
- The method should improve `ExpectedSearchCost`, `SR`, `SPL` or `AttemptSPL`, stale old-location false positives, and proposal-aware search robustness.

논문 주장:

- Final claim should include real RGB-D / open-vocabulary proposal robustness and a search/navigation bridge, not only annotation-proxy stale memory behavior.
- Direction B is the final target claim family; Direction A is the core method claim that must survive ablation and bridge tests.
- Human task context is not yet a main contribution claim. The current defensible phrasing is that structured task context is a conditioning signal for memory trust and re-observation, not that the system understands human intent.

## Schedule

| Phase | Goal | Main output | Gate |
| --- | --- | --- | --- |
| E003-M39 | Temporal/spatial support instrumentation | Complete: support fields, runner insertion point, and verification plan fixed | No long rerun until schema and verification command are fixed |
| E003-M40 | Proposal-quality runner smoke | Complete: support fields implemented and short Docker smoke passed | Support fields must appear in validated proposal output |
| E003-M41 | Support-aware selection policy gate | Complete: selected `confidence_sqrt_depth_support_temporal_v0` | No long rerun until policy contract and success checks are fixed |
| E003-M42 | Support-aware selection runner smoke | Complete: selected score mode implemented and short Docker smoke passed | Validator must pass and support-aware score mode must be recorded |
| E003-M43 | Support-aware scaled rerun route gate | Complete: selected `pre_cap_candidate_pool_export_then_offline_replay_v0` | No immediate long rerun because existing artifacts cannot support score ablation |
| E003-M44 | Pre-cap candidate-pool export and offline replay harness | Complete: exported 629 support-instrumented candidates and reproduced runner selection offline | Replay reproduced runner selected stable-candidate set |
| E003-M45 | Scaled candidate-pool export and support-aware replay | Complete: 60,435 candidate pool rows, replay ready, frozen verdict `fail_redesign` | Support-aware score lost targets, added false positives, and failed hard/weak criteria |
| E003-M46 | Support-aware redesign or external proposal baseline gate | Complete: 12 local score policies swept, hard pass 0, weak positive 0 | Selected `external_proposal_baseline_gate_first` |
| E003-M47 | External proposal/mapping baseline feasibility gate | Complete: selected `Grounded-SAM` over `OpenMask3D`, `ConceptGraphs`, `OVIR-3D`, `HOV-SG` | First route must diagnose whether box-depth projection is the current proposal bottleneck |
| E003-M48 | `Grounded-SAM` mask-backprojection contract | Complete: `grounded_sam_mask_backproject_v0` input/output contract, blocked inputs, optional mask fields, and long-running job policy fixed | No result claim; implementation smoke remains next |
| E003-M49 | `Grounded-SAM` Docker/model smoke | Complete: mask-depth rows emitted, validator passed, M21 matcher passed | Implementation smoke only |
| E003-M50 | Same-subset bbox-depth vs mask-depth comparison gate | Complete: bbox-depth beat mask-depth on matched targets, precision, recall, and centroid error | Do not scale `Grounded-SAM` yet |
| E003-M51 | Post-M50 route decision | Complete: selected artifact-local `Grounded-SAM` mask failure analysis | Must avoid spending compute on a route with negative same-subset evidence |
| E003-M52 | `Grounded-SAM` mask failure analysis | Complete: target loss is mask projection dropout and centroid worsening is match-set composition | Do not scale current `Grounded-SAM` route as-is |
| E003-M53 | Bbox-depth continuation and failure-boundary repair gate | Complete: selected search-critical bbox-depth failure-boundary audit | Must preserve the stronger current route while keeping external baseline expansion open |
| E003-M54 | Search-critical bbox-depth failure-boundary audit | Complete: exact current query-instance joins 0, label-level bridge risk identified | Current detector failures cannot yet be used as direct search-decision evidence |
| E003-M55 | Dynamic-pair-aligned real-proposal bridge gate | Complete: selected search-failure current-rescan staging first | Must stage current-rescan sequence payloads before detector output can be evaluated against E001/E002 rows |
| E003-M56 | Current-rescan sequence payload staging plan | Complete: fixed target scan list, command, output paths, logs, and verification for 4 current rescans | Use long-running/background task rule for download/decompression |
| E003-M57 | Current-rescan sequence staging background job | Complete: launched M56 command in `tmux`, recorded job status/log path, and verified 4 / 4 payloads ready | Direct detector bridge design can start |
| E003-M58 | Direct current-rescan detector/evaluation bridge design | Complete: 7 query rows, 5 unique bridge targets, 4 scans, `chair`/`pillow` prompt set, M59 command plan | No real RGB-D search claim until detector bridge output is evaluated |
| E003-M59 | Direct current-rescan detector bridge Docker run | Complete: 93 frames, 96 proposals, validator errors/warnings 0 / 0, matched 21, false positives 75 | Query-level bridge evaluation required before search claim |
| E003-M60 | Direct current-rescan query-level bridge evaluation | Complete: 3 / 7 query targets detected, `detector_task_budget_v0` success 0 / 7 | Budget/rank gap blocks real RGB-D search claim |
| E003-M61 | Direct bridge rank/failure analysis gate | Complete: detector recall miss 4, task-budget mismatch 2, false-positive rank failure 1 | Selected `proposal_rerank_then_openmask3d_feasibility` |
| E003-M62 | Offline proposal rerank/budget repair sweep | Complete: best deployable unbounded repair 3 / 7, bounded top-5/adaptive repair 2 / 7 | Selected bounded repair integration before `OpenMask3D` |
| E003-M63 | Bounded rerank/budget repair integration gate | Complete: bounded repair ablation ready, unique rerank gain false, unbounded upper-bound only | Selected `openmask3d_feasibility_gate_next` |
| E003-M64 | `OpenMask3D` feasibility decision gate | Complete: target-undetected rows 4, minimal-input-ready scans 4 / 4 | Selected `openmask3d_scene_format_model_smoke_plan_next` |
| E003-M65 | `OpenMask3D` scene-format/model smoke plan | Fix scene-format manifest, command plan, adapter contract, and verification command | No Docker/model run until background/log/output/verification contract is fixed |
| E004-M01 | Task-context memory trust contract | Fix task context fields for memory trust / re-observation decision | Natural language parser remains adapter, not main claim |
| E004-M02 | Task-conditioned re-observation/search policy | Evaluate task-conditioned policy under stale memory + proposal noise | Must beat static memory, fixed top-k, and detector-confidence-first |
| E005-M49 | Full heldout metric aggregation | Complete: all 9 heldout `ConceptGraphs` scans aggregated, strict bbox top5 114 / 195 | External baseline still needs H001 comparison on the same query contract |
| E005-M50 | H001-vs-`ConceptGraphs` comparison gate | Complete: direct common query rows 0, paired superiority not ready from original universes | Replay H001 on the `M38` heldout query contract |
| E005-M51 | H001 heldout replay contract | Complete: 195 / 195 heldout query rows adapter-ready, issues 0 | No result claim until H001 replay is run |
| E005-M52 | H001 heldout policy replay | Complete: H001 172 / 195, `ConceptGraphs` 114 / 195, static memory 141 / 195, context-agnostic 171 / 195 | Paired failure/table decision required before paper claim |
| E005-M53 | Paired failure analysis / paper-table decision | Complete: H001-vs-`ConceptGraphs` and H001-vs-static proxy-search claims ready; task-context main claim not ready | Do not claim human intent as the main contribution |
| E005-M54 | Paper-table claim ledger / method claim rewrite | Complete: paper-facing table, allowed claims, blocked claims, and method framing fixed | Main claim centers memory trust, staleness handling, and bounded re-observation |
| E005-M55 | Real RGB-D/open-vocabulary robustness expansion gate | Complete: selected `robustness_denominator_contract_then_open3dsg_audit` | Real RGB-D robustness remains blocked |
| E005-M56 | Robustness denominator + `Open3DSG` audit | Complete: Table A proxy-search denominator 195 rows, Table B real RGB-D proposal bridge denominator 96 rows, `Open3DSG_staged` read-only audit passed | No `Open3DSG` performance claim before query-level conversion |
| E005-M57 | `Open3DSG` output schema inspection / query-conversion contract | Complete: relation raw dump ready, feature/checkpoint route feasible, object candidate export needed | No `Open3DSG` object-search claim before candidate rows exist |
| E005-M58 | `Open3DSG` object-candidate dump/export smoke plan | Complete: read-only Docker command, object-candidate schema, local output path, export contract, and verifier fixed | No `Open3DSG` object-search claim before one-batch candidate rows exist |
| E005-M59 | `Open3DSG` object-candidate export hook / one-batch Docker smoke | Complete: lower-memory relaunch ready, 180 object-candidate rows, completed batches 1 | Input to M60/M61 coverage diagnosis |
| E005-M60 | `Open3DSG` query-level conversion | Complete after M61 rerun and target-geometry loader fix: 195-row denominator, 7,600 object candidates, 759 query/eval candidate rows, 585 policy rows, strict 81 / 195 | Primary-label adapter below `ConceptGraphs` |
| E005-M61 | Targeted `Open3DSG` denominator-aligned batch export | Complete: all 9 query scans, 51 target subgraphs, 7,600 object-candidate rows, source modified false | Input to M60 rerun |
| E005-M62 | `Open3DSG` result interpretation | Complete after corrected M60: bridge feasibility true, main-table performance baseline false, H001 strict margin +91 | Input to M63 |
| E005-M63 | `Open3DSG` route decision | Complete: diagnostic predicted-term strict 144 / 195, selected bounded repair next | M64 completed the policy verification |
| E005-M64 | `Open3DSG` leakage-safe vocabulary policy | Complete: strict 144 / 195, relaxed 147 / 195, leakage audit pass | Input to M65 paper-table boundary decision |
| E005-M65 | `Open3DSG` paper-table integration boundary | Complete: include predicted-vocabulary adapter row, exclude primary-label adapter from main table, human intent secondary | Input to E005-M66 failure-boundary rows |
| E005-M66 | External-baseline failure-boundary rows | Complete: H001-only 60 vs `ConceptGraphs`, H001-only 39 vs `Open3DSG` vocab, task-context gain 1 | Input to E005-M67 robustness route decision |
| E005-M67 | Real RGB-D/open-vocabulary robustness route decision | Complete: selected `scale_real_proposal_bridge_to_m38_heldout_denominator`, denominator gap 195 vs 96 rows | Input to E005-M68 full-denominator bridge plan |
| E005-M68 | Full-denominator real proposal bridge plan | Complete: 195 rows, 9 ready scans, 65 object targets, 22 prompt labels, 214 sampled frames, 3 heldout batches | Input to E005-M69 detector batch launch |
| E005-M69 | Full-denominator real proposal detector batch launch | Complete: `heldout_b01` launched in tmux `e005_m69_real_proposal_heldout_b01` | Input to E005-M70 completion verification |
| E005-M70 | `heldout_b01` detector completion verification | Complete: expected files 12/12, prediction rows 261, matched targets 18/22, recall 0.8182, precision 0.0690, false-positive rate 0.9310 | Input to E005-M71 query-level metric conversion |
| E005-M71 | `heldout_b01` real proposal query-level conversion | Complete: target detected 54/66, H001 48/66, context-agnostic 48/66, `ConceptGraphs` same-batch 45/66 | Input to E005-M72 remaining batch launch |
| E005-M72 | Remaining real proposal detector batch launch | Complete: `heldout_b02` and `heldout_b03` launched sequentially | Input to E005-M73 verification |
| E005-M73 | Remaining detector completion verification | Complete: b02 expected files 12/12, prediction rows 264, matched targets 14/17; b03 expected files 12/12, prediction rows 400, matched targets 16/20 | Input to E005-M74 conversion |
| E005-M74 | Remaining query-level conversion | Complete: b02 target detected 42/69, H001 54/69; b03 target detected 48/60, H001 55/60 | Input to E005-M75 aggregate |
| E005-M75 | Real-proposal aggregate route | Complete: 195 rows, target detected 144/195, H001 157/195, context-agnostic 156/195, `ConceptGraphs` same-batch 114/195 | Input to E005-M76 claim-boundary decision |
| E005-M76 | Real-proposal claim-boundary decision | Complete: diagnostic table ready, final robustness blocked, selected `include_diagnostic_table_then_offline_detector_prompt_repair` | Input to E005-M77 offline repair design |
| E005-M77 | Offline detector/prompt repair design | Complete: pre-cap targets 54/65 vs current 48/65, best offline top5 60/195 vs current 51/195 | Input to E005-M78 fixed replay implementation |
| E005-M78 | Fixed offline repair replay | Complete: M77 best policy reproduced with 0 mismatches, top5 60/195, target detected 147/195, precision 0.105832 | Input to E005-M79 runner insertion / targeted rerun plan |
| E005-M79 | Runner insertion point and targeted repair rerun plan | Complete: runner source edit required false, `confidence_log_depth` score mode, first rerun batch `heldout_b02` | Input to E005-M80 targeted detector rerun launch |
| E005-M80 | Confidence-log-depth targeted detector rerun launch | Complete: `heldout_b02` launched in tmux `e005_m80_confidence_log_depth_heldout_b02` | Input to E005-M81 verification |
| E005-M81 | Confidence-log-depth detector completion verification | Complete: expected files 14 / 14, prediction rows 264, matched targets 14 / 17, precision 0.053030 | Input to M82 query metrics |
| E005-M82 | Confidence-log-depth query-level metric conversion | Complete: b02 detector top5 15 / 69, task-budget 7 / 69, target detected 42 / 69 | Input to M83 remaining-batch decision |
| E005-M83 | Confidence-log-depth rerun interpretation | Complete: b02 reproduction supports only limited ranking repair; b01/b03 reruns skipped now | Input to E005-M84 prompt/label recall repair or external proposal route decision |
| E005-M84 | Prompt/label recall repair or external proposal route decision | Complete: selected prompt/label recall audit first; external proposal route remains later | Input to E005-M85 prompt/label recall miss audit and repair contract |
| E005-M85 | Prompt/label recall miss audit and repair contract | Complete: no-same-label candidate 5, localization/matcher audit 5, broad/missing label 1; leakage-safe repair contract fixed | Input to E005-M86 prompt repair preflight or visibility/matcher audit |
| E005-M86 | Prompt repair preflight or visibility/matcher audit | Complete: bounded prompt repair preflight false; visibility/matcher 5 targets / 15 rows, zero-written scan 5 targets / 15 rows, broad contract 1 target / 3 rows | Input to E005-M87 candidate-survival / match-threshold / zero-written scan audit |
| E005-M87 | Candidate survival / match-threshold / zero-written scan audit | Complete: strict pre-cap suppressed 0, selected 1.5m recovery 2 targets / 6 rows, pre-cap 1.5m recovery 3 targets / 9 rows, zero-written scan 5 targets / 15 rows | Input to E005-M88 zero-written trace |
| E005-M88 | Zero-written raw-label trace / post-filter instrumentation audit | Complete: `569d8f0f` M69/M80 raw/projected/written 513 / 483 / 0, active label `chair`, prompt has `chair=true`, pre-cap rows 0, likely loss at prompt-label cleanup | Exact drop reason unavailable without raw-label trace |
| E005-M89 | Target-independent cleanup-trace runner patch / `heldout_b02` trace rerun | Complete: verification status `e005_m89_cleanup_trace_detector_batch_ready`; analysis status `e005_m89_cleanup_trace_analysis_ready`; trace rows 483, all drop, `drop_not_scan_prompt_label` 479, canonical `stool` 479, active scan label `chair`, blocked-field hits 0 | Input to E005-M90 label-normalization / scan-prompt scope repair decision |
| E005-M90 | Label-normalization / scan-prompt scope repair decision | Complete: selected `active_scan_exact_label_precedence_v0`; rejected `scan_prompt_scope_expand_stool_for_chair_scan_v0`; active-exact replay keep rows 479 / 483; blocked-field hits 0; upper-bound selected proposals 24 | Input to E005-M91 active-label precedence runner patch / one-scan cleanup smoke |
| E005-M91 | Active-label precedence runner patch / one-scan cleanup smoke | Complete: M89 pre-cap/final 0 / 0 -> M91 479 / 24; cleanup keep/drop 479 / 4; cap respected; matched target rows 5 / 5; precision 0.208333 | Input to E005-M92 decision |
| E005-M92 | Active-label precedence query/rerun decision | Complete: affected query rows 15; target detected 0 -> 15; detector top5 lower-bound +3; task-budget lower-bound +2; H001 delta 0; `chair`/`stool` side-effect risk 1 scan / 15 rows / 3 `stool` rows | Input to E005-M93 bounded b02 rerun |
| E005-M93 | Bounded `heldout_b02` active-label precedence rerun / result analysis | Complete: target detected 42 / 69 -> 57 / 69; detector top5 15 / 69 -> 18 / 69; detector task-budget 7 / 69 unchanged; H001 54 / 69 unchanged; side-effect observed false | Input to E005-M94 |
| E005-M94 | Active-label precedence claim-boundary / broader repair decision | Complete: selected `stop_and_record_m93_as_batch_level_repair_diagnostic`; diagnostic projection target detected 159 / 195, detector top5 60 / 195, detector task-budget 26 / 195, H001 157 / 195 | Input to E005-M95 |
| E005-M95 | Paper-facing real-proposal diagnostic table and final E005 boundary refresh | Complete: 7 main diagnostic rows, 4 repair rows, 2 allowed diagnostic claims, 4 blocked claims | Input to E005-M96 |
| E005-M96 | Next expansion route decision | Complete: selected `external_proposal_mapping_baseline_first`; navigation/search bridge deferred | Input to E005-M97 |
| E005-M97 | External proposal/mapping baseline feasibility matrix | Complete: selected `conceptgraphs_derived_map_candidate_route`; `Open3DSG` supporting, `OpenMask3D` environment-blocked, `HOV-SG` source-audit required | Input to E005-M98 |
| E005-M98 | `ConceptGraphs`-derived proposal/map reliability smoke | Complete: `ConceptGraphs` strict top5 114 / 195, real detector top5 51 / 195, real detector task-budget 24 / 195, H001 157 / 195; H001 recovers both map/top5 failure 54 rows; map-only H001 failure 24 rows | Input to E005-M99 |
| E005-M99 | Row-group inspection / heavier external route decision | Complete: selected `map_assisted_h001_repair_first`; H001 failure 38 rows / 13 targets; `ConceptGraphs` repair candidate 24 rows / 8 targets; H001-or-`ConceptGraphs` upper bound 181 / 195 | Input to E005-M100 |
| E005-M100 | `ConceptGraphs`-assisted H001 fallback policy smoke | Complete: selected `h001_then_conceptgraphs_top5_on_observed_miss_v0`; success 181 / 195; `AttemptSPL` 0.798675; mean cost 2.435897 | Input to E005-M101 |
| E005-M101 | Map-assisted fallback claim-boundary / navigation-bridge decision | Complete: selected `paper_table_integration_and_navigation_bridge_next`; paper-table integration ready true; next E007-M01 | Input to E007 |
| E007-M01 | Navigation/path-cost bridge contract | Complete: M100/E002 row overlap 195 / 195; E002 target-grid reachable overlap 186 / 195; `ConceptGraphs` query overlap 195 / 195; selected `e002_occupancy_grid_astar_v0` | Input to E007-M02 |
| E007-M02 | Path-source compatibility / candidate-route materialization audit | Complete: 1,170 query-policy rows, 3,814 route rows, 705 projection-ready rows, 3,097 external projection-pending rows, 36 source gap rows | Input to E007-M03 |
| E007-M03 | External candidate grid projection / path-cost route computation | Complete: route projection-ready 3,785 / 3,814, route path-ready 3,331 / 3,814, query-policy eval-ready 928 / 1,170, no-route query-policy rows 36 | Input to E007-M04 |
| E007-M04 | Path-cost policy metric evaluation | Complete: source-ready 972 / 1,170; method source-ready success 163 / 174; mean path cost 2.996131m; mean `PathAttemptSPLProxy` 0.824554; paired delta vs H001-only success +0.054545 / `PathAttemptSPLProxy` +0.004390 / cost +0.941948m | Input to E007-M05 |
| E007-M05 | Path-cost result interpretation / paper-table boundary | Complete: selected paper-facing occupancy-grid path-cost bridge table; main navigation table false; `OldLocationDeadEndCostM` primary false | Input to E007-M06 |
| E007-M06 | Path-start/source-limit sensitivity and reviewer-defense audit | Complete: source-limited 198 / 1,170; stop-rank 47 / 1,170; old-first non-target zero-step 153; bridge table defensible with proxy boundary true | Input to E007-M07 |
| E007-M07 | Bridge-table package and navigation-expansion decision | Complete: final E007 bridge table, claim ledger, reviewer defense, and navigation expansion decision packaged | Input to E008-M01 |
| E008-M01 | Real navigation benchmark/source preflight and episode contract | Complete: selected local read-only `HM3D ObjectNav` + `Habitat`; fixed episode schema, allowed/blocked inputs, metrics, baselines, and no-launch gate | Input to E008-M02 |
| E008-M02 | `HM3D ObjectNav` episode/source adapter smoke | Complete: 6 episode rows, 2 scenes, 6/6 scene/navmesh ready, Docker `Habitat` pathfinder smoke success | Input to E008-M03 |
| E008-M03 | `H001` candidate-to-navigation adapter contract | Complete: candidate schema/leakage guard fixed; eval goal rows ready 6/6; H001 `HM3D` candidate-source rows 0 | Input to E008-M04 |
| E008-M04 | `ObjectNav` goal/viewpoint oracle path smoke | Complete: viewpoint paths 6/6, goal-snapped paths 4/6, oracle metric plumbing ready | Input to E008-M05 |
| E008-M05 | `HM3D` candidate-source staging plan | Complete: selected annotation-derived semantic candidate-source smoke after semantic files 2/2 scenes and label support 6/6 rows | No full benchmark run |
| E008-M06 | `HM3D` semantic annotation candidate-source smoke | Complete: label support 6/6 but Habitat nonzero-AABB 0/2 scenes and GLB geometry mapping 0/2 scenes; candidate rows 0 | Do not use ObjectNav goal/viewpoint leakage |
| E008-M07 | `HM3D` rendered RGB-D detector candidate-source plan | Complete: 24 start-pose yaw-sweep render rows, 6 detector manifest rows, 5 labels, `Habitat` / `real-smoke` readiness, M09 command plan | Input to E008-M08 |
| E008-M08 | `HM3D` rendered RGB-D frame staging smoke | Complete: 24/24 rendered RGB-D/pose rows, 6/6 detector-compatible sequence dirs, detector input files ready | Input to E008-M09 |
| E008-M09 | `HM3D` rendered RGB-D detector candidate smoke | Complete: 137 detector candidate rows, 137 coordinate candidate rows, 409 pre-cap rows, validator errors/warnings 0/0 | Input to E008-M10 |
| E008-M10 | Detector candidate coordinate-frame / snap-to-navmesh validation | Complete: candidate rows 137, join-ready 137/137, snapped navigable 136/137, source-to-snapped paths 125/137, warning/failure rows 12 | Input to E008-M11; no navigation `SR` / `SPL` claim before execution rows exist |
| E008-M11 | Reachable-subset detector candidate visit-order path smoke | Complete: 512 visit-order rows, 28 policy metric rows, 12 explicit failure rows; `path_cost_ascending_reachable_subset_v0` mean first-ready cost 0.791484m | Input to E008-M12; no deployable policy claim before leakage-safe goal evaluation / execution rows exist |
| E008-M12 | Leakage-safe detector candidate goal-evaluation smoke | Complete: 512 candidate-goal eval rows, leakage audit pass, primary `GoalEvalProxySR` 3/6 for all policies, `goal_xz_1p0` 1/6 | Input to E008-M13; no navigation `SR` / `SPL` claim before simulator execution rows exist |
| E008-M13 | Detector-goal failure audit and observation-coverage expansion decision | Complete: 3 all-policy failure episodes, 2 pre-cap target-region misses, 1 near-miss localization threshold case, 0 post-cap/snap suppression cases; selected non-oracle observation coverage expansion | No full simulator benchmark until non-oracle target coverage is expanded and re-audited |
| E008-M14 | Non-oracle observation-coverage expansion plan | Complete: 54 observation poses, 216 expanded render rows, 36 frames per episode, selected `bounded_start_neighborhood_multiview_v0` | Input to E008-M15; must not use `ObjectNav` goal/viewpoints, success labels, or candidate-to-goal distance as policy input |
| E008-M15 | Non-oracle observation expansion frame staging / snap validation | Complete: 216/216 ready frames, 6/6 ready scans, 216/216 snap-ready rows, 8 large snap warnings | Input to E008-M16 detector rerun; no navigation `SR` / `SPL` claim before candidate-goal and trajectory execution rows |
| E008-M16 | Non-oracle observation expansion detector candidate smoke | Complete: 216 frame rows, 4,009 raw predictions, 214 coordinate candidate rows, 3,801 pre-cap candidate rows | Input to E008-M17; no eval goal/viewpoint policy input |
| E008-M17 | Expanded detector candidate navmesh validation | Complete: 214/214 coordinate-valid, 213/214 snapped navigable, 189/214 source-to-snapped paths, every scan path-ready | Input to E008-M18; path warnings retained |
| E008-M18 | Expanded detector candidate visit-order path smoke | Complete: 781 visit-order rows, 28 policy metric rows, reachable-subset top1-ready 6/6 scans | Input to E008-M19; still not real navigation `SR` / `SPL` |
| E008-M19 | Expanded leakage-safe detector candidate goal-evaluation smoke | Complete: 781 candidate-goal eval rows, `any_viewpoint_xz_1p0` proxy hit 6/6, `goal_xz_1p0` proxy hit 4/6, leakage audit pass | Input to E008-M20; still not real navigation `SR` / `SPL` |
| E008-M20 | Expanded detector-goal failure comparison / navigation-execution decision | Complete: M12 failure rows 12 -> M19 0, gate counts pass 3 / warning 4 / fail 2, selected trajectory-execution contract next | Input to E008-M21; H001 source and trajectory metrics still missing |
| E008-M21 | Expanded detector-policy trajectory execution contract / Docker preflight | Complete: contract ready true, Docker preflight pass 6 / warning 1, policy execution plan rows 24, M22 runner missing | Input to E008-M22; real `SR` / `SPL` still false |
| E008-M22 | Expanded detector-policy trajectory execution smoke | Complete: trajectory rows 372, scan-policy rows 24, aggregate rows 4, leakage audit pass, detector-policy smoke `SR` 1.0, `SPL` 0.303595-0.410800 | Input to E008-M23; final H001 navigation claim still false |
| E008-M23 | Trajectory-vs-proxy consistency and H001 candidate-source decision | Complete: success agreement 24/24, proxy `SPL` order consistency 0/4, H001 candidate-source rows 0 | Input to E008-M24; instantiate H001 source before scaling navigation |
| E008-M24 | H001 candidate-source instantiation contract | Complete: initial memory-proxy 137 rows / 125 path-ready, current-observation 214 rows / 189 path-ready, task-context rows 18, leakage pass true | Input to E008-M25; materialize H001 rows before execution/scaling |
| E008-M25 | H001 candidate-source materialization smoke | Complete: H001 candidate-source rows 1,053, query context rows 18, policy execution plan rows 90, ready rows 72, blocked rows 18, leakage pass true | Input to E008-M26; build H001 visit-order/path rows before trajectory execution |
| E008-M26 | H001 visit-order/path smoke | Complete: H001 candidate visit-order rows 252, policy path metric rows 77, evaluated ready policy plans 72, blocked external-map/runtime-event rows 18, leakage pass true | Input to E008-M27; evaluate H001 visit rows against eval-only goals without policy leakage |
| E008-M27 | H001 leakage-safe goal-evaluation smoke | Complete: candidate-goal eval rows 252, scan-policy rows 72, aggregate policy rows 4, leakage pass true, primary `GoalEvalProxySR` detector confidence 0.500000 / H001 0.333333 / context-agnostic 0.333333 / static 0.000000 | Input to E008-M28; compare H001 failures before trajectory execution |
| E008-M28 | H001 goal-evaluation comparison / trajectory decision | Complete: H001 6/18, detector confidence 9/18, context-agnostic 6/18, static 0/18; detector-only rows 3, H001-only rows 0; trajectory gate pass 2 / warning 1 / fail 4 | Input to E008-M29; repair current-observation fallback/source before trajectory execution |
| E008-M29 | H001 current-observation fallback/source repair contract | Complete: backstop plan rows 18, repair opportunity rows 12, detector-only recoverable rows 3, all-policy source-gap rows 9, allowed/blocked input rows 28/22 | Input to E008-M30; replay fallback before trajectory execution |
| E008-M30 | H001 current-observation fallback replay smoke | Complete: repaired H001 `GoalEvalProxySR` 9/18 vs H001 6/18 vs detector 9/18; recovered rows 3; success-loss 0; remaining source-gap 9; repaired `GoalEvalProxySPL` 0.291005 vs detector 0.381619 | Input to E008-M31; define bounded trajectory contract and source-gap boundary |
| E008-M31 | H001 fallback trajectory-execution contract / source-gap boundary | Complete: sanitized candidate visit rows 141; execution plan rows 18; source-gap boundary rows 9; policy leakage pass true; no proxy-success filtering | Input to E008-M32; implement Docker H001 fallback trajectory runner |
| E008-M32 | H001 fallback trajectory execution smoke | Complete: Docker inside true; trajectory attempt rows 104; scan-task metrics 18; `SR` 0.5; `SPL` 0.141996; proxy/trajectory success agreement 18/18; source-gap success 0/9 | Input to E008-M33; interpret result and align detector/H001 baselines |
| E008-M33 | H001 trajectory result interpretation / baseline alignment | Complete: baseline alignment ready; H001 vs primary detector `SR` delta -0.5 and `SPL` delta -0.268804; source-gap H001 `SR` 0.0 vs detector `SR` 1.0 | Input to E008-M34; design dynamic-stale navigation benchmark/source intervention before scaling |
| E008-M34 | Dynamic-stale navigation benchmark / source-intervention contract | Complete: selected `hm3d_counterfactual_stale_overlay_v0`, intervention plan rows 18, source-gap diagnostic rows 9, final navigation result false | Input to E008-M35; materialize dynamic-stale overlay rows before any scale-up |
| E008-M35 | Dynamic-stale overlay row materialization smoke | Complete: intervention rows 18, policy execution plan rows 90, candidate rows 924, source-gap plan rows 45, leakage pass true | Input to E008-M36; adapt trajectory runner before dynamic-stale `SR` / `SPL` |
| E008-M36 | Dynamic-stale overlay trajectory contract / runner adaptation | Complete: trajectory candidate rows 924, execution plan rows 90, execute-in-runner rows 90, runner `py_compile` pass true, Docker image inspect pass true, leakage pass true | Input to E008-M37; execute dynamic-stale overlay trajectories before any `SR` / `SPL` claim |
| E008-M37 | Dynamic-stale overlay trajectory execution smoke | Complete: Docker trajectory attempts 467, scan-task-policy rows 90, H001 `SR` 0.5 / `SPL` 0.141996, detector confidence `SR` 1.0 / `SPL` 0.407894, leakage pass true | Input to E008-M38; interpret negative/limited H001 navigation result before scaling |
| E008-M38 | Dynamic-stale overlay result interpretation / baseline alignment | Complete: H001 beats static memory but not detector confidence, fixed current top-k efficiency, or task-agnostic memory trust; scale-up recommended false | Input to E008-M39; repair policy/source-gap contract before scaling |
| E008-M39 | Budget-matched dynamic-stale policy repair / source-gap contract | Complete: primary budget cap 5, source-ready/source-gap separation, repair policy contract rows 7, M40 materialization plan rows 90, scale-up recommended false | Input to E008-M40; materialize repaired rows before trajectory rerun |
| E006-M01 optional | Context-sensitive utility benchmark design | Define task-context-sensitive query rows and utility metrics | Start only if human task context is promoted beyond secondary ablation |
| E006-M02 optional | Strong context-agnostic baseline suite | Compare against fixed trust, all-high-value, all-reobserve, risk-only, path-cost-only, detector-confidence-only | Human task context must beat these baselines beyond a 1-row gain |
| E006-M03 optional | Context generalization stress | Test heldout scan / label / task-group transfer | Human task context main claim requires broad transfer, not one label group |
| E008 optional | Navigation `SR` / `SPL` bridge | Add simulator/navmesh/trajectory execution and navigation baselines | Do not start before E008-M01 source/episode preflight and launch gate are stable |

## Human Task Context Claim Upgrade

사실:

- E005-M53 shows H001 improves over `ConceptGraphs` and static memory on the heldout proxy-search table.
- E005-M53 also shows that H001 improves over context-agnostic memory trust by only 1 row.
- Current evidence supports task context as a secondary ablation, not as the main contribution.

논문 주장:

- Do not write the current paper as a human-intent understanding paper.
- The current paper can say structured task context conditions memory trust and re-observation decisions, but it should not claim that human task context is the main source of improvement.
- Natural language or LLM parsing should remain an adapter until structured context has a strong independent effect.

에이전트 추론:

- Human intent is worth keeping in the research direction, but not worth expanding before the real RGB-D/open-vocabulary robustness gate is planned.
- Promote human task context only if a dedicated context-sensitive utility benchmark shows clear gains over strong context-agnostic policies.
- The right upgrade target is not generic natural-language understanding; it is context-dependent utility: different task contexts should rationally change memory trust, re-observation budget, candidate visit order, and old-location dead-end cost.

Upgrade requirements:

- Build `task-context-sensitive` query rows where the same object/location evidence should lead to different decisions under different task contexts.
- Add strong context-agnostic baselines: fixed trust, all-high-value trust, all-reobserve, risk-threshold only, path-cost only, and detector-confidence only.
- Add context-dependent utility metrics: `ExpectedSearchCost`, old-location dead-end cost, unnecessary re-observation cost, missed-high-value penalty, false trust penalty, and candidate visit order.
- Require heldout scan / label / task-group transfer before writing a general human-context claim.
- Treat LLM-based natural-language intent parsing as a later input adapter, not as a source of method novelty.

Decision:

- Immediate paper path: keep human task context as secondary evidence.
- Optional expansion path: launch E006 only after E005-M54 if the paper needs a stronger human-intent claim.

## Claim Expansion Order

사실:

- Real RGB-D/open-vocabulary robustness is not ready.
- Real navigation `SR` / `SPL` is not ready.
- E005-M53 makes the proxy-search claim boundary explicit.

에이전트 추론:

- The next claim to mature is proxy-search with external map baseline comparison.
- The next expansion after that should be real RGB-D/open-vocabulary robustness.
- Real navigation `SR` / `SPL` should come last because it requires simulator/navmesh/trajectory execution and navigation baselines.

Order:

1. E005-M54: paper-table claim ledger / method claim rewrite. Complete.
2. E005-M55: real RGB-D/open-vocabulary robustness expansion gate. Complete.
3. E005-M56: two-table robustness denominator and `Open3DSG` source/interface audit. Complete.
4. E005-M57: `Open3DSG` output schema inspection / query-conversion contract. Complete.
5. E005-M58: `Open3DSG` object-candidate dump/export smoke plan. Complete.
6. E005-M59: `Open3DSG` object-candidate export hook implementation / one-batch Docker smoke. Complete.
7. E005-M60: `Open3DSG` query-level conversion. Complete after M61 rerun and target-geometry loader fix.
8. E005-M61: targeted denominator-aligned `Open3DSG` export. Complete.
9. E005-M62: `Open3DSG` result interpretation. Complete with corrected metrics.
10. E005-M63: `Open3DSG` route decision. Complete; bounded predicted-vocabulary repair selected.
11. E005-M64: leakage-safe `Open3DSG` predicted-vocabulary policy. Complete.
12. E005-M65: `Open3DSG` vocabulary-policy claim-boundary / paper-table integration decision. Complete.
13. E005-M66: external-baseline table failure-boundary rows. Complete.
14. E005-M67: real RGB-D/open-vocabulary robustness expansion route decision. Complete.
15. E005-M68: full-denominator real RGB-D proposal bridge plan. Complete.
16. E005-M69: full-denominator real proposal detector batch launch. Complete for `heldout_b01`.
17. E005-M70: `heldout_b01` detector completion verification. Complete.
18. E005-M71: `heldout_b01` real proposal query-level metric conversion. Complete.
19. E005-M72: `heldout_b02` / `heldout_b03` real proposal detector batch launch. Complete.
20. E005-M73/M74: verify/convert `heldout_b02` / `heldout_b03`. Complete.
21. E005-M75: aggregate b01/b02/b03. Complete.
22. E005-M76: diagnostic-table inclusion and detector/prompt repair decision. Complete.
23. E005-M77: offline detector/prompt repair design over existing pre-cap candidate pools. Complete.
24. E005-M78: fixed offline repair replay implementation and M75/M76 comparison. Complete.
25. E005-M79: runner insertion point and targeted repair rerun plan. Complete.
26. E005-M80: confidence-log-depth targeted detector rerun launch for `heldout_b02`. Complete.
27. E005-M81/M82: completion verification and query metric conversion for targeted rerun. Complete.
28. E005-M83: result interpretation and remaining-batch decision. Complete.
29. E005-M84: prompt/label recall repair or external proposal baseline route decision. Complete.
30. E005-M85: prompt/label recall miss audit and repair contract. Complete.
31. E005-M86: prompt repair preflight or visibility/matcher audit. Complete.
32. E005-M87: candidate-survival / match-threshold / zero-written scan audit. Complete.
33. E005-M88: zero-written raw-label trace / post-filter instrumentation audit. Complete.
34. E005-M89: target-independent cleanup-trace runner patch / `heldout_b02` trace rerun. Complete; `569d8f0f` zero-written cluster is dominated by label-resolution / scan-prompt scope mismatch.
35. E005-M90: label-normalization / scan-prompt scope repair decision. Complete.
36. E005-M91: active-label precedence runner patch / one-scan cleanup smoke. Complete.
37. E005-M92: one-scan matched-target/query conversion or bounded heldout rerun decision. Complete.
38. E005-M93: bounded `heldout_b02` active-label precedence rerun launch/verification. Complete.
39. E005-M94: claim-boundary update or broader repair decision. Complete.
40. E005-M95: paper-facing real-proposal diagnostic table and final E005 boundary refresh. Complete.
41. E005-M96: next expansion route decision. Complete.
42. E005-M97: external proposal/mapping baseline feasibility matrix. Complete.
43. E005-M98: `ConceptGraphs`-derived proposal/map reliability and failure-boundary smoke. Complete.
44. E005-M99: row-group inspection / heavier external route decision. Complete.
45. E005-M100: `ConceptGraphs`-assisted H001 fallback policy smoke. Complete.
46. E005-M101: map-assisted fallback claim-boundary / navigation-bridge decision. Complete.
47. E007-M01: navigation/path-cost bridge contract. Complete.
48. E007-M02: path-source compatibility and candidate-route materialization audit. Complete.
49. E007-M03: external candidate grid projection and path-cost route computation. Complete.
50. E007-M04: path-cost policy metric evaluation with source-limited accounting. Complete.
51. E007-M05: path-cost result interpretation and paper-table boundary decision. Complete.
52. E007-M06: path-start/source-limit sensitivity and reviewer-defense audit. Complete.
53. E007-M07: bridge-table package and navigation-expansion decision. Complete.
54. E008-M01: real navigation benchmark/source preflight and episode contract. Complete.
55. E008-M02: `HM3D ObjectNav` episode/source adapter smoke. Complete.
56. E008-M03: `H001` candidate-to-navigation adapter contract. Complete.
57. E008-M04: `ObjectNav` goal/viewpoint oracle path smoke. Complete.
58. E008-M05: `HM3D` candidate-source staging plan. Complete.
59. E008-M06: `HM3D` semantic annotation candidate-source smoke. Complete with coordinate-extraction blocker.
60. E008-M07: `HM3D` rendered RGB-D detector candidate-source plan. Complete.
61. E008-M08: `HM3D` rendered RGB-D frame staging smoke. Complete.
62. E008-M09: `HM3D` rendered RGB-D detector candidate smoke. Complete.
63. E008-M10: detector candidate coordinate-frame and snap-to-navmesh validation. Complete.
64. E008-M11: reachable-subset detector candidate visit-order path smoke. Complete.
65. E008-M12: leakage-safe detector candidate goal-evaluation smoke. Complete.
66. E008-M13: detector-goal failure audit and observation-coverage expansion decision. Complete.
67. E008-M14: non-oracle observation-coverage expansion plan. Complete.
68. E008-M15: non-oracle observation expansion frame staging smoke. Complete.
69. E008-M16: non-oracle observation expansion detector candidate smoke. Complete.
70. E008-M17: expanded detector candidate navmesh validation. Complete.
71. E008-M18: expanded detector candidate visit-order path smoke. Complete.
72. E008-M19: expanded leakage-safe detector candidate goal-evaluation smoke. Complete.
73. E008-M20: expanded detector-goal failure comparison and navigation-execution decision. Complete.
74. E008-M21: expanded detector-policy trajectory execution contract and Docker preflight. Complete.
75. E008-M22: expanded detector-policy trajectory execution runner scaffold. Complete.
76. E008-M23: trajectory-vs-proxy consistency and H001 candidate-source decision. Complete.
77. E008-M24: H001 candidate-source instantiation contract. Complete.
78. E008-M25: H001 candidate-source materialization smoke. Complete.
79. E008-M26: H001 visit-order/path smoke. Complete.
80. E008-M27: H001 leakage-safe goal-evaluation smoke. Complete.
81. E008-M28: H001 goal-evaluation comparison and trajectory-execution decision. Complete.
82. E008-M29: H001 current-observation fallback/source repair contract. Complete.
83. E008-M30: H001 current-observation fallback replay smoke. Complete.
84. E008-M31: H001 fallback trajectory-execution contract and source-gap boundary. Complete.
85. E008-M32: H001 fallback trajectory-execution runner scaffold. Complete.
86. E008-M33: H001 trajectory result interpretation and baseline alignment decision. Complete.
87. E008-M34: dynamic-stale navigation benchmark contract and source-intervention design. Complete.
88. E008-M35: dynamic-stale overlay row materialization smoke. Complete.
89. E008-M36: dynamic-stale overlay trajectory execution contract and runner adaptation. Complete.
90. E008-M37: dynamic-stale overlay trajectory execution smoke. Complete.
91. E008-M38: dynamic-stale overlay result interpretation and baseline alignment. Complete.
92. E008-M39: budget-matched dynamic-stale policy repair and source-gap contract. Complete.
93. E008-M40: budget-matched repair row materialization smoke. Complete.
94. E008-M41: budget-matched repair trajectory execution smoke. Complete.
95. E008-M42: budget-matched repair result interpretation and scale decision. Complete.
96. E008-M43: dynamic-stale navigation policy redesign contract. Complete.
97. E008-M44: source-diverse redesign row materialization smoke. Complete.
98. E008-M45: source-diverse redesign trajectory execution contract and Docker preflight. Complete.
99. E008-M46: source-diverse redesign trajectory execution smoke. Next.
100. Optional E006 human task-context upgrade: context-sensitive utility benchmark and strong context-agnostic baselines.
101. E008 navigation bridge: simulator/navmesh/trajectory execution, `SR`, `SPL`, `ExpectedSearchCost`, candidate visit order, stale old-location dead-end cost.

## External Baseline Expansion

Top-tier submission needs external baselines beyond current internal policies.

### Open-Vocabulary Mapping Baseline

Candidate baselines:

- `ConceptGraphs`
- `HOV-SG`
- `Open3DSG` if implementation/data compatibility is practical

Purpose:

- Compare against map construction and open-vocabulary object/relationship representation baselines.
- Show whether stale-memory decision logic adds value beyond stronger open-vocabulary map representations.

### Dynamic Semantic Mapping Baseline

Candidate baselines:

- `DualMap` or a compatible DualMap-style dynamic mapping baseline

Purpose:

- Compare against online open-vocabulary mapping for dynamically changing scenes.
- Clarify whether the contribution is dynamic map update, stale-memory trust, or downstream search decision.

### Navigation/Search Baseline

Candidate baselines:

- `VLFM`
- `HM3D-OVON` baseline
- `GOAT-Bench` modular baseline

Purpose:

- Connect semantic memory to downstream `SR`, `SPL`, `ExpectedSearchCost`, and lifelong/multimodal navigation metrics.
- Avoid limiting the paper to proxy object retrieval.

### Scene Memory Baseline

Candidate baseline:

- `3D-Mem`

Purpose:

- Compare against recent 3D scene memory and memory-management approaches for embodied exploration/reasoning.
- Position H001 as task-conditioned stale semantic memory rather than generic scene memory.

### Detector/Proposal Baseline

Candidate baselines:

- `Grounded-SAM`
- `OpenMask3D`
- `OVIR-3D`
- `ConceptGraphs` proposal path

Requirement:

- Add at least 1-2 proposal baselines beyond `GroundingDINO`.

Purpose:

- Prevent the real RGB-D/open-vocabulary claim from depending on one detector backend.
- Separate detector/proposal quality from stale-memory update behavior.

## Dataset Plan

사실:

- `3RScan` / `3DSSG` remains the core dataset for object movement, rescan alignment, and stale semantic memory.
- Current 8-scan real-proposal artifact is too small for reliable label-stratified split learning.

에이전트 추론:

- Keep `3RScan` / `3DSSG` as the primary dynamic-memory benchmark.
- Add `HM3D-OVON` or `GOAT-Bench` when the claim shifts to navigation/search metrics.
- Consider `OpenLex3D` only if open-vocabulary representation quality itself becomes a central claim.

## Immediate Next Actions

- Run E008-M46 source-diverse redesign trajectory execution smoke.
- Do not launch b01/b03 confidence-log-depth reruns unless a complete diagnostic detector-repair row is explicitly needed.
- Do not claim navigation `SR` / `SPL` until H001 beats budget-matched baselines, source-gap failures are separated, dynamic-stale overlay trajectories scale beyond the 6-episode smoke, and navigation/search baseline rows are added.
- Keep the main paper claim centered on memory trust, staleness handling, bounded re-observation, and proxy-search improvement over `ConceptGraphs` / static memory.
- Keep human task context as a secondary ablation unless E006 is explicitly launched and passes context-sensitive utility gates.
- Expand real RGB-D/open-vocabulary robustness before real navigation `SR` / `SPL`.
- Keep `OpenMask3D` as the later 3D instance proposal baseline candidate.
- Keep `Open3DSG`, `ConceptGraphs`, and `HOV-SG` for map/scene-graph/navigation baseline expansion.

## Claim Boundary

사실:

- Current real RGB-D/open-vocabulary claim readiness is false.
- Current real navigation `SR` / `SPL` claim readiness is false.
- Current human task context main-claim readiness is false.
- Current H001-vs-`ConceptGraphs` proxy-search claim readiness is true with proxy boundary.
- Current internal evidence supports controlled/proxy behavior, not final top-tier paper evidence.
- E003-M39 selects `docker_runner_pre_consolidation_support_evidence_v0` and rejects final-artifact post-processing as insufficient.
- E003-M39 fixes insertion point `select_cap_aware_label_balanced_candidates.after_cleaned_before_grouped`.
- E003-M40 status is `temporal_spatial_support_runner_smoke_ready`.
- E003-M40 attaches support evidence to 95 / 95 selected rows with validator errors/warnings 0 / 0.
- E003-M40 keeps real RGB-D/open-vocabulary claim readiness false because it is a short smoke, not heldout policy evidence.
- E003-M41 status is `support_aware_selection_policy_gate_ready`.
- E003-M41 selects `confidence_sqrt_depth_support_temporal_v0`.
- E003-M41 keeps hard support filter false, support cap changes false, and long rerun readiness false.
- E003-M42 status is `support_aware_selection_runner_smoke_ready`.
- E003-M42 validator errors/warnings are 0 / 0.
- E003-M42 matched/false-positive/precision delta vs E003-M40 is 0 / 0 / 0.0.
- E003-M43 status is `support_aware_scaled_rerun_route_gate_ready`.
- E003-M43 selected route is `pre_cap_candidate_pool_export_then_offline_replay_v0`.
- E003-M43 M42 vs M40 common selected rows are 94 / 95, selected symmetric difference is 2 rows, pre-cap rank changed common rows are 68, and selection-score changed common rows are 89.
- E003-M43 marks existing candidate-pool replay available false and immediate support-aware long rerun recommended false.
- E003-M44 status is `pre_cap_candidate_pool_replay_smoke_ready`.
- E003-M44 exported 629 pre-cap candidate rows with support policy on 629 / 629 rows.
- E003-M44 reproduced runner selection for `confidence_sqrt_depth_support_temporal_v0`: runner selected rows 95, offline replay rows 95, ordered/set reproduction true / true.
- E003-M45 tmux session `e003_m45_scaled_pool` completed with log `logs/20260508_155219_e003_m45_scaled_candidate_pool_export_replay_tmux.log`.
- E003-M45 verification status is `scaled_candidate_pool_replay_ready`, but frozen contract verdict is `fail_redesign`.
- E003-M45 support-aware score result is 196 matched targets, 3211 false positives, and proposal precision 0.057529, worse than the M33 confidence baseline 204 / 3210 / 0.059754.
- E003-M46 status is `score_redesign_or_external_gate_ready`.
- E003-M46 swept 12 bounded score policies and found hard pass 0, weak positive 0.
- E003-M46 selected `external_proposal_baseline_gate_first` because simple support-aware score redesign did not improve the M45 failure.
- E003-M47 status is `external_baseline_feasibility_gate_ready`.
- E003-M47 selected `Grounded-SAM` because it is the smallest controlled change from the current `GroundingDINO` RGB-D backprojection backend.
- `OpenMask3D` remains the stronger 3D instance segmentation baseline candidate, but its scene-format/checkpoint/MinkowskiEngine burden makes it a second route.
- `ConceptGraphs` and `HOV-SG` remain mapping/navigation baselines, not first proposal-failure diagnosis routes.
- E003-M48 status is `grounded_sam_contract_ready`.
- E003-M48 preserves the existing `real_proposal_prediction_jsonl_v0` required fields and adds 9 optional mask diagnostic fields.
- E003-M48 did not execute Docker/model inference and does not make a new result claim.
- E003-M49 `Grounded-SAM` Docker/model smoke emitted 24 mask-depth proposal rows and passed schema/matching smoke.
- E003-M50 same-subset comparison found bbox-depth 31 proposals / 2 matched targets / 29 false positives / precision 0.064516, while mask-depth had 24 / 1 / 23 / 0.041667.
- E003-M51 selected artifact-local mask failure analysis before any scaled `Grounded-SAM` rerun or `OpenMask3D` feasibility.
- E003-M52 found common candidate rows 24, bbox-only candidate rows 7, mask-only candidate rows 0, and skipped mask projection rows 16.
- E003-M52 lost-by-mask target count is 1, label `plant`; common same-target match-distance delta mask minus bbox is -0.018907m.
- E003-M52 diagnoses the aggregate centroid worsening as match-set composition after an easy bbox-depth target dropout, not common-target centroid degradation.
- E003-M52 keeps scaled `Grounded-SAM` recommended false and selects `E003-M53 bbox-depth continuation and failure-boundary repair gate`.
- E003-M53 status is `bbox_continuation_repair_gate_ready`.
- E003-M53 selected route is `search_critical_bbox_failure_boundary_first`.
- E003-M53 route scores: search-critical bbox boundary 46, deployable bbox suppression repair 30, `OpenMask3D` feasibility 27, `ConceptGraphs` mapping 19, `Open3DSG` mapping 16, `HOV-SG` navigation/mapping 10.
- E003-M53 keeps `OpenMask3D` as a later external 3D instance proposal baseline and keeps `Open3DSG` / `ConceptGraphs` / `HOV-SG` for later map/scene-graph/navigation baseline expansion.
- E003-M54 status is `search_critical_bbox_failure_boundary_ready`.
- E003-M54 exact current query-instance joins are 0 because M33/M45 detector-ready scans do not overlap with E001 current `rescan_id` rows.
- E003-M54 reference-memory-only joins are 120, label overlap count is 21, and existing E001/E002 search failures with label-level detector risk are 7.
- E003-M54 strongest bridge labels are `pillow` and `chair`; these remain label-level risks, not direct real RGB-D search-failure proof.
- E003-M55 status is `dynamic_pair_bridge_gate_ready`.
- E003-M55 selected route is `stage_search_failure_current_rescans_first`.
- E003-M55 search-failure current rescans are 4; semantic triplet ready is 4 / 4 and sequence-ready is 0 / 4.
- E003-M55 priority scans are `5555106a-36f1-29c0-8913-df1ba3c3cfd5`, `4731976c-f9f7-2a1a-95cc-31c4d1751d0b`, `ddc73795-765b-241a-9c5d-b97744afe077`, and `10b17957-3938-2467-88a5-9e9254930dad`.
- E003-M56 status is `current_rescan_sequence_staging_plan_ready`.
- E003-M56 target scan count is 4, prelaunch sequence-ready count is 0 / 4, and download-required count is 4 / 4.
- E003-M56 records a resumable `wget -c` staging script and `verify_m56_sequence_payloads.py --require-ready` verification command.
- E003-M57 status is `sequence_staging_job_launched`.
- E003-M57 background job status was `running` at launch in tmux session `e003_m56_sequence_stage`; the session later ended.
- E003-M57 log path is `logs/20260510_170443_e003_m56_sequence_staging.log`.
- E003-M57 verification status is `sequence_payloads_ready`, ready rows 4 / 4.
- E003-M57 does not create a paper result claim; it only prepares the direct current-rescan detector bridge denominator.
- E003-M58 status is `direct_current_rescan_bridge_design_ready`.
- E003-M58 links 7 search-failure query rows, 5 unique bridge targets, 4 current rescans, 29 same-label object targets, and 93 sampled frames for the next detector run.
- E003-M58 detector run executed is false and real RGB-D/open-vocabulary search claim readiness remains false.
- E003-M59 status is `pre_cap_candidate_pool_export_smoke_ready`.
- E003-M59 background job has completed.
- E003-M59 tmux session is `e003_m59_direct_bridge`.
- E003-M59 log path is `logs/20260511_114356_e003_m59_direct_current_rescan_detector_run.log`.
- E003-M59 target scans are 4 and bridge query rows are 7.
- E003-M59 scanned 93 frames, produced 2015 raw predictions, wrote 96 selected proposals, and exported 1970 pre-cap candidate rows.
- E003-M59 validator status is `proposal_schema_smoke_valid`, with errors/warnings 0 / 0.
- E003-M59 matching status is `detector_matching_smoke_ready`, with 21 matched proposals, 75 false-positive proposals, precision 0.218750, and scan target recall 0.724138.
- E003-M59 does not create a query-level paper result claim by itself; E003-M60 provides the first query-level bridge metric.
- E003-M60 status is `direct_query_bridge_budget_rank_gap`.
- E003-M60 query target detected rows are 3 / 7 and unique target detected rows are 3 / 5.
- E003-M60 mean detected target rank is 5.0 and mean false positives before detected target is 4.0.
- E003-M60 `detector_task_budget_v0` success is 0 / 7.
- E003-M60 `detector_top5_v0` success is 2 / 7.
- E003-M60 unbounded detector success is 3 / 7.
- E003-M60 keeps real RGB-D/open-vocabulary search claim readiness false.
- E003-M61 status is `direct_bridge_rank_failure_gate_ready`.
- E003-M61 failure class counts are detector recall miss 4, task-budget mismatch 2, and false-positive rank failure 1.
- E003-M61 unique target failure class counts are detector recall miss 2, task-budget mismatch 2, and false-positive rank failure 1.
- E003-M61 selected next route is `proposal_rerank_then_openmask3d_feasibility`.
- E003-M61 keeps real RGB-D/open-vocabulary search claim readiness false.
- E003-M62 status is `offline_rerank_budget_repair_ready`.
- E003-M62 best deployable unbounded repair succeeds on 3 / 7 rows with mean expected search cost 16.428571.
- E003-M62 bounded top-5/adaptive repair succeeds on 2 / 7 rows.
- E003-M62 selected next route is `integrate_deployable_rerank_budget_then_openmask3d`.
- E003-M62 keeps real RGB-D/open-vocabulary search claim readiness false.
- E003-M63 status is `bounded_repair_integration_gate_ready`.
- E003-M63 selected bounded policy is `old_memory_distance_guard+adaptive_uncertainty_top5`.
- E003-M63 selected bounded repair succeeds on 2 / 7 rows with mean expected search cost 5.428571.
- E003-M63 best task-budget rerank succeeds on 1 / 7 rows.
- E003-M63 unbounded upper-bound succeeds on 3 / 7 rows.
- E003-M63 bounded budget repair ablation ready is true, but bounded rerank unique gain ready is false.
- E003-M63 selected next route is `openmask3d_feasibility_gate_next`.
- E003-M64 status is `openmask3d_feasibility_decision_ready`.
- E003-M64 bounded failure rows are 5 / 7: target-undetected 4 and rank/budget gap 1.
- E003-M64 bridge scans with `OpenMask3D` minimal input readiness are 4 / 4.
- E003-M64 selected next route is `openmask3d_scene_format_model_smoke_plan_next`.
- E003-M64 launched no Docker/model run and keeps real RGB-D/open-vocabulary search claim readiness false.

논문 주장:

- Do not claim deployable real RGB-D/open-vocabulary robustness until external baselines and heldout-transfer evidence are added.
- Do not claim real navigation `SR` / `SPL` until a simulator, navmesh, or trajectory execution source is integrated.
