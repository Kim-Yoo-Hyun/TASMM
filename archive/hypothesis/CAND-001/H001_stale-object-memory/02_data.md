# Data

## 사실

- Local dataset root: `local_dataset/`.
- `3RScan/files/3RScan.json`에서 reference-rescan metadata pairs 1004개를 스캔했다.
- Local reference semantic payload가 있는 pair는 84개다.
- 현재 local-ready semantic pairs는 12개다.
- Current observations are annotation-level `semseg.v2.json`.
- Current relation evidence is `3DSSG/relationships.json`.
- Complete local reference-rescan RGB-D pair는 아직 확보하지 않았다.

## 데이터 경로

- Initial route: `metadata_guided_synthetic_stale_probe`.
- Pair validation route: reference-rescan semantic OBB geometry and scene alignment.
- Multi-pair route: locally staged rescans with `labels.instances.annotated.v2.ply`, `semseg.v2.json`, `mesh.refined.0.010000.segs.v2.json`.

## 주요 Pair

| Pair | 역할 | 결과 |
| --- | --- | --- |
| `ddc73797` -> `c7895f07` | 초기 semantic pair | scene-aligned moved rows >= 1.0 m: 0 / 11 |
| `569d8f0d` -> `569d8f0f` | high-displacement smoke | 5 row-valid rigid rows, 3 significant moved rows |
| `280d8ebb` -> `4731976c` | hard `pillow` case | target rank 2 |
| `0cac7578` -> `ddc73795` | hard `pillow` case | target rank 3 |
| `280d8ebb` -> `ea318260` | strict threshold crossing | 12-pair strict pass로 확장 |

## 논문 주장

지원되는 주장:

- `3RScan` / `3DSSG` metadata와 semantic geometry로 stale-memory hypothesis-stage probe를 구성할 수 있다.
- 12개 reference-rescan semantic pair까지 local artifact를 확장했다.

아직 지원되지 않는 주장:

- RGB-D replay robustness.
- Open-vocabulary proposal robustness.
- Full benchmark coverage.

## 에이전트 추론

현재 데이터는 semantic map-update mechanism을 분리해서 보기에는 충분하지만, robot deployment claim에는 부족하다. 다음 단계는 perception noise를 controlled perturbation으로 먼저 넣고, 이후 실제 RGB-D / open-vocabulary proposal로 확장하는 편이 좋다.

## 사용자 판단 필요

Perception claim을 바로 real RGB-D pipeline으로 갈지, 먼저 `semseg.v2.json`에 dropout / false positive / pose jitter를 넣는 controlled noise gate로 갈지 결정해야 한다.
