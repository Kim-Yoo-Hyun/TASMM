# Gates

## 사실

| Gate | 핵심 결과 | 상태 |
| --- | --- | --- |
| Schema smoke | 32 stale-label rows, acceptance pass | 완료 |
| Value smoke | stale FP 0.0000, moved recovery 0.0000 | 완료 |
| Unchanged control | trusted FNR 0.0000 | 완료 |
| Re-observation smoke | target available 1.0000, recovery 0.0000 | 완료 |
| Pair geometry | rigid joins 11 / 11, removed absent 6 / 6 | 완료 |
| Real-pair query | stale FP 0.0000, moved recovery 0.0000 | 완료 |
| Search-region prior | best non-oracle hit 0.6364 | 완료 |
| Instance evidence | 3-row exact recovery 1.0000, but annotation-anchor risk | 완료 |
| Non-persistent anchor | 3-row exact recovery 1.0000 without persistent id ranking | 완료 |
| Multi-pair validation | 12 pairs, 10 significant moved rows, `strict_pass` | 완료 |
| Uncertainty top-k | Recall@returned K 1.0000, mean `ExpectedSearchCost` 1.3000 | 완료 |
| Search-cost bridge | proxy search success 1.0000, `AttemptSPL` proxy 0.883333, mean checked locations 1.3000 | 완료 |
| Perception-noise robustness | controlled proposal-noise primary pass: observable-target success 0.904000, `AttemptSPL` proxy 0.644833 | 완료 |
| Task-context conditioning | structured context pass: `high_value_fetch` success 0.988000, utility delta +0.265350 | 완료 |
| Budget baseline | `routine_fetch` more budget-efficient than `always_top5`; `high_value_fetch` matches `always_top5` | 완료 |
| Main experiment readiness | `ready_with_constraints`; proxy semantic-pair benchmark only | 완료 |

## 논문 주장

지원되는 주장:

- H001 has a strict hypothesis-stage semantic map-update signal.
- Old stale locations can be suppressed while low-motion object memories are preserved.
- Hard top-1 failures can be exposed through bounded candidate uncertainty.
- `ExpectedSearchCost` can be bridged to a candidate-inspection search proxy on the current artifact.
- Under controlled annotation-level proposal noise, `uncertainty_topk_v0` preserves higher observable-target search success than direct top-1 memory update.
- Structured task context can change returned candidate budget and improve task-weighted utility without claiming language understanding.
- Budget conditioning is not just better than a fixed uncertainty budget; it must be compared against `always_topK` baselines in experiments.

아직 지원되지 않는 주장:

- The method solves exact moved-object recovery.
- The method improves navigation `SR` / `SPL`.
- The method is robust to real RGB-D or open-vocabulary perception noise.
- The method understands natural-language human intention.

## 에이전트 추론

기존 01-36 문서의 대부분은 gate-by-gate execution log였다. 현재 의사결정에는 모든 중간 gate를 따로 유지할 필요가 없고, 위 표와 `artifacts/` outputs가 충분하다.

Search-cost bridge, perception-noise gate, task-context conditioning gate, budget baseline gate는 모두 통과했다. 단, 이들은 real navigation / real RGB-D perception / natural-language intention understanding이 아니라 proxy gate다. Budget baseline 결과상 `high_value_fetch`의 best behavior는 `always_top5`와 같으므로, experiment에서는 fixed top-k baselines를 반드시 포함해야 한다.

## 사용자 판단 필요

다음 판단은 `ready_with_constraints`를 받아들이고 main experiment design으로 넘어갈지 여부다. 추가 pair staging은 `5630cfcb` -> `d7d40d75`가 가능하지만, main experiment transition 이후에 진행한다.
