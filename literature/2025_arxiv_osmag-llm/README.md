# osmAG-LLM: Zero-Shot Open-Vocabulary Object Navigation via Semantic Maps and Large Language Models Reasoning

## Bibliographic Info

- Year/Venue: 2025 arXiv
- Source: https://arxiv.org/abs/2507.12753

## One-Line Contribution

Combines semantic maps with LLM priors to handle static, moved, or unmapped object queries in zero-shot ObjectNav.

## Existing Limitation

High-detail object maps quickly become outdated when objects move, and unmapped objects require active reasoning rather than retrieval.

## Why This Is Semantic Mapping

The map is used as environment grounding and context rather than a complete truth source.

## Method / Map Representation

Semantic map plus LLM object-location priors and active online navigation/search.

## Dataset / Benchmark / Metrics

Simulated and real-world object navigation; retrieval success and path length for static, dynamic, and unmapped queries.

## Author Organization Pattern

Challenges the high-fidelity-map assumption, reframes map purpose, then compares dynamic/unmapped cases.

## Useful Insight

A map can be deliberately incomplete if paired with uncertainty-aware search and commonsense reasoning.

## Failure Lesson

If LLM priors dominate incorrectly, the agent needs map-calibrated confidence and clarification.
