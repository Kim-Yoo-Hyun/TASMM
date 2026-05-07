# E003-M18 Proposal Output Validator

## Status

scaffold_empty_output_validated

## 사실

- Prediction rows: 0
- Error rows: 0
- Warning rows: 0
- Empty scaffold allowed: True
- Detector predictions ready: False
- Real RGB-D/open-vocabulary claim ready: False
- Paper-table command ready: False

## 논문 주장

- This validator can support schema and denominator checks for later real detector outputs.
- This validator smoke does not support real perception robustness results.

## 에이전트 추론

- Empty-output validation is useful only for checking the Docker/output contract.
- A non-empty detector output must pass the same validator before proposal recall or search metrics are computed.

## 사용자 판단 필요

- None for validator smoke.
