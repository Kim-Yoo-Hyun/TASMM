# GOAT-Bench: A Benchmark for Multi-Modal Lifelong Navigation

## Bibliographic Info

- Year/Venue: 2024 CVPR
- Source: https://arxiv.org/abs/2404.06609

## One-Line Contribution

Benchmarks navigation to a sequence of open-vocabulary goals specified by category, image, or language.

## Existing Limitation

Most navigation benchmarks isolate one goal modality and reset the agent, avoiding lifelong memory and multimodal target specification.

## Why This Is Semantic Mapping

A lifelong agent must reuse spatial-semantic memory across goals and modalities within the same environment.

## Method / Map Representation

Benchmark, not a mapping method; compares monolithic and modular methods with explicit or implicit memory.

## Dataset / Benchmark / Metrics

GOAT task; open-vocabulary sequential targets; success, SPL, robustness to noisy goals, memory dependency.

## Author Organization Pattern

Defines universal navigation, builds benchmark, compares method families, analyzes memory and robustness.

## Useful Insight

A good semantic mapping paper can use multi-goal episodes to show why memory matters.

## Failure Lesson

If explicit memory does not help, the stored semantics may not match the goal modality or query distribution.
