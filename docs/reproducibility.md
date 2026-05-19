# Reproducibility Notes

Updated: 2026-05-18

이 문서는 현재 repo에서 실험을 다시 실행하기 위해 필요한 데이터 위치, 다운로드 명령, checkpoint 위치, Docker 실행법, 재현 명령, artifact/evaluation 요약을 한 곳에 모은다. 세부 workflow 규칙은 `docs/experiments.md`를 따른다.

## Current Scope

사실:

- Active experiment route: `experiments/E005_external_baseline_transition/`.
- Active external baseline: `ConceptGraphs`.
- Docker image: `research2/conceptgraphs-smoke:latest`.
- Current heldout state: `heldout_b01` and `heldout_b02` runtime/metric conversion are complete; `heldout_b03` is waiting for GPU free memory >= 24GB.
- Final baseline claim is still false until all heldout batches are complete and aggregated.

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

For the current next batch:

```bash
python experiments/E005_external_baseline_transition/tools/launch_m43_conceptgraphs_heldout_runtime_batch.py --batch-id heldout_b03
python experiments/E005_external_baseline_transition/tools/verify_m43_conceptgraphs_heldout_runtime_batch.py --batch-id heldout_b03
```

Runtime launch preflight requires GPU free memory >= 24GB unless `--ignore-gpu-memory` is explicitly used. The default should remain the 24GB gate because previous `SAM` / `ConceptGraphs` runs were sensitive to GPU memory pressure.

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

논문 주장:

- Current evidence supports external-baseline conversion and heldout batch diagnostics.
- It does not yet support final `ConceptGraphs` heldout baseline, final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

## Next Reproduction Gate

사실:

- Run `heldout_b03` when GPU free memory is >= 24GB.
- Verify `heldout_b03` outputs.
- Convert `heldout_b03` to query-level metrics.
- Aggregate `heldout_b01/b02/b03` into the final 9-scan `ConceptGraphs` heldout baseline table.
