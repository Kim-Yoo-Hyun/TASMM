# CAND-001: Intent- And Staleness-Aware Semantic Mapping

## Problem

사람 지시를 수행하는 robot은 semantic map 안의 모든 object memory를 같은 방식으로 믿으면 안 된다. 어떤 object는 현재 task에 중요하고, 어떤 object는 stale할 수 있으며, 어떤 relation은 다시 확인해야 한다.

## Existing Limitation

사실:

- DualMap, OpenIN, OGScene3D는 dynamic scenes, moved objects, temporal memory를 다룬다.
- Clio는 task가 map granularity를 결정해야 한다고 주장한다.
- LangMap은 scene/room/region/instance granularity를 benchmark로 분리한다.

에이전트 추론:

- 아직 "현재 human instruction에 필요한 semantic memory만 선택적으로 믿고 갱신한다"는 formulation은 선명한 빈틈으로 보인다.

## Why Semantic Mapping

- 핵심은 language parsing만도, navigation policy만도 아니다.
- map이 object, relation, timestamp, confidence, task relevance, re-observation need를 어떻게 저장하고 update하는지가 문제다.

## Evaluation Plan

Dataset / benchmark 후보:

- OpenIN-style Habitat dynamic domestic tasks
- AI2-THOR rearrangement / custom before-after RGB-D replay
- LangMap or HM3D-OVON for open-vocabulary static grounding sanity check

Metrics:

- stale false-positive rate
- moved-object recovery time
- text-to-object Recall@k
- task success
- query latency
- map size / update latency

Baselines:

- static object-centric semantic map
- time-decay confidence map
- DualMap-style global/local map
- oracle current object pose

## Feasibility Gate Update

사실:

- 2026-05-05 local check found 8 `3RScan` validation reference scans with RGB-D frames and poses.
- Those 8 scans are covered by local `3DSSG` object and relationship annotations.
- `3RScan.json` provides reference/rescan change metadata for those scans.
- No complete local reference-rescan RGB-D pair is currently available.
- One target reference-rescan semantic geometry pair is currently available.
- H001 target pair geometry validation passed: 11 / 11 rigid geometry joins, 6 / 6 removed absent in rescan `semseg.v2.json`, `object_direct_error_m` median 0.0611 m, max 0.2066 m.

에이전트 추론:

- CAND-001 remains viable as a hypothesis-stage semantic mapping candidate.
- The immediate gate is stale-label construction, not full `Habitat Simulator` or full dataset evaluation.
- If stale labels cannot be constructed from `3RScan` metadata or a small manual perturbation, CAND-001 becomes a benchmark-construction problem rather than a direct method problem.
- H001 value smoke suggests the current idea is stronger as stale-memory suppression than as moved-object recovery; recovery likely needs re-observation planning or a real paired rescan check.
- H001 unchanged-control smoke did not show over-stale behavior, but controls are weak negatives until real paired rescan geometry is staged.
- H001 re-observation smoke shows non-stale target availability but not recovery; only 0.4545 of moved rows have non-structural old context.
- Earlier H001 value summary kept CAND-001 alive but blocked main experiment transition until `real_pair_query_smoke` tied one real-pair geometry result to query-level behavior; this blocker is now superseded by later multi-pair and expansion gates.
- New local dataset root `/home/yoohyun/research2/local_dataset` makes the target pair graph-ready and semantic-geometry-ready.
- `real_pair_query_smoke` ties the one target pair to query-level behavior: `ours_staleness_v0` suppresses stale old-location returns and removed-object returns, but moved-object recovery remains 0.0000 with oracle gap 1.0000.
- Recovery-gap branch decision: add constrained `search_region_prior_smoke`, evaluated as search-region targeting rather than exact current-position prediction.
- `search_region_prior_smoke` shows that a simple old-location plus old relation-context search prior is weak: `semantic_context_r3` improves hit count over `old_location_r3` by 1 / 11 with larger area proxy, and `semantic_context_r4` matches `old_location_r4` with larger area proxy.
- Scene-level alignment changes the current local-pair interpretation: the only local ready semantic pair has 0 / 11 rigid moved rows above 1.0 m planar displacement after alignment.
- Metadata proxy staging selection found stronger candidate pairs. The current top target is `569d8f0d-72aa-2f24-8ac6-c6ee8d927c4b` -> `569d8f0f-72aa-2f24-89a6-77f8b8779ae9`, with 3 / 6 proxy moved rows above 1.0 m.
- The top target rescan semantic payload is now staged. The actual staged pair has 4 / 6 scene-aligned moved rows above 1.0 m.
- High-displacement pair geometry validation is partial: 5 / 6 rigid rows are row-valid, but removed absence is not ready.
- Row-filtered high-displacement query smoke shows a first positive recovery signal: on 3 significant moved rows, static scene-aligned memory has 0.0000 exact recovery and 1.0000 stale FP, while `label_nearest_current_observation` reaches 0.6667 exact recovery and `label_top3_current_observation` reaches 1.0000 Recall@3.
- Earlier CAND-001 promotion was blocked until H001 added instance-level visual/geometric evidence beyond label-only current observations; later `non_persistent_anchor_v0`, `uncertainty_topk_v0`, expansion gates, and budget baseline gate now make promotion decision possible.
- H001 multi-pair non-persistent validation is strict-pass positive after the latest staging rerun: 12 validated pairs, 10 significant moved rows, `non_persistent_anchor_v0` exact 0.8000, Recall@3 1.0000, stale FP 0.0000.
- H001 pillow hard failure shows the current method is not a defensible direct top-1 moved-object recovery claim: object `43` is valid but ranked 2 while candidate `46` wins top 1.
- H001 `uncertainty_topk_gate` is now designed as a bounded candidate-set return gate with Recall@k, `ExpectedSearchCost`, confidence calibration, and stale FP as primary checks.
- H001 `uncertainty_topk_v0` is implemented and strict-pass positive after the latest staging rerun: significant Recall@returned K 1.0000, mean `ExpectedSearchCost` 1.3000, stale FP 0.0000, low-motion static preserved 1.0000, two `pillow` hard rows captured at ranks 2 and 3.
- H001 `38770ca1` -> `38770ca3` staging increased validated pair coverage but did not increase significant moved rows; this exposes a proxy-target selection limitation.
- H001 `352e9c36` -> `74ef846e` staging increased significant moved rows by 1, but the new `stool` row is a trivial same-label case.
- H001 `f62fd5f8` -> `20c9939d` staging increased validated pair and control coverage but added 0 significant moved rows; this exposes a proxy-target selection limitation.
- H001 `0cac7578` -> `ddc73795` staging increased significant moved rows by 1 and added a hard high-ambiguity `pillow` row; top-1 recovery fails, but `uncertainty_topk_v0` captures the target at rank 3.
- H001 `280d8ebb` -> `10b17957` staging increased significant moved rows by 1 with a `gymnastic ball` row; it helps coverage but is not a hard instance-disambiguation case.
- H001 `f62fd5f8` -> `20c9939f` staging increased validated pair and control coverage but added 0 significant moved rows; this again exposes a proxy-target selection limitation.
- H001 `0cac762b` -> `0cac762f` staging increased significant moved rows by 1 with a `couch table` row; it helps the denominator but is a trivial same-label case.
- H001 `280d8ebb` -> `ea318260` staging increased significant moved rows by 1 and crossed the strict threshold with a `gymnastic ball` row; it helps coverage but remains a trivial same-label case.
- H001 strict-pass value summary concludes that the viable claim is `Task-Conditioned Stale Semantic Memory Update`, not final exact moved-object recovery or navigation.

## What Failure Teaches

- 성능이 오르지 않으면 bottleneck은 stale memory가 아니라 perception/re-identification일 수 있다.
- stale false-positive만 줄고 success가 떨어지면 conservative memory가 useful object recall을 해친 것이다.
- simulation에서는 되고 real replay에서 안 되면 pose noise, occlusion, re-identification이 핵심이다.

## Next Action

Benchmark shortlist와 H001 draft는 [archive/hypothesis/CAND-001](../archive/hypothesis/CAND-001/README.md) 아래로 이동했다.

현재 판단:

- H001 root Markdown은 `README.md`와 `01_setup.md`~`06_summary.md`로 병합했다.
- H001은 main experiment implementation으로 전환됐다.
- E001 내용은 `experiments/E001_semantic_pair_dynamic_search_proxy/README.md`에서 관리한다.
- H001 search-cost bridge gate는 proxy search success와 `AttemptSPL` proxy 기준으로 통과했다.
- H001 perception-noise gate는 controlled annotation-level proposal noise 기준으로 통과했다.
- H001 task-context gate는 structured context-conditioned budget 기준으로 통과했다.
- H001 budget baseline gate는 fixed top-k reviewer-risk 기준으로 통과했다. 단, high-value context는 `always_top5`와 같은 behavior이므로 experiment baseline에 fixed top-k를 포함해야 한다.
- 다음 작업은 E001 query construction 구현 단위 결정이다.
- Route A는 E002 search/navigation bridge에서 `Habitat Simulator` dynamic navigation episode로 확장할지 다시 판단한다.
