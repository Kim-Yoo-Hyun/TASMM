# N23 Simulation-First Robotics-Wide Direction Search

> Historical route report. 이 문서의 당시 next action은 [N28](admission-bottleneck-synthesis-search-stop-n28-2026-09.md)이 대체하며, archived source/artifact를 자동 복원하지 않는다.

- Date: 2026-09-01
- Status: complete; strict pass 0, one conditional diagnostic lead
- Outcome: `retain_joint-filter_externality_for_n24_diagnostic_contract_only`

## 1. Decision

에이전트 추론:

- 현재 여섯 진입 조건을 모두 **실증적으로** 통과한 research candidate는 없다.
- robotics 전반에서 공개 simulator/evaluator를 먼저 찾는 순서로 다시 조사했을 때, 다음 gate로 넘길 가치가 있는 유일한 lead는 **Causal Safety Externalities in Multi-Robot Learning**이다.
- 이 lead의 질문은 다음과 같다.

> A centralized joint safety filter can change several agents' controls. Does the commonly used per-agent correction penalty misattribute which nominal policy caused the shared safety burden, and does that miscredit reduce coordination efficiency even when hard safety is preserved?

- 한국어 working description은 `joint safety filter의 source--victim credit misattribution`이다. `responsibility allocation`, generic `safe MARL`, generic `constraint conflict`, 새 safety shield는 novelty claim으로 쓰지 않는다.
- 공개 code의 구조와 one-week diagnostic 경로는 있으나 simple-control-resistant row-level residual은 아직 없다. 따라서 numbered candidate, hypothesis, method, paper claim은 열지 않고 `N24` no-outcome diagnostic contract만 허용한다.

## 2. User Evidence Contract

사용자 판단:

- mechanism, ablation, robustness, scale과 main quantitative result는 simulation에서 모두 산출한다.
- real hardware는 마지막 quantitative transfer/effect validation에만 사용한다.
- qualitative-only hardware evidence, hardware-first dataset collection, real-robot debugging이 주장을 지탱하는 방향은 제외한다.

에이전트 추론:

- candidate admission에 필요한 simulation artifact는 nominal action, filtered/executed action, active safety constraints, task outcome, path/time cost를 episode와 timestep 수준에서 내보내야 한다.
- real test는 simulation에서 고정한 metric과 intervention을 그대로 재사용할 수 있어야 한다. hardware 영상의 qualitative success example은 보조 자료일 뿐 claim evidence가 아니다.

## 3. Search Procedure

Artifact-first 순서를 다음과 같이 적용했다.

1. released measurement structure
2. executable denominator
3. at least three simple baselines and their possible residual
4. 2024--2026 exact problem/principle prior
5. two simulator/domain route
6. failure-diagnosis-implied method form

탐색 대상은 manipulation/VLA evaluation, locomotion and system identification, multi-robot control, social navigation, aerial robotics, surgical robotics, sim-to-real evaluation이었다. `/home/yoohyun/PaperReview`는 discovery registry로만 사용했고 아래 판단은 primary paper, official project, official repository로 재확인했다.

## 4. Primary-Source Audit

### 4.1 Sources

| Source | Released contract | What it owns or enables | N23 use |
| --- | --- | --- | --- |
| [JaxRobotarium](https://github.com/GT-STAR-Lab/JaxRobotarium) / CoRL 2025 | JAX multi-robot training, barrier-filter option, Robotarium deployment route | same scenario interface from accelerated simulation to remotely accessible robots | primary denominator lead |
| [Robotarium](https://www.robotarium.gatech.edu/) | remotely accessible multi-robot hardware testbed | bounded final quantitative robot test without owning a robot fleet | hardware-only final route |
| [Layered Safe MARL](https://www.roboticsproceedings.org/rss21/p094.html) / RSS 2025 | code/project, multi-agent aerial simulation, Crazyflie hardware | conflicting multi-agent constraints, proactive MARL, pair prioritization, tactical safety filter | closest direct prior and strong baseline |
| [Learning Responsibility Allocations](https://arxiv.org/abs/2410.07409) / 2024, revised 2026 | differentiable CBF optimization on synthetic and real data | state-dependent willingness to deviate from desired control | exact wording/method threat |
| [SIMPLER](https://simpler-env.github.io/) | paired simulated/real manipulation evaluation | simulation-based real-policy ranking and sim-real correlation | kills generic simulation surrogate claim |
| [LIBERO-Safety](https://libero-safety.github.io/) / ECCV 2026 | physical/semantic safety suites and demonstrations | task success versus safety gap in VLA manipulation | kills generic hidden-safety-gap claim |
| [SafeVLA-Bench](https://safevla.org/) / 2026 | post-hoc safety instrumentation over manipulation simulators | safety violation types and success-safety evaluation | kills generic safety instrumentation claim |
| [SPI-Active](https://lecar-lab.github.io/spi-active_/) / CoRL 2025 | official code and legged sim-to-real pipeline | active exploration for contact-rich legged system identification | kills active SysID lead |
| [HumanoidBench](https://humanoid-bench.github.io/) | MuJoCo benchmark with 27 whole-body tasks | open locomotion/manipulation denominator | strong substrate, no unoccupied forced residual found |
| [Arena-Rosnav](https://github.com/Arena-Rosnav) / current platform; Arena 3.0 RSS 2024, Arena 4.0 ICRA 2025 | ROS2 navigation across multiple simulators and pedestrian models | social-navigation model and metric variation | denominator exists; model-bias problem already explicit |
| [ORBIT-Surgical](https://orbit-surgical.github.io/) / ICRA 2024 | 14 Isaac-based surgical tasks, dVRK transfer | simulation-first surgical learning | high-quality substrate, specialized hardware bottleneck |
| [Cosmos-Surg-dVRK](https://cosmos-surg-dvrk.github.io/) / 2025 | simulated policy evaluation compared with real dVRK | simulation as predictor of real surgical policy performance | direct evaluation prior |
| [Beyond Binary Success](https://arxiv.org/abs/2603.13616) / 2026 | sequential, anytime-valid robot-policy comparison | reduced real evaluation burden across non-binary metrics | kills generic real-trial allocation |
| [Active Real-World Factor-Based Evaluation](https://arxiv.org/abs/2607.14439) / 2026 | adaptive factor selection over 2,331 real trials | sample-efficient factor-conditional hardware evaluation | kills active evaluation lead |

사실:

- 위 표는 14개 primary/official source를 포함한다. `PaperReview` entry나 secondary summary만으로 source status를 판정하지 않았다.
- field-survey는 implementation deep read와 동일하지 않다. JaxRobotarium만 primary lead의 source-level 구조를 감사했고, 나머지는 problem/artifact/prior screening 수준이다.

### 4.2 Family-Level Screening

Legend: `P` pass, `C` conditional, `F` fail, `U` untested.

| Family / question | Public executable denominator | Exact novelty | Simple-baseline residual | One-week kill | Two domains | Forced method | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Simulation predicts real policy ranking | P | F | F | P | P | F | killed by SIMPLER and 2026 evaluation flow |
| Success hides physical/semantic safety | P | F | F | P | P | F | killed by LIBERO-Safety/SafeVLA-Bench |
| Sample-efficient real policy evaluation | P | F | C | P | P | F | killed by sequential and active-evaluation priors |
| Active/provably safe system identification | P | F | C | C | P | F | killed by SPI-Active and adjacent safe SysID flow |
| Social-navigation ranking under pedestrian-model shift | P | F | C | P | P | F | model-dependence is explicit; mixture/robust training is obvious |
| Surgical simulation as real-policy surrogate | P | F | C | C | C | F | direct evaluation prior plus specialized hardware dependence |
| Joint-filter source--victim credit misattribution | P | C | U | P | P | C | retain for diagnostic contract only |

에이전트 추론:

- 공개 benchmark가 있다는 이유만으로 manipulation/VLA evaluation을 선택하면 2026 evaluation crowding에 즉시 충돌한다.
- HumanoidBench처럼 unsolved task가 많다는 사실도 novelty가 아니다. failure taxonomy가 특정 principle을 강제하지 않으면 algorithm shopping으로 끝난다.
- multi-robot joint filter lead만 simulator 내부의 chosen action과 executed action 사이에 아직 직접 측정 가능한 attribution gap을 남긴다.

## 5. Source-Level Evidence for the Retained Lead

사실:

- audited JaxRobotarium commit: `6200711f6fb98015579af3e7a534bcfb8bcb69af`.
- `jaxrobotarium/robotarium_env.py`의 `Controller.get_action`은 controller가 만든 nominal `dxu`를 `barrier_fn(dxu, x, [])`에 넣고 `dxu_safe`만 반환한다.
- `rps_jax/utilities/barrier_certificates2.py`의 robust barrier는 JAXopt `OSQP`로 전체 robot action을 한 joint QP에서 푼다. pairwise constraint row에는 상호작용하는 두 robot의 control term이 함께 들어간다.
- 현재 environment API는 nominal action, filtered action, active constraint/dual을 evaluation row에 함께 노출하지 않는다. 이는 작은 instrumentation point이지 새 simulator를 만들 이유가 아니다.

논문 주장:

- JaxRobotarium은 accelerated multi-robot learning과 Robotarium hardware deployment를 같은 platform에 묶는다.
- Layered Safe MARL은 three-or-more-agent interaction에서 conflicting constraints를 줄이는 MARL layer, urgency-based pair prioritization, safety filter를 결합하고 aerial simulation과 Crazyflie hardware에서 평가한다.
- Learning Responsibility Allocations는 responsibility를 타 agent를 수용하기 위해 desired control에서 얼마나 벗어나는지로 정의하고 differentiable CBF optimization으로 allocation을 학습한다.

에이전트 추론:

- joint projection에서 `||u_i^safe-u_i^nom||`가 큰 agent가 반드시 위험을 야기한 source agent는 아니다. 다른 agent의 nominal proposal 때문에 constraint가 active되어 correction을 받은 victim일 수 있다.
- 이 source--victim discordance가 실제로 빈번하고 outcome과 연결되는지는 아직 사실이 아니다. `N24`가 증명 또는 기각해야 할 hypothesis 이전의 diagnostic question이다.
- closest prior와 구분되는 경계는 **desired-control deviation share를 학습하는 것**이 아니라 **각 nominal proposal이 다른 agent의 projection burden을 얼마나 야기했는지 counterfactual하게 귀속하고, 기존 learning signal이 그 원인을 반대로 학습하는지 검사하는 것**이다.

## 6. Required Simple Controls

다음 controls가 counterfactual attribution을 이기면 lead는 종료한다.

| ID | Control | Why it may close the problem |
| --- | --- | --- |
| B0 | safety-blind MARL + fixed safety filter | filter alone may preserve both safety and useful efficiency |
| B1 | collision/proximity or time-to-collision penalty | geometry may identify the causing agent without filter internals |
| B2 | per-agent own correction `||u_i^safe-u_i^nom||` | standard intervention penalty may already provide sufficient credit |
| B3 | global correction magnitude / active-constraint count | team-level burden may be enough for cooperative reward |
| B4 | critic/replay conditioned on executed action | chosen-versus-executed mismatch may be solved by exposing applied control |
| B5 | Layered Safe MARL conflict reward/pair prioritization | direct recent method may remove the relevant conflict before attribution matters |
| O1 | leave-one-agent-proposal-out QP re-solve | diagnostic oracle for source-to-victim externality, not a deployable baseline |

최소 세 가지 “더 단순한 X”는 B1, B2, B4다. 이들과 B5를 통과하기 전 externality-aware learner를 만들지 않는다.

## 7. N24 One-Week Kill Contract Outline

### 7.1 Frozen diagnostic object

For nominal joint action `u`, filtered action `u* = F(x,u)`, define a source-to-victim matrix only as a diagnostic oracle:

`E[i,j] = burden_j(F(x,u)) - burden_j(F(x,u with agent i replaced by a safe/reference proposal))`.

Exact replacement, sign, normalization, feasible reference proposal, and QP failure handling must be frozen before outcomes are read. Dual-based approximation may be measured but cannot replace exact re-solve in the first gate.

### 7.2 Rows and strata

- at least two JaxRobotarium coordination scenarios
- `N = 2` as negative/control stratum and `N >= 3` dense interaction as primary stratum
- matched seeds across B0--B5
- episode and timestep tables containing state, nominal action, executed action, filter status, active constraints, attribution controls, success, makespan/path cost, minimum separation, deadlock/timeout

### 7.3 Diagnostic metrics

- off-diagonal externality mass: burden caused on `j != i`
- source--victim disagreement rate between O1 and B2
- top-source accuracy/AUROC for B1--B4 against O1
- next-horizon delay/deadlock predictiveness after controlling for density, minimum distance, total intervention and state
- task success, makespan, path length, minimum separation, filter intervention rate/magnitude, deadlock/timeout
- hard safety violations are a constraint, not an efficiency trade-off metric

### 7.4 Sequential kill rules

1. **K0 artifact:** exact nominal/executed/constraint rows cannot be deterministically materialized -> kill.
2. **K1 mechanism:** no stable off-diagonal source--victim discordance in both primary scenarios -> kill.
3. **K2 simple explanation:** B1, B2, or B4 predicts O1 attribution and downstream inefficiency as well as O1 -> kill.
4. **K3 outcome relevance:** O1 externality adds no held-out prediction of delay/deadlock/success after geometry and total-intervention controls -> kill.
5. Only after K0--K3 survive may a minimal credit-assignment intervention be specified. A performance threshold must be frozen then, before method outcomes.

에이전트 추론:

- K0--K3 are diagnosis, not a paper result. They can be completed without real hardware and before full MARL training.
- one-week feasibility comes from reusing the existing joint OSQP and scenarios, adding logging plus counterfactual re-solves, and running small matched-seed Docker experiments. No vision model, dataset download, or real robot is needed.

## 8. Two-Domain and Real-Hardware Route

| Stage | Domain | Quantitative role |
| --- | --- | --- |
| primary simulation | JaxRobotarium ground multi-robot navigation/coordination | mechanism, controls, scale over agent count/density, ablation, robustness |
| external simulation | Layered Safe MARL double-integrator / aerial AAM-style scenarios | dynamics and interaction-topology generalization |
| final hardware | remote Robotarium; optional Crazyflie only if access exists | frozen transfer/effect metrics, not discovery |

사용자 판단이 필요한 시점:

- 지금은 없음. Hardware access를 먼저 확보할 필요가 없다.
- K0--K3와 external simulation이 모두 survive한 뒤에만 Robotarium queue/account feasibility를 확인한다.
- final hardware protocol은 success, makespan/path length, minimum separation, intervention rate/magnitude, deadlock을 simulation과 동일하게 정량 보고한다. 동영상 사례만으로 transfer claim을 쓰지 않는다.

## 9. Novelty and Venue Judgment

에이전트 추론:

- 매력도는 현재 `conditional`, top-tier 가능성은 아직 낮음--중간이다. Multi-agent safe learning과 credit assignment의 교차점은 RSS/IROS에 맞지만, Layered Safe MARL과 CBF responsibility prior가 매우 가깝다.
- novelty가 살아나는 필요조건은 “filter가 자주 개입한다”가 아니다. **기존 own-deviation/executed-action/proximity signal이 causal source를 체계적으로 오귀속하고, 그 오귀속이 안전을 유지한 상태에서도 coordination loss를 만든다**는 두 단계 evidence다.
- 이 현상이 two-agent toy case에만 있거나 B4로 닫히면 paper direction이 아니다.
- 반대로 three-plus-agent constraint coupling에서 재현되고 ground/aerial 두 dynamics에 일반화되며 externality-aware credit만 residual을 줄이면, contribution sentence에서 module 이름을 지워도 남는 principle이 생긴다.
- venue route는 simulation-scale와 quantitative Robotarium validation이 가능한 RSS/IROS first가 현실적이다. 이후 더 넓은 multi-agent task/dynamics와 formal analysis가 생길 때 CoRL/RA-L/T-RO 확장을 검토할 수 있다.

## 10. Claim Boundary

허용하지 않는 claim:

- a new safety filter
- generic safe multi-agent reinforcement learning
- resolving multi-agent constraint conflicts
- learning responsibility allocation
- sim-to-real policy evaluation
- fair or capability-aware collision avoidance

N24가 survive할 때만 검토할 수 있는 provisional insight:

> In jointly filtered multi-robot learning, intervention magnitude measures who was corrected, not necessarily whose nominal action caused the shared correction; learning from that victim-side signal can preserve collision safety while degrading coordination.

이 문장은 현재 paper claim이 아니라 falsifiable diagnostic target이다.

## 11. Final State

- `N23`: complete.
- strict six-condition pass: `0`.
- retained conditional lead: `1`.
- candidate/hypothesis/method/paper/runtime: not opened.
- next action: write `N24` source-level, no-outcome K0--K3 contract with exact replacement semantics, scenarios, rows, controls, and disconfirmation thresholds. Docker execution is a later step after the contract is frozen.
