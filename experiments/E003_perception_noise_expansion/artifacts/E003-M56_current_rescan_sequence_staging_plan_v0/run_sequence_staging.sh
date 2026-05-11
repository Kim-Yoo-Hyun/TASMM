#!/usr/bin/env bash
set -euo pipefail
cd /home/yoohyun/research2
mkdir -p logs

# 5555106a-36f1-29c0-8913-df1ba3c3cfd5
mkdir -p '/home/yoohyun/research2/local_dataset/3RScan/scans/5555106a-36f1-29c0-8913-df1ba3c3cfd5'
wget -c -O '/home/yoohyun/research2/local_dataset/3RScan/scans/5555106a-36f1-29c0-8913-df1ba3c3cfd5/sequence.zip' 'http://campar.in.tum.de/public_datasets/3RScan/Dataset/5555106a-36f1-29c0-8913-df1ba3c3cfd5/sequence.zip'
unzip -n '/home/yoohyun/research2/local_dataset/3RScan/scans/5555106a-36f1-29c0-8913-df1ba3c3cfd5/sequence.zip' -d '/home/yoohyun/research2/local_dataset/3RScan/scans/5555106a-36f1-29c0-8913-df1ba3c3cfd5/sequence'

# 4731976c-f9f7-2a1a-95cc-31c4d1751d0b
mkdir -p '/home/yoohyun/research2/local_dataset/3RScan/scans/4731976c-f9f7-2a1a-95cc-31c4d1751d0b'
wget -c -O '/home/yoohyun/research2/local_dataset/3RScan/scans/4731976c-f9f7-2a1a-95cc-31c4d1751d0b/sequence.zip' 'http://campar.in.tum.de/public_datasets/3RScan/Dataset/4731976c-f9f7-2a1a-95cc-31c4d1751d0b/sequence.zip'
unzip -n '/home/yoohyun/research2/local_dataset/3RScan/scans/4731976c-f9f7-2a1a-95cc-31c4d1751d0b/sequence.zip' -d '/home/yoohyun/research2/local_dataset/3RScan/scans/4731976c-f9f7-2a1a-95cc-31c4d1751d0b/sequence'

# ddc73795-765b-241a-9c5d-b97744afe077
mkdir -p '/home/yoohyun/research2/local_dataset/3RScan/scans/ddc73795-765b-241a-9c5d-b97744afe077'
wget -c -O '/home/yoohyun/research2/local_dataset/3RScan/scans/ddc73795-765b-241a-9c5d-b97744afe077/sequence.zip' 'http://campar.in.tum.de/public_datasets/3RScan/Dataset/ddc73795-765b-241a-9c5d-b97744afe077/sequence.zip'
unzip -n '/home/yoohyun/research2/local_dataset/3RScan/scans/ddc73795-765b-241a-9c5d-b97744afe077/sequence.zip' -d '/home/yoohyun/research2/local_dataset/3RScan/scans/ddc73795-765b-241a-9c5d-b97744afe077/sequence'

# 10b17957-3938-2467-88a5-9e9254930dad
mkdir -p '/home/yoohyun/research2/local_dataset/3RScan/scans/10b17957-3938-2467-88a5-9e9254930dad'
wget -c -O '/home/yoohyun/research2/local_dataset/3RScan/scans/10b17957-3938-2467-88a5-9e9254930dad/sequence.zip' 'http://campar.in.tum.de/public_datasets/3RScan/Dataset/10b17957-3938-2467-88a5-9e9254930dad/sequence.zip'
unzip -n '/home/yoohyun/research2/local_dataset/3RScan/scans/10b17957-3938-2467-88a5-9e9254930dad/sequence.zip' -d '/home/yoohyun/research2/local_dataset/3RScan/scans/10b17957-3938-2467-88a5-9e9254930dad/sequence'

python experiments/E003_perception_noise_expansion/tools/verify_m56_sequence_payloads.py --manifest '/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M56_current_rescan_sequence_staging_plan_v0/download_manifest.jsonl' --out-dir '/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M56_current_rescan_sequence_staging_plan_v0/verification' --require-ready
