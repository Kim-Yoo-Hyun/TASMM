# Paper

Status: Deferred until paper writing starts.

이 문서는 이전 `literature/paper_protocol.md`를 옮긴 초안이다. 실제 논문 작성 단계가 시작되면 target venue, claim-evidence ledger, figure/table plan에 맞춰 다시 작성한다.

## Goal

top-tier paper를 빨리 쓰는 것이 아니라, 실험이 논문 문장을 강제로 정직하게 만들도록 한다. 이 문서는 semantic mapping 연구를 NeurIPS, CVPR, ICCV, ECCV, CoRL, ICRA, RA-L 같은 venue에 맞게 발전시키기 위한 작성 프로토콜이다.

## Claim-Evidence Ledger

논문 초안보다 먼저 이 표를 채운다.

| Claim | Evidence | Figure/Table | Missing risk | Status |
| --- | --- | --- | --- | --- |
| Our map improves language grounding in partially observed scenes. | TBD | TBD | no real-world result yet | open |
| Object-level temporal memory reduces stale semantic errors. | TBD | TBD | dynamic benchmark not fixed | open |
| The method is efficient enough for online robot use. | TBD | TBD | compute/hardware not logged | open |

Rule:

- claim이 evidence 없이 있으면 abstract에 넣지 않는다.
- evidence가 있지만 baseline이 약하면 contribution으로 쓰지 않는다.
- qualitative demo는 quantitative table을 보조할 때만 main claim으로 쓴다.

## Paper Shape

### Abstract

Four sentences:

1. problem and why current semantic maps are insufficient
2. method idea in one concrete sentence
3. key experimental setting
4. strongest quantitative and real-world result

### Introduction

Use this order:

1. Human-facing robot tasks require maps that understand language, intent, and spatial state.
2. Existing semantic maps are strong but usually fail under ambiguity, dynamic changes, embodiment/viewpoint gap, or task-specific intent.
3. State the technical gap, not just an application gap.
4. State the method in one paragraph.
5. State contributions as testable claims.

### Method

Must expose the contract between modules:

- observation to map update
- language/intention to query representation
- semantic feature fusion
- object/relation/temporal memory
- grounding or planner interface
- uncertainty and failure handling

### Experiments

Every experiment should answer one reviewer question.

| Reviewer question | Experiment |
| --- | --- |
| Does the map improve over simpler VLM retrieval? | 2D retrieval vs 3D map vs ours |
| Does object memory matter? | no-instance and no-temporal ablation |
| Does it work online? | latency, memory, FPS, query time |
| Does it handle natural language variation? | synonym/paraphrase/ambiguous query split |
| Does it transfer outside simulation? | replay log or real robot episodes |
| What breaks? | failure taxonomy and limitations |

### Limitations

Write limitations before submission week. Good limitations are specific.

- Fails when object is never observed and common-sense prior is wrong.
- Requires camera pose quality above a stated threshold.
- Open-vocabulary labels inherit VLM bias and may be unreliable for rare or culturally specific objects.
- Dynamic object update assumes at least one re-observation after movement.
- Human data or preference memory requires privacy and consent handling.

## Venue-Aware Notes

Always verify the exact current call for papers before submission; requirements change by year.

- NeurIPS: include the official paper checklist. The checklist is designed around reproducibility, transparency, ethics, and societal impact.
- CVPR/ICCV/ECCV style venues: expect strict anonymization, page limits, supplementary rules, asset attribution, and strong pressure toward code/data release. CVPR 2026 made compute reporting procedural for all submissions.
- CoRL: robotics + learning fit is strong if the method is evaluated on embodied tasks. CoRL 2026 requires a limitations section in the main paper and strongly encourages reproducibility details.
- ICRA/RA-L/IEEE: robotics systems value matters. Provide method detail, data/code availability, video evidence when appropriate, and real-robot or realistic deployment discussion.
- Dual submission: do not submit substantially similar work to multiple archival venues at the same time unless the venue policy explicitly allows it.
- AI writing tools: check the target venue policy. Some IEEE/RAS instructions restrict AI-generated manuscript text and references, so use AI assistance only in a way that remains compliant.

## Reproducibility Checklist

Before a draft is considered serious:

- exact dataset version and split are recorded
- preprocessing is described
- train/eval seeds are fixed and logged
- all hyperparameters are in config
- all baselines are implemented or clearly sourced
- exact commands reproduce main tables
- pretrained weights or checkpoints are documented
- hardware, runtime, memory, and approximate compute are logged
- all external code, models, datasets, and assets are cited with version/license
- failure cases are not filtered out silently
- limitations are linked to actual experiments

## Ethics And Human Data

Because the research direction is human-friendly robot intelligence, do not treat human interaction data as ordinary logs.

- If collecting human instructions, preferences, corrections, images, voice, or personally identifiable data, check IRB or local ethics approval requirements.
- Store private user identifiers separately from research logs.
- Avoid claims about "understanding human intention" unless the evaluation actually tests intent inference or interaction outcomes.
- Include failure modes where the robot should ask for clarification instead of acting.

## When To Create A Paper Folder

Create a paper folder only when all are true:

- one-sentence thesis is stable
- at least one main result table exists
- one system diagram or method figure is sketched
- target venue and deadline are selected
- related work map has at least 15 closely read papers
- claim-evidence ledger has no empty evidence for main claims

Until then, keep paper work in this protocol and result logs.
