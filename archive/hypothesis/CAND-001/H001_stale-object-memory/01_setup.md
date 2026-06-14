# Setup

## 사실

- H001은 `Stale Object Memory`에서 출발했지만, 현재 연구 방향은 `Task-Conditioned Stale Semantic Memory Update`로 좁혀졌다.
- Local route는 `3RScan`, `3DSSG`, `3DSSG_subset`를 사용한다.
- Hypothesis 단계는 full reproduction이나 full dataset 검증이 아니다.
- 현재 증거는 annotation-level `semseg.v2.json`와 `3DSSG/relationships.json`를 사용한다.
- 현재 gate는 navigation, RGB-D perception, open-vocabulary perception, exact current target pose for ranking, persistent cross-scan object-id anchor를 사용하지 않는다.

## 논문 주장

지원되는 주장:

- Semantic map은 object memory를 `trusted`, `stale`, `needs_reobservation`, `updated`, `absent`, `topk_current_candidates` 같은 상태로 관리할 수 있다.
- H001은 task-relevant object memory의 trust / stale / uncertainty를 다루는 semantic mapping 문제다.

아직 지원되지 않는 주장:

- Final exact moved-object recovery.
- Navigation `SR` / `SPL` improvement.
- RGB-D 또는 open-vocabulary perception robustness.
- Rich human-intention understanding.
- Deployable search policy.

## 에이전트 추론

H001의 top-tier 가능성은 단순 stale detection이 아니라, dynamic object search/navigation에서 map state가 robot behavior metric을 바꾸고, controlled perception noise 아래에서도 유지되며, task context에 따라 trust/budget을 조절하는지에 달려 있다.

Human task context는 main language-understanding claim이 아니라 memory trust와 re-observation strictness를 바꾸는 condition으로 쓰는 편이 안전하다.

## 사용자 판단 필요

다음 판단은 H001을 `docs/experiments.md` planning으로 승격할지 여부다. 승격하더라도 real navigation, real RGB-D perception, open-vocabulary perception claim은 아직 올리지 않는다.
