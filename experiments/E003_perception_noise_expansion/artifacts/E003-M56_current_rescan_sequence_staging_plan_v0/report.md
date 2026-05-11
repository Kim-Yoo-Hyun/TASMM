# E003-M56 Current-Rescan Sequence Staging Plan

## Status

current_rescan_sequence_staging_plan_ready

## 사실

- Target scan count: 4.
- Sequence-ready target scan count before launch: 0.
- Scans needing download: 4.
- Scans needing decompression after zip appears: 4.
- Background job status: `not_launched`.
- Launch command: `mkdir -p logs && tmux new -d -s e003_m56_sequence_stage 'cd /home/yoohyun/research2 && bash /home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M56_current_rescan_sequence_staging_plan_v0/run_sequence_staging.sh > /home/yoohyun/research2/logs/20260510_170443_e003_m56_sequence_staging.log 2>&1'`.
- Verification command: `python experiments/E003_perception_noise_expansion/tools/verify_m56_sequence_payloads.py --manifest '/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M56_current_rescan_sequence_staging_plan_v0/download_manifest.jsonl' --out-dir '/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M56_current_rescan_sequence_staging_plan_v0/verification' --require-ready`.
- Next recommended unit: `E003-M57 launch current-rescan sequence staging background job`.

## Target Scans

- `5555106a-36f1-29c0-8913-df1ba3c3cfd5`: failure labels {'chair': 3}, download required True, sequence ready False.
- `4731976c-f9f7-2a1a-95cc-31c4d1751d0b`: failure labels {'pillow': 2}, download required True, sequence ready False.
- `ddc73795-765b-241a-9c5d-b97744afe077`: failure labels {'pillow': 1}, download required True, sequence ready False.
- `10b17957-3938-2467-88a5-9e9254930dad`: failure labels {'pillow': 1}, download required True, sequence ready False.

## 논문 주장

- E003-M56 does not create a paper result claim.
- It fixes the reproducible staging plan needed before current-rescan detector outputs can be evaluated against E001/E002 rows.
- Real RGB-D/open-vocabulary search robustness remains blocked until the staging job completes and detector inference/evaluation runs.

## 에이전트 추론

- The smallest direct bridge is to stage only the 4 current rescans that already have E001/E002 search failures.
- `wget -c` is preferred over the official script because it is resumable; the official script remains a fallback command.
- The next step should launch this as a background job rather than block the main agent.

## 사용자 판단 필요

- None if E003-M57 launches the background staging job with the recorded command.
