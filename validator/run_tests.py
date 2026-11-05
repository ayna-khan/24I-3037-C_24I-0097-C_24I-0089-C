"""runs the validator on cases.xlsx and on every file in validator/tests/ and prints the report.

    python validator/run_tests.py cases.xlsx > validation_report.txt
"""
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VALIDATE = os.path.join(HERE, "validate.py")


def run(path, partial):
    cmd = [sys.executable, VALIDATE, path] + (["--partial"] if partial else [])
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    return out


def main():
    cases = sys.argv[1]
    print("=" * 70)
    print("PART 1: the submitted dataset cases.xlsx")
    print("=" * 70)
    print(run(cases, partial=False))

    print("=" * 70)
    print("PART 2: valid test cases must PASS, every broken copy must be REJECTED")
    print("=" * 70)
    wrong = 0
    files = sorted(glob.glob(os.path.join(HERE, "tests", "*.xlsx")))
    for path in files:
        name = os.path.basename(path)
        expect_pass = name.startswith("valid-")
        out = run(path, partial=True)
        passed = "RESULT: PASS" in out
        ok = passed == expect_pass
        wrong += not ok
        print(f"--- {name}: expected {'PASS' if expect_pass else 'REJECT'}, got {'PASS' if passed else 'REJECT'}"
              f"  [{'OK' if ok else 'WRONG'}]")
        for line in out.splitlines():
            if "FAIL" in line or line.startswith("    "):
                print("   ", line.strip())
    broken = sum(1 for p in files if not os.path.basename(p).startswith("valid-"))
    print()
    print(f"SUMMARY: {broken} broken copies, {len(files) - broken} valid copies, "
          f"{wrong} unexpected results -> {'ALL AS EXPECTED' if wrong == 0 else 'PROBLEM'}")
    return 1 if wrong else 0


if __name__ == "__main__":
    sys.exit(main())
