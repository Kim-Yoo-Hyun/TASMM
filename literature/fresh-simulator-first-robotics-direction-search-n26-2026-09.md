# N26 Fresh Simulator-First Robotics Direction Search

> Historical route report. 이 문서의 당시 next action은 [N28](admission-bottleneck-synthesis-search-stop-n28-2026-09.md)이 대체하며, archived source/artifact를 자동 복원하지 않는다.

- Date: 2026-09-01
- Status: complete; strict pass 0, conditional lead 0
- Outcome: `no_strict_pass_no_conditional_lead`

## 1. Decision

에이전트 추론:

- 기존 N0--N25 exclusion ledger 밖에서 `RoboVerse/MetaSim`, `Verti-Bench`, `GranularGym`, `IMBench`, `RoboLab`, `OopsieVerse`, `SafeManip`, `DVS`, adversarial multi-robot benchmark를 새로 감사했지만, 여섯 진입 조건을 모두 만족한 research candidate는 없다.
- 가장 강해 보였던 두 축도 유지하지 않는다.
  - **cross-simulator interaction semantics**는 `RoboVerse/MetaSim` 자체가 observation/reward parity, policy cross-sim rollout, contact/actuator/timestep mismatch를 correctness contract와 regression target으로 이미 다룬다. 남는 것은 simulator engineering 또는 generic sim-to-real evaluation에 가깝다.
  - **action-mutable deformable substrate**는 `PSANE`, `NeSAM`, `DiffusiveGRAIN`, active material identification과 deformable-material SysID가 active sensing, online adaptation, action-conditioned environment change, joint robot/environment prediction을 나누어 직접 점유한다. 이들을 결합하는 것만으로는 새 principle이 아니다.
- 따라서 N26에서는 candidate, hypothesis, method, learner, Docker runtime, GPU, dataset download, hardware를 열지 않았다.
- 다음 탐색은 외부 scene/contact state를 반복해서 변형하는 계열을 더 좁히지 않는다. 아직 exclusion ledger에서 독립적으로 다루지 않은 **persistent internal robot state**—battery, thermal state, actuator saturation/fatigue, wear—가 공개 simulator에서 task outcome과 policy ordering을 바꾸는지 artifact-first로 한 번 감사한다.

## 2. Frozen Admission Contract

사용자 판단:

- 정량 evidence의 대부분은 simulation에서 산출한다.
- hardware는 마지막 quantitative validation에만 사용한다.
- 다음 여섯 조건은 완화하지 않는다.

| Gate | Required evidence |
| --- | --- |
| G1 public denominator | 공개 code/data/evaluator와 reproducible task metric이 존재한다. |
| G2 exact novelty | 2024--2026 direct prior가 문제와 원리를 이미 점유하지 않는다. |
| G3 simple residual | 적어도 세 개의 naive baseline으로 failure가 닫히지 않는다. |
| G4 one-week kill | outcome을 보기 전에 고정 가능한 1주 diagnostic/kill path가 있다. |
| G5 two-domain route | 두 dataset, simulator, task domain 또는 독립 physical route로 확장할 수 있다. |
| G6 forced method | failure diagnosis가 교체 가능한 module이 아니라 특정 representation/inference/control form을 요구한다. |

사실:

- `/home/yoohyun/PaperReview`는 discovery registry로만 사용했다.
- 논문/프로젝트 주장은 primary paper, official project, official repository에서 다시 확인했다.
- External source는 `/tmp/n26-audit-bjLwaH/`에 read-only source audit 용도로만 clone했다. Host dependency install, import, compile, simulator execution은 하지 않았다.

## 3. Primary And Official Source Audit

| Source | Released or stated contract | N26 judgment |
| --- | --- | --- |
| [RoboVerse, RSS 2025](https://www.roboticsproceedings.org/rss21/p022.html) / [code](https://github.com/RoboVerseOrg/RoboVerse) | unified task/data framework over multiple simulators; cross-simulator task and policy utilities | broad simulator-agnostic task direction is occupied |
| [MetaSim](https://github.com/RoboVerseOrg/MetaSim) | common state/action/scenario interface over MuJoCo, Newton, SAPIEN, Isaac and other backends | public substrate exists, but parity is an explicit framework obligation |
| [Scenario Execution for Robotics](https://arxiv.org/abs/2409.07080) | backend/middleware-agnostic reproducible scenario execution over multiple simulators and real systems | kills generic backend-agnostic experiment claim |
| [SimBenchmark](https://leggedrobotics.github.io/SimBenchmark/) | contact and multibody comparison over RaiSim, Bullet, ODE, MuJoCo and DART | physics-engine contact mismatch is not a new observation |
| [RoboLab, RSS 2026](https://roboticsconference.org/program/papers/96/) / [code](https://github.com/NVlabs/RoboLab) | controlled simulation perturbations for real-policy analysis; repository warns that Isaac Sim versions alter contact-rich dynamics | version/backend sensitivity is already explicit and pinning the stack is an obvious control |
| [SIMPLER, CoRL 2024](https://simpler-env.github.io/) | matched simulated/real manipulation evaluation and real-policy ranking analysis | generic simulator-as-policy-evaluator claim is occupied |
| [PolaRiS, RSS 2026](https://roboticsconference.org/program/papers/62/) | scalable real-to-sim evaluation of generalist robot policies | further occupies simulation-based real-policy analysis |
| [Verti-Bench, RSS 2025](https://www.roboticsproceedings.org/rss21/p138.html) / [code](https://github.com/RobotiXX/verti_bench) | 100 environments, 1,000 tasks, rigid/deformable terrain, multiple vehicles and mobility systems | strong denominator for off-road mobility, not by itself a new problem |
| [Project Chrono SCM API](https://api.chrono.projectchrono.org/classchrono_1_1vehicle_1_1_s_c_m_deformable_terrain.html) | mutable terrain node level, sinkage/plastic-sinkage/touched-state quantities | enables a history intervention but does not establish a novel residual |
| [PSANE, 2026](https://arxiv.org/abs/2603.08905) | interaction-derived deformable-terrain sensing, safe-set estimation and active navigation | directly occupies active terrain probing/navigation |
| [NeSAM, 2026](https://arxiv.org/abs/2608.21330) | differentiable terramechanics, soil-parameter adaptation, Verti-Bench and physical Verti-Arena validation | directly occupies deformable-soil online adaptation and closed-loop use |
| [Soil2Cover, 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12134033/) | coverage planning that explicitly minimizes soil compaction from route choice and repeated machinery passage | repeated-pass terrain impact is an explicit planning objective |
| [SPI-Active, CoRL 2025](https://proceedings.mlr.press/v305/sobanbabu25a.html) | Fisher-information active exploration for contact-rich legged SysID and sim-to-real | active SysID baseline/principle is occupied |
| [GranularGym, RSS 2023](https://roboticsproceedings.org/rss19/p034.html) / [code](https://github.com/dmillard/GranularGym) | GPU granular dynamics core and benchmark examples in the paper | second-domain physics core exists; released repo lacks a turn-key task/evaluator suite |
| [Interactive Identification of Granular Materials, 2024](https://arxiv.org/abs/2403.17606) | force-based interactive exploration over 11 granular materials | generic interaction-based material identification is occupied |
| [DPSI, 2024](https://arxiv.org/abs/2411.00554) | differentiable physics-based identification of elastoplastic material parameters from interaction and point clouds | deformable-material SysID is occupied |
| [DiffusiveGRAIN, CoRL 2025](https://proceedings.mlr.press/v305/hu25d.html) | action-conditioned granular environment predictor plus robot-state predictor and joint planning | action changes both substrate and robot state is a direct prior |
| [IMBench, 2026](https://imbench.org/) | 35 intuitive manipulation tasks spanning dynamics, hidden properties, recovery and stability | task family is rich, but each prospective residual has direct analytic or recent learned baselines |
| [Stable Object Placement Planning, 2025/2026](https://papers.starslab.ca/stable-placement-planning/) | first-principles contact-robust stable placement planning and real-robot evaluation | kills broad release/stability reasoning claim |
| [SafeManip, 2026](https://arxiv.org/abs/2605.12386) | temporal safety predicates including grasp/release stability and recovery | kills generic temporal/release-safety instrumentation claim |
| [OopsieVerse, RSS 2026](https://roboticsconference.org/program/papers/98/) | simulator-agnostic damage signal in OmniGibson and RoboCasa, learning/evaluation/sim-to-real use cases | damage-aware simulation and cross-backend safety instrumentation are occupied |
| [DVS, RSS 2025](https://immvlab.github.io/DVS/) | virtual-real synchronized dynamic-human platform | paper/project exists, but no public executable benchmark/evaluator was confirmed |
| [KlaskTron, RSS 2026](https://roboticsconference.org/program/papers/38/) | public adversarial multi-agent digital twin and low-cost hardware route | opponent dependence is real, but payoff matrix/Elo/Nash controls are obvious and prior-rich |
| [Betting for Sim-to-Real Performance Evaluation, RSS 2026](https://roboticsconference.org/program/papers/90/) | theory and code for real-performance estimation from cross-fidelity simulators | further closes generic multi-simulator performance-estimation claims |
| [Beyond Binary Success, RSS 2026](https://roboticsconference.org/program/papers/76/) | anytime-valid, sample-efficient policy comparison for binary and fine-grained metrics | further closes generic evaluation-efficiency claims |

### 3.1 Audited Revisions

사실:

- `RoboVerse`: `e9b5c6efeb665052edeb934fc3172df8b9d3c9d7`
- `MetaSim`: `6947e353ac6832cb85767ebe1472fb8908a5d371`
- `Verti-Bench`: `7d8e366d0bc8f4bf9b2bf6483d6c6456c0972ca8`
- `GranularGym`: `11d913842a9d8510a5f26ca941dafd955ba52347`
- `diffsim` supporting audit: `d34521f5e93c55f1206b19501641cedb32414a35`

## 4. Family-Level Screening

Legend: `P` pass, `C` conditional, `F` fail.

| Family / question | G1 | G2 | G3 | G4 | G5 | G6 | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Same task/config across physics backends yields different contact behavior | P | F | F | P | P | F | parity engineering and simulator benchmarking already own it |
| Simulator/backend disagreement predicts hardware or policy ranking | P | F | C | P | P | F | SIMPLER/PolaRiS/RoboLab/Betting flow plus worst-backend or ensemble control |
| Simulator version drift invalidates benchmark scores | P | C | F | P | P | F | immutable image/version pin and same-stack comparison close it |
| Repeated traversal changes deformable terrain and future traversability | P | F | C | P | C | C | NeSAM, PSANE, Soil2Cover and prior terramechanics already cover the principle |
| Active identification is biased because a probe mutates the substrate | C | C | C | C | F | C | strongest residual, but no ready two-domain denominator and direct-prior components surround it |
| Hidden physics must be inferred before manipulation | C | F | C | C | C | F | IMBench/DPSI/material probing and history/world-model baselines occupy it |
| Release/stability failures require temporal validation | P | F | F | P | P | F | support/COM/contact-robust planning and SafeManip close it |
| Damage or temporal safety is hidden by binary success | P | F | F | P | P | F | OopsieVerse/SafeManip own benchmark and intervention space |
| Dynamic virtual-real scenes need synchronized evaluation | F | F | C | C | C | F | released denominator absent; platform contribution already states synchronization |
| Adversarial robot policy ranking is opponent-dependent | P | F | F | P | P | F | standard game-theoretic population evaluation closes it |

에이전트 추론:

- `P`가 많은 row도 research pass는 아니다. 공개 simulator와 easy kill test가 있어도 G2/G3/G6가 실패하면 top-tier candidate가 아니다.
- RSS 2026에는 `RoboLab`, `PolaRiS`, `Betting for Sim-to-Real Performance Evaluation`, `Beyond Binary Success`, `OopsieVerse`가 동시에 등장한다. Generic simulation-based evaluation, controlled factor sensitivity, low-real-trial estimation, safety instrumentation은 신규 claim 공간이 아니다.

## 5. Why Cross-Simulator Interaction Semantics Is Rejected

사실:

- `RoboVerse/AGENTS.md`는 simulator 간 parity를 framework의 load-bearing correctness contract로 명시한다.
- 같은 문서는 closed-loop dynamics parity와 observation-bitwise parity가 다르며, 한 backend에서 학습한 policy가 다른 backend로 전이되지 않을 수 있음을 명시한다.
- repository에는 `eval_cartpole_cross_sim.py`, `eval_go1_cross_sim.py`, `parity_obs_reward_cartpole.py`, `parity_go1_diag.py`가 있다.
- `ROADMAP.md`와 `MetaSim/CHANGELOG.md`는 Newton joint-name mismatch, silent action drop, partial actuator specification에 따른 effort-limit divergence, seed propagation, contact-force warm-step 같은 실제 cross-backend failure를 기록한다.

에이전트 추론:

- 이 evidence는 phenomenon이 실제임을 지지하지만 novelty를 지지하지 않는다. 오히려 framework 유지보수 항목과 기존 physics-engine benchmark가 broad claim을 선점했다.
- matched pre-contact branch와 contact-event sequence만 비교하도록 좁혀도 state normalization, timestep/substep matching, actuator calibration, parameter randomization, worst-backend evaluation이 강한 simple controls다.
- hardware ranking까지 연결하면 N23에서 이미 제외한 generic simulation-surrogate evaluation과 RSS 2026 evaluation papers에 충돌한다.

Decision: `kill_direct_ownership_or_simple_parity_control`.

## 6. Why Action-Mutable Substrate Is Not Retained

검토한 provisional question:

> When an interaction used to infer terrain or material properties also irreversibly changes that substrate, do stationary-latent active identification and static traversability baselines become confidently wrong, requiring a joint belief over material properties and action-conditioned substrate state?

사실:

- Verti-Bench는 Chrono `SCMTerrain`, bulldozing, mud/sand/snow semantics를 사용한다. SCM API는 current level, sinkage, plastic sinkage와 touched state를 제공한다.
- Verti-Bench paper는 SCM이 wheel interaction 뒤 terrain deformation을 시뮬레이션하며 현재 vertical displacement를 유지한다고 설명한다.
- NeSAM은 persistent terrain deformation을 motivation으로 명시하고, terrain observation/history, differentiable Bekker-Wong mechanics, EKF soil-parameter update, MPPI를 Verti-Bench와 Verti-Arena에서 평가한다.
- PSANE은 leg-terrain interaction measurement로 deformable terrain을 탐색하고 safe region/frontier를 갱신한다.
- DiffusiveGRAIN은 granular action이 environment와 robot state를 함께 바꾸는 failure를 진단하고 두 predictor를 joint planning에 사용한다.
- GranularGym code는 particle-system core를 공개하지만, 현재 repository에는 paper의 turn-key Franka excavation benchmark runner와 fixed evaluator가 없다.

필수 simple controls:

- current height/elevation-map update
- recent transition history를 쓰는 recurrent kinodynamic model
- NeSAM-style online soil-parameter adaptation
- random 또는 cost-matched interaction
- conservative no-revisit / avoid-deformable-region planner
- action-conditioned next-depth or substrate-state predictor

에이전트 추론:

- 위 controls를 통과하려면 `property uncertainty`, `mutable substrate state`, `task-compatible acquisition`이 각각 독립적으로 필요하다는 evidence가 있어야 한다.
- 그러나 현재 direct priors가 이 세 조각을 각각 이미 차지한다. 이를 하나의 architecture로 묶는 것은 failure-derived principle보다 integration으로 보인다.
- second route인 GranularGym은 core physics는 공개됐지만 fixed task/evaluator가 없어 G5 one-week independent route를 충족하지 못한다.
- Verti-Bench 내부 sand/mud/snow 또는 여러 차량은 robustness strata이지 독립 second domain으로 세지 않는다.

Decision: `reject_direct_component_coverage_and_no_ready_second_domain`.

Re-entry 조건:

1. independent second simulator/task가 exact substrate pre/post state와 downstream task metric을 공개한다.
2. current geometry/elevation, recurrent history, online parameter adaptation, action-conditioned predictor가 같은 history intervention을 설명하지 못한다.
3. failure가 property-only adaptation이 아니라 mutable-state transition과 task-preserving acquisition을 동시에 요구한다.
4. 2024--2026 exact-prior audit에서 해당 결합 원리가 실제로 비어 있다.

이는 active TODO가 아니라 external re-entry trigger다.

## 7. Reviewer And Venue Judgment

에이전트 추론:

- 현재 strict candidate 수는 `0`이다. 논문을 쓰거나 method를 고를 단계가 아니다.
- cross-simulator 방향은 reproducibility/tooling paper로는 의미가 있지만, 새 robotics principle 없이 RSS/CoRL top-tier main contribution으로 방어하기 어렵다.
- mutable-substrate 방향은 물리적으로 매력적이지만 최신 prior를 포함하면 현재 residue가 좁고, public second denominator와 simple-baseline-resistant evidence가 없다.
- “benchmark가 어렵다”, “simulator가 다양하다”, “deformable terrain이 중요하다”는 motivation일 뿐 novelty가 아니다.
- strict pass를 억지로 선언하지 않은 것이 일정상 손실이 아니라, 1주 뒤 direct-prior 또는 denominator 문제로 죽을 방향에 implementation 비용을 쓰지 않은 결과다.

## 8. Final State And Next Action

- `N26`: complete.
- strict six-condition pass: `0`.
- conditional lead: `0`.
- candidate/hypothesis/method/paper/runtime/GPU/hardware: not opened.
- N25 JaxRobotarium route: remains killed; tolerance/trajectory selection으로 구제하지 않는다.
- Cross-simulator parity and action-mutable substrate: exclusion ledger에 추가한다.
- Next: `N27 persistent internal robot-state artifact search`.

N27 boundary:

- battery state-of-charge/voltage sag, actuator temperature/saturation, fatigue/wear 중 public simulator가 state transition과 task metric을 모두 노출하는 것만 조사한다.
- generic energy-aware planning, battery-constrained routing, thermal-aware control이 direct prior로 이미 닫으면 즉시 제외한다.
- 최대 12개 official artifacts를 한 번 감사하고 strict pass가 없으면 해당 family를 종료한다.
- search 단계에는 runtime, GPU, learner, custom simulator, hardware를 열지 않는다.
