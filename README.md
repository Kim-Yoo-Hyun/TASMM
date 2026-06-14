# Semantic Mapping Research Workspace

업데이트: 2026-06-14

## Overview

이 repository는 semantic mapping을 중심으로 dynamic object search/navigation에서 stale semantic memory를 어떻게 신뢰, 갱신, 재관측, 실행 결정에 연결할지 연구한다. 현재 목표는 Direction B `Task-Aware Dynamic Semantic Mapping for Open-Vocabulary Search and Navigation`이다. 핵심 실험은 `HM3D ObjectNav` + `Habitat`, real RGB-D/open-vocabulary proposal, external map baseline, path/search-cost metric을 연결해 paper-facing evidence를 만드는 것이다. 논문 목표는 AI, ML, CV, Robotics top-tier journal/conference 수준의 novelty, benchmark rigor, reproducibility를 만족하는 것이다.

## Core Question

Dynamic object search에서 실패는 stale memory 하나가 틀렸기 때문만이 아니라, current evidence confidence, stale-memory trust, source coverage, path feasibility가 서로 충돌하기 때문에 발생한다. 따라서 semantic map은 object memory를 저장하는 데서 끝나지 않고, re-observation/search decision과 search/navigation cost를 함께 노출해야 한다.

## Repository Structure

| Path | Role |
| --- | --- |
| [AGENTS.md](AGENTS.md) | repo-level 작업 규칙, novelty 기준, Docker/reproducibility 원칙 |
| [TODO.md](TODO.md) | 현재 Now/Next/Completed 작업판 |
| [summary.md](summary.md) | 연구 방향, 배경, 문제 정의, hypothesis, framework, experiment plan 요약 |
| [docs/](docs/) | workflow, paper framing, reproducibility 기준 |
| [literature/](literature/) | 문헌 조사와 cross-paper synthesis |
| [src/](src/) | 재사용 가능한 핵심 코드가 승격될 위치 |
| [scripts/](scripts/) | top-level 실행 wrapper |
| [configs/](configs/) | 공유 가능한 경량 config |
| [experiments/](experiments/) | main experiment 구현, report, artifact index |
| [results/](results/) | 가벼운 결과 요약, 표, 로그 요약 |
| [archive/](archive/) | hypothesis-stage workspace, blocked routes, local generated artifact archive |

각 폴더의 `README.md`를 해당 폴더의 local entry point로 사용한다. 루트 README에는 긴 실험 기록을 중복하지 않는다.

## Key Execution

현재 active experiment는 [experiments/E008_real_navigation_benchmark](experiments/E008_real_navigation_benchmark/README.md)이다. 작업 전에는 항상 [TODO.md](TODO.md)의 Now/Next를 확인한다.

최근 검증된 E008 source-pool scale chain:

```bash
bash scripts/run_e008_source_pool_scale.sh
```

동일한 chain을 수동으로 실행하려면:

```bash
python experiments/E008_real_navigation_benchmark/tools/verify_m194_source_pool_scale_render_detector_execution.py --require-ready
python experiments/E008_real_navigation_benchmark/tools/run_m195_source_pool_scale_candidate_navmesh_source_readiness_validation.py
python experiments/E008_real_navigation_benchmark/tools/run_m196_source_pool_scale_candidate_visit_order_path_materialization.py
python experiments/E008_real_navigation_benchmark/tools/run_m197_source_pool_scale_leakage_safe_goal_evaluation_proxy.py
python experiments/E008_real_navigation_benchmark/tools/plan_m198_source_pool_scale_proxy_result_interpretation.py
```

현재 다음 gate는 `E008-M199 source-pool scale failure decomposition and candidate-generation repair decision`이다. 전체 데이터, checkpoint, Docker, 재현 명령은 [docs/reproducibility.md](docs/reproducibility.md)를 따른다.

## Artifact Policy

- `local_dataset/` 아래의 dataset, checkpoint, model cache, generated bridge data는 git에 올리지 않는다.
- `/home/yoohyun/research/local_dataset/Open3DSG_staged`와 `/home/yoohyun/research3/local_dataset/data`는 read-only source로만 사용한다.
- Derived `Open3DSG` 결과는 `local_dataset/Open3DSG_bridge/`에 저장한다.
- Derived E008 navigation 결과는 `local_dataset/HM3D_navigation_bridge/`에 저장한다.
- Active commands may regenerate outputs under `experiments/*/artifacts/`; generated artifacts are ignored by Git.
- Historical generated artifacts moved out of active code live locally under `archive/generated_artifacts/`, which is also ignored by Git.
- Share-facing result summaries live under [results/](results/).
- Long-running download, Docker build/run, preprocessing job은 `tmux`/background로 실행하고 `logs/`에 timestamped log를 남긴다.
- Paper-body experiment는 Docker 기반 실행을 기본으로 한다.

## Navigation

- 현재 작업 우선순위: [TODO.md](TODO.md)
- 연구 요약: [summary.md](summary.md)
- 문서 지도: [docs/index.md](docs/index.md)
- Literature workflow: [docs/literature.md](docs/literature.md)
- Hypothesis workflow: [docs/hypothesis.md](docs/hypothesis.md)
- Experiment workflow: [docs/experiments.md](docs/experiments.md)
- Paper framing / novelty / reviewer defense: [docs/paper.md](docs/paper.md)
- 재현성과 artifact 관리: [docs/reproducibility.md](docs/reproducibility.md)
- Historical hypothesis workspace: [archive/hypothesis/](archive/hypothesis/)
