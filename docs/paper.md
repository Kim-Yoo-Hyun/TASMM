# Paper Workflow

Status: active protocol, no paper folder yet.

이 문서는 paper 작성 규칙과 claim 검증 기준만 관리한다. 논문 본문 산출물은 아직 만들지 않는다. 실제 paper folder는 thesis, main result table, method figure, target venue, claim-evidence ledger가 구체화된 뒤에 만든다.

Source note: this workflow reflects the "Motivation is Not Novelty" guide: https://gisbi-kim.github.io/motivation-is-not-novelty/

## Core Rule

Motivation is not novelty.

For this project, the following is only motivation:

- dynamic objects make semantic memory stale
- RGB-D / open-vocabulary perception creates missed targets, false positives, and localization errors
- human task context should affect robot behavior
- existing mapping systems do not directly solve our dynamic search setting

Novelty starts only when the paper can explain why the naive solution fails, what principle follows from that diagnosis, and why the method must have its specific form.

## Paper Claim Ladder

Use this ladder before writing any abstract, introduction, method, or contribution list.

| Stage | Required Output | Current H001 Direction |
| --- | --- | --- |
| Motivation | What existing methods fail to handle | Stale semantic memory under dynamic object search and noisy RGB-D/open-vocabulary proposals |
| Naive baseline | Simplest implementation implied by the motivation | static old memory, fixed top-k, detector-confidence ranking, context-agnostic memory trust |
| Failure diagnosis | Why the naive baseline fails | stale old-location FP, detector recall miss, false-positive pushdown, centroid/localization error, path/reachability mismatch, task-budget mismatch |
| Principle | One sentence that explains the required method form | Candidate: memory trust should be conditioned on staleness, task value, current-evidence reliability, and search/re-observation cost |
| Method form | Components derived from the principle | task context conditioner, memory trust gate, re-observation budget, path/search-cost ranking, proposal reliability bridge |
| Evidence | Experiments that test the principle, not just performance | E001/E002 proxy search, E003 noise and real proposal bridge, E004 memory trust policy, E005 external baselines |
| Boundary | What the paper cannot claim yet | real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, natural-language intent understanding |

## Current One-Liner

Working one-liner:

> In dynamic indoor search, stale semantic memory fails not because old memory is always wrong, but because its reliability is task- and observation-cost dependent; therefore a semantic map should expose memory trust and re-observation as first-class decisions conditioned on task value, current proposal reliability, and search cost.

This is still a working hypothesis. It becomes a paper-ready novelty sentence only if ablations show that each condition is necessary and simpler alternatives fail for predictable reasons.

## Novelty Gate

Before calling anything a contribution, answer these questions.

- What is the closest naive baseline, in one sentence?
- Why does it fail, in a mechanism-level sentence?
- Which method component is forced by that failure diagnosis?
- What breaks when that component is removed?
- Why not static memory, detector-confidence ranking, fixed top-k, or context-agnostic memory trust?
- Which result tests the insight rather than merely showing a better score?
- Does the claim hold beyond one scan, one label group, or one artifact route?
- Can the novelty be explained in 30 seconds without saying "we propose"?

If four or more answers are weak, the work is still motivation-stage and the method section should not be drafted.

## Claim-Evidence Ledger

| Claim Candidate | Evidence Needed | Current Status | Risk |
| --- | --- | --- | --- |
| Task/staleness-aware memory decision improves dynamic object search proxy behavior | E001/E002/E004 tables vs static memory, fixed top-k, context-agnostic trust, path-aware variants | partially supported | task-context effect is narrow |
| The decision layer remains useful under real RGB-D/open-vocabulary proposal noise | E003 direct current-rescan bridge, heldout split, detector/proposal baseline comparison | not final | false-positive load and detector recall miss remain large |
| The framework is stronger than external dynamic/open-vocabulary mapping baselines | E005 `DualMap` or `ConceptGraphs` adapter and fair query-level comparison | in progress | `DualMap` runs but lacks object `*.pkl`; `ConceptGraphs` 4-scan and `heldout_b01/b02` query metrics are ready; `heldout_b03` and full aggregation remain |
| The system supports deployable search policy | bounded budget improvement, allowed-input contract, failure separation | not ready | current policy is diagnostic, not deployable |
| The system improves real navigation `SR` / `SPL` | simulator/navmesh/trajectory execution and navigation baselines | unsupported | no real navigation evaluation yet |

## Experiment-To-Paper Mapping

- E001: defines the semantic-pair dynamic object search problem and naive baselines.
- E002: adds path/search-cost bridge and separates source-limited failures from policy failures.
- E003: tests controlled perception noise and real RGB-D/open-vocabulary proposal failure modes.
- E004: tests memory trust and task-context conditioning, with claim boundaries.
- E005: adds external baseline pressure; `DualMap` runs without object-map outputs, while `ConceptGraphs` now has 4-scan metrics plus `heldout_b01/b02` batch diagnostics and needs `heldout_b03` before final aggregation.

Main tables should not merely report that our method is better. They should show which failure mode is addressed by which component.

## Required Ablations

Minimum ablation set for a serious paper draft:

- no task context
- no staleness / memory-trust term
- no current-proposal reliability term
- no re-observation budget
- no path/search-cost term
- fixed top-k replacement
- detector-confidence-only replacement
- context-agnostic trust replacement
- external mapping baseline replacement when available

Each ablation must have an expected failure mode before running it.

## Reviewer Defense

Expected reviewer questions:

- Why is this semantic mapping, not just ranking?
- Why is structured task context enough, and what is not claimed about natural language?
- Why not use a stronger detector or open-vocabulary mapper directly?
- Why does stale memory require task-conditioned trust instead of a fixed decay score?
- Why does the method generalize beyond `chair` / `pillow` and the current 4 rescans?
- What does `DualMap` / `ConceptGraphs` fail or solve compared with our method?
- Where are real navigation `SR` / `SPL` and what is the bridge until then?

Answers must refer to artifacts, tables, ablations, or explicit limitations.

## Paper Shape

### Abstract

Four sentences only:

1. problem and mechanism-level failure of existing semantic memory
2. principle and method form in one concrete sentence
3. dataset / benchmark / baseline setting
4. strongest quantitative result and boundary

### Introduction

Use this order:

1. Human-facing robot tasks need semantic maps that support action under stale and noisy observations.
2. Existing semantic maps or open-vocabulary mappers do not directly decide when old memory should be trusted for a task.
3. Diagnose the naive baseline failure, not just the application pain point.
4. State the principle that forces the method design.
5. State contributions as tested claims with evidence pointers.

### Method

Do not write a system-diagram-only method section. Each component must be introduced by the failure mode that requires it.

### Experiments

Every experiment answers a reviewer question:

| Reviewer Question | Experiment |
| --- | --- |
| Does stale memory require a decision layer? | static memory vs trust/re-observation policies |
| Does task context matter beyond a global threshold? | task-conditioned vs context-agnostic trust |
| Does path/search cost change the decision? | E002/E004 cost-aware metrics |
| Does the result survive proposal noise? | E003 controlled and real proposal diagnostics |
| Is this competitive with external mappers? | E005 `DualMap` / `ConceptGraphs` comparison |
| What breaks? | failure taxonomy and claim boundary table |

## Reproducibility Checklist

- exact dataset version and split are recorded
- preprocessing is described
- all policy inputs and forbidden inputs are fixed
- all baselines are sourced or implemented
- exact commands reproduce main tables
- Docker image and hardware are recorded for paper-body experiments
- external code, models, checkpoints, datasets, and assets are cited with version/license
- failure cases are not filtered out silently
- limitations are linked to actual experiments

Current reproducibility entry point: `docs/reproducibility.md`.

## When To Create A Paper Folder

Create a paper folder only when all are true:

- one-sentence thesis is stable
- method components are derived from diagnosed failures
- at least one main result table exists
- one system diagram or method figure is sketched
- target venue and deadline are selected
- related work map has at least 20 closely read papers
- claim-evidence ledger has no empty evidence for main claims

Until then, keep paper work in this protocol and result logs.
