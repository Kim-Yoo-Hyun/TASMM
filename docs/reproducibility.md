# Reproducibility Notes

Updated: 2026-06-01

이 문서는 현재 repo에서 실험을 다시 실행하기 위해 필요한 데이터 위치, 다운로드 명령, checkpoint 위치, Docker 실행법, 재현 명령, artifact/evaluation 요약을 한 곳에 모은다. 세부 workflow 규칙은 `docs/experiments.md`를 따른다.

## Current Scope

사실:

- Active experiment route: `experiments/E008_real_navigation_benchmark/`.
- Active external baselines: `ConceptGraphs`; bounded `Open3DSG` predicted-vocabulary adapter row candidate.
- Docker images: `research2/conceptgraphs-smoke:latest`, `research2/real-smoke:latest`, `research3/habitat-h001:20260508-calib-artifacts` for E008 `Habitat` smoke.
- Current `ConceptGraphs` heldout state: `heldout_b01/b02/b03` runtime/metric conversion and full 9-scan aggregation are complete.
- Current claim state: E005-M56-M101 use `/home/yoohyun/research/local_dataset/Open3DSG_staged` as a read-only source and store derived outputs under `/home/yoohyun/research2/local_dataset/Open3DSG_bridge/`. E005-M100 selects `h001_then_conceptgraphs_top5_on_observed_miss_v0`: H001 success 157 / 195 -> 181 / 195, `AttemptSPL` proxy 0.773932 -> 0.798675, mean `ExpectedSearchCost` 1.758974 -> 2.435897. E007-M07 packages the E007 bridge table as paper-facing occupancy-grid path-cost proxy evidence with 6 table rows, 3 allowed claim rows, and 3 blocked claim rows. E008-M01-M86 now cover local read-only `HM3D ObjectNav` + `Habitat` source preflight through dynamic-stale overlay trajectory execution smoke, budget-matched repair, source-diverse policy redesign/materialization/execution, routine-fetch repair, navigation boundary package/paper-table freeze, high-path tail-slot policy materialization, full-val-mini detector-policy trajectory smoke, loss-safe candidate-source expansion, source-gap non-oracle source/observation expansion, source-gap render frame staging verification, and source-gap detector candidate-source verification. E008-M86 produced 48 final source-gap detector candidates from 1,896 pre-cap candidates, with validator errors/warnings 0/0 and matching target rows 0. Final real navigation remains blocked until M87 navmesh/source-readiness validation, source-gap recovery evaluation, trajectory checks, heldout transfer, and stronger navigation/search baselines.

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
- Existing `HM3D` / `ObjectNav` / `Habitat` data path from another research workspace: `/home/yoohyun/research3/local_dataset/data`. Use read-only for E008 source/episode preflight; do not write artifacts there.
- Derived E008 navigation bridge outputs: `local_dataset/HM3D_navigation_bridge/`.

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
python experiments/E005_external_baseline_transition/tools/plan_m83_confidence_log_depth_rerun_decision.py
python experiments/E005_external_baseline_transition/tools/plan_m84_prompt_label_external_route.py
python experiments/E005_external_baseline_transition/tools/plan_m85_prompt_label_recall_audit.py
python experiments/E005_external_baseline_transition/tools/plan_m86_prompt_repair_preflight_visibility_matcher.py
python experiments/E005_external_baseline_transition/tools/plan_m87_candidate_survival_threshold_zero_written.py
python experiments/E005_external_baseline_transition/tools/plan_m88_zero_written_raw_label_trace.py
E005_M89_SUDO_PASSWORD=<password> python experiments/E005_external_baseline_transition/tools/launch_m89_cleanup_trace_detector.py
python experiments/E005_external_baseline_transition/tools/verify_m70_full_denominator_real_proposal_detector_batch.py \
  --batch-id heldout_b02 \
  --launch-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M89_cleanup_trace_detector_launch_v0 \
  --run-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M89_cleanup_trace_detector_run_v0 \
  --out-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M89_cleanup_trace_detector_verification_v0 \
  --require-ready
python experiments/E005_external_baseline_transition/tools/analyze_m89_cleanup_trace_result.py
python experiments/E005_external_baseline_transition/tools/plan_m90_label_normalization_prompt_scope_repair.py
printf '<sudo-password>\n' | python experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py \
  --m17-dir /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M68_full_denominator_real_proposal_bridge_plan_v0/batches/heldout_b02 \
  --out-dir /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M91_active_label_precedence_smoke_v0/heldout_b02 \
  --max-scans 1 \
  --scan-id 569d8f0f-72aa-2f24-89a6-77f8b8779ae9 \
  --max-frames-per-scan 24 \
  --max-labels 9 \
  --max-predictions 64800 \
  --max-predictions-per-frame 100 \
  --threshold 0.08 \
  --text-threshold 0.08 \
  --candidate-selection-policy cap_aware_label_balanced_ranking_v0 \
  --selection-score-mode confidence \
  --pre-cap-per-scan-label-cap 24 \
  --pre-cap-spatial-consolidation-radius-m 0.5 \
  --raw-candidate-collection-cap 400000 \
  --export-pre-cap-candidate-pool \
  --export-cleanup-trace \
  --build \
  --docker-sudo \
  --sudo-password-stdin
python experiments/E005_external_baseline_transition/tools/analyze_m91_active_label_precedence_smoke.py
python experiments/E005_external_baseline_transition/tools/plan_m92_active_label_precedence_next_step.py
E005_M93_SUDO_PASSWORD=<password> python experiments/E005_external_baseline_transition/tools/launch_m93_active_label_precedence_b02.py
python experiments/E005_external_baseline_transition/tools/verify_m70_full_denominator_real_proposal_detector_batch.py \
  --batch-id heldout_b02 \
  --launch-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M93_active_label_precedence_detector_launch_v0 \
  --run-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M93_active_label_precedence_detector_run_v0 \
  --out-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M93_active_label_precedence_detector_verification_v0 \
  --require-ready
python experiments/E005_external_baseline_transition/tools/run_m71_real_proposal_query_metrics.py \
  --batch-id heldout_b02 \
  --m69-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M93_active_label_precedence_detector_run_v0 \
  --m70-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M93_active_label_precedence_detector_verification_v0 \
  --out-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M93_active_label_precedence_query_metric_v0
python experiments/E005_external_baseline_transition/tools/analyze_m93_active_label_precedence_result.py
python experiments/E005_external_baseline_transition/tools/plan_m94_active_label_precedence_claim_boundary.py
python experiments/E005_external_baseline_transition/tools/plan_m95_real_proposal_paper_boundary.py
python experiments/E005_external_baseline_transition/tools/plan_m96_next_expansion_route.py
python experiments/E005_external_baseline_transition/tools/plan_m97_external_proposal_mapping_feasibility.py
python experiments/E005_external_baseline_transition/tools/analyze_m98_conceptgraphs_reliability_boundary.py
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
| `E005-M83_confidence_log_depth_rerun_decision_v0` | remaining-batch decision | b02 actual top5 gain +6 rows; b02 target-detection gain 0; expected all-batch fixed-policy top5 60 / 195; H001 157 / 195; b01/b03 rerun skipped now | diagnostic detector-ranking repair only; next E005-M84 |
| `E005-M84_prompt_label_external_route_decision_v0` | prompt/label vs external proposal route decision | recall-miss 11 / 65 targets; max query exposure 33 / 195; remaining b01/b03 ranking gain 3 rows; `Grounded-SAM` weak positive false; `OpenMask3D` hard blockers 3 | route decision ready; next E005-M85 |
| `E005-M85_prompt_label_recall_audit_v0` | prompt/label recall miss audit | no-same-label candidate 5; localization/matcher audit 5; broad/missing label 1; repair contract blocks target-linked leakage fields | audit ready; next E005-M86 |
| `E005-M86_prompt_repair_preflight_visibility_matcher_v0` | prompt repair preflight / visibility-matcher decision | audited targets 11; query exposure 33 / 195; visibility/matcher 5 targets / 15 rows; zero-written scan 5 targets / 15 rows; broad contract 1 target / 3 rows; prompt repair preflight false | decision ready; superseded by E005-M87 audit |
| `E005-M87_candidate_survival_threshold_zero_written_v0` | candidate survival / match-threshold / zero-written scan audit | audited targets 11; query exposure 33 / 195; strict pre-cap suppressed 0; selected 1.5m recovery 2 targets / 6 rows; pre-cap 1.5m recovery 3 targets / 9 rows; instance ambiguity 2 targets / 6 rows; zero-written scan 5 targets / 15 rows | audit ready; superseded by E005-M88 trace audit |
| `E005-M88_zero_written_raw_label_trace_v0` | zero-written raw-label trace / post-filter instrumentation audit | scan `569d8f0f`; zero-written 5 targets / 15 rows; M69/M80 raw/projected/written 513 / 483 / 0; active label `chair`; prompt has `chair=true`; likely loss at prompt-label cleanup; raw-label trace missing | audit ready; superseded by E005-M89 |
| `E005-M89_cleanup_trace_analysis_v0` | target-independent cleanup trace analysis | trace rows 483; all dropped; `drop_not_scan_prompt_label` 479; canonical `stool` 479; active scan label `chair`; blocked-field hits 0 | analysis ready; input to E005-M90 |
| `E005-M90_label_normalization_prompt_scope_repair_v0` | label-normalization / prompt-scope repair decision | selected `active_scan_exact_label_precedence_v0`; active-exact replay keep rows 479 / 483; blocked-field hits 0; upper-bound selected proposals 24 | route decision ready; next E005-M91 |
| `E005-M91_active_label_precedence_smoke_v0` | active-label precedence one-scan cleanup smoke | pre-cap rows 479; final prediction rows 24; cleanup keep/drop 479 / 4; matched target rows 5 / 5; proposal precision 0.208333 | one-scan repair smoke ready; final robustness still false |
| `E005-M92_active_label_precedence_next_step_v0` | query/rerun decision for M91 repair | affected query rows 15; target detected 0 -> 15; detector top5 lower-bound +3; task-budget lower-bound +2; H001 delta 0; side-effect risk 1 scan / 15 rows / 3 `stool` rows | bounded b02 rerun selected; final robustness still false |
| `E005-M93_active_label_precedence_result_analysis_v0` | bounded b02 active-label precedence rerun analysis | target detected 42 / 69 -> 57 / 69; detector top5 15 / 69 -> 18 / 69; detector task-budget 7 / 69 unchanged; H001 54 / 69 unchanged; side-effect loss 0 | batch-level repair diagnostic; final robustness still false |
| `E005-M94_active_label_precedence_claim_boundary_v0` | claim-boundary / broader repair decision | selected `stop_and_record_m93_as_batch_level_repair_diagnostic`; projected diagnostic aggregate target detected 159 / 195, detector top5 60 / 195, detector task-budget 26 / 195, H001 157 / 195 | stop-and-record route ready; next E005-M95 |
| `E005-M95_real_proposal_paper_boundary_v0` | paper-facing real-proposal table and final E005 boundary | 7 main diagnostic rows; 4 repair diagnostic rows; 2 allowed diagnostic claims; 4 blocked claims; next E005-M96 | final E005 boundary ready; robustness/navigation still false |
| `E005-M96_next_expansion_route_decision_v0` | external proposal/mapping vs navigation route decision | selected `external_proposal_mapping_baseline_first`; deferred navigation/search bridge; next E005-M97 | route decision ready; robustness/navigation still false |
| `E005-M97_external_proposal_mapping_feasibility_v0` | external proposal/mapping baseline feasibility matrix | selected `conceptgraphs_derived_map_candidate_route`; `Open3DSG` supporting row; `OpenMask3D` env-blocked; `HOV-SG` source-audit required; next E005-M98 | feasibility ready; robustness/navigation still false |
| `E005-M98_conceptgraphs_reliability_boundary_v0` | `ConceptGraphs` / real detector / H001 row-group reliability smoke | `ConceptGraphs` strict top5 114 / 195; real detector top5 51 / 195; real task-budget 24 / 195; H001 157 / 195; H001 recovers both map/top5 failure 54 rows; map-success H001-failure 24 rows | diagnostic ready; final robustness/navigation still false |
| `E005-M99_row_group_heavier_route_decision_v0` | row-group inspection / heavier external route decision | H001 failure 38 rows / 13 targets; `ConceptGraphs` map-assisted repair candidate 24 rows / 8 targets; H001-or-`ConceptGraphs` upper bound 181 / 195; selected `map_assisted_h001_repair_first` | route decision ready; next E005-M100 |
| `E005-M100_conceptgraphs_assisted_fallback_policy_v0` | `ConceptGraphs`-assisted H001 fallback policy smoke | selected `h001_then_conceptgraphs_top5_on_observed_miss_v0`; success 181 / 195; `AttemptSPL` 0.798675; mean `ExpectedSearchCost` 2.435897; top6 sensitivity 184 / 195 | policy smoke ready; next E005-M101 |
| `E005-M101_map_assisted_claim_boundary_navigation_decision_v0` | map-assisted fallback claim-boundary / navigation-bridge decision | selected `paper_table_integration_and_navigation_bridge_next`; paper-table integration ready true; next E007-M01 | route decision ready; navigation still false |
| `E007-M01_navigation_path_cost_bridge_contract_v0` | navigation/path-cost bridge contract | M100/E002 row overlap 195 / 195; E002 target-grid reachable overlap 186 / 195; `ConceptGraphs` query overlap 195 / 195; real detector proposal rows 925; selected `e002_occupancy_grid_astar_v0` | contract ready; next E007-M02 |
| `E007-M02_path_source_compatibility_v0` | path-source compatibility / route materialization | query rows 195; query-policy rows 1,170; route rows 3,814; all-six-policy materialized queries 177 / 195; external projection pending 3,097; source gaps 36 | materialization ready; next E007-M03 |
| `E007-M03_external_candidate_grid_projection_v0` | external candidate grid projection / path-cost route fields | query rows 195; query-policy rows 1,170; route rows 3,814; route projection-ready 3,785; route path-ready 3,331; query-policy eval-ready 928; no-route query-policy rows 36 | route path-cost fields ready; next E007-M04 |
| `E007-M04_path_cost_policy_metrics_v0` | path-cost policy metrics | source-ready 972 / 1,170; method full success 181 / 195; method source-ready success 163 / 174; mean path cost 2.996131m; mean `PathAttemptSPLProxy` 0.824554 | proxy path metric ready; input to E007-M05 |
| `E007-M05_path_cost_result_interpretation_v0` | path-cost result interpretation / paper-table boundary | selected paper-facing occupancy-grid path-cost bridge table; main navigation table false; real navigation `SR` / `SPL` false; `OldLocationDeadEndCostM` primary false; next E007-M06 | bridge table ready with proxy boundary |
| `E007-M06_path_start_source_limit_sensitivity_v0` | path-start/source-limit sensitivity | source-limited 198 / 1,170; stop-rank 47 / 1,170; old-first non-target zero-step 153; bridge table defensible with proxy boundary true | reviewer defense ready; input to E007-M07 |
| `E007-M07_bridge_table_package_navigation_decision_v0` | bridge-table package / navigation-expansion decision | paper table package ready true; table rows 6; allowed claims 3; blocked claims 3; selected next `E008-M01`; launch long job now false | proxy bridge package ready; real navigation still false |
| `E008-M01_navigation_source_episode_contract_v0` | real navigation source / episode contract | selected `hm3d_objectnav_habitat_local_research3`; `HM3D` `.glb` 1,095; `.navmesh` 910; `ObjectNav val_mini` episodes 30; `Habitat` import ready true; selected next E008-M02; launch long job false | source preflight ready; real `SR` / `SPL` still false |
| `E008-M02_hm3d_objectnav_adapter_smoke_v0` | `HM3D ObjectNav` episode/source adapter smoke | sampled episodes 6; unique scenes 2; scene/navmesh ready 6 / 6; Docker `Habitat` scene smoke success true; selected next E008-M03; launch long job false | adapter smoke ready; real `SR` / `SPL` still false |
| `E008-M03_h001_candidate_navigation_adapter_contract_v0` | H001 candidate-to-navigation adapter contract | M02 episodes 6; eval goal rows ready 6 / 6; policy adapter rows 7; H001 candidate-source rows ready 0; oracle upper-bound smoke ready true; selected next E008-M04 | contract ready; H001 execution and real `SR` / `SPL` still false |
| `E008-M04_objectnav_oracle_path_smoke_v0` | ObjectNav oracle path/metric smoke | episode rows 6; viewpoint paths found 6 / 6; goal-snapped paths found 4 / 6; mean viewpoint path length 5.738806m; selected next E008-M05 | oracle metric plumbing ready; policy execution and real `SR` / `SPL` still false |
| `E008-M05_hm3d_candidate_source_staging_plan_v0` | `HM3D` candidate-source staging plan | semantic scene files ready 2 / 2; semantic category support 6 / 6; selected route `hm3d_semantic_annotation_candidate_source_smoke`; selected next E008-M06 | staging plan ready; candidate coordinates, policy execution, and real `SR` / `SPL` still false |
| `E008-M06_hm3d_semantic_candidate_source_smoke_v0` | `HM3D` semantic annotation candidate-source smoke | label support 6 / 6; Habitat nonzero-AABB scenes 0 / 2; GLB geometry mapping scenes 0 / 2; candidate rows 0; selected next E008-M07 | negative smoke ready; rendered RGB-D/external-map candidate route needed |
| `E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0` | `HM3D` rendered RGB-D detector candidate-source plan | episode rows 6; render plan rows 24; detector manifest rows 6; detector labels 5; `Habitat` image ready true; `real-smoke` image ready true; selected next E008-M08 | detector-source plan ready; superseded by E008-M08 frame staging; real `SR` / `SPL` still false |
| `E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0` | `HM3D` rendered RGB-D frame staging smoke | render plan rows 24; rendered frame rows 24; ready frames 24 / 24; ready scans 6 / 6; detector manifest rows 6; detector input files ready true; selected next E008-M09 | detector-compatible frame staging ready; detector candidates and real `SR` / `SPL` still false |
| `E008-M09_hm3d_rendered_rgbd_detector_candidate_smoke_v0` | `HM3D` rendered RGB-D detector candidate smoke | frame rows 24; raw/written predictions 441 / 137; prediction rows 137; coordinate candidate rows 137; pre-cap candidate rows 409; validator errors/warnings 0 / 0; selected next E008-M10 | detector candidate source ready; coordinate validation and real `SR` / `SPL` still false |
| `E008-M10_detector_candidate_navmesh_validation_v0` | detector candidate coordinate-frame / snap-to-navmesh validation | candidate rows 137; join-ready 137 / 137; coordinate-valid 137 / 137; snapped navigable 136 / 137; source-to-snapped path found 125 / 137; status counts `candidate_path_ready` 125 / `blocked_snapped_point_unreachable_from_episode_start` 11 / `blocked_snap_failed_non_finite` 1; selected next E008-M11 | navmesh validation ready with path warnings; real `SR` / `SPL` still false |
| `E008-M11_detector_candidate_visit_order_path_smoke_v0` | reachable-subset detector candidate visit-order path smoke | input candidate rows 137; path-ready 125 / 137; failure rows 12; visit-order rows 512; policy metric rows 28; `path_cost_ascending_reachable_subset_v0` mean first-ready cost 0.791484m; selected next E008-M12 | visit-order/path-cost smoke ready; no `ObjectNav` eval goal/viewpoint policy input; real `SR` / `SPL` still false |
| `E008-M12_detector_candidate_goal_evaluation_smoke_v0` | leakage-safe detector candidate goal-evaluation smoke | candidate-goal eval rows 512; scan-policy rows 24; aggregate rows 4; primary `any_viewpoint_xz_1p0` proxy success 3 / 6 for all policies; `goal_xz_1p0` proxy success 1 / 6; leakage audit pass; selected next E008-M13 | goal-eval proxy ready with limited success; real `SR` / `SPL` still false |
| `E008-M13_detector_goal_failure_audit_v0` | detector-goal failure audit / observation-coverage decision | episode rows 6; policy failure audit rows 12; all-policy failure episodes 3; pre-cap target-region misses 2; near-miss localization threshold 1; post-cap/snap suppression 0; selected next E008-M14 | coverage expansion selected; real `SR` / `SPL` still false |
| `E008-M14_non_oracle_observation_coverage_plan_v0` | non-oracle observation-coverage expansion plan | episode rows 6; observation pose rows 54; expanded render rows 216; frames per episode 36; selected `bounded_start_neighborhood_multiview_v0`; selected next E008-M15 | plan ready; M15 frame staging and navmesh snap validation required; real `SR` / `SPL` still false |
| `E008-M15_non_oracle_observation_expansion_frame_staging_v0` | non-oracle observation expansion frame staging / snap validation | render plan rows 216; rendered/ready frames 216 / 216; ready scans 6 / 6; snap-ready rows 216 / 216; large snap warnings 8; detector manifest rows 6; selected next E008-M16 | expanded frame staging ready with snap warnings; detector rerun required; real `SR` / `SPL` still false |
| `E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0` | non-oracle observation expansion detector candidate smoke | frame rows 216; raw predictions 4,009; prediction rows 214; coordinate candidate rows 214; pre-cap candidate rows 3,801; selected next E008-M17 | expanded detector candidates ready; real `SR` / `SPL` still false |
| `E008-M17_expanded_detector_candidate_navmesh_validation_v0` | expanded detector candidate navmesh validation | candidate rows 214; coordinate-valid 214 / 214; snapped navigable 213 / 214; source-to-snapped paths 189 / 214; every scan path-ready true; selected next E008-M18 | navmesh validation ready with path warnings; real `SR` / `SPL` still false |
| `E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0` | expanded detector candidate visit-order path smoke | input candidates 214; path-ready 189; failure rows 25; visit-order rows 781; policy metric rows 28; reachable-subset top1-ready scans 6 / 6; selected next E008-M19 | visit-order/path-cost smoke ready; no eval-only policy input; real `SR` / `SPL` still false |
| `E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0` | expanded leakage-safe detector candidate goal-evaluation smoke | candidate-goal eval rows 781; scan-policy rows 24; aggregate rows 4; `any_viewpoint_xz_1p0` proxy hit 6 / 6 for all policies; `goal_xz_1p0` proxy hit 4 / 6; primary failure rows 0; selected next E008-M20 | goal-eval proxy ready; no eval-only policy input; real `SR` / `SPL` still false |
| `E008-M20_expanded_detector_goal_failure_comparison_navigation_decision_v0` | expanded detector-goal failure comparison / navigation-execution decision | M12 primary failure rows 12 -> M19 0; resolved episodes 3; policies with 6/6 proxy success 4/4; gate counts pass 3 / warning 4 / fail 2; selected next E008-M21 | navigation-execution contract selected; H001 source and trajectory metrics still missing |
| `E008-M21_expanded_detector_policy_trajectory_execution_contract_v0` | expanded detector-policy trajectory execution contract / Docker preflight | contract ready true; Docker preflight pass 6 / warning 1; policy execution plan rows 24; policy contracts 4; M22 runner missing; selected next E008-M22 | runner scaffold selected; real `SR` / `SPL` still false |
| `E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0` | expanded detector-policy trajectory execution smoke | trajectory rows 372; scan-policy rows 24; aggregate rows 4; leakage audit pass; detector-policy smoke `SR` 1.0 for 4 / 4 policies; aggregate `SPL` 0.303595-0.410800; selected next E008-M23 | trajectory smoke ready; final H001 navigation claim still false |
| `E008-M23_trajectory_proxy_consistency_h001_source_decision_v0` | trajectory-vs-proxy consistency / H001 candidate-source decision | scan consistency rows 24; success agreement 24 / 24; proxy `SPL` order consistency 0 / 4 policies; H001 candidate-source rows 0; selected next E008-M24 | source instantiation contract selected; final H001 navigation claim still false |
| `E008-M24_h001_candidate_source_instantiation_contract_v0` | H001 candidate-source instantiation contract | initial memory-proxy candidate rows 137; current-observation candidate rows 214; task-context rows planned 18; source input leakage pass true; selected next E008-M25 | materialization inputs ready; final H001 navigation claim still false |
| `E008-M25_h001_candidate_source_materialization_smoke_v0` | H001 candidate-source materialization smoke | H001 candidate-source rows 1,053; query context rows 18; policy execution plan rows 90; materialized-ready policy plan rows 72; blocked policy plan rows 18; source input leakage pass true; selected next E008-M26 | source rows and policy plans ready; H001 execution and final navigation claim still false |
| `E008-M26_h001_visit_order_path_smoke_v0` | H001 visit-order/path smoke | H001 candidate visit-order rows 252; policy path metric rows 77; evaluated ready policy plans 72; blocked external-map/runtime-event rows 18; source input leakage pass true; selected next E008-M27 | visit-order/path proxy rows ready; H001 trajectory execution and final navigation claim still false |
| `E008-M27_h001_goal_evaluation_smoke_v0` | H001 leakage-safe goal-evaluation smoke | candidate-goal eval rows 252; scan-policy rows 72; aggregate policy rows 4; leakage audit pass true; primary `GoalEvalProxySR` detector confidence 0.500000 / H001 0.333333 / context-agnostic 0.333333 / static memory 0.000000; selected next E008-M28 | goal-eval proxy ready with negative H001-vs-detector boundary; H001 trajectory execution and final navigation claim still false |
| `E008-M28_h001_goal_evaluation_comparison_trajectory_decision_v0` | H001 goal-evaluation comparison / trajectory decision | H001 6/18; detector confidence 9/18; context-agnostic 6/18; static 0/18; H001-vs-detector detector-only 3 and H001-only 0; trajectory gate pass 2 / warning 1 / fail 4; selected next E008-M29 | repair-first route ready; H001 trajectory execution and final navigation claim still false |
| `E008-M29_h001_current_observation_fallback_source_repair_contract_v0` | H001 current-observation fallback/source repair contract | backstop plan rows 18; repair contract rows 2; repair opportunity rows 12; detector-only recoverable rows 3; all-policy source-gap rows 9; allowed/blocked input rows 28/22; selected next E008-M30 | leakage-safe replay contract ready; repaired H001 score, trajectory execution, and final navigation claim still false |
| `E008-M30_h001_current_observation_fallback_replay_smoke_v0` | H001 current-observation fallback replay smoke | repaired candidate-goal eval rows 141; repaired `GoalEvalProxySR` 9/18 vs H001 6/18 vs detector 9/18; recovered detector-only rows 3; success-loss rows 0; remaining source-gap rows 9; repaired `GoalEvalProxySPL` 0.291005 vs detector 0.381619; selected next E008-M31 | leakage-safe replay result ready; trajectory execution and final navigation claim still false |
| `E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0` | H001 fallback trajectory-execution contract / source-gap boundary | sanitized candidate visit rows 141; trajectory execution plan rows 18; source-gap boundary rows 9; proxy success/failure plan rows 9/9; policy leakage pass true; selected next E008-M32 | leakage-safe trajectory input contract ready; H001 trajectory execution and final navigation claim still false |
| `E008-M32_h001_fallback_trajectory_execution_smoke_v0` | H001 fallback trajectory execution smoke | Docker inside true; trajectory attempt rows 104; scan-task metric rows 18; H001 fallback trajectory `SR` 0.5; `SPL` 0.141996; proxy/trajectory success agreement 18/18; source-gap success 0/9; selected next E008-M33 | trajectory smoke ready; final navigation claim still false |
| `E008-M33_h001_trajectory_result_interpretation_baseline_alignment_v0` | H001 trajectory result interpretation / baseline alignment | H001 vs primary detector `SR` delta -0.5; `SPL` delta -0.268804; source-gap H001 `SR` 0.0 vs detector `SR` 1.0; selected next E008-M34 | baseline alignment ready; current H001 navigation improvement claim false; dynamic-stale navigation benchmark needed |
| `E008-M34_dynamic_stale_navigation_contract_v0` | dynamic-stale navigation benchmark/source-intervention contract | selected `hm3d_counterfactual_stale_overlay_v0`; intervention plan rows 18; source-gap diagnostic rows 9; selected next E008-M35; launch long job false | contract ready; no trajectory result or final navigation claim |
| `E008-M35_dynamic_stale_overlay_materialization_smoke_v0` | dynamic-stale overlay materialization smoke | selected route `hm3d_counterfactual_stale_overlay_v0`; intervention rows 18; policy execution plan rows 90; candidate rows 924; source-gap plan rows 45; blocked field hits 0; selected next E008-M36 | input materialization ready; trajectory execution and final navigation claim still false |
| `E008-M36_dynamic_stale_overlay_trajectory_contract_v0` | dynamic-stale overlay trajectory contract / runner adaptation | trajectory candidate rows 924; execution plan rows 90; execute-in-runner rows 90; intervention rows 18; policy count 5; leakage pass true; runner `py_compile` pass true; Docker image inspect pass true; selected next E008-M37 | trajectory contract and generalized runner scaffold ready; no trajectory result or final navigation claim |
| `E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0` | dynamic-stale overlay trajectory execution smoke | Docker inside true; trajectory attempts 467; scan-task-policy rows 90; success rows 45; overall `SR` 0.5; mean `SPL` 0.218178; leakage pass true; H001 `SR` 0.5 / `SPL` 0.141996; detector confidence `SR` 1.0 / `SPL` 0.407894; selected next E008-M38 | trajectory smoke ready; final navigation claim still false |
| `E008-M38_dynamic_stale_overlay_result_interpretation_baseline_alignment_v0` | dynamic-stale overlay result interpretation / baseline alignment | policy result rows 5; pairwise summary rows 4; failure diagnosis rows 7; H001 beats static true; beats detector false; beats fixed current top-k success false; beats task-agnostic success false; scale-up recommended false; selected next E008-M39 | repair-before-scale decision ready; final navigation claim still false |
| `E008-M39_budget_matched_policy_repair_source_gap_contract_v0` | budget-matched dynamic-stale policy repair / source-gap contract | primary budget cap 5; budget alignment rows 15; repair policy contract rows 7; source-gap contract rows 3; M40 materialization plan rows 90; source-ready rows 9; source-gap rows 9; scale-up recommended false; selected next E008-M40 | contract ready; no repaired trajectory result or final navigation claim |
| `E008-M40_budget_matched_repair_row_materialization_smoke_v0` | budget-matched repair row materialization smoke | policy plan rows 90; trajectory candidate rows 378; policy count 5; source-ready/source-gap plan rows 45/45; leakage pass true; budget cap compliance pass true; M41 runner input ready true; selected next E008-M41 | repaired runner input ready; no trajectory result or final navigation claim |
| `E008-M41_budget_matched_repair_trajectory_execution_smoke_v0` | budget-matched repair trajectory execution smoke | Docker inside true; scan-task-policy rows 90; trajectory attempts 270; success rows 36; overall `SR` 0.4; mean `SPL` 0.298698; H001 repaired `SR`/`SPL` 0.5/0.373373; leakage pass true; selected next E008-M42 | repaired trajectory smoke ready; final navigation claim still false |
| `E008-M42_budget_matched_repair_result_interpretation_scale_decision_v0` | budget-matched repair result interpretation and scale decision | policy rows 5; source boundary rows 10; H001 source-ready `SR` 1.0; H001 source-gap `SR` 0.0; H001 vs detector/fixed/task-agnostic `delta_SR` 0.0 and `delta_SPL` 0.0; scale-up recommended false; selected next E008-M43 | interpretation ready; policy redesign required before scale; final navigation claim still false |
| `E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0` | dynamic-stale navigation policy redesign contract | selected policy `h001_task_conditioned_source_diverse_budget5_v1`; source route `source_diverse_current_candidate_pool_rerank_v1`; detector source-gap full/cap5 `SR` 1.0/0.0; M44 plan rows 108; selected next E008-M44 | redesign contract ready; no materialized rows or trajectory result yet |
| `E008-M44_source_diverse_redesign_row_materialization_smoke_v0` | source-diverse redesign row materialization smoke | M43 plan rows 108; execution plan rows 108; candidate rows 468; source-ready/source-gap plan rows 54/54; leakage pass true; budget cap compliance pass true; M45 runner input ready true; selected next E008-M45 | runner input ready; no trajectory result or final navigation claim yet |
| `E008-M45_source_diverse_redesign_trajectory_contract_v0` | source-diverse trajectory execution contract and Docker preflight | candidate rows 468; execution plan rows 108; Docker CLI/image/data/navmesh/ObjectNav checks pass; M37/M46 runner compile pass; source-gap reporting fallback ready; selected next E008-M46 | Docker-ready contract; no trajectory result or final navigation claim yet |
| `E008-M46_source_diverse_redesign_trajectory_execution_smoke_v0` | source-diverse trajectory execution smoke | scan-task-policy rows 108; trajectory attempts 346; success rows 50; leakage pass true; H001 `SR`/`SPL` 0.6111/0.2595; task-agnostic source-diverse `SR`/`SPL` 0.6667/0.3226; selected next E008-M47 | trajectory smoke ready; final navigation claim still false |
| `E008-M47_source_diverse_result_interpretation_scale_decision_v0` | source-diverse result interpretation and scale decision | scale gate pass 4/8; scale-up recommended false; regression cases 2; routine_fetch H001-task-agnostic delta `SR`/`SPL` -0.1667/-0.1893; selected next E008-M48 | interpretation ready; repair required before scale |
| `E008-M48_routine_fetch_task_context_regression_source_gap_repair_contract_v0` | routine-fetch regression/source-gap repair contract | regression diagnosis rows 2; repair principles 3; selected repair policy `h001_task_conditioned_safe_source_diverse_budget5_v2`; M49 expected execution plan rows 126; expected candidate rows 558; readiness gates 8/8; selected next E008-M49 | contract ready; materialization required before execution |
| `E008-M49_routine_fetch_repair_row_materialization_smoke_v0` | routine-fetch repair row materialization smoke | candidate rows 558; execution plan rows 126; policy count 7; baseline preservation 108/108; regression target audit 2/2; leakage audit pass true; budget cap compliance pass true; selected next E008-M50 | runner input ready; no trajectory result or final navigation claim yet |
| `E008-M50_routine_fetch_repair_trajectory_contract_v0` | routine-fetch repair trajectory contract and Docker preflight | candidate rows 558; execution plan rows 126; execute-in-runner rows 126; M37/M51 runner compile pass true; Docker preflight pass true; selected next E008-M51 | Docker-ready contract; no trajectory result or final navigation claim yet |
| `E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0` | routine-fetch repair trajectory execution smoke | Docker inside true; scan-task-policy rows 126; trajectory attempts 409; success rows 62; overall `SR` 0.4921; mean `SPL` 0.2658; H001 v2 `SR`/`SPL` 0.6667/0.3226; task-agnostic source-diverse `SR`/`SPL` 0.6667/0.3226; leakage pass true; selected next E008-M52 | trajectory smoke ready; final navigation claim still false |
| `E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0` | routine-fetch repair result interpretation and scale decision | scale gate pass 5/10; scale-up recommended false; H001 v2 `SR`/`SPL` 0.6667/0.3226; detector/fixed delta `SPL` -0.0508; task-agnostic source-diverse exact tie; source-gap H001 `SR` 0.3333; selected next E008-M53 | interpretation ready; final navigation and human-intent main claims still false |
| `E008-M53_routine_fetch_task_context_specificity_boundary_next_route_v0` | routine-fetch task-context specificity boundary and next-route decision | evidence gates 3/8; task-context distinct gain 0/3; no regression vs task-agnostic true; selected route `demote_task_context_and_package_boundary`; selected next E008-M54 | task context secondary only; final navigation and human-intent main claims still false |
| `E008-M54_navigation_boundary_package_paper_table_freeze_v0` | navigation boundary package and paper-table freeze | diagnostic navigation table rows 7; freeze gates 6/6; allowed claims 4; blocked claims 6; H001 v2 `SR`/`SPL` 0.6667/0.3226; task-agnostic exact tie; detector `SPL` 0.3734; source-gap H001 `SR` 0.3333; selected next E008-M55 | diagnostic table frozen; main navigation, deployable policy, human-intent, and real RGB-D robustness claims still false |
| `E008-M55_source_gap_candidate_generation_repair_feasibility_v0` | source-gap candidate-generation repair feasibility decision | source-gap episodes 3; contexts 9; H001 v2 source-gap `SR` 0.3333; task-agnostic source-gap `SR` 0.3333; remaining failed contexts 6; executed top-5 variant hit in remaining failures 0; selected next E008-M56 | rerank-only repair false; candidate-source expansion required |
| `E008-M56_source_gap_candidate_source_expansion_contract_v0` | source-gap candidate-source expansion contract | source-gap episodes 3; M19 full-pool hit episodes 3/3; full-pool hits outside budget-5 episodes 3/3; unrecovered budget-surfacing episodes 2; allowed input groups 5; blocked input groups 4; selected next E008-M57 | contract ready; budgeted source surfacing must be audited before new policy or scale-up |
| `E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0` | source-gap full-pool candidate-source feature audit | full-pool candidate feature rows 142; source-gap episodes 3; unrecovered budget-surfacing episodes 2; detector-confidence budget-5 unrecovered hits 0/2; `confidence_top4_plus_high_path_top1` unrecovered hits 2/2; selected next E008-M58 | diagnostic feature audit ready; high-path tail-slot policy must be materialized before trajectory execution |
| `E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0` | source-gap high-path tail-slot policy materialization | candidate rows 648; trajectory execution plan rows 144; new policy `h001_task_conditioned_high_path_tail_slot_budget5_v3`; new policy plan/candidate rows 18/90; M49 order preservation 126/126; leakage pass true; unrecovered source-gap recovered 2/2 episodes and 6/6 contexts in diagnostic audit; selected next E008-M59 | materialization ready; goal-evaluation and trajectory execution still required |
| `E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0` | high-path tail-slot leakage-safe goal-evaluation smoke | candidate-goal rows 648; scan-policy rows 144; leakage pass true; new policy full/source-gap `GoalEvalProxySR` 1.0000/1.0000; base H001 v2 full/source-gap 0.6667/0.3333; source-gap recovered vs base 6 contexts with 0 loss; selected next E008-M60 | goal-evaluation proxy ready; Docker trajectory contract/execution still required |
| `E008-M60_high_path_tail_slot_trajectory_contract_v0` | high-path tail-slot trajectory contract and Docker preflight | candidate rows 648; execution plan rows 144; execute-in-runner rows 144; policy count 8; M37/M61 runner compile pass true; Docker/HM3D/navmesh/ObjectNav preflight pass true; M59 source-gap proxy recovery 6 with 0 loss; selected next E008-M61 | contract ready; trajectory execution still required |
| `E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0` | high-path tail-slot trajectory execution smoke | Docker inside true; candidate rows 648; execution plan rows 144; scan-task-policy rows 144; trajectory attempts 472; leakage pass true; H001 high-path tail-slot `SR`/`SPL` 1.0000/0.3961; base H001 v2 and task-agnostic source-diverse 0.6667/0.3226; detector/fixed 0.5000/0.3734; selected next E008-M62 | positive controlled smoke; final real navigation still requires interpretation, scale, and stronger baselines |
| `E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0` | high-path tail-slot result interpretation and scale decision | diagnostic navigation table ready true; scale-up contract ready true; source-gap recovery supported true; source-ready efficiency warning true; scale gates 10 pass / 1 warning / 5 fail; selected next E008-M63 | bounded diagnostic table ready; final navigation still requires scale, heldout transfer, source-ready guard, and stronger baselines |
| `E008-M63_high_path_tail_slot_scaleup_contract_v0` | high-path tail-slot scale-up contract and source-boundary baseline plan | selected denominator `val_mini_full_episode_scale`; 30 episodes; 90 scan-task contexts; 720 core scan-task-policy rows; expected render frames 1,080; holdout episodes 24; baseline plan rows 11; no long job launched; selected next E008-M64 | contract ready; no materialized candidates or trajectories |
| `E008-M64_full_val_mini_high_path_scale_materialization_v0` | full-val-mini high-path scale denominator materialization | 30 episodes; 90 episode-task-context rows; 270 observation poses; 1,080 planned render frames; 30 detector manifest rows; 720 core policy execution plan rows; leakage audit pass; no long job launched; selected next E008-M65 | materialization ready; candidate rows and trajectory execution still required |
| `E008-M65_full_val_mini_render_detector_contract_v0` | full-val-mini render frame staging and detector candidate-source contract | render plan rows 1,080; detector manifest rows 30; detector object target rows 44; prompt labels 8; expected render frame files 3,270; Docker/image preflight pass; M66/M67 command ledger ready; selected next E008-M66 | contract ready; M66 rendered frames now verified; candidate rows and trajectory execution still required |
| `E008-M66_full_val_mini_render_frame_staging_v0` | full-val-mini render frame staging launch / repair / verification | initial ready frames 1,068/1,080; repair rows 12; repaired ready frames 1,080/1,080; ready scans 30/30; detector input files ready true; large snap warnings 20; max snap distance 3.4857m; selected next E008-M67 | frame staging ready with warnings; detector inference and navigation still required |
| `E008-M67_full_val_mini_detector_candidate_source_v0` | full-val-mini detector candidate-source verification | raw predictions 19,061; pre-cap candidates 18,196; final proposal rows 973; coordinate candidate rows 973; frames with written predictions 696/1,080; scan coverage 30/30; validator errors/warnings 0/0; matching target rows 0 | detector-source ready for M68; target recall and navigation claims still false |
| `E008-M68_full_val_mini_detector_candidate_navmesh_validation_v0` | full-val-mini detector candidate navmesh validation | candidate rows 973; coordinate-valid 973/973; snapped navigable 971/973; source-to-snapped path 900/973; path-ready scans 30/30; source-ready episode-task rows 90/90; gate pass | source-readiness ready for M69; real navigation claims still false |
| `E008-M69_full_val_mini_detector_candidate_visit_order_path_smoke_v0` | full-val-mini detector candidate visit-order/path smoke | query-compatible 973/973; path-ready 900/973; visit-order rows 3,673; policy metric rows 124; episode-task policy rows 360; eval-goal/viewpoint leakage false | path smoke ready for M70; real navigation claims still false |
| `E008-M70_full_val_mini_detector_candidate_goal_evaluation_smoke_v0` | full-val-mini leakage-safe detector candidate goal-evaluation smoke | eval episodes 30/30; candidate-goal eval rows 3,673; policy goal metric rows 124; episode-task goal metric rows 360; leakage pass true; all detector policies primary `GoalEvalProxySR` 24/30 | proxy goal-evaluation ready for M71; real navigation claims still false |
| `E008-M71_full_val_mini_detector_goal_failure_comparison_trajectory_decision_v0` | full-val-mini detector-goal failure comparison and trajectory decision | trajectory contract ready true; min `GoalEvalProxySR` 0.8; all-policy failure episodes 6; severe candidate-source coverage gap 1; best SPL proxy policy `path_cost_ascending_reachable_subset_v0`; max SPL proxy gain +0.146945 | ready for M72 trajectory contract/preflight; real navigation claims still false |
| `E008-M72_full_val_mini_detector_policy_trajectory_contract_v0` | full-val-mini detector-policy trajectory contract and Docker preflight | candidate rows 3,673; execution plan rows 120; eval goal/oracle rows 30/30; leakage pass true; Docker preflight pass true; full-ranked min `GoalEvalProxySR` 0.8; budget-5 min `GoalEvalProxySR` 0.2667; runner implemented true; status `ready_runner_next` | ready for M73 trajectory execution smoke; real navigation claims still false |
| `E008-M73_full_val_mini_detector_policy_trajectory_execution_smoke_v0` | full-val-mini detector-policy trajectory execution smoke | trajectory candidate rows 3,673; trajectory attempt rows 1,598; scan-task-policy rows 120; success rows 96; aggregate `SR` 0.8; mean `SPL` 0.1947; leakage pass true | executed smoke ready; superseded by M74 interpretation; final navigation claims still false |
| `E008-M74_full_val_mini_detector_policy_result_interpretation_v0` | full-val-mini detector-policy trajectory result interpretation | M73 trajectory `SR` 0.8; mean `SPL` 0.1947; path-cost vs detector-confidence `delta_SPL` -0.1036; path-cost `delta_PathLengthM` -7.2246m; source-gap `SR` 0.0; budget-5 min proxy `SR` 0.2667; gate pass/warning/fail 4/1/5 | diagnostic interpretation ready; next E008-M75 source-gap/SPL repair; final navigation claims still false |
| `E008-M75_source_gap_spl_repair_contract_v0` | source-gap/SPL repair contract | source-gap failure episodes 2; source-ready failure episodes 4; path-cost helped/hurt/tied `SPL` rows 10/14/6; selected `spl_guarded_confidence_path_tail_budget5_v0` and `candidate_source_expansion_probe_v0`; trajectory execution ready false | contract ready; next E008-M76 row materialization; final navigation claims still false |
| `E008-M76_source_gap_spl_repair_row_materialization_smoke_v0` | source-gap/SPL repair row materialization | repair candidate rows 2,700; execution plan rows 90; goal-eval-ready plan rows 60; probe-only plan rows 30; leakage pass true; top-4 preserved 30/30; guarded tail inserted 26/30 | row materialization ready; next E008-M77 proxy evaluation; final navigation claims still false |
| `E008-M77_source_gap_spl_repair_goal_evaluation_smoke_v0` | source-gap/SPL repair leakage-safe goal evaluation | candidate-goal eval rows 2,100; full-rank guarded ties detector-confidence `SR`/`SPL` 0.8000/0.3506; budget-5 guarded regresses `SR`/`SPL` 0.4333/0.2853 -> 0.4000/0.2734; budget-5 loss 1 | proxy evaluation ready; direct trajectory promotion blocked |
| `E008-M78_source_gap_spl_repair_result_interpretation_v0` | source-gap/SPL repair result interpretation | budget-5 `GoalEvalProxySR` delta -0.0333; budget-5 `GoalEvalProxySPL` delta -0.0118; budget-5 loss rows 1; source-gap unresolved rows 2; selected E008-M79 | rerank-only repair rejected; loss-safe candidate-source expansion required |
| `E008-M79_source_gap_candidate_source_expansion_loss_safe_policy_contract_v0` | source-gap candidate-source expansion and loss-safe policy contract | source-gap expansion cases 2; budget-5 loss sentinel 1; localization controls 4; policy contract rows 5; M80 materialize policy rows 3; detector budget-5 preservation required true | ready for M80 row materialization; no source-gap recovery or final navigation claim |
| `E008-M80_loss_safe_candidate_source_expansion_row_materialization_smoke_v0` | loss-safe candidate-source expansion row materialization | candidate rows 390; detector core rows 150; append policy rows 240; policy plan rows 60; source/observation expansion plan rows 6; budget invariant 30/30 pass; leakage audit pass true | ready for M81 proxy goal-evaluation; no source-gap recovery, trajectory, or final navigation claim |
| `E008-M81_loss_safe_candidate_source_expansion_goal_evaluation_smoke_v0` | loss-safe candidate-source expansion goal evaluation | candidate-goal eval rows 690; detector budget-5 core vs append 13/30 vs 13/30; policy-budget append 15/30 vs core 13/30; append gain/loss 2/0; source-gap append gain/loss 0/0; leakage audit pass true | interpreted by M82; no source-gap recovery, trajectory, or final navigation claim |
| `E008-M82_loss_safe_candidate_source_expansion_result_interpretation_v0` | loss-safe candidate-source expansion result interpretation | append gain/loss 2/0; source-gap append gain/loss 0/0; selected route `source_observation_expansion_contract_first`; direct trajectory promotion false | interpreted by M83; no source-gap recovery, trajectory, or final navigation claim |
| `E008-M83_source_gap_non_oracle_source_observation_expansion_contract_v0` | source-gap non-oracle source/observation expansion contract | source-gap cases 2; selected materialization route rows 4; allowed/blocked inputs 5/4; M84 materialization contract rows 6; readiness gate fail/warning 0/1; long job launch false | superseded by M84 materialization; no source-gap recovery, render/detector output, trajectory, or final navigation claim |
| `E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0` | source-gap source/observation expansion materialization smoke | source-gap cases 2; observation poses 24; render plan rows 192; detector manifests 2; selected route materializations 4; readiness gate fail/warning 0/0; long-job command rows 2; long job launch false | superseded by M85 render verification; no detector output, source-gap recovery, trajectory, or final navigation claim |
| `E008-M85_source_gap_render_frame_staging_launch_v0` + M85 verification rows | source-gap render frame staging launch / verification | launch status `e008_m85_source_gap_render_frame_staging_launched`; verification status `e008_m85_source_gap_render_frame_staging_verified`; ready frames 192/192; ready scans 2/2; snap-ready rows 192/192; detector input files ready true | ready for M86 detector launch; no detector quality, source-gap recovery, trajectory, or final navigation claim |
| `E008-M86_source_gap_detector_candidate_source_launch_v0` + `E008-M86_source_gap_detector_candidate_source_v0` | source-gap detector candidate-source launch / verification | launch status `e008_m86_source_gap_detector_candidate_source_launched`; verification status `e008_m86_source_gap_detector_candidate_source_verified`; final candidates 48; pre-cap candidates 1,896; raw predictions 1,964; frames with written predictions 48/192; validator errors/warnings 0/0; matching target rows 0 | ready for M87 navmesh/source-readiness validation; no detector recall, source-gap recovery, trajectory, or final navigation claim |

논문 주장:

- Current evidence supports proxy-search comparison against a full heldout `ConceptGraphs` external map baseline.
- It does not yet support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.

## Next Reproduction Gate

사실:

- Run E008-M87 source-gap detector candidate navmesh/source-readiness validation.
- Keep lower-memory runtime patch active to avoid unnecessary `InstructBLIP` GPU loading for object-candidate export.
- Keep `OpenMask3D` as a later proposal baseline until its Docker/`MinkowskiEngine` blocker is worth revisiting.

## Git Tracking Boundary

사실:

- `.gitignore` intentionally excludes `local_dataset/`, `**/artifacts/`, `*.log`, and `*.jsonl`.
- Therefore raw datasets, generated bridge outputs, heavy artifacts, logs, and row-level JSONL files do not go to GitHub.
- Reproduction-critical scripts and docs are not ignored: E005 bridge/repair scripts, E007 path-cost bridge scripts, E008 navigation scripts through `launch_m86_source_gap_detector_candidate_source.py`, `README.md`, `TODO.md`, and this document are visible to git.

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
| E005-M83 confidence-log-depth rerun decision | `python experiments/E005_external_baseline_transition/tools/plan_m83_confidence_log_depth_rerun_decision.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M83_confidence_log_depth_rerun_decision_v0/coverage.json` |
| E005-M84 prompt/label vs external proposal route decision | `python experiments/E005_external_baseline_transition/tools/plan_m84_prompt_label_external_route.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M84_prompt_label_external_route_decision_v0/coverage.json` |
| E005-M85 prompt/label recall miss audit | `python experiments/E005_external_baseline_transition/tools/plan_m85_prompt_label_recall_audit.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M85_prompt_label_recall_audit_v0/coverage.json` |
| E005-M86 prompt repair preflight / visibility-matcher decision | `python experiments/E005_external_baseline_transition/tools/plan_m86_prompt_repair_preflight_visibility_matcher.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M86_prompt_repair_preflight_visibility_matcher_v0/coverage.json` |
| E005-M87 candidate survival / threshold / zero-written audit | `python experiments/E005_external_baseline_transition/tools/plan_m87_candidate_survival_threshold_zero_written.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M87_candidate_survival_threshold_zero_written_v0/coverage.json` |
| E005-M88 zero-written raw-label trace audit | `python experiments/E005_external_baseline_transition/tools/plan_m88_zero_written_raw_label_trace.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M88_zero_written_raw_label_trace_v0/coverage.json` |
| E005-M89 cleanup trace detector launch | `E005_M89_SUDO_PASSWORD=<password> python experiments/E005_external_baseline_transition/tools/launch_m89_cleanup_trace_detector.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M89_cleanup_trace_detector_launch_v0/heldout_b02/coverage.json` |
| E005-M89 cleanup trace detector verification | `python experiments/E005_external_baseline_transition/tools/verify_m70_full_denominator_real_proposal_detector_batch.py --batch-id heldout_b02 --launch-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M89_cleanup_trace_detector_launch_v0 --run-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M89_cleanup_trace_detector_run_v0 --out-root /home/yoohyun/research2/experiments/E005_external_baseline_transition/artifacts/E005-M89_cleanup_trace_detector_verification_v0 --require-ready` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M89_cleanup_trace_detector_verification_v0/heldout_b02/coverage.json` |
| E005-M89 cleanup trace analysis | `python experiments/E005_external_baseline_transition/tools/analyze_m89_cleanup_trace_result.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M89_cleanup_trace_analysis_v0/coverage.json` |
| E005-M90 label-normalization / prompt-scope repair decision | `python experiments/E005_external_baseline_transition/tools/plan_m90_label_normalization_prompt_scope_repair.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M90_label_normalization_prompt_scope_repair_v0/coverage.json` |
| E005-M91 active-label precedence smoke analysis | `python experiments/E005_external_baseline_transition/tools/analyze_m91_active_label_precedence_smoke.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M91_active_label_precedence_analysis_v0/coverage.json` |
| E005-M92 active-label precedence next-step decision | `python experiments/E005_external_baseline_transition/tools/plan_m92_active_label_precedence_next_step.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M92_active_label_precedence_next_step_v0/coverage.json` |
| E005-M93 active-label precedence b02 launch / analysis | `E005_M93_SUDO_PASSWORD=<password> python experiments/E005_external_baseline_transition/tools/launch_m93_active_label_precedence_b02.py`; verify/convert with the M93 roots; then `python experiments/E005_external_baseline_transition/tools/analyze_m93_active_label_precedence_result.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M93_active_label_precedence_result_analysis_v0/coverage.json` |
| E005-M94 active-label precedence claim boundary | `python experiments/E005_external_baseline_transition/tools/plan_m94_active_label_precedence_claim_boundary.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M94_active_label_precedence_claim_boundary_v0/coverage.json` |
| E005-M95 real-proposal paper boundary | `python experiments/E005_external_baseline_transition/tools/plan_m95_real_proposal_paper_boundary.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M95_real_proposal_paper_boundary_v0/coverage.json` |
| E005-M96 next expansion route decision | `python experiments/E005_external_baseline_transition/tools/plan_m96_next_expansion_route.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M96_next_expansion_route_decision_v0/coverage.json` |
| E005-M97 external proposal/mapping feasibility | `python experiments/E005_external_baseline_transition/tools/plan_m97_external_proposal_mapping_feasibility.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M97_external_proposal_mapping_feasibility_v0/coverage.json` |
| E005-M98 ConceptGraphs reliability boundary | `python experiments/E005_external_baseline_transition/tools/analyze_m98_conceptgraphs_reliability_boundary.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M98_conceptgraphs_reliability_boundary_v0/coverage.json` |
| E005-M99 row-group / route decision | `python experiments/E005_external_baseline_transition/tools/plan_m99_row_group_heavier_route_decision.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M99_row_group_heavier_route_decision_v0/coverage.json` |
| E005-M100 ConceptGraphs-assisted fallback policy | `python experiments/E005_external_baseline_transition/tools/run_m100_conceptgraphs_assisted_fallback_policy.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M100_conceptgraphs_assisted_fallback_policy_v0/coverage.json` |
| E005-M101 map-assisted claim boundary | `python experiments/E005_external_baseline_transition/tools/plan_m101_map_assisted_claim_boundary_navigation_decision.py` | Inspect `experiments/E005_external_baseline_transition/artifacts/E005-M101_map_assisted_claim_boundary_navigation_decision_v0/coverage.json` |
| E007-M01 navigation/path-cost bridge contract | `python experiments/E007_navigation_path_cost_bridge/tools/plan_m01_navigation_path_cost_bridge_contract.py` | Inspect `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M01_navigation_path_cost_bridge_contract_v0/coverage.json` |
| E007-M02 path-source compatibility | `python experiments/E007_navigation_path_cost_bridge/tools/audit_m02_path_source_compatibility.py` | Inspect `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M02_path_source_compatibility_v0/coverage.json` |
| E007-M03 external candidate grid projection | `python experiments/E007_navigation_path_cost_bridge/tools/project_m03_external_candidate_grid_paths.py` | Inspect `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M03_external_candidate_grid_projection_v0/coverage.json` |
| E007-M04 path-cost policy metrics | `python experiments/E007_navigation_path_cost_bridge/tools/evaluate_m04_path_cost_policy_metrics.py` | Inspect `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M04_path_cost_policy_metrics_v0/coverage.json` |
| E007-M05 path-cost result interpretation | `python experiments/E007_navigation_path_cost_bridge/tools/plan_m05_path_cost_result_interpretation.py` | Inspect `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M05_path_cost_result_interpretation_v0/coverage.json` |
| E007-M06 path-start/source-limit sensitivity | `python experiments/E007_navigation_path_cost_bridge/tools/audit_m06_path_start_source_limit_sensitivity.py` | Inspect `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M06_path_start_source_limit_sensitivity_v0/coverage.json` |
| E007-M07 bridge-table package / navigation decision | `python experiments/E007_navigation_path_cost_bridge/tools/plan_m07_bridge_table_navigation_decision.py` | Inspect `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M07_bridge_table_package_navigation_decision_v0/coverage.json` |
| E008-M01 navigation source / episode contract | `python experiments/E008_real_navigation_benchmark/tools/plan_m01_navigation_source_episode_contract.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M01_navigation_source_episode_contract_v0/coverage.json` |
| E008-M02 `HM3D ObjectNav` adapter smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m02_hm3d_objectnav_adapter_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M02_hm3d_objectnav_adapter_smoke_v0/coverage.json` and `local_dataset/HM3D_navigation_bridge/E008-M02_hm3d_objectnav_adapter_smoke_v0/episode_adapter_rows.jsonl` |
| E008-M03 H001 candidate navigation adapter | `python experiments/E008_real_navigation_benchmark/tools/plan_m03_h001_candidate_navigation_adapter.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M03_h001_candidate_navigation_adapter_contract_v0/coverage.json` and `local_dataset/HM3D_navigation_bridge/E008-M03_h001_candidate_navigation_adapter_contract_v0/episode_goal_eval_rows.jsonl` |
| E008-M04 ObjectNav oracle path smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m04_objectnav_oracle_path_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M04_objectnav_oracle_path_smoke_v0/coverage.json` and `local_dataset/HM3D_navigation_bridge/E008-M04_objectnav_oracle_path_smoke_v0/oracle_path_rows.jsonl` |
| E008-M05 `HM3D` candidate-source staging plan | `python experiments/E008_real_navigation_benchmark/tools/plan_m05_hm3d_candidate_source_staging.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M05_hm3d_candidate_source_staging_plan_v0/coverage.json` and `local_dataset/HM3D_navigation_bridge/E008-M05_hm3d_candidate_source_staging_plan_v0/coverage.json` |
| E008-M06 `HM3D` semantic annotation candidate-source smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m06_hm3d_semantic_candidate_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M06_hm3d_semantic_candidate_source_smoke_v0/coverage.json` and `local_dataset/HM3D_navigation_bridge/E008-M06_hm3d_semantic_candidate_source_smoke_v0/coverage.json` |
| E008-M07 `HM3D` rendered RGB-D detector-source plan | `python experiments/E008_real_navigation_benchmark/tools/plan_m07_hm3d_rendered_rgbd_detector_source.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0/coverage.json` and `local_dataset/HM3D_navigation_bridge/E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0/coverage.json` |
| E008-M08 `HM3D` rendered RGB-D frame staging smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m08_hm3d_rendered_rgbd_frame_staging_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/verify_m08_hm3d_rendered_rgbd_frame_staging.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0/coverage.json`, `verification_coverage.json`, and `local_dataset/HM3D_navigation_bridge/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0/3RScan/scans/<scan_id>/sequence/` |
| E008-M09 `HM3D` rendered RGB-D detector candidate smoke | `python experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py --dataset-root /home/yoohyun/research2/local_dataset/HM3D_navigation_bridge/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0 --m17-dir /home/yoohyun/research2/local_dataset/HM3D_navigation_bridge/E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0/detector_inputs --out-dir /home/yoohyun/research2/experiments/E008_real_navigation_benchmark/artifacts/E008-M09_hm3d_rendered_rgbd_detector_candidate_smoke_v0 --max-scans 6 --max-frames-per-scan 4 --max-labels 5 --max-predictions 12000 --max-predictions-per-frame 100 --threshold 0.08 --text-threshold 0.08 --candidate-selection-policy cap_aware_label_balanced_ranking_v0 --selection-score-mode confidence_log_depth --pre-cap-per-scan-label-cap 24 --pre-cap-spatial-consolidation-radius-m 0.5 --raw-candidate-collection-cap 50000 --export-pre-cap-candidate-pool` | `python experiments/E008_real_navigation_benchmark/tools/verify_m09_hm3d_rendered_rgbd_detector_candidate_smoke.py --require-ready` |
| E008-M10 detector candidate navmesh validation | `python experiments/E008_real_navigation_benchmark/tools/run_m10_detector_candidate_navmesh_validation.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M10_detector_candidate_navmesh_validation_v0/coverage.json`, `candidate_navmesh_rows.jsonl`, and `local_dataset/HM3D_navigation_bridge/E008-M10_detector_candidate_navmesh_validation_v0/coverage.json` |
| E008-M11 detector candidate visit-order path smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m11_detector_candidate_visit_order_path_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M11_detector_candidate_visit_order_path_smoke_v0/coverage.json`, `policy_metric_rows.jsonl`, and `local_dataset/HM3D_navigation_bridge/E008-M11_detector_candidate_visit_order_path_smoke_v0/coverage.json` |
| E008-M12 detector candidate goal-evaluation smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m12_detector_candidate_goal_evaluation_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M12_detector_candidate_goal_evaluation_smoke_v0/coverage.json`, `policy_goal_metric_rows.jsonl`, `leakage_audit_rows.jsonl`, and `local_dataset/HM3D_navigation_bridge/E008-M12_detector_candidate_goal_evaluation_smoke_v0/coverage.json` |
| E008-M13 detector-goal failure audit | `python experiments/E008_real_navigation_benchmark/tools/plan_m13_detector_goal_failure_audit.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M13_detector_goal_failure_audit_v0/coverage.json`, `episode_failure_audit_rows.jsonl`, `coverage_expansion_contract_rows.jsonl`, and `local_dataset/HM3D_navigation_bridge/E008-M13_detector_goal_failure_audit_v0/coverage.json` |
| E008-M14 non-oracle observation coverage plan | `python experiments/E008_real_navigation_benchmark/tools/plan_m14_non_oracle_observation_coverage.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M14_non_oracle_observation_coverage_plan_v0/coverage.json`, `observation_pose_plan_rows.jsonl`, `expanded_render_plan_rows.jsonl`, and `local_dataset/HM3D_navigation_bridge/E008-M14_non_oracle_observation_coverage_plan_v0/coverage.json` |
| E008-M15 non-oracle observation expansion frame staging | `python experiments/E008_real_navigation_benchmark/tools/run_m15_non_oracle_observation_expansion_frame_staging.py`; `python experiments/E008_real_navigation_benchmark/tools/verify_m15_non_oracle_observation_expansion_frame_staging.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M15_non_oracle_observation_expansion_frame_staging_v0/coverage.json`, `verification_coverage.json`, `verification_frame_rows.jsonl`, and `local_dataset/HM3D_navigation_bridge/E008-M15_non_oracle_observation_expansion_frame_staging_v0/snap_validation_rows.jsonl` |
| E008-M16 non-oracle observation expansion detector candidate smoke | `python experiments/E008_real_navigation_benchmark/tools/launch_m16_non_oracle_observation_expansion_detector.py --force`; `python experiments/E008_real_navigation_benchmark/tools/verify_m16_non_oracle_observation_expansion_detector_candidate_smoke.py --require-ready` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0/e008_m16_verification_coverage.json`, `container_output/real_proposals.jsonl`, and `container_output/pre_cap_candidate_pool.jsonl` |
| E008-M17 expanded detector candidate navmesh validation | `python experiments/E008_real_navigation_benchmark/tools/run_m17_expanded_detector_candidate_navmesh_validation.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M17_expanded_detector_candidate_navmesh_validation_v0/coverage.json`, `candidate_navmesh_rows.jsonl`, and `local_dataset/HM3D_navigation_bridge/E008-M17_expanded_detector_candidate_navmesh_validation_v0/coverage.json` |
| E008-M18 expanded detector candidate visit-order path smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m18_expanded_detector_candidate_visit_order_path_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0/coverage.json`, `policy_metric_rows.jsonl`, and `failure_rows.jsonl` |
| E008-M19 expanded detector candidate goal-evaluation smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m19_expanded_detector_candidate_goal_evaluation_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0/coverage.json`, `policy_goal_metric_rows.jsonl`, `failure_rows.jsonl`, and `leakage_audit_rows.jsonl` |
| E008-M20 expanded detector-goal failure comparison and navigation decision | `python experiments/E008_real_navigation_benchmark/tools/plan_m20_expanded_detector_goal_failure_comparison_navigation_decision.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M20_expanded_detector_goal_failure_comparison_navigation_decision_v0/coverage.json`, `policy_delta_rows.jsonl`, `episode_summary_rows.jsonl`, and `navigation_readiness_gate_rows.jsonl` |
| E008-M21 expanded detector-policy trajectory execution contract | `python experiments/E008_real_navigation_benchmark/tools/plan_m21_expanded_detector_policy_trajectory_execution_contract.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M21_expanded_detector_policy_trajectory_execution_contract_v0/coverage.json`, `policy_execution_contract_rows.jsonl`, `trajectory_policy_execution_plan_rows.jsonl`, `docker_preflight_rows.jsonl`, and `docker_command_rows.jsonl` |
| E008-M22 expanded detector-policy trajectory execution smoke | `docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp -v /home/yoohyun/research3/local_dataset/data:/data:ro -v /home/yoohyun/research2:/work -w /work research3/habitat-h001:20260508-calib-artifacts bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m22_expanded_detector_policy_trajectory_execution_smoke.py --m21-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M21_expanded_detector_policy_trajectory_execution_contract_v0 --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0 --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0"` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0/coverage.json`, `trajectory_policy_metric_rows.jsonl`, `trajectory_attempt_rows.jsonl`, `trajectory_failure_rows.jsonl`, and `leakage_audit_rows.jsonl` |
| E008-M23 trajectory-vs-proxy consistency and H001 source decision | `python experiments/E008_real_navigation_benchmark/tools/plan_m23_trajectory_proxy_consistency_h001_source_decision.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M23_trajectory_proxy_consistency_h001_source_decision_v0/coverage.json`, `policy_consistency_rows.jsonl`, `readiness_gate_rows.jsonl`, `h001_candidate_source_decision_rows.jsonl`, and `report.md` |
| E008-M24 H001 candidate-source instantiation contract | `python experiments/E008_real_navigation_benchmark/tools/plan_m24_h001_candidate_source_instantiation_contract.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M24_h001_candidate_source_instantiation_contract_v0/coverage.json`, `source_availability_rows.jsonl`, `policy_instantiation_contract_rows.jsonl`, `leakage_guard_rows.jsonl`, and `report.md` |
| E008-M25 H001 candidate-source materialization smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m25_h001_candidate_source_materialization_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M25_h001_candidate_source_materialization_smoke_v0/coverage.json`, `h001_candidate_source_rows.jsonl`, `h001_query_context_rows.jsonl`, `h001_policy_execution_plan_rows.jsonl`, `leakage_audit_rows.jsonl`, and `report.md` |
| E008-M26 H001 visit-order/path smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m26_h001_visit_order_path_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M26_h001_visit_order_path_smoke_v0/coverage.json`, `h001_candidate_visit_order_rows.jsonl`, `h001_policy_path_metric_rows.jsonl`, `source_filter_accounting_rows.jsonl`, `leakage_audit_rows.jsonl`, and `report.md` |
| E008-M27 H001 leakage-safe goal-evaluation smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m27_h001_goal_evaluation_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M27_h001_goal_evaluation_smoke_v0/coverage.json`, `h001_candidate_goal_eval_rows.jsonl`, `h001_policy_goal_metric_rows.jsonl`, `h001_goal_failure_rows.jsonl`, `leakage_audit_rows.jsonl`, and `report.md` |
| E008-M28 H001 goal-evaluation comparison / trajectory decision | `python experiments/E008_real_navigation_benchmark/tools/plan_m28_h001_goal_evaluation_comparison_trajectory_decision.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M28_h001_goal_evaluation_comparison_trajectory_decision_v0/coverage.json`, `h001_baseline_delta_rows.jsonl`, `episode_task_comparison_rows.jsonl`, `failure_taxonomy_rows.jsonl`, `trajectory_execution_gate_rows.jsonl`, and `report.md` |
| E008-M29 H001 current-observation fallback/source repair contract | `python experiments/E008_real_navigation_benchmark/tools/plan_m29_h001_current_observation_fallback_source_repair.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M29_h001_current_observation_fallback_source_repair_contract_v0/coverage.json`, `repair_contract_rows.jsonl`, `backstop_plan_rows.jsonl`, `repair_opportunity_rows.jsonl`, `repair_gate_rows.jsonl`, and `report.md` |
| E008-M30 H001 current-observation fallback replay smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m30_h001_current_observation_fallback_replay_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M30_h001_current_observation_fallback_replay_smoke_v0/coverage.json`, `fallback_replay_policy_goal_metric_rows.jsonl`, `fallback_replay_delta_rows.jsonl`, `failure_transition_rows.jsonl`, `replay_gate_rows.jsonl`, and `report.md` |
| E008-M31 H001 fallback trajectory contract / source-gap boundary | `python experiments/E008_real_navigation_benchmark/tools/plan_m31_h001_fallback_trajectory_contract_source_gap_boundary.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0/coverage.json`, `h001_fallback_candidate_visit_order_rows.jsonl`, `trajectory_execution_plan_rows.jsonl`, `source_gap_boundary_rows.jsonl`, `readiness_gate_rows.jsonl`, and `report.md` |
| E008-M32 H001 fallback trajectory execution smoke | `docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp -v /home/yoohyun/research3/local_dataset/data:/data:ro -v /home/yoohyun/research2:/work -w /work research3/habitat-h001:20260508-calib-artifacts bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m32_h001_fallback_trajectory_execution_smoke.py --m31-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0 --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M32_h001_fallback_trajectory_execution_smoke_v0 --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M32_h001_fallback_trajectory_execution_smoke_v0"` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M32_h001_fallback_trajectory_execution_smoke_v0/coverage.json`, `trajectory_policy_metric_rows.jsonl`, `trajectory_attempt_rows.jsonl`, `proxy_trajectory_delta_rows.jsonl`, `source_gap_outcome_rows.jsonl`, and `report.md` |
| E008-M33 H001 trajectory result interpretation / baseline alignment | `python experiments/E008_real_navigation_benchmark/tools/plan_m33_h001_trajectory_result_interpretation_baseline_alignment.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M33_h001_trajectory_result_interpretation_baseline_alignment_v0/coverage.json`, `aligned_navigation_metric_rows.jsonl`, `pairwise_baseline_delta_rows.jsonl`, `claim_boundary_rows.jsonl`, `route_decision_rows.jsonl`, and `report.md` |
| E008-M34 dynamic-stale navigation contract | `python experiments/E008_real_navigation_benchmark/tools/plan_m34_dynamic_stale_navigation_contract.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M34_dynamic_stale_navigation_contract_v0/coverage.json`, `dynamic_stale_intervention_plan_rows.jsonl`, `policy_baseline_contract_rows.jsonl`, `metric_contract_rows.jsonl`, `claim_boundary_rows.jsonl`, `route_decision_rows.jsonl`, and `report.md` |
| E008-M35 dynamic-stale overlay materialization smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m35_dynamic_stale_overlay_materialization_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M35_dynamic_stale_overlay_materialization_smoke_v0/coverage.json`, `dynamic_stale_overlay_policy_candidate_rows.jsonl`, `dynamic_stale_overlay_policy_execution_plan_rows.jsonl`, `policy_materialization_summary_rows.jsonl`, `leakage_audit_rows.jsonl`, and `report.md` |
| E008-M36 dynamic-stale overlay trajectory contract | `python experiments/E008_real_navigation_benchmark/tools/plan_m36_dynamic_stale_overlay_trajectory_contract.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M36_dynamic_stale_overlay_trajectory_contract_v0/coverage.json`, `trajectory_execution_plan_rows.jsonl`, `dynamic_stale_overlay_trajectory_candidate_rows.jsonl`, `runner_adaptation_rows.jsonl`, `docker_command_rows.jsonl`, and `report.md` |
| E008-M37 dynamic-stale overlay trajectory execution smoke | `docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp -v /home/yoohyun/research3/local_dataset/data:/data:ro -v /home/yoohyun/research2:/work -w /work research3/habitat-h001:20260508-calib-artifacts bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py --m36-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M36_dynamic_stale_overlay_trajectory_contract_v0 --out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0 --derived-out-root local_dataset/HM3D_navigation_bridge/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0"` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0/coverage.json`, `dynamic_stale_trajectory_policy_metric_rows.jsonl`, `pairwise_policy_delta_rows.jsonl`, `old_location_dead_end_outcome_rows.jsonl`, `claim_boundary_rows.jsonl`, and `report.md` |
| E008-M38 dynamic-stale overlay result interpretation / baseline alignment | `python experiments/E008_real_navigation_benchmark/tools/plan_m38_dynamic_stale_overlay_result_interpretation_baseline_alignment.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M38_dynamic_stale_overlay_result_interpretation_baseline_alignment_v0/coverage.json`, `policy_result_rows.jsonl`, `pairwise_baseline_summary_rows.jsonl`, `failure_diagnosis_rows.jsonl`, `claim_boundary_rows.jsonl`, and `report.md` |
| E008-M39 budget-matched dynamic-stale policy repair / source-gap contract | `python experiments/E008_real_navigation_benchmark/tools/plan_m39_budget_matched_dynamic_stale_policy_repair_source_gap_contract.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M39_budget_matched_policy_repair_source_gap_contract_v0/coverage.json`, `budget_alignment_rows.jsonl`, `repair_policy_contract_rows.jsonl`, `source_gap_contract_rows.jsonl`, `m40_materialization_plan_rows.jsonl`, and `report.md` |
| E008-M40 budget-matched repair row materialization smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m40_budget_matched_repair_row_materialization_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M40_budget_matched_repair_row_materialization_smoke_v0/coverage.json`, `dynamic_stale_overlay_trajectory_candidate_rows.jsonl`, `trajectory_execution_plan_rows.jsonl`, `repair_policy_materialization_summary_rows.jsonl`, `leakage_audit_rows.jsonl`, `m41_command_rows.jsonl`, and `report.md` |
| E008-M41 budget-matched repair trajectory execution smoke | `docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp -v /home/yoohyun/research3/local_dataset/data:/data:ro -v /home/yoohyun/research2:/work -w /work research3/habitat-h001:20260508-calib-artifacts bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m41_budget_matched_repair_trajectory_execution_smoke.py"` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M41_budget_matched_repair_trajectory_execution_smoke_v0/coverage.json`, `dynamic_stale_trajectory_policy_metric_rows.jsonl`, `pairwise_policy_delta_rows.jsonl`, `old_location_dead_end_outcome_rows.jsonl`, `claim_boundary_rows.jsonl`, and `report.md` |
| E008-M42 budget-matched repair result interpretation and scale decision | `python experiments/E008_real_navigation_benchmark/tools/plan_m42_budget_matched_repair_result_interpretation_scale_decision.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M42_budget_matched_repair_result_interpretation_scale_decision_v0/coverage.json`, `policy_result_rows.jsonl`, `source_boundary_rows.jsonl`, `pairwise_decision_rows.jsonl`, `scale_gate_rows.jsonl`, `claim_boundary_rows.jsonl`, and `report.md` |
| E008-M43 dynamic-stale navigation policy redesign contract | `python experiments/E008_real_navigation_benchmark/tools/plan_m43_dynamic_stale_navigation_policy_redesign_contract.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0/coverage.json`, `policy_redesign_contract_rows.jsonl`, `source_expansion_contract_rows.jsonl`, `m44_materialization_plan_rows.jsonl`, `evaluation_gate_rows.jsonl`, `claim_boundary_rows.jsonl`, and `report.md` |
| E008-M44 source-diverse redesign row materialization smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m44_source_diverse_redesign_row_materialization_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M44_source_diverse_redesign_row_materialization_smoke_v0/coverage.json`, `source_diverse_redesign_candidate_rows.jsonl`, `source_diverse_redesign_execution_plan_rows.jsonl`, `policy_materialization_summary_rows.jsonl`, `policy_distinctness_audit_rows.jsonl`, `leakage_audit_rows.jsonl`, `m45_command_rows.jsonl`, and `report.md` |
| E008-M45 source-diverse trajectory contract / Docker preflight | `python experiments/E008_real_navigation_benchmark/tools/plan_m45_source_diverse_redesign_trajectory_contract.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M45_source_diverse_redesign_trajectory_contract_v0/coverage.json`, `trajectory_execution_contract_rows.jsonl`, `runner_compatibility_rows.jsonl`, `docker_preflight_rows.jsonl`, `m46_command_rows.jsonl`, and `report.md` |
| E008-M46 source-diverse trajectory execution smoke | `docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp -v /home/yoohyun/research3/local_dataset/data:/data:ro -v /home/yoohyun/research2:/work -w /work research3/habitat-h001:20260508-calib-artifacts bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m46_source_diverse_redesign_trajectory_execution_smoke.py"` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M46_source_diverse_redesign_trajectory_execution_smoke_v0/coverage.json`, `dynamic_stale_trajectory_policy_metric_rows.jsonl`, `pairwise_policy_delta_rows.jsonl`, `claim_boundary_rows.jsonl`, and `report.md` |
| E008-M47 source-diverse result interpretation and scale decision | `python experiments/E008_real_navigation_benchmark/tools/plan_m47_source_diverse_result_interpretation_scale_decision.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M47_source_diverse_result_interpretation_scale_decision_v0/coverage.json`, `scale_gate_rows.jsonl`, `regression_case_rows.jsonl`, `route_decision_rows.jsonl`, and `report.md` |
| E008-M48 routine-fetch regression/source-gap repair contract | `python experiments/E008_real_navigation_benchmark/tools/plan_m48_routine_fetch_regression_source_gap_repair_contract.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M48_routine_fetch_task_context_regression_source_gap_repair_contract_v0/coverage.json`, `regression_case_diagnosis_rows.jsonl`, `repair_policy_contract_rows.jsonl`, `m49_materialization_plan_rows.jsonl`, `readiness_gate_rows.jsonl`, and `report.md` |
| E008-M49 routine-fetch repair row materialization smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m49_routine_fetch_repair_row_materialization_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M49_routine_fetch_repair_row_materialization_smoke_v0/coverage.json`, `dynamic_stale_overlay_trajectory_candidate_rows.jsonl`, `trajectory_execution_plan_rows.jsonl`, `baseline_preservation_audit_rows.jsonl`, `regression_repair_target_audit_rows.jsonl`, `leakage_audit_rows.jsonl`, and `report.md` |
| E008-M50 routine-fetch repair trajectory contract / Docker preflight | `python experiments/E008_real_navigation_benchmark/tools/plan_m50_routine_fetch_repair_trajectory_contract.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M50_routine_fetch_repair_trajectory_contract_v0/coverage.json`, `trajectory_execution_contract_rows.jsonl`, `runner_compatibility_rows.jsonl`, `docker_preflight_rows.jsonl`, `m51_command_rows.jsonl`, and `report.md` |
| E008-M51 routine-fetch repair trajectory execution smoke | `docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp -v /home/yoohyun/research3/local_dataset/data:/data:ro -v /home/yoohyun/research2:/work -w /work research3/habitat-h001:20260508-calib-artifacts bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m51_routine_fetch_repair_trajectory_execution_smoke.py"` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0/coverage.json`, `dynamic_stale_trajectory_policy_metric_rows.jsonl`, `pairwise_policy_delta_rows.jsonl`, `old_location_dead_end_outcome_rows.jsonl`, `claim_boundary_rows.jsonl`, and `report.md` |
| E008-M52 routine-fetch repair result interpretation and scale decision | `python experiments/E008_real_navigation_benchmark/tools/plan_m52_routine_fetch_repair_result_interpretation_scale_decision.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0/coverage.json`, `scale_gate_rows.jsonl`, `task_context_effect_rows.jsonl`, `source_boundary_rows.jsonl`, `claim_boundary_rows.jsonl`, `route_decision_rows.jsonl`, and `report.md` |
| E008-M53 routine-fetch task-context specificity boundary and next-route decision | `python experiments/E008_real_navigation_benchmark/tools/plan_m53_routine_fetch_task_context_specificity_boundary_next_route.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M53_routine_fetch_task_context_specificity_boundary_next_route_v0/coverage.json`, `task_context_specificity_rows.jsonl`, `specificity_evidence_gate_rows.jsonl`, `claim_boundary_rows.jsonl`, `route_decision_rows.jsonl`, and `report.md` |
| E008-M54 navigation boundary package and paper-table freeze | `python experiments/E008_real_navigation_benchmark/tools/plan_m54_navigation_boundary_package_paper_table_freeze.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M54_navigation_boundary_package_paper_table_freeze_v0/coverage.json`, `paper_navigation_table_rows.csv`, `paper_table_freeze_rows.jsonl`, `allowed_claim_rows.jsonl`, `blocked_claim_rows.jsonl`, `next_route_rows.jsonl`, and `report.md` |
| E008-M55 source-gap candidate-generation repair feasibility decision | `python experiments/E008_real_navigation_benchmark/tools/plan_m55_source_gap_candidate_generation_repair_feasibility.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M55_source_gap_candidate_generation_repair_feasibility_v0/coverage.json`, `source_gap_episode_rows.jsonl`, `candidate_generation_feasibility_rows.jsonl`, `evidence_gate_rows.jsonl`, `route_decision_rows.jsonl`, and `report.md` |
| E008-M56 source-gap candidate-source expansion contract | `python experiments/E008_real_navigation_benchmark/tools/plan_m56_source_gap_candidate_source_expansion_contract.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M56_source_gap_candidate_source_expansion_contract_v0/coverage.json`, `source_gap_case_rows.jsonl`, `full_pool_hit_diagnostic_rows.jsonl`, `allowed_input_contract_rows.jsonl`, `blocked_input_rows.jsonl`, `materialization_plan_rows.jsonl`, and `report.md` |
| E008-M57 source-gap full-pool candidate-source feature audit | `python experiments/E008_real_navigation_benchmark/tools/plan_m57_source_gap_full_pool_candidate_source_feature_audit.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0/coverage.json`, `source_gap_full_pool_candidate_feature_rows.jsonl`, `source_gap_promoter_rule_audit_rows.jsonl`, `source_gap_promoter_feasibility_gate_rows.jsonl`, and `report.md` |
| E008-M58 source-gap high-path tail-slot policy materialization | `python experiments/E008_real_navigation_benchmark/tools/run_m58_source_gap_high_path_tail_slot_policy_materialization.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0/coverage.json`, `high_path_tail_candidate_rows.jsonl`, `trajectory_execution_plan_rows.jsonl`, `source_gap_episode_recovery_rows.jsonl`, `leakage_audit_rows.jsonl`, and `report.md` |
| E008-M59 high-path tail-slot leakage-safe goal-evaluation smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m59_high_path_tail_slot_goal_evaluation_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0/coverage.json`, `high_path_tail_policy_goal_metric_rows.jsonl`, `pairwise_policy_delta_rows.jsonl`, `source_gap_goal_recovery_rows.jsonl`, `readiness_gate_rows.jsonl`, and `report.md` |
| E008-M60 high-path tail-slot trajectory contract / Docker preflight | `python experiments/E008_real_navigation_benchmark/tools/plan_m60_high_path_tail_slot_trajectory_contract.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M60_high_path_tail_slot_trajectory_contract_v0/coverage.json`, `trajectory_execution_contract_rows.jsonl`, `runner_compatibility_rows.jsonl`, `docker_preflight_rows.jsonl`, `m61_command_rows.jsonl`, and `report.md` |
| E008-M61 high-path tail-slot trajectory execution smoke | `docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp -v /home/yoohyun/research3/local_dataset/data:/data:ro -v /home/yoohyun/research2:/work -w /work research3/habitat-h001:20260508-calib-artifacts bash -lc "micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m61_high_path_tail_slot_trajectory_execution_smoke.py"` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0/coverage.json`, `dynamic_stale_trajectory_policy_metric_rows.jsonl`, `pairwise_policy_delta_rows.jsonl`, `claim_boundary_rows.jsonl`, and `report.md` |
| E008-M62 high-path tail-slot result interpretation and scale decision | `python experiments/E008_real_navigation_benchmark/tools/plan_m62_high_path_tail_slot_result_interpretation_scale_decision.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0/coverage.json`, `policy_result_rows.jsonl`, `source_boundary_rows.jsonl`, `scale_gate_rows.jsonl`, `route_decision_rows.jsonl`, and `report.md` |
| E008-M63 high-path tail-slot scale-up contract and source-boundary baseline plan | `python experiments/E008_real_navigation_benchmark/tools/plan_m63_high_path_tail_slot_scaleup_contract.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M63_high_path_tail_slot_scaleup_contract_v0/coverage.json`, `scale_denominator_contract_rows.jsonl`, `split_plan_rows.jsonl`, `source_boundary_guard_rows.jsonl`, `baseline_plan_rows.jsonl`, `m64_materialization_plan_rows.jsonl`, and `report.md` |
| E008-M64 full-val-mini high-path scale denominator materialization | `python experiments/E008_real_navigation_benchmark/tools/plan_m64_full_val_mini_high_path_scale_materialization.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M64_full_val_mini_high_path_scale_materialization_v0/coverage.json`, `episode_task_context_rows.jsonl`, `render_plan_rows.jsonl`, `detector_manifest_rows.jsonl`, `core_policy_execution_plan_rows.jsonl`, `leakage_audit_rows.jsonl`, `readiness_gate_rows.jsonl`, and `report.md` |
| E008-M65 full-val-mini render/detector contract | `python experiments/E008_real_navigation_benchmark/tools/plan_m65_full_val_mini_render_detector_contract.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M65_full_val_mini_render_detector_contract_v0/coverage.json`, `render_plan_rows.jsonl`, `detector_manifest_rows.jsonl`, `detector_object_target_rows.jsonl`, `long_job_command_rows.jsonl`, `readiness_gate_rows.jsonl`, and `report.md` |
| E008-M66 full-val-mini render launch / repair / verification | `python experiments/E008_real_navigation_benchmark/tools/launch_m66_full_val_mini_render_frame_staging.py`; `python experiments/E008_real_navigation_benchmark/tools/repair_m66_full_val_mini_render_frame_staging.py`; `python experiments/E008_real_navigation_benchmark/tools/verify_m66_full_val_mini_render_frame_staging.py --require-ready` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M65_full_val_mini_render_detector_contract_v0/verification_coverage.json`, `verification_frame_rows.jsonl`, `verification_scan_rows.jsonl`, and `experiments/E008_real_navigation_benchmark/artifacts/E008-M66_full_val_mini_render_frame_staging_repair_v0/repair_coverage.json` |
| E008-M67 full-val-mini detector candidate-source launch / verification | Launch command is recorded in `experiments/E008_real_navigation_benchmark/README.md` under `E008-M67`; log `logs/20260531_230150_e008_m67_full_val_mini_detector.log` | Verify with `python experiments/E008_real_navigation_benchmark/tools/verify_m16_non_oracle_observation_expansion_detector_candidate_smoke.py --m15-artifact-dir /home/yoohyun/research2/experiments/E008_real_navigation_benchmark/artifacts/E008-M65_full_val_mini_render_detector_contract_v0 --m15-data-dir /home/yoohyun/research2/local_dataset/HM3D_navigation_bridge/E008-M65_full_val_mini_render_detector_contract_v0 --m16-dir /home/yoohyun/research2/experiments/E008_real_navigation_benchmark/artifacts/E008-M67_full_val_mini_detector_candidate_source_v0 --tmux-session e008_m67_full_val_mini_detector --require-ready`; inspect `coverage.json`, `container_output/real_proposals.jsonl`, `container_output/pre_cap_candidate_pool.jsonl`, `validator/coverage.json`, and `matching/coverage.json` |
| E008-M68 full-val-mini detector candidate navmesh validation | `python experiments/E008_real_navigation_benchmark/tools/run_m68_full_val_mini_detector_candidate_navmesh_validation.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M68_full_val_mini_detector_candidate_navmesh_validation_v0/coverage.json`, `candidate_navmesh_validation_rows.jsonl`, `scan_source_boundary_rows.jsonl`, `episode_task_source_ready_rows.jsonl`, `failure_taxonomy_rows.jsonl`, `route_decision_rows.jsonl`, and `report.md` |
| E008-M69 full-val-mini detector candidate visit-order/path smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m69_full_val_mini_detector_candidate_visit_order_path_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M69_full_val_mini_detector_candidate_visit_order_path_smoke_v0/coverage.json`, `candidate_visit_order_rows.jsonl`, `policy_metric_rows.jsonl`, `episode_task_policy_metric_rows.jsonl`, `failure_rows.jsonl`, `route_decision_rows.jsonl`, and `report.md` |
| E008-M70 full-val-mini leakage-safe detector candidate goal-evaluation smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m70_full_val_mini_detector_candidate_goal_evaluation_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M70_full_val_mini_detector_candidate_goal_evaluation_smoke_v0/coverage.json`, `full_val_mini_eval_goal_rows.jsonl`, `candidate_goal_eval_rows.jsonl`, `policy_goal_metric_rows.jsonl`, `episode_task_goal_metric_rows.jsonl`, `leakage_audit_rows.jsonl`, `failure_rows.jsonl`, `route_decision_rows.jsonl`, and `report.md` |
| E008-M71 full-val-mini detector-goal failure comparison and trajectory decision | `python experiments/E008_real_navigation_benchmark/tools/plan_m71_full_val_mini_detector_goal_failure_comparison_trajectory_decision.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M71_full_val_mini_detector_goal_failure_comparison_trajectory_decision_v0/coverage.json`, `policy_comparison_rows.jsonl`, `failure_episode_rows.jsonl`, `episode_policy_outcome_rows.jsonl`, `navigation_readiness_gate_rows.jsonl`, `trajectory_decision_rows.jsonl`, `claim_boundary_rows.jsonl`, and `report.md` |
| E008-M72 full-val-mini detector-policy trajectory contract and Docker preflight | `python experiments/E008_real_navigation_benchmark/tools/plan_m72_full_val_mini_detector_policy_trajectory_contract.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M72_full_val_mini_detector_policy_trajectory_contract_v0/coverage.json`, `dynamic_stale_overlay_trajectory_candidate_rows.jsonl`, `trajectory_execution_plan_rows.jsonl`, `episode_goal_eval_rows.jsonl`, `oracle_path_rows.jsonl`, `budget_proxy_summary_rows.jsonl`, `docker_preflight_rows.jsonl`, `m73_command_rows.jsonl`, and `report.md` |
| E008-M73 full-val-mini detector-policy trajectory runner scaffold | `python -m py_compile experiments/E008_real_navigation_benchmark/tools/run_m73_full_val_mini_detector_policy_trajectory_execution_smoke.py`; `python experiments/E008_real_navigation_benchmark/tools/run_m73_full_val_mini_detector_policy_trajectory_execution_smoke.py --help`; `python experiments/E008_real_navigation_benchmark/tools/plan_m72_full_val_mini_detector_policy_trajectory_contract.py` | Inspect M72 `coverage.json` for `status=e008_m72_full_val_mini_detector_policy_trajectory_contract_ready_runner_next`, `runner_implemented=true`, and `runner_py_compile_pass=true` |
| E008-M73 full-val-mini detector-policy trajectory execution smoke | Use the Docker command recorded in `experiments/E008_real_navigation_benchmark/artifacts/E008-M72_full_val_mini_detector_policy_trajectory_contract_v0/m73_command_rows.jsonl` | Expected output: `experiments/E008_real_navigation_benchmark/artifacts/E008-M73_full_val_mini_detector_policy_trajectory_execution_smoke_v0/coverage.json` with `status=e008_m73_full_val_mini_detector_policy_trajectory_execution_smoke_ready` and `scan_task_policy_rows=120` |
| E008-M74 full-val-mini detector-policy result interpretation | `python experiments/E008_real_navigation_benchmark/tools/plan_m74_full_val_mini_detector_policy_result_interpretation.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M74_full_val_mini_detector_policy_result_interpretation_v0/coverage.json`, `diagnostic_policy_table.csv`, `gate_rows.jsonl`, `claim_boundary_rows.jsonl`, and `report.md` |
| E008-M75 source-gap/SPL repair contract | `python experiments/E008_real_navigation_benchmark/tools/plan_m75_source_gap_spl_repair_contract.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M75_source_gap_spl_repair_contract_v0/coverage.json`, `repair_problem_rows.jsonl`, `policy_repair_contract_rows.jsonl`, `input_guard_rows.jsonl`, `evaluation_gate_rows.jsonl`, and `report.md` |
| E008-M76 source-gap/SPL repair row materialization | `python experiments/E008_real_navigation_benchmark/tools/run_m76_source_gap_spl_repair_row_materialization_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M76_source_gap_spl_repair_row_materialization_smoke_v0/coverage.json`, `repair_candidate_visit_order_rows.jsonl`, `budget_accounting_rows.jsonl`, `leakage_audit_rows.jsonl`, and `report.md` |
| E008-M77 source-gap/SPL repair goal evaluation | `python experiments/E008_real_navigation_benchmark/tools/run_m77_source_gap_spl_repair_goal_evaluation_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M77_source_gap_spl_repair_goal_evaluation_smoke_v0/coverage.json`, `aggregate_policy_goal_metric_rows.jsonl`, `policy_delta_summary_rows.jsonl`, `policy_pairwise_delta_rows.jsonl`, `gate_rows.jsonl`, and `report.md` |
| E008-M78 source-gap/SPL repair result interpretation | `python experiments/E008_real_navigation_benchmark/tools/plan_m78_source_gap_spl_repair_result_interpretation.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M78_source_gap_spl_repair_result_interpretation_v0/coverage.json`, `budget5_loss_diagnosis_rows.jsonl`, `source_gap_interpretation_rows.jsonl`, `route_candidate_rows.jsonl`, and `report.md` |
| E008-M79 source-gap candidate-source expansion and loss-safe policy contract | `python experiments/E008_real_navigation_benchmark/tools/plan_m79_source_gap_candidate_source_expansion_loss_safe_policy_contract.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M79_source_gap_candidate_source_expansion_loss_safe_policy_contract_v0/coverage.json`, `expansion_case_rows.jsonl`, `loss_safe_policy_contract_rows.jsonl`, `source_expansion_contract_rows.jsonl`, and `report.md` |
| E008-M80 loss-safe candidate-source expansion row materialization | `python experiments/E008_real_navigation_benchmark/tools/run_m80_loss_safe_candidate_source_expansion_row_materialization_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M80_loss_safe_candidate_source_expansion_row_materialization_smoke_v0/coverage.json`, `loss_safe_candidate_visit_order_rows.jsonl`, `budget_invariant_rows.jsonl`, `leakage_audit_rows.jsonl`, and `report.md` |
| E008-M81 loss-safe candidate-source expansion goal evaluation | `python experiments/E008_real_navigation_benchmark/tools/run_m81_loss_safe_candidate_source_expansion_goal_evaluation_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M81_loss_safe_candidate_source_expansion_goal_evaluation_smoke_v0/coverage.json`, `aggregate_policy_goal_metric_rows.jsonl`, `policy_delta_summary_rows.jsonl`, `source_boundary_goal_metric_rows.jsonl`, `leakage_audit_rows.jsonl`, and `report.md` |
| E008-M82 loss-safe candidate-source expansion result interpretation | `python experiments/E008_real_navigation_benchmark/tools/plan_m82_loss_safe_candidate_source_expansion_result_interpretation.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M82_loss_safe_candidate_source_expansion_result_interpretation_v0/coverage.json`, `append_gain_interpretation_rows.jsonl`, `source_gap_decision_rows.jsonl`, `trajectory_source_expansion_decision_rows.jsonl`, and `report.md` |
| E008-M83 source-gap non-oracle source/observation expansion contract | `python experiments/E008_real_navigation_benchmark/tools/plan_m83_source_gap_non_oracle_source_observation_expansion_contract.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M83_source_gap_non_oracle_source_observation_expansion_contract_v0/coverage.json`, `source_gap_contract_case_rows.jsonl`, `source_observation_expansion_route_rows.jsonl`, `materialization_contract_rows.jsonl`, `long_job_policy_rows.jsonl`, and `report.md` |
| E008-M84 source-gap non-oracle source/observation expansion materialization smoke | `python experiments/E008_real_navigation_benchmark/tools/run_m84_source_gap_non_oracle_source_observation_expansion_materialization_smoke.py` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0/coverage.json`, `source_gap_observation_pose_plan_rows.jsonl`, `source_gap_render_plan_rows.jsonl`, `source_gap_detector_manifest_rows.jsonl`, `long_job_command_rows.jsonl`, and `report.md` |
| E008-M85 source-gap render frame staging launch / verification | `python experiments/E008_real_navigation_benchmark/tools/launch_m85_source_gap_render_frame_staging.py`; `python experiments/E008_real_navigation_benchmark/tools/verify_m85_source_gap_render_frame_staging.py --require-ready` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M85_source_gap_render_frame_staging_launch_v0/launch_coverage.json`, `experiments/E008_real_navigation_benchmark/artifacts/E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0/m85_verification_coverage.json`, `render_summary.json`, `rendered_frame_rows.jsonl`, and `snap_validation_rows.jsonl` |
| E008-M86 source-gap detector candidate-source launch / verification | `python experiments/E008_real_navigation_benchmark/tools/launch_m86_source_gap_detector_candidate_source.py`; `python experiments/E008_real_navigation_benchmark/tools/verify_m86_source_gap_detector_candidate_source.py --require-ready` | Inspect `experiments/E008_real_navigation_benchmark/artifacts/E008-M86_source_gap_detector_candidate_source_launch_v0/launch_coverage.json`, `experiments/E008_real_navigation_benchmark/artifacts/E008-M86_source_gap_detector_candidate_source_v0/e008_m86_verification_coverage.json`, `container_output/real_proposals.jsonl`, `container_output/pre_cap_candidate_pool.jsonl`, `validator/coverage.json`, and `matching/coverage.json` |
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

- The safest minimal Drive package for moving machines is: selected `Open3DSG` checkpoint, `h001-open3dsg-repro:cu128` image tar, E005-M45/M49/M52/M53/M54/M66/M67/M68/M69/M70/M71/M75/M76/M77/M78/M79/M80/M81/M82/M83/M84/M85/M86/M87/M88/M89/M90/M91/M92/M93/M94/M95/M96/M97/M98 row-level artifacts, E003-M75 bridge artifact, `local_dataset/Open3DSG_bridge/`, and dataset manifests/raw data only if license permits.

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
