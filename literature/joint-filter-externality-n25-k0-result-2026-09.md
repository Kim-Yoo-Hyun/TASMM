# N25 Joint-Filter Externality K0 Result

> Historical route report. 이 문서의 당시 next action은 [N28](admission-bottleneck-synthesis-search-stop-n28-2026-09.md)이 대체하며, archived source/artifact를 자동 복원하지 않는다.

- Date: 2026-09-01
- Status: complete; killed at K0
- Outcome: `kill_artifact_or_instrumentation`

## 1. Decision

사실:

- Frozen `jfe-n24-v1`의 K0만 CPU Docker에서 실행했다.
- Development seeds `{0,1,2,3}`만 사용했고 main seeds `1000--1063`, K1--K3, learner, MARL training, GPU, Robotarium hardware는 실행하거나 읽지 않았다.
- Final independent verifier는 13개 artifact checks 중 10개를 통과했지만 K0 9개 조건 중 5개만 통과했다.
- Sequential rule에 따라 outcome은 `kill_artifact_or_instrumentation`이며 K1 mechanism, K2 simple-control residual, K3 outcome relevance를 열지 않는다.

에이전트 추론:

- 이 결과는 joint-filter source--victim externality가 존재하지 않는다는 반증이 아니다.
- 현재 pinned JaxRobotarium source와 default JAXopt OSQP contract가 exact counterfactual attribution oracle을 안정적으로 지탱하지 못한다는 denominator/readiness kill이다.
- Solver tolerance를 사후 완화하거나 `SOLVED` row만 골라 K1로 넘어가는 것은 N24 failure rule을 위반하므로 허용하지 않는다.

## 2. Frozen Execution

| Item | Value |
| --- | --- |
| Image | `tasm:n25-jfe-260901` |
| Image ID / local repo digest | `sha256:f7d686be30bc6170ac655019a7d30859338417b37737e3c90c6630a8e4cf5b62` |
| Image size | `430,351,637` bytes |
| Device | CPU only; no GPU request |
| JaxRobotarium | `6200711f6fb98015579af3e7a534bcfb8bcb69af` |
| Simulator submodule | `9a7ab8df8cc4e566c40d4de3eadf8ce77ec1dbd9` |
| Layered Safe MARL | `9b9d4bb7809edaf14f39a23b2df9eca954eaab9d` |
| Development seeds | `{0,1,2,3}` |
| Pool | `3,960` microstates |
| Original/action parity packet | `100` hashed rows; six scenario-count cells represented by `16--17` rows each |
| Non-ambiguous diagnostic packet | `1/100` required rows |
| Output | `/home/yoohyun/research2_retired_20260901/local_dataset/JFE_n25/results/` |

Final logs:

- build: `/home/yoohyun/research2_retired_20260901/logs/20260901_n25_jfe_build_source_action_locked.log`
- repeat A: `/home/yoohyun/research2_retired_20260901/logs/20260901_n25_jfe_run_a_source_action.log`
- repeat B: `/home/yoohyun/research2_retired_20260901/logs/20260901_n25_jfe_run_b_source_action.log`
- verifier: `/home/yoohyun/research2_retired_20260901/logs/20260901_n25_jfe_verify_source_action.log`

The producer and verifier use separate entry points. The verifier does not import producer code. Runtime network was disabled and both source snapshots were mounted read-only.

## 3. K0 Result

| K0 check | Frozen requirement | Result | Decision |
| --- | --- | --- | --- |
| K0-1 source revisions/hashes | all pinned values match | all match | pass |
| K0-2 dependency/image/config | locked; includes `jaxopt` | match; `jaxopt==0.8.3`, test dependency `quadprog==0.1.13` recorded | pass |
| K0-3 upstream smoke | barrier and environment smoke pass | barrier `2/2`, environment `11/11` in both repeats | pass |
| K0-4 original/instrumented parity | 100 rows, max error `<=1e-7` | `100` rows, max error `0.0` | pass |
| K0-5 float32/float64 parity | overall `>=99.9%`, every cell `>=99%`, max error `<=1e-4` | status-aware valid parity `44/100=0.44`; max error `0.0239234`; cell rates `0.00--0.941` | fail |
| K0-6 base/counterfactual validity | `>=99.9%`, finite | one diagnostic row; its base audit status is `UNSOLVED`; status-aware base/counterfactual valid rate `0.0` | fail |
| K0-7 CPU repeatability | max difference `<=1e-8` | A/B numeric digest identical: `66d2ebc8f5558b59e4e5ce791a1f18dcc1a5f5f91ec88e937654492fbb1fbe5e` | pass |
| K0-8 permutation equivariance | 100 non-ambiguous rows, rate `>=99%` | only `1` eligible row; that row is equivariant but support is `1/100` | fail |
| K0-9 CVXPY/OSQP agreement | 100 rows, control `<=1e-4`, objective relative `<=1e-3` | all-row max control difference `3.04706`; max objective relative difference approximately `1.0` | fail |

Final verifier summary:

- K0 checks: `5/9` pass.
- Independent artifact checks: `10/13` pass.
- Artifact checksum closure: `11/11` listed inputs pass.
- Final decision: `kill_artifact_or_instrumentation`.

## 4. Failure Diagnosis

### 4.1 Source action parity is not the blocker

사실:

- An early wrapper version propagated a reconstructed solve and missed the frozen `1e-7` parity tolerance.
- The final wrapper returns the pinned source barrier action exactly and uses a separate graph only for matrices/status.
- Final original/instrumented maximum action difference is `0.0`.

에이전트 추론:

- The final kill cannot be attributed to state-transition drift introduced by the wrapper.

### 4.2 The pinned QP is not sufficiently solved on the frozen packet

사실:

- JAXopt defines status `0` as `UNSOLVED` and `1` as `SOLVED`.
- The audit solve for the same pinned float32 QP reports `SOLVED` on only `48/100` parity rows. Float64 reports the same solved fraction.
- Requiring status, finite values, slack, and float parity leaves `44/100` valid parity rows.
- MaterialTransport `N=4` and `N=6` have zero valid float-parity rows in the frozen packet.

에이전트 추론:

- Exact counterfactual attribution would confound the proposed externality with solver termination and numerical precision. It is not a trustworthy oracle for K1 under the frozen upstream settings.

### 4.3 Diagnostic support is absent

사실:

- The deterministic frozen pool contains only one filter-active, source-non-ambiguous row after exact `R-safe` attribution.
- That row's audit base solve is `UNSOLVED`, so status-aware base/counterfactual validity is zero.

에이전트 추론:

- A `1/100` invariance packet cannot establish attribution correctness. More hand-picked geometry or post-outcome trajectory expansion would convert a support failure into selection bias.

### 4.4 Independent solver agreement also fails

사실:

- The independent CVXPY/OSQP route uses the same `A z >= b` constraints and wheel-space quadratic objective.
- The frozen 100-row agreement gate fails both control and objective-relative tolerances.
- Rows with unresolved JAXopt status dominate the largest disagreement; near-zero objectives also make the frozen relative-only objective test stringent.

에이전트 추론:

- This does not justify changing the metric after outcome. It reinforces that the current exact-oracle contract is numerically under-specified for paper evidence.

## 5. Bounded Implementation Fixes

The following changes were made before the final packet. None changes research thresholds, seeds, row quotas, or outcomes.

1. Git read-only mounts were passed as command-local `safe.directory` values.
2. Missing upstream test dependency `quadprog==0.1.13` was added to the Docker lock.
3. Exact QP graphs were compiled once per static agent-count shape to prevent per-row tracing growth.
4. Verifier validity was corrected to require JAXopt `status==SOLVED`.
5. The final wrapper returns the source barrier action exactly rather than a reconstructed action.

The final A/B artifacts were regenerated after all five fixes with the final image ID.

## 6. Claim Boundary and Next Action

사실:

- Active candidate, hypothesis, method, and paper claim remain none.
- K1--K3 artifacts and main-seed rows do not exist.

에이전트 추론:

- Close the JaxRobotarium joint-filter externality lead under the current source/contract.
- Do not retry with relaxed solver tolerances, selected solved rows, longer hand-picked conflict trajectories, or a learned attribution module.
- Re-entry would require a genuinely new denominator: an upstream revision that exposes solver status and exact primal/dual residuals under a precommitted contract, or an independent simulator/hardware route with a stable exact counterfactual oracle. It is not an automatic next task.

Next task: start a fresh simulator-first robotics direction search while adding this exact-counterfactual joint-filter route to the exclusion ledger.

## 7. Artifact Entry Points

- Probe and Docker commands: `/home/yoohyun/research2_retired_20260901/hypothesis/probes/joint-filter-externality/README.md`
- Frozen contract: [N24 contract](joint-filter-externality-n24-no-outcome-diagnostic-contract-2026-09.md)
- Metrics: `/home/yoohyun/research2_retired_20260901/local_dataset/JFE_n25/results/metrics.json`
- Independent verifier: `/home/yoohyun/research2_retired_20260901/local_dataset/JFE_n25/results/verifier.json`
- Artifact manifest: `/home/yoohyun/research2_retired_20260901/local_dataset/JFE_n25/results/artifact_manifest.json`
- Repeat artifacts: `/home/yoohyun/research2_retired_20260901/local_dataset/JFE_n25/results/run_a/`, `/home/yoohyun/research2_retired_20260901/local_dataset/JFE_n25/results/run_b/`
