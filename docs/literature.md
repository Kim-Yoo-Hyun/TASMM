# Literature Workflow

Updated: 2026-05-05

This document is the operating rule for literature work. Read it before adding or editing paper notes.

## Scope

Focus on semantic mapping for human-friendly robot intelligence:

- robots understanding human language, intent, knowledge, and preferences
- open-vocabulary 3D semantic maps, scene graphs, object memories, and spatial language grounding
- embodied tasks such as navigation, mobile manipulation, search, and question answering
- top-tier writing patterns from NeurIPS, CVPR, ICCV, ECCV, CoRL, ICRA, RSS, RA-L, and related venues

## Storage Rule

문헌 조사 결과는 루트의 `literature/` 폴더에 저장한다.

- 전체 문헌 조사 인덱스와 synthesis: `literature/README.md`
- paper registry와 reading queue: `literature/PAPER.md`
- contribution candidate 목록: `literature/Contribution Candidates.md`
- candidate별 상세 문서: `literature/CAND-<number>.md`
- 논문별 상세 정리: `literature/<paper-folder>/`
- 작업 계획과 진행 상태: `TODO.md`
- workflow와 작성 규칙: `docs/literature.md`

`docs/literature.md`는 절차와 기준만 관리한다. 논문 내용, paper registry, trend note, contribution candidate는 `literature/` 아래에 기록한다.

## Paper Folder Convention

논문 하나는 하나의 폴더로 관리한다.

```text
literature/
  <year>_<venue-or-arxiv>_<short-title>/
    README.md
    paper.pdf
    01_metadata.md
    02_paper_card.md
    03_evaluation.md
    04_insights.md
```

예시:

```text
literature/
  2024_cvpr_open3dsg/
    README.md
    paper.pdf
    01_metadata.md
    02_paper_card.md
    03_evaluation.md
    04_insights.md
```

폴더명 규칙:

- 소문자 사용
- 공백 대신 `-` 사용
- 가능한 형식: `<year>_<venue>_<short-title>`
- venue가 불명확하면 `arxiv` 또는 `preprint` 사용
- 같은 논문을 중복 생성하지 않는다. 먼저 `literature/PAPER.md`의 Paper Registry를 확인한다.
- 각 paper folder의 첫 진입점은 `README.md`로 둔다.
- 가능한 경우 논문 PDF를 `paper.pdf`라는 이름으로 저장한다.
- arXiv 등에서 버전이 중요한 경우 `01_metadata.md`에 확인한 버전과 다운로드 날짜를 적는다.

## File Roles

### `README.md`

폴더별 인덱스와 짧은 결론을 저장한다. 길게 쓰지 않는다.

```md
# <Paper Title>

- Status:
- Source:
- Why this folder exists:
- Key takeaway:
- Files:
```

### `01_metadata.md`

논문의 식별 정보와 출처를 저장한다.

```md
# <Paper Title>

- Date checked:
- Year:
- Venue / status:
- Authors:
- Link:
- PDF:
- Local PDF: `paper.pdf`
- PDF version:
- PDF downloaded:
- Code:
- Project page:
- Dataset:
- Tags:
- Reading status: Queued / Skimmed / Read / Revisit
```

### `02_paper_card.md`

논문의 핵심 문제와 방법을 정리한다.

```md
# Paper Card

## Problem

## Core Idea

## Input / Output

## Method

## Main Claims

## Strengths

## Limitations

## Relevance to My Research

## Follow-up Questions
```

### `03_evaluation.md`

실험과 평가 가능성을 따로 본다. 석사 연구로 이어질 수 있는지 판단하는 핵심 파일이다.

```md
# Evaluation

## Dataset / Benchmark

## Splits

## Metrics

## Baselines

## Main Results

## Reproducibility Notes

## Evaluation Weaknesses
```

### `04_insights.md`

에이전트의 해석, trend 연결, 기여 가능성을 기록한다. 논문 사실과 추론을 분리한다.

```md
# Insights

## Facts

## Paper Claims

## Inferences

## Connection to Field Trends

## Possible Contribution Angles

## What Would Change This Assessment
```

## Global Literature Index

`literature/README.md`는 전체 문헌 조사 결과의 인덱스와 cross-paper synthesis를 관리한다.

포함해야 할 섹션:

- Field Map
- Trend Synthesis
- Cross-Paper Insights
- Open Questions

개별 논문 내용은 각 paper folder에 두고, `literature/README.md`에는 cross-paper synthesis만 남긴다.

## Literature Control Files

### `literature/PAPER.md`

paper registry와 reading queue를 관리한다.

- `Paper Registry`: 논문 목록, venue, folder, status, why it matters
- `Reading Queue`: 다음에 읽을 논문/주제, priority, status

### `literature/Contribution Candidates.md`

contribution candidate 목록을 관리한다.

- 후보를 간단히 비교할 수 있는 수준으로 유지한다.
- 특정 후보가 길어지면 별도 `literature/CAND-<number>.md`로 분리한다.
- 후보 목록에는 detail file 링크를 둔다.

### `literature/CAND-<number>.md`

특정 contribution candidate의 세부 문제 설정, feasibility, dataset/metric/baseline 판단을 관리한다.

## Literature Workflow

문헌 조사 작업은 네 단계로 수행한다.

1. Field Survey
   - 최근 2-3년 연구 흐름을 조사한다.
   - 결과는 `literature/README.md`의 Field Map / Trend Synthesis와 `literature/PAPER.md`의 Reading Queue에 반영한다.

2. Paper Intake
   - 읽을 가치가 있는 논문마다 paper folder를 만든다.
   - `01_metadata.md`부터 작성한다.
   - `literature/PAPER.md`의 Paper Registry를 갱신한다.

3. Paper Analysis
   - `02_paper_card.md`, `03_evaluation.md`, `04_insights.md`를 작성한다.
   - 방법보다 evaluation을 반드시 따로 본다.

4. Contribution Scan
   - 여러 논문을 비교해 기여 가능성을 찾는다.
   - 결과는 `literature/Contribution Candidates.md`에 기록한다.
   - 후보가 구체화되면 `literature/CAND-<number>.md`로 분리한다.

## Evidence Rules

- 우선순위 소스: 논문 PDF, arXiv, CVF Open Access, OpenReview, 공식 프로젝트 페이지, 공식 코드 저장소.
- 블로그/뉴스/요약글은 보조 자료로만 사용한다.
- 논문을 인용할 때는 제목, 연도, venue 또는 preprint 상태, 링크를 기록한다.
- "최근", "최신", "SOTA", "트렌드"라고 말하려면 검색 날짜 또는 확인 날짜를 함께 남긴다.
- 근거가 약한 판단은 `Inference`로 표시한다.
- 출처를 확인하지 못한 항목은 확정된 사실처럼 쓰지 않는다.

## Quality Gate

문헌 조사 결과가 아래 기준을 만족하지 않으면 contribution candidate를 확정하지 않는다.

- 최소 6개 이상의 primary source를 확인했다.
- 각 주요 trend는 2개 이상의 근거 논문을 가진다.
- dataset, benchmark, metric이 확인되어 있다.
- "이 분야에서 중요해 보인다"가 아니라 "왜 아직 풀리지 않았는지"가 설명되어 있다.
- 해당 주제가 꼭 필요한 문제인지 설명할 수 있다.
- 석사 연구 범위에서 구현/검증 가능한지 판단할 수 있다.
