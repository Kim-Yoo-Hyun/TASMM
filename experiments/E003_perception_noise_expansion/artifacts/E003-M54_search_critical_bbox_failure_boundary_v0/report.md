# E003-M54 Search-Critical Bbox Failure Boundary

## Status

search_critical_bbox_failure_boundary_ready

## 사실

- E001 query rows: 294.
- E002 reachable-first rows: 267.
- M33 detector scans / frames: 8 / 192.
- E001 current `rescan_id` overlap with M33 detector scans: 0.
- Exact current query-instance joins: 0.
- Reference-memory-only joins: 120.
- Label overlap count: 21.
- Existing E001/E002 search failures with label-level detector risk: 7.
- Next recommended unit: `E003-M55 dynamic-pair-aligned real-proposal bridge gate`.

## Search-Critical Labels

- `pillow`: priority 8, E001 fail 4/27, E002 fail 2/12, M33 FP 76, target recall 0.5806451612903226, visible misses 2, risk ['low_target_recall', 'depth_visible_proxy_target_miss'].
- `chair`: priority 7, E001 fail 3/117, E002 fail 3/111, M33 FP 129, target recall 0.7894736842105263, visible misses 0, risk ['high_false_positive_load'].
- `plant`: priority 6, E001 fail 0/6, E002 fail 0/6, M33 FP 176, target recall 0.5185185185185185, visible misses 1, risk ['high_false_positive_load', 'low_proposal_precision', 'low_target_recall', 'depth_visible_proxy_target_miss'].
- `shelf`: priority 6, E001 fail 0/3, E002 fail 0/3, M33 FP 133, target recall 0.5, visible misses 1, risk ['high_false_positive_load', 'low_proposal_precision', 'low_target_recall', 'depth_visible_proxy_target_miss'].
- `sofa`: priority 6, E001 fail 0/3, E002 fail 0/3, M33 FP 117, target recall 0.6, visible misses 1, risk ['high_false_positive_load', 'low_proposal_precision', 'low_target_recall', 'depth_visible_proxy_target_miss'].
- `couch`: priority 4, E001 fail 0/3, E002 fail 0/3, M33 FP 23, target recall 0.3333333333333333, visible misses 1, risk ['low_proposal_precision', 'low_target_recall', 'depth_visible_proxy_target_miss'].
- `table`: priority 3, E001 fail 0/12, E002 fail 0/12, M33 FP 116, target recall 0.8, visible misses 0, risk ['high_false_positive_load', 'low_proposal_precision'].
- `box`: priority 3, E001 fail 0/15, E002 fail 0/15, M33 FP 111, target recall 0.75, visible misses 0, risk ['high_false_positive_load', 'low_proposal_precision'].
- `couch table`: priority 2, E001 fail 0/21, E002 fail 0/21, M33 FP 86, target recall 0.5, visible misses 0, risk ['low_proposal_precision', 'low_target_recall'].
- `bench`: priority 2, E001 fail 0/6, E002 fail 0/6, M33 FP 70, target recall 0.5, visible misses 0, risk ['low_proposal_precision', 'low_target_recall'].

## 논문 주장

- E003-M54 does not establish a final real RGB-D/open-vocabulary search robustness claim.
- E003-M54 supports a claim boundary: current M33/M45 detector failures cannot be causally attached to E001/E002 current search instances because the detector-ready scans do not overlap with E001 current rescans.
- M54 can only support a label-level bridge risk until a dynamic-pair-aligned real-proposal denominator exists.

## 에이전트 추론

- `chair` and `pillow` are the strongest immediate bridge labels because they already cause E002 search failures and also show M33 detector risk.
- High false-positive labels such as `plant`, `shelf`, `sofa`, `table`, and `box` remain detector-pressure risks, but they are not yet proven to cause E001/E002 decision failure in the current artifact alignment.
- The next step should build a dynamic-pair-aligned bridge or explicitly convert the claim to label-level detector stress; another external detector alone will not fix the missing E001/E002 current-rescan join.

## 사용자 판단 필요

- None if `E003-M55 dynamic-pair-aligned real-proposal bridge gate` is accepted as the next route.
- Choose immediate `OpenMask3D` only if the goal is proposal-quality evidence with a weaker search-bridge claim.
