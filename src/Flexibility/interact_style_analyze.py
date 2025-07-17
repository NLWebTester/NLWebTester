import json
import sys
from collections import defaultdict

def main(src_path: str, dst_path: str, sum_path: str | None = None):

    total_cnt = success_cnt = failure_cnt = 0

    cat_counter = defaultdict(lambda: {"total": 0, "success": 0})

    with open(src_path, encoding="utf-8") as fin, open(dst_path, "w", encoding="utf-8") as fout:
        for line in fin:
            obj = json.loads(line)
            # without get and done
            actions = [a for a in obj["actions"] if a["name"] != "get"]
            obj["actions"] = actions
            actions = [a for a in obj["actions"] if a["name"] != "done"]
            obj["actions"] = actions

            for a in actions:
                cat = a["category"]
                cat_counter[cat]["total"] += 1
                total_cnt += 1

                if a["success"] is True:
                    cat_counter[cat]["success"] += 1
                    success_cnt += 1
                elif a["success"] is False:
                    failure_cnt += 1


            json.dump(obj, fout, ensure_ascii=False)
            fout.write("\n")

    summary = {
        "overall": {
            "total_actions": total_cnt,
            "total_success": success_cnt,
            "total_failure": failure_cnt,
            "success_rate": round(success_cnt / total_cnt, 4) if total_cnt else None,
        },
        "by_category": cat_counter
    }


    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if sum_path:
        with open(sum_path, "w", encoding="utf-8") as fsum:
            json.dump(summary, fsum, ensure_ascii=False, indent=2)
        print(f"✅ write in  {sum_path}")

    print(f"✅ write in {dst_path}")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        print("usage: python filter_and_summary.py <parsed.jsonl> <filtered.jsonl> [summary.json]")
        sys.exit(1)
    main(*sys.argv[1:])
