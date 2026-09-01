# N22 Artifact-to-Failure 3D Vision × Robotics Direction Search

> Historical route report. 이 문서의 당시 next action은 [N28](admission-bottleneck-synthesis-search-stop-n28-2026-09.md)이 대체하며, archived source/artifact를 자동 복원하지 않는다.

- Date: 2026-09-01 KST
- Search order: released measurement structure → executable denominator → simple-baseline residual → exact prior → two-domain path → method necessity
- Scope: 2024--2026 public robotics datasets, official code/evaluators, `/home/yoohyun/PaperReview` discovery registry
- Runtime: one bounded CPU Docker control on public `RH20T cfg3` low-dimensional data; no RGB/audio/depth/model/GPU runtime
- Outcome: `no_strict_pass_3d_robotics_artifact_search`
- Active candidate / hypothesis / method / paper claim: none

## Executive Verdict

에이전트 판단:

> 이번 artifact-first search의 strict pass는 **0개**다. `AgiBotWorld2026 RichInteraction`은 RGB-D와 wrench를 함께 제공하지만 감사한 episode에는 failure/contact/outcome label이 없어 denominator가 성립하지 않았다. `RH20T`는 public rating, calibrated multi-view, force/torque, pose를 함께 제공해 유일하게 실행 가능한 lead가 되었지만, task-conditioned **trajectory-only linear control**이 scene-grouped OOF에서 `AUROC=0.836`, `balanced accuracy=0.758`을 기록했다. Precommitted task-macro closure threshold에는 못 미쳐 결과는 `inconclusive_lowdim_residual`이지만, “simple baseline으로 닫히지 않는다”는 후보 진입 조건도 통과하지 못했다.

따라서 `Contact-Grounded 3D Reward under Visual Aliasing`을 candidate로 만들지 않는다. Broad reward/failure modeling은 `Robometer`, `RoboReward`, `Guardian`이, RH20T vision–force representation은 `Kepler-Encoder`, `MSDP`, adaptive vision–torque fusion이 이미 강하게 점유한다. 남는 exact 3D-contact reward residue는 아직 strong video baseline 대비 residual과 second-domain denominator가 없다.

## 1. Fixed Admission Criteria

사용자 승인으로 다음 여섯 조건을 완화하지 않았다.

| Gate | Requirement |
| --- | --- |
| G1 | 공개되고 실제 실행 가능한 benchmark/denominator |
| G2 | 2024--2026 direct prior가 문제와 원리를 이미 점유하지 않음 |
| G3 | simple baseline으로 닫히지 않는 failure mechanism |
| G4 | 1주 내 decisive kill test |
| G5 | 두 dataset/domain으로 확장 가능한 경로 |
| G6 | failure diagnosis가 특정 method principle을 필연적으로 요구 |

이번 search에서는 topic 이름을 먼저 만들지 않았다. 공개 artifact가 가진 실제 row/schema를 읽고, 그 측정값이 만들 수 있는 failure와 control을 먼저 정의했다.

## 2. Artifact Screen

### 2.1 Summary

| Artifact | Released measurements | Executable outcome denominator | Immediate simple-control pressure | Decision |
| --- | --- | --- | --- | --- |
| `AgiBotWorld2026 RichInteraction` | multi-view RGB, head depth, pose/action, 12-D end wrench, extrinsics | 감사한 single episode에 error/contact/success/outcome label 없음 | endpoint·wrench threshold는 가능하지만 target label이 없음 | `reject_no_row_denominator` |
| `RH20T` | multi-view RGB-D, calibration, pose/action, force/torque, 0--9 task rating | rating 0/1 failure, 2--9 quality; public API와 community LeRobot row | task prior, trajectory, force aggregate를 즉시 실행 가능 | **bounded control 실행** |
| `DROID` | multi-view robot demonstrations, calibration/depth route, actions | expert-demo 중심이며 matched success/failure row를 공식 schema에서 확인하지 못함 | calibration/action consistency로 문제를 바꾸면 direct-prior pressure가 큼 | `reject_no_failure_denominator` |
| `BEHAVIOR-1K` | simulator RGB-D/instance state, BDDL predicate progress, exact replay | predicate/task success는 강함; released replay의 joint effort는 물리를 step하지 않아 유효 F/T가 아님 | predicate progress, object-distance, terminal rule이 강한 control | `reject_prior_or_simple_progress` |
| `RoboMIND / RoboMIND 2.0` | failures, multi-embodiment, 3D/tactile/sim-real data | failure rows는 있으나 dataset papers가 failure/tactile/sim-real use를 이미 전면 평가 | embodiment/task identity와 released baselines가 강함 | `reject_direct_ownership` |

### 2.2 AgiBotWorld2026 bounded sample audit

사실:

- official public dataset: [`AgiBotWorld2026`](https://huggingface.co/datasets/agibot-world/AgiBotWorld2026)
- pinned revision: `1b6c876b23f91190f7174a8fef0f1e484f794dd2`
- audited file: `RichInteraction/CommercialSpaces/task_4439/458713_458713.tar.gz`
- archived local file: `/home/yoohyun/research2_retired_20260901/local_dataset/N22_agibot_sample/task_4439_ep458713.tar.gz`
- size: `325,891,979` bytes
- SHA-256: `d2de2288979bfaf8ebf0cdfae4afc08e3031d14a8594b7930d11a67d2bc34cfe`
- one episode, 2,089 frames, 30 fps, `g2a`
- seven camera streams including `head_depth`; state 169-D, action 44-D, end wrench 12-D
- task text는 generic random interaction이고 `key_frame`은 비어 있다.
- audited metadata/parquet에는 missed grasp, collision, drop, contact onset, object identity, restorable state 또는 validated success/failure field가 없다.

논문/공식 발표 주장:

- [AgiBot official release announcement](https://www.agibot.com/article/231/detail/72.html)는 RichInteraction이 missed grasps, collisions, drops, unstable contacts, liquid splashes를 포함한다고 설명한다.
- [`A2World`](https://github.com/LogosRoboticsGroup/A2World)는 AgiBot을 포함한 action-conditioned world modeling과 transferable dynamics prior를 이미 전개한다.

에이전트 추론:

- 현상 자체가 video에 나타날 수 있다는 공식 설명과 episode-level evaluator가 있다는 것은 다른 주장이다.
- 직접 label을 새로 붙이면 “공개 denominator”가 아니라 우리 annotation benchmark가 된다. 현재 일정과 기준에서 이를 candidate의 기반으로 사용하지 않는다.
- 한 episode 감사로 전체 RichInteraction release에 label이 절대 없다고 주장하지 않는다. 다만 실제 내려받은 bounded route에는 executable label이 없었고, official card에서 해당 task directory의 row-level evaluator를 찾지 못했다.

### 2.3 RH20T source and row audit

사실:

- official project: [`RH20T`](https://rh20t.github.io/)
- official API source: [`rh20t/rh20t_api`](https://github.com/rh20t/rh20t_api), audited commit `aa3124434729ed622109a29b2cbb9f3bbb1c5eeb`
- API는 timestamp-aligned RGB-D pairs, camera/base-frame TCP와 zeroed force/torque를 제공한다.
- official metadata contract는 rating `0=robot failure`, `1=task failure`, `2--9=completion quality`로 정의한다.
- public unofficial port: [`robot-lev/rh20t_cfg3`](https://huggingface.co/datasets/robot-lev/rh20t_cfg3), pinned revision `343835bee9a3a4045262c9315dcad30088d07a76`
- port는 RGB-only video sidecar와 함께 pose/action, force, torque, robot-FT, rating을 LeRobot v3 row로 제공한다. 이번 probe는 video/audio를 받지 않았다.
- 798 episodes 중 rating `-1` 4개를 제외한 794개가 valid이며 failure 110, non-failure 684다.
- 41개 task가 같은 task 안에서 failure와 non-failure를 모두 가진다.

에이전트 추론:

- 이것은 이번 screen에서 유일하게 “public measurement + same-task positive/negative + bounded materialization”을 동시에 만족했다.
- 반대로 original accurate-depth package는 config 단위로 매우 크고, port는 depth를 포함하지 않는다. 따라서 이번 gate가 3D input의 우월성을 직접 측정한 것은 아니다. 먼저 low-dimensional control이 label을 닫는지만 falsify했다.

## 3. Artifact-Derived Pre-Candidate Question

후보로 승격하지 않은 provisional question:

> 2D video-language reward models는 contact-rich manipulation에서 시각적으로 유사하지만 3D contact/interaction quality가 다른 near-miss를 체계적으로 mis-rank하며, 이 residual은 task identity, trajectory statistics, force thresholds로 닫히지 않는가?

기존 limitation:

- Video reward models는 성공, progress, trajectory preference를 대규모로 학습하지만 contact state, occluded geometry, force를 직접 관측하지 않는다.

왜 3D Vision × Robotics 문제인가:

- Valid mechanism이 있다면 error는 generic image classification이 아니라 task-conditioned 3D relation/contact state와 robot execution quality 사이의 non-identifiability여야 한다.
- 필요한 method도 단순 RGB-D concatenation이 아니라 temporal 3D contact state를 reward ordering에 연결해야 한다.

실패 시 배우는 것:

- Task/trajectory/force aggregate가 rating을 충분히 설명하면 3D reward representation은 필연적이지 않다.
- Strong video reward가 residual을 닫으면 problem novelty가 없다.
- Depth/force를 넣어도 개선이 없으면 contact-grounded representation claim이 성립하지 않는다.

## 4. Frozen Simple-Control Probe

Contract와 code: `/home/yoohyun/research2_retired_20260901/hypothesis/probes/contact-grounded-3d-reward/README.md`

### 4.1 Protocol

사실:

- label: failure `rating in {0,1}`, non-failure `rating in {2,...,9}`
- split: five-fold `StratifiedGroupKFold`, seed `260901`
- group: `(task_id, scene_id)`; 같은 task-scene group은 train/test에 동시에 나오지 않는다.
- 모든 learned control은 task identity one-hot을 포함하되 train fold에서만 fit했다.
- `trajectory_linear`: duration/frame count, end-effector displacement/path/range, gripper/action statistics
- `force_linear`: force/torque/robot-FT distribution과 temporal-difference statistics
- `combined_linear`, class-balanced `combined_rf`
- RGB, depth, point cloud, audio, pretrained encoder는 사용하지 않았다.

### 4.2 Result

| Control | AUROC ↑ | Failure AUPRC ↑ | Balanced Acc. ↑ | Task-macro Balanced Acc. ↑ |
| --- | ---: | ---: | ---: | ---: |
| `task_prior` | 0.672 | 0.261 | 0.617 | 0.388 |
| `trajectory_linear` | **0.836** | **0.576** | **0.758** | **0.710** |
| `force_linear` | 0.656 | 0.293 | 0.627 | 0.557 |
| `combined_linear` | 0.756 | 0.467 | 0.706 | 0.679 |
| `combined_rf` | 0.793 | 0.510 | 0.618 | 0.618 |

Gate:

- G0 artifact validity: pass.
- G1 simple closure: false. Precommitted rule는 `task_prior` 또는 `combined_rf`가 `AUROC >=0.80`과 task-macro `>=0.75`를 동시에 만족해야 했다.
- G2 low-dimensional residual: false. 모든 control이 weak해야 하지만 `trajectory_linear`가 `AUROC=0.836`, task-macro `0.710`이었다.
- Outcome: `inconclusive_lowdim_residual`.

에이전트 추론:

- 이 결과를 “force가 쓸모없다”로 일반화하지 않는다. Frozen aggregate와 split에서 force-only가 weak했고, 120개 force feature를 단순히 더한 control은 trajectory-only보다 나빴다는 것만 지지한다.
- 그러나 reviewer 관점에서 더 중요한 사실은 **새 3D/contact method 없이 trajectory statistics가 이미 강하다**는 점이다. Precommitted kill threshold를 완전히 넘지는 않았어도, 연구 후보 조건 G3인 “simple baseline으로 닫히지 않음”을 입증하지 못했다.
- 따라서 threshold를 낮춰 kill로 바꾸거나, 반대로 RGB-D subset을 선택해 claim을 살리지 않는다. 판정은 inconclusive이며 candidate는 열지 않는다.

## 5. Exact-Prior Pressure

논문 주장:

- [`Robometer`](https://arxiv.org/abs/2603.02115), RSS 2026, 는 frame-level progress/success와 trajectory comparison을 함께 학습해 mixed-expertise/failure trajectories를 general-purpose reward로 사용한다. [Official project/code](https://robometer.github.io/)
- [`RoboReward`](https://arxiv.org/abs/2601.00675)는 success-heavy robot data에 calibrated negative/near-miss와 temporal clipping을 추가해 reward benchmark/model을 만든다.
- [`Guardian`](https://arxiv.org/abs/2512.01946)은 simulated/real failure synthesis와 multi-view VLM failure detection을 제공한다.
- [`Kepler-Encoder-v0.1`](https://arxiv.org/abs/2607.13522)은 RH20T에서 vision, proprioception, force/torque를 shared latent로 fuse한다. Vision-only raw feature의 force recovery가 거의 없고 cross-modal latent가 더 낫다고 보고하지만, single-timestep이며 contact dynamics와 action-conditioned causality는 future work로 남긴다.
- [`MSDP`](https://arxiv.org/abs/2511.14427)는 vision, force, proprioception의 masked cross-sensor/dynamics pretraining을 contact-rich policy learning에 사용한다.
- [`Learning When to See and When to Feel`](https://arxiv.org/abs/2604.01414)은 contact phase에서 vision–torque를 adaptive하게 gate하는 diffusion-policy fusion을 비교한다.
- [`A2World`](https://github.com/LogosRoboticsGroup/A2World)는 action-conditioned multi-view world modeling을 AgiBot 등 여러 manipulation source로 확장한다.

에이전트 추론:

- “failure data로 reward model을 개선한다”, “near-miss를 생성한다”, “vision이 contact를 못 보므로 force를 fuse한다”, “action-conditioned world model로 physics를 배운다”는 contribution은 모두 사용할 수 없다.
- Search에서 exact phrase의 `3D point-cloud contact reward model`을 찾지 못했지만, absence proof는 아니다. 더 중요하게는 현재 residual이 이 exact method를 요구하지 않는다.
- `trajectory_linear`가 강한 상태에서 3D encoder를 먼저 설계하면 failure diagnosis에서 method가 나온 것이 아니라 fashionable modalities를 결합한 것이 된다.

## 6. Two-Domain Route

검토한 route:

1. `RH20T` real contact-rich rating + RGB-D/F/T
2. `BEHAVIOR-1K` simulation RGB-D/instance/BDDL predicate progress
3. `AgiBotWorld2026 RichInteraction` real humanoid RGB-D/wrench

사실:

- [`BEHAVIOR-1K dataset/evaluation`](https://behavior.stanford.edu/challenge/archive/2025/dataset.html)는 task predicate와 simulation replay를 제공하지만 RH20T와 같은 operator quality rating/F/T contract가 아니며, released joint effort는 valid physics-step measurement가 아니다.
- `AgiBotWorld2026` audited sample은 sensors는 풍부하지만 row-level outcome이 없다.

에이전트 추론:

- “두 dataset에서 RGB-D가 있다”는 것만으로 G5를 통과하지 않는다. 같은 failure relation과 metric을 정의해야 한다.
- 현재는 RH20T의 ordinal task rating, BEHAVIOR의 symbolic predicate, AgiBot의 unlabeled interaction을 하나의 denominator로 정당하게 연결할 수 없다.
- 따라서 two-domain path는 conceptual일 뿐 `credible executable path`가 아니다.

## 7. Six-Gate Decision

| Gate | Best route | Result | Reason |
| --- | --- | --- | --- |
| G1 public executable denominator | RH20T cfg3 | pass | 794 valid, 110 failures, 41 mixed-label tasks |
| G2 unoccupied 2024--2026 problem/principle | exact 3D-contact reward only | conditional/fail | broad reward, failure, fusion은 직접 점유; exact residue도 absence proof 없음 |
| G3 not closed by simple baseline | RH20T low-dimensional probe | **fail** | trajectory-only AUROC 0.836; precommitted result inconclusive, residual pass 아님 |
| G4 one-week kill | public LeRobot packet | pass | 75 MB row packet, CPU Docker로 같은 날 실행 |
| G5 two-domain route | BEHAVIOR/AgiBot | **fail** | label/metric contract 불일치 또는 outcome 부재 |
| G6 failure forces method form | temporal 3D-contact reward | **fail** | trajectory control이 강하고 RGB-vs-3D residual 미측정 |

Sequential outcome: `no_strict_pass_3d_robotics_artifact_search`.

## 8. Reviewer-Level Judgment

에이전트 판단:

- 매력도: contact-aware reward는 시의성은 높지만 현재 evidence로는 “2026 reward model + RH20T + depth/force” 조합에 가깝다.
- novelty: broad problem은 낮다. Exact 3D/contact ordering mechanism이 독립 residual로 증명될 때만 중간 이상이 될 수 있다.
- reasonableness: public data와 one-week control은 좋았지만, second domain과 label alignment가 약하다.
- top-tier readiness: candidate 이전 단계에서 탈락이다. Method, main table, paper claim을 만들 근거가 없다.
- 기준의 난이도: 기준이 과도해서가 아니라, 이 기준이 **풍부한 sensor를 가진 dataset을 새로운 research question으로 오인하는 것**을 막았다.

## 9. Reproducibility

### Input

- `/home/yoohyun/research2_retired_20260901/local_dataset/N22_rh20t_cfg3/data.parquet`
  - bytes: `78,048,495`
  - SHA-256: `6a50df519c0bf4daac9e5526ee8fe44681c573652b48e583c0aa4ef9a7bc72bb`
- `/home/yoohyun/research2_retired_20260901/local_dataset/N22_rh20t_cfg3/rh20t_episodes.json`
  - bytes: `393,843`
  - SHA-256: `c4df9da7c034bee10696b185df30aab4836b4d759bd9bf0ea1294971cc147133`

### Docker

- Dockerfile: `/home/yoohyun/research2_retired_20260901/hypothesis/probes/contact-grounded-3d-reward/docker/Dockerfile`
- image tag: `tasm:n22`
- image ID / local repo digest: `sha256:3eea4e1f0b2f218246c44d7dc340a3ca7e2925987fa6a18de5129595cf1480ef`
- CPU only; GPU not requested
- exact commands: `/home/yoohyun/research2_retired_20260901/hypothesis/probes/contact-grounded-3d-reward/README.md`
- log: `/home/yoohyun/research2_retired_20260901/logs/20260901_n22_lowdim_final.log`

### Output

- Metrics: `/home/yoohyun/research2_retired_20260901/hypothesis/probes/contact-grounded-3d-reward/artifacts/metrics.json`, SHA-256 `5746c8be22a6482d4df198d316bf0259df7084df409280ac23ab969eec0d3291`
- OOF predictions: `/home/yoohyun/research2_retired_20260901/hypothesis/probes/contact-grounded-3d-reward/artifacts/oof_predictions.csv`, SHA-256 `0c2a5267c5bff156e17dd0d192a4a482fa51ff3fa52f860984896db19dc403e7`
- Episode features: `/home/yoohyun/research2_retired_20260901/hypothesis/probes/contact-grounded-3d-reward/artifacts/episode_features.csv`, SHA-256 `1c7598396a2a9a239c988ca09ee246a04ad97ba20490e492df893152f279a8d7`
- Verification: `/home/yoohyun/research2_retired_20260901/hypothesis/probes/contact-grounded-3d-reward/artifacts/verification.json`, independent checks 9/9 pass
- Two repeated `n_jobs=1` runs produced byte-identical `metrics.json` and `oof_predictions.csv`.

## 10. Re-entry Requirement

이 family는 다음 조건이 모두 생길 때만 다시 연다.

1. Public RGB-D/point-cloud + contact/outcome row가 같은 episode에 있고 task-level negative support가 충분하다.
2. Task prior, duration/path/action, force threshold, frozen visual reward model을 같은 split에서 이긴 residual이 먼저 확인된다.
3. Error가 occluded 3D contact relation에 집중되고, temporal history나 simple geometric relation alone으로 닫히지 않는다.
4. Independent second dataset에서 같은 ordering/success metric을 정의할 수 있다.
5. `Robometer`, `RoboReward`, `Kepler`, `MSDP`, adaptive fusion 위에 남는 exact method principle이 있다.

그 전에는 candidate ID, hypothesis, RGB-D download, reward-model reproduction, GPU run, method implementation, paper workspace를 열지 않는다.
