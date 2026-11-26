# Hamza's work and handoff

Built on Ayna's A/D and Adan's C/G implementations; those modules, tests and
169 existing result rows are unchanged. The implementation, tests, evidence and handoff are included in this delivery.

## Required by the assignment image, now implemented

- B route planning: counted binary-heap Dijkstra, BFS reachability/fewest roads,
  Bellman-Ford exact baseline, closures, deterministic paths and NO_ROUTE.
- F network planning: Kruskal/union-find primary, heap Prim baseline, minimum
  spanning forests and optional HQ-reachable subset.
- Loader and validation: streamed master CSVs, typed teammate records,
  schema/value/identity/reference checks, optional all-file SHA-256 verification.
- Seven-day coordinator and CLI: calendar file, cumulative closures/reopening,
  daily values/expiry/availability, optional consumed stock, A/B/C/D calls,
  F/G review, independent simple-policy comparison and JSON export.
- Frontend backend: Python service functions and a local JSON HTTP adapter,
  including the exact C/G entry points Adan supplied.
- Experiments: seven sizes, 35 measured configurations, one warmup and five
  timed repetitions, median/IQR, memory, operation counts, fitted exponents,
  pre-run predictions, quality comparisons and six plots with captions.
- Tests: independent Floyd-Warshall/exhaustive-forest references, randomized
  checks, malformed CSVs, campaign integration and actual HTTP endpoints.
  Ten seeded faults are caught (including a deliberate loop via timeout).
- Documentation: filled Hamza's README placeholders and appended B/F prediction
  entries. Report-ready results/fits/figures and a failure-mode paragraph are
  in results/comparison-BF.md and the related BF files.

## Evidence

62 sampled master cases: 867 Dijkstra/Bellman comparisons and 289
Kruskal/Prim comparisons, all agreeing; closure waves are cumulative.
Growth uses nested connected prefixes of case 10-40 (16..1024 vertices),
not pooled networks. BFS costs up to 20 times the cheapest route. All eight
pre-run predictions met their tolerances. All 20 master-file hashes verified.
Timing is one session on this machine, with power state unverified; fits
include a changing edge density and do not establish universal exponents.
An initial trial overlapped fault injection and was discarded; published
measurements were rerun with no other project benchmark running.

The example campaign on case 41-00 gives these separate metrics:

| Metric | Optimized | Simple baseline |
|---|---:|---:|
| Delivered value | 4585 | 4532 |
| Dispatched route cost | 450 | 450 |
| Rescue total value | 1907 | 1606 |
| Urgent-alarm mean wait | 0.7 | 5.9 |

The example uses daily stock reset and does not invent closure dates. These
numbers demonstrate integration, not compliance with an unavailable calendar.
No combined score or universal improvement guarantee is claimed.

## Run it

```text
python -m unittest discover -s tests -t .
python -m src.cli --master MASTER --output results/sample-outputs/campaign-example.json campaign --case 41-00 --calendar calendars/example.json --compare
python -m src.server --master MASTER --port 8000
python experiments/runBF.py --master MASTER
python experiments/analyzeBF.py
python experiments/faultBF.py
```

README section 13 documents calendar fields and the frontend API. The server
runs locally; a browser frontend can use a same-origin development proxy.
The test summary is results/test-summary-BF.txt. Measurements are in
results/results.csv (only B/F rows added); the six new figures are
results/plots/B-*.png and F-*.png, with captions-BF.md.

## Remaining decisions and teammate handoff

1. Supply/confirm the original project calendar and statement. The repository
   and Adan's PDF contain only partial events; calendars/example.json is
   explicitly labelled as an example. Replace it with the exact dates,
   targets, closures, expiry and stock semantics, then rerun the coordinator.
   The implementation supports those changes without editing teammates' code.
2. Adan connects the frontend to Backend or the local JSON endpoints; see
   README section 13. No frontend files were changed.
3. Ayna uses the B/F tables, plots, captions and test summary for report.pdf
   and decides the final ranked failure-mode list. Hamza's contribution is
   prepared locally; no messages were sent to teammates.
4. Pull the latest main branch to receive this delivery. Predictions were
   committed before the experiment (ef1cce6); implementation and results are
   in the following delivery commit. Unrelated local proposal.tex/proposal.pdf
   changes were excluded.
