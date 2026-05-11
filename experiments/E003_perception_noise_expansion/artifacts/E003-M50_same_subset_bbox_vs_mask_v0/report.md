# E003-M50 Same-Subset Bbox-Depth Vs Mask-Depth

## Status

same_subset_comparison_ready

## 사실

- Bbox-depth backend: `groundingdino_rgbd_backproject_v0`.
- Mask-depth backend: `grounded_sam_mask_backproject_v0`.
- Same-subset config: max scans 1, frames 2, labels 12.
- Bbox prediction rows: 31.
- Mask prediction rows: 24.
- Bbox matched / FP / precision: 2 / 29 / 0.06451612903225806.
- Mask matched / FP / precision: 1 / 23 / 0.041666666666666664.
- Bbox mean matched centroid error m: 0.5913555.
- Mask mean matched centroid error m: 0.916258.
- Weak positive: False.
- Hard positive: False.
- Selected next route: `do_not_scale_grounded_sam_yet`.
- Real RGB-D/open-vocabulary claim ready: False.

## 논문 주장

- E003-M50 is a same-subset diagnostic gate, not a final robustness result.
- It does not support real RGB-D/open-vocabulary robustness, heldout transfer, or navigation/search claims.

## 에이전트 추론

- Mask-depth does not beat the bbox-depth route on the same subset; scaling now would be a weak use of compute.
- The next route should be chosen from this gate before any scaled `Grounded-SAM` rerun.

## 사용자 판단 필요

- None if the selected next route is accepted.
