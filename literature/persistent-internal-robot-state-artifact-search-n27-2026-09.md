# N27 Persistent Internal Robot-State Artifact Search

> Historical route report. 이 문서의 당시 next action은 [N28](admission-bottleneck-synthesis-search-stop-n28-2026-09.md)이 대체하며, archived source/artifact를 자동 복원하지 않는다.

- Date: 2026-09-01
- Status: complete; strict pass 0, conditional lead 0
- Outcome: `no_pass_exit_internal_state_family`

## 1. Decision

에이전트 추론:

- Battery state-of-charge/voltage sag, actuator thermal state/saturation, fatigue/wear를 12개 primary/official artifact 범위에서 감사했지만 여섯 진입 조건을 모두 만족한 research candidate는 없다.
- Battery-aware planning은 공개 실행 substrate가 가장 강하지만 `Open-RMF`, `meSch`, energy-aware task allocation, battery-health-aware fleet scheduling이 threshold, charging, assignment, persistence, degradation cost를 이미 직접 다룬다.
- Motor thermal state는 long-horizon robot capability를 실제로 바꾸는 persistent state지만 2026년의 temperature-conditioned locomotion policy와 whole-body thermal residual policy가 problem, representation, reward와 hardware consequence를 직접 점유한다.
- Saturation은 `Isaac Lab`의 public actuator model에서 재현 가능하지만 현재 형태는 accumulated health state가 아니라 instantaneous torque-speed clipping이다. Rate/effort limits와 history actuator model이 simple solution이다.
- Fatigue/wear는 `MyoSuite`가 cumulative fatigue state와 task success를 함께 공개하지만 biological muscle domain이고, electric actuator 쪽은 recent fault estimator/adaptive control prior가 이미 강하다. 두 영역을 합치는 것만으로는 새 robotics principle이 아니다.
- 가장 가까운 residue인 voltage-sag-dependent actuation capability도 공개 fixed task/evaluator가 없고 voltage-conditioned torque envelope, conservative derating, SoC/voltage threshold가 먼저 닫는다.
- 따라서 candidate, hypothesis, method, learner, Docker runtime, GPU, dataset download와 hardware를 열지 않는다.

## 2. Frozen Admission Contract

사용자 판단:

- 정량 evidence의 대부분은 simulation에서 산출한다.
- hardware는 마지막 quantitative validation에만 사용한다.
- 다음 여섯 조건은 완화하지 않는다.

| Gate | Required evidence |
| --- | --- |
| G1 public denominator | Public code/data/evaluator와 fixed task metric이 있다. |
| G2 exact novelty | 2024--2026 direct prior가 문제와 원리를 점유하지 않았다. |
| G3 simple residual | 최소 세 simple baseline 뒤에도 case-level residual이 남는다. |
| G4 one-week kill | outcome 전 고정 가능한 1주 kill test가 있다. |
| G5 two-domain route | 두 simulator/task domain 또는 독립 quantitative hardware route가 있다. |
| G6 forced method | failure가 특정 state representation/inference/control form을 강제한다. |

Persistent internal state의 operational definition:

- 이전 action/load history에 따라 변한다.
- 현재 또는 미래 actuation/task feasibility를 바꾼다.
- episode 중 단순한 pose/velocity observation만으로 제거되지 않는다.
- static effort limit, one-shot motor-strength randomization, external terrain/contact state는 포함하지 않는다.

## 3. Audited Official Artifacts

12-artifact ceiling을 초과하지 않았다.

| ID | Primary / official artifact | Released contract | N27 judgment |
| --- | --- | --- | --- |
| A01 | [Gazebo Sim LinearBattery demo](https://github.com/gazebosim/gz-sim/blob/main/examples/worlds/linear_battery_demo.sdf) | SoC transition, recharge, zero-charge joint-force cutoff | state substrate only; no fixed robotics benchmark metric |
| A02 | [CTU Gazebo ROS Battery](https://github.com/ctu-vras/gazebo_ros_battery) | open-circuit voltage, load-dependent discharge, dynamic temperature/internal resistance, motor/mechanical consumers | rich transition model but example world, not task/evaluator denominator |
| A03 | [Open-RMF task planner](https://docs.ros.org/en/rolling/p/rmf_task/generated/classrmf__task_1_1TaskPlanner.html) / [demos](https://github.com/open-rmf/rmf_demos) | SoC-aware feasibility, recharge insertion, `BatteryAware` assignment profile and battery penalty | executable task substrate, but simple baseline and platform solution already exist |
| A04 | [Webots Robot battery API/sample](https://cyberbotics.com/doc/reference/robot?version=released) | motor energy drains battery, charger restores it, zero energy terminates controller | independent simulator substrate; battery-specific fixed evaluator absent |
| A05 | [meSch, IROS 2025](https://dasc-lab.github.io/papers/2025/2025-mesch/) / [code](https://github.com/kalebbennaveed/meSch) | SoC-aware persistent multi-robot scheduling, fixed/mobile charger, simulation and hardware | directly occupies persistent battery scheduling |
| A06 | [Energy-Aware Task Allocation for Teams of Multi-mode Robots, 2025](https://arxiv.org/abs/2503.12787) | joint task/mobility-mode allocation under state- and environment-dependent energy cost | occupies mode/task/energy co-optimization |
| A07 | [Fleet-Level Battery-Health-Aware Scheduling, 2026](https://arxiv.org/abs/2603.22731) | assignment, sequencing, charging mode/access and battery aging jointly optimized | directly occupies battery wear/health scheduling |
| A08 | [Isaac Lab actuator models](https://isaac-sim.github.io/IsaacLab/develop/source/concepts/actuators.html) | effort/velocity limits, DC motor torque-speed envelope, delay, angle-dependent ceiling, learned history model | public saturation substrate; no accumulating thermal/wear state |
| A09 | [Learning Thermal-Aware Locomotion Policies, 2026](https://arxiv.org/abs/2603.01631) | motor temperature in policy state plus thermal reward; Unitree A1 long-duration validation | directly occupies thermal-state-conditioned locomotion |
| A10 | [Learning to Balance Motor Thermal Safety..., 2026](https://arxiv.org/abs/2605.27046) | whole-body thermal transition plus residual policy, simulation and Unitree A1 validation | directly occupies failure-derived thermal residual control |
| A11 | [MyoSuite](https://arxiv.org/abs/2205.13600) / [code](https://github.com/MyoHub/myosuite) | cumulative muscle fatigue/sarcopenia, contact-rich tasks, reward and success evaluator | valid fatigue denominator, but biological domain and principle already explicit |
| A12 | [FT-WBC, 2026](https://ft-wbc.github.io/) | proprioceptive fault estimator and posture adaptation under weakening/locked actuators; simulation and real robot | occupies latent actuator-health inference/adaptation boundary |

### 3.1 Read-Only Source Audit

사실:

- `/home/yoohyun/PaperReview`는 discovery registry로만 사용했고 primary/official source에서 재검증했다.
- Read-only checkouts는 `/tmp/n27-audit-NUgpIm/`에만 만들었다. Dependency install, import, compile, simulator runtime은 수행하지 않았다.
- Audited revisions:
  - `gazebo_ros_battery`: `bfb8f4490e437def60237d17b7697a0d7e55b8a8`
  - `meSch`: `948e9a93edf1dfb4e14629ef710d6e86ac54e588`
  - `myosuite`: `94300995076b20ed6a8cfc65794c54bc997a0697`
  - `rmf_demos`: `4f8850fd3ff9c214252e4428d2ed03a646e6c839`
  - `robotVitals` supporting audit: `f16ca589599c687c5ecf96e2188422cf56af971f`

Source-level observations:

- `gazebo_ros_battery` updates SoC from component load and voltage and optionally computes temperature and temperature-dependent internal resistance. It provides only an example world and lint tests; no fixed task set, success evaluator or policy baseline is released.
- Current `rmf_demos` configs expose `account_for_battery_drain`, `recharge_threshold`, `recharge_soc`, `BatteryAware` and polynomial `battery_penalty`. `rmf_demos_tasks` can dispatch and observe task completion, but no frozen battery benchmark split/scoreboard is defined.
- `meSch` releases double-integrator/quadrotor dynamics, linear SoC discharge, fixed/mobile charger experiments and simulation notebooks. This is a method artifact, not an unoccupied denominator.
- `MyoSuite` implements a 3CC-r cumulative fatigue state, applies history-dependent available muscle activation, and shares the existing task reward/`solved` evaluator. Thus progressive internal capability loss is already an explicit benchmark variation.
- `robotVitals` exposes a reusable Gazebo/real-robot performance-degradation monitor, but its published experiments manipulate laser noise and rough terrain rather than battery/thermal/wear transitions. It is supporting prior, not a valid N27 denominator.

## 4. Family-Level Screening

Legend: `P` pass, `C` conditional, `F` fail.

| Family / provisional question | G1 | G2 | G3 | G4 | G5 | G6 | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| SoC-aware robot task allocation and charging | P | F | F | P | P | F | Open-RMF/meSch/recent scheduling directly own it |
| Battery aging/health-aware fleet scheduling | C | F | F | P | C | F | 2026 fleet-level SoH scheduling and simple degradation cost close it |
| Voltage sag changes low-level actuator capability and task success | F | C | F | C | F | F | no public denominator; voltage-conditioned torque scaling is obvious |
| Motor temperature history changes locomotion feasibility | C | F | F | C | C | F | two 2026 thermal policies directly own problem and method forms |
| Static effort/velocity saturation causes policy failure | P | F | F | P | P | F | actuator envelope, rate limit and clipping controls close it |
| Gradual electric-actuator wear must be inferred online | F | F | C | C | C | C | FT-WBC/ADAPT/fault-tolerant flow plus no public gradual-wear evaluator |
| Cumulative muscle fatigue changes manipulation/locomotion success | P | F | F | P | F | F | MyoSuite already exposes the state and phenomenon; not a second robot domain |
| Cross-episode carry-over invalidates IID policy evaluation | F | C | F | C | F | F | reset/cool-down/block randomization and state stratification close it |

에이전트 추론:

- G1만 통과하는 것은 충분하지 않다. `Open-RMF`와 `MyoSuite`는 실행 가능한 substrate지만 각각 G2/G3/G6가 실패한다.
- Hidden internal state로 좁혀도 recent thermal and fault-estimation methods가 temperature/proprioceptive history를 이용한 inference/control을 직접 다룬다.
- State를 observable로 만들면 threshold/penalty/state-conditioned policy가 닫고, hidden으로 만들면 recurrent adaptation, system identification, fault estimator가 strongest simple/adjacent baseline이 된다.
- Public battery plugins와 robot task suite를 임의로 결합하면 denominator contribution이 아니라 authored custom benchmark가 되며, 사용자가 고정한 G1을 충족했다고 셀 수 없다.

## 5. Required Simple Controls

후속 method를 정당화하려면 최소한 아래 controls를 모두 같은 state/action evidence와 cost에서 이겨야 한다.

- current SoC/voltage/temperature threshold and safe stop
- conservative power/torque derating
- remaining-energy or time-to-limit predictor
- `Open-RMF BatteryAware` assignment/recharge scheduling
- temperature/health appended to policy observation
- recurrent policy over recent proprioception/action/current history
- randomized motor strength/effort limit during training
- online dynamics or actuator-parameter adaptation
- fault estimator plus gait/posture library
- fixed cool-down/reset and order-blocked evaluation

에이전트 추론:

- Battery scheduling은 first four controls에서 닫힌다.
- Thermal locomotion은 temperature-conditioned policy와 residual policy가 이미 direct prior다.
- Hidden wear는 recurrent adaptation/fault estimation이 자연스러운 answer이며, 이를 넘어서는 specific method necessity를 강제할 released paired failure가 없다.

## 6. Strongest Rejected Residue

검토한 provisional question:

> When load history causes voltage sag or thermal accumulation to reduce the actuator envelope, can two trajectories with the same pose/task state have different future feasibility, requiring a joint belief over resource state and action-dependent capability rather than an energy budget alone?

사실:

- `gazebo_ros_battery`는 load-dependent voltage, temperature와 internal resistance를 계산한다.
- `Isaac Lab`은 voltage-independent DC motor torque-speed envelope와 history-based actuator models를 제공한다.
- 두 공개 component를 연결한 frozen task benchmark/evaluator는 확인하지 못했다.
- Thermal papers는 action/load history에서 temperature를 갱신하고 policy input/reward 또는 residual control에 사용한다.

에이전트 추론:

- Battery model과 actuator envelope를 직접 연결하면 G1을 새로 제작해야 한다.
- 먼저 비교할 control은 `tau_max(V)` scaling, voltage threshold, time-to-cutoff MPC다. 이들은 representation novelty 없이 provisional failure를 설명한다.
- Thermal branch로 이동하면 A09/A10이 joint resource-state/control principle을 이미 점유한다.
- Manipulation, navigation, locomotion 두 domain에 같은 calibrated transition을 제공하는 public route도 없다.

Decision: `reject_no_public_denominator_simple_coupling_and_direct_thermal_prior`.

## 7. Reviewer Judgment

에이전트 추론:

- Persistent internal robot state는 실제 배치 문제로는 중요하지만 현재 확보한 artifact 아래에서는 top-tier research gap이 아니다.
- “현재 benchmark가 battery/thermal/wear를 무시한다”는 motivation이다. 공개 paired failure, nontrivial residual과 method necessity가 없으면 novelty가 아니다.
- Battery/thermal/wear module을 existing simulator에 붙이는 것은 systems engineering 또는 benchmark construction이며, 현재 사용자가 고정한 admission rule 아래 research candidate로 승격할 수 없다.
- 이 family를 더 좁혀 탐색하면 voltage curve, motor type 또는 특정 robot에 claim이 갇힐 가능성이 높다.

## 8. Final State And Next Action

- `N27`: complete.
- strict six-condition pass: `0`.
- conditional lead: `0`.
- outcome: `no_pass_exit_internal_state_family`.
- Candidate/hypothesis/method/paper/runtime/GPU/hardware: not opened.
- Battery/thermal/saturation/fatigue/wear를 더 좁혀 구제하지 않는다.
- Next: `N28 admission-bottleneck synthesis and search-stop decision`.

N28 boundary:

- N20--N27의 각 gate failure를 집계해 반복되는 bottleneck이 topic shortage인지, public-denominator constraint인지, exact-prior crowding인지 분리한다.
- criteria를 완화하거나 새 candidate를 만드는 작업이 아니다.
- 같은 search pattern의 반복이 합리적인지 판단하고, 다음 research search를 열 수 있는 falsifiable entry condition을 한 번 고정한다.
- 문서 synthesis만 수행하며 runtime, GPU, method, dataset, hardware를 열지 않는다.
