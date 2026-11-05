# LIFELINE - Algorithmic Relief-Command Engine (DAA project, group 41)

Iteration 1: data generator, validator, the workbook of 50 cases, approach note and proposal.

- Reproduce the data: see `generator/README.md` (one command).
- Check the data: `python validator/validate.py cases.xlsx`. The full output, including the rejection of
  every broken copy, is saved in the validation report text file in the project root.
- Reports: the approach note (PDF and Markdown, LaTeX source with four parts in the folder `approach`)
  and the proposal (PDF, LaTeX source).
- Python library used: `openpyxl` (reading and writing Excel files) only.
