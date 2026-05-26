# Reproducibility Notes

Updated: 2026-05-26

이 문서는 현재 repo에서 실험을 다시 실행하기 위해 필요한 데이터 위치, 다운로드 명령, checkpoint 위치, Docker 실행법, 재현 명령, artifact/evaluation 요약을 한 곳에 모은다. 세부 workflow 규칙은 `docs/experiments.md`를 따른다.

## Current Scope

사실:

- Active experiment route: `experiments/E005_external_baseline_transition/`.
- Active external baselines: `ConceptGraphs`; bounded `Open3DSG` predicted-vocabulary adapter row candidate.
- Docker images: `research2/conceptgraphs-smoke:latest`, `research2/real-smoke:latest`.
- Current `ConceptGraphs` heldout state: `heldout_b01/b02/b03` runtime/metric conversion and full 9-scan aggregation are complete.
- Current claim state: E005-M56-M82 use `/home/yoohyun/research/local_dataset/Open3DSG_staged` as a read-only source and store derived outputs under `/home/yoohyun/research2/local_dataset/Open3DSG_bridge/`. E005-M61 generated denominator-aligned `Open3DSG` object candidates for all 9 query scans: 7,600 rows and 51 / 51 completed batches. Corrected E005-M60 verifies query-level conversion for the 195-row M38/M45 denominator: 759 query candidate/eval rows and 585 policy rows. Corrected primary-label `Open3DSG` strict bbox top5 is 81 / 195 and relaxed bbox 1m top3 is 90 / 195. E005-M64 verifies the leakage-safe predicted-vocabulary adapter policy: strict bbox top5 144 / 195 and relaxed bbox 1m top3 147 / 195. E005-M68 materializes the M38/M45 full-denominator real proposal bridge plan from local `3RScan` / `3DSSG`: 195 rows, 9 ready scans, 65 object targets, 22 prompt labels, and 3 heldout batches. E005-M75 full real-proposal aggregate has 195 query rows, target detected 144 / 195, H001 157 / 195, context-agnostic 156 / 195, `ConceptGraphs` same-batch 114 / 195, detector task-budget 24 / 195, and detector top5 51 / 195. E005-M76 marks M75 diagnostic-table ready but keeps final real RGB-D/open-vocabulary robustness false because detector precision is 0.051892, target detection is 0.738462, and mean false positives before target is 8.104167. E005-M78 fixed replay verifies `offline_confidence_log_depth_radius0p5_cap24_fixed_replay_v0`: M77 reproduction mismatch 0, selected proposals 926, proposal precision 0.105832, target detected 147 / 195, and top5 success 60 / 195. E005-M80-M82 verifies the first runner-integrated `confidence_log_depth` rerun on `heldout_b02`: detector top5 9 / 69 -> 15 / 69, task-budget 5 / 69 -> 7 / 69, and target detected unchanged at 42 / 69.

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
- Log path: `logs/20260523_140609_e005_m59_open3dsg_object_export.log`.
- Current status as of 2026-05-23 14:10 KST: lower-memory object-only relaunch completed; candidate rows 180; completed batches 1; source modified false.
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

`Open3DSG` query-conversion reproduction:

```bash
python experiments/E005_external_baseline_transition/tools/plan_m60_open3dsg_query_conversion_contract.py
python experiments/E005_external_baseline_transition/tools/verify_m60_open3dsg_query_conversion_contract.py
python experiments/E005_external_baseline_transition/tools/run_m60_open3dsg_query_conversion.py --require-object-candidates-ready
python experiments/E005_external_baseline_transition/tools/verify_m60_open3dsg_query_conversion.py --require-policy-rows
```

`Open3DSG` denominator-aligned export plan:

```bash
python experiments/E005_external_baseline_transition/tools/plan_m61_open3dsg_denominator_aligned_export.py
python experiments/E005_external_baseline_transition/tools/verify_m61_open3dsg_denominator_export.py --require-ready
python experiments/E005_external_baseline_transition/tools/analyze_m62_open3dsg_result_interpretation.py
python experiments/E005_external_baseline_transition/tools/analyze_m63_open3dsg_route_decision.py
python experiments/E005_external_baseline_transition/tools/run_m64_open3dsg_vocab_expansion_policy.py --require-object-candidates-ready
python experiments/E005_external_baseline_transition/tools/verify_m64_open3dsg_vocab_expansion_policy.py --require-ready
python experiments/E005_external_baseline_transition/tools/plan_m65_open3dsg_table_integration.py
python experiments/E005_external_baseline_transition/tools/analyze_m66_external_baseline_failure_boundary.py
python experiments/E005_external_baseline_transition/tools/plan_m67_real_rgbd_ov_robustness_route.py
python experiments/E005_external_baseline_transition/tools/plan_m68_full_denominator_real_proposal_bridge.py
E005_M69_SUDO_PASSWORD=<password> python experiments/E005_external_baseline_transition/tools/launch_m69_full_denominator_real_proposal_batch.py --batch-id heldout_b01
python experiments/E005_external_baseline_transition/tools/verify_m70_full_denominator_real_proposal_detector_batch.py --batch-id heldout_b01 --require-ready
python experiments/E005_external_baseline_transition/tools/run_m71_real_proposal_query_metrics.py --batch-id heldout_b01
E005_M69_SUDO_PASSWORD=<password> python experiments/E005_external_baseline_transition/tools/launch_m69_full_denominator_real_proposal_batch.py --batch-id heldout_b02
python experiments/E005_external_baseline_transition/tools/verify_m70_full_denominator_real_proposal_detector_batch.py --batch-id heldout_b02 --require-ready
python experiments/E005_external_baseline_transition/tools/run_m71_real_proposal_query_metrics.py --batch-id heldout_b02
E005_M69_SUDO_PASSWORD=<password> python experiments/E005_external_baseline_transition/tools/launch_m69_full_denominator_real_proposal_batch.py --batch-id heldout_b03
python experiments/E005_external_baseline_transition/tools/verify_m70_full_denominator_real_proposal_detector_batch.py --batch-id heldout_b03 --require-ready
python experiments/E005_external_baseline_transition/tools/run_m71_real_proposal_query_metrics.py --batch-id heldout_b03
python experiments/E005_external_baseline_transition/tools/analyze_m75_real_proposal_aggregate_route.py --require-all
python experiments/E005_external_baseline_transition/tools/plan_m76_real_proposal_claim_boundary.py
python experiments/E005_external_baseline_transition/tools/plan_m77_offline_detector_prompt_repair.py
python experiments/E005_external_baseline_transition/tools/run_m78_offline_repair_replay.py
python experiments/E005_external_baseline_transition/tools/plan_m79_runner_insertion_targeted_rerun.py
E005_M80_SUDO_PASSWORD=<password> python experiments/E005_external_baseline_transition/tools/launch_m80_confidence_log_depth_detector_batch.py --batch-id heldout_b02
python experiments/E005_external_baseline_transition/tools/verify_m70_full_denominator_real_proposal_detector_batch.py --batch-id heldout_b02 --launch-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M80_confidence_log_depth_detector_launch_v0 --run-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M80_confidence_log_depth_detector_run_v0 --out-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M81_confidence_log_depth_detector_verification_v0 --require-ready
python experiments/E005_external_baseline_transition/tools/run_m71_real_proposal_query_metrics.py --batch-id heldout_b02 --m69-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M80_confidence_log_depth_detector_run_v0 --m70-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M81_confidence_log_depth_detector_verification_v0 --out-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M82_confidence_log_depth_query_metric_v0
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
| `E005-M59_object_candidate_export_smoke_v0` | `Open3DSG` one-batch object-candidate export | relaunched in tmux `e005_m59_open3dsg_object_export`; log `logs/20260523_140609_e005_m59_open3dsg_object_export.log`; output path `local_dataset/Open3DSG_bridge/E005-M59_object_candidate_export_smoke_v0/`; candidate rows 180; completed batches 1; lower-memory object-only patch active | export smoke ready; no `Open3DSG` performance claim |
| `E005-M60_open3dsg_query_conversion_contract_v0` | `Open3DSG` query-level conversion | M38/M45 denominator 195 rows, M59 candidate rows 180, policy rows 585, scan overlap 0, query/eval candidate rows 0, outputs under `local_dataset/Open3DSG_bridge/E005-M60_query_conversion_contract_v0/` | verified harness; no `Open3DSG` performance claim |
| `E005-M61_denominator_aligned_export_plan_v0` | `Open3DSG` denominator-aligned target export plan | query rows 195; query scans 9; target subgraphs 51; preprocessed/features ready 51 / 51; train rows 123 and validation rows 72 | export plan ready; no `Open3DSG` performance claim |
| `E005-M61_denominator_aligned_export_v0` | `Open3DSG` denominator-aligned target export | object candidate rows 7,600; completed batches 51 / 51; query scan overlap 9 / 9; source modified false | export ready |
| `E005-M60_open3dsg_query_conversion_m61_v0` | `Open3DSG` denominator-aligned query conversion | query rows 195; query/eval candidate rows 759; policy rows 585; corrected strict bbox top5 81 / 195; corrected relaxed bbox 1m top3 90 / 195 | primary-label adapter below `ConceptGraphs` |
| `E005-M62_open3dsg_result_interpretation_v0` | `Open3DSG` result interpretation | bridge feasibility true; main-table performance baseline false; H001 - corrected `Open3DSG` strict +91 rows; `ConceptGraphs` - corrected `Open3DSG` strict +33 rows | input to M63 route decision |
| `E005-M63_open3dsg_route_decision_v0` | `Open3DSG` route decision | diagnostic predicted-term strict 144 / 195; diagnostic predicted-term relaxed 147 / 195; selected bounded repair next | diagnostic route decision, superseded by M64 policy verification |
| `E005-M64_open3dsg_vocab_expansion_policy_v0` | `Open3DSG` leakage-safe predicted-vocabulary adapter policy | query rows 195; query/eval candidate rows 1,533; policy rows 585; strict bbox top5 144 / 195; relaxed bbox 1m top3 147 / 195; center strict top5 42 / 195; leakage audit pass | bounded external baseline row candidate; not standalone method novelty |
| `E005-M65_open3dsg_table_integration_v0` | `Open3DSG` paper-table integration boundary | include predicted-vocabulary adapter main table true; primary-label adapter main table false; H001 172 / 195; `Open3DSG` vocab 144 / 195; human intent reflected as structured task context true; human intent main claim false | table boundary ready |
| `E005-M66_external_baseline_failure_boundary_v0` | row-level external-baseline failure boundary | H001 vs `ConceptGraphs`: both_success 112, H001-only 60, `ConceptGraphs`-only 2, both_fail 21; H001 vs `Open3DSG` vocab: both_success 133, H001-only 39, `Open3DSG`-only 11, both_fail 12; task-context-specific gain 1 | proxy-search failure-boundary ready; real robustness still false |
| `E005-M67_real_rgbd_ov_robustness_route_v0` | real RGB-D/open-vocabulary robustness route decision | selected `scale_real_proposal_bridge_to_m38_heldout_denominator`; M38/M45 denominator 195 rows / 9 scans / 65 target rows; E003-M75 real-proposal bridge 96 rows; denominator mismatch 99 rows | route ready; final real robustness still false |
| `E005-M68_full_denominator_real_proposal_bridge_plan_v0` | full-denominator real proposal bridge plan | 195 query rows; 9 / 9 ready scans; 65 object targets; 22 prompt labels; 214 sampled frames; 3 heldout batches; row-level overlap with E003-M75 is 0 | input/command plan ready |
| `E005-M69_full_denominator_real_proposal_detector_launch_v0` / `heldout_b01` | detector batch launch | tmux `e005_m69_real_proposal_heldout_b01`; log `logs/20260524_004619_e005_m69_real_proposal_heldout_b01.log`; output `E005-M69_full_denominator_real_proposal_detector_run_v0/heldout_b01/` | launch record |
| `E005-M70_full_denominator_real_proposal_detector_verification_v0` / `heldout_b01` | detector completion verification | expected files 12 / 12; prediction rows 261; pre-cap candidate rows 5,310; matched targets 18 / 22; recall 0.8182; precision 0.0690; false-positive rate 0.9310 | ready for query-level conversion; final robustness still false |
| `E005-M71_real_proposal_query_metric_v0` / `heldout_b01` | real proposal query metrics | query rows 66; target detected 54 / 66; real detector task-budget 8 / 66; real detector top5 21 / 66; H001 48 / 66; `ConceptGraphs` same-batch 45 / 66 | batch query metric ready; final robustness still false |
| `E005-M69_full_denominator_real_proposal_detector_launch_v0` / `heldout_b02` | detector batch launch | tmux `e005_m69_real_proposal_heldout_b02`; log `logs/20260525_111101_e005_m69_real_proposal_heldout_b02.log`; output `E005-M69_full_denominator_real_proposal_detector_run_v0/heldout_b02/` | launch record |
| `E005-M70_full_denominator_real_proposal_detector_verification_v0` / `heldout_b02` | detector completion verification | expected files 12 / 12; prediction rows 264; pre-cap candidate rows 6,799; matched targets 14 / 17; recall 0.8235; precision 0.0530; false-positive rate 0.9470 | ready for query-level conversion; final robustness still false |
| `E005-M71_real_proposal_query_metric_v0` / `heldout_b02` | real proposal query metrics | query rows 69; target detected 42 / 69; real detector task-budget 5 / 69; real detector top5 9 / 69; H001 54 / 69; `ConceptGraphs` same-batch 45 / 69 | target detection weak; aggregate decision pending |
| `E005-M69_full_denominator_real_proposal_detector_launch_v0` / `heldout_b03` | detector batch launch | tmux `e005_m69_real_proposal_heldout_b03`; log `logs/20260525_234108_e005_m69_real_proposal_heldout_b03.log`; output `E005-M69_full_denominator_real_proposal_detector_run_v0/heldout_b03/` | completed |
| `E005-M70_full_denominator_real_proposal_detector_verification_v0` / `heldout_b03` | detector completion verification | expected files 12 / 12; prediction rows 400; matched targets 16; recall 0.8000; precision 0.0400 | ready for query-level conversion |
| `E005-M71_real_proposal_query_metric_v0` / `heldout_b03` | real proposal query metrics | query rows 60; target detected 48 / 60; detector task-budget 11 / 60; detector top5 21 / 60; H001 55 / 60; context-agnostic 54 / 60; `ConceptGraphs` same-batch 24 / 60 | batch query metric ready |
| `E005-M75_real_proposal_aggregate_route_v0` | full real proposal aggregate | ready batches b01/b02/b03; query rows 195; target detected 144 / 195; H001 157 / 195; context-agnostic 156 / 195; `ConceptGraphs` same-batch 114 / 195; detector task-budget 24 / 195; detector top5 51 / 195 | full diagnostic aggregate ready; final robustness still false |
| `E005-M76_real_proposal_claim_boundary_v0` | real proposal claim-boundary decision | diagnostic table ready true; detector precision 0.051892; scan target recall 0.813559; selected route `include_diagnostic_table_then_offline_detector_prompt_repair`; next `E005-M77` | M75 may be a diagnostic table only; final robustness still false |
| `E005-M77_offline_detector_prompt_repair_v0` | offline pre-cap detector/prompt repair design | pre-cap candidate rows 23,742; pre-cap detected targets 54 / 65; current selected detected targets 48 / 65; current replay top5 51 / 195 matches M75 detector top5; best offline policy `offline_confidence_log_depth_radius0p5_cap24` top5 60 / 195 | offline repair promising; final robustness still false |
| `E005-M78_offline_repair_replay_v0` | fixed offline repair replay | fixed policy `offline_confidence_log_depth_radius0p5_cap24_fixed_replay_v0`; M77 reproduction mismatch 0; selected proposals 926; matched proposal rows 98; precision 0.105832; target detected 147 / 195; top5 60 / 195 | runner insertion / targeted rerun needed before paper-facing detector repair claim |
| `E005-M79_runner_insertion_targeted_rerun_plan_v0` | runner insertion / targeted rerun plan | runner source edit required false; insertion point `select_cap_aware_label_balanced_candidates.score_candidate_before_spatial_consolidation_and_caps`; first rerun batch `heldout_b02`; command plan rows 3 | input to E005-M80 launch; final robustness still false |
| `E005-M80_confidence_log_depth_detector_launch_v0` / `heldout_b02` | confidence-log-depth targeted detector launch | tmux `e005_m80_confidence_log_depth_heldout_b02`; log `logs/20260526_020840_e005_m80_confidence_log_depth_heldout_b02.log`; output `E005-M80_confidence_log_depth_detector_run_v0/heldout_b02/`; GPU free at launch 24,421 MiB | launch record |
| `E005-M81_confidence_log_depth_detector_verification_v0` / `heldout_b02` | detector completion verification | expected files 14 / 14; prediction rows 264; pre-cap candidates 6,799; matched targets 14 / 17; precision 0.053030 | ready for query-level conversion |
| `E005-M82_confidence_log_depth_query_metric_v0` / `heldout_b02` | query-level metric conversion | query rows 69; target detected 42 / 69; detector task-budget 7 / 69; detector top5 15 / 69; H001 54 / 69 | ranking gain reproduced; final robustness still false |

논문 주장:

- Current evidence supports proxy-search comparison against a full heldout `ConceptGraphs` external map baseline.
- It does not yet support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

## Next Reproduction Gate

사실:

- Run E005-M83: interpret the `heldout_b02` confidence-log-depth rerun result and decide whether b01/b03 reruns are justified.
- Keep lower-memory runtime patch active to avoid unnecessary `InstructBLIP` GPU loading for object-candidate export.
- Keep `OpenMask3D` as a later proposal baseline until its Docker/`MinkowskiEngine` blocker is worth revisiting.

## Git Tracking Boundary

사실:

- `.gitignore` intentionally excludes `local_dataset/`, `**/artifacts/`, `*.log`, and `*.jsonl`.
- Therefore raw datasets, generated bridge outputs, heavy artifacts, logs, and row-level JSONL files do not go to GitHub.
- Reproduction-critical scripts and docs are not ignored: `experiments/E005_external_baseline_transition/tools/launch_m59_open3dsg_object_export_smoke.py`, `m59_open3dsg_object_dump_runtime_patch.py`, `run_m60_open3dsg_query_conversion.py`, `run_m64_open3dsg_vocab_expansion_policy.py`, `verify_m64_open3dsg_vocab_expansion_policy.py`, `plan_m65_open3dsg_table_integration.py`, `analyze_m66_external_baseline_failure_boundary.py`, `plan_m67_real_rgbd_ov_robustness_route.py`, `plan_m68_full_denominator_real_proposal_bridge.py`, `analyze_m75_real_proposal_aggregate_route.py`, `plan_m76_real_proposal_claim_boundary.py`, `plan_m77_offline_detector_prompt_repair.py`, `run_m78_offline_repair_replay.py`, `plan_m79_runner_insertion_targeted_rerun.py`, `launch_m80_confidence_log_depth_detector_batch.py`, `README.md`, `TODO.md`, and this document are visible to git.

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
| E005-M66 external-baseline failure boundary | `python experiments/E005_external_baseline_transition/tools/analyze_m66_external_baseline_failure_boundary.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M66_external_baseline_failure_boundary_v0/coverage.json` |
| E005-M67 robustness route decision | `python experiments/E005_external_baseline_transition/tools/plan_m67_real_rgbd_ov_robustness_route.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M67_real_rgbd_ov_robustness_route_v0/coverage.json` |
| E005-M68 full-denominator real proposal bridge plan | `python experiments/E005_external_baseline_transition/tools/plan_m68_full_denominator_real_proposal_bridge.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M68_full_denominator_real_proposal_bridge_plan_v0/coverage.json` |
| E005-M69 detector batch launch | `E005_M69_SUDO_PASSWORD=<password> python experiments/E005_external_baseline_transition/tools/launch_m69_full_denominator_real_proposal_batch.py --batch-id heldout_b01` and repeat for b02/b03 | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M69_full_denominator_real_proposal_detector_launch_v0/<batch>/coverage.json` |
| E005-M70 detector completion verification | `python experiments/E005_external_baseline_transition/tools/verify_m70_full_denominator_real_proposal_detector_batch.py --batch-id heldout_b01 --require-ready` and repeat for b02/b03 | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M70_full_denominator_real_proposal_detector_verification_v0/<batch>/coverage.json` |
| E005-M71 real proposal query metrics | `python experiments/E005_external_baseline_transition/tools/run_m71_real_proposal_query_metrics.py --batch-id heldout_b01` and repeat for b02/b03 after verification | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M71_real_proposal_query_metric_v0/<batch>/coverage.json` |
| E005-M75 real proposal aggregate route | `python experiments/E005_external_baseline_transition/tools/analyze_m75_real_proposal_aggregate_route.py --require-all` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M75_real_proposal_aggregate_route_v0/coverage.json` |
| E005-M76 real proposal claim boundary | `python experiments/E005_external_baseline_transition/tools/plan_m76_real_proposal_claim_boundary.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M76_real_proposal_claim_boundary_v0/coverage.json` |
| E005-M77 offline detector/prompt repair design | `python experiments/E005_external_baseline_transition/tools/plan_m77_offline_detector_prompt_repair.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M77_offline_detector_prompt_repair_v0/coverage.json` |
| E005-M78 fixed offline repair replay | `python experiments/E005_external_baseline_transition/tools/run_m78_offline_repair_replay.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M78_offline_repair_replay_v0/coverage.json` |
| E005-M79 runner insertion / targeted rerun plan | `python experiments/E005_external_baseline_transition/tools/plan_m79_runner_insertion_targeted_rerun.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M79_runner_insertion_targeted_rerun_plan_v0/coverage.json` |
| E005-M80 confidence-log-depth detector launch | `E005_M80_SUDO_PASSWORD=<password> python experiments/E005_external_baseline_transition/tools/launch_m80_confidence_log_depth_detector_batch.py --batch-id heldout_b02` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M80_confidence_log_depth_detector_launch_v0/heldout_b02/coverage.json` |
| E005-M81 confidence-log-depth detector verification | `python experiments/E005_external_baseline_transition/tools/verify_m70_full_denominator_real_proposal_detector_batch.py --batch-id heldout_b02 --launch-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M80_confidence_log_depth_detector_launch_v0 --run-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M80_confidence_log_depth_detector_run_v0 --out-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M81_confidence_log_depth_detector_verification_v0 --require-ready` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M81_confidence_log_depth_detector_verification_v0/heldout_b02/coverage.json` |
| E005-M82 confidence-log-depth query metrics | `python experiments/E005_external_baseline_transition/tools/run_m71_real_proposal_query_metrics.py --batch-id heldout_b02 --m69-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M80_confidence_log_depth_detector_run_v0 --m70-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M81_confidence_log_depth_detector_verification_v0 --out-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M82_confidence_log_depth_query_metric_v0` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M82_confidence_log_depth_query_metric_v0/heldout_b02/coverage.json` |
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
- `experiments/E005_external_baseline_transition/artifacts/E005-M66_external_baseline_failure_boundary_v0/`
  Contains row-level H001 vs `ConceptGraphs` / `Open3DSG` failure-boundary rows and claim-boundary rows.
- `experiments/E005_external_baseline_transition/artifacts/E005-M67_real_rgbd_ov_robustness_route_v0/`
  Contains the real RGB-D/open-vocabulary robustness route decision and M68 minimum contract.
- `experiments/E005_external_baseline_transition/artifacts/E005-M68_full_denominator_real_proposal_bridge_plan_v0/`
  Contains full-denominator real proposal bridge inputs and batch command plans.
- `experiments/E003_perception_noise_expansion/artifacts/E003-M75_expanded_direct_query_bridge_v0/`  
  Size: 1.2 MB. Contains real RGB-D/open-vocabulary bridge rows, policy rows, failure rows, and metrics.

Small but useful `Open3DSG` bridge contracts and smoke outputs:

- `local_dataset/Open3DSG_bridge/`  
  Contains M57/M58/M59/M60/M61/M62 schema, launch, conversion, denominator-alignment, and interpretation outputs. It includes denominator-aligned `Open3DSG` performance rows, but current performance is weak.
- `experiments/E005_external_baseline_transition/artifacts/E005-M56_robustness_denominator_open3dsg_audit_v0/`
- `experiments/E005_external_baseline_transition/artifacts/E005-M57_open3dsg_output_schema_contract_v0/`
- `experiments/E005_external_baseline_transition/artifacts/E005-M58_object_candidate_export_plan_v0/`
- `experiments/E005_external_baseline_transition/artifacts/E005-M59_object_candidate_export_smoke_v0/`
- `experiments/E005_external_baseline_transition/artifacts/E005-M60_open3dsg_query_conversion_contract_v0/`
- `experiments/E005_external_baseline_transition/artifacts/E005-M61_denominator_aligned_export_plan_v0/`

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

- The safest minimal Drive package for moving machines is: selected `Open3DSG` checkpoint, `h001-open3dsg-repro:cu128` image tar, E005-M45/M49/M52/M53/M54/M66/M67/M68/M69/M70/M71/M75/M76/M77/M78/M79 row-level artifacts, E003-M75 bridge artifact, `local_dataset/Open3DSG_bridge/`, and dataset manifests/raw data only if license permits.

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
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M59_object_candidate_export_smoke_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M60_open3dsg_query_conversion_contract_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M61_denominator_aligned_export_plan_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M61_denominator_aligned_export_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M60_open3dsg_query_conversion_m61_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M62_open3dsg_result_interpretation_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M63_open3dsg_route_decision_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M64_open3dsg_vocab_expansion_policy_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M65_open3dsg_table_integration_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M66_external_baseline_failure_boundary_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M67_real_rgbd_ov_robustness_route_v0 \
  /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M68_full_denominator_real_proposal_bridge_plan_v0 \
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
python experiments/E005_external_baseline_transition/tools/plan_m61_open3dsg_denominator_aligned_export.py
python experiments/E005_external_baseline_transition/tools/verify_m61_open3dsg_denominator_export.py --require-ready
python experiments/E005_external_baseline_transition/tools/run_m60_open3dsg_query_conversion.py --require-object-candidates-ready
python experiments/E005_external_baseline_transition/tools/verify_m60_open3dsg_query_conversion.py --require-policy-rows
python experiments/E005_external_baseline_transition/tools/analyze_m62_open3dsg_result_interpretation.py
python experiments/E005_external_baseline_transition/tools/analyze_m66_external_baseline_failure_boundary.py
python experiments/E005_external_baseline_transition/tools/plan_m67_real_rgbd_ov_robustness_route.py
```

Expected current verification status:

```text
M59 verifier: ready with 180 first-batch rows
M61 verifier: ready with 7,600 denominator-aligned rows and scan overlap 9/9
M60 verifier: ready with 759 query/eval candidate rows and 585 policy rows
M62 interpretation: ready; corrected Open3DSG bridge feasible but below ConceptGraphs under primary labels
M63 route decision: ready; diagnostic predicted-vocabulary repair selected and completed by M64
M64 verifier: ready with leakage-safe predicted-vocabulary strict 144/195 and relaxed 147/195
M65 table integration: ready; Open3DSG vocab adapter included as bounded external row; human intent main claim false
M66 failure boundary: ready; H001-only 60 vs ConceptGraphs, 39 vs Open3DSG vocab; task-context gain 1
M67 route decision: ready; selected scale_real_proposal_bridge_to_m38_heldout_denominator
```

7. Resume the active experiment only after the above checks pass.

```bash
python experiments/E005_external_baseline_transition/tools/plan_m67_real_rgbd_ov_robustness_route.py
```

### Restore Failure Triage

| Failure | Likely cause | Action |
| --- | --- | --- |
| `docker image inspect h001-open3dsg-repro:cu128` fails | Image tar was not restored or tag differs | Run `docker images`, reload tar, retag only if the image id matches the saved image |
| `verify_m58...` reports missing checkpoint | `Open3DSG_staged` checkpoint path incomplete | Restore checkpoint to the exact path above or update M58/M59 contracts intentionally |
| M60 verifier reports scan overlap 0 | M61 denominator-aligned rows missing or wrong input directory | Verify M61 output, then rerun M60 with `--require-object-candidates-ready` |
| M60 verifier fails denominator row count | E005-M45 contract artifacts missing | Restore `E005-M45_conceptgraphs_heldout_query_metric_v0` and related M45 contract artifacts or regenerate them |
| M59 writes rows but M60 still has no query candidates | Generic first-batch rows do not overlap the M38/M45 denominator | Use M61 target scan/subgraph export instead of generic first-batch export |

사용자 판단 필요:

- Decide whether to include the 13 GB eval feature directory in the default Drive package. It is optional but useful if E005-M59/M60 continues on another machine.
- Decide whether to include the 131 GB official feature directory. It is not recommended unless Drive capacity is not a concern.
