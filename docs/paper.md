# Paper Workflow

Updated: 2026-08-28

이 문서는 특정 claim ledger가 아니라 top-tier paper로 승격하는 판단 규칙을 관리한다. 과거 CAND-001 전용 ledger는 `/home/yoohyun/research2_retired_20260901/archive/task-aware-semantic-memory-mapping-2026-08-28/docs/paper-legacy-claim-ledger.md`에 보존한다.

## Current Boundary

- 현재 paper direction은 확정되지 않았다.
- `Policy-Conditional Semantic Mapping`은 K05 G1 semantic gate에서 종료됐으며 candidate나 paper direction이 아니다.
- `Task-Aware Semantic Memory Mapping`, human-intent conditioning, acquisition/admission, decision-calibrated revision은 active contribution이 아니다.
- `paper/`는 thesis, main result table, method figure, target venue, claim-evidence ledger가 concrete해질 때만 만든다.

## Claim Construction

각 claim은 다음 순서를 만족해야 한다.

1. motivation
2. naive baseline
3. case-level failure diagnosis
4. failure에서 도출된 principle
5. principle이 강제하는 method form
6. component ablation과 external-baseline evidence

`we propose`를 지워도 남는 mechanism insight가 없으면 contribution으로 승격하지 않는다.

## Promotion Gates

| Gate | Minimum evidence |
| --- | --- |
| novelty | 가장 가까운 primary prior와 exact residue; module-combination novelty 금지 |
| phenomenon | 2개 이상의 split/scene/task/domain에서 denominator와 prevalence |
| simple baseline | 최소 3개 단순 대안과 strongest adjacent baseline을 같은 evidence/cost에서 비교 |
| method necessity | simple baseline 뒤에도 residual이 남고 component가 failure mechanism에서 필연적으로 도출 |
| behavior | map metric뿐 아니라 task success, regret, path/search/re-observation cost |
| generalization | 2개 이상의 독립 축과 precommitted robustness/failure analysis |
| reproducibility | Docker image/source/data/seed/command/output/verifier 기록 |

## Claim-Evidence Ledger Template

| Claim | Baseline threat | Required evidence | Disconfirmation rule | Status |
| --- | --- | --- | --- | --- |
| phenomenon | simplest measurement explanation | frozen denominator and paired result | negligible or unstable prevalence | open |
| method | strongest simple/adjacent method | same-input, cost-matched comparison and ablation | simple baseline closes residual | open |
| generality | split/domain shift | independent held-out routes | single-route or label-specific effect | open |

## Reviewer Defense

- 왜 semantic mapping 문제이며 calibration/ranking만의 문제가 아닌가?
- 왜 더 단순한 coverage, source count, calibration, weighting, abstention으로 충분하지 않은가?
- acquisition policy와 evaluation policy가 바뀌어도 비교가 leakage-safe한가?
- no-support 영역에서 무엇을 추정하지 않고 abstain/re-observe하는가?
- map-quality 변화가 실제 behavior와 cost에 어떤 causal consequence를 만드는가?
- 실패 조건과 claim boundary가 사전에 고정됐는가?

답은 문장보다 artifact, table, ablation, failure row로 한다.

## Paper Folder Gate

다음이 모두 준비되기 전에는 `paper/`를 만들지 않는다.

- stable one-sentence thesis
- failure-derived method
- main result table 1개 이상
- method figure 초안
- target venue/deadline
- close-prior map
- main claim마다 evidence와 disconfirmation record
