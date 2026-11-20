"""Fits, comparison tables and plots for module C, all from results/.

    python experiments/analyzeC.py            (after runC.py)

Writes results/fits-C.csv, results/fits-C.md, results/comparison-C.md and the plots
results/plots/C-*.png. Every plot has labelled axes with units, a legend and a caption
(printed under the plot and repeated in results/plots/captions-C.md; the captions of
modules A and D in captions.md are not touched).
"""
import csv
import math
import os
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src import measure  # noqa: E402

NAME = {"greedy": "C: earliest-finish greedy (ours)", "dp": "C: DP with binary search (ours)",
        "dpquad": "C: plain O(n^2) DP (ours)", "brute": "C: brute force, all subsets (ours)"}
STYLE = {"greedy": ("tab:orange", "s"), "dp": ("tab:blue", "o"), "dpquad": ("tab:green", "D"), "brute": ("tab:red", "^")}

THEORY = {("C-scale-n", "greedy"): "n log n: slope slightly above 1", ("C-scale-n", "dp"): "n log n: slope slightly above 1",
          ("C-scale-n", "dpquad"): "n^2: slope 2 once the quadratic term dominates",
          ("C-small-n", "brute"): "2^n: base 2 per window"}


def load(folder):
    with open(os.path.join(folder, "results.csv"), newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r["module"] == "C"]


def series(rows, exp, alg, field="time_s"):
    pts = [(float(r["size"]), float(r[field]), float(r["time_iqr_s"] or 0)) for r in rows
           if (r["experiment"], r["algorithm"]) == (exp, alg) and r["status"] == "OK" and r[field] != ""]
    return sorted(pts)


def note_value(row, key):
    for part in row["note"].split(";"):
        part = part.strip()
        if part.startswith(key + "="):
            return float(part.split("=", 1)[1])
    raise KeyError(key)


def fits(rows):
    out = []
    for (exp, alg), theory in THEORY.items():
        for field, label in (("time_s", "time"), ("ops", "operations")):
            pts = [p for p in series(rows, exp, alg, field) if p[1] > 0]
            if len(pts) < 5:
                continue
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            if exp == "C-small-n":
                f = measure.fit_semilog(xs, ys)
                out.append(dict(experiment=exp, algorithm=alg, quantity=label, model="semi-log", sizes=len(xs),
                                estimate=f"{f['base']:.3f}", ci95=f"{f['base_ci95'][0]:.3f} to {f['base_ci95'][1]:.3f}",
                                r2=f"{f['r2']:.4f}", theory=theory))
            else:
                f = measure.fit_loglog(xs, ys)
                out.append(dict(experiment=exp, algorithm=alg, quantity=label, model="log-log", sizes=len(xs),
                                estimate=f"{f['slope']:.3f}", ci95=f"+-{f['ci95']:.3f}", r2=f"{f['r2']:.4f}", theory=theory))
    for alg in ("greedy", "dp", "dpquad"):          # time against the counted operations: slope 1 = the count explains the time
        pts = sorted((float(r["ops"]), float(r["time_s"])) for r in rows
                     if (r["experiment"], r["algorithm"]) == ("C-scale-n", alg) and r["status"] == "OK" and r["ops"] != "")
        pts = [p for p in pts if p[0] > 0 and p[1] > 0]
        if len(pts) >= 5:
            f = measure.fit_loglog([p[0] for p in pts], [p[1] for p in pts])
            out.append(dict(experiment="C-scale-n", algorithm=alg, quantity="time against ops", model="log-log", sizes=len(pts),
                            estimate=f"{f['slope']:.3f}", ci95=f"+-{f['ci95']:.3f}", r2=f"{f['r2']:.4f}",
                            theory="time proportional to the counted operations: slope 1"))
    return out


def extrapolate_dnf(rows, alg="dpquad", target=None):
    """Time at the DNF size from the log-log fit on the C-scale-n points of `alg` (an extrapolation, not a measurement)."""
    dnf = [r for r in rows if r["experiment"] == "C-dnf" and r["algorithm"] == alg]
    pts = series(rows, "C-scale-n", alg)
    if len(pts) < 5 or not dnf:
        return None
    target = target or float(dnf[0]["size"])
    f = measure.fit_loglog([p[0] for p in pts], [p[1] for p in pts])
    return 2 ** (f["intercept"] + f["slope"] * math.log2(target))


def write_fit_files(folder, fit_rows):
    if not fit_rows:
        return
    with open(os.path.join(folder, "fits-C.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(fit_rows[0]))
        w.writeheader()
        w.writerows(fit_rows)
    lines = ["| experiment | algorithm | quantity | model | sizes | slope or base | 95 % interval | R^2 | theory |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in fit_rows:
        lines.append("| " + " | ".join(str(r[k]) for k in ("experiment", "algorithm", "quantity", "model", "sizes",
                                                            "estimate", "ci95", "r2", "theory")) + " |")
    with open(os.path.join(folder, "fits-C.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def human(seconds):
    if seconds < 1e-3:
        return f"{seconds * 1e6:.1f} us"
    if seconds < 1:
        return f"{seconds * 1e3:.2f} ms"
    return f"{seconds:.2f} s"


def comparison_tables(folder, rows):
    parts = ["# Comparison tables for module C (generated by experiments/analyzeC.py)\n",
             "Time = median of 5 runs after one warm-up, with the interquartile range (IQR). ops = operations as defined in the README "
             "(comparisons + moves + probes + windows examined + table cells + subsets). mem = peak memory beyond the input. "
             "Objective: count for greedy, value for dp, dpquad and brute.\n"]
    for exp, title, algs, ratio in (("C-scale-n", "C: growth in n", ["greedy", "dp", "dpquad"], ("dpquad", "dp")),
                                    ("C-small-n", "C: small inputs", ["greedy", "dp", "dpquad", "brute"], ("brute", "dp"))):
        sizes = sorted({float(r["size"]) for r in rows if r["experiment"] == exp})
        if not sizes:
            continue
        parts.append(f"\n## {title}\n")
        head = "| n | " + " | ".join(f"{a} time (IQR) | {a} ops | {a} mem" for a in algs) + f" | {ratio[0]} / {ratio[1]} time |"
        parts += [head, "|" + "---|" * (len(algs) * 3 + 2)]
        for s in sizes:
            cells, times = [], {}
            for a in algs:
                r = next((x for x in rows if x["experiment"] == exp and x["algorithm"] == a and float(x["size"]) == s), None)
                if r is None or r["status"] != "OK":
                    cells += ["DNF" if r else "-", "-", "-"]
                    continue
                times[a] = float(r["time_s"])
                mem = f"{int(float(r['mem_bytes'])):,}" if r["mem_bytes"] != "" else "-"
                cells += [f"{human(float(r['time_s']))} ({human(float(r['time_iqr_s']))})", f"{int(float(r['ops'])):,}", mem]
            q = f"{times[ratio[0]] / times[ratio[1]]:.3g}" if ratio[0] in times and ratio[1] in times else "-"
            parts.append(f"| {int(s):,} | " + " | ".join(cells) + f" | {q} |")
    dnf = [r for r in rows if r["experiment"] == "C-dnf"]
    if dnf:
        parts.append("\n## C: the 5 minute rule\n")
        parts += ["| algorithm | n | status | time | note |", "|---|---|---|---|---|"]
        for r in dnf:
            parts.append(f"| {r['algorithm']} | {int(float(r['size'])):,} | {r['status']} | "
                         f"{human(float(r['time_s'])) if r['time_s'] else '> 300 s'} | {r['note']} |")
        est = extrapolate_dnf(rows)
        if est:
            parts.append(f"\nExtrapolated time of dpquad at that size from the log-log fit on n up to 3000: {human(est)} "
                         "(an extrapolation of a fit, not a measurement: the run was stopped at 300 s).")
    with open(os.path.join(folder, "comparison-C.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(parts) + "\n")


def quality_tables(folder):
    qc = os.path.join(folder, "quality-C.csv")
    if not os.path.exists(qc):
        return
    with open(qc, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    lines = ["\n## C: what the earliest-finish rule gives up (sample of the master data)\n",
             "| tier | cases | greedy count = optimum | greedy value optimal | mean greedy/DP value | worst greedy/DP value | "
             "mean windows of the value-optimal plan / greedy count | count equals claim | DP value equals claim |",
             "|---|---|---|---|---|---|---|---|---|"]
    for tier in ("S", "M", "L", "X"):
        sub = [r for r in rows if r["tier"] == tier]
        if not sub:
            continue
        ratios = [float(r["greedy_over_dp"]) for r in sub]
        use = [int(r["dp_value_plan_windows"]) / int(r["greedy_count"]) for r in sub]
        cc = [int(r["greedy_count_matches_claim"]) for r in sub if r["greedy_count_matches_claim"] != ""]
        vc = [int(r["dp_value_matches_claim"]) for r in sub if r["dp_value_matches_claim"] != ""]
        lines.append(f"| {tier} | {len(sub)} | {sum(int(r['greedy_count_optimal']) for r in sub)}/{len(sub)} | "
                     f"{sum(int(r['greedy_value_optimal']) for r in sub)}/{len(sub)} | {sum(ratios) / len(ratios):.4f} | {min(ratios):.4f} | "
                     f"{sum(use) / len(use):.3f} | {(str(sum(cc)) + '/' + str(len(cc))) if cc else 'n/a'} | "
                     f"{(str(sum(vc)) + '/' + str(len(vc))) if vc else 'n/a'} |")
    with open(os.path.join(folder, "comparison-C.md"), "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ------------------------------------------------------------------ plots
CAPTIONS = []


def finish(fig, ax, path, title, caption, xlabel, ylabel):
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=11)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8)
    fig.text(0.01, 0.005, textwrap.fill(caption, 118), fontsize=7.5, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.11, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)
    CAPTIONS.append(f"**{os.path.basename(path)}**: {caption}")


def line_plot(rows, folder, exp, algs, field, fname, title, xlabel, ylabel, caption, logx=True, extra=None):
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    drew = False
    for a in algs:
        pts = series(rows, exp, a, field)
        if not pts:
            continue
        c, mk = STYLE[a]
        ax.errorbar([p[0] for p in pts], [p[1] for p in pts], yerr=[p[2] / 2 for p in pts] if field == "time_s" else None,
                    color=c, marker=mk, capsize=2, label=NAME[a])
        drew = True
    if not drew:
        plt.close(fig)
        return
    if extra:
        extra(ax)
    if logx:
        ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    finish(fig, ax, os.path.join(folder, "plots", fname), title, caption, xlabel, ylabel)


def make_plots(folder, rows):
    os.makedirs(os.path.join(folder, "plots"), exist_ok=True)
    dnf_rows = [r for r in rows if r["experiment"] == "C-dnf"]

    def dnf_marker(ax):
        for r in dnf_rows:
            if r["status"] == "DNF":
                ax.axvline(float(r["size"]), color="gray", linestyle=":", linewidth=1)
                ax.annotate(f"{r['algorithm']}: DNF (> 300 s)", (float(r["size"]), 300), fontsize=7, rotation=90, va="top", ha="right")
            elif r["time_s"]:
                c, mk = STYLE[r["algorithm"]]
                ax.plot([float(r["size"])], [float(r["time_s"])], marker=mk, color=c, markerfacecolor="none", linestyle="none",
                        label=f"{r['algorithm']} at the DNF size (single point)")
        ax.axhline(300, color="gray", linestyle="--", linewidth=0.8, label="300 s limit")

    line_plot(rows, folder, "C-scale-n", ["greedy", "dp", "dpquad"], "time_s", "C-time-vs-n.png",
              "Module C: running time against the number of windows", "number of windows n",
              "running time (seconds, median of 5)",
              "Figure C1. Median time on pooled tier L windows; bars are the interquartile range. Both axes are logarithmic: the greedy rule and the DP with "
              "binary search follow lines of slope a little above 1 (n log n), the plain DP of slope close to 2 (n^2). The hollow marker and the dotted line "
              "at the right belong to the 5 minute run: the dashed line is the 300 s limit.", extra=dnf_marker)
    line_plot(rows, folder, "C-small-n", ["greedy", "dp", "dpquad", "brute"], "time_s", "C-small-inputs.png",
              "Module C: small inputs, exact methods against the greedy rule", "number of windows n",
              "running time (seconds, median of 5)",
              "Figure C2. Median time on pooled tier S windows. The vertical axis is logarithmic and the horizontal one linear, so brute force "
              "(2^n subsets) is a straight line while the DP and the greedy rule stay almost flat.", logx=False)
    line_plot(rows, folder, "C-scale-n", ["greedy", "dp", "dpquad"], "ops", "C-operations.png",
              "Operations counted against input size", "number of windows n", "operations counted (number)",
              "Figure C3. Operations as defined in the README: comparisons + moves of our merge sort, binary-search probes, windows examined and table cells. "
              "The two n log n methods differ by a constant factor of about 1.5; the plain DP examines n (n - 1) / 2 pairs.")

    qc = os.path.join(folder, "quality-C.csv")
    if os.path.exists(qc):
        with open(qc, newline="", encoding="utf-8") as f:
            q = list(csv.DictReader(f))
        fig, ax = plt.subplots(figsize=(6.4, 4.8))
        tiers = [t for t in ("S", "M", "L", "X") if any(r["tier"] == t for r in q)]
        for i, t in enumerate(tiers):
            vals = [float(r["greedy_over_dp"]) for r in q if r["tier"] == t]
            ax.scatter([i + 0.04 * (k % 7 - 3) for k in range(len(vals))], vals, alpha=0.6, color="tab:orange", label=None)
            ax.hlines(sum(vals) / len(vals), i - 0.3, i + 0.3, color="black", label="mean" if i == 0 else None)
        ax.set_xticks(range(len(tiers)))
        ax.set_xticklabels([f"tier {t}" for t in tiers])
        ax.scatter([], [], color="tab:orange", label="one case (greedy value / DP value)")
        ax.set_ylim(0, 1.05)
        finish(fig, ax, os.path.join(folder, "plots", "C-greedy-quality.png"),
               "Module C: value of the greedy plan relative to the optimum",
               "Figure C4. For every sampled case, the total value of the earliest-finish plan divided by the optimal total value found by the DP "
               "(1.0 = the greedy plan is optimal). Black bars are the means per tier. The greedy rule is optimal for the number of windows in every case, "
               "but it never looks at values.", "tier of the sampled master-data cases", "greedy value / optimal value (ratio)")
    if CAPTIONS:
        with open(os.path.join(folder, "plots", "captions-C.md"), "w", encoding="utf-8") as f:
            f.write("# Captions of the plots of module C\n\n" + "\n\n".join(CAPTIONS) + "\n")


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results")
    rows = load(folder)
    fit_rows = fits(rows)
    write_fit_files(folder, fit_rows)
    comparison_tables(folder, rows)
    quality_tables(folder)
    make_plots(folder, rows)
    path = os.path.join(folder, "fits-C.md")
    if os.path.exists(path):
        print(open(path, encoding="utf-8").read())


if __name__ == "__main__":
    main()
