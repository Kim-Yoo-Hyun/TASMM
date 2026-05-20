# Reproducibility Notes

Updated: 2026-05-21

이 문서는 현재 repo에서 실험을 다시 실행하기 위해 필요한 데이터 위치, 다운로드 명령, checkpoint 위치, Docker 실행법, 재현 명령, artifact/evaluation 요약을 한 곳에 모은다. 세부 workflow 규칙은 `docs/experiments.md`를 따른다.

## Current Scope

사실:

- Active experiment route: `experiments/E005_external_baseline_transition/`.
- Active external baseline: `ConceptGraphs`.
- Docker image: `research2/conceptgraphs-smoke:latest`.
- Current heldout state: `heldout_b01/b02/b03` runtime/metric conversion and full 9-scan aggregation are complete.
- Current claim state: E005-M59 failed on CUDA OOM and still keeps final real RGB-D/open-vocabulary robustness false. E005-M56 fixes separate proxy-search / real RGB-D proposal denominators, E005-M57/M58 define the `Open3DSG` conversion/export contracts, and E005-M59 attempts one-batch object candidate export while using `/home/yoohyun/research/local_dataset/Open3DSG_staged` as a read-only source. Derived `Open3DSG` bridge outputs are stored under `/home/yoohyun/research2/local_dataset/Open3DSG_bridge/`.

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
- Current status as of 2026-05-21 04:54 KST: failed; tmux stopped; candidate rows not written; CUDA OOM during `InstructBLIP` checkpoint loading.

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
| `E005-M59_object_candidate_export_smoke_v0` | `Open3DSG` one-batch object-candidate export | launched in tmux `e005_m59_open3dsg_object_export`; log `logs/20260521_044206_e005_m59_open3dsg_object_export.log`; output path `local_dataset/Open3DSG_bridge/E005-M59_object_candidate_export_smoke_v0/`; candidate rows 0 as of 2026-05-21 04:54 KST; failure is CUDA OOM during `InstructBLIP` loading | failed; no `Open3DSG` performance claim |

논문 주장:

- Current evidence supports proxy-search comparison against a full heldout `ConceptGraphs` external map baseline.
- It does not yet support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

## Next Reproduction Gate

사실:

- Repair E005-M59 `Open3DSG` object-candidate export hook implementation / one-batch Docker smoke.
- Candidate repair routes: GPU-exclusive relaunch with stricter free-memory preflight, or lower-memory runtime patch that avoids unnecessary `InstructBLIP` GPU loading for object-candidate export.
- Keep `OpenMask3D` as a later proposal baseline until its Docker/`MinkowskiEngine` blocker is worth revisiting.

## Git Tracking Boundary

사실:

- `.gitignore` intentionally excludes `local_dataset/`, `**/artifacts/`, `*.log`, and `*.jsonl`.
- Therefore raw datasets, generated bridge outputs, heavy artifacts, logs, and row-level JSONL files do not go to GitHub.
- Reproduction-critical scripts and docs are not ignored: `experiments/E005_external_baseline_transition/tools/launch_m59_open3dsg_object_export_smoke.py`, `m59_open3dsg_object_dump_runtime_patch.py`, `verify_m59_open3dsg_object_export_smoke.py`, `README.md`, `TODO.md`, and this document are visible to git.

에이전트 추론:

- The current `.gitignore` is acceptable for keeping large/local data out of GitHub, but key result summaries, exact commands, expected paths, and verification commands must stay in tracked Markdown files because result payloads and logs are ignored.
