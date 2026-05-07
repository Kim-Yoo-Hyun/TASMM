# E001-M01 Pair Manifest

## Status

ready

## 사실

- Dataset root: `/home/yoohyun/research2/local_dataset`
- Manifest version: `e001_pair_manifest_v0`
- Metadata groups scanned: 478
- Metadata pairs scanned: 1004
- Local `3RScan` scan directories: 54
- Local semantic payload triplets: 54
- Local sequence payloads: 8
- `3DSSG` object scan entries: 1482
- `3DSSG` relationship scan entries: 1335
- `ready_minimal` pairs: 13
- Blocked pairs: 991
- Output directory: `/home/yoohyun/research2/experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M01_pair_manifest_v0`

## Coverage

| Split | Total pairs | Ready minimal | Blocked |
| --- | ---: | ---: | ---: |
| `test` | 101 | 0 | 101 |
| `train` | 793 | 8 | 785 |
| `validation` | 110 | 5 | 105 |

## Main Exclusion Reasons

| Reason | Count |
| --- | ---: |
| `missing_rescan_ply` | 982 |
| `missing_rescan_scan_dir` | 982 |
| `missing_rescan_segs` | 982 |
| `missing_rescan_semseg` | 982 |
| `missing_reference_ply` | 920 |
| `missing_reference_scan_dir` | 920 |
| `missing_reference_segs` | 920 |
| `missing_reference_semseg` | 920 |
| `missing_reference_3dssg_relationships` | 101 |
| `missing_rigid_metadata` | 22 |

## 논문 주장

- This artifact supports the denominator and payload-coverage claim for E001.
- This artifact does not support dynamic object search performance, navigation `SR` / `SPL`, RGB-D robustness, open-vocabulary robustness, or human-intent claims.

## 에이전트 추론

- E001-M01 should keep blocked pairs in the manifest because paper reviewers will ask how much of `3RScan` / `3DSSG` was excluded before evaluation.
- `sequence` availability is recorded now so E003 can later reuse the same denominator without changing pair IDs.
- Query construction should use only `ready_minimal` rows and should decide significant moved / low-motion status separately.

## 사용자 판단 필요

- None for E001-M01. Continue to E001-M02 query construction.

## Outputs

- `manifest.jsonl`
- `coverage.json`
- `report.md`
