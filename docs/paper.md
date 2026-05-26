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
| The decision layer remains useful under real RGB-D/open-vocabulary proposal noise | E003 direct current-rescan bridge, heldout split, detector/proposal baseline comparison | diagnostic supported, final robustness not ready | M75 full aggregate over b01/b02/b03 has target detected 144 / 195, H001 157 / 195, context-agnostic 156 / 195, `ConceptGraphs` 114 / 195, detector task-budget 24 / 195, and detector top5 51 / 195. M76 marks this diagnostic-table ready but blocks final robustness due to detector precision 0.051892, target detection 0.738462, and false-positive load. M78 fixed replay reproduces M77 best policy with 0 mismatches and reaches top5 60 / 195, target detected 147 / 195, precision 0.105832. M80-M82 reproduces the expected `heldout_b02` runner gain: detector top5 9 / 69 -> 15 / 69 and task-budget 5 / 69 -> 7 / 69, but target detected stays 42 / 69 |
| The framework is stronger than external dynamic/open-vocabulary mapping baselines | E005 `ConceptGraphs` and at least one additional fair query-level route such as `Open3DSG` / `HOV-SG` | partially supported for proxy-search only | `ConceptGraphs` full 195-row heldout comparison is ready; corrected `Open3DSG` bridge is denominator-aligned; M65 includes the M64 predicted-vocabulary adapter as a bounded external scene-graph baseline row; M66 fixes row-level failure boundaries |
| The system supports deployable search policy | bounded budget improvement, allowed-input contract, failure separation | not ready | current policy is diagnostic, not deployable |
| The system improves real navigation `SR` / `SPL` | simulator/navmesh/trajectory execution and navigation baselines | unsupported | no real navigation evaluation yet |

## Experiment-To-Paper Mapping

- E001: defines the semantic-pair dynamic object search problem and naive baselines.
- E002: adds path/search-cost bridge and separates source-limited failures from policy failures.
- E003: tests controlled perception noise and real RGB-D/open-vocabulary proposal failure modes.
- E004: tests memory trust and task-context conditioning, with claim boundaries.
- E005: adds external baseline pressure; `DualMap` runs without object-map outputs, `ConceptGraphs` now has full 195-row heldout query-level aggregation, and `Open3DSG` is source/schema/export/query-conversion ready on the same denominator. Corrected `Open3DSG` primary-label strict bbox top5 is 81/195 and relaxed bbox 1m top3 is 90/195. M64 leakage-safe predicted-vocabulary adapter reaches strict 144/195 and relaxed 147/195. M65 includes it as a bounded external baseline row, keeps the primary-label adapter diagnostic, and keeps human intent as secondary structured task-context evidence. M66 records H001-only 60 rows vs `ConceptGraphs`, H001-only 39 rows vs `Open3DSG` vocab, and only 1 task-context-specific gain row. M68 materializes the robustness route: 195-row full-denominator real proposal bridge inputs split into 3 heldout batches. M71/M74/M75 convert and aggregate all b01/b02/b03 detector batches. M76 makes M75 a diagnostic real-proposal search table. M77 separates pre-cap recoverable targets from prompt/detector recall misses. M78 implements fixed offline repair replay. M79 confirms runner insertion without source edit and selects `heldout_b02` as the first targeted rerun. M80-M82 launch, verify, and convert that rerun; M83 must decide whether to rerun b01/b03 or keep this as diagnostic detector-repair evidence.

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
- What does `DualMap` / `ConceptGraphs` / `Open3DSG` fail or solve compared with our method?
- Does `Open3DSG` remain weak after a leakage-safe predicted-vocabulary adapter, or was the gap mostly an adapter mismatch?
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
| Is this competitive with external mappers? | E005 `ConceptGraphs` comparison is positive; corrected `Open3DSG` is weaker under primary labels, while M65 accepts the M64 bounded predicted-vocabulary adapter as a main-table external baseline row; M66 reports the row-level boundary |
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
