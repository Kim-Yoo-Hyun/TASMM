# OpenEQA: Embodied Question Answering in the Era of Foundation Models

## Bibliographic Info

- Year/Venue: 2024 CVPR
- Source: https://openaccess.thecvf.com/content/CVPR2024/html/Majumdar_OpenEQA_Embodied_Question_Answering_in_the_Era_of_Foundation_Models_CVPR_2024_paper.html

## One-Line Contribution

Defines open-vocabulary embodied question answering for agents that must understand environments well enough to answer natural-language questions.

## Existing Limitation

Embodied evaluation often stops at navigation or detection, while human-facing agents need to answer questions about spaces and past observations.

## Why This Is Semantic Mapping

Answering "where did I leave X?" or "what is near Y?" requires a persistent semantic memory of objects, relations, and episodes.

## Method / Map Representation

Benchmark formulation for episodic memory and active exploration; not a map method itself, but a target evaluation for semantic memory.

## Dataset / Benchmark / Metrics

Open-vocabulary EQA benchmark with natural-language answer evaluation.

## Author Organization Pattern

Reframes the task around environment understanding, defines benchmark splits, evaluates foundation-model agents.

## Useful Insight

Human-friendly mapping should be evaluated through communicative behavior, not only path success.

## Failure Lesson

If a map supports navigation but fails EQA, it lacks relation, episode, or context memory.
