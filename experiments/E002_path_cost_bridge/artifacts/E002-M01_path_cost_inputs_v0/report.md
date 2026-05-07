# E002-M01 Path Cost Inputs

## Status

path_cost_inputs_ready

## 사실

- Input directory: `/home/yoohyun/research2/experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M02_query_construction_v0`
- Query rows: 294
- Candidate rows: 1248
- Rows with path-cost proxy: 294
- Rows with real navigation path cost: 0
- Significant moved rows: 33
- Old-location dead-end rows: 33
- Output directory: `/home/yoohyun/research2/experiments/E002_path_cost_bridge/artifacts/E002-M01_path_cost_inputs_v0`

## Path Profile

- `path_cost_profile_id`: `euclidean_polyline_proxy_v0`
- Source: Euclidean polyline proxy from old memory location to ordered candidate centroids.
- Old-location dead-end cost: 1.0m distance-equivalent inspection penalty for stale rows.

## 논문 주장

- E002-M01 supports path-cost bridge input construction.
- E002-M01 does not support real navigation `SR` / `SPL` or deployable search policy claims.

## 에이전트 추론

- The E001 denominator is preserved while adding path-cost fields.
- This makes the next E002 step an evaluation problem rather than a schema problem.
- Real navigation claims still require navmesh, occupancy, simulator, or robot trajectory path cost.

## 사용자 판단 필요

- None for E002-M01. Continue to E002 path-cost policy evaluation.

## Outputs

- `path_query_rows.jsonl`
- `path_candidate_rows.jsonl`
- `coverage.json`
- `report.md`
