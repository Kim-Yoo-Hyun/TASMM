# E003-M53 Bbox-Depth Continuation Repair Gate

## Status

bbox_continuation_repair_gate_ready

## 사실

- M33 scaled bbox-depth: 8 scans / 192 frames.
- M33 matched / FP / precision: 204 / 3210 / 0.05975395430579965.
- M52 scaled `Grounded-SAM` recommended: False.
- M52 target loss cause: `mask_projection_candidate_dropout_before_matching`.
- Selected immediate route: `search_critical_bbox_failure_boundary_first`.
- Next recommended unit: `E003-M54 search-critical bbox-depth failure-boundary audit`.

## Route Ranking

- `search_critical_bbox_failure_boundary_first`: score 46, type `current_best_route_defense_and_repair`, next `E003-M54 search-critical bbox-depth failure-boundary audit`.
- `deployable_bbox_suppression_repair_now`: score 30, type `proposal_filter_repair`, next `E003-M54 deployable bbox-depth suppression repair smoke`.
- `openmask3d_feasibility_now`: score 27, type `external_3d_instance_baseline`, next `E003-M54 OpenMask3D scene-format feasibility gate`.
- `conceptgraphs_mapping_baseline_now`: score 19, type `open_vocabulary_mapping_baseline`, next `E005 ConceptGraphs mapping baseline adapter planning`.
- `open3dsg_mapping_baseline_now`: score 16, type `scene_graph_mapping_baseline`, next `E005 scene-graph mapping baseline planning`.
- `hovsg_navigation_mapping_baseline_now`: score 10, type `hierarchical_mapping_navigation_baseline`, next `E005 HOV-SG navigation/mapping baseline planning`.

## External Baseline Boundary

- `OpenMask3D`: role `later_external_3d_instance_proposal_baseline`; not immediate: M52 only showed the current Grounded-SAM route should not scale; the current best bbox-depth route still needs a defensible failure-boundary bridge before another heavy external dependency.
- `Open3DSG`: role `later_scene_graph_mapping_baseline`; not immediate: The current blocker is proposal-row false positives and target dropout under real RGB-D/open-vocabulary output, not 3D scene graph construction quality.
- `ConceptGraphs`: role `later_open_vocabulary_mapping_baseline`; not immediate: It is a mapping stack, not the smallest test for the current bbox-depth proposal failure boundary.
- `HOV-SG`: role `later_hierarchical_mapping_navigation_baseline`; not immediate: Navigation/hierarchy claims are still blocked by real navigation source and downstream benchmark integration.
- `OVIR-3D`: role `fallback_3d_retrieval_baseline`; not immediate: Its retrieval-oriented output is less direct for proposal precision/recall and stale-memory search rows.

## 논문 주장

- E003-M53 does not create a paper result claim.
- It fixes the immediate route after negative `Grounded-SAM` evidence.
- Real RGB-D/open-vocabulary robustness remains unsupported.

## 에이전트 추론

- The next step should not be another heavy external baseline before the current best bbox-depth route has a search-critical failure boundary.
- `OpenMask3D` is a better external proposal-quality baseline than `Open3DSG`, `ConceptGraphs`, or `HOV-SG` for this specific E003 failure, but it is still not the immediate next unit.
- `Open3DSG`, `ConceptGraphs`, and `HOV-SG` are more appropriate for later map/scene-graph/navigation baseline expansion.

## 사용자 판단 필요

- None if E003-M54 search-critical bbox-depth failure-boundary audit is accepted as the next immediate unit.
