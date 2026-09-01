# N28 Admission-Bottleneck Synthesis And Search-Stop Decision

- Date: 2026-09-01
- Status: complete
- Scope: N20--N27 admission evidence only
- Outcome: `stop_open_ended_direction_search_under_current_admission_contract`
- Active candidate / hypothesis / method / paper claim: none

## 1. Decision

N20--N27의 evidence는 **Robotics에 연구 문제가 없다는 결론**을 지지하지 않는다. Contact/support aliasing, contact-grounded reward, joint-filter externality, action-mutable substrate, persistent internal robot state처럼 물리적으로 흥미로운 mechanism은 반복해서 발견됐다.

그러나 현재 project contract 아래에서는 admission 가능한 route가 없다.

> 공개된 executable denominator, 2024--2026 exact novelty, simple-baseline-resistant residual, one-week disconfirmation, credible second-domain route, failure-derived method necessity를 동시에 만족한 route는 0개다. 특히 scientific core인 exact novelty, simple residual, forced method를 최종 상태에서 통과한 route가 하나도 없다.

따라서 같은 방식으로 adjacent robotics family를 하나씩 더 여는 open-ended direction search를 중단한다. Criteria를 낮추거나 threshold를 바꾸지 않으며, candidate/hypothesis/method/runtime을 만들지 않는다. 새 search는 Section 8의 외부 re-entry condition 또는 사용자의 명시적인 resource/scope 변경이 있을 때만 다시 연다.

## 2. Accounting Protocol

### 사실

- Decision-bearing 기록은 [N20](paired-contact-support-denominator-n20-feasibility-gate-2026-09.md), [N22](artifact-to-failure-3d-robotics-direction-search-n22-2026-09.md), [N23](simulation-first-robotics-wide-direction-search-n23-2026-09.md), [N25](joint-filter-externality-n25-k0-result-2026-09.md), [N26](fresh-simulator-first-robotics-direction-search-n26-2026-09.md), [N27](persistent-internal-robot-state-artifact-search-n27-2026-09.md)이다.
- N21은 N20 kill로 열리지 않았다. Outcome이 없으므로 count에서 제외한다.
- [N24](joint-filter-externality-n24-no-outcome-diagnostic-contract-2026-09.md)는 outcome 전 protocol을 고정한 문서다. 독립 search result로 세지 않는다.
- N23과 N25는 같은 `joint-filter externality` route의 search-stage와 K0 disposition이다. 따라서 여섯 문서를 여섯 독립 topic으로 세지 않고, 아래에서는 **다섯 route**로 집계한다.

### 집계 단위

1. N20 paired contact/support denominator
2. N22 contact-grounded 3D reward
3. N23→N25 joint-filter externality
4. N26 fresh simulator-first families
5. N27 persistent internal-state families

표의 기호는 `P`=최종 evidence상 demonstrated pass, `C`=conditional, `B`=explicit blocker, `U`=earlier kill 때문에 미검증이다. `U`를 failure outcome으로 과장하지 않지만 strict admission pass로도 세지 않는다.

## 3. Five-Route Ledger

| Route | Public executable denominator | Exact novelty | Simple residual | One-week decision | Second-domain path | Forced method | Observed disposition |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| N20 paired contact/support | **B** | U | U | P | C | **B** | observation-matched physical pair가 omission/artifact 없이 성립하지 않음 |
| N22 contact-grounded reward | P | **B** | **B** | P | **B** | **B** | trajectory-only `AUROC=0.836`; common second metric과 3D-specific necessity 없음 |
| N23→N25 joint-filter externality | **B** | C | U | P | P | U | public simulator는 있으나 exact counterfactual oracle이 K0 numerical/support gate에서 실패 |
| N26 simulator-first families | C | **B** | U | C | **B** | U | 가장 강한 mutable-substrate residue도 direct component coverage와 independent denominator에 닫힘 |
| N27 persistent internal state | **B** | **B** | **B/U** | C | **B** | **B** | public substrate branch는 prior/simple control에, novel residue는 denominator 부재에 닫힘 |

### Strict pass coverage

| Admission condition | Demonstrated pass | Interpretation |
| --- | ---: | --- |
| Public executable denominator/readiness | `1/5` | N22 RH20T만 final route 수준에서 유효했다. Repository나 simulator API 존재만으로는 denominator가 아니다. |
| Unoccupied exact problem/principle | `0/5` | exact residue가 untestable이거나 direct/adjacent prior가 problem과 method components를 점유했다. |
| Simple-baseline-resistant residual | `0/5` | N22는 trajectory control이 강했고, 나머지는 residual probe 전 kill되거나 simple state/history/control로 먼저 닫혔다. |
| One-week decisive path | `3/5`, two conditional | 핵심 병목이 아니다. N20, N22, N25는 bounded decision을 실제로 냈다. |
| Credible second-domain path | `1/5` | N23 search stage만 ground/aerial route를 가졌고, primary oracle readiness에서 먼저 종료됐다. |
| Failure-forced method principle | `0/5` | 어느 route도 final evidence에서 특정 non-substitutable method form을 강제하지 못했다. |

이 숫자는 statistical discovery probability가 아니다. 서로 다른 search family를 동일 모집단의 독립 표본으로 간주하지 않는다. 반복되는 **admission structure**를 요약하는 operational ledger다.

## 4. What Actually Blocks Admission

### 4.1 Topic shortage가 아니다

사실:

- 각 search는 물리적으로 의미 있는 question을 만들었다.
- N23은 실제로 conditional lead 하나를 N24/N25까지 진행했다.
- N22는 public row와 CPU Docker control까지 실행했다.

에이전트 추론:

- 문제는 idea generation failure가 아니라 **admissible evidence chain의 단절**이다.
- 정확한 표현은 `research-topic shortage`가 아니라 `admissible-topic shortage under the current public-artifact/resource contract`다.

### 4.2 Public denominator만의 문제도 아니다

사실:

- N20, N25, N26의 strongest residue와 N27의 voltage/wear residue는 denominator/readiness에서 막혔다.
- 반면 N22는 valid RH20T denominator와 same-day control이 있었는데도 G3/G5/G6가 실패했다.
- N27의 Open-RMF/MyoSuite처럼 public substrate가 있는 branch도 direct prior와 simple controls 때문에 탈락했다.

에이전트 추론:

- Public denominator 부재는 novel-looking residue를 막는 중요한 resource bottleneck이다.
- 하지만 denominator만 추가한다고 novelty가 자동으로 생기지 않는다. 실행 가능한 branch는 오히려 direct-prior crowding과 simple-control pressure가 강했다.

### 4.3 Scientific bottleneck은 G2/G3/G6의 결합이다

사실:

- 다섯 route 중 exact novelty, simple residual, forced method의 demonstrated pass는 각각 `0/5`다.
- N26의 mutable-substrate lead는 sensing/adaptation/action-conditioned transition components가 이미 recent prior에 분할 점유됐다.
- N27에서 internal state가 observable이면 threshold/penalty/state-conditioned control이, hidden이면 recurrent adaptation/SysID/fault estimator가 immediate baseline이 됐다.

에이전트 추론:

- 현재 가장 큰 novelty bottleneck은 `새 현상`이 아니라 `simple explanation 뒤에도 남고 특정 principle을 강제하는 residual`의 부재다.
- 이 세 조건을 완화하면 구현 가능한 paper는 만들 수 있어도, top-tier reviewer가 묻는 “왜 더 단순한 X가 아닌가?”와 “module을 바꿔도 insight가 남는가?”를 방어할 수 없다.

### 4.4 Schedule은 primary blocker가 아니다

사실:

- N20은 source-level feasibility에서, N22는 small public packet과 CPU Docker에서, N25는 frozen K0에서 각각 bounded decision을 냈다.
- N26/N27도 artifact ceiling 아래에서 conditional lead 없이 종료됐다.

에이전트 추론:

- One-week kill rule은 좋은 후보를 반복적으로 제거한 evidence가 없다. 오히려 denominator 또는 simple-control failure를 method implementation 전에 드러냈다.
- Search를 멈추는 이유는 일정 때문에 premature stop하는 것이 아니라, 같은 acquisition process의 marginal information gain이 낮아졌기 때문이다.

## 5. Are The Criteria Too Strict?

### Top-tier scientific conditions

다음 세 조건은 유지해야 한다.

- `G2 exact novelty`: motivation이나 component integration을 contribution으로 쓰지 않기 위해 필요하다.
- `G3 simple residual`: dataset bias, task prior, trajectory/history, threshold, state conditioning으로 닫히는 문제를 제거한다.
- `G6 forced method`: failure diagnosis가 method form을 요구해야 contribution이 architecture shopping이 되지 않는다.

이 셋을 낮추는 것은 candidate pool을 늘리지만 top-tier acceptance probability를 높이지 않는다.

### Project/resource conditions

- `G1 public denominator`는 학계의 절대 법칙이 아니라 현재 project의 resource contract다. 이를 완화하면 N20/N26/N27 계열에서 original benchmark construction이 가능할 수 있지만, 이는 새 evaluator, oracle, data collection 또는 hardware instrumentation을 만드는 **다른 종류의 project**다.
- `G4 one-week kill`은 paper claim 조건이 아니라 search-risk control이다. 현재 evidence상 유지가 유리하다.
- `G5 two-domain path`는 admission 시 full result를 요구하는 것이 아니라 credible extension route만 요구한다. Top-tier generalization을 생각하면 과도하지 않다.

결론적으로 admission 기준 전체가 비현실적으로 엄격한 것은 아니다. 다만 `public denominator + one-week materialization`은 original benchmark contribution을 의도적으로 제외한다. 이 범위를 바꾸려면 사용자 authorization과 일정/resource 재계산이 필요하다.

## 6. Search-Stop Rationale

### 사실

- N22 artifact-first search는 strict pass 0이었다.
- N23은 broad robotics search에서 conditional lead 하나를 냈지만 N25 K0에서 종료됐다.
- 그 뒤 독립적으로 수행한 N26 simulator-first search와 N27 internal-state search는 strict pass 0, conditional lead 0이었다.
- N20의 마지막 contact/support re-entry도 valid pair denominator가 없어 종료됐다.

### 에이전트 추론

- Search order를 benchmark-first, artifact-to-failure, simulator-first, mechanism-first로 바꿔도 같은 교차 병목이 반복됐다.
- 새 family 이름만 바꾸고 동일 public artifact pool을 재탐색하면 새로운 evidence보다 이미 기록한 exclusion reason을 다시 발견할 가능성이 높다.
- 따라서 현재 contract에서 `next robotics family search`를 자동 TODO로 추가하는 것은 합리적이지 않다.

### Search-stop outcome

`stop_open_ended_direction_search_under_current_admission_contract`

이는 다음을 뜻한다.

- Robotics/3D Vision 자체를 영구 포기하지 않는다.
- 현재 여섯 admission 조건을 완화하지 않는다.
- N20/N22/N23/N26/N27 lead를 더 좁혀 salvage하지 않는다.
- 새 method, learner, GPU run, dataset download, hardware test, paper workspace를 열지 않는다.
- external trigger 없이 broad survey를 한 차례 더 반복하지 않는다.

## 7. Reviewer-Level Judgment

에이전트 추론:

- 현재 active paper direction의 top-tier acceptance 가능성을 평가할 수 없다. 제출 가능한 thesis/claim이 없기 때문이다.
- N20--N27 중 어느 하나를 현재 상태로 살리면 novelty는 대부분 benchmark gap, modality combination, state conditioning 또는 attribution module 수준으로 보일 가능성이 높다.
- 반대로 지금 stop하는 것은 negative result가 아니라 research triage 결과다. Weak claim을 구현하는 비용을 막고, 재진입에 필요한 evidence를 명확히 했다.

논문 주장:

- 없음. N28은 literature/experiment evidence의 project-level synthesis이며 새로운 scientific claim을 만들지 않는다.

## 8. Falsifiable Re-entry Conditions

다음 중 단순히 “관련 paper가 나왔다”가 아니라, 최소 하나의 **구체적인 entry trigger**가 생겨야 search를 다시 연다.

### E1. New public denominator trigger

공개 artifact가 아래를 동시에 제공한다.

1. policy-visible observation/action history,
2. privileged mechanism oracle,
3. task outcome/cost,
4. fixed evaluator와 immutable revision,
5. 최소 two task strata 또는 independent extension route.

### E2. Pre-existing residual trigger

같은 public packet의 group-disjoint split에서 최소 세 simple controls가 모두 실패하고, case-level residual이 재현된다. Controls에는 problem에 따라 task/scene prior, geometry/trajectory/history, threshold/state-conditioned rule가 포함돼야 한다.

### E3. Principle trigger

2024--2026 exact-prior audit 뒤에도 남는 한 문장의 principle이 있고, 그 principle이 특정 representation/inference/control form을 요구한다. Module 이름을 지워도 insight가 남아야 한다.

### E4. Scope-change trigger

사용자가 public-denominator-only constraint를 변경하고 original benchmark/data/hardware instrumentation에 필요한 일정, compute, data authority와 quantitative validation route를 명시적으로 승인한다.

E1--E3 중 하나도 없이 “새로운 robotics topic을 더 찾아본다”는 것은 re-entry condition이 아니다. E4는 scientific gate 완화가 아니라 project class 변경이다.

## 9. User Decision Boundary

사용자 판단 필요:

1. **권장:** 여섯 scientific/admission criteria를 유지하고 external E1--E3 trigger까지 open-ended direction search를 pause한다.
2. Original denominator/benchmark construction을 새 project로 승인한다. 이 경우 G1 resource contract와 venue/deadline 계획을 다시 작성해야 한다.
3. Robotics/3D Vision 밖으로 scope를 바꾸거나, 현재 확보한 negative protocol/reusable assets를 다른 연구 프로그램에 넘긴다.

N28은 1번을 default operational state로 기록한다. 2번이나 3번은 material scope expansion이므로 자동으로 선택하지 않는다.

## 10. Final State

- N28: complete.
- Strictly admitted routes: `0/5`.
- Active candidate/hypothesis/method/paper: none.
- Runtime/Docker/GPU/dataset/hardware: not opened.
- Automatic next research task: none.
- Next action: user-authorized research-program branch decision or external E1--E3 re-entry trigger.
