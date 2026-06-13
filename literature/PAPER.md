# Paper Registry

Updated: 2026-06-09

## Paper Registry

| Paper | Year | Venue / status | Folder | Status | Why it matters |
| --- | --- | --- | --- | --- | --- |
| VLFM: Vision-Language Frontier Maps for Zero-Shot Semantic Navigation | 2024 | ICRA | [2024_icra_vlfm](2024_icra_vlfm/README.md) | Skimmed | language-conditioned frontier map for ObjectNav |
| ConceptGraphs: Open-Vocabulary 3D Scene Graphs for Perception and Planning | 2024 | ICRA | [2024_icra_conceptgraphs](2024_icra_conceptgraphs/README.md) | Read | object-centric scene graph as map-reasoning interface |
| Open3DSG: Open-Vocabulary 3D Scene Graphs from Point Clouds with Queryable Objects and Open-Set Relationships | 2024 | CVPR | [2024_cvpr_open3dsg](2024_cvpr_open3dsg/README.md) | Skimmed | open-set object and relation labels |
| LangSplat / Language Embedded 3D Gaussians for Open-Vocabulary Scene Understanding | 2024 | CVPR | [2024_cvpr_langsplat](2024_cvpr_langsplat/README.md) | Skimmed | efficient language-embedded Gaussian map |
| EmbodiedScan | 2024 | CVPR | [2024_cvpr_embodiedscan](2024_cvpr_embodiedscan/README.md) | Skimmed | embodied 3D perception benchmark substrate |
| OpenEQA | 2024 | CVPR | [2024_cvpr_openeqa](2024_cvpr_openeqa/README.md) | Skimmed | human-facing embodied QA evaluation |
| GOAT-Bench | 2024 | CVPR | [2024_cvpr_goat-bench](2024_cvpr_goat-bench/README.md) | Skimmed | multimodal lifelong navigation benchmark |
| O2V-Mapping | 2024 | ECCV | [2024_eccv_o2v-mapping](2024_eccv_o2v-mapping/README.md) | Read | online open-vocabulary mapping baseline |
| HOV-SG | 2024 | RSS | [2024_rss_hov-sg](2024_rss_hov-sg/README.md) | Read | hierarchical scene graph for language navigation |
| Clio | 2024 | arXiv / RSS workshop lineage | [2024_arxiv_clio](2024_arxiv_clio/README.md) | Read | task-driven open-set map granularity |
| RoboHop | 2024 | arXiv | [2024_arxiv_robohop](2024_arxiv_robohop/README.md) | Queued | segment-based topological semantic map |
| HM3D-OVON | 2024 | arXiv | [2024_arxiv_hm3d-ovon](2024_arxiv_hm3d-ovon/README.md) | Skimmed | open-vocabulary ObjectNav benchmark |
| One Map to Find Them All | 2024 | arXiv | [2024_arxiv_one-map](2024_arxiv_one-map/README.md) | Skimmed | reusable open-vocabulary map for multi-object navigation |
| OpenGraph | 2024 | arXiv | [2024_arxiv_opengraph](2024_arxiv_opengraph/README.md) | Queued | large-scale outdoor open-vocabulary graph |
| Open-Vocabulary Mobile Manipulation with 3D Semantic Maps | 2024 | arXiv | [2024_arxiv_ovmm-3d-semantic-maps](2024_arxiv_ovmm-3d-semantic-maps/README.md) | Skimmed | connects semantic map to manipulation |
| OVO-SLAM | 2024 | arXiv / RA-L 2025 status reported by authors | [2024_arxiv_ovo-slam](2024_arxiv_ovo-slam/README.md) | Queued | online semantic SLAM assumption check |
| DualMap | 2025 | RA-L / arXiv | [2025_ral_dualmap](2025_ral_dualmap/README.md) | Read | dynamic language navigation with global/local maps |
| FindAnything | 2025 | arXiv | [2025_arxiv_findanything](2025_arxiv_findanything/README.md) | Skimmed | object-centric resource-aware exploration |
| OpenIN | 2025 | arXiv | [2025_arxiv_openin](2025_arxiv_openin/README.md) | Read | moved-instance navigation with Carrier-Relationship Scene Graph |
| OpenMap | 2025 | ACM MM | [2025_acmmm_openmap](2025_acmmm_openmap/README.md) | Read | instruction grounding via instance-level visual-language map |
| Open-Vocabulary Functional 3D Scene Graphs | 2025 | CVPR | [2025_cvpr_openfungraph](2025_cvpr_openfungraph/README.md) | Read | functional relation map for QA/manipulation |
| Open-Vocabulary Octree-Graph | 2025 | ICCV | [2025_iccv_octree-graph](2025_iccv_octree-graph/README.md) | Skimmed | occupancy + relation-aware compact representation |
| 3D-Mem | 2025 | CVPR | [2025_cvpr_3d-mem](2025_cvpr_3d-mem/README.md) | Queued | scene memory for embodied reasoning |
| osmAG-LLM | 2025 | arXiv | [2025_arxiv_osmag-llm](2025_arxiv_osmag-llm/README.md) | Queued | semantic map plus LLM reasoning for static/moved/unmapped objects |
| LangMap | 2026 | arXiv | [2026_arxiv_langmap](2026_arxiv_langmap/README.md) | Read | hierarchical open-vocabulary goal navigation benchmark |
| OVI-MAP | 2026 | arXiv | [2026_arxiv_ovi-map](2026_arxiv_ovi-map/README.md) | Read | open-vocabulary instance-semantic mapping |
| OGScene3D | 2026 | arXiv | [2026_arxiv_ogscene3d](2026_arxiv_ogscene3d/README.md) | Read | incremental Gaussian scene graph with temporal memory |
| Scene Graph Backed Open Set Semantic Mapping | 2026 | arXiv | [2026_arxiv_scene-graph-backed-semantic-mapping](2026_arxiv_scene-graph-backed-semantic-mapping/README.md) | Queued | graph as semantic map backend |

## Reading Queue

| Priority | Paper / topic | Status | Next action |
| --- | --- | --- | --- |
| P0 | E008-M137 top-tier targeted refresh | First pass complete | Use [CAND-001_top-tier-refresh-2026.md](CAND-001_top-tier-refresh-2026.md) to design confidence-preserving trajectory repair |
| P0 | `Remember with Confidence` + `SCOUT` + `RAVEN` + uncertainty/active-perception papers | Queued | Promote to paper folders if E008-M137 uses uncertainty/source-coverage language |
| P0 | `VLFM` + `HM3D-OVON` + `GOAT-Bench` + `HOV-SG` + `3D-Mem` | Queued | Update deep-read cards before any final navigation `SR` / `SPL` claim |
| P0 | DualMap + OpenIN + OGScene3D | In progress | Extract dynamic-memory metrics and baselines |
| P0 | Clio + HOV-SG + LangMap | In progress | Compare granularity/hierarchy assumptions |
| P1 | OpenMap + Open-Vocabulary Functional 3D Scene Graphs | Pending | Check whether instruction/function can be combined with staleness |
| P1 | 3D-Mem + FindAnything | Pending | Compare memory representation and efficiency story |
| P2 | RoboHop + OpenGraph + OVO-SLAM | Pending | Decide whether topological/SLAM issues belong in first thesis scope |

## Source Notes

확인일: 2026-06-09.

Primary sources used include arXiv, CVF Open Access, OpenReview, official project pages, and official code/project pages where available. The 2026-06-09 targeted refresh additionally used arXiv API metadata and shallow/filter GitHub clone inspection under `local_dataset/external_repos/literature_audit/`. Items marked `Queued` are not yet strong enough to support a contribution claim.
