# E008-M198 Summary

Updated: 2026-06-14

## 사실

- Active experiment: `E008_real_navigation_benchmark`.
- Current completed gate: `E008-M198 source-pool scale proxy result interpretation`.
- Next gate: `E008-M199 source-pool scale failure decomposition and candidate-generation repair decision`.
- Source-pool scale denominator: 30 triggered `HM3D ObjectNav val_mini` episodes.
- M194 render/detector output: 960 / 960 render frames ready, 552 detector prediction rows, 552 coordinate candidate rows, 8,867 pre-cap candidate rows.
- M195 validation: 523 / 552 candidate rows path-ready, 23 / 30 source-ready scans, 7 source-gap no-detector scans.
- M196 materialization: 2,121 visit-order rows, full 30-row denominator retained.
- M197 source-pool protected detector-confidence proxy: recovery 17 / 30, proxy `SR` 0.5667, proxy `SPL` 0.3235.
- M70 no-source detector baseline: recovery 24 / 30, proxy `SR` 0.8000, proxy `SPL` 0.3506.

## 논문 주장

- M198 is a negative scale boundary.
- The current source-pool route does not support immediate Docker trajectory execution or final real navigation `SR` / `SPL` improvement.
- Source-pool acquisition remains useful as a diagnostic candidate-generation interface, but it needs failure decomposition and repair before being claimed as a positive method component.

## 에이전트 추론

- The next useful step is not a larger trajectory run; it is M199 failure decomposition.
- The main reviewer defense should emphasize protected baseline comparison: source-pool expansion must not reduce detector-confidence recovery on the full denominator.

