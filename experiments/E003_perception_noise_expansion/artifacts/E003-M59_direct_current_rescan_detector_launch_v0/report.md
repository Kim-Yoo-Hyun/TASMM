# E003-M59 Direct Current-Rescan Detector Launch

## Status

direct_current_rescan_detector_job_launched

## 사실

- tmux session: `e003_m59_direct_bridge`.
- job status: `running`.
- launched: True.
- log path: `/home/yoohyun/research2/logs/20260511_114356_e003_m59_direct_current_rescan_detector_run.log`.
- run script: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M59_direct_current_rescan_detector_launch_v0/run_m59_detector.sh`.
- output path: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M59_direct_current_rescan_detector_run_v0`.
- working directory: `/home/yoohyun/research2`.
- target scans: 4 / [`10b17957-3938-2467-88a5-9e9254930dad`, `4731976c-f9f7-2a1a-95cc-31c4d1751d0b`, `5555106a-36f1-29c0-8913-df1ba3c3cfd5`, `ddc73795-765b-241a-9c5d-b97744afe077`].
- bridge query rows: 7.
- verification command: `python experiments/E003_perception_noise_expansion/tools/validate_real_proposal_output.py --predictions /home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M59_direct_current_rescan_detector_run_v0/container_output/real_proposals.jsonl --manifest /home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M58_direct_current_rescan_bridge_design_v0/real_proposal_query_manifest.jsonl --targets /home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M58_direct_current_rescan_bridge_design_v0/real_proposal_object_targets.jsonl --schema /home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M58_direct_current_rescan_bridge_design_v0/proposal_output_schema.json --out-dir /home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M59_direct_current_rescan_detector_run_v0/validator --schema-only-smoke`.
- expected files: ['/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M59_direct_current_rescan_detector_run_v0/coverage.json', '/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M59_direct_current_rescan_detector_run_v0/container_output/real_proposals.jsonl', '/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M59_direct_current_rescan_detector_run_v0/matching/coverage.json', '/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M59_direct_current_rescan_detector_run_v0/validator/coverage.json'].
- password value recorded: False.

## 논문 주장

- E003-M59 launch does not create a paper result claim.
- It only starts the Docker detector run required before query-level direct current-rescan bridge evaluation.

## 에이전트 추론

- Do not monitor the detector job continuously.
- Verify completion with the recorded verification command and expected files before E003-M60.
- If the job fails, inspect only the log tail or targeted error lines.

## 사용자 판단 필요

- None while the background job is running.
