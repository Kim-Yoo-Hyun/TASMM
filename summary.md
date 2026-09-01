# Research Summary

Updated: 2026-09-01

## Current State

사실:

- Active candidate, hypothesis, experiment, paper claim은 없다.
- Open-ended direction search는 N28에서 pause했다.
- Runtime, GPU, dataset download와 hardware execution은 열려 있지 않다.

에이전트 판단:

- 지금까지의 문제는 idea shortage가 아니라 `admissible-topic shortage under the current public-artifact/resource contract`다.
- Top-tier scientific core인 exact novelty, simple-baseline-resistant residual, failure-forced method는 완화하지 않는다.
- Public-denominator-only 조건을 바꾸면 original benchmark project가 가능할 수 있지만, 이는 별도 일정과 resource authorization이 필요한 project-class 변경이다.

## Core Research Outcomes

| Lineage | Core question | Final outcome | Reusable lesson |
| --- | --- | --- | --- |
| Task-Aware / Decision-Calibrated Semantic Memory | stale evidence와 task context가 update/re-observation을 강제하는가 | parked; simple union/time-decay와 competence floor가 residual 대부분을 설명 | DynaMem, Voxeland, Bayesian Fields, MHT의 operator differences와 evaluation protocol |
| Policy-Conditional Semantic Mapping | 한 acquisition policy의 map confidence가 다른 policy/task에 portable한가 | K5 G1 kill; `A→B ΔBrier=+0.0022`, `B→A=-0.0087` | split/leakage-controlled kill-test design |
| Contradiction-Grounded Belief Repair | culprit hypothesis와 discriminative action이 새 principle인가 | diagnosis/POMDP/MHT direct method overlap으로 kill | failure diagnosis가 domain adaptation인지 먼저 확인 |
| Query-Family-Sufficient Compression | byte parity에서 joint witness가 선택적으로 소실되는가 | HM3D perception-bearing denominator competence failure | atomic metric과 relational query witness를 분리해야 함 |
| Population-Conditional Evaluation | population mean이 stable disagreement를 지우는가 | released artifact/schema mismatch에서 G0 kill | post-selection과 evaluator hash를 outcome 전에 검증 |
| Configuration-Space Fidelity / Causal 4D / Policy-Visible Safety | 3D representation, demonstration clocks, safety observability가 새 문제인가 | exact prior 또는 row-level denominator 부재로 kill | benchmark motivation과 new principle을 분리 |
| N20 paired contact/support | observation-matched physical pair가 가능한가 | `kill_no_valid_observation_matched_physical_pair` | simulator API 존재는 valid denominator 존재가 아님 |
| N22 contact-grounded reward | 3D/contact evidence가 failure ordering을 설명하는가 | strict pass 0; trajectory-only `AUROC=0.836` | simple low-dimensional control을 먼저 실행 |
| N23--N25 joint-filter externality | corrected victim과 causal source가 다른가 | K0 `kill_artifact_or_instrumentation` | exact counterfactual oracle의 solver validity/support가 선행 조건 |
| N26 simulator-first families | mutable substrate 등에서 forced residual이 있는가 | strict pass 0, conditional lead 0 | public substrate가 있어도 direct component coverage와 second route가 필요 |
| N27 persistent internal state | battery/thermal/fatigue가 policy ordering을 바꾸는가 | strict pass 0, conditional lead 0 | observable state는 simple control, hidden state는 SysID/adaptation prior가 압박 |

## N28 Aggregate

| Admission condition | Demonstrated pass |
| --- | ---: |
| Public executable denominator/readiness | `1/5` |
| Unoccupied exact problem/principle | `0/5` |
| Simple-baseline-resistant residual | `0/5` |
| One-week decisive path | `3/5`, two conditional |
| Credible second-domain path | `1/5` |
| Failure-forced method principle | `0/5` |

상세 ledger와 counting boundary는 [N28](literature/admission-bottleneck-synthesis-search-stop-n28-2026-09.md)에 있다.

## Retired Assets

모든 기존 source, artifacts, paper folders, datasets와 logs는 `/home/yoohyun/research2_retired_20260901/`에 원래 hierarchy로 보존했다.

주요 복구 후보:

| Archived path | Potential reuse |
| --- | --- |
| `experiments/E003_perception_noise_expansion/` | controlled RGB-D/OV proposal and noise pipeline |
| `experiments/E005_external_baseline_transition/` | ConceptGraphs/Open3DSG adapter evidence |
| `experiments/E008_real_navigation_benchmark/` | HM3D/Habitat render, navmesh and trajectory utilities |
| `experiments/E009_decision_calibrated_memory/` | DynaMem/Voxeland/Bayesian Fields/MHT protocol and controls |
| `hypothesis/probes/` | completed negative probes and independent verifiers |
| `local_dataset/` | HM3D, 3RScan/3DSSG, derived packets and audit data |
| `literature/` | full paper registry, deep reads and N0--N27 history |

새 hypothesis가 named asset을 요구하기 전에는 복원하지 않는다.

## Re-entry Conditions

1. New public denominator가 observation/action, mechanism oracle, outcome/cost, fixed evaluator를 함께 공개한다.
2. 같은 public packet에서 최소 세 simple controls 뒤 residual이 group-disjoint split에 남는다.
3. Exact-prior audit 뒤에도 남는 principle이 특정 method form을 강제한다.
4. 또는 사용자가 original benchmark/data/hardware instrumentation을 별도 project로 승인한다.
