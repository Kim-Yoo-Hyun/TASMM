# E005 External Baseline Transition

Updated: 2026-05-27

## Status

`E005-M01` through `E005-M101` are complete through heldout `ConceptGraphs` runtime/query conversion, H001 heldout replay, `Open3DSG` adapter checks, full-denominator real proposal diagnostics, paper-facing claim boundary, external proposal/mapping feasibility, `ConceptGraphs` reliability boundary, row-group/heavier-route decision, `ConceptGraphs`-assisted H001 fallback policy smoke, and map-assisted fallback claim-boundary decision. `ConceptGraphs` is the active positive external mapping baseline route: full heldout strict bbox top5 is 114 / 195 = 0.584615, relaxed bbox 1m top3 is 144 / 195 = 0.738462, and centroid strict top5 is 75 / 195 = 0.384615. E005-M101 marks `h001_then_conceptgraphs_top5_on_observed_miss_v0` as paper-facing query-level table ready with boundary: H001 success 157 / 195 -> 181 / 195, `AttemptSPL` proxy 0.773932 -> 0.798675, mean `ExpectedSearchCost` 1.758974 -> 2.435897. Follow-up E007-M01-M07 is complete through navigation/path-cost bridge contract, route materialization, external candidate grid projection, path-cost policy metrics, paper-table boundary interpretation, source-limit/path-start sensitivity, final bridge-table packaging, and navigation-expansion decision. Next unit is E008-M01 real navigation benchmark/source preflight and episode contract. Keep `OpenMask3D` as a later proposal baseline because Docker/`MinkowskiEngine` remains blocked. Final real RGB-D/open-vocabulary robustness and real navigation `SR` / `SPL` remain blocked.

## E005-M101 Map-Assisted Fallback Claim Boundary

사실:

- Status: `e005_m101_map_assisted_claim_boundary_navigation_decision_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M101_map_assisted_claim_boundary_navigation_decision_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m101_map_assisted_claim_boundary_navigation_decision.py`.
- Selected route: `paper_table_integration_and_navigation_bridge_next`.
- Paper-table integration ready: true.
- Main table rows include `real_static_memory_only_v0`, `real_detector_confidence_top5_v0`, `conceptgraphs_only_strict_top5_v0`, `real_context_agnostic_memory_trust_reobserve_v0`, `h001_real_task_context_memory_trust_v0`, and `h001_then_conceptgraphs_top5_on_observed_miss_v0`.
- Follow-up completed: E007-M01 navigation/path-cost bridge contract, E007-M02 path-source compatibility audit, E007-M03 external candidate grid projection/path-cost route computation, E007-M04 path-cost policy metric evaluation, E007-M05 path-cost result interpretation / paper-table boundary decision, E007-M06 path-start/source-limit sensitivity audit, and E007-M07 bridge-table package / navigation-expansion decision.

논문 주장:

- M101 allows M100 as a paper-facing query-level policy row with explicit boundary labels.
- M101 still blocks final real RGB-D/open-vocabulary robustness, deployable search policy, real navigation `SR` / `SPL`, and human intent main claim.

에이전트 추론:

- The immediate top-tier expansion should be navigation/path-cost bridging, not another external mapping route.
- `OpenMask3D` / `HOV-SG` remain later routes if navigation bridge exposes proposal-source bottlenecks or reviewer pressure requires more external baselines.

## E005-M100 ConceptGraphs-Assisted H001 Fallback Policy

사실:

- Status: `e005_m100_conceptgraphs_assisted_fallback_policy_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M100_conceptgraphs_assisted_fallback_policy_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/run_m100_conceptgraphs_assisted_fallback_policy.py`.
- Selected policy: `h001_then_conceptgraphs_top5_on_observed_miss_v0`.
- H001 success / selected fallback success: 157 / 195 -> 181 / 195.
- H001 `AttemptSPL` proxy / selected fallback `AttemptSPL` proxy: 0.773932 -> 0.798675.
- H001 mean `ExpectedSearchCost` / selected fallback mean `ExpectedSearchCost`: 1.758974 -> 2.435897.
- Top6 sensitivity success: 184 / 195, diagnostic only.
- Follow-up completed: E005-M101 map-assisted fallback claim-boundary / navigation-bridge decision.

논문 주장:

- M100 supports a query-level map-assisted fallback smoke with explicit cost accounting.
- M100 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, real navigation `SR` / `SPL`, or human intent main contribution.

에이전트 추론:

- The selected top5 fallback improves both success and `AttemptSPL` proxy, so it is stronger than the earlier union upper-bound argument.
- Map-first variants avoid more old-location dead ends but have worse `AttemptSPL`; they should not be the default policy yet.
- Follow-up completed: E005-M101 paper-table decision and E007-M01-M05 navigation/path-cost bridge setup through paper-table boundary.

## E005-M99 Row-Group / External Route Decision

사실:

- Status: `e005_m99_row_group_heavier_route_decision_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M99_row_group_heavier_route_decision_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m99_row_group_heavier_route_decision.py`.
- Query rows / unique targets: 195 / 65.
- H001 failure rows / targets: 38 / 13.
- `ConceptGraphs` map-assisted repair candidate rows / targets: 24 / 8.
- H001-or-`ConceptGraphs` upper bound: 181 / 195.
- H001-or-`ConceptGraphs`-or-real-top5 upper bound: 183 / 195.
- H001 context-sensitive targets: 1 / 65.
- Follow-up completed: E005-M100 `ConceptGraphs`-assisted H001 fallback policy smoke.

논문 주장:

- M99 supports `ConceptGraphs` as a method-facing repair opportunity, not only as an external baseline row.
- M99 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, human intent main contribution, or real navigation `SR` / `SPL`.

에이전트 추론:

- The immediate blocker is now policy form and cost accounting for map-assisted fallback, not another heavy external baseline.
- `OpenMask3D` / `HOV-SG` should be revisited after M100 if shared gaps or reviewer baseline pressure remain high.
- Navigation bridge should wait until the fallback trigger, candidate visit order, and `ExpectedSearchCost` accounting are fixed.

## E005-M98 ConceptGraphs Reliability Boundary

사실:

- Status: `e005_m98_conceptgraphs_reliability_boundary_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M98_conceptgraphs_reliability_boundary_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/analyze_m98_conceptgraphs_reliability_boundary.py`.
- Query rows: 195.
- `ConceptGraphs` target detected / strict top5 success: 138 / 195, 114 / 195.
- Real detector target detected / top5 / task-budget: 144 / 195, 51 / 195, 24 / 195.
- H001 real memory-trust success: 157 / 195.
- H001 recovers both `ConceptGraphs` strict top5 and real detector top5 failure: 54 rows.
- `ConceptGraphs` succeeds while H001 fails: 24 rows.
- Neither `ConceptGraphs` nor real detector target-detects: 12 rows.
- Follow-up completed: E005-M99 row-group inspection / heavier external route decision.

논문 주장:

- M98 supports `ConceptGraphs` as a reliability diagnostic under the same 195-row denominator.
- M98 supports a diagnostic memory-decision claim because H001 recovers many rows where both external map strict top5 and real detector top5 fail.
- M98 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

에이전트 추론:

- H001 is not reducible to external map retrieval because it recovers 54 rows where both `ConceptGraphs` strict top5 and real detector top5 fail.
- The 24 `map_success_h001_failure` rows are reviewer-critical and should be inspected before any broad superiority claim.
- M99 should decide whether to inspect those rows first, repair/launch a heavier external route, or move to navigation bridge design.

## E005-M97 External Proposal/Mapping Feasibility Matrix

사실:

- Status: `e005_m97_external_proposal_mapping_feasibility_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M97_external_proposal_mapping_feasibility_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m97_external_proposal_mapping_feasibility.py`.
- Selected first route: `conceptgraphs_derived_map_candidate_route`.
- Candidate routes: `ConceptGraphs`-derived route, `Open3DSG` bounded vocab adapter, `OpenMask3D`, `HOV-SG`.
- `ConceptGraphs` route: data ready true, Docker ready true, denominator alignment ready at 195 rows.
- `Open3DSG` bounded vocab adapter: supporting row, not first route.
- `OpenMask3D`: deferred because Docker image is not ready after `MinkowskiEngine` build failure.
- `HOV-SG`: deferred because source/runtime audit is not present in this workspace.
- Next unit: E005-M98 `ConceptGraphs`-derived proposal/map reliability and failure-boundary smoke.

논문 주장:

- M97 is a feasibility decision, not a performance claim.
- M97 does not make final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL` ready.

에이전트 추론:

- `ConceptGraphs`-derived route is the best immediate next step because it reuses denominator-aligned 195-row external map evidence without a heavy run.
- `OpenMask3D` and `HOV-SG` are still valuable for top-tier pressure, but they should not block the next low-burden failure-boundary smoke.
- M98 must avoid repeating M49 retrieval scores; it should connect external map/proposal coverage to H001, real proposal, and shared-failure row groups.

## E005-M96 Next Expansion Route Decision

사실:

- Status: `e005_m96_next_expansion_route_decision_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M96_next_expansion_route_decision_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m96_next_expansion_route.py`.
- M95 blocked claims: 4.
- M95 allowed diagnostic claims: 2.
- Selected route: `external_proposal_mapping_baseline_first`.
- Deferred route: `navigation_search_bridge_first`.
- Next unit: E005-M97 external proposal/mapping baseline feasibility matrix.

논문 주장:

- M96 is a route decision, not a new performance claim.
- M96 keeps final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` blocked.
- The next claim-expansion pressure should come from external proposal/mapping baselines before navigation execution.

에이전트 추론:

- External proposal/mapping baseline feasibility should precede navigation because M95's active blocker is robustness of the proposal/mapping evidence.
- Starting navigation now would confound mapping/proposal failures with search policy failures.
- E005-M97 should compare `ConceptGraphs`-derived proposal/map route, `OpenMask3D`, `HOV-SG`, and `Open3DSG` bounded vocab adapter before launching a heavy route.

## E005-M95 Real-Proposal Paper Boundary

사실:

- Status: `e005_m95_real_proposal_paper_boundary_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M95_real_proposal_paper_boundary_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m95_real_proposal_paper_boundary.py`.
- Paper-facing diagnostic table rows: 7.
- Repair diagnostic rows: 4.
- Allowed diagnostic claims: 2.
- Blocked claims: 4.
- M75 H001 / context-agnostic / `ConceptGraphs` / detector top5: 157 / 156 / 114 / 51 over 195 rows.
- M94 projected b02-replaced aggregate: target detected 159 / 195, detector top5 60 / 195, detector task-budget 26 / 195, H001 157 / 195.
- Selected next route: `close_current_e005_boundary_and_choose_next_expansion_route`.
- Next unit: E005-M96 next expansion route decision.

논문 주장:

- M95 allows only diagnostic claims for the real-proposal table and active-label repair.
- M95 blocks final real RGB-D/open-vocabulary robustness, deployable search policy, real navigation `SR` / `SPL`, and human intent main contribution.

에이전트 추론:

- The paper-facing E005 result should use M75 as the full-denominator real-proposal diagnostic table.
- M93/M94 should remain repair/failure-analysis evidence, not a main method result.
- Next progress should come from choosing between stronger external proposal/mapping evidence and navigation/search execution evidence.

## E005-M94 Active-Label Precedence Claim Boundary

사실:

- Status: `e005_m94_active_label_precedence_claim_boundary_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M94_active_label_precedence_claim_boundary_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m94_active_label_precedence_claim_boundary.py`.
- Selected route: `stop_and_record_m93_as_batch_level_repair_diagnostic`.
- M93 b02 target detected rows: 42 / 69 -> 57 / 69.
- M93 b02 detector top5 rows: 15 / 69 -> 18 / 69.
- M93 b02 detector task-budget rows: 7 / 69 -> 7 / 69.
- M93 b02 H001 rows: 54 / 69 -> 54 / 69.
- Projected diagnostic aggregate if b02 is replaced by M93: target detected 159 / 195, detector top5 60 / 195, detector task-budget 26 / 195, H001 157 / 195.
- Completed next unit: E005-M95 paper-facing real-proposal diagnostic table and final E005 boundary refresh.

논문 주장:

- M94 supports recording M93 as batch-level target-detection repair diagnostic evidence.
- M94 blocks final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` claims.

에이전트 추론:

- b01/b03 active-label reruns are not the best immediate use of effort because M93 does not improve H001 success or detector task-budget success.
- The next paper-facing task should refresh the real-proposal diagnostic table and claim boundary, then decide whether stronger external proposal/mapping baselines or navigation/search execution should be prioritized.

## E005-M93 Active-Label Precedence Bounded Rerun / Result Analysis

사실:

- Result status: `e005_m93_active_label_precedence_result_analysis_ready`.
- Launch artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M93_active_label_precedence_detector_launch_v0/heldout_b02/`.
- Run artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M93_active_label_precedence_detector_run_v0/heldout_b02/`.
- Verification artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M93_active_label_precedence_detector_verification_v0/heldout_b02/`.
- Query metric artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M93_active_label_precedence_query_metric_v0/heldout_b02/`.
- Result analysis artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M93_active_label_precedence_result_analysis_v0/`.
- Selection score mode: `confidence_log_depth`.
- Prediction / pre-cap / cleanup rows: 288 / 7,498 / 7,840.
- Matched target rows / proposal precision / scan target recall: 19 / 0.065972 / 0.863636.
- Query target detected rows: 42 / 69 -> 57 / 69.
- Detector top5 success rows: 15 / 69 -> 18 / 69.
- Detector task-budget success rows: 7 / 69 -> 7 / 69.
- H001 success rows: 54 / 69 -> 54 / 69.
- Target detection gain/loss rows: 15 / 0.
- `chair`/`stool` side-effect observed: false.
- Completed next unit: E005-M94 claim-boundary update or broader repair decision.

논문 주장:

- M93 supports batch-level target-detection repair evidence for `active_scan_exact_label_precedence_v0`.
- M93 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

에이전트 추론:

- The repair is useful as detector/prompt bridge evidence, not as a main H001 method gain, because H001 success is unchanged.

## E005-M92 Active-Label Precedence Next-Step Decision

사실:

- Status: `e005_m92_active_label_precedence_next_step_decision_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M92_active_label_precedence_next_step_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m92_active_label_precedence_next_step.py`.
- Affected scan: `569d8f0f-72aa-2f24-89a6-77f8b8779ae9`.
- Affected query rows / targets: 15 / 5.
- M82 target detected rows on affected scan: 0 / 15.
- M91 target detected rows on affected scan: 15 / 15.
- M91 detector top5 / task-budget success rows on affected scan: 3 / 2.
- H001 success before / after one-scan conversion: 6 / 6.
- b02 no-side-effect lower-bound target detected rows/rate: 57 / 69 = 0.826087.
- Side-effect risk: 1 scan, 15 query rows, including 3 `stool` rows.
- Selected route: `bounded_heldout_b02_rerun_before_full_query_claim`.
- Next unit: E005-M93 bounded `heldout_b02` active-label precedence rerun launch/verification.

논문 주장:

- M92 supports only a route decision: M91 should be promoted to a bounded b02 rerun before updating full query-level real-proposal claims.
- M92 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

에이전트 추론:

- M91 recovers target detection on the audited scan, but most recovered target ranks are outside H001's detector budget, so it does not yet strengthen the H001 memory-decision success table.
- A bounded b02 rerun is more defensible than one-scan-only conversion because it can measure net gain and `chair`/`stool` side effects under the same batch contract.

## E005-M91 Active-Label Precedence Runner Patch / One-Scan Cleanup Smoke

사실:

- Status: `e005_m91_active_label_precedence_smoke_ready`.
- Run artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M91_active_label_precedence_smoke_v0/heldout_b02/`.
- Analysis artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M91_active_label_precedence_analysis_v0/`.
- Runner patch: `resolve_canonical_label()` now gives exact normalized active scan labels precedence before global prompt aliases.
- M89 pre-cap / final rows: 0 / 0.
- M91 pre-cap / final rows: 479 / 24.
- M91 cleanup keep/drop: 479 / 4.
- M91 canonical labels: `chair` 479, `a` 4.
- Selected proposal cap respected: true.
- Matching smoke: matched target rows 5 / 5, proposal precision 0.208333, scan target recall 1.0.
- Next unit: E005-M92 one-scan matched-target/query conversion or bounded heldout rerun decision.

논문 주장:

- M91 supports a narrow implementation claim: the selected leakage-safe label-resolution repair fixes the cleanup-stage zero-written failure on the audited scan.
- M91 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

에이전트 추론:

- This is a strong reviewer-defense step because it follows the chain `failure diagnosis -> minimal repair principle -> bounded smoke evidence`.
- The next decision should avoid overclaiming from one scan and decide whether to run query-level conversion or a bounded heldout rerun first.

## E005-M90 Label Normalization / Prompt Scope Repair Decision

사실:

- Status: `e005_m90_label_normalization_prompt_scope_repair_decision_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M90_label_normalization_prompt_scope_repair_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m90_label_normalization_prompt_scope_repair.py`.
- Selected route: `active_scan_exact_label_precedence_then_one_scan_cleanup_smoke`.
- Selected option: `active_scan_exact_label_precedence_v0`.
- Rejected option: `scan_prompt_scope_expand_stool_for_chair_scan_v0`.
- Prompt conflict count: 1, normalized prompt `chair` maps to canonical labels `chair` and `stool`.
- Active-exact replay keep rows: 479 / 483.
- Blocked-field hits: 0.
- Worst-case new selected proposal upper bound before matching: 24.
- Next unit: E005-M91 active-label precedence runner patch / one-scan cleanup smoke.

논문 주장:

- M90 supports only a leakage-safe repair route decision.
- M90 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

에이전트 추론:

- The repair should change label resolution, not scan-prompt scope. If normalized detector text exactly matches an active scan canonical label, that active label should win before global prompt aliases.
- Simply allowing `stool` in a `chair`-only scan is semantically unsafe and likely inflates false positives.

## E005-M89 Cleanup Trace Runner Patch / Rerun

사실:

- Status: `e005_m89_cleanup_trace_analysis_ready`.
- Runner patch files:
  - `experiments/E003_perception_noise_expansion/docker/real_proposals/run_rgbd_ov_proposals.py`
  - `experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py`
  - `experiments/E005_external_baseline_transition/tools/verify_m70_full_denominator_real_proposal_detector_batch.py`
- Launch artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M89_cleanup_trace_detector_launch_v0/heldout_b02/`.
- Run artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M89_cleanup_trace_detector_run_v0/heldout_b02/`.
- Verification artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M89_cleanup_trace_detector_verification_v0/heldout_b02/`.
- Analysis artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M89_cleanup_trace_analysis_v0/`.
- tmux session: `e005_m89_cleanup_trace_heldout_b02_569d8f0f` completed.
- Log: `logs/20260526_182011_e005_m89_cleanup_trace_heldout_b02_569d8f0f.log`.
- Verification status: `e005_m89_cleanup_trace_detector_batch_ready`.
- Analysis command: `python experiments/E005_external_baseline_transition/tools/analyze_m89_cleanup_trace_result.py`.
- Trace rows: 483.
- Decision counts: `drop` 483.
- Drop reason counts: `drop_not_scan_prompt_label` 479, `drop_non_prompt_label` 4.
- Canonical label counts: `stool` 479, `a` 4.
- Active scan labels: `chair`.
- Blocked-field hits: 0.
- Target-independent trace fields: raw `label_text`, resolved `label_canonical`, active scan labels, enabled prompt labels, cleanup decision, cleanup drop reason.
- Blocked fields: `target_uid`, `candidate_is_target`, `matched_3dssg_instance_id`, nearest target distance, query success label.

논문 주장:

- M89 supports an instrumentation and failure-diagnosis claim: the zero-written cluster is post-projection cleanup loss dominated by label-resolution / scan-prompt scope mismatch.
- M89 does not support prompt repair, final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

에이전트 추론:

- The `569d8f0f` zero-written cluster is not primarily a score ranking, cap, or match-threshold failure.
- The next decision should be E005-M90: a leakage-safe label-normalization or scan-prompt scope repair gate with false-positive inflation checks.

## E005-M88 Zero-Written Raw-Label Trace Audit

사실:

- Status: `e005_m88_zero_written_raw_label_trace_audit_ready_trace_missing`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M88_zero_written_raw_label_trace_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m88_zero_written_raw_label_trace.py`.
- Scan: `569d8f0f-72aa-2f24-89a6-77f8b8779ae9`.
- Zero-written cluster: 5 targets / 15 query rows.
- M69 raw/projected/written: 513 / 483 / 0.
- M80 raw/projected/written: 513 / 483 / 0.
- M69/M80 pre-cap rows for this scan: 0 / 0.
- Reconstructed active scan labels: `chair`.
- Prompt has `chair`: true.
- Existing artifact has raw-label text distribution: false.
- Likely loss stage: `prompt_label_cleanup_before_spatial_consolidation_and_caps`.

논문 주장:

- M88 supports a narrow failure localization claim: this zero-written cluster is post-projection and pre-pre-cap-pool, not a score-mode, ranking, cap, or match-threshold failure.
- M88 does not support prompt repair, detector repair, final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

에이전트 추론:

- The next step should patch target-independent cleanup tracing into the runner and rerun `heldout_b02` or the `569d8f0f` scan if a scan filter is added.
- The trace must record raw `label_text`, resolved `label_canonical`, active scan labels, enabled prompt labels, and cleanup drop reason without target uid, query success, or match labels.

## E005-M87 Candidate Survival / Threshold / Zero-Written Audit

사실:

- Status: `e005_m87_candidate_survival_threshold_zero_written_audit_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M87_candidate_survival_threshold_zero_written_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m87_candidate_survival_threshold_zero_written.py`.
- Audited targets: 11, query exposure 33 / 195.
- Strict pre-cap candidate suppressed targets: 0.
- Selected candidate recoverable at 1.5m: 2 targets / 6 query rows.
- Pre-cap candidate recoverable at 1.5m: 3 targets / 9 query rows.
- Same-label instance ambiguity: 2 targets / 6 query rows.
- Zero-written scan cluster: 5 targets / 15 query rows.
- Bounded prompt repair ready: false.
- Launch detector rerun now: false.
- Selected route: `zero_written_raw_label_trace_before_prompt_or_threshold_repair`.

논문 주장:

- M87 supports a failure-boundary decision: the current detector/prompt route is diagnostic, not final robustness evidence.
- M87 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

에이전트 추론:

- This route decision was executed by E005-M88. The 1.5m threshold remains diagnostic because the `569d8f0f` cluster has zero pre-cap rows.

## E005-M86 Prompt Repair Preflight / Visibility-Matcher Decision

사실:

- Status: `e005_m86_prompt_repair_preflight_visibility_matcher_decision_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M86_prompt_repair_preflight_visibility_matcher_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m86_prompt_repair_preflight_visibility_matcher.py`.
- Audited targets: 11, query exposure 33 / 195.
- Visibility/matcher audit: 5 targets / 15 query rows.
- Zero-written scan audit: 5 targets / 15 query rows.
- Broad-label contract: 1 target / 3 query rows.
- Bounded prompt repair preflight ready: false.
- Launch detector rerun now: false.
- Selected route: `candidate_survival_match_threshold_and_zero_written_scan_audit_before_prompt_rerun`.

논문 주장:

- M86 supports a route decision: prompt repair is not yet a defensible paper claim.
- M86 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

에이전트 추론:

- This route decision was executed by E005-M87. M86 should now be read as the pre-M87 split that motivated candidate-survival / threshold / zero-written auditing.

## E005-M85 Prompt/Label Recall Miss Audit

사실:

- Status: `e005_m85_prompt_label_recall_audit_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M85_prompt_label_recall_audit_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m85_prompt_label_recall_audit.py`.
- Audited recall-miss targets: 11 / 65.
- Audit class counts: `detector_or_label_parse_no_same_label_candidates` 5, `localization_or_match_threshold_gap` 4, `matcher_or_target_assignment_audit_needed` 1, `prompt_contract_gap_broad_or_missing_label` 1.
- Selected route: `visibility_matcher_audit_then_bounded_prompt_repair_preflight`.
- Blocked repair-policy inputs: `target_uid`, `object_instance_id`, `matched_3dssg_instance_id`, target match distance, query success labels.

논문 주장:

- M85 supports a diagnosis contract for prompt/label recall misses.
- M85 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

에이전트 추론:

- Prompt repair alone is not sufficient. Five targets need no-same-label candidate diagnosis, five need visibility/matcher or threshold audit, and one broad `object` target needs denominator/prompt-contract handling.

## E005-M84 Prompt/Label vs External Proposal Route Decision

사실:

- Status: `e005_m84_prompt_label_external_route_decision_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M84_prompt_label_external_route_decision_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m84_prompt_label_external_route.py`.
- Selected route: `prompt_label_recall_audit_first_then_external_proposal_baseline_gate`.
- Prompt/detector recall-miss targets: 11 / 65.
- Max query-detection exposure if those targets are recovered: 33 / 195.
- Remaining b01/b03 confidence-log-depth expected gain after b02: 3 rows.
- Miss labels: `chair` 6, `stool` 2, `commode` 1, `door` 1, `object` 1.
- `Grounded-SAM` same-subset weak positive: false.
- `OpenMask3D` hard blockers: 3 (`docker_build_failed`, `minkowskiengine_build_requirement_error`, `image_not_ready`).

논문 주장:

- M84 supports the route decision that recall diagnosis is the next lightweight step.
- M84 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

에이전트 추론:

- The next step should not be b01/b03 rerun or a heavy external proposal job. First separate prompt alias, broad-label, visibility, and detector-miss causes for the 11 recall-miss targets.

## E005-M83 Confidence-Log-Depth Rerun Decision

사실:

- Status: `e005_m83_confidence_log_depth_rerun_decision_ready_limited_detector_ranking_gain`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M83_confidence_log_depth_rerun_decision_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m83_confidence_log_depth_rerun_decision.py`.
- Actual b02 detector top5 gain: 9 / 69 -> 15 / 69.
- Actual b02 target-detection gain: 42 / 69 -> 42 / 69.
- Expected all-batch detector top5 if b01/b03 fixed-policy gains are also realized: 60 / 195.
- H001 real memory-trust policy on the same real-proposal aggregate: 157 / 195.
- Remaining rerun recommendation: skip b01 now because expected top5 gain is 0; skip b03 now unless a complete diagnostic detector-repair table is needed.

논문 주장:

- M83 supports only a limited detector-ranking repair diagnostic.
- M83 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

에이전트 추론:

- The next useful unit is not another detector rerun. It is E005-M84: decide whether to repair prompt/label recall misses or move to an external proposal baseline route.

## E005-M82 Confidence-Log-Depth Query Metrics

사실:

- Status: `e005_m71_real_proposal_query_metric_ready_target_detection_weak`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M82_confidence_log_depth_query_metric_v0/heldout_b02/`.
- Command: `python experiments/E005_external_baseline_transition/tools/run_m71_real_proposal_query_metrics.py --batch-id heldout_b02 --m69-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M80_confidence_log_depth_detector_run_v0 --m70-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M81_confidence_log_depth_detector_verification_v0 --out-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M82_confidence_log_depth_query_metric_v0`.
- Query rows: 69.
- Query target detected: 42 / 69 = 0.608696.
- Detector task-budget success: 7 / 69.
- Detector top5 success: 15 / 69.
- H001 success: 54 / 69.
- Context-agnostic memory trust success: 54 / 69.
- `ConceptGraphs` same-batch success: 45 / 69.
- Baseline M71 `heldout_b02` detector top5 was 9 / 69 and task-budget was 5 / 69.

논문 주장:

- M82 supports that `confidence_log_depth` improves selected-proposal ranking on `heldout_b02`.
- M82 does not support final real RGB-D/open-vocabulary robustness because target detection remains 42 / 69 and the detector-only row is still far below H001.

에이전트 추론:

- E005-M83 already decided that the reproduced b02 gain is diagnostic-only and not enough to justify immediate b01/b03 reruns.

## E005-M81 Confidence-Log-Depth Detector Verification

사실:

- Status: `e005_m70_real_proposal_detector_batch_ready_with_false_positive_load`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M81_confidence_log_depth_detector_verification_v0/heldout_b02/`.
- Command: `python experiments/E005_external_baseline_transition/tools/verify_m70_full_denominator_real_proposal_detector_batch.py --batch-id heldout_b02 --launch-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M80_confidence_log_depth_detector_launch_v0 --run-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M80_confidence_log_depth_detector_run_v0 --out-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M81_confidence_log_depth_detector_verification_v0 --require-ready`.
- Expected files ready: 14 / 14.
- Prediction rows: 264.
- Pre-cap candidate rows: 6,799.
- Matched targets: 14 / 17.
- Scan target recall: 0.823529.
- Proposal precision: 0.053030.
- Query metric conversion ready: true.

논문 주장:

- M81 supports detector completion and schema/matching readiness for the M80 rerun.
- M81 does not support final robustness or navigation claims.

## E005-M80 Confidence-Log-Depth Detector Launch

사실:

- Status: `e005_m80_confidence_log_depth_detector_job_launched`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M80_confidence_log_depth_detector_launch_v0/heldout_b02/`.
- Command: `python experiments/E005_external_baseline_transition/tools/launch_m80_confidence_log_depth_detector_batch.py --batch-id heldout_b02`.
- Batch: `heldout_b02`.
- tmux session: `e005_m80_confidence_log_depth_heldout_b02`.
- Log: `logs/20260526_020840_e005_m80_confidence_log_depth_heldout_b02.log`.
- Output: `experiments/E005_external_baseline_transition/artifacts/E005-M80_confidence_log_depth_detector_run_v0/heldout_b02/`.
- GPU free at launch: 24,421 MiB.
- Fixed score mode: `confidence_log_depth`.
- Verification: completed by E005-M81.
- Query-level conversion: completed by E005-M82.

논문 주장:

- M80 only supports that the runner-integrated detector rerun was launched.
- It does not yet support real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

에이전트 추론:

- M80 should be interpreted together with E005-M81/M82; the useful result is the b02 ranking gain, not a final robustness claim.

## E005-M79 Runner Insertion / Targeted Rerun Plan

사실:

- Status: `e005_m79_runner_insertion_targeted_rerun_plan_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M79_runner_insertion_targeted_rerun_plan_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m79_runner_insertion_targeted_rerun.py`.
- Runner source edit required: false.
- Fixed score mode: `confidence_log_depth`.
- Insertion point: `select_cap_aware_label_balanced_candidates.score_candidate_before_spatial_consolidation_and_caps`.
- M78 expected top5 by batch: `heldout_b01` 21/66, `heldout_b02` 15/69, `heldout_b03` 24/60.
- M75 detector top5 by batch: `heldout_b01` 21/66, `heldout_b02` 9/69, `heldout_b03` 21/60.
- First rerun batch: `heldout_b02`.
- Selected next route: `gain_batch_first_targeted_rerun_then_remaining_batches_if_reproduction_holds`.
- Completed next unit: E005-M80 confidence-log-depth targeted detector rerun launch for `heldout_b02`.

논문 주장:

- M79 supports that the M78 repair policy is expressible by existing runner arguments.
- M79 is not a detector result and does not support final robustness.

에이전트 추론:

- `heldout_b02` is the right first rerun because it tests the largest expected repair gain rather than only runner smoke compatibility.

## E005-M78 Offline Repair Replay

사실:

- Status: `e005_m78_offline_repair_replay_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M78_offline_repair_replay_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/run_m78_offline_repair_replay.py`.
- Fixed policy: `offline_confidence_log_depth_radius0p5_cap24_fixed_replay_v0`.
- M77 source policy: `offline_confidence_log_depth_radius0p5_cap24`.
- M77 reproduction: top5 mismatch 0, target-rank mismatch 0.
- Selected proposals: 926.
- Matched proposal rows: 98.
- Proposal precision: 0.105832.
- Scan target recall: 49 / 65 = 0.753846.
- Query target detected: 147 / 195 = 0.753846.
- Top5 success: 60 / 195 = 0.307692.
- Delta vs M75 detector top5: +9 rows.
- Delta vs H001 real memory-trust policy: -97 rows.
- Selected next route: `fixed_offline_repair_ready_for_runner_insertion_or_targeted_rerun`.
- Next unit: E005-M79 runner insertion point and targeted repair rerun plan.

논문 주장:

- M78 supports a detector-ranking repair argument over existing pre-cap candidates.
- M78 does not support final real RGB-D/open-vocabulary robustness because it is fixed offline replay, not a new detector run or downstream search execution.

에이전트 추론:

- The right next step is to connect this fixed policy to the runner path before any targeted long rerun.
- M78 should stay separate from the H001 memory-decision claim because H001 still outperforms the repaired detector-only row by 97 query rows.

## E005-M77 Offline Detector / Prompt Repair

사실:

- Status: `e005_m77_offline_detector_prompt_repair_design_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M77_offline_detector_prompt_repair_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m77_offline_detector_prompt_repair.py`.
- Pre-cap candidate rows: 23,742.
- Target rows: 65.
- Query rows: 195.
- Current replay top5: 51 / 195, matching M75 detector top5.
- Pre-cap detected targets: 54 / 65 = 0.830769.
- Current selected detected targets: 48 / 65 = 0.738462.
- Repair class counts: `rank_or_false_positive_budget_gap` 29, `selection_or_cap_lost_target` 6, `prompt_or_detector_recall_miss` 11, `already_top5_or_memory_recovered` 19.
- Best offline top5 policy: `offline_confidence_log_depth_radius0p5_cap24`, top5 60 / 195.
- Selected next route: `offline_replay_repair_candidate_then_targeted_detector_rerun`.
- Next unit: E005-M78 offline repair replay implementation.

논문 주장:

- M77 supports that part of the detector failure is repairable offline from existing pre-cap candidates.
- M77 does not support final real RGB-D/open-vocabulary robustness or deployable search policy because the repair is not yet fixed/replayed as the paper-facing detector route.

에이전트 추론:

- The next step should implement the selected offline policy as a fixed replay artifact and compare it against M75/M76, before launching another long detector run.
- The 11 pre-cap recall-miss targets still require prompt/label repair or an external proposal baseline later.

## E005-M76 Real Proposal Claim Boundary

사실:

- Status: `e005_m76_real_proposal_claim_boundary_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M76_real_proposal_claim_boundary_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m76_real_proposal_claim_boundary.py`.
- Diagnostic table ready: true.
- Selected next route: `include_diagnostic_table_then_offline_detector_prompt_repair`.
- Next unit: E005-M77 offline detector/prompt repair design.
- Detector aggregate precision: 0.051892.
- Detector aggregate scan-target recall: 0.813559.
- Target detected: 144 / 195 = 0.738462.
- Mean false positives before target: 8.104167.
- H001 vs `ConceptGraphs` same-batch: +43 success rows.
- H001 vs detector top5: +106 success rows.
- H001 vs context-agnostic memory trust: +1 success row and +0.097436 mean `ExpectedSearchCost`.

논문 주장:

- M75/M76 supports including the full real-proposal aggregate as a diagnostic real-proposal search table.
- M75/M76 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, real navigation `SR` / `SPL`, or human intent as the main contribution.

에이전트 추론:

- The next low-risk route is offline repair design over existing pre-cap candidate pools before launching another detector run.
- Prompt/label repair should follow only if M77 shows recall misses are recoverable; external 3D proposal baselines remain later, heavier pressure tests.

## E005-M75 Real Proposal Aggregate Route

사실:

- Status: `e005_m75_real_proposal_aggregate_ready_with_claim_boundary`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M75_real_proposal_aggregate_route_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/analyze_m75_real_proposal_aggregate_route.py --require-all`.
- Ready batches: `heldout_b01`, `heldout_b02`, `heldout_b03`.
- Missing batch: none.
- Query rows: 195.
- Query target detected: 144 / 195 = 0.738462.
- Mean target rank when detected: 9.104167.
- Mean false positives before target when detected: 8.104167.
- `real_detector_task_budget_v0`: 24 / 195 = 0.123077.
- `real_detector_confidence_top5_v0`: 51 / 195 = 0.261538.
- `real_static_memory_only_v0`: 141 / 195 = 0.723077.
- `real_task_context_memory_trust_reobserve_v0`: 157 / 195 = 0.805128.
- `real_context_agnostic_memory_trust_reobserve_v0`: 156 / 195 = 0.800000.
- `ConceptGraphs` same-batch strict bbox top5: 114 / 195 = 0.584615.
- Selected next route: `aggregate_diagnostic_ready_review_claim_boundary`.

논문 주장:

- M75 supports a full-denominator real-proposal diagnostic table.
- M75 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.
- Human task context remains unsupported as a main claim because H001 beats context-agnostic memory trust by only 1 / 195 row and has higher mean `ExpectedSearchCost`.

에이전트 추론:

- The aggregate should separate detector target-recall limits from memory-policy effects.
- E005-M76 decided to include this aggregate only as a diagnostic table and to design offline detector/prompt repair before any final robustness claim.

## E005-M74 Heldout B03 Query Metrics

사실:

- Status: `e005_m71_real_proposal_query_metric_ready_with_false_positive_boundary`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M71_real_proposal_query_metric_v0/heldout_b03/`.
- Command: `python experiments/E005_external_baseline_transition/tools/run_m71_real_proposal_query_metrics.py --batch-id heldout_b03`.
- Query rows: 60.
- Unique targets: 20.
- Query target detected: 48 / 60 = 0.800000.
- `real_detector_task_budget_v0`: 11 / 60 = 0.183333.
- `real_detector_confidence_top5_v0`: 21 / 60 = 0.350000.
- `real_context_agnostic_memory_trust_reobserve_v0`: 54 / 60 = 0.900000.
- `real_task_context_memory_trust_reobserve_v0`: 55 / 60 = 0.916667.
- `ConceptGraphs` same-batch strict bbox top5: 24 / 60 = 0.400000.
- Selected next route: `launch_remaining_batches_after_recording_false_positive_boundary`.

논문 주장:

- b03 supports a positive batch diagnostic for H001 over detector-only and `ConceptGraphs` same-batch retrieval.
- b03 alone does not support final robustness or navigation claims.

## E005-M73 Heldout B03 Detector Verification

사실:

- Status: `e005_m70_real_proposal_detector_batch_ready_with_false_positive_load`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M70_full_denominator_real_proposal_detector_verification_v0/heldout_b03/`.
- Command: `python experiments/E005_external_baseline_transition/tools/verify_m70_full_denominator_real_proposal_detector_batch.py --batch-id heldout_b03 --require-ready`.
- Expected files ready: 12 / 12.
- Prediction rows: 400.
- Matched targets: 16.
- Scan target recall smoke: 0.800000.
- Proposal precision smoke: 0.040000.

## E005-M74 Heldout B02 Query Metrics

사실:

- Status: `e005_m71_real_proposal_query_metric_ready_target_detection_weak`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M71_real_proposal_query_metric_v0/heldout_b02/`.
- Command: `python experiments/E005_external_baseline_transition/tools/run_m71_real_proposal_query_metrics.py --batch-id heldout_b02`.
- Query rows: 69.
- Unique targets: 23.
- Query target detected: 42 / 69 = 0.608696.
- `real_detector_task_budget_v0`: 5 / 69 = 0.072464.
- `real_detector_confidence_top5_v0`: 9 / 69 = 0.130435.
- `real_context_agnostic_memory_trust_reobserve_v0`: 54 / 69 = 0.782609.
- `real_task_context_memory_trust_reobserve_v0`: 54 / 69 = 0.782609.
- `ConceptGraphs` same-batch strict bbox top5: 45 / 69 = 0.652174.
- Selected next route: `repair_real_detector_or_prompt_route_before_remaining_batches`.

논문 주장:

- b02 supports a failure-boundary diagnostic, not a robustness claim.
- The weak target detection rate means final real RGB-D/open-vocabulary robustness remains unsupported.
- Human task-context main contribution remains unsupported because H001 and context-agnostic memory trust are tied on b02.

에이전트 추론:

- b03 later confirmed that the detector/prompt weakness is systematic enough to require claim-boundary handling.
- The aggregate should separate memory-policy gains from detector target-recall limitations.

## E005-M73 Heldout B02 Detector Verification

사실:

- Status: `e005_m70_real_proposal_detector_batch_ready_with_false_positive_load`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M70_full_denominator_real_proposal_detector_verification_v0/heldout_b02/`.
- Command: `python experiments/E005_external_baseline_transition/tools/verify_m70_full_denominator_real_proposal_detector_batch.py --batch-id heldout_b02 --require-ready`.
- Expected files ready: 12 / 12.
- Prediction rows: 264.
- Pre-cap candidate rows: 6,799.
- Matched targets: 14 / 17.
- Scan target recall smoke: 0.8235294117647058.
- Proposal precision smoke: 0.05303030303030303.
- False-positive proposal rate smoke: 0.946969696969697.

논문 주장:

- M73 supports detector completion and schema/matching readiness for `heldout_b02`.
- M73 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

## E005-M72 Sequential Remaining Detector Launch

사실:

- Status: `e005_m69_real_proposal_detector_job_launched` for `heldout_b02`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M69_full_denominator_real_proposal_detector_launch_v0/heldout_b02/`.
- Command: `python experiments/E005_external_baseline_transition/tools/launch_m69_full_denominator_real_proposal_batch.py --batch-id heldout_b02`.
- tmux session: `e005_m69_real_proposal_heldout_b02`.
- Log: `logs/20260525_111101_e005_m69_real_proposal_heldout_b02.log`.
- Working directory: `/home/yoohyun/research2`.
- Input dir: `experiments/E005_external_baseline_transition/artifacts/E005-M68_full_denominator_real_proposal_bridge_plan_v0/batches/heldout_b02/`.
- Output dir: `experiments/E005_external_baseline_transition/artifacts/E005-M69_full_denominator_real_proposal_detector_run_v0/heldout_b02/`.
- Expected files: `coverage.json`, `container_output/real_proposals.jsonl`, `matching/coverage.json`, `validator/coverage.json`.
- Verification command: `python experiments/E005_external_baseline_transition/tools/verify_m70_full_denominator_real_proposal_detector_batch.py --batch-id heldout_b02 --require-ready`.
- `heldout_b03` launch status: launched.
- `heldout_b03` tmux session: `e005_m69_real_proposal_heldout_b03`.
- `heldout_b03` log: `logs/20260525_234108_e005_m69_real_proposal_heldout_b03.log`.
- `heldout_b03` output dir: `experiments/E005_external_baseline_transition/artifacts/E005-M69_full_denominator_real_proposal_detector_run_v0/heldout_b03/`.
- `heldout_b03` verification command: `python experiments/E005_external_baseline_transition/tools/verify_m70_full_denominator_real_proposal_detector_batch.py --batch-id heldout_b03 --require-ready`.

논문 주장:

- M72 is a launch event, not a performance result.
- Final real RGB-D/open-vocabulary robustness remains blocked even after `heldout_b02` / `heldout_b03` completion because aggregate detector precision and false-positive load remain weak.

에이전트 추론:

- Sequential launch is preferable here because the same Docker image/build/run path and GPU are shared by both remaining detector batches.

## E005-M71 Real Proposal Query Metrics

사실:

- Status: `e005_m71_real_proposal_query_metric_ready_with_false_positive_boundary`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M71_real_proposal_query_metric_v0/heldout_b01/`.
- Command: `python experiments/E005_external_baseline_transition/tools/run_m71_real_proposal_query_metrics.py --batch-id heldout_b01`.
- Query rows: 66.
- Unique targets: 22.
- Query target detected: 54 / 66 = 0.818182.
- Mean target rank when detected: 8.777778.
- Mean false positives before target when detected: 7.777778.
- `real_detector_task_budget_v0`: 8 / 66 = 0.121212.
- `real_detector_confidence_top5_v0`: 21 / 66 = 0.318182.
- `real_static_memory_only_v0`: 45 / 66 = 0.681818.
- `real_context_agnostic_memory_trust_reobserve_v0`: 48 / 66 = 0.727273.
- `real_task_context_memory_trust_reobserve_v0`: 48 / 66 = 0.727273.
- `ConceptGraphs` same-batch strict bbox top5: 45 / 66 = 0.681818.
- Selected next route: `launch_remaining_batches_after_recording_false_positive_boundary`.

논문 주장:

- M71 supports a `heldout_b01` query-level diagnostic for real RGB-D/open-vocabulary proposals.
- M71 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, real navigation `SR` / `SPL`, or human task-context main contribution.

에이전트 추론:

- Remaining batches are worth launching because target detection is usable and H001 memory trust beats real detector-only baselines on this batch.
- The context-specific part of H001 is still weak: H001 and context-agnostic memory trust both reach 48 / 66, while H001 has higher mean `ExpectedSearchCost`.

## E005-M70 Full-Denominator Detector Verification

사실:

- Status: `e005_m70_real_proposal_detector_batch_ready_with_false_positive_load`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M70_full_denominator_real_proposal_detector_verification_v0/heldout_b01/`.
- Command: `python experiments/E005_external_baseline_transition/tools/verify_m70_full_denominator_real_proposal_detector_batch.py --batch-id heldout_b01 --require-ready`.
- Batch: `heldout_b01`.
- Expected files ready: 12 / 12.
- Prediction rows: 261.
- Pre-cap candidate rows: 5,310.
- Matched targets: 18 / 22.
- Scan target recall smoke: 0.8181818181818182.
- Proposal precision smoke: 0.06896551724137931.
- False-positive proposal rate smoke: 0.9310344827586207.
- Mean matched centroid error: 0.5892226111111111m.
- Next recommended unit: `E005-M71 heldout_b01 real proposal query-level metric conversion`.

논문 주장:

- M70 supports detector completion and schema/matching readiness for `heldout_b01`.
- M70 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

에이전트 추론:

- The detector output is ready for query-level conversion, but the high false-positive rate makes rank/budget/search-cost evaluation mandatory before launching further batches as paper evidence.

## E005-M69 Full-Denominator Detector Launch

사실:

- Status: `e005_m69_real_proposal_detector_job_launched`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M69_full_denominator_real_proposal_detector_launch_v0/heldout_b01/`.
- Batch: `heldout_b01`.
- tmux session: `e005_m69_real_proposal_heldout_b01`.
- Log: `logs/20260524_004619_e005_m69_real_proposal_heldout_b01.log`.
- Working directory: `/home/yoohyun/research2`.
- Input dir: `experiments/E005_external_baseline_transition/artifacts/E005-M68_full_denominator_real_proposal_bridge_plan_v0/batches/heldout_b01/`.
- Output dir: `experiments/E005_external_baseline_transition/artifacts/E005-M69_full_denominator_real_proposal_detector_run_v0/heldout_b01/`.
- Expected files: `coverage.json`, `container_output/real_proposals.jsonl`, `matching/coverage.json`, `validator/coverage.json`.
- Next recommended unit: `E005-M70 full-denominator real proposal detector completion verification`.

논문 주장:

- M69 is a launch event, not a performance result.
- Final real RGB-D/open-vocabulary robustness remains blocked until detector completion and query-level metric conversion.

## E005-M68 Full-Denominator Real Proposal Bridge

사실:

- Status: `e005_m68_full_denominator_real_proposal_bridge_plan_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M68_full_denominator_real_proposal_bridge_plan_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m68_full_denominator_real_proposal_bridge.py`.
- Query rows: 195.
- Ready scans: 9 / 9.
- Object targets: 65.
- Prompt labels: 22.
- Sampled frames: 214.
- Batches: `heldout_b01` 66 rows, `heldout_b02` 69 rows, `heldout_b03` 60 rows.
- Row-level overlap with E003-M75: 0.
- Next recommended unit: `E005-M69 full-denominator real proposal detector batch launch`.

논문 주장:

- M68 is input materialization and command planning, not a robustness result.
- Final real RGB-D/open-vocabulary robustness remains blocked until detector execution and query-level metric conversion are complete.
- Real navigation `SR` / `SPL` remains blocked.

에이전트 추론:

- Because E003-M75 has 0 row-level overlap with the M38/M45 heldout denominator, the full 195-row real-proposal denominator must be executed rather than partially reused.
- Running by heldout batch is more operationally reliable than a single 9-scan detector run.

## E005-M67 Real RGB-D / Open-Vocabulary Robustness Route

사실:

- Status: `e005_m67_real_rgbd_ov_robustness_route_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M67_real_rgbd_ov_robustness_route_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m67_real_rgbd_ov_robustness_route.py`.
- Selected route: `scale_real_proposal_bridge_to_m38_heldout_denominator`.
- M38/M45 heldout denominator: 195 query rows, 9 scans, 65 target rows.
- Current E003-M75 real-proposal bridge: 96 query rows, target detected 87 rows, bounded repair success 33 rows.
- Denominator mismatch: 99 query rows.
- Next recommended unit: `E005-M68 full-denominator real RGB-D proposal bridge plan`.

논문 주장:

- M67 does not add a performance claim. It selects the route needed before claiming final real RGB-D/open-vocabulary robustness.
- Final real RGB-D/open-vocabulary robustness remains blocked until the scaled denominator is executed and evaluated.
- Real navigation `SR` / `SPL` remains blocked until a simulator/navmesh/trajectory protocol exists.

에이전트 추론:

- Scaling the real-proposal bridge to the M38/M45 denominator is more valuable now than starting `OpenMask3D`, `HOV-SG`, or real navigation, because it attacks the biggest reviewer weakness in the current evidence table.
- Human intent should remain secondary because M66 found only 1 task-context-specific gain row.

## E005-M66 External Baseline Failure Boundary

사실:

- Status: `e005_m66_external_baseline_failure_boundary_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M66_external_baseline_failure_boundary_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/analyze_m66_external_baseline_failure_boundary.py`.
- Query rows: 195.
- H001 vs `ConceptGraphs`: both_success 112, H001-only 60, `ConceptGraphs`-only 2, both_fail 21.
- H001 vs `Open3DSG` predicted-vocabulary adapter: both_success 133, H001-only 39, `Open3DSG`-only 11, both_fail 12.
- `Open3DSG` predicted-vocabulary vs primary-label adapter: both_success 78, vocab-only 66, primary-only 3, both_fail 48.
- Human intent boundary: no task-context-specific difference 194, task-context-specific gain 1.

논문 주장:

- M66 supports a proxy-search failure-boundary claim, not final real RGB-D/open-vocabulary robustness.
- `Open3DSG` predicted-vocabulary adapter is a bounded vocabulary-mismatch repair, not a method contribution.
- Human intent remains a structured task-context ablation, not the main claim.

에이전트 추론:

- The table boundary is now strong enough to move to real RGB-D/open-vocabulary robustness route planning.
- Real navigation `SR` / `SPL` should still wait until the robustness bridge has a stable denominator and baseline set.

## E005-M65 Open3DSG Table Integration

사실:

- Status: `e005_m65_open3dsg_table_integration_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M65_open3dsg_table_integration_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m65_open3dsg_table_integration.py`.
- H001: 172 / 195.
- `Open3DSG` predicted-vocabulary adapter: 144 / 195.
- `Open3DSG` primary-label adapter: 81 / 195.
- `ConceptGraphs`: 114 / 195.
- `Open3DSG` predicted-vocabulary adapter main table include: true.
- `Open3DSG` primary-label adapter main table include: false.
- Human intent reflected as structured `task_context_id`: true.
- Human intent main claim ready: false.

논문 주장:

- `Open3DSG` predicted-vocabulary adapter can be included as a bounded external scene-graph baseline row.
- H001 remains stronger than both `ConceptGraphs` and the bounded `Open3DSG` adapter under the 195-row proxy-search denominator.
- Human intent is a secondary ablation in E005, not the main contribution.

에이전트 추론:

- E005 did reflect human intent, but only as structured task context that conditions memory trust / re-observation.
- Since H001 beats context-agnostic memory trust by only 1 success row, the paper should not be framed as human-intent understanding.

## E005-M64 Open3DSG Vocabulary Expansion Policy

사실:

- Status: `e005_m64_open3dsg_vocab_expansion_policy_verified`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M64_open3dsg_vocab_expansion_policy_v0/`.
- Data output: `local_dataset/Open3DSG_bridge/E005-M64_vocab_expansion_policy_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/run_m64_open3dsg_vocab_expansion_policy.py --require-object-candidates-ready`.
- Verification: `python experiments/E005_external_baseline_transition/tools/verify_m64_open3dsg_vocab_expansion_policy.py --require-ready`.
- Query rows: 195.
- Query candidate/eval rows: 1,533.
- Policy rows: 585.
- Strict bbox top5: 144 / 195 = 0.738462.
- Relaxed bbox 1m top3: 147 / 195 = 0.753846.
- Center strict top5: 42 / 195 = 0.215385.
- Policy allowed inputs: `scan_id`, `query_label`, `candidate_label`, `candidate_score`, `candidate_rank`.
- Blocked before ranking: `gt_object_label`, `id2name_label`, `target_uid`, `object_instance_id_rescan`, target geometry, target success labels.
- Leakage audit: pass.

논문 주장:

- M64 promotes the M63 diagnostic into a bounded, leakage-safe `Open3DSG` vocabulary-adapter policy.
- It can support a paper-table candidate row for `Open3DSG` predicted-vocabulary adapter, but it is not standalone method novelty.
- Final real RGB-D/open-vocabulary robustness and real navigation `SR` / `SPL` remain unsupported.

에이전트 추론:

- The previous `Open3DSG` gap was largely a vocabulary/query adapter mismatch under the H001 query contract.
- E005-M65 decided to include this row in the claim-evidence ledger as a bounded external baseline, without overstating it as a full external mapper win.

## E005-M63 Open3DSG Route Decision

사실:

- Status: `e005_m63_open3dsg_route_decision_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M63_open3dsg_route_decision_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/analyze_m63_open3dsg_route_decision.py`.
- Current corrected `Open3DSG` strict bbox top5: 81 / 195 = 0.415385.
- Current corrected `Open3DSG` relaxed bbox 1m top3: 90 / 195 = 0.461538.
- Diagnostic predicted-term strict bbox top5: 144 / 195 = 0.738462.
- Diagnostic predicted-term relaxed bbox 1m top3: 147 / 195 = 0.753846.
- Target object present in exported top20 rows: 171 / 195.
- Target has primary-label candidate: 57 / 195.
- Target has predicted-term candidate: 93 / 195.
- No-primary but expanded-term candidate rows: 51 / 195.

논문 주장:

- M63 is diagnostic only. It does not make the expanded-term result a paper claim yet.
- It supports the next bounded repair route because the immediate blocker appears to be vocabulary/query adapter mismatch.

에이전트 추론:

- Selected route: `bounded_open3dsg_predicted_vocab_expansion_repair_next`.
- E005-M64 implemented the predicted-vocabulary expansion as a leakage-safe policy and verified that the diagnostic gain survives.

## E005-M62 Open3DSG Result Interpretation

사실:

- Status: `e005_m62_open3dsg_result_interpretation_ready_primary_label_below_conceptgraphs`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M62_open3dsg_result_interpretation_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/analyze_m62_open3dsg_result_interpretation.py`.
- `Open3DSG` bridge feasibility ready: true.
- `Open3DSG` main-table performance baseline ready: false.
- `Open3DSG` primary-label main-table performance baseline ready: false.
- H001 minus corrected `Open3DSG` strict bbox top5: +91 success rows.
- `ConceptGraphs` minus corrected `Open3DSG` strict bbox top5: +33 success rows.

논문 주장:

- M61/M60 supports an `Open3DSG` bridge feasibility claim.
- Current `Open3DSG` does not support a strong external baseline performance claim.

에이전트 추론:

- The dominant failure signal is coverage/vocabulary mismatch, not only ranking: corrected strict policy has 72 `no_same_label_candidates`, 36 `target_object_not_in_open3dsg_candidates`, and 6 `target_present_but_rank_gt_budget`.
- M63 selected bounded predicted-vocabulary expansion before moving to `HOV-SG` / `OpenMask3D`.

## E005-M61 Open3DSG Denominator-Aligned Export Plan

사실:

- Status: `e005_m61_open3dsg_denominator_aligned_export_plan_ready`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M61_denominator_aligned_export_plan_v0/`.
- Data output: `local_dataset/Open3DSG_bridge/E005-M61_denominator_aligned_export_plan_v0/`.
- Command: `python experiments/E005_external_baseline_transition/tools/plan_m61_open3dsg_denominator_aligned_export.py`.
- Launch script: `python experiments/E005_external_baseline_transition/tools/launch_m61_open3dsg_denominator_export.py --launch --min-gpu-free-mib 20000`.
- Verification script: `python experiments/E005_external_baseline_transition/tools/verify_m61_open3dsg_denominator_export.py --require-ready`.
- Runtime status: `completed`.
- tmux: `e005_m61_open3dsg_denominator_export`.
- Runtime output: `local_dataset/Open3DSG_bridge/E005-M61_denominator_aligned_export_v0/`.
- Runtime artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M61_denominator_aligned_export_v0/`.
- Runtime log: `logs/20260523_150156_e005_m61_open3dsg_denominator_export.log`.
- Runtime object candidate rows: 7,600.
- Completed batches: 51 / 51.
- Query scan overlap: 9 / 9.
- M38/M45 query denominator rows: 195.
- Query scan count: 9.
- Query rows by `Open3DSG` source split: train 123, validation 72.
- Target subgraphs by source split: train 29, validation 22, total 51.
- Preprocessed-ready target subgraphs: 51 / 51.
- Feature-ready target subgraphs: 51 / 51.
- Validation-only smoke target: 3 scans, 22 subgraphs, 72 / 195 query rows.
- Full denominator target: 9 scans, 51 subgraphs, 195 / 195 query rows.
- Existing staged source modified: false.

논문 주장:

- M61 supports a denominator-alignment readiness claim for `Open3DSG`.
- It establishes denominator-aligned `Open3DSG` export readiness but not strong `Open3DSG` performance.

에이전트 추론:

- The runtime patch lets the test dataloader use the selected train+validation target relationships without modifying `/home/yoohyun/research/local_dataset/Open3DSG_staged`.
- The dependent M60 rerun is complete, so the next issue is claim boundary rather than export coverage.

## E005-M60 Open3DSG Query Conversion Contract

사실:

- Contract status: `e005_m60_open3dsg_query_conversion_contract_ready_for_conversion_smoke`.
- Conversion status: `e005_m60_open3dsg_query_conversion_verified`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M60_open3dsg_query_conversion_m61_v0/`.
- Data output: `local_dataset/Open3DSG_bridge/E005-M60_query_conversion_m61_v0/`.
- Verification: `python experiments/E005_external_baseline_transition/tools/verify_m60_open3dsg_query_conversion_contract.py`.
- Conversion command: `python experiments/E005_external_baseline_transition/tools/run_m60_open3dsg_query_conversion.py --require-object-candidates-ready`.
- Conversion verification: `python experiments/E005_external_baseline_transition/tools/verify_m60_open3dsg_query_conversion.py --require-policy-rows`.
- M58 object schema: `open3dsg_object_candidate_jsonl_v0`.
- M58 query schema: `open3dsg_query_candidate_jsonl_v0`.
- M38/M45 denominator rows: 195 / 195.
- M61 object candidate rows: 7,600.
- M61 completed batches: 51.
- M61 candidate scan count: 9.
- M38/M45 query scan count: 9.
- Scan overlap count: 9.
- Query candidate rows: 759.
- Candidate eval rows: 759.
- Policy rows: 585.
- Strict bbox top5 success: 81 / 195 = 0.415385.
- Relaxed bbox 1m top3 success: 90 / 195 = 0.461538.
- Center strict top5 success: 21 / 195 = 0.107692.
- Join rule: `scan_id == current_rescan_id`, normalized `candidate_label == label_canonical`, rank by `Open3DSG` `candidate_score`.
- Leakage rule: do not use `target_uid`, `object_instance_id_rescan`, GT labels, `id2name`, or candidate-is-target fields before ranking.
- Planned policies: `open3dsg_objects_probs_bbox_strict_top5_v0`, `open3dsg_objects_probs_bbox_relaxed_1m_top3_v0`, `open3dsg_objects_probs_center_strict_top5_v0`.
- Planned metrics: target detected rate, query bridge success rate, target rank, `ExpectedSearchCost`, `AttemptSPL` proxy, old-location dead-end avoidance, failure classes.

논문 주장:

- M60 supports a conversion-harness claim: the `Open3DSG` query-level conversion path is implemented and verified on the 195-row denominator.
- It does not establish a strong `Open3DSG` performance baseline because the primary-label adapter remains below `ConceptGraphs`.

에이전트 추론:

- This removes the previous coverage blocker and the target-geometry loading bug; the remaining issue is vocabulary/query adapter mismatch.
- The dependent M64 leakage-safe predicted-vocabulary expansion is complete; the next action is M65 claim-boundary integration.

## E005-M59 Open3DSG Object Candidate Export Smoke

사실:

- Status: `e005_m59_open3dsg_object_export_smoke_ready`.
- tmux session: `e005_m59_open3dsg_object_export`.
- Relaunch time: 2026-05-23 14:06 KST.
- Relaunch command: `python experiments/E005_external_baseline_transition/tools/launch_m59_open3dsg_object_export_smoke.py --launch --min-gpu-free-mib 24000`.
- Workdir: `/home/yoohyun/research2`.
- Log: `logs/20260523_140609_e005_m59_open3dsg_object_export.log`.
- Output: `local_dataset/Open3DSG_bridge/E005-M59_object_candidate_export_smoke_v0/`.
- Artifact: `experiments/E005_external_baseline_transition/artifacts/E005-M59_object_candidate_export_smoke_v0/`.
- Verification command: `python experiments/E005_external_baseline_transition/tools/verify_m59_open3dsg_object_export_smoke.py --require-ready`.
- Initial verification command: `python experiments/E005_external_baseline_transition/tools/verify_m59_open3dsg_object_export_smoke.py`.
- Completion verification time: 2026-05-23 14:10 KST; tmux running false, source modified false, candidate rows 180, completed batches 1.
- Expected files ready: `open3dsg_object_candidates.jsonl`, `open3dsg_object_candidates.completed.jsonl`, `open3dsg_object_candidates.manifest.json`.
- Previous failure reason: CUDA OOM while loading `InstructBLIP`; log reported GPU 0 had 93 MiB free at failure and the Open3DSG process used about 16.35 GiB.
- Repair decision: prefer lower-memory object-only export patch over blind GPU-exclusive relaunch.
- Repair patch: `OPEN3DSG_OBJECT_DUMP_SKIP_BLIP_LOAD=1` skips pretrained `InstructBLIP` loading; `OPEN3DSG_OBJECT_DUMP_OBJECT_ONLY=1` stubs relation prediction because object candidates do not require relation captioning.
- Relaunch preflight: default `--min-gpu-free-mib 24000`.
- Relaunch GPU check: 2026-05-23 14:06 KST, 28,887 MiB free, launch executed true.

논문 주장:

- This step establishes that the lower-memory object-candidate export path can write rows.
- It does not establish `Open3DSG` query-level object-search performance because the first completed batch is not denominator-aligned.

에이전트 추론:

- The next dependent action is targeted denominator-aligned export, not another generic first-batch smoke.

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
- Source hypothesis: `archive/hypothesis/CAND-001/H001_stale-object-memory/`
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
