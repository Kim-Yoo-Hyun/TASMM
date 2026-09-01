# N24 Joint-Filter Externality No-Outcome Diagnostic Contract

> Historical route contract. 이 문서의 당시 next action은 [N28](admission-bottleneck-synthesis-search-stop-n28-2026-09.md)이 대체하며, archived source/artifact를 자동 복원하지 않는다.

- Date: 2026-09-01
- Status: complete; contract frozen, no runtime or outcome read
- Outcome: `ready_for_n25_k0_docker_preflight_only`

## 1. Decision

에이전트 추론:

- N24는 candidate나 hypothesis를 승격하지 않는다. JaxRobotarium의 joint safety filter에서 `corrected victim`과 `causal source proposal`이 다른지를 가장 단순한 controls로 기각할 수 있게 만드는 no-outcome contract다.
- JaxRobotarium repository에는 deployment config가 있지만 config가 가리키는 trained weights가 없다. 따라서 checkpoint availability에 기대지 않고 official scenario/action semantics를 따르는 deterministic scripted proposal로 K0--K3를 진단한다.
- Primary correction burden은 Euclidean action difference가 아니다. Audited QP가 실제로 최소화하는 projected wheel-velocity discrepancy를 per-agent contribution으로 분해한다.
- Counterfactual reference는 arbitrary agent removal이 아니다. Agent는 같은 state와 constraint graph에 남겨 두고, 그 agent의 nominal proposal만 base QP가 적용한 safe action으로 바꾼다. Zero proposal은 sensitivity로만 사용한다.
- K0 source/artifact preflight 전에는 K1--K3 main seeds를 실행하거나 읽지 않는다. K0--K3 전부 통과하기 전에는 learner, reward modification, MARL training, candidate, hypothesis, paper claim을 열지 않는다.

## 2. Question and Claim Boundary

Falsifiable diagnostic question:

> When a joint barrier QP corrects multiple robots, how often does the largest victim-side correction identify a different agent from the nominal proposal whose removal most reduces other agents' correction burden, and does this residual predict coordination stall beyond geometry, intervention magnitude, executed-action features, and Layered Safe MARL's multi-engagement signal?

허용하지 않는 claim:

- a new safety filter
- generic safe MARL
- resolving conflicting constraints
- responsibility allocation or fairness
- causal performance improvement
- sim-to-real transfer

K0--K3가 모두 survive해도 허용되는 결론은 `minimal learning-intervention contract를 열 가치가 있다`까지다. Predictive diagnostic만으로 causal learning claim을 쓰지 않는다.

## 3. Audited Sources and Frozen Revisions

### 3.1 JaxRobotarium

사실:

- official repository: [GT-STAR-Lab/JaxRobotarium](https://github.com/GT-STAR-Lab/JaxRobotarium)
- repository commit: `6200711f6fb98015579af3e7a534bcfb8bcb69af`
- Robotarium simulator submodule commit: `9a7ab8df8cc4e566c40d4de3eadf8ce77ec1dbd9`
- `Controller.get_action` computes controller output `dxu`, applies `barrier_fn`, and returns only `dxu_safe`.
- `create_robust_barriers` creates every inter-robot pair constraint in one OSQP problem. Each pair row contains both agents' wheel-control terms.
- The source constructs `D`, `L`, `L_all`, `Q=2 L_all^T L_all`, and solves the joint projection before converting wheel velocities back to unicycle controls.
- `Navigation` reset generates `2N` positions: the first `N` are robots and the next `N` are individual goals. Its official test contains a deterministic greedy cardinal goal policy.
- `MaterialTransport` exposes robot poses, remaining zone loads, payload, speed and carrying-capacity fields, and task success/material remaining.
- Deployment configs use `clf_uni_position`, `robust_barriers`, discrete cardinal waypoints, `update_frequency=30` for Navigation and `60` for MaterialTransport.
- Referenced deployment `models/...safetensors` files are absent from the audited repository.
- `pyproject.toml` lists unpinned packages and omits `jaxopt`, although the barrier implementation imports `jaxopt.OSQP`.

Frozen source hashes:

| File | SHA-256 |
| --- | --- |
| `pyproject.toml` | `85702731496d05c1a2b99503d64d11a43b8df077d5dee5aa860e4864c9d70993` |
| `jaxrobotarium/robotarium_env.py` | `58a7ac18536162352128ef0c86453ae4001aa4d6cfb6197cce6b9dffdfbf3404` |
| `jaxrobotarium/scenarios/navigation.py` | `2993d8b0eb0e4821ec0d34e728196841065809008877cee9ac77028641616b84` |
| `jaxrobotarium/scenarios/material_transport.py` | `74d09f650bfb59a35f867354fc579522a8ce1ae1c039d78e9c71ceace00b7228` |
| `rps_jax/utilities/barrier_certificates2.py` | `eb274d5959feac03d5d3437f955d68a250f1e8131a0fbfc68699ba7244d10a51` |

### 3.2 Layered Safe MARL

사실:

- official repository: [DINaMo-MIT/Layered-Safe-MARL](https://github.com/DINaMo-MIT/Layered-Safe-MARL)
- audited commit: `9b9d4bb7809edaf14f39a23b2df9eca954eaab9d`
- The repository includes double-integrator and air-taxi trained models, but N24 does not execute them.
- `reward_multiple_engagement` activates only when more than one other agent is within engagement distance and accumulates closing speed weighted by closeness to separation distance.
- `reward_diff_from_filtered_action` penalizes the agent's own `action_diff`.
- These are direct simple-control threats to the retained lead.

Frozen source hashes:

| File | SHA-256 |
| --- | --- |
| `multiagent/config.py` | `a2a985a4f792106aebe9942e01272d6fdf93a49b886b8949571f88319087981e` |
| `multiagent/custom_scenarios/navigation_graph_safe.py` | `16699445122773da53f9bbab1c38d68ee0352dc48988fa843a91fafe37f323da` |

논문 주장:

- [Layered Safe MARL](https://www.roboticsproceedings.org/rss21/p094.html) claims that learning to avoid multi-agent interactions, prioritizing urgent pairs, and applying a tactical safety filter reduce conflicts while preserving safety and efficiency.
- [Learning Responsibility Allocations](https://arxiv.org/abs/2410.07409) defines responsibility as willingness to deviate from desired control and learns state-dependent allocation with differentiable CBF optimization.

에이전트 추론:

- N24가 새롭게 검사할 수 있는 residue는 responsibility share나 conflict prevalence가 아니다. `own correction`이 corrected victim을 측정할 뿐 other-agent burden을 야기한 source proposal을 측정하지 못한다는 source--victim distinction뿐이다.

## 4. Frozen Execution Scope

### 4.1 Scenarios and agent counts

| ID | Scenario | Agent counts | Role |
| --- | --- | --- | --- |
| S1 | `Navigation` | `N={2,4,6}` | independent goals and crossing conflicts |
| S2 | `MaterialTransport` | `N={2,4,6}` | shared task, bidirectional loading/drop-off traffic |

- `N=2` is the pairwise control stratum; it cannot contain an active-constraint node with degree at least two.
- `N=4` is primary and matches the official MaterialTransport scale.
- `N=6` is density/scale stress. Navigation is capped at six because its reset samples `2N` points without replacement from a finite 0.5 m grid; larger `N` approaches or exceeds the current reset capacity.
- Primary phenomenon/generalization statements require both S1 and S2 and must not be based on pooled rows alone.

### 4.2 Environment configuration

Common:

- `action_type=Discrete`
- controller `clf_uni_position`
- barrier `robust_barriers`
- `SAFETY_RADIUS=0.20`
- `actuation_noise=0`
- simulator backend `jax`
- `eval=True`, so controller and barrier are recomputed at every simulator microstep as in deployment rather than held fixed for an entire macro action

S1:

- `max_steps=100`
- `update_frequency=30`
- `step_dist=0.2`
- `goal_radius=0.1`

S2:

- `max_steps=70`
- `update_frequency=60`
- homogeneous capability `[speed=0.30, capacity=10]` repeated exactly `N` times in the primary diagnostic, eliminating capability allocation as an explanation
- deterministic work per agent: `zone1_mu=10N`, `zone2_mu=5N`, both `sigma=0`
- `step_dist=1` is retained; the scenario-specific decoder multiplies it by speed capability
- official heterogeneous capability sets are deferred to robustness after K0--K3 and cannot rescue a failed primary gate

### 4.3 Deterministic proposal policies

P-S1 `greedy-cardinal-goal`:

1. If an agent is within `goal_radius`, emit discrete null action `0`.
2. Otherwise normalize the vector to its assigned goal.
3. Take `argmax` dot product over `[[0,0],[0,1],[0,-1],[1,0],[-1,0]]` using source order for tie breaking.

This is the policy in the official Navigation batched-rollout test with the at-goal guard added to avoid zero-vector normalization.

P-S2 `load-deliver-cardinal`:

1. Let Robotarium bounds be `[b_x,b_y,w,h]`.
2. If carrying payload, greedily move toward `[b_x+0.1,0]` in the left drop-off zone.
3. Else if `zone1_load>0`, greedily move toward `[0,0]`, the central circular loading zone.
4. Else if `zone2_load>0`, greedily move toward `[b_x+w-0.1,current_y]` in the right loading strip.
5. Else emit action `0`.
6. Use the same cardinal `argmax` and source-order tie rule as P-S1.

These are controlled diagnostic proposals, not learned baselines and not proposed methods. No checkpoint is downloaded or inferred.

### 4.4 Seeds and leakage boundary

- K0 development-only seeds: `{0,1,2,3}`. K0 may inspect schema, finite values, solver validity and invariants but may not aggregate mechanism or outcome metrics.
- Main seeds: `{1000,...,1063}` for every scenario-by-agent-count cell.
- Fit split: `1000--1031`; held-out test split: `1032--1063`.
- No threshold, feature, event rule, model hyperparameter or exclusion may change after any main-seed row is read.
- Agent permutations are generated from a separate deterministic key derived from `SHA256("n24-permute|scenario|N|seed|macro_step")` and do not alter the fit/test split.

## 5. Instrumentation and Row Contract

The instrumentation wrapper may expose source intermediates but must not change scenario state transition, controller output or base safe action.

### 5.1 Required tables

`microstep_rows.parquet` primary key:

`(schema_version, scenario, N, seed, split, macro_step, micro_step, agent_id)`

Required fields:

- robot pose `x,y,theta`
- decoded waypoint and discrete action
- `u_nominal[v,omega]`
- source float32 `u_safe_executed[v,omega]`
- diagnostic float64 `u_safe_base[v,omega]`
- wheel-space nominal and safe controls
- per-agent exact QP burden
- minimum pair distance, pairwise closing speed, active-constraint degree
- solver finite/status, primal slack minimum, base parity error
- scenario progress fields and done/success fields

`counterfactual_rows.parquet` primary key:

`(scenario,N,seed,macro_step,micro_step,reference,source_agent,victim_agent)`

Required fields:

- base burden, counterfactual burden, signed `E_ij`, positive `E_ij`
- reference control and counterfactual safe control
- counterfactual solver validity/slack
- source score, source-effect ratio and ambiguity flags

`event_rows.parquet` contains only the first valid filter-active microstep of each macro step. This avoids treating highly autocorrelated simulator microsteps as independent events. It includes all B0--B5 fields, O1 fields and future-stall targets, but statistical resampling remains episode-clustered.

`episode_rows.parquet` contains success, first completion step, normalized completion time, total path length, minimum separation, intervention burden, stall count, final task remainder and solver-validity counts.

### 5.2 Artifact set

- `source_manifest.json`
- `dependency.lock`
- `config.lock.yaml`
- `microstep_rows.parquet`
- `counterfactual_rows.parquet`
- `event_rows.parquet`
- `episode_rows.parquet`
- `metrics.json`
- `verifier.json`
- `commands.txt`

No rendered video is a required artifact.

## 6. Exact Burden and Counterfactual Semantics

### 6.1 Base burden

Let `D` and `L` be the exact matrices constructed by the audited barrier source. For agent `j`, convert unicycle control to wheel velocity:

`z_j = D^{-1} u_j`.

The per-agent base burden is:

`C_j = (z_j^safe - z_j^nom)^T L^T L (z_j^safe - z_j^nom)`.

`C_total = sum_j C_j`.

This is the per-agent contribution to the source QP objective up to its constant/scale, and is primary. Euclidean `||u_safe-u_nom||_2` is recorded only as B2-E sensitivity.

### 6.2 Active event

A microstep is base-valid when:

- every control and solution value is finite;
- minimum primal slack over the original `A z >= b` is at least `-1e-5`;
- float32 executed and float64 diagnostic safe actions have maximum absolute difference at most `1e-4`.

A valid microstep is filter-active when:

- at least one robot-pair constraint has slack `<=1e-5`; and
- at least one agent has `||u_safe_executed-u_nominal||_2 > 1e-4`.

Velocity-limit-only events are recorded but are not eligible for source--victim analysis.

### 6.3 Primary reference `R-safe`

At fixed state `x` and fixed constraints:

1. Solve the base diagnostic QP for all nominal proposals `u_nom` and obtain `u_safe_base`.
2. For source candidate `i`, replace only `u_nom_i` with `u_safe_base_i`.
3. Keep every other nominal proposal and every robot state unchanged.
4. Re-solve the same QP.

For `j != i`:

`E_ij = C_j(base) - C_j(counterfactual_i)`.

Diagonal `E_ii` is undefined and stored as null because the counterfactual changes agent `i`'s own nominal reference. Negative off-diagonal values are retained. Positive source score:

`S_i = sum_{j != i} max(E_ij,0)`.

Source-effect ratio:

`R_i = S_i / (C_total + 1e-12)`.

`R_i` is not assumed to be bounded by one because marginal effects can overlap.

### 6.4 Sensitivity reference `R-zero`

Replace only `u_nom_i` with exact zero unicycle control and re-solve. It remains a proposal intervention, not physical agent removal. `R-zero` cannot be chosen after outcomes; primary claims use `R-safe` and must remain directionally stable under `R-zero`.

### 6.5 Source, victim and ambiguity

- top source `i* = argmax_i S_i`
- top victim `j* = argmax_j C_j`
- source--victim mismatch `M=1[i* != j*]`
- a source or victim tie is ambiguous when the top-two gap is at most `1e-6 * max(1, top_value)`
- an event is source-significant only when `max_i R_i >= 0.10`
- ambiguous or non-significant events are excluded from mismatch numerators but included in support and exclusion reports

## 7. Controls B0--B5 and Oracle O1

All learned diagnostic predictors train on fit episodes only. No counterfactual/O1 field enters B0--B5.

| ID | Control | Frozen definition |
| --- | --- | --- |
| B0 | uniform source | source probability `1/N`; top-source accuracy chance control |
| B1 | geometry/TTC | per-agent minimum distance, active-pair degree and summed positive pair-closing rate from state plus nominal controls |
| B2-Q | own QP burden | rank agents by `C_i` |
| B2-E | Euclidean own correction | rank by `||u_safe_executed-u_nominal||_2` |
| B3 | global intervention | total burden, active-pair count, maximum degree and density; same team features for outcome models |
| B4 | executed-action linear control | L2-regularized logistic model over standardized B1--B3 plus nominal, executed and delta action components; regularization grid `{0.01,0.1,1,10}` selected by four-fold grouped CV on fit episodes |
| B5 | Layered multi-engagement | engagement radius `2*SAFETY_RADIUS`; if an agent has more than one engaged neighbor, sum positive closing speed times linear closeness from engagement radius to safety radius; else zero |
| O1 | exact counterfactual source | top source and `S_i` from `R-safe` QP re-solves |

B4 uses no MLP, GNN or sequence model. If a linear observable model closes the attribution gap, a new externality-aware learner is not justified.

## 8. Outcomes and Metrics

### 8.1 Attribution metrics

- source--victim mismatch rate
- source-effect ratio distribution
- top-source accuracy, mean reciprocal rank and one-vs-rest macro AUROC of B0--B5 against O1
- event support, ambiguity rate and source-significant rate
- active-constraint maximum degree and fraction with degree at least two
- `R-safe` versus `R-zero` top-source agreement

All intervals use 2,000 episode-cluster bootstrap replicates with frozen seed `240901`.

### 8.2 Common task metrics

- success
- normalized completion time; failure is assigned `1.0`
- total and per-agent path length
- minimum separation
- collision/boundary violation
- total and per-agent correction burden
- intervention-active macro-step fraction

Hard safety is a constraint. Efficiency improvement cannot compensate for collision increase.

### 8.3 Future-stall targets

S1 task work:

`W_t = sum_i max(||goal_i-position_i||_2-goal_radius,0)`.

S1 five-macro-step stall:

`Y_stall=1` when unfinished and `(W_t-W_{t+5}) <= 0.01*max(W_0,1e-6)`.

S2 task work:

`W_t = zone1_load + zone2_load + sum_i capacity_i * payload_i`.

S2 ten-macro-step stall:

`Y_stall=1` when unfinished and `(W_t-W_{t+10}) <= 0`.

Rows without the complete future horizon are excluded and counted. A scenario lacks a usable K3 denominator if either class contains fewer than 100 eligible events or fewer than 10 distinct episodes in fit or test.

### 8.4 Outcome models

Base model `Q_base`:

- L2 logistic regression
- state progress/work, macro-step fraction, `N`, minimum distance, closing rate, active degree, B2-Q, B2-E, C-total and B5
- same regularization grid and fit-only grouped CV as B4

Augmented model `Q_ext`:

- all `Q_base` features
- O1 maximum source score, source-effect ratio, source concentration, mismatch and positive off-diagonal mass

Primary metrics are held-out AUROC and Brier score. Episode ID is the grouping unit for CV, bootstrap and permutation.

## 9. Sequential Gates

No later gate is computed after an earlier kill.

### K0 Artifact and Instrumentation

Pass only if all hold:

1. repository commits, submodule commit and source hashes match Section 3;
2. Docker dependency lock is materialized and explicitly includes a compatible `jaxopt` absent from upstream `pyproject.toml`;
3. original barrier/unit smoke passes inside Docker;
4. instrumented base action matches original source action within `1e-7` in the same dtype for 100 hashed development states;
5. float32 executed versus float64 diagnostic parity is `<=1e-4` for at least 99.9% of valid development microsteps and no scenario/count cell falls below 99%;
6. base and counterfactual QP valid rate is at least 99.9%, with no NaN/Inf;
7. repeat-run rows match within absolute `1e-8` on CPU;
8. agent permutation equivariance is at least 99% for safe action, burden and transformed top-source identity over 100 non-ambiguous hashed rows;
9. an independent CVXPY/OSQP re-solve agrees with JAXopt safe controls within `1e-4` and objective within relative `1e-3` on 100 hashed rows.

Any failure returns `kill_artifact_or_instrumentation`. K1--K3 main seeds remain unread.

### K1 Nontrivial Source--Victim Mechanism

Evaluate S1 and S2 separately, pooling only `N={4,6}` within each scenario after reporting each count.

Pass only if both scenarios satisfy all:

1. at least 200 source-significant, non-ambiguous test events from at least 20/32 test episodes;
2. both `N=4` and `N=6` contribute at least 50 such events;
3. at least 100 events have active-constraint maximum degree `>=2`;
4. source--victim mismatch point estimate is at least `0.25` and its 95% episode-cluster bootstrap lower bound exceeds `0.15`;
5. within degree-`>=2` events, mismatch point estimate is at least `0.30`;
6. `R-safe` versus `R-zero` top-source agreement is at least `0.75`;
7. source/victim ambiguity is at most `0.20`.

Otherwise return `kill_no_stable_source_victim_mechanism`.

### K2 Simple-Control Residual

For each scenario, evaluate B0--B5 against O1 on held-out test events.

Kill if any non-oracle control simultaneously reaches either:

- top-source accuracy `>=0.85`; or
- macro AUROC `>=0.90` and mean reciprocal rank `>=0.90`.

Also kill if the same control reaches top-source accuracy `>=0.75` and macro AUROC `>=0.85` in both scenarios while suffering no more than a `0.03` fit-to-test accuracy drop in either; this captures a stable cross-task simple explanation below the single-scenario ceiling.

Survival requires the residual in both S1 and S2. Outcome: `kill_simple_control_closes_attribution` or pass to K3.

### K3 Outcome Relevance Beyond Controls

For each scenario separately:

1. stall target must satisfy the support rule in Section 8.3;
2. compare `Q_ext` with `Q_base` on held-out episodes;
3. require `Delta AUROC = AUROC_ext-AUROC_base >=0.05`;
4. require `Delta Brier = Brier_base-Brier_ext >=0.01`;
5. require both episode-cluster bootstrap lower bounds to exceed zero;
6. require a one-sided, 1,000-repeat episode-cluster permutation test with frozen seed `240902` to give `p<0.05` for both metrics.

Both S1 and S2 must pass. Otherwise return `kill_no_incremental_outcome_relevance` or `kill_no_valid_stall_denominator`.

If all K0--K3 pass, outcome is only:

`open_minimal_learning_intervention_contract`.

## 10. Independent Verifier

The verifier consumes immutable tables and manifests, not in-memory producer objects. It must check:

1. source revision and SHA-256 manifest;
2. dependency/image/config hashes;
3. primary-key uniqueness and exact split/seed membership;
4. action shapes, finite values and state/action alignment;
5. original/instrumented action parity;
6. QP primal feasibility and objective/burden recomputation;
7. `R-safe`, `R-zero`, null diagonal and signed `E_ij` equations;
8. one event row is the first eligible microstep per macro step;
9. no O1/counterfactual field enters B0--B5 or `Q_base`;
10. grouped CV/bootstrap/permutation has no episode leakage;
11. agent-permutation equivariance;
12. sequential gate enforcement and non-computation of later gates after kill;
13. expected artifact count and checksum closure.

The producer and verifier must be separate entry points. A verifier that imports producer aggregation functions does not count as independent.

## 11. Docker and Resource Boundary

No execution occurred in N24.

Frozen next-stage constraints:

- all source install/import, JAX/JAXopt/CVXPY execution and tests are Docker-only;
- proposed short image tag: `tasm:n25-jfe-260901`;
- source snapshots mounted read-only;
- historical outputs archived under `/home/yoohyun/research2_retired_20260901/local_dataset/JFE_n25/`;
- historical build/run logs archived under `/home/yoohyun/research2_retired_20260901/logs/`;
- N25 runs K0 development seeds only on CPU first;
- GPU is optional only after K0 CPU parity passes and must use explicit `--gpus` plus recorded device;
- no free-VRAM/utilization waiting condition is imposed;
- no Robotarium submission, remote hardware, Layered Safe MARL training or checkpoint inference is allowed in K0;
- exact Dockerfile, dependency lock, image digest, build/run command, mounts, seed list, output path and verification command must be recorded before K0 result interpretation.

## 12. Failure Interpretation

| Failure | What it teaches | Forbidden rescue |
| --- | --- | --- |
| K0 | upstream artifact/instrumentation cannot support the oracle reliably | host execution, tolerance relaxation after rows |
| K1 support | filter interaction is too rare or attribution is ambiguous/reference-dependent | denser hand-picked geometry after outcome |
| K1 effect | victim correction usually identifies source, or mismatch is not multi-agent-stable | rename generic intervention as externality |
| K2 | geometry, own correction, executed action or Layered signal explains source | add nonlinear/GNN attribution module |
| K3 denominator | public tasks do not yield a balanced stall target | redefine success/stall after outcome |
| K3 effect | exact externality has no incremental behavioral consequence | train a reward with O1 anyway |

## 13. Final State and Next Action

- N24 source/code audit: complete.
- Runtime, Docker build, main seeds, outcomes: not executed/read.
- Active candidate/hypothesis/method/paper: none.
- Contract status: frozen as `jfe-n24-v1`.
- Next action: N25 Docker-only K0 preflight over development seeds `{0,1,2,3}`. Stop at K0 and write a result report; main seeds remain unopened even if K0 passes.
