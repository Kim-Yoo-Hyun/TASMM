# Evaluation

## Dataset / Benchmark

The paper reports experiments on robot-relevant indoor office/building scenes and task-driven queries. Exact reuse feasibility needs PDF-level extraction.

## Splits

Not extracted yet.

## Metrics

- task execution accuracy
- map compactness
- online runtime / onboard compute
- scene graph relevance to task objects and regions

## Baselines

- fixed-threshold open-set mapping variants
- non-task-driven clustering / segmentation variants

## Main Results

논문 주장: task-driven clustering constructs compact open-set 3D scene graphs online and improves task execution by retaining relevant semantic concepts.

## Reproducibility Notes

- Official code exists: https://github.com/MIT-SPARK/Clio
- Need to check dataset availability and exact run commands.

## Evaluation Weaknesses

- Not a benchmark for dynamic moved objects.
- Need to inspect whether failure modes distinguish mapping failure from task planner failure.
