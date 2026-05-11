# Experiment Report

Updated: 2026-05-11

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
- E003-M58 fixes the direct current-rescan detector/evaluation bridge denominator for 7 search-failure query rows, 5 unique bridge targets, 4 current rescans, and `chair` / `pillow` prompts.
- Real navigation `SR` / `SPL` remains unsupported.
- Final real RGB-D/open-vocabulary robustness claim remains unsupported.

논문 주장:

- The currently defensible paper core is `Task-Conditioned Stale Semantic Memory Update`.
- The current paper should not claim a better detector, deployable navigation policy, or natural-language intention understanding.
- The final paper target is Direction B: `Task-Aware Dynamic Semantic Mapping for Open-Vocabulary Search and Navigation`.

에이전트 추론:

- The strongest current framing is a semantic memory decision problem: when a robot has stale semantic memory and noisy current proposals, task context changes memory trust, re-observation priority, search budget, and candidate visit order.
- The current work is more defensible as semantic mapping for embodied decision-making than as a pure perception or navigation paper.

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

- External baselines such as `OpenMask3D`, `ConceptGraphs`, `HOV-SG`, `Open3DSG`, `DualMap`, `VLFM`, `HM3D-OVON`, `GOAT-Bench`, and `3D-Mem` have not yet been run.
- E001/E002 still use proxy search metrics, not real executed navigation.
- E003 real perception evidence is not yet connected to E001/E002 current-rescan search-failure rows by detector output.
- The current 8-scan real-proposal artifact is too small for reliable heldout transfer.
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

## Reviewer Defense Priorities

논문 주장:

- The main claim should be: task/staleness-aware semantic memory update improves dynamic object search decisions under stale memory and noisy proposals.
- The method should be defended as a semantic mapping decision layer, not as a detector, language parser, or navigation planner.

에이전트 추론:

- Defense 1: formalize stale semantic memory as a decision problem with explicit inputs, forbidden information, outputs, and metrics.
- Defense 2: include ablations for task context, staleness score, memory trust, re-observation budget, reachable-first ordering, proposal filtering, and path/search-cost term.
- Defense 3: separate controlled annotation-proxy evidence, real proposal diagnostic evidence, and real navigation evidence in all tables.
- Defense 4: execute E003-M59 and E003-M60 so detector outputs can be evaluated against the M58 current-rescan search-failure rows rather than only label-level overlap.
- Defense 5: add at least one external 3D proposal/mapping baseline before final real RGB-D/open-vocabulary claim.
- Defense 6: keep structured task context as the controlled condition; add LLM parsing only as an adapter after the decision contract is stable.
- Defense 7: report negative results such as M45 and M50 as boundary evidence, not failed side experiments.
- Defense 8: scale from diagnostic scans to heldout splits only after the detector/evaluation bridge is stable.

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
- E003-M58 direct current-rescan detector/evaluation bridge design and E003-M59/M60 detector/evaluation table.
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

## Recommended Path

에이전트 추론:

- Use Direction A as the backbone now.
- Treat Direction B as the final target, not a separate replacement.
- The next technical step should be E003-M59: direct current-rescan detector bridge Docker run using the M58 command plan.
- After E003-M59/M60, choose whether to run an external 3D proposal baseline such as `OpenMask3D` or to first scale the direct bridge denominator.
- Do not claim real navigation `SR` / `SPL` until simulator, navmesh, or trajectory execution is integrated.

사용자 판단 필요:

- The final target is fixed as Direction B.
- A smaller intermediate submission remains possible if Direction A becomes independently strong before the broader mapping-navigation evidence is complete.
