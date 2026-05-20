#!/usr/bin/env python3
"""Plan Open3DSG object-candidate export without modifying staged source data."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
STAGED_ROOT = Path("/home/yoohyun/research/local_dataset/Open3DSG_staged")
LOCAL_DATA_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M58_object_candidate_export_plan_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E005-M58_object_candidate_export_plan_v0"
M57_LOCAL_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M57_output_schema_contract_v0"
M57_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E005-M57_open3dsg_output_schema_contract_v0"
VERSION = "e005_m58_open3dsg_object_candidate_export_plan_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path: Path, base: Path = STAGED_ROOT) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def find_line_numbers(path: Path, needles: list[str]) -> dict[str, int | None]:
    if not path.exists():
        return {needle: None for needle in needles}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    out: dict[str, int | None] = {}
    for needle in needles:
        found = None
        for idx, line in enumerate(lines, start=1):
            if needle in line:
                found = idx
                break
        out[needle] = found
    return out


def collect_source_context() -> dict[str, Any]:
    trainer = (
        STAGED_ROOT
        / "h001_runtime"
        / "source"
        / "open3dsg_source"
        / "open3dsg"
        / "scripts"
        / "trainer.py"
    )
    run_py = (
        STAGED_ROOT
        / "h001_runtime"
        / "source"
        / "open3dsg_source"
        / "open3dsg"
        / "scripts"
        / "run.py"
    )
    hparams = STAGED_ROOT / "h001_runtime" / "mlops" / "opensg" / "tensorboards" / "tmp" / "version_0" / "hparams.yaml"
    checkpoint_dir = (
        STAGED_ROOT
        / "training_repro"
        / "mlops"
        / "opensg"
        / "mlflow"
        / "363094050435167554"
        / "2a23a9af581b4666a207423aa6217853"
        / "checkpoints"
    )
    selected_checkpoint = checkpoint_dir / "last.ckpt"
    alternate_checkpoint = checkpoint_dir / "epoch=19-step=18720.ckpt"
    feature_dir = STAGED_ROOT / "training_repro" / "output" / "features" / "clip_features_h001_official_blip_top5_scales3"
    return {
        "read_only_source_root": str(STAGED_ROOT),
        "source_files": {
            "trainer_py": {
                "path": rel(trainer),
                "exists": trainer.exists(),
                "line_hints": find_line_numbers(
                    trainer,
                    [
                        "def test_step",
                        "objects_predict, objects_probs, object_mostlikely, objects_valid",
                        "eval_dict['objects_predict']",
                        "eval_dict['objects_probs']",
                        "OPEN3DSG_RAW_DUMP_JSONL",
                        "predicate_scores",
                    ],
                ),
            },
            "run_py": {
                "path": rel(run_py),
                "exists": run_py.exists(),
                "line_hints": find_line_numbers(run_py, ["--test", "--checkpoint", "--quick_eval", "--load_features"]),
            },
            "hparams_yaml": {
                "path": rel(hparams),
                "exists": hparams.exists(),
            },
        },
        "runtime_assets": {
            "selected_checkpoint_host": str(selected_checkpoint),
            "selected_checkpoint_container": "/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/last.ckpt",
            "alternate_checkpoint_host": str(alternate_checkpoint),
            "selected_checkpoint_exists": selected_checkpoint.exists(),
            "alternate_checkpoint_exists": alternate_checkpoint.exists(),
            "feature_dir_host": str(feature_dir),
            "feature_dir_container": "/workspace/local_dataset/Open3DSG_staged/training_repro/output/features/clip_features_h001_official_blip_top5_scales3",
            "feature_dir_exists": feature_dir.exists(),
        },
        "source_policy": {
            "source_modified": False,
            "source_write_allowed": False,
            "derived_output_root": str(LOCAL_DATA_DIR),
            "docker_mount": f"-v {STAGED_ROOT}:/workspace/local_dataset/Open3DSG_staged:ro",
        },
    }


def build_object_candidate_schema() -> dict[str, Any]:
    return {
        "schema_id": "open3dsg_object_candidate_jsonl_v0",
        "record_type": "open3dsg_object_candidate",
        "purpose": "Raw per-object Open3DSG object-class candidates for later H001 query conversion.",
        "unit": "one row per predicted object-node and candidate label",
        "required_fields": [
            "schema_version",
            "record_type",
            "baseline_run_id",
            "checkpoint_path",
            "model_source_stage",
            "scan_id",
            "raw_scan_id",
            "subset_split_id",
            "subgraph_id",
            "object_id",
            "object_node_index",
            "object_count",
            "candidate_label",
            "candidate_rank",
            "candidate_score",
            "score_type",
            "candidate_vocab",
            "object_vocab_size",
            "bbox_or_center",
            "source_tensors",
        ],
        "optional_eval_only_fields": [
            "gt_object_label",
            "gt_object_category_id",
            "id2name_label",
            "objects_cat_raw",
        ],
        "blocked_policy_fields": [
            "gt_object_label",
            "gt_object_category_id",
            "id2name_label",
            "objects_cat_raw",
        ],
        "field_semantics": {
            "candidate_label": "Object label decoded from Open3DSG object vocabulary index, not from GT id2name.",
            "candidate_rank": "0-indexed rank after sorting objects_probs descending for the object node.",
            "candidate_score": "Score from objects_probs[object_node_index, candidate_label_index].",
            "score_type": "open3dsg_objects_probs",
            "bbox_or_center": "Geometry copied from preprocessed graph data only for evaluation/search-cost joins.",
            "source_tensors": ["objects_probs", "objects_predict", "objects_predict_mostlikely", "objects_valid"],
        },
        "top_k_default": 20,
        "leakage_rule": "Ranking and candidate labels must use Open3DSG prediction tensors only; GT labels are eval-only.",
    }


def build_query_candidate_schema() -> dict[str, Any]:
    return {
        "schema_id": "open3dsg_query_candidate_jsonl_v0",
        "record_type": "open3dsg_query_candidate",
        "purpose": "Join raw Open3DSG object candidates to the H001 query denominator.",
        "required_fields": [
            "query_id",
            "query_label",
            "query_scan_id",
            "query_subset_split_id",
            "target_object_id",
            "candidate_object_id",
            "candidate_label",
            "candidate_rank",
            "candidate_score",
            "strict_bbox_hit",
            "relaxed_bbox_hit_1m",
            "expected_search_cost_proxy",
            "baseline_run_id",
            "source_object_candidate_record_id",
        ],
        "join_rule": [
            "Filter raw object-candidate rows by query scan/subgraph.",
            "Keep candidate rows where candidate_label matches query_label after the same normalization used in H001 M38/M52.",
            "Rank by candidate_score descending, with stable tie-breakers object_id and candidate_rank.",
            "Compute strict/relaxed hit against target_object_id and target bbox/center only after ranking.",
        ],
        "metric_targets": [
            "strict_bbox_top5",
            "relaxed_bbox_1m_top3",
            "ExpectedSearchCost",
            "proxy_SR",
            "proxy_SPL",
            "failure_reduction_vs_static_and_ConceptGraphs",
        ],
    }


def build_export_hook_contract(source_context: dict[str, Any]) -> dict[str, Any]:
    return {
        "contract_id": "open3dsg_object_candidate_export_hook_contract_v0",
        "execution_policy": "Do not edit Open3DSG_staged; use a local runtime patch/copy or monkey patch mounted from research2.",
        "source_tensor_location": {
            "file": source_context["source_files"]["trainer_py"]["path"],
            "test_step_source": "eval_dict['objects_predict'] and eval_dict['objects_probs'] are populated during D3SSGModule.test_step.",
            "object_score_source": "objects_probs",
            "object_topk_source": "objects_predict",
        },
        "new_env_vars": {
            "OPEN3DSG_OBJECT_DUMP_JSONL": "/out/open3dsg_object_candidates.jsonl",
            "OPEN3DSG_OBJECT_DUMP_COMPLETED_JSONL": "/out/open3dsg_object_candidates.completed.jsonl",
            "OPEN3DSG_OBJECT_DUMP_MANIFEST_JSON": "/out/open3dsg_object_candidates.manifest.json",
            "OPEN3DSG_OBJECT_DUMP_STREAM_BATCHES": "1",
            "OPEN3DSG_OBJECT_DUMP_RESUME": "1",
            "OPEN3DSG_OBJECT_DUMP_TOPK": "20",
            "OPEN3DSG_OBJECT_DUMP_MAX_BATCHES": "1",
            "OPEN3DSG_BASELINE_RUN_ID": "open3dsg_h001_last_ckpt_object_candidate_smoke",
            "OPEN3DSG_CHECKPOINT": source_context["runtime_assets"]["selected_checkpoint_container"],
            "OPEN3DSG_MODEL_SOURCE_STAGE": "open3dsg_staged_read_only_runtime_patch",
        },
        "implementation_requirements": [
            "Add object-candidate streaming in a local patch that mirrors the existing relation raw dump resume/completion behavior.",
            "Decode candidate_label from the same obj_class_dict used by _predict_obj_from_clip.",
            "Write top-k candidates per object node before query filtering.",
            "Include GT/id2name only as eval-only diagnostics, never as ranking input.",
            "Support OPEN3DSG_OBJECT_DUMP_MAX_BATCHES=1 for a bounded smoke test.",
        ],
        "smoke_success_criteria": [
            "one-batch Docker run exits 0 or exits intentionally after dump",
            "object candidate JSONL exists under research2/local_dataset/Open3DSG_bridge/E005-M58_object_candidate_export_plan_v0 or successor M59 directory",
            "rows_written > 0",
            "all required schema fields present",
            "source_modified is false",
        ],
    }


def build_docker_command_contract(source_context: dict[str, Any]) -> dict[str, Any]:
    output_container = "/out"
    source_container = "/workspace/local_dataset/Open3DSG_staged"
    tools_container = "/workspace/research2/tools"
    checkpoint = source_context["runtime_assets"]["selected_checkpoint_container"]
    features = source_context["runtime_assets"]["feature_dir_container"]
    python_command = " ".join(
        [
            "python",
            "open3dsg/scripts/run.py",
            "--test",
            "--dataset 3rscan",
            f"--checkpoint {checkpoint}",
            "--n_beams 5",
            "--weight_2d 0.5",
            "--clip_model OpenSeg",
            "--node_model ViT-L/14@336px",
            "--blip",
            "--avg_blip_emb",
            "--use_rgb",
            f"--load_features {features}",
            "--top_k_frames 5",
            "--scales 3",
            "--gpus 1",
            "--workers 0",
            "--quick_eval",
            "--run_name tmp_open3dsg_object_dump_smoke",
        ]
    )
    docker_args = [
        "docker",
        "run",
        "--rm",
        "--gpus",
        "all",
        "-v",
        f"{STAGED_ROOT}:{source_container}:ro",
        "-v",
        f"{LOCAL_DATA_DIR}:{output_container}",
        "-v",
        f"{EXP_ROOT / 'tools'}:{tools_container}:ro",
        "-e",
        f"OPEN3DSG_OBJECT_DUMP_JSONL={output_container}/open3dsg_object_candidates.jsonl",
        "-e",
        f"OPEN3DSG_OBJECT_DUMP_COMPLETED_JSONL={output_container}/open3dsg_object_candidates.completed.jsonl",
        "-e",
        f"OPEN3DSG_OBJECT_DUMP_MANIFEST_JSON={output_container}/open3dsg_object_candidates.manifest.json",
        "-e",
        "OPEN3DSG_OBJECT_DUMP_STREAM_BATCHES=1",
        "-e",
        "OPEN3DSG_OBJECT_DUMP_RESUME=1",
        "-e",
        "OPEN3DSG_OBJECT_DUMP_TOPK=20",
        "-e",
        "OPEN3DSG_OBJECT_DUMP_MAX_BATCHES=1",
        "-e",
        "OPEN3DSG_BASELINE_RUN_ID=open3dsg_h001_last_ckpt_object_candidate_smoke",
        "-e",
        f"OPEN3DSG_CHECKPOINT={checkpoint}",
        "-e",
        "OPEN3DSG_MODEL_SOURCE_STAGE=open3dsg_staged_read_only_runtime_patch",
        "h001-open3dsg-repro:cu128",
        "bash",
        "-lc",
        (
            f"cd {source_container}/h001_runtime/source/open3dsg_source && "
            f"python {tools_container}/m59_open3dsg_object_dump_runtime_patch.py "
            f"--source-root . -- {python_command}"
        ),
    ]
    return {
        "contract_id": "open3dsg_object_candidate_docker_smoke_command_v0",
        "command_status": "template_only_waiting_for_m59_runtime_patch",
        "docker_image": "h001-open3dsg-repro:cu128",
        "working_directory_host": str(ROOT),
        "source_mount": {
            "host": str(STAGED_ROOT),
            "container": source_container,
            "mode": "read_only",
        },
        "output_mount": {
            "host": str(LOCAL_DATA_DIR),
            "container": output_container,
            "mode": "read_write",
        },
        "tools_mount": {
            "host": str(EXP_ROOT / "tools"),
            "container": tools_container,
            "mode": "read_only",
        },
        "expected_output_files": [
            "open3dsg_object_candidates.jsonl",
            "open3dsg_object_candidates.completed.jsonl",
            "open3dsg_object_candidates.manifest.json",
        ],
        "verification_command": (
            "python experiments/E005_external_baseline_transition/tools/"
            "verify_m58_open3dsg_object_candidate_export.py --require-output"
        ),
        "docker_args": docker_args,
        "tmux_template": (
            "mkdir -p logs && tmux new -d -s e005_m59_open3dsg_object_export "
            "'cd /home/yoohyun/research2 && <docker command from docker_args> "
            "> logs/<timestamp>_e005_m59_open3dsg_object_export.log 2>&1'"
        ),
        "not_launched_in_m58": True,
    }


def build_verification_contract() -> dict[str, Any]:
    return {
        "contract_id": "open3dsg_object_candidate_verification_contract_v0",
        "plan_verification_command": (
            "python experiments/E005_external_baseline_transition/tools/"
            "verify_m58_open3dsg_object_candidate_export.py"
        ),
        "output_verification_command": (
            "python experiments/E005_external_baseline_transition/tools/"
            "verify_m58_open3dsg_object_candidate_export.py --require-output"
        ),
        "checks": [
            "required contract files exist",
            "object candidate schema has required fields",
            "query candidate schema has required fields",
            "Docker command mounts Open3DSG_staged read-only",
            "derived output root is under research2/local_dataset/Open3DSG_bridge",
            "if candidate rows exist, all required fields are present",
        ],
    }


def build_next_actions() -> dict[str, Any]:
    return {
        "selected_next_unit": "E005-M59 Open3DSG object-candidate export hook implementation / one-batch Docker smoke",
        "why": [
            "M58 fixes the object-candidate schema and Docker/run contract, but does not create candidate rows.",
            "Query-level conversion cannot be judged until one-batch candidate rows exist.",
            "The next step should implement a local runtime patch only under research2 and keep Open3DSG_staged read-only.",
        ],
        "after_m59_if_pass": "E005-M60 Open3DSG query-level conversion smoke on H001 denominator",
        "after_m59_if_fail": "Classify failure as runtime/env/schema/checkpoint/data split, then decide whether Open3DSG remains a feasible second baseline.",
        "blocked_claims": [
            "Open3DSG query-level search baseline performance",
            "second external map baseline generality claim",
            "final real RGB-D/open-vocabulary robustness",
            "real navigation SR/SPL",
        ],
    }


def build_report(
    coverage: dict[str, Any],
    object_schema: dict[str, Any],
    hook_contract: dict[str, Any],
    docker_contract: dict[str, Any],
    next_actions: dict[str, Any],
) -> str:
    lines = [
        "# E005-M58 Open3DSG Object Candidate Export Plan",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- Read-only source: `{coverage['staged_root']}`.",
        f"- Derived output root: `{coverage['local_output_dir']}`.",
        f"- Source modified: {coverage['source_modified']}.",
        f"- Selected checkpoint exists: {coverage['selected_checkpoint_exists']}.",
        f"- Feature dir exists: {coverage['feature_dir_exists']}.",
        f"- Object candidate schema fields: {len(object_schema['required_fields'])}.",
        f"- Docker image: `{docker_contract['docker_image']}`.",
        "",
        "## Contract Decision",
        "",
        "- `Open3DSG` relation raw dump is not enough for object-search evaluation.",
        "- M58 uses `objects_probs` / `objects_predict` as the planned source for raw object candidates.",
        "- The export must be implemented as a local runtime patch or copied source under `research2`, not as edits under `Open3DSG_staged`.",
        "- GT labels and `id2name` are allowed only as eval diagnostics, not as ranking signals.",
        "",
        "## Smoke Criteria",
        "",
        *[f"- {item}" for item in hook_contract["smoke_success_criteria"]],
        "",
        "## Next Action",
        "",
        f"- {next_actions['selected_next_unit']}.",
        "",
    ]
    return "\n".join(lines)


def run() -> dict[str, Any]:
    m57_artifact = read_json(M57_ARTIFACT_DIR / "coverage.json")
    m57_contract = read_json(M57_LOCAL_DIR / "conversion_contract.json")
    if m57_artifact.get("status") != "e005_m57_open3dsg_output_schema_contract_ready_object_candidate_export_needed":
        raise RuntimeError(f"M57 artifact is not ready: {m57_artifact.get('status')}")
    if m57_contract.get("contract_id") != "open3dsg_query_conversion_contract_v0":
        raise RuntimeError("Missing M57 conversion contract.")
    if not STAGED_ROOT.exists():
        raise RuntimeError(f"Missing read-only Open3DSG source: {STAGED_ROOT}")

    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    source_context = collect_source_context()
    object_schema = build_object_candidate_schema()
    query_schema = build_query_candidate_schema()
    hook_contract = build_export_hook_contract(source_context)
    docker_contract = build_docker_command_contract(source_context)
    verification_contract = build_verification_contract()
    next_actions = build_next_actions()

    coverage = {
        "status": "e005_m58_open3dsg_object_candidate_export_plan_ready_hook_smoke_needed",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "staged_root": str(STAGED_ROOT),
        "local_output_dir": str(LOCAL_DATA_DIR),
        "artifact_dir": str(ARTIFACT_DIR),
        "source_modified": False,
        "data_outputs_written_under_research2_local_dataset": True,
        "object_candidate_schema_ready": True,
        "query_candidate_schema_ready": True,
        "export_hook_contract_ready": True,
        "docker_command_contract_ready": True,
        "verification_contract_ready": True,
        "one_batch_smoke_executed": False,
        "candidate_rows_exist": False,
        "query_level_conversion_ready": False,
        "selected_checkpoint_exists": source_context["runtime_assets"]["selected_checkpoint_exists"],
        "feature_dir_exists": source_context["runtime_assets"]["feature_dir_exists"],
        "selected_next_unit": next_actions["selected_next_unit"],
    }

    smoke_manifest = {
        "status": coverage["status"],
        "source_context": source_context,
        "schemas": {
            "object_candidate": object_schema["schema_id"],
            "query_candidate": query_schema["schema_id"],
        },
        "contracts": {
            "export_hook": hook_contract["contract_id"],
            "docker_command": docker_contract["contract_id"],
            "verification": verification_contract["contract_id"],
        },
        "next_actions": next_actions,
    }

    write_json(LOCAL_DATA_DIR / "source_context.json", source_context)
    write_json(LOCAL_DATA_DIR / "object_candidate_schema.json", object_schema)
    write_json(LOCAL_DATA_DIR / "query_candidate_schema.json", query_schema)
    write_json(LOCAL_DATA_DIR / "export_hook_contract.json", hook_contract)
    write_json(LOCAL_DATA_DIR / "docker_command_contract.json", docker_contract)
    write_json(LOCAL_DATA_DIR / "verification_contract.json", verification_contract)
    write_json(LOCAL_DATA_DIR / "next_actions.json", next_actions)
    write_json(LOCAL_DATA_DIR / "smoke_manifest.json", smoke_manifest)

    pointer = {
        "status": coverage["status"],
        "local_data_dir": str(LOCAL_DATA_DIR),
        "files": [
            "source_context.json",
            "object_candidate_schema.json",
            "query_candidate_schema.json",
            "export_hook_contract.json",
            "docker_command_contract.json",
            "verification_contract.json",
            "next_actions.json",
            "smoke_manifest.json",
        ],
    }
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_json(ARTIFACT_DIR / "artifact_pointer.json", pointer)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, object_schema, hook_contract, docker_contract, next_actions))
    return coverage


def main() -> int:
    print(json.dumps(run(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
