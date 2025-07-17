"""
统计 UI 复杂度 JSONL 文件：
  1. total_dom_elements
  2. num_interactive_elements
  3. dom_tree_depth

输出：
  - overall  : 所有行的统计
  - per-project: 若每行包含 "project"，则附加分项目统计
"""

import argparse, json, sys, statistics
from collections import defaultdict

FIELDS = ["total_dom_elements", "num_interactive_elements", "dom_tree_depth"]

def update(stats, rec):
    for f in FIELDS:
        stats[f]["sum"] += rec[f]
        stats[f]["max"] = max(stats[f]["max"], rec[f])
        stats[f]["min"] = min(stats[f]["min"], rec[f])
        stats[f]["vals"].append(rec[f])

def finalize(stats):
    result = {}
    for f, d in stats.items():
        vals = d["vals"]
        result[f] = {
            "total": d["sum"],
            "mean":  round(statistics.mean(vals), 2),
            "max":   d["max"],
            "min":   d["min"],
            "count": len(vals)
        }
    return result

def pretty_print(title, res):
    print(f"\n=== {title} ===")
    for f, m in res.items():
        print(f"{f:25}: "
              f"total={m['total']:>8} | "
              f"mean={m['mean']:>6} | "
              f"max={m['max']:>6} | "
              f"min={m['min']:>6} | "
              f"n={m['count']}")
    print("-" * 60)

def main(paths):
    # stats["overall"] 和 stats[project_name] 结构相同
    base_tpl = lambda: {f: {"sum":0,"max":-1e9,"min":1e9,"vals":[]} for f in FIELDS}
    stats = defaultdict(base_tpl)

    for path in paths:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                rec = json.loads(line)
                project = rec.get("project", "_overall")
                update(stats["_overall"], rec)
                update(stats[project],   rec)

    # 打印整体
    pretty_print("OVERALL", finalize(stats["_overall"]))

    # 打印每项目（去掉整体条目）
    for proj, st in stats.items():
        if proj in ("_overall",): continue
        pretty_print(f"PROJECT → {proj}", finalize(st))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Aggregate UI-metrics JSONL files.")
    parser.add_argument("files", nargs="+", help="metrics_*.jsonl file(s)")
    args = parser.parse_args()
    main(args.files)
