# CAND-003: Functional Semantic Memory For Household Assistance

## Problem

사람의 household instruction은 object category와 location만으로는 부족하다. robot은 "어디에 놓을 수 있는가", "무엇을 열 수 있는가", "무엇을 지지할 수 있는가" 같은 functional relation을 알아야 한다.

## Existing Limitation

사실:

- Open-Vocabulary Functional 3D Scene Graphs는 functional relation prediction을 별도 task로 제안한다.
- Open-Vocabulary Mobile Manipulation with 3D Semantic Maps는 semantic maps를 manipulation success와 연결한다.

에이전트 추론:

- functional mapping은 human-friendly angle이 강하지만, annotation과 manipulation evaluation 비용이 크다.

## Why Semantic Mapping

functional relation은 planner가 object affordance를 사용할 수 있도록 map에 저장되어야 한다. 단일 frame prediction으로는 household task memory가 되기 어렵다.

## Evaluation Plan

Dataset / benchmark 후보:

- FunGraph3D
- SceneFun3D
- BEHAVIOR-style household tasks
- custom tabletop/mobile manipulation replay

Metrics:

- functional relation accuracy
- task completion
- implausible placement rate
- unsafe assumption rate

## What Failure Teaches

- function prediction이 안 되면 visual-only VLM semantics가 household affordance를 충분히 담지 못한다는 뜻이다.
- relation accuracy는 높은데 task success가 낮으면 planner/action interface가 bottleneck이다.

## Next Action

FunGraph3D와 SceneFun3D access, license, annotation format을 확인한다.
