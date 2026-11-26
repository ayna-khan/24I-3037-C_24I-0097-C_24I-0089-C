# Hamza's completed work and final handoff

The original Project Statement has now been checked. The required calendar
from section 7.4 (page 7) is implemented and is the CLI/backend default.
Ayna does not need to invent or configure that calendar.

## Completed against Hamza's assignment

| Assigned work | Implementation and evidence |
|---|---|
| B route planning | src/modules/routes.py: counted heap Dijkstra, BFS reachability/fewest roads, Bellman-Ford baseline, deterministic routes/NO_ROUTE |
| F network planning | src/modules/networkplan.py: Kruskal with union-find, Prim baseline, HQ-component tree/whole-map forest |
| Tests/experiments for B/F | Independent references and randomized tests; seven geometric sizes; identical baseline inputs; predictions, timing/IQR, separate preprocessing counts, memory, fits/95% intervals/R-squared/relative error; results/results.csv and BF plots/tables |
| Seven-day campaign and CLI | src/campaign.py, src/cli.py, calendars/official.json; exact daily targets/closures, storm rounding, penalties/values/alarms, rescue availability, unreachable trips and no-load evacuation |
| Shared system work | Streaming loader, cross-table validation, reusable measurement harness, daily independent output invariants, integration/HTTP tests and 15 detected seeded faults |
| Interface backend | src/backend.py and src/server.py; Python API plus local JSON endpoints, official default calendar, case cache and explicit invalid-input responses |
| Final-report contribution | B/F and official campaign tables, nine plots with captions, test summary, sample program output and failure-mode paragraph ready for Ayna |

Teammates' A/C/D/G implementations, tests and 169 existing result rows are
preserved. Changes to shared documentation fill Hamza's parts or document
integration. The unrelated local proposal.tex/proposal.pdf edits are excluded.

## Official campaign evidence

Five master_release_v1 cases from seed-41 every-seventh tier samples:
1-06 (S), 1-26 (M), 2-40 (L), 4-47 (trap 47), 2-48 (trap 48).
Each runs seven days with optimized algorithms, algorithm baselines and
additional simple policies: 105 daily policy records, all invariants passed.
Exact route/rescue/queue/cable/G baselines agree on identical daily inputs.

- Days 2-5 block only their own wave, with zero-based wrapping over sorted
  stored wave labels (supports 0-based and 1-based master groups).
- Day 2: ceil(1.5 * base road minutes), tools x2, alarm priority 9 at tick 0.
- Day 3: food x2. Day 4: base penalties >=2 doubled.
- Day 5: medicine x3, alarm priority 10 at tick 0.
- Days 6-7: union of all closure waves. Day 7: evacuation without loading.
- Targets follow target_0, target_1, target_2, target_0, target_1, target_2,
  target_0; each day starts at HQ and all daily transformations reset.
- Rescue filtering uses Adan's exact entry points. F/G run in day-7 review
  using Adan's solve_chain/solve_drum signatures.
- The statement prescribes no stock consumption or expiry cutoff, so the
  official run resets daily stock. Custom controls remain available.
- Costs describe the outbound route; no unprescribed return leg is invented.

Difficult scenarios: trap-47 normal-day greedy loading delivers 113 against
DP's 198 (57.071%); trap-48 BFS travel costs 64 against Dijkstra's 12 (5.333x).
The large landslide case has six unreachable days, explicitly skipped.
Daily inputs, decisions, checked constraints and outcomes are in the JSON
traces and compact CSV/readable output. They reconstruct all daily changes.

## Reproduce and hand off

```text
python -m unittest discover -s tests -t .
python -m src.cli --master MASTER campaign --case 41-00 --compare
python experiments/run_campaign.py --master MASTER
python -m src.server --master MASTER --port 8000
python experiments/runBF.py --master MASTER
python experiments/analyzeBF.py
python experiments/faultBF.py
```

The campaign CLI defaults to readable output; --output PATH saves JSON.
`--calendar PATH` is only needed for a custom calendar. Frontend POST /campaign
can send {"case_id":"41-00"}; official rules apply automatically.
README section 13 documents all inputs, endpoints, policies and assumptions.

Files for Ayna:
- results/campaign-comparison.md, campaign-daily.csv, campaign-summary.csv.
- results/campaign/*.json: immutable base input and all three daily runs.
- results/sample-outputs/campaign-official.txt: readable program output.
- results/plots/campaign-*.png and captions-campaign.md: three campaign figures.
- results/comparison-BF.md, fits-BF.*, quality-BF.csv, B/F plots and captions.
- results/test-summary-BF.txt, fault-injection-BF.txt and prediction checks.

B/F round 2 reran 35 configurations with preprocessing reported separately.
All 15 informed exponent predictions met tolerance; all four precommitted
campaign predictions met tolerance. 867 master route comparisons and 289
forest comparisons agree. Original historical results remain in Git history;
no teammate result row was replaced. All 20 master checksums were verified.
Timing is one session/machine, power state unverified; nested prefixes of one
network do not establish universal growth. No real five-minute DNF run is
claimed; deadline/DNF behavior is implemented and tested without a long wait.

## Remaining team work

No assigned Hamza implementation or calendar-configuration item remains.
Adan connects his frontend to the documented backend/API. Ayna incorporates
the supplied evidence into report.pdf and finalizes her ranked failure-mode
list. The group performs the live demo and submission packaging. No report
or frontend file belonging to a teammate was overwritten, and no messages
were sent to teammates by the assistant.
