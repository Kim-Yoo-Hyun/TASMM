# CAND-002: Common-Ground Semantic Mapping Across Human And Robot Viewpoints

## Problem

사람은 human-height viewpoint와 prior knowledge로 object를 설명하지만, robot은 낮은 camera height, occlusion, partial observation에 기반해 map을 만든다.

## Existing Limitation

사실:

- OpenMap과 LangMap은 instruction/goal grounding을 다루지만 human-view와 robot-view mismatch 자체를 핵심 benchmark로 삼지는 않는다.
- HOV-SG와 ConceptGraphs는 hierarchy와 relation을 저장하지만 viewpoint provenance를 중심 문제로 두지는 않는다.

에이전트 추론:

- common-ground map은 human-friendly robot intelligence와 잘 맞지만, benchmark 설계 부담이 크다.

## Why Semantic Mapping

semantic map이 visibility, viewpoint provenance, relation evidence, uncertainty를 저장해야 "사람이 말한 object"와 "robot이 본 object"를 맞출 수 있다.

## Evaluation Plan

Dataset / benchmark 후보:

- HM3D / Replica human-height vs robot-height rendered views
- Matterport3D instruction grounding
- custom paired human-robot RGB-D replay

Metrics:

- viewpoint-shift grounding accuracy
- relation grounding accuracy
- clarification need rate
- correction success rate

## What Failure Teaches

- 효과가 없으면 viewpoint mismatch보다 VLM feature quality나 relation parser가 bottleneck일 수 있다.
- hidden object에서만 효과가 있으면 occlusion-aware memory로 좁혀야 한다.

## Next Action

HM3D/Replica에서 human-height와 robot-height camera split을 쉽게 만들 수 있는지 확인한다.
