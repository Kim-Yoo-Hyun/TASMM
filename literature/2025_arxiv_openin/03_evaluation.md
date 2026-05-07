# Evaluation

## Dataset / Benchmark

- `Gibson` scenes for offline multi-type query evaluation.
- `Habitat Simulator` long-sequence navigation tasks for frequently used everyday items.
- Real robot validation.

## Splits

The paper reports five scenes for offline query and four everyday scenes for long-sequence navigation. Exact scene IDs should be extracted before implementation.

## Metrics

- offline query success rate
- `SR`
- `Tasks_SR(i)`
- `SPL`

## Baselines

- offline query: `VLMaps`, `ConceptGraphs`
- long-sequence navigation: `VLFM`, `OpenFMNav` variants with thresholds `0.4`, `0.55`, `0.7`
- ablations: `w/o GPT-4o`, `w/o text`, `w/o RGB`, `Ours-w/o-update`, carrier selection strategies

## Main Results

논문 주장: updating the Carrier-Relationship Scene Graph enables efficient navigation to moved targets.

## Reproducibility Notes

Project page exists. Code/data availability needs check.

## Evaluation Weaknesses

- Need metric separation between object memory error and navigation policy error.
- Carrier relation may not represent arbitrary object displacement.
- Strong source for CAND-001, but CAND-001 should generalize beyond carrier relationships.
