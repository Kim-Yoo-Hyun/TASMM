# VLFM: Vision-Language Frontier Maps for Zero-Shot Semantic Navigation

## Bibliographic Info

- Year/Venue: 2024 ICRA
- Source: https://openreview.net/forum?id=InGGNyZD4k

## One-Line Contribution

Uses a vision-language value map over exploration frontiers so a robot can search for unseen object categories in zero-shot ObjectNav.

## Existing Limitation

ObjectNav agents often require fixed categories or training-time object labels and do not exploit broad VLM semantic priors during exploration.

## Why This Is Semantic Mapping

The key artifact is a map that joins occupancy, frontier structure, and language-grounded semantic value; the map decides where to explore next.

## Method / Map Representation

Depth builds occupancy and frontiers; RGB observations and a VLM produce a language-grounded value map used to rank frontiers.

## Dataset / Benchmark / Metrics

Gibson, HM3D, MP3D in Habitat; real-world Spot deployment; ObjectNav SPL and success.

## Author Organization Pattern

Problem motivation from human semantic search, modular method, simulator benchmark, then real robot deployment.

## Useful Insight

The paper is strong because the map is tied directly to an embodied metric, not only localization quality.

## Failure Lesson

If VLM frontier values fail, the bottleneck may be semantic prior calibration or exploration policy, not 3D reconstruction.
