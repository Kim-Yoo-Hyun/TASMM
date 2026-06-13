# CAND-001 Top-Tier Literature Refresh For E008-M137

Checked: 2026-06-09

Purpose: E008-M137 `confidence-preserving trajectory-aware repair` 설계에 직접 연결되는 literature refresh다. 목표는 broad survey 자체가 아니라, 현재 H001의 병목인 detector-confidence baseline 대비 `SPL` 손실, real RGB-D/open-vocabulary proposal noise, external map/navigation baseline, human intent claim boundary를 해결할 근거를 찾는 것이다.

## Scope

사실:

- 기존 `literature/`에는 2024-2026 semantic mapping / open-vocabulary navigation 중심의 28개 paper folder가 있다.
- 이번 refresh에서는 `Google Scholar` 자동 scraping이나 PDF bulk download를 하지 않았다.
- metadata scan은 기존 local paper registry, arXiv API metadata, CVF/OpenReview/project pages, official GitHub를 우선 사용했다.
- GitHub code audit은 checkpoint/model download 없이 shallow/filter clone 또는 기존 local clone inspection으로 수행했다.

사용자 판단 필요:

- 후속 작업에서 아래 deep-read shortlist 중 8-12개만 개별 paper folder로 승격할지 결정해야 한다.

## Current H001 Bottleneck

사실:

- E008-M135에서 모든 tested policy는 one target-free case에서 `SR` 1.0을 달성했다.
- Selected repair `trajectory_greedy_confidence_path_repair_v0`는 `SPL` 0.329622이고, detector-confidence / confidence-only baseline은 `SPL` 0.701267이다.
- E008-M136은 current repair scale-up을 reject했고, next unit으로 E008-M137 `confidence-preserving trajectory-aware repair`를 선택했다.
- E006-M08은 current evidence로 human intent main claim을 지지하지 않는다.

에이전트 추론:

- 지금 필요한 문헌 근거는 "더 많은 semantic map"이 아니라 "confidence, uncertainty, path cost, visibility, frontier/source coverage, re-observation을 어떤 의사결정 구조로 결합해야 detector-confidence를 망치지 않는가"다.
- E008-M137은 path cost를 primary score로 쓰면 안 된다. trajectory/search cost는 confidence ordering을 뒤집는 신호가 아니라, confidence band 안의 guarded tie-break, veto, 또는 budget allocator로 들어가야 한다.

## 100-Paper Metadata Scan

아래 표는 metadata scan이다. `Deep?`는 이번 단계에서 deep-read 후보인지 표시한다. `Use`는 H001/E008에 바로 연결되는 역할이다.

| # | Paper / Method | Year | Source status | Deep? | Use for H001 |
| --- | --- | --- | --- | --- | --- |
| 1 | `ConceptGraphs` | 2024 | existing folder + code | yes | external open-vocabulary map baseline |
| 2 | `Open3DSG` | 2024 | existing folder + local read-only source | yes | external 3D scene graph baseline |
| 3 | `HOV-SG` | 2024 | existing folder + cloned code | yes | hierarchy/map-navigation baseline |
| 4 | `O2V-Mapping` | 2024 | existing folder | yes | online open-vocabulary mapping comparison |
| 5 | `VLFM` | 2024 | existing folder + cloned code | yes | frontier/navigation baseline pressure |
| 6 | `HM3D-OVON` | 2024 | existing folder + cloned code | yes | open-vocabulary ObjectNav benchmark |
| 7 | `GOAT-Bench` | 2024 | existing folder + cloned code | yes | lifelong / multi-goal navigation benchmark |
| 8 | `OpenEQA` | 2024 | existing folder | no | environment memory / QA boundary |
| 9 | `EmbodiedScan` | 2024 | existing folder | no | embodied 3D benchmark substrate |
| 10 | `LangSplat` | 2024 | existing folder | no | language feature map baseline |
| 11 | `Clio` | 2024 | existing folder | yes | task-driven granularity |
| 12 | `One Map to Find Them All` | 2024 | existing folder | no | reusable open-vocabulary map |
| 13 | `OpenGraph` | 2024 | existing folder | no | hierarchical graph representation |
| 14 | `OVO-SLAM` | 2024 | existing folder | no | online semantic SLAM assumption check |
| 15 | `Open-Vocabulary Mobile Manipulation with 3D Semantic Maps` | 2024 | existing folder | no | manipulation-facing map boundary |
| 16 | `RoboHop` | 2024 | existing folder | no | topological semantic map comparison |
| 17 | `DynaMem` | 2024 | project page + arXiv | yes | dynamic memory update and real robot baseline pressure |
| 18 | `Open Scene Graphs for Open-World Object-Goal Navigation` | 2024/2025 | project page + code link | yes | scene memory for open-world ObjectNav |
| 19 | `DovSG` | 2024/2025 | arXiv + GitHub page | yes | dynamic open-vocabulary 3D scene graph update |
| 20 | `OpenObject-NAV` | 2024 | arXiv metadata | no | carrier relationship / dynamic ObjectNav |
| 21 | `DualMap` | 2025 | existing folder + cloned code | yes | dynamic global/local map baseline |
| 22 | `OpenIN` | 2025 | existing folder + project page | yes | moved instance navigation with carrier relationship |
| 23 | `OpenMap` | 2025 | existing folder + project page | yes | instruction-to-instance grounding |
| 24 | `Open-Vocabulary Functional 3D Scene Graphs` | 2025 | existing folder | no | functional relation extension |
| 25 | `Open-Vocabulary Octree-Graph` | 2025 | existing folder | no | compact object/occupancy graph |
| 26 | `3D-Mem` | 2025 | existing folder + cloned code | yes | scene memory / exploration / reasoning baseline |
| 27 | `FindAnything` | 2025 | existing folder | no | object-centric resource-aware search |
| 28 | `osmAG-LLM` | 2025 | existing folder | no | semantic map + LLM navigation |
| 29 | `Graph2Nav` | 2025 | arXiv metadata | yes | relation graph to object search efficiency |
| 30 | `SD-OVON` | 2025 | arXiv metadata | no | dynamic-scene OVON benchmark generation |
| 31 | `OVAMOS` | 2025 | arXiv metadata | no | open-vocabulary multi-object search |
| 32 | `Uncertainty-Informed Active Perception for Open Vocabulary Object Goal Navigation` | 2025 | arXiv metadata | yes | uncertainty/re-observation design |
| 33 | `Where Did I Leave My Glasses?` | 2025 | arXiv metadata | yes | semi-static real-world semantic exploration |
| 34 | `DIV-Nav` | 2025 | arXiv metadata | no | spatial relationship multi-object navigation |
| 35 | `NavA^3` | 2025 | arXiv metadata | no | broad instruction/navigation/search scope |
| 36 | `FiLM-Nav` | 2025 | arXiv metadata | no | open-vocabulary ObjectNav policy baseline |
| 37 | `KM-ViPE` | 2025 | arXiv metadata | no | online VLG semantic SLAM |
| 38 | `JanusVLN` | 2025 | arXiv metadata | no | dual implicit memory for VLN |
| 39 | `Structured Interfaces for Automated Reasoning with 3D Scene Graphs` | 2025 | arXiv metadata | no | structured 3DSG reasoning interface |
| 40 | `Language-Grounded Hierarchical Planning and Execution with Multi-Robot 3D Scene Graphs` | 2025 | arXiv metadata | no | multi-robot 3DSG planning |
| 41 | `RAVEN` | 2026 | project page | yes | behavior-tree semantic memory switching |
| 42 | `SCOUT` | 2026 | arXiv metadata | yes | uncertainty-guided semantic scene coverage |
| 43 | `Remember with Confidence` | 2026 | arXiv metadata | yes | uncertainty quantification for spatio-temporal memory |
| 44 | `OVAL` | 2026 | arXiv metadata | yes | augmented memory for lifelong ObjectNav |
| 45 | `ConsistNav` | 2026 | arXiv metadata | yes | semantic executive control / action consistency |
| 46 | `DRIVE-Nav` | 2026 | arXiv metadata | yes | directional reasoning, inspection, verification |
| 47 | `R2F` | 2026 | arXiv metadata | yes | ray frontier repurposing without LLM |
| 48 | `TravExplorer` | 2026 | arXiv metadata | no | traversability-aware 3D planning |
| 49 | `GoalVLM` | 2026 | arXiv metadata | no | VLM-driven ObjectNav |
| 50 | `GoalSwarm` | 2026 | arXiv metadata | no | multi-UAV semantic coordination |
| 51 | `USS-Nav` | 2026 | arXiv metadata | no | lightweight UAV scene graph ObjectNav |
| 52 | `SpaceVLN` | 2026 | arXiv metadata | no | online spatial cognitive memory |
| 53 | `IntentNav` | 2026 | arXiv metadata | no | human-demonstration ObjectNav |
| 54 | `PlatonicNav` | 2026 | arXiv metadata | no | topological map semantic correspondence |
| 55 | `PSG-Nav` | 2026 | arXiv metadata | yes | probabilistic scene graph decision making |
| 56 | `Uni-LaViRA` | 2026 | arXiv metadata | no | language-vision-action translation |
| 57 | `MORN` | 2026 | arXiv metadata | yes | metacognitive object-goal regulation |
| 58 | `BEACON` | 2026 | arXiv metadata | yes | navigation affordance under occlusion |
| 59 | `EvoMemNav` | 2026 | arXiv metadata | yes | self-evolving fine-grained memory |
| 60 | `APEX` | 2026 | arXiv metadata | no | memory-based aerial ObjectNav |
| 61 | `Dynamic Resilient Spatio-Semantic Memory` | 2026 | arXiv metadata | yes | hybrid localization for mobile manipulation |
| 62 | `Predictive Spatio-Temporal Scene Graphs for Semi-Static Scenes` | 2026 | arXiv metadata | yes | predictive stale-memory modeling |
| 63 | `IGV-RRT` | 2026 | arXiv metadata | yes | active object search in changing environments |
| 64 | `Rheos` | 2026 | arXiv metadata | no | continuous motion in hierarchical 3DSG |
| 65 | `Relational Semantic Reasoning on 3D Scene Graphs for Open World Interactive Object Search` | 2026 | arXiv metadata | yes | relational search baseline pressure |
| 66 | `HERO` | 2025/2026 | arXiv metadata | no | movable obstacles in traversable 3DSG |
| 67 | `DGSG-Mind` | 2026 | arXiv metadata | no | dynamic Gaussian scene graphs |
| 68 | `FUS3DMaps` | 2026 | arXiv metadata | no | voxel-instance fusion |
| 69 | `OVI-MAP` | 2026 | existing folder | yes | instance-semantic separation |
| 70 | `OGScene3D` | 2026 | existing folder | yes | temporal confidence in incremental graph update |
| 71 | `LangMap` | 2026 | existing folder | yes | hierarchical goal navigation benchmark |
| 72 | `RAG-3DSG` | 2026 | project/arXiv metadata | no | re-shot retrieval for 3DSG semantic consistency |
| 73 | `FOUND-IT` | 2026 | arXiv metadata | no | task-driven 3DSG granularity |
| 74 | `LEXI-SG` | 2026 | arXiv metadata | no | monocular 3DSG with room-guided reconstruction |
| 75 | `Relationship-Aware Hierarchical 3D Scene Graph` | 2026 | project/arXiv metadata | no | relation-aware task reasoning |
| 76 | `T-FunS3D` | 2026 | arXiv metadata | no | task-driven functional 3D segmentation |
| 77 | `Hierarchical and Holistic Open-Vocabulary Functional 3D Scene Graphs` | 2026 | arXiv metadata | no | hierarchical function graph |
| 78 | `Grounding by Remembering` | 2026 | arXiv metadata | no | memory for functional affordances |
| 79 | `3D-Belief` | 2026 | arXiv metadata | no | embodied belief inference |
| 80 | `Skill-3D` | 2026 | arXiv metadata | no | scene-aware skill evolution |
| 81 | `HIMM` | 2026 | arXiv metadata | no | long-term embodied memory |
| 82 | `BrainMem` | 2026 | arXiv metadata | no | evolving memory for task planning |
| 83 | `VLingNav` | 2026 | arXiv metadata | no | visual-assisted linguistic memory |
| 84 | `Remember to be Curious` | 2026 | arXiv metadata | no | episodic context / persistent worlds |
| 85 | `Personalizing Embodied MLLM Agents over Long-term User Interactions` | 2026 | arXiv metadata | no | personalization / human context |
| 86 | `AgentComm` | 2026 | arXiv metadata | no | semantic communication for embodied agents |
| 87 | `AgentComm-Bench` | 2026 | arXiv metadata | no | stress testing embodied cooperation |
| 88 | `BEHAVIOR` / `BEHAVIOR-1K` | 2021/2022 | benchmark background | no | household task realism |
| 89 | `OK-Robot` | 2024 | arXiv/project | yes | static memory manipulation baseline |
| 90 | `VLMaps` | 2023 | project | yes | language-feature map baseline |
| 91 | `CLIP-Fields` | 2023 | paper background | no | dense language field baseline |
| 92 | `LERF` | 2023 | paper background | no | language embedded radiance field |
| 93 | `OpenScene` | 2023 | paper background | no | open-vocabulary 3D segmentation |
| 94 | `OpenMask3D` | 2023 | existing route | yes | external 3D instance proposal baseline |
| 95 | `OVIR-3D` | 2023/2024 | project background | no | open-vocabulary instance retrieval |
| 96 | `OVSG` | 2023/2024 | project background | no | scene graph from OVIR-3D |
| 97 | `GroundingDINO` | 2023 | detector paper/code | yes | detector-confidence baseline source |
| 98 | `SAM` | 2023 | segmentation paper/code | no | mask proposal baseline source |
| 99 | `OWL-ViT` | 2022 | detector paper/code | no | open-vocabulary detector baseline |
| 100 | `YOLO-World` | 2024 | detector paper/code | no | efficient open-vocabulary detector pressure |

## Deep-Read Shortlist

사실:

The following 25 papers/methods should be treated as the immediate deep-read set for E008-M137 and the next top-tier claim audit.

| Priority | Paper / Method | Why deep-read now | Direct H001 question |
| --- | --- | --- | --- |
| P0 | `VLFM` | strong `SPL` pressure in `Habitat` ObjectNav | What does frontier/value-map ranking do that H001 lacks? |
| P0 | `HM3D-OVON` | official open-vocabulary ObjectNav benchmark path | What split/category mapping is fair for final `SR` / `SPL`? |
| P0 | `GOAT-Bench` | lifelong/multimodal repeated-goal pressure | Can H001 claim reusable memory without GOAT-style tasks? |
| P0 | `HOV-SG` | hierarchy and graph search pressure | Can hierarchy solve source-gap better than H001? |
| P0 | `ConceptGraphs` | already integrated external map baseline | Which H001 failures are repaired by map fallback? |
| P0 | `Open3DSG` | bounded scene-graph external row exists | Is H001 stronger than scene-graph object candidates? |
| P0 | `DualMap` | direct dynamic open-vocabulary mapping baseline | Does global/local map already solve our stale-memory story? |
| P0 | `DynaMem` | dynamic memory in real robot manipulation | How should memory update/remove stale points? |
| P0 | `OpenIN` | moved-instance / carrier relationship | Should H001 add carrier/support priors? |
| P0 | `3D-Mem` | scene memory benchmark with GOAT/A-EQA eval | Can memory hierarchy become our stronger baseline? |
| P0 | `SCOUT` | uncertainty-guided traversal | How to choose re-observation/source coverage without target leakage? |
| P0 | `Remember with Confidence` | probabilistic memory confidence | Can E008-M137 use confidence intervals/bands? |
| P0 | `Uncertainty-Informed Active Perception for OV ObjectNav` | active perception for open-vocabulary navigation | What is the correct uncertainty metric for re-observation? |
| P0 | `RAVEN` | behavior-tree semantic memory switching | Should H001 become a behavior selector, not one score? |
| P1 | `Open Scene Graphs` | open-world object-goal scene memory | What OSG schema is a stronger structured-map baseline? |
| P1 | `Graph2Nav` | relation graph improves search efficiency | Which relation edges reduce search cost? |
| P1 | `OVAL` | augmented memory for lifelong ObjectNav | What memory augmentation is missing in H001? |
| P1 | `ConsistNav` | semantic executive control | Can executive consistency prevent confidence/path flips? |
| P1 | `DRIVE-Nav` | inspection and verification | Should E008-M137 include verify-before-commit? |
| P1 | `R2F` | ray frontier without LLM | Can source coverage use ray-frontier instead of target-aware geometry? |
| P1 | `PSG-Nav` | probabilistic scene graph decisions | Is H001 a probabilistic decision problem? |
| P1 | `MORN` | metacognitive regulation | Can a budget/risk controller explain method form? |
| P1 | `BEACON` | occlusion-aware affordance | Does occlusion explain source-gap failures? |
| P1 | `OVI-MAP` | instance-semantic separation | Should proposal confidence and instance memory be decoupled? |
| P1 | `OGScene3D` | temporal confidence graph update | Can temporal graph confidence support stale-memory update? |

## GitHub Code Audit

사실:

- Code audit clones are stored under `local_dataset/external_repos/literature_audit/`; this path is ignored by git.
- Existing external clones also exist under `local_dataset/external_repos/`.
- No model checkpoints or datasets were downloaded in this refresh.

| Codebase | Local status | Commit | Immediate usable interface | Integration burden |
| --- | --- | --- | --- | --- |
| `vlfm` | shallow cloned | `584ed56` | `vlfm/run.py`, `Habitat` eval, GroundingDINO/MobileSAM weights | high: separate detector/frontier stack, but strong `SPL` baseline |
| `HOV-SG` | shallow cloned | `d6e65a5` | `application/create_graph.py`, `visualize_query_graph.py`, HM3DSem graph eval | high: OpenCLIP/SAM/HM3DSem setup, useful for source-gap baseline |
| `3D-Mem` | shallow cloned | `f445e08` | `run_goatbench_evaluation.py`, `src/tsdf_planner.py`, memory snapshots | medium-high: good memory baseline, may require GOAT/A-EQA data |
| `ovon` | shallow cloned | `8300fcc` | `ovon/run.py`, HM3D-OVON eval | medium: benchmark alignment, not a method baseline by itself |
| `goat-bench` | shallow cloned | `74c41d1` | `goat_bench/run.py`, sequential goal task | high: lifelong eval setup, strong top-tier pressure |
| `DualMap` | shallow cloned | `157235e` | `applications/runner_dataset.py`, `offline_local_map_query.py`, dynamic navigation docs | high: previous runtime produced no object `*.pkl`; useful as reviewer defense and future retry only |
| `foundation_obj_nav` / `OSG Navigator` | shallow cloned | `32bec00` | `scene_graph.py`, `objnav_evaluate.py`, `navigate_homerobot.py` | medium-high: scene graph baseline for open-world ObjectNav |
| `concept-graphs` | existing clone | `93277a0` | object candidate export already adapted in E005/E008 | already integrated but source-gap performance is weak on current cases |
| `Grounded-Segment-Anything` | existing clone | `a4d76a2` | detector/proposal route already used via E003/E005/E008 | already integrated as real RGB-D proposal path, false-positive burden remains |

에이전트 추론:

- Immediate E008-M137 should not attempt a full `VLFM` or `HOV-SG` reproduction. Their value now is method pressure: they show that `SPL`-strong baselines preserve confidence/frontier value and use path only through navigation execution or frontier selection.
- `3D-Mem`, `DynaMem`, and `Remember with Confidence` suggest H001 should expose memory confidence as a calibrated decision state, not a raw heuristic score.
- `OSG Navigator`, `HOV-SG`, and `ConceptGraphs` suggest external map candidates should be used as conditional fallback/source-expansion, not merged unconditionally with H001 candidates.

## Cross-Paper Relation Map

### Axis 1. Representation

사실:

- Dense feature maps: `VLMaps`, `CLIP-Fields`, `LangSplat`, `OpenScene`, `O2V-Mapping`.
- Object/graph maps: `ConceptGraphs`, `Open3DSG`, `HOV-SG`, `Open Scene Graphs`, `OpenMap`, `OVI-MAP`.
- Dynamic memory maps: `DualMap`, `DynaMem`, `OpenIN`, `DovSG`, `OGScene3D`.

에이전트 추론:

- H001 should be positioned as a decision layer over object-centric semantic memory, not as a new detector or dense map.

### Axis 2. Decision Policy

사실:

- `VLFM` and `R2F` emphasize frontier/value search.
- `RAVEN` emphasizes behavior switching between semantic voxel search, ray search, LVLM auxiliary reasoning, and frontier exploration.
- `DRIVE-Nav`, `ConsistNav`, and `MORN` emphasize verification, executive control, or metacognitive regulation.

에이전트 추론:

- E008-M137 should become a small policy controller with guarded modes, not a single scalar ranker.

### Axis 3. Evaluation Pressure

사실:

- `HM3D-OVON`, `GOAT-Bench`, and `VLFM` pressure H001 through `SR` / `SPL`.
- `ConceptGraphs`, `HOV-SG`, `Open3DSG`, and `Open Scene Graphs` pressure H001 through map-to-candidate quality.
- `DynaMem`, `DualMap`, and `OpenIN` pressure H001 through dynamic update and stale-object handling.

에이전트 추론:

- A top-tier paper cannot rely on proxy `ExpectedSearchCost` only. It needs at least one paper-facing bridge table plus a credible route to executed `SR` / `SPL`.

## Seven Integration Proposals

### Proposal 1. Confidence-Preserving Trajectory Tie-Break

논문 주장 후보:

- Path/trajectory cost should not replace detector or map confidence; it should only reorder candidates inside a confidence band.

Method form:

- Sort by source confidence first.
- Define confidence bands using absolute threshold or quantile gap.
- Apply trajectory cost only within the active band.
- Never demote the top confidence candidate below a low-confidence candidate unless a hard feasibility veto fires.

Metric:

- `SPL` vs detector-confidence baseline, `SR`, rank-flip count, confidence-band violation count.

Failure teaches:

- If it still loses `SPL`, then H001's issue is not path-cost dominance but candidate-source quality or trajectory execution mismatch.

### Proposal 2. Hard Feasibility Veto, Not Soft Path Penalty

논문 주장 후보:

- Reachability/path evidence is reliable when it blocks impossible candidates, but unreliable as a fine-grained preference signal across semantically plausible candidates.

Method form:

- Use navmesh/path check as `reachable`, `unreachable`, `snap_failed`, or `source_gap`.
- Veto unreachable candidates.
- Do not continuously penalize path length unless confidence tie remains.

Metric:

- unreachable top-k rate, `SPL`, path-ready retained target rate, false veto rate.

Failure teaches:

- If false veto is high, coordinate/snap/source alignment is the dominant bottleneck.

### Proposal 3. Source-Coverage Before Ranking

논문 주장 후보:

- Some failures are not ranking failures; they are source-coverage failures where the target region was never observed from a useful viewpoint.

Method form:

- Add a source-ready/source-gap classifier before candidate ranking.
- If source-gap, trigger target-free source expansion using frontier/ray/visibility policies.
- If source-ready, run confidence-preserving ranking.

Metric:

- source-gap recovery, detector candidate target presence, proxy recovery, executed `SR` / `SPL`.

Failure teaches:

- If source expansion does not create candidates, current detector/proposal stack is the bottleneck.

### Proposal 4. External Map Fallback As Conditional Source, Not Ensemble

논문 주장 후보:

- External maps help when H001 memory/proposal evidence fails, but naive ensembling can increase false positives and path cost.

Method form:

- H001 primary candidates remain first.
- `ConceptGraphs` / `HOV-SG` / `Open3DSG` candidates enter only after observed miss, source-gap, or low-confidence band.
- External candidates must pass same navmesh/source-readiness and leakage-safe goal-evaluation gates.

Metric:

- H001-only failure recovery, added cost per recovered query, false-positive injection rate.

Failure teaches:

- If external fallback fails, top-tier claim should be H001 vs external map diagnostic rather than system superiority.

### Proposal 5. Calibrated Memory Trust

논문 주장 후보:

- Stale semantic memory should expose calibrated trust, not binary old/current memory choice.

Method form:

- Store memory confidence with uncertainty terms: age/staleness, observation support, source confidence, object persistence, relation support.
- Use confidence intervals or conservative lower bounds for trust decisions.

Metric:

- calibration error, stale false-positive rate, recall retained, confidence-band ablation.

Failure teaches:

- If calibration is poor, the novelty shifts from policy to uncertainty estimation or data quality.

### Proposal 6. Human Intent As Utility Profile, Not Main Rank Signal

논문 주장 후보:

- Human task context should affect memory trust only through utility/risk/budget profiles unless stronger evidence beats context-agnostic baselines.

Method form:

- Keep structured task context as a profile: `risk_of_stale_fp`, `cost_of_miss`, `reobserve_budget`, `allowed_delay`.
- Apply it after confidence and feasibility gates.
- Do not let task profile directly override strong evidence.

Metric:

- `ContextSpecificGain`, `IntentRegret`, transfer by label/scan/task group.

Failure teaches:

- If context remains weak, paper should not claim human intent as main contribution.

### Proposal 7. Failure-Typed Policy Router

논문 주장 후보:

- Dynamic open-vocabulary search fails by different mechanisms; a single score cannot handle stale FP, source gap, detector recall miss, path mismatch, and occlusion.

Method form:

- Route each query/case into one of: `confidence_rank`, `feasibility_veto`, `source_expansion`, `external_map_fallback`, `reobserve`, `stop_and_report_uncertain`.
- Each route has allowed inputs and a primary metric.

Metric:

- per-failure-type success, route confusion, cost per recovery, reviewer-facing failure taxonomy.

Failure teaches:

- If router decisions are unstable, method is heuristic stacking and needs a simpler principle.

## Three Orthogonal Persona Reviews

### Persona A. Semantic Mapping / CV Reviewer

사실:

- The field has many open-vocabulary maps and 3D scene graph systems.
- H001 currently does not introduce a new detector, point cloud representation, or graph backbone.

에이전트 추론:

- Integration is possible if H001 is framed as a semantic memory decision layer that exposes calibrated trust, stale status, source readiness, and re-observation need.
- It is weak if written as "we combine detector confidence, path cost, and task context."

Required defense:

- Show why static memory, fixed decay, detector-confidence ranking, and external map fallback fail on different cases.

### Persona B. Embodied Navigation / Robotics Reviewer

사실:

- Current E008 evidence has `SR` smoke but selected H001 repair loses `SPL` to detector-confidence.
- `VLFM`, `HM3D-OVON`, `GOAT-Bench`, `RAVEN`, and `OSG Navigator` create strong navigation pressure.

에이전트 추론:

- Integration is possible only if E008-M137 preserves detector-confidence `SPL` while adding recovery or reducing failure cost.
- If E008-M137 cannot beat or tie confidence baseline, navigation claim should remain diagnostic.

Required defense:

- Same start states, same candidates or explicitly fair candidate source, same `SR` / `SPL`, source-gap split, and no eval-goal leakage.

### Persona C. ML / Uncertainty / Systems Reviewer

사실:

- Current H001 policy has many route decisions and risk of appearing heuristic.
- `Remember with Confidence`, probabilistic scene graph navigation, and active perception papers pressure uncertainty handling.

에이전트 추론:

- Integration is possible if E008-M137 has precommitted gates: confidence band, hard veto, tie-break, source-gap trigger, and ablation.
- The method is weak if thresholds are tuned posthoc on the one target-free case.

Required defense:

- Predefine thresholds or calibration source, run ablations, report failure cases, and keep Docker/reproducibility contracts.

## Recommendation For E008-M137

에이전트 추론:

E008-M137 should implement a contract, not a new broad experiment:

1. Keep detector-confidence / confidence-only as the protected baseline.
2. Define confidence bands before looking at new outcomes.
3. Apply trajectory cost only as tie-break inside a confidence band.
4. Use hard feasibility veto only for unreachable/snap-failed candidates.
5. Add source-gap route before ranking, but do not claim recovery until source expansion creates target candidates.
6. Keep human intent as profile/budget metadata unless E006-M09 is explicitly restarted.
7. Predefine pass/warning/fail:
   - pass: `SR` ties confidence baseline and `SPL` improves or no worse within tolerance while recovering extra cases
   - warning: `SR` ties but `SPL` slightly worse with diagnosable recovery
   - fail: `SPL` remains far below confidence baseline or confidence top candidate is demoted without hard veto

## Follow-Up Reading Actions

- Promote `Remember with Confidence`, `SCOUT`, `RAVEN`, `Uncertainty-Informed Active Perception for OV ObjectNav`, and `DynaMem` to individual paper folders if E008-M137 uses uncertainty/source-coverage language.
- Promote `VLFM`, `HOV-SG`, `3D-Mem`, `HM3D-OVON`, and `GOAT-Bench` to updated deep-read cards before final paper claim.
- Do not create a paper folder yet. This refresh supports experiment design and reviewer defense, not a final draft.

## Key Primary Links

- `VLFM`: https://arxiv.org/abs/2312.03275, https://github.com/rai-opensource/vlfm
- `HOV-SG`: https://arxiv.org/abs/2403.17846, https://github.com/hovsg/HOV-SG
- `HM3D-OVON`: https://arxiv.org/abs/2409.14296, https://github.com/naokiyokoyama/ovon
- `GOAT-Bench`: https://arxiv.org/abs/2404.06609, https://github.com/Ram81/goat-bench
- `DualMap`: https://arxiv.org/abs/2506.01950, https://github.com/Eku127/DualMap
- `DynaMem`: https://dynamem.github.io/, https://arxiv.org/abs/2411.04999
- `OpenIN`: https://arxiv.org/abs/2501.04279, https://openin-nav.github.io/
- `Open Scene Graphs`: https://open-scene-graphs.github.io/
- `3D-Mem`: https://umass-embodied-agi.github.io/3D-Mem/, https://github.com/UMass-Embodied-AGI/3D-Mem
- `ConceptGraphs`: https://concept-graphs.github.io/
- `DovSG`: https://arxiv.org/abs/2410.11989, https://github.com/BJHYZJ/DovSG
- `RAVEN`: https://raven-semantic.github.io/
