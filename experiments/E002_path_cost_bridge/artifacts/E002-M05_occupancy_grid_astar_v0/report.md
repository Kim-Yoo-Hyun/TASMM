# E002-M05 Occupancy Grid A*

## Status

grid_path_cost_smoke_ready

## 사실

- Dataset root: `/home/yoohyun/research2/local_dataset`
- Input directory: `/home/yoohyun/research2/experiments/E002_path_cost_bridge/artifacts/E002-M01_path_cost_inputs_v0`
- Query rows: 294
- Candidate rows: 1248
- Scan grids ready: 13 / 13
- Query rows with free-space path source: 288
- Candidate rows reachable: 1029
- Candidate rows unreachable: 219
- Target rows reachable: 267
- Real navigation path-cost rows: 0
- Output directory: `/home/yoohyun/research2/experiments/E002_path_cost_bridge/artifacts/E002-M05_occupancy_grid_astar_v0`

## Path Profile

- `grid_path_cost_profile_id`: `occupancy_grid_astar_v0`
- Grid resolution: 0.1m
- Robot radius: 0.18m
- Source: annotated PLY floor/obstacle occupancy with A* over 2D free cells.

## Failure Types

| Failure type | Rows |
| --- | ---: |
| `candidate_unprojectable` | 21 |
| `disconnected_free_space` | 168 |
| `start_unprojectable` | 30 |

## 논문 주장

- E002-M05 supports free-space path-cost smoke construction from local `3RScan` geometry.
- E002-M05 does not support real navigation `SR` / `SPL`, simulator execution, or deployable search policy claims.

## 에이전트 추론

- This upgrades E002 beyond straight-line Euclidean proxy where grid paths are reachable.
- Unreachable rows are explicit artifacts, so denominator drift is avoided.
- The next step should evaluate the existing policies against grid path costs rather than candidate-count or straight-line cost.

## 사용자 판단 필요

- None for E002-M05. Continue to grid-path policy evaluation if this coverage is acceptable.

## Outputs

- `grid_query_rows.jsonl`
- `grid_candidate_rows.jsonl`
- `scan_grid_summaries.jsonl`
- `failure_rows.jsonl`
- `coverage.json`
- `report.md`
