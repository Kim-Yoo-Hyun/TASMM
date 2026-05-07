# CAND-001 Benchmark Shortlist

Updated: 2026-05-05

## Purpose

CAND-001을 검증 가능한 hypothesis로 만들기 위해 `DualMap`, `OpenIN`, `OGScene3D`, `LangMap`에서 dataset / benchmark / metric / baseline 후보를 추출한다.

## Shortlist

| Rank | Benchmark route | Source papers | Fit | Risk | Decision |
| --- | --- | --- | --- | --- | --- |
| 1 | Dynamic moved-object navigation episodes | `OpenIN`, `DualMap` | Directly tests stale object memory | Need reproducible dynamic scene construction | Use for H001 |
| 2 | Static-to-dynamic RGB-D replay with before/after maps | `DualMap`, `OGScene3D` | Isolates mapping and stale-memory update without full robot stack | May need custom replay construction | Selected for hypothesis-stage Route B |
| 3 | Hierarchical open-vocabulary goal navigation | `LangMap` | Tests granularity and human-facing language | Does not include moved-object dynamics | Use as static sanity check, not primary |
| 4 | Incremental open-vocabulary scene graph mapping | `OGScene3D` | Tests temporal memory and graph update | Focuses more on scene understanding than navigation | Use as representation reference |

## Extracted Evidence

### DualMap

사실:

- `DualMap` evaluates semantic segmentation and efficiency on `ScanNet` and `Replica`.
- For static object navigation, it uses `HM3D` scenes `00829`, `00848`, `00880` and augments them with `YCB` objects.
- For dynamic navigation, it constructs object-level dynamic environments in `Habitat Simulator`, with `In-anchor relocation` and `Cross-anchor relocation`.
- Metrics include `mIoU`, `F-mIoU`, `mAcc`, `ODR`, average/peak memory, `TPF`, and navigation `SR`.
- Baselines include `ConceptGraphs` and `HOV-SG`; candidate selection ablation compares `Random Pick`, `Based on Ma`, and `Based on M'a`.

논문 주장:

- `DualMap` claims that global abstract map / local concrete map decomposition helps online language-guided navigation in dynamic changing scenes.
- It reports dynamic `SR` for `In-anchor` and `Cross-anchor` changes and analyzes cross-anchor failures.

CAND-001에 주는 의미:

- `DualMap` gives the best starting evaluation shape for dynamic semantic map update.
- But it does not isolate `stale false-positive rate` as a primary metric, so CAND-001 can add a sharper stale-memory evaluation contract.

### OpenIN

사실:

- `OpenIN` defines displaced instance exploration and navigation in domestic environments.
- It uses `Gibson` scenes for offline multi-type query evaluation and `Habitat Simulator` long-sequence navigation with moved everyday instances.
- Metrics include query success rate, `SR`, `Tasks_SR(i)`, `SPL`.
- Baselines include `VLMaps`, `ConceptGraphs`, `VLFM`, and `OpenFMNav` variants.
- Ablations include `w/o GPT-4o`, `w/o text`, `w/o RGB`, `Ours-w/o-update`, and carrier-selection strategies.

논문 주장:

- `OpenIN` claims that updating `Carrier-Relationship Scene Graph` improves navigation to moved target instances.

CAND-001에 주는 의미:

- `OpenIN` is the closest benchmark shape for moved-instance memory.
- It suggests a relation-based stale-memory baseline: carrier relationship update only.

### OGScene3D

사실:

- `OGScene3D` evaluates open-vocabulary semantic mapping on `Replica` and `ScanNet`, and scene graph construction on `3RScan`.
- Metrics include `mIoU`, `F-mIoU`, `mAcc`, graph `Recall`, and runtime.
- Baselines include `ConceptGraphs`, `HOV-SG`, 3DGS-based semantic mapping methods, and `OpenGS-SLAM` depending on task.

논문 주장:

- `OGScene3D` claims confidence-based Gaussian semantic representation, hierarchical semantic optimization, temporal memory, and progressive graph construction improve incremental open-vocabulary scene understanding.

CAND-001에 주는 의미:

- `OGScene3D` supports the trend that temporal memory and confidence are becoming core semantic mapping components.
- It is less ideal as the first benchmark because it emphasizes scene understanding and segmentation more than moved-object task success.

### LangMap

사실:

- `LangMap` introduces `HieraNav`, a multi-granularity open-vocabulary goal navigation task at scene, room, region, and instance levels.
- It is built on all 36 `HM3D-Sem` validation scenes.
- It provides human-verified region labels, region descriptions, instance descriptions over 414 object categories, and 18K+ navigation tasks.
- Metrics include `SR`, `SPL`, `SeqSR`, and `SeqSR-4`.
- Baselines include `PSL`, `SenseAct-Mono`, `3D-Mem`, `Uni-NaVid`, and `MTU3D`.

논문 주장:

- `LangMap` claims hierarchical open-vocabulary goal navigation reveals failures hidden by object-only navigation.

CAND-001에 주는 의미:

- `LangMap` is useful for static granularity and instruction-style sanity checks.
- It does not directly test stale object memory, so it should not be the primary H001 benchmark.

## H001 Benchmark Decision

에이전트 추론:

- H001 should ultimately use `OpenIN` / `DualMap`-style moved-object episodes as the primary evaluation target.
- For the hypothesis stage, Route B before/after RGB-D replay is selected because the goal is research-potential validation, not full reproduction.
- `LangMap` should be a secondary static grounding/granularity sanity check.
- `OGScene3D` should inform representation design, especially temporal confidence, but not define the first experiment.

## H001 Metric Decision

Primary metrics:

- `stale false-positive rate`: fraction of queries where the map returns an old invalid target as current.
- `moved-object recovery success`: whether the system finds or correctly redirects search after detecting stale memory.
- `moved-object recovery attempts`: number of candidate locations or anchors checked before recovery.
- `SR`: navigation or query success under moved-object episodes.

Secondary metrics:

- `SPL` if full navigation is available.
- query latency.
- map update latency.
- map size / memory.

## H001 Baseline Decision

Baselines:

- static object-centric semantic map.
- time-decay confidence map.
- relation-only update map, inspired by `OpenIN`'s `CRSG`.
- global/local candidate selection, inspired by `DualMap`.
- oracle current object pose.

## Next Action

Create `H001_stale-object-memory` as a draft hypothesis and keep it below experiment-ready until dataset access and baseline implementation feasibility are checked.
