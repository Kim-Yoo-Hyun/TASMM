# Reproducibility Notes

Updated: 2026-05-22

이 문서는 현재 repo에서 실험을 다시 실행하기 위해 필요한 데이터 위치, 다운로드 명령, checkpoint 위치, Docker 실행법, 재현 명령, artifact/evaluation 요약을 한 곳에 모은다. 세부 workflow 규칙은 `docs/experiments.md`를 따른다.

## Current Scope

사실:

- Active experiment route: `experiments/E005_external_baseline_transition/`.
- Active external baseline: `ConceptGraphs`.
- Docker image: `research2/conceptgraphs-smoke:latest`.
- Current heldout state: `heldout_b01/b02/b03` runtime/metric conversion and full 9-scan aggregation are complete.
- Current claim state: E005-M59 failed on CUDA OOM and still keeps final real RGB-D/open-vocabulary robustness false. E005-M56 fixes separate proxy-search / real RGB-D proposal denominators, E005-M57/M58 define the `Open3DSG` conversion/export contracts, E005-M59 attempts one-batch object candidate export while using `/home/yoohyun/research/local_dataset/Open3DSG_staged` as a read-only source, and E005-M60 predefines the query-level conversion contract for the 195-row M38/M45 denominator. Derived `Open3DSG` bridge outputs are stored under `/home/yoohyun/research2/local_dataset/Open3DSG_bridge/`.

## Data Location

사실:

- Repo root: `/home/yoohyun/research2`.
- Dataset root: `/home/yoohyun/research2/local_dataset`.
- `3RScan` scans: `local_dataset/3RScan/scans/`.
- `3RScan` metadata: `local_dataset/3RScan/files/3RScan.json`.
- `3DSSG` annotations: `local_dataset/3DSSG/objects.json`, `local_dataset/3DSSG/relationships.json`.
- `3DSSG_subset`: `local_dataset/3DSSG_subset/`.
- `ConceptGraphs` staged RGB-D layout: `local_dataset/ConceptGraphs_staged/3rscan_depth_aligned_scannet/`.
- `ConceptGraphs` model cache: `local_dataset/ConceptGraphs_model_cache/`.
- External repos: `local_dataset/external_repos/concept-graphs/`, `local_dataset/external_repos/Grounded-Segment-Anything/`.
- Existing `Open3DSG` staged path from another research workspace: `/home/yoohyun/research/local_dataset/Open3DSG_staged`. Use read-only for audit/conversion planning; do not write artifacts there.
- Derived `Open3DSG` bridge outputs: `local_dataset/Open3DSG_bridge/`.

## Data Download Commands

사실:

`3RScan` sequence payloads can be fetched with the heldout acquisition launcher:

```bash
python experiments/E005_external_baseline_transition/tools/launch_m39_conceptgraphs_heldout_sequence.py
python experiments/E003_perception_noise_expansion/tools/verify_m56_sequence_payloads.py \
  --manifest experiments/E005_external_baseline_transition/artifacts/E005-M39_conceptgraphs_heldout_sequence_launch_v0/download_manifest.jsonl \
  --out-dir experiments/E005_external_baseline_transition/artifacts/E005-M39_conceptgraphs_heldout_sequence_launch_v0/verification \
  --require-ready
```

Per-scan fallback command:

```bash
wget -c -O local_dataset/3RScan/scans/<scan_id>/sequence.zip \
  http://campar.in.tum.de/public_datasets/3RScan/Dataset/<scan_id>/sequence.zip
unzip -n local_dataset/3RScan/scans/<scan_id>/sequence.zip \
  -d local_dataset/3RScan/scans/<scan_id>/sequence
```

Official local script fallback:

```bash
python local_dataset/3RScan/download_3rscan.py \
  -o local_dataset/3RScan/scans --id <scan_id> --type sequence.zip
```

## Checkpoints

사실:

- SAM checkpoint source: `local_dataset/checkpoints/openmask3d/sam_vit_h_4b8939.pth`.
- SAM checkpoint used by `ConceptGraphs`: `local_dataset/ConceptGraphs_model_cache/gsa/sam_vit_h_4b8939.pth`.
- `GroundingDINO` checkpoint: `local_dataset/ConceptGraphs_model_cache/gsa/groundingdino_swint_ogc.pth`.
- Hugging Face / CLIP cache: `local_dataset/ConceptGraphs_model_cache/huggingface/`.

Checkpoint acquisition command:

```bash
python experiments/E005_external_baseline_transition/tools/launch_m23_conceptgraphs_acquisition.py
python experiments/E005_external_baseline_transition/tools/verify_m23_conceptgraphs_acquisition.py
```

Manual `GroundingDINO` fallback:

```bash
wget -c -O local_dataset/ConceptGraphs_model_cache/gsa/groundingdino_swint_ogc.pth \
  https://github.com/IDEA-Research/GroundingDINO/releases/download/v0.1.0-alpha/groundingdino_swint_ogc.pth
```

## Environment Setup

사실:

- Required host tools: `python3`, `docker`, NVIDIA Docker runtime, `nvidia-smi`, `tmux`, `wget`, `unzip`.
- Paper-body external baseline execution uses Docker.
- Repository-local JSON/JSONL planning and aggregation scripts run with host Python.

Build and verify the current `ConceptGraphs` image:

```bash
python experiments/E005_external_baseline_transition/tools/launch_m25_conceptgraphs_docker_build.py
python experiments/E005_external_baseline_transition/tools/verify_m25_conceptgraphs_docker_build.py
```

Direct Docker build command:

```bash
docker build --progress=plain \
  -t research2/conceptgraphs-smoke:latest \
  --build-arg CONCEPTGRAPHS_COMMIT=93277a02bd89171f8121e84203121cf7af9ebb5d \
  --build-arg GSA_COMMIT=a4d76a2b55e348943cba4cd57d7553c354296223 \
  -f experiments/E005_external_baseline_transition/docker/conceptgraphs_smoke/Dockerfile \
  experiments/E005_external_baseline_transition/docker/conceptgraphs_smoke
```

## Docker Runtime

사실:

Heldout `ConceptGraphs` runtime batches are launched through a bounded tmux wrapper:

```bash
python experiments/E005_external_baseline_transition/tools/launch_m43_conceptgraphs_heldout_runtime_batch.py --batch-id heldout_b01
python experiments/E005_external_baseline_transition/tools/verify_m43_conceptgraphs_heldout_runtime_batch.py --batch-id heldout_b01
```

For reproducing `heldout_b03`:

```bash
python experiments/E005_external_baseline_transition/tools/launch_m43_conceptgraphs_heldout_runtime_batch.py --batch-id heldout_b03
python experiments/E005_external_baseline_transition/tools/verify_m43_conceptgraphs_heldout_runtime_batch.py --batch-id heldout_b03
```

Runtime launch preflight requires GPU free memory >= 24GB unless `--ignore-gpu-memory` is explicitly used. The default should remain the 24GB gate because previous `SAM` / `ConceptGraphs` runs were sensitive to GPU memory pressure. `heldout_b03` has already completed, so these commands are reproduction commands, not the current next action.

`Open3DSG` object-candidate export smoke:

```bash
python experiments/E005_external_baseline_transition/tools/launch_m59_open3dsg_object_export_smoke.py --launch
python experiments/E005_external_baseline_transition/tools/verify_m59_open3dsg_object_export_smoke.py --require-ready
```

Required source path:

```text
/home/yoohyun/research/local_dataset/Open3DSG_staged
```

Runtime contract:

- Docker image: `h001-open3dsg-repro:cu128`.
- Source mount: `/home/yoohyun/research/local_dataset/Open3DSG_staged:/workspace/local_dataset/Open3DSG_staged:ro`.
- Output path: `local_dataset/Open3DSG_bridge/E005-M59_object_candidate_export_smoke_v0/`.
- Log path: `logs/20260521_044206_e005_m59_open3dsg_object_export.log`.
- Current status as of 2026-05-21 04:59 KST: failed once; lower-memory object-only patch implemented; candidate rows not written; relaunch waits for GPU free memory >= 24GB.
- Object-only repair env: `OPEN3DSG_OBJECT_DUMP_SKIP_BLIP_LOAD=1`, `OPEN3DSG_OBJECT_DUMP_OBJECT_ONLY=1`.
- Default relaunch preflight: `--min-gpu-free-mib 24000`.

## Experiment Reproduction Commands

사실:

Current E005 metric contract and conversion:

```bash
python experiments/E005_external_baseline_transition/tools/plan_m45_conceptgraphs_heldout_metric_contract.py
python experiments/E005_external_baseline_transition/tools/run_m45_conceptgraphs_heldout_query_metrics.py --batch-id heldout_b01
python experiments/E005_external_baseline_transition/tools/run_m45_conceptgraphs_heldout_query_metrics.py --batch-id heldout_b02
```

Latest ready checks:

```bash
python experiments/E005_external_baseline_transition/tools/verify_m43_conceptgraphs_heldout_runtime_batch.py --batch-id heldout_b02
python -m py_compile \
  experiments/E005_external_baseline_transition/tools/plan_m45_conceptgraphs_heldout_metric_contract.py \
  experiments/E005_external_baseline_transition/tools/run_m45_conceptgraphs_heldout_query_metrics.py
```

`Open3DSG` query-conversion contract reproduction:

```bash
python experiments/E005_external_baseline_transition/tools/plan_m60_open3dsg_query_conversion_contract.py
python experiments/E005_external_baseline_transition/tools/verify_m60_open3dsg_query_conversion_contract.py
```

## Artifact And Evaluation Summary

사실:

| Artifact | Scope | Key result | Claim status |
| --- | --- | --- | --- |
| `E003-M75_expanded_direct_query_bridge_v0` | real RGB-D/open-vocabulary bridge, 96 query rows | target detected 87 / 96; `detector_task_budget_v0` success 13 / 96; bounded repair success 33 / 96 | diagnostic only |
| `E004-M05_scale_split_stress_v0` | task-context memory trust split stress, 96 rows | memory-trust claim `split_supported`; task-context claim `limited_positive_not_label_broad` | limited positive |
| `E005-M35_conceptgraphs_4scan_query_metric_v0` | 4 staged `ConceptGraphs` scans | strict bbox top5 3 / 7 on primary `M60`; expanded `M73` strict bbox top5 57 / 96 | small-subset baseline diagnostic |
| `E005-M45_conceptgraphs_heldout_query_metric_v0` / `heldout_b01` | 3 heldout scans, 66 / 195 heldout query rows | strict bbox top5 45 / 66 = 0.681818; relaxed bbox 1m top3 57 / 66 = 0.863636 | batch diagnostic |
| `E005-M45_conceptgraphs_heldout_query_metric_v0` / `heldout_b02` | 3 heldout scans, 69 / 195 heldout query rows | strict bbox top5 45 / 69 = 0.652174; relaxed bbox 1m top3 51 / 69 = 0.739130 | batch diagnostic |
| `E005-M49_conceptgraphs_full_heldout_aggregation_v0` | 9 heldout scans, 195 query rows | strict bbox top5 114 / 195 = 0.584615; relaxed bbox 1m top3 144 / 195 = 0.738462 | external map baseline ready for proxy-search comparison |
| `E005-M54_paper_table_claim_ledger_v0` | 195 query rows | H001 172 / 195; `ConceptGraphs` 114 / 195; context-agnostic 171 / 195 | proxy-search claim ready; human task context main claim false |
| `E005-M55_real_rgbd_ov_robustness_gate_v0` | robustness expansion gate | selected `robustness_denominator_contract_then_open3dsg_audit` | final real RGB-D/open-vocabulary robustness still false |
| `E005-M56_robustness_denominator_open3dsg_audit_v0` | denominator + `Open3DSG` audit | proxy-search denominator 195 rows; real RGB-D proposal bridge denominator 96 rows; `Open3DSG_staged` source/checkpoints/features/eval present | `Open3DSG` query-level performance still false |
| `E005-M57_open3dsg_output_schema_contract_v0` | `Open3DSG` schema / conversion contract | relation raw dump ready; feature `.pt` route ready; object candidate dump false; local data output under `local_dataset/Open3DSG_bridge/E005-M57_output_schema_contract_v0/` | object-search baseline still false |
| `E005-M58_object_candidate_export_plan_v0` | `Open3DSG` object-candidate export plan | object-candidate schema, query-candidate schema, export hook contract, read-only Docker command contract, and verifier ready; local data output under `local_dataset/Open3DSG_bridge/E005-M58_object_candidate_export_plan_v0/` | one-batch export still false |
| `E005-M59_object_candidate_export_smoke_v0` | `Open3DSG` one-batch object-candidate export | launched once in tmux `e005_m59_open3dsg_object_export`; log `logs/20260521_044206_e005_m59_open3dsg_object_export.log`; output path `local_dataset/Open3DSG_bridge/E005-M59_object_candidate_export_smoke_v0/`; candidate rows 0 as of 2026-05-21 04:59 KST; lower-memory object-only patch implemented after CUDA OOM | needs relaunch; no `Open3DSG` performance claim |
| `E005-M60_open3dsg_query_conversion_contract_v0` | `Open3DSG` query-level conversion contract | M38/M45 denominator 195 rows, M58 schemas ready, M59 candidate rows 0, join/leakage/metric contract fixed under `local_dataset/Open3DSG_bridge/E005-M60_query_conversion_contract_v0/` | contract ready; no `Open3DSG` performance claim |

논문 주장:

- Current evidence supports proxy-search comparison against a full heldout `ConceptGraphs` external map baseline.
- It does not yet support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

## Next Reproduction Gate

사실:

- Relaunch E005-M59 `Open3DSG` object-candidate export hook implementation / one-batch Docker smoke when GPU free memory is >= 24GB.
- Preferred repair route: lower-memory runtime patch that avoids unnecessary `InstructBLIP` GPU loading for object-candidate export.
- Backup repair route: GPU-exclusive relaunch if the lower-memory patch still fails.
- Keep `OpenMask3D` as a later proposal baseline until its Docker/`MinkowskiEngine` blocker is worth revisiting.

## Git Tracking Boundary

사실:

- `.gitignore` intentionally excludes `local_dataset/`, `**/artifacts/`, `*.log`, and `*.jsonl`.
- Therefore raw datasets, generated bridge outputs, heavy artifacts, logs, and row-level JSONL files do not go to GitHub.
- Reproduction-critical scripts and docs are not ignored: `experiments/E005_external_baseline_transition/tools/launch_m59_open3dsg_object_export_smoke.py`, `m59_open3dsg_object_dump_runtime_patch.py`, `verify_m59_open3dsg_object_export_smoke.py`, `README.md`, `TODO.md`, and this document are visible to git.

에이전트 추론:

- The current `.gitignore` is acceptable for keeping large/local data out of GitHub, but key result summaries, exact commands, expected paths, and verification commands must stay in tracked Markdown files because result payloads and logs are ignored.

## Ignored Payload Classification

사실:

The following files and directories are intentionally blocked from GitHub by `.gitignore`, Docker image storage, or local-only workspace rules.

### Preserve In Drive Or External Storage

| Payload | Why preserve | Preservation action |
| --- | --- | --- |
| `local_dataset/3RScan/`, `local_dataset/3DSSG/`, `local_dataset/3DSSG_subset/` | Raw dataset/source annotation versions affect every split and metric. Re-download may require credentials, terms, or unavailable mirrors. | Preserve in a private Drive/external disk only if license permits. Otherwise preserve only download credentials, manifest, and expected layout outside Git. |
| `/home/yoohyun/research/local_dataset/Open3DSG_staged/` | This is a read-only source from another research workspace, not generated by this repo. Current `Open3DSG` feasibility depends on its source, checkpoints, features, and existing eval artifacts. | Preserve externally or keep the original workspace intact. Do not write derived files there. |
| `h001-open3dsg-repro:cu128` Docker image | The current repo does not contain a confirmed Dockerfile/build recipe for this exact image. E005-M59 depends on it. | Save the image if `Open3DSG` remains part of the paper route: `docker save h001-open3dsg-repro:cu128 \| gzip > <drive>/docker/h001-open3dsg-repro_cu128_20260521.tar.gz`. Verify after restore with `gunzip -c <tar.gz> \| docker load` and `docker image inspect h001-open3dsg-repro:cu128`. |
| `local_dataset/checkpoints/openmask3d/`, `local_dataset/ConceptGraphs_model_cache/gsa/` | Checkpoints are usually downloadable, but URLs/permissions can change and failed downloads block reproduction. | Preserve when storage allows. Also keep acquisition commands below so this remains regenerable if sources are available. |
| `.env`, `.env.*`, API tokens, dataset credentials | Required for some downloads but should never be committed. | Preserve in a private password manager or secure Drive note, not in Git. |

### Regenerable From Repo Commands

The payloads below are intentionally ignored but can be regenerated when raw data, checkpoints, and required Docker images are available.

| Payload | Regeneration command | Verification command |
| --- | --- | --- |
| `local_dataset/external_repos/concept-graphs/`, `local_dataset/external_repos/Grounded-Segment-Anything/`, `ConceptGraphs` checkpoints | `python experiments/E005_external_baseline_transition/tools/launch_m23_conceptgraphs_acquisition.py` | `python experiments/E005_external_baseline_transition/tools/verify_m23_conceptgraphs_acquisition.py` |
| `research2/conceptgraphs-smoke:latest` | `python experiments/E005_external_baseline_transition/tools/launch_m25_conceptgraphs_docker_build.py` | `python experiments/E005_external_baseline_transition/tools/verify_m25_conceptgraphs_docker_build.py` |
| `research2/real-smoke:latest` | `python experiments/E003_perception_noise_expansion/tools/run_m18_real_proposal_scaffold.py --build --smoke-run --docker-sudo --sudo-password-stdin` | `docker image inspect research2/real-smoke:latest` |
| `local_dataset/ConceptGraphs_staged/3rscan_depth_aligned_scannet/` | `python experiments/E005_external_baseline_transition/tools/materialize_m42_conceptgraphs_heldout_staging.py` | `python experiments/E005_external_baseline_transition/tools/verify_m40_conceptgraphs_heldout_sequence_staging.py` |
| `ConceptGraphs` heldout runtime outputs | `python experiments/E005_external_baseline_transition/tools/launch_m43_conceptgraphs_heldout_runtime_batch.py --batch-id heldout_b01` and repeat for `heldout_b02`, `heldout_b03` | `python experiments/E005_external_baseline_transition/tools/verify_m43_conceptgraphs_heldout_runtime_batch.py --batch-id heldout_b01` and repeat for each batch |
| `ConceptGraphs` query metrics and full aggregation | `python experiments/E005_external_baseline_transition/tools/run_m45_conceptgraphs_heldout_query_metrics.py --batch-id heldout_b01` and repeat for each batch; then `python experiments/E005_external_baseline_transition/tools/run_m49_conceptgraphs_full_heldout_aggregation.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M49_conceptgraphs_full_heldout_aggregation_v0/coverage.json` and compare summary values in this document |
| H001 heldout policy replay artifacts | `python experiments/E005_external_baseline_transition/tools/plan_m51_h001_heldout_policy_replay_contract.py`; `python experiments/E005_external_baseline_transition/tools/run_m52_h001_heldout_policy_replay.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M52_h001_heldout_policy_replay_v0/coverage.json` |
| `local_dataset/Open3DSG_bridge/E005-M57_output_schema_contract_v0/` | `python experiments/E005_external_baseline_transition/tools/plan_m57_open3dsg_output_schema_contract.py` | Inspect generated `README.md` / `coverage.json` under the output directory |
| `local_dataset/Open3DSG_bridge/E005-M58_object_candidate_export_plan_v0/` | `python experiments/E005_external_baseline_transition/tools/plan_m58_open3dsg_object_candidate_export.py` | `python experiments/E005_external_baseline_transition/tools/verify_m58_open3dsg_object_candidate_export.py` |
| `local_dataset/Open3DSG_bridge/E005-M59_object_candidate_export_smoke_v0/` | `python experiments/E005_external_baseline_transition/tools/launch_m59_open3dsg_object_export_smoke.py --launch` | `python experiments/E005_external_baseline_transition/tools/verify_m59_open3dsg_object_export_smoke.py --require-ready` |
| E003 direct RGB-D bridge outputs | `python experiments/E003_perception_noise_expansion/tools/launch_m74_direct_bridge_denominator_detector.py`; `python experiments/E003_perception_noise_expansion/tools/evaluate_m75_expanded_direct_query_bridge.py` | `python experiments/E003_perception_noise_expansion/tools/verify_m74_direct_bridge_detector_completion.py` |
| `logs/*.log` | Rerun the relevant launcher; logs are operational evidence, not paper artifacts. | Use `tail`, `head`, or targeted `rg` only. Do not print huge logs. |

### Not Regenerable From This Repo Alone

| Payload or state | Reason |
| --- | --- |
| `/home/yoohyun/research/local_dataset/Open3DSG_staged/` | External workspace source. This repo can consume it read-only but cannot recreate it from tracked files. |
| Exact historical `logs/*.log` contents | Logs depend on timestamp, GPU state, process scheduling, package cache state, and failure timing. They are not required if summaries and commands are tracked. |
| Failed tmux/background process state | Session state disappears after reboot and is not a reproducible artifact. |
| Byte-identical Hugging Face / package caches without revision pins | Cache contents can change if upstream files, mirrors, or auth state change. Preserve important checkpoints when a paper result depends on them. |
| Manual labels or human inspection notes not summarized in tracked Markdown | If future manual annotation affects a claim, record the summary and schema in tracked docs or preserve the raw annotation privately. |

사용자 판단 필요:

- Decide whether to export `h001-open3dsg-repro:cu128` to Drive before continuing `Open3DSG` work on another machine.
- Decide whether raw `3RScan` / `3DSSG` data can be stored in Drive under the dataset license. If not, preserve only manifests and acquisition instructions.

## Drive Backup Candidate Paths

사실:

These are concrete local paths checked on 2026-05-21. `Open3DSG_staged` is not under `/home/yoohyun/research2/local_dataset`; it is an external read-only source at `/home/yoohyun/research/local_dataset/Open3DSG_staged`.

### Priority A: Preserve For Continuity

Checkpoint:

- `/home/yoohyun/research/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt`  
  Size: 401 MB. This is the currently referenced `Open3DSG` checkpoint candidate.
- Optional same-run checkpoint folder, if exact checkpoint choice may change:
  `/home/yoohyun/research/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/`

Docker image without confirmed repo-local build recipe:

```bash
docker save h001-open3dsg-repro:cu128 | gzip > <drive>/docker/h001-open3dsg-repro_cu128_20260521.tar.gz
```

Verify after restore:

```bash
gunzip -c <drive>/docker/h001-open3dsg-repro_cu128_20260521.tar.gz | docker load
docker image inspect h001-open3dsg-repro:cu128
```

Core row-level artifacts for current paper-table evidence:

- `experiments/E005_external_baseline_transition/artifacts/E005-M45_conceptgraphs_heldout_query_metric_v0/`  
  Size: 25 MB. Contains `candidate_rows_heldout_b01/b02/b03.jsonl`, `object_rows_heldout_b01/b02/b03.jsonl`, `policy_rows_heldout_b01/b02/b03.jsonl`, `target_rows*.jsonl`, `metrics_heldout_b*.json`, and reports.
- `experiments/E005_external_baseline_transition/artifacts/E005-M49_conceptgraphs_full_heldout_aggregation_v0/`  
  Size: 236 KB. Contains full heldout aggregation rows and metrics.
- `experiments/E005_external_baseline_transition/artifacts/E005-M52_h001_heldout_policy_replay_v0/`  
  Size: 3.5 MB. Contains H001 replay `policy_rows.jsonl`, `comparison_rows.jsonl`, `failure_rows.jsonl`, metrics, and report.
- `experiments/E005_external_baseline_transition/artifacts/E005-M53_paired_failure_table_decision_v0/`  
  Size: 236 KB. Contains paired H001-vs-`ConceptGraphs` failure rows.
- `experiments/E005_external_baseline_transition/artifacts/E005-M54_paper_table_claim_ledger_v0/`  
  Size: 32 KB. Contains `claim_ledger.jsonl`, `paper_table_rows.jsonl`, and paper-table markdown.
- `experiments/E003_perception_noise_expansion/artifacts/E003-M75_expanded_direct_query_bridge_v0/`  
  Size: 1.2 MB. Contains real RGB-D/open-vocabulary bridge rows, policy rows, failure rows, and metrics.

Small but useful `Open3DSG` bridge contracts:

- `local_dataset/Open3DSG_bridge/`  
  Size: 144 KB as of 2026-05-21. Contains M57/M58/M59 schema and launch contracts. It does not yet contain successful M59 candidate rows.
- `experiments/E005_external_baseline_transition/artifacts/E005-M56_robustness_denominator_open3dsg_audit_v0/`
- `experiments/E005_external_baseline_transition/artifacts/E005-M57_open3dsg_output_schema_contract_v0/`
- `experiments/E005_external_baseline_transition/artifacts/E005-M58_object_candidate_export_plan_v0/`

Raw data, if license permits private backup:

- `/home/yoohyun/research2/local_dataset/3RScan/`  
  Size: 2.8 GB.
- `/home/yoohyun/research2/local_dataset/3DSSG/`  
  Size: 34 MB.
- `/home/yoohyun/research2/local_dataset/3DSSG_subset/`  
  Size: 22 MB.

### Priority B: Optional, Large Or Regenerable

Feature `.pt` directories:

- `/home/yoohyun/research/local_dataset/Open3DSG_staged/training_repro/output/features/clip_features_h001_official_blip_top5_scales3/`  
  Size: 131 GB. Backup only if avoiding expensive feature regeneration is more important than Drive space.
- `/home/yoohyun/research/local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3/`  
  Size: 13 GB. Backup is useful if E005-M59/M60 will continue on another machine.

Runtime checkpoints and model caches:

- `/home/yoohyun/research/local_dataset/Open3DSG_staged/h001_runtime/output/checkpoints/`  
  Size: 1.2 GB. Contains `blip2_positional_embedding.pt`, `pointnet.pth`, `pointnet2_ulip.pt`.
- `/home/yoohyun/research2/local_dataset/ConceptGraphs_model_cache/`  
  Size: 4.8 GB. Regenerable, but backup saves download time and avoids URL/cache drift.
- `/home/yoohyun/research2/local_dataset/checkpoints/openmask3d/`  
  Size: 3.3 GB. Optional because `OpenMask3D` is currently a later baseline.
- `/home/yoohyun/research2/local_dataset/DualMap_model_cache/`  
  Size: 871 MB. Low priority because `DualMap` is not the active baseline route.

Docker images with tracked build recipes:

- `research2/conceptgraphs-smoke:latest`  
  Size: 27.8 GB. Optional because the Dockerfile and build script are tracked, but saving it avoids a long rebuild.
- `research2/real-smoke:latest`  
  Size: 1.64 GB. Optional and easy to rebuild.
- `h001-qwen-vl-runtime:cu128`  
  Size: 34.6 GB. Optional only if a future Qwen-based route is resumed; current active E005 route does not require it.

### Not Currently Present Or Not Worth Backing Up

사실:

- `experiments/H001_geom_reliability/sources/open3dsg/...` does not exist in the current `/home/yoohyun/research2` workspace.
- `/home/yoohyun/research2/local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/...` was not found in the current workspace.
- `logs/*.log` are not worth Drive backup for paper continuity. Keep only if a specific failure trace must be debugged.
- `local_dataset/external_repos/` is low priority because repos are cloneable and commit/build instructions are tracked.

에이전트 추론:

- The safest minimal Drive package for moving machines is: selected `Open3DSG` checkpoint, `h001-open3dsg-repro:cu128` image tar, E005-M45/M49/M52/M53/M54 row-level artifacts, E003-M75 bridge artifact, `local_dataset/Open3DSG_bridge/`, and dataset manifests/raw data only if license permits.

## Open3DSG Backup And Restore Checklist

사실:

This checklist is for moving the current `Open3DSG` route to another machine without depending on the current workstation state. Replace `<drive_root>` with the actual Google Drive mount or sync directory.

### Backup Package Layout

Recommended Drive layout:

```text
<drive_root>/TASMM_backup_20260522/
  README_restore.md
  manifest/
  docker/
  open3dsg/
    checkpoints/
    bridge/
    artifacts/
    optional_features/
  datasets_optional/
```

### Priority A Backup Commands

Create directories and checksum manifest:

```bash
BACKUP_ROOT=<drive_root>/TASMM_backup_20260522
mkdir -p "$BACKUP_ROOT"/{manifest,docker,open3dsg/checkpoints,open3dsg/bridge,open3dsg/artifacts,datasets_optional}
```

Save the selected `Open3DSG` checkpoint:

```bash
rsync -av --partial \
  /home/yoohyun/research/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt \
  "$BACKUP_ROOT/open3dsg/checkpoints/"

sha256sum \
  /home/yoohyun/research/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt \
  > "$BACKUP_ROOT/manifest/open3dsg_epoch13_ckpt.sha256"
```

Save the `Open3DSG` Docker image because this repo does not yet have a confirmed local build recipe for it:

```bash
docker save h001-open3dsg-repro:cu128 | gzip > "$BACKUP_ROOT/docker/h001-open3dsg-repro_cu128_20260522.tar.gz"
sha256sum "$BACKUP_ROOT/docker/h001-open3dsg-repro_cu128_20260522.tar.gz" \
  > "$BACKUP_ROOT/manifest/h001-open3dsg-repro_cu128_20260522.tar.gz.sha256"
```

Save `Open3DSG` bridge contracts and current paper-table row-level artifacts:

```bash
rsync -av --partial /home/yoohyun/research2/local_dataset/Open3DSG_bridge/ \
  "$BACKUP_ROOT/open3dsg/bridge/Open3DSG_bridge/"

rsync -av --partial \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M45_conceptgraphs_heldout_metric_contract_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M45_conceptgraphs_heldout_query_metric_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M49_conceptgraphs_full_heldout_aggregation_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M51_h001_heldout_policy_replay_contract_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M52_h001_heldout_policy_replay_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M53_paired_failure_table_decision_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M54_paper_table_claim_ledger_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M56_robustness_denominator_open3dsg_audit_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M57_open3dsg_output_schema_contract_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M58_object_candidate_export_plan_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M60_open3dsg_query_conversion_contract_v0 \
  "$BACKUP_ROOT/open3dsg/artifacts/"

rsync -av --partial \
  /home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M75_expanded_direct_query_bridge_v0 \
  "$BACKUP_ROOT/open3dsg/artifacts/"
```

Save optional raw data only if the dataset license permits private Drive storage:

```bash
rsync -av --partial /home/yoohyun/research2/local_dataset/3RScan "$BACKUP_ROOT/datasets_optional/"
rsync -av --partial /home/yoohyun/research2/local_dataset/3DSSG "$BACKUP_ROOT/datasets_optional/"
rsync -av --partial /home/yoohyun/research2/local_dataset/3DSSG_subset "$BACKUP_ROOT/datasets_optional/"
```

### Priority B Optional Backup Commands

Use these only when Drive space is acceptable. They are large or lower priority.

```bash
mkdir -p "$BACKUP_ROOT/open3dsg/optional_features"

rsync -av --partial \
  /home/yoohyun/research/local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3 \
  "$BACKUP_ROOT/open3dsg/optional_features/"

rsync -av --partial \
  /home/yoohyun/research/local_dataset/Open3DSG_staged/training_repro/output/features/clip_features_h001_official_blip_top5_scales3 \
  "$BACKUP_ROOT/open3dsg/optional_features/"

rsync -av --partial \
  /home/yoohyun/research/local_dataset/Open3DSG_staged/h001_runtime/output/checkpoints \
  "$BACKUP_ROOT/open3dsg/"
```

Optional Docker image caches:

```bash
docker save research2/conceptgraphs-smoke:latest | gzip > "$BACKUP_ROOT/docker/research2_conceptgraphs-smoke_latest_20260522.tar.gz"
docker save research2/real-smoke:latest | gzip > "$BACKUP_ROOT/docker/research2_real-smoke_latest_20260522.tar.gz"
```

### Restore Order On A New Machine

1. Clone the repo and enter it.

```bash
git clone https://github.com/Kim-Yoo-Hyun/TASMM.git /home/yoohyun/research2
cd /home/yoohyun/research2
```

2. Restore local datasets if they were backed up and license permits.

```bash
mkdir -p /home/yoohyun/research2/local_dataset
rsync -av --partial "$BACKUP_ROOT/datasets_optional/3RScan" /home/yoohyun/research2/local_dataset/
rsync -av --partial "$BACKUP_ROOT/datasets_optional/3DSSG" /home/yoohyun/research2/local_dataset/
rsync -av --partial "$BACKUP_ROOT/datasets_optional/3DSSG_subset" /home/yoohyun/research2/local_dataset/
```

3. Restore the external read-only `Open3DSG_staged` source location. Keep derived outputs under `research2/local_dataset/Open3DSG_bridge/`, not inside this source path.

```bash
mkdir -p /home/yoohyun/research/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints
rsync -av --partial "$BACKUP_ROOT/open3dsg/checkpoints/" \
  /home/yoohyun/research/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/
```

If the full `Open3DSG_staged` tree was preserved elsewhere, restore it to:

```text
/home/yoohyun/research/local_dataset/Open3DSG_staged
```

4. Restore bridge contracts and artifacts.

```bash
mkdir -p /home/yoohyun/research2/local_dataset/Open3DSG_bridge
rsync -av --partial "$BACKUP_ROOT/open3dsg/bridge/Open3DSG_bridge/" \
  /home/yoohyun/research2/local_dataset/Open3DSG_bridge/

mkdir -p /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts
rsync -av --partial "$BACKUP_ROOT/open3dsg/artifacts/" \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/
```

5. Load Docker images.

```bash
gunzip -c "$BACKUP_ROOT/docker/h001-open3dsg-repro_cu128_20260522.tar.gz" | docker load
docker image inspect h001-open3dsg-repro:cu128
```

6. Verify the restored state.

```bash
test -f /home/yoohyun/research/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt
docker image inspect h001-open3dsg-repro:cu128 >/dev/null
python experiments/E005_external_baseline_transition/tools/verify_m58_open3dsg_object_candidate_export.py
python experiments/E005_external_baseline_transition/tools/plan_m60_open3dsg_query_conversion_contract.py
python experiments/E005_external_baseline_transition/tools/verify_m60_open3dsg_query_conversion_contract.py
```

Expected current verification status before M59 succeeds:

```text
e005_m60_open3dsg_query_conversion_contract_ready_waiting_m59_rows
```

7. Resume the active experiment only after the above checks pass.

```bash
python experiments/E005_external_baseline_transition/tools/launch_m59_open3dsg_object_export_smoke.py --launch
python experiments/E005_external_baseline_transition/tools/verify_m59_open3dsg_object_export_smoke.py --require-ready
```

### Restore Failure Triage

| Failure | Likely cause | Action |
| --- | --- | --- |
| `docker image inspect h001-open3dsg-repro:cu128` fails | Image tar was not restored or tag differs | Run `docker images`, reload tar, retag only if the image id matches the saved image |
| `verify_m58...` reports missing checkpoint | `Open3DSG_staged` checkpoint path incomplete | Restore checkpoint to the exact path above or update M58/M59 contracts intentionally |
| M60 verifier waits for M59 rows | Expected state before M59 relaunch | Not a failure; relaunch M59 when GPU memory is available |
| M60 verifier fails denominator row count | E005-M45 contract artifacts missing | Restore `E005-M45_conceptgraphs_heldout_query_metric_v0` and related M45 contract artifacts or regenerate them |
| M59 writes rows but M60 still waits | Candidate file path mismatch | Check `local_dataset/Open3DSG_bridge/E005-M59_object_candidate_export_smoke_v0/open3dsg_object_candidates.jsonl` |

사용자 판단 필요:

- Decide whether to include the 13 GB eval feature directory in the default Drive package. It is optional but useful if E005-M59/M60 continues on another machine.
- Decide whether to include the 131 GB official feature directory. It is not recommended unless Drive capacity is not a concern.
