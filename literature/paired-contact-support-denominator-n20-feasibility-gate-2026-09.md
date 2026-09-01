# N20 Paired Contact/Support Denominator Feasibility Gate

> Historical route report. 이 문서의 당시 next action은 [N28](admission-bottleneck-synthesis-search-stop-n28-2026-09.md)이 대체하며, archived source/artifact를 자동 복원하지 않는다.

- Date: 2026-09-01 KST
- Scope: official `DuoBench`/`Robot Control Stack` and `ManiSkill` source, adjacent 2024--2026 primary work
- Runtime: none; read-only source audit only
- Docker / GPU / dataset / policy rollout: not opened
- Outcome: `kill_no_valid_observation_matched_physical_pair`
- Active candidate / hypothesis / method / paper claim: none

## Executive Verdict

에이전트 판단:

> 두 backend 모두 state replay와 contact evidence 추출에는 충분하지만, **같은 policy-visible RGB-D/proprioception 아래 실제 contact/support 또는 load-bearing state만 달라지는 물리적으로 정당한 paired denominator**를 제공하지 않는다. Pair를 만들려면 sensor tolerance, hidden material parameter, controller/history omission, evaluator history, solver nondeterminism 중 하나에 의존해야 한다. 이들은 각각 arbitrary near-match, hidden-property/OOD benchmark, artificial POMDP, label artifact, simulator artifact로 문제를 바꾼다.

따라서 `N20`은 `N21` Docker materialization contract로 진행하지 않는다. Generic visual state aliasing은 이미 direct prior가 있고, generic vision-versus-tactile contact benchmark도 `ManiSkill-ViTac`과 `TacO`가 점유한다. 현재 evidence로는 benchmark contribution과 method necessity를 동시에 방어할 수 없다.

## 1. Fixed Gate

N20이 통과하려면 다음 조건이 모두 필요했다.

| Gate | Requirement | Result |
| --- | --- | --- |
| G0 | official source와 immutable revision | pass |
| G1 | dynamic state snapshot/restore와 replay route | conditional pass |
| G2 | contact pair와 force/impulse oracle | conditional pass |
| G3 | observation-matched이면서 물리적으로 다른 paired state | **fail** |
| G4 | pair마다 최적 action/order가 달라지는 privileged denominator | not reached |
| G5 | two tasks와 independent second backend 확장 | conditional only |
| G6 | controller/history omission 또는 solver artifact가 아닌 observation contract | **fail** |

Sequential rule상 G3와 G6가 실패하면 outcome은 `kill_no_valid_observation_matched_physical_pair`다. G4 outcome experiment, baseline, learned method를 열지 않는다.

## 2. Source Pins And Audit Boundary

사실:

| Source | Revision | Role |
| --- | --- | --- |
| [`RobotControlStack/duobench`](https://github.com/RobotControlStack/duobench) | `082a57cdafea9db115029e6fe9e03691e755f93f` | bimanual tasks, contact/stage logic |
| [`RobotControlStack/robot_control_stack`](https://github.com/RobotControlStack/robot_control_stack) | `4f78aeffae3bc4d0c02e7beab993e5406261dcf6` | MuJoCo simulator state/replay contract |
| [`haosulab/ManiSkill`](https://github.com/haosulab/ManiSkill) | `62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3` | current SAPIEN/PhysX state and contact APIs |
| archived `ManiSkill2` tag `v0.5.3` | `493be36121a9dd06071a57172274babe617b789f` | legacy API comparison only |

- Source checkout은 `/tmp/n20_paired_contact_audit/`에서 read-only로 감사했다.
- Host에서 package import, dependency install, simulator execution, compile을 하지 않았다.
- `ManiSkill2`보다 current `ManiSkill`이 유지되는 API와 explicit CPU/GPU contact-force route를 제공하므로 primary backend로 판정했다.

## 3. DuoBench / Robot Control Stack

### 3.1 What exists

사실:

- RCS `Sim.get_state_schema()`, `get_state()`, `set_state()`는 dynamic joints의 `qpos`와 `qvel`을 serialize/restore한다.
- RCS replay test는 observation을 `atol=1e-5`, reward를 `atol=1e-7`로 비교한다. 이는 useful replay witness지만 exact full-physics-state identity를 증명하지 않는다.
- DuoBench helper는 `sim.data.ncon`을 순회해 gripper contact bodies와 body-pair contact boolean을 얻는다.
- `TransferCube`는 left/right gripper contact, sole holder, both-gripper contact, transfer stage를 계산한다.
- `BlockBalance`는 MuJoCo contact pairs, velocity와 tilt를 이용해 beam/cube contact와 stability stage를 계산한다.
- MuJoCo 자체의 `mj_contactForce`를 호출하면 contact force를 추가로 얻을 수 있지만 DuoBench/RCS가 이 값을 benchmark label로 expose하지는 않는다.

### 3.2 What is missing

사실:

- RCS state vector에는 actuator/controller target, applied control, contact impulse/force, solver warm-start state가 없다.
- DuoBench의 stage tracker는 누적 `internal_state`와 `initial_holder` 같은 history variable을 별도로 유지한다. RCS `Sim` snapshot에는 이 state가 포함되지 않는다.
- Contact existence는 얻을 수 있지만 support/load-bearing graph 또는 normalized load share는 native benchmark field가 아니다.

에이전트 추론:

- `TransferCube`의 `initial_holder`나 sticky stage를 숨겨 pair를 만들면 동일한 physical state의 evaluator history만 달라진다. 이는 desired contact-state aliasing이 아니다.
- `qpos/qvel`만 복원하고 controller target을 의도적으로 누락해 다음 action outcome을 바꾸면, action/controller history baseline으로 닫히는 artificial partial-observation setup이다.
- `mj_contactForce` adapter는 G2를 보강할 수 있지만 G3의 paired construction을 해결하지 않는다.

## 4. ManiSkill

### 4.1 What exists

사실:

- `BaseEnv.get_state_dict()`는 scene actor/articulation state와 controller state를 모은다.
- `Scene.get_sim_state()`/`set_sim_state()`는 dynamic actor pose/linear velocity/angular velocity와 articulation `qpos/qvel`을 저장·복원한다. Static actor state는 deterministic reconstruction을 전제로 제외한다.
- `Scene.get_pairwise_contact_impulses()`와 `get_pairwise_contact_forces()`는 CPU와 GPU route에서 pairwise privileged contact evidence를 제공한다.
- `Humanoid TransportBox`는 left/right hand-to-box contact force와 force threshold를 실제 evaluation field에 사용한다.
- `TwoRobotStackCube`는 two-arm stack/release action structure를 제공한다.
- CPU state-replay tests는 restored observation equality를 검사하지만 tolerance가 존재한다. GPU test suite는 GPU simulation이 deterministic하지 않음을 명시한다.

### 4.2 Snapshot caveat

사실:

- `get_state_dict()`는 non-empty controller state를 `controller` key에 넣는다.
- 감사한 current source의 `set_state_dict()`는 `scene.set_sim_state(state, env_idx)`를 호출하지만 controller restore를 명시적으로 호출하지 않는다.
- Flat `set_state()`도 actor/articulation state를 재구성하는 경로가 중심이다.

에이전트 추론:

- 이 asymmetry는 replay contract를 검증할 때 보완해야 할 implementation issue지만, 이를 이용해 pair를 정의하면 desired physical contact latent가 아니라 omitted controller state를 측정하게 된다.
- `Humanoid TransportBox`는 force-label feasibility를, `TwoRobotStackCube`는 two-arm task feasibility를 각각 보여준다. 둘을 결합해도 observation-matched counterfactual pair는 자동으로 생기지 않는다.

## 5. Why The Pair Cannot Be Defined Cleanly

고정하려던 visible state를 `o=(RGB-D, proprioception, recent action/history)`로, privileged state를 `z=(contact topology, support/load share)`로 두었다. Required pair는 `d(o_i,o_j) <= epsilon`, `z_i != z_j`, `a_i* != a_j*`를 만족해야 한다.

| Construction route | Superficial benefit | Why it fails the intended claim |
| --- | --- | --- |
| Tiny pose/contact-gap perturbation below image threshold | easiest simulator pair | exact pair가 아니라 arbitrary `epsilon` pair다. High-precision depth/proprioception 또는 다른 rendering resolution이 차이를 복구한다. Real sensor calibration 없이는 threshold가 claim-dependent다. |
| Hidden mass, friction, compliance change | same geometry with different response | problem이 contact topology가 아니라 hidden physical-property/OOD inference로 바뀐다. Known direct-prior crowding도 크다. |
| Controller target, previous action, gripper command omission | next-step outcome can diverge | simple action-history/controller-state baseline으로 닫히는 artificial observation contract다. |
| DuoBench sticky stage or `initial_holder` change | exact visible-state match possible | physical state가 아니라 evaluator bookkeeping history가 다르다. |
| Solver cache, warm-start, GPU nondeterminism | different force realization possible | reproducible physical latent가 아닌 backend artifact다. |

에이전트 추론:

- 동일 rigid-body model에서 complete generalized positions/velocities, controller/applied forces와 deterministic solver state가 같으면 contact response도 결정된다.
- 의미 있는 non-identifiability는 compliant deformation, hysteresis, internal tactile state 또는 statically indeterminate force distribution처럼 **실제로 존재하지만 policy-visible sensor가 보지 못하는 state**에서 나와야 한다.
- 현재 두 backend의 standard rigid task/snapshot contract는 그러한 latent를 ground truth로 보존하지 않는다. 이 상태에서 pair를 강제하면 failure diagnosis가 method form을 필연적으로 요구하지 못한다.

## 6. Exact-Prior Pressure

논문 주장:

- [`Mitigating State Aliasing in Vision-Language-Action Models via Inverse Dynamics Learning`](https://arxiv.org/abs/2605.29577)은 visually similar states가 different actions를 요구하는 VLA state aliasing을 직접 문제화하고 inverse-dynamics supervision을 제시한다.
- [`ManiSkill-ViTac 2025`](https://arxiv.org/abs/2411.12503)은 contact-rich manipulation에서 vision-only와 visual-tactile policy를 비교하는 simulated/real benchmark를 제공한다. [Official code](https://github.com/chuanyune/ManiSkill-ViTac2025)
- [`TacO: Benchmarking Tactile Sensors for Object Manipulation`](https://arxiv.org/abs/2605.21976)은 unknown-mass pick-and-place, reorientation, plug insertion 등에서 vision-only와 visuotactile policies 및 tactile sensor properties를 비교한다. [Project](https://tacobench.github.io/)
- N18에서 감사한 `Broadcasting Support Relations`, `Tactile-Driven Extrinsic Contact Mode Control`, `PhysGraph`, `D-CODA`는 support graph, tactile contact mode, contact-state graph/augmentation의 obvious method forms를 이미 점유한다.

에이전트 추론:

- “visual state aliasing이 있으므로 history/inverse dynamics를 쓴다”는 broad claim은 direct prior와 충돌한다.
- “vision이 contact를 못 보므로 tactile을 추가한다”는 benchmark/method claim도 crowded하다.
- 남을 가능성이 있던 좁고 방어 가능한 insight는 **support/load-path topology를 바꾼 observation-matched pair에서 action ordering이 뒤집히는 mechanism**이었다. 하지만 N20은 이 insight를 측정할 denominator 자체가 성립하지 않음을 보였다.

## 7. Final Gate Decision

### 사실

- Two official backends 모두 snapshot/replay와 contact-label extraction의 building block을 가진다.
- 어느 backend도 native pair generator, support/load-share state, same-observation/different-physical-state contract를 제공하지 않는다.
- No runtime artifact or result was generated.

### 에이전트 판단

- Outcome: `kill_no_valid_observation_matched_physical_pair`.
- `N21` paired-state Docker CPU materialization, policy rollout, GPU experiment, baseline implementation, method design을 열지 않는다.
- “API가 있으니 데이터를 만들 수 있다”를 “연구 질문을 검증하는 denominator가 있다”로 과장하지 않는다.

### Re-entry Requirement

다음 조건이 함께 생길 때만 이 family를 다시 연다.

1. force/tactile hardware 또는 compliant tactile simulator가 deformation/hysteresis/internal contact state를 reproducibly expose한다.
2. Policy-visible sensor stream과 privileged physical state의 calibration이 고정되어 arbitrary `epsilon`을 피한다.
3. 같은 visible history에서 different optimal action/order를 보이는 pair와 cost-matched simple controls를 만들 수 있다.
4. `TacO`, `ManiSkill-ViTac`, inverse-dynamics state-aliasing prior 위에 남는 exact mechanism residue가 있다.
5. 두 task family 또는 simulator-to-real second route가 있다.

## 8. Reusable Evidence

- DuoBench: bimanual task/stage/contact source locations와 RCS snapshot limitation.
- ManiSkill: CPU/GPU pairwise contact-force API, replay nondeterminism caveat, controller-state restore caveat.
- Negative construction taxonomy: tolerance pair, hidden-property pair, omitted-controller pair, evaluator-history pair, solver-artifact pair.

이 evidence는 이후 tactile/contact 주제의 early feasibility filter로만 재사용한다. 새 candidate나 method rationale로 간주하지 않는다.
