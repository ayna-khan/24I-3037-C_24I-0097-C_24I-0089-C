# LIFELINE generator (group 41)

Reproduce the workbook with one command, run from the project root:

    python generator/generate.py --seed 41 --out cases.xlsx

Needs Python 3.9 or later and the `openpyxl` library only. The same seed always gives the same data:
every module of every case has its own random generator seeded from the group seed, the case number
and the module name. No global random state, no clock and no external data are used.

Files in this folder: `common.py` (ranges, tiers, random generators), `crates.py` (crates and traps 46
and 47), `radio.py` (radio log, patterns, reports and trap 49), `graph.py` (locations, roads, waves,
targets and trap 48), and one file each for the windows and alarms, the tour and sensors, the pipeline
and drum, the safety rules and rations, and the tier S claims. `generate.py` builds the 50 cases and
writes the 20 sheets.

The validator is in the folder `validator`: `validate.py` runs all checks (V1 to V8 and the variety
rules) and uses three helper files (text and crate checks, route checks, exact methods).

    python validator/validate.py cases.xlsx

It prints PASS or the broken rules for every case. The folder `validator/tests` holds the valid test
cases and their broken copies; the test runner script in the validator folder checks all of them and
prints the text that is saved as the validation report.
