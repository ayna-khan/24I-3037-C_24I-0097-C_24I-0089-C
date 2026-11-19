"""Fits, comparison tables and plots for modules A and D, all from results/.

    python experiments/analyzeAD.py            (after runAD.py)

Writes results/fits-AD.csv, results/fits-AD.md, results/comparison-AD.md and
the plots results/plots/*.png. Every plot has labelled axes with units, a legend
and a caption (printed under the plot and repeated in results/plots/captions.md).
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

NAME = {("A", "dp"): "A: DP over the capacity (ours)", ("A", "greedy"): "A: ratio greedy (ours)",
        ("A", "brute"): "A: brute force, all subsets (ours)", ("D", "heap"): "D: binary heap (ours)",
        ("D", "scan"): "D: linear scan (ours)"}
STYLE = {"dp": ("tab:blue", "o"), "greedy": ("tab:orange", "s"), "brute": ("tab:red", "^"),
         "heap": ("tab:blue", "o"), "scan": ("tab:red", "^")}

THEORY = {("A-scale-n", "dp"): "n*W with W proportional to n: slope 2", ("A-scale-n", "greedy"): "n log n: slope slightly above 1",
          ("A-scale-W", "dp"): "n*W: slope 1 in W", ("A-scale-W", "greedy"): "independent of W: slope 0",
          ("A-small-n", "brute"): "2^n: base 2 per crate", ("A-small-n", "dp"): "n*W (W about 4 n): slope 2",
          ("A-small-n", "greedy"): "n log n", ("D-scale-m", "heap"): "m log m: slope slightly above 1",
          ("D-scale-m", "scan"): "m * backlog, backlog proportional to m: slope 2"}


def load(folder):
    with open(os.path.join(folder, "results.csv"), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def series(rows, module, exp, alg, field="time_s", key="size"):
    pts = [(float(r[key]), float(r[field]), float(r["time_iqr_s"] or 0)) for r in rows
           if (r["module"], r["experiment"], r["algorithm"]) == (module, exp, alg) and r["status"] == "OK" and r[field] != ""]
    return sorted(pts)


def fits(rows):
    out = []
    for (exp, alg), theory in THEORY.items():
        module = exp[0]
        key = "size2" if exp == "A-scale-W" else "size"
        for field, label in (("time_s", "time"), ("ops", "operations")):
            pts = series(rows, module, exp, alg, field, key)
            pts = [p for p in pts if p[1] > 0]
            if len(pts) < 5:
                continue
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            if exp == "A-small-n" and alg == "brute":
                f = measure.fit_semilog(xs, ys)
                out.append(dict(module=module, experiment=exp, algorithm=alg, quantity=label, model="semi-log", sizes=len(xs),
                                estimate=f"{f['base']:.3f}", ci95=f"{f['base_ci95'][0]:.3f} to {f['base_ci95'][1]:.3f}",
                                r2=f"{f['r2']:.4f}", theory=theory))
            else:
                f = measure.fit_loglog(xs, ys)
                out.append(dict(module=module, experiment=exp, algorithm=alg, quantity=label, model="log-log", sizes=len(xs),
                                estimate=f"{f['slope']:.3f}", ci95=f"+-{f['ci95']:.3f}", r2=f"{f['r2']:.4f}", theory=theory))
    # time against the counted operations: slope 1 means "the count explains the time"
    for exp, alg in (("A-scale-n", "dp"), ("A-scale-W", "dp"), ("D-scale-m", "scan"), ("D-scale-m", "heap"), ("A-scale-n", "greedy")):
        module = exp[0]
        pts = [(float(r["ops"]), float(r["time_s"])) for r in rows
               if (r["module"], r["experiment"], r["algorithm"]) == (module, exp, alg) and r["status"] == "OK" and r["ops"] != ""]
        pts = sorted(p for p in pts if p[0] > 0 and p[1] > 0)
        if len(pts) >= 5:
            f = measure.fit_loglog([p[0] for p in pts], [p[1] for p in pts])
            out.append(dict(module=module, experiment=exp, algorithm=alg, quantity="time against ops", model="log-log",
                            sizes=len(pts), estimate=f"{f['slope']:.3f}", ci95=f"+-{f['ci95']:.3f}", r2=f"{f['r2']:.4f}",
                            theory="time proportional to the counted operations: slope 1"))
    return out


def write_fit_files(folder, fit_rows):
    with open(os.path.join(folder, "fits-AD.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(fit_rows[0]))
        w.writeheader()
        w.writerows(fit_rows)
    lines = ["| module | experiment | algorithm | quantity | model | sizes | slope or base | 95 % interval | R^2 | theory |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in fit_rows:
        lines.append("| " + " | ".join(str(r[k]) for k in ("module", "experiment", "algorithm", "quantity", "model", "sizes",
                                                            "estimate", "ci95", "r2", "theory")) + " |")
    with open(os.path.join(folder, "fits-AD.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def human(seconds):
    if seconds < 1e-3:
        return f"{seconds * 1e6:.1f} us"
    if seconds < 1:
        return f"{seconds * 1e3:.2f} ms"
    return f"{seconds:.2f} s"


def comparison_tables(folder, rows):
    parts = ["# Comparison tables for modules A and D (generated by experiments/analyzeAD.py)\n",
             "Time = median of 5 runs after one warm-up, with the interquartile range (IQR). ops = operations as defined in the README. "
             "mem = peak memory beyond the input.\n"]
    for exp, title, alg_a, alg_b, label_size in (("A-scale-n", "A: growth in n", "dp", "greedy", "n"),
                                                 ("A-scale-W", "A: growth in W (n fixed)", "dp", "greedy", "W"),
                                                 ("A-small-n", "A: small inputs", "dp", "brute", "n"),
                                                 ("D-scale-m", "D: growth in m", "heap", "scan", "m")):
        module = exp[0]
        key = "size2" if exp == "A-scale-W" else "size"
        sizes = sorted({float(r[key]) for r in rows if r["experiment"] == exp})
        if not sizes:
            continue
        algs = [alg_a, alg_b] + (["greedy"] if exp == "A-small-n" else [])
        parts.append(f"\n## {title}\n")
        head = f"| {label_size} | " + " | ".join(f"{a} time (IQR) | {a} ops | {a} mem" for a in algs) + f" | {alg_b} / {alg_a} time |"
        parts += [head, "|" + "---|" * (len(algs) * 3 + 2)]
        for s in sizes:
            cells = []
            times = {}
            for a in algs:
                r = next((x for x in rows if x["experiment"] == exp and x["algorithm"] == a and float(x[key]) == s), None)
                if r is None or r["status"] != "OK":
                    cells += ["DNF" if r else "-", "-", "-"]
                    continue
                times[a] = float(r["time_s"])
                mem = f"{int(float(r['mem_bytes'])):,}" if r["mem_bytes"] != "" else "-"
                cells += [f"{human(float(r['time_s']))} ({human(float(r['time_iqr_s']))})", f"{int(float(r['ops'])):,}", mem]
            ratio = f"{times[alg_b] / times[alg_a]:.3g}" if alg_a in times and alg_b in times else "-"
            parts.append(f"| {int(s):,} | " + " | ".join(cells) + f" | {ratio} |")
    dnf = [r for r in rows if r["experiment"] == "D-dnf"]
    if dnf:
        parts.append("\n## D: the 5 minute rule\n")
        parts += ["| algorithm | m | status | time | note |", "|---|---|---|---|---|"]
        for r in dnf:
            parts.append(f"| {r['algorithm']} | {int(float(r['size'])):,} | {r['status']} | "
                         f"{human(float(r['time_s'])) if r['time_s'] else '> 300 s'} | {r['note']} |")
    with open(os.path.join(folder, "comparison-AD.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(parts) + "\n")


def quality_tables(folder):
    lines = []
    qa = os.path.join(folder, "quality-A.csv")
    if os.path.exists(qa):
        with open(qa, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        lines += ["\n## A: how much value the greedy rule loses (sample of the master data)\n",
                  "| tier | cases | greedy optimal | mean greedy/DP | worst greedy/DP | DP equals claim |", "|---|---|---|---|---|---|"]
        for tier in ("S", "M", "L", "X", "X47"):
            sub = [r for r in rows if r["tier"] == tier]
            if not sub:
                continue
            ratios = [float(r["greedy_over_dp"]) for r in sub if r["greedy_over_dp"]]
            claims = [r["dp_matches_claim"] for r in sub if r["dp_matches_claim"] != ""]
            lines.append(f"| {tier} | {len(sub)} | {sum(int(r['greedy_optimal']) for r in sub)}/{len(sub)} | "
                         f"{sum(ratios) / len(ratios):.4f} | {min(ratios):.4f} | "
                         f"{(str(sum(map(int, claims))) + '/' + str(len(claims))) if claims else 'n/a'} |")
    qd = os.path.join(folder, "quality-D.csv")
    if os.path.exists(qd):
        with open(qd, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        lines += ["\n## D: urgency order against first-come-first-served (sample of the master data)\n",
                  "| tier | cases | mean wait, all alarms (both orders) | mean wait of priority 9-10, urgency | mean wait of priority 9-10, FIFO | worst wait of priority 9-10, urgency | worst wait of priority 9-10, FIFO |",
                  "|---|---|---|---|---|---|---|"]
        for tier in ("S", "M", "L", "X"):
            sub = [r for r in rows if r["tier"] == tier]
            if not sub:
                continue
            m = lambda k: sum(float(r[k]) for r in sub) / len(sub)  # noqa: E731
            lines.append(f"| {tier} | {len(sub)} | {m('mean_wait_urgency'):.1f} | {m('mean_wait_p9plus_urgency'):.1f} | "
                         f"{m('mean_wait_p9plus_fifo'):.1f} | {max(int(r['max_wait_p9plus_urgency']) for r in sub)} | "
                         f"{max(int(r['max_wait_p9plus_fifo']) for r in sub)} |")
    with open(os.path.join(folder, "comparison-AD.md"), "a", encoding="utf-8") as f:
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


def line_plot(rows, folder, exp, module, algs, key, fname, title, xlabel, caption, logy=True, logx=True, extra=None):
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    for a in algs:
        pts = series(rows, module, exp, a, "time_s", key)
        if not pts:
            continue
        c, mk = STYLE[a]
        ax.errorbar([p[0] for p in pts], [p[1] for p in pts], yerr=[p[2] / 2 for p in pts], color=c, marker=mk,
                    capsize=2, label=NAME[(module, a)])
    if extra:
        extra(ax)
    if logx:
        ax.set_xscale("log", base=2)
    if logy:
        ax.set_yscale("log")
    finish(fig, ax, os.path.join(folder, "plots", fname), title, caption, xlabel, "running time (seconds, median of 5)")


def make_plots(folder, rows):
    os.makedirs(os.path.join(folder, "plots"), exist_ok=True)
    line_plot(rows, folder, "A-scale-n", "A", ["dp", "greedy"], "size", "A-time-vs-n.png",
              "Module A: running time against the number of crates",
              "number of crates n (capacity W about 3.4 n)",
              "Figure A1. Median time of the DP and of the ratio greedy rule on pooled tier L crates; bars are the interquartile range. "
              "Both axes are logarithmic: the DP follows a line of slope about 2 (n x W work), the greedy rule about 1.")
    line_plot(rows, folder, "A-scale-W", "A", ["dp", "greedy"], "size2", "A-time-vs-W.png",
              "Module A: running time against the truck capacity (n = 1600)",
              "truck capacity W (kg)",
              "Figure A2. Median time for 1600 crates while only the capacity grows. The DP is linear in W (slope near 1); the greedy rule does not depend on W.")
    line_plot(rows, folder, "A-small-n", "A", ["dp", "greedy", "brute"], "size", "A-small-inputs.png",
              "Module A: small inputs, exact methods against the greedy rule",
              "number of crates n",
              "Figure A3. Median time on pooled tier S crates. The vertical axis is logarithmic and the horizontal one linear, so brute force "
              "(2^n subsets) is a straight line and the DP stays almost flat.", logx=False)

    def dnf_marker(ax):
        pts = [r for r in rows if r["experiment"] == "D-dnf" and r["status"] == "DNF"]
        for r in pts:
            ax.axvline(float(r["size"]), color="gray", linestyle=":", linewidth=1)
            ax.annotate("scan: DNF (> 300 s)", (float(r["size"]), 300), fontsize=7, rotation=90, va="top", ha="right")
        ax.axhline(300, color="gray", linestyle="--", linewidth=0.8, label="300 s limit")

    d_rows = [r for r in rows if r["experiment"] == "D-dnf" and r["algorithm"] == "heap" and r["status"] == "OK"]
    merged = rows + [dict(r, experiment="D-scale-m") for r in d_rows]
    line_plot(merged, folder, "D-scale-m", "D", ["heap", "scan"], "size", "D-time-vs-m.png",
              "Module D: running time against the number of alarms",
              "number of alarms m",
              "Figure D1. Median time to release all alarms of pooled tier L streams; bars are the interquartile range. The linear scan is "
              "quadratic (slope about 2) because the backlog grows in proportion to m; the heap is close to m log m. The dashed line is the 300 s limit.",
              extra=dnf_marker)

    # operations plot
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    for module, exp, algs, key in (("A", "A-scale-n", ["dp", "greedy"], "size"), ("D", "D-scale-m", ["heap", "scan"], "size")):
        for a in algs:
            pts = series(rows, module, exp, a, "ops", key)
            if pts:
                c, mk = STYLE[a]
                ax.plot([p[0] for p in pts], [p[1] for p in pts], marker=mk, linestyle="-" if module == "A" else "--",
                        label=NAME[(module, a)])
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    finish(fig, ax, os.path.join(folder, "plots", "AD-operations.png"), "Operations counted against input size",
           "Figure AD1. Operations as defined in the README: table cells (A, DP), comparisons plus moves (A, greedy; D, heap and scan). "
           "Solid lines belong to module A and dashed lines to module D; the horizontal axis is n for A and m for D.",
           "input size (crates n for A, alarms m for D)", "operations counted (number)")

    # quality plots
    qa = os.path.join(folder, "quality-A.csv")
    if os.path.exists(qa):
        with open(qa, newline="", encoding="utf-8") as f:
            q = list(csv.DictReader(f))
        fig, ax = plt.subplots(figsize=(6.4, 4.8))
        tiers = [t for t in ("S", "M", "L", "X", "X47") if any(r["tier"] == t for r in q)]
        for i, t in enumerate(tiers):
            vals = [float(r["greedy_over_dp"]) for r in q if r["tier"] == t and r["greedy_over_dp"]]
            ax.scatter([i] * len(vals), vals, alpha=0.6, label=None)
            ax.hlines(sum(vals) / len(vals), i - 0.3, i + 0.3, color="black", label="mean" if i == 0 else None)
        ax.set_xticks(range(len(tiers)))
        ax.set_xticklabels([f"tier {t}" if t != "X47" else "trap 47" for t in tiers])
        ax.scatter([], [], color="tab:blue", label="one case (greedy value / DP value)")
        finish(fig, ax, os.path.join(folder, "plots", "A-greedy-quality.png"), "Module A: value of the greedy load relative to the optimum",
               "Figure A4. For every sampled case, the value of the ratio-greedy load divided by the optimal value found by the DP (1.0 = greedy is optimal). "
               "Black bars are the means per group of cases.", "group of cases (master data sample)", "greedy value / optimal value (ratio)")
    qd = os.path.join(folder, "quality-D.csv")
    if os.path.exists(qd):
        with open(qd, newline="", encoding="utf-8") as f:
            q = list(csv.DictReader(f))
        fig, ax = plt.subplots(figsize=(6.4, 4.8))
        tiers = [t for t in ("S", "M", "L", "X") if any(r["tier"] == t for r in q)]
        w = 0.35
        for off, key, lab, col in ((-w / 2, "mean_wait_p9plus_urgency", "urgency order (ours)", "tab:blue"),
                                    (w / 2, "mean_wait_p9plus_fifo", "first come, first served", "tab:red")):
            ys = [max(1e-1, sum(float(r[key]) for r in q if r["tier"] == t) / len([r for r in q if r["tier"] == t])) for t in tiers]
            ax.bar([i + off for i in range(len(tiers))], ys, width=w, label=lab, color=col)
        ax.set_yscale("log")
        ax.set_xticks(range(len(tiers)))
        ax.set_xticklabels([f"tier {t}" for t in tiers])
        finish(fig, ax, os.path.join(folder, "plots", "D-wait-of-urgent-alarms.png"),
               "Module D: waiting time of priority 9 and 10 alarms",
               "Figure D2. Mean number of ticks that an alarm of priority 9 or 10 waits before release, averaged over the sampled cases of each tier. "
               "The mean wait of all alarms is identical in both orders; only who waits changes.",
               "group of cases (master data sample)", "mean wait of priority 9 and 10 alarms (ticks)")
    with open(os.path.join(folder, "plots", "captions.md"), "w", encoding="utf-8") as f:
        f.write("# Captions of the plots\n\n" + "\n\n".join(CAPTIONS) + "\n")


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results")
    rows = load(folder)
    fit_rows = fits(rows)
    write_fit_files(folder, fit_rows)
    comparison_tables(folder, rows)
    quality_tables(folder)
    make_plots(folder, rows)
    print(open(os.path.join(folder, "fits-AD.md"), encoding="utf-8").read())


if __name__ == "__main__":
    main()
