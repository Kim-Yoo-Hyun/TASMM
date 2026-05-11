# E003-M34 Scaled Failure Analysis

## Status

scaled_pre_cap_failure_analysis_ready

## 사실

- M33 evaluated scans / frames: 8 / 192
- M33 matched targets / scan targets: 204 / 344
- M33 false-positive proposal rows: 3210
- M33 proposal precision: 0.05975395430579965
- M33 scan target recall: 0.5930232558139535
- Depth-consistent visible-proxy target rows: 154
- Visible-proxy missed target rows: 13
- Visible-proxy recall: 0.9155844155844156
- Top false-positive labels: plant 176, shelf 133, chair 129, sofa 117, table 116, box 111, cabinet 110, lamp 106
- Top visible-miss labels: picture 2, pillow 2, basket 1, couch 1, curtain 1, cushion 1, pile of books 1, plant 1
- M31 blocker status counts after M34: analyzed_not_resolved 1, partially_resolved_by_visibility_separation 1, reframed_after_scaling 1, resolved 1, unresolved 2, unresolved_claim_boundary 1
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M34 supports a scaled diagnostic failure analysis for the 8-scan real RGB-D/open-vocabulary proposal route.
- E003-M34 does not support a final real RGB-D/open-vocabulary robustness claim because false-positive load remains unresolved and visibility remains a proxy.
- E003-M34 does not support a deployable search-policy claim from real detector proposals yet.

## 에이전트 추론

- The previous scale-count blocker is resolved, but the main technical blocker moved to false-positive suppression.
- Scan-level missed targets are mostly not visible under the current sampled-frame proxy; visible-proxy misses are much smaller and should be reported separately.
- The next useful unit is a false-positive suppression route decision before connecting M33 proposals into E001/E002 search-policy tables.

## 사용자 판단 필요

- None for M34. Next recommended unit: `E003-M35 false-positive suppression route decision`.
