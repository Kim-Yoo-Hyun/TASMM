# Docs Index

Updated: 2026-06-14

이 파일은 `docs/` 아래 workflow 문서들의 짧은 입구다. `docs/index.md`는 세부 연구 내용을 반복하지 않고, 새 작업자가 어떤 문서를 어떤 순서로 읽어야 하는지 알려주는 navigation hub로 쓴다.

## Read Order

1. `AGENTS.md`
2. `README.md`
3. `TODO.md`
4. `docs/index.md`
5. 작업에 해당하는 workflow 문서
6. 작업 대상 폴더의 가장 가까운 `README.md`
7. 필요한 경우 해당 `report.md`, artifact note, 또는 재현성 기록

`TODO.md`의 Now/Next는 실제 작업 우선순위를 정한다. `docs/` 문서는 절차와 판단 기준을 관리하고, 세부 결과는 workflow가 지정한 산출물 폴더에 기록한다.

## Workflows

- [literature.md](literature.md): 문헌조사 workflow와 작성 규칙
- [hypothesis.md](hypothesis.md): contribution candidate를 검증 가능한 hypothesis로 바꾸는 workflow
- [experiments.md](experiments.md): main experiment workflow와 작성 규칙
- [paper.md](paper.md): paper framing, novelty discipline, claim-evidence ledger, reviewer defense 기준
- [reproducibility.md](reproducibility.md): 데이터 위치, 다운로드, checkpoint, Docker, 재현 명령, artifact/evaluation, backup/restore 기준

## Folder Entry Points

- Root `README.md`: repo 전체의 현재 상태와 핵심 파일 안내
- `literature/README.md`: 문헌 조사 결과의 cross-paper synthesis
- `literature/CAND-001_top-tier-refresh-2026.md`: E008-M137 confidence-preserving trajectory repair에 직접 연결한 targeted literature refresh
- `hypothesis/README.md`: hypothesis index와 active gate
- `experiments/README.md`: main experiment index와 experiment 간 연결
- Future `paper/README.md`: paper workspace가 생성된 뒤 파일 역할, 읽는 순서, 업데이트 규칙을 관리한다. 현재 `paper/`는 thesis, main result table, method figure, target venue, claim-evidence ledger가 concrete해진 뒤에만 만든다.

## Rules

- `AGENTS.md`에는 repo-level 규칙, 작업 기대치, 파일 책임, novelty 기준, Docker/reproducibility 원칙만 둔다.
- 논문 관련 판단은 [paper.md](paper.md)의 top-tier novelty rule과 reviewer-defense 기준을 우선한다.
- 실험 재현, artifact, checkpoint, Docker 관련 판단은 [reproducibility.md](reproducibility.md)를 우선한다.
- hypothesis-stage smoke test와 paper-body experiment artifact를 명확히 구분한다.
- 세부 결과나 긴 실험 기록은 루트 README나 `AGENTS.md`에 중복하지 않고 가장 가까운 local README, `report.md`, artifact note에 기록한다.
