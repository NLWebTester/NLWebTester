"""
------------------------
Collect UI-complexity metrics (DOM size, tree depth, interactive element count)
for a list of web projects

usage:
========
1. open Chrome/Chromium manually
       chrome --remote-debugging-port=9222
              --user-data-dir=/tmp/rq2_profile
   finish log in，and keep the window open

2. write projects.yaml（project name: base URL）:
       nocodb:  http://localhost:8080

3. run script（default http://localhost:9222）:
       python ui_complexity_crawler.py -c projects.yaml -o ui_metrics
"""

import asyncio
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import yaml
import pandas as pd
from playwright.async_api import async_playwright

# JS snippet executed in browser
JS_METRICS = """
(() => {
  const total = document.getElementsByTagName('*').length;
  const interact = document.querySelectorAll(
    'button,input,select,textarea,a'
  ).length;
  function depth(n){return n.children.length
      ? 1 + Math.max(...[...n.children].map(depth))
      : 1;}
  const treeDepth = depth(document.documentElement);
  return { total_dom_elements: total,
           num_interactive_elements: interact,
           dom_tree_depth: treeDepth,
           url: location.href };
})();
"""

_ATTR_RE  = re.compile(r'\s+\w+="[^"]*"')
_SPACE_RE = re.compile(r'\s+')

def dom_signature(html: str) -> str:
    """Return MD5 of DOM structure after stripping attribute values/whitespace."""
    cleaned = _SPACE_RE.sub(' ', _ATTR_RE.sub('', html))
    return hashlib.md5(cleaned.encode()).hexdigest()

def same_origin(a: str, b: str) -> bool:
    ua, ub = urlparse(a), urlparse(b)
    return (ua.scheme, ua.hostname, ua.port) == (ub.scheme, ub.hostname, ub.port)

async def crawl_project(
    name: str,
    base_url: str,
    out_dir: Path,
    max_pages: int = 120,
    max_depth: int = 2,
):
    visited, seen_sig = set(), set()
    queue = [(base_url, 0)]
    out_path = out_dir / f"metrics_{name}.jsonl"
    fout = out_path.open("w", encoding="utf-8")

    async with async_playwright() as pw:
        cdp_url = os.getenv("CDP_ENDPOINT", "http://localhost:9222")
        browser = await pw.chromium.connect_over_cdp(cdp_url)

        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = await context.new_page()

        while queue and len(visited) < max_pages:
            url, depth = queue.pop(0)
            if url in visited or depth > max_depth:
                continue
            visited.add(url)

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
            except Exception:
                continue

            html = await page.content()
            sig = dom_signature(html)
            if sig not in seen_sig:
                seen_sig.add(sig)
                metrics = await page.evaluate(JS_METRICS)
                metrics["project"] = name
                fout.write(json.dumps(metrics) + "\n")


            links = await page.eval_on_selector_all(
                "a[href]",
                "els => els.map(e => e.href)"
            )
            for link in links:
                if same_origin(base_url, link):
                    queue.append((link, depth + 1))


        await page.close()
        if len(browser.contexts) > 1:
            await context.close()

    fout.close()
    print(f"[{name}] pages visited={len(visited)}, unique UI={len(seen_sig)} → {out_path}")

def aggregate(out_dir: Path, summary_csv: Path):
    rows = []
    for fp in out_dir.glob("metrics_*.jsonl"):
        data = [json.loads(l) for l in fp.read_text().splitlines()]
        if not data:
            continue
        df = pd.DataFrame(data)
        mean_vals = df[["total_dom_elements",
                        "dom_tree_depth",
                        "num_interactive_elements"]].mean()
        mean_vals["project"] = fp.stem.replace("metrics_", "")
        rows.append(mean_vals)
    if rows:
        (pd.DataFrame(rows)
           .set_index("project")
           .round(2)
           .to_csv(summary_csv))
        print(f"Summary saved to {summary_csv}")

def main():
    parser = argparse.ArgumentParser(
        description="Collect UI complexity metrics via an already-open browser."
    )
    parser.add_argument("-c", "--config", default="projects.yaml",
                        help="YAML mapping project_name → base URL")
    parser.add_argument("-o", "--out", default="ui_metrics",
                        help="Output directory")
    parser.add_argument("--max_pages", type=int, default=120,
                        help="Max pages to visit per project")
    parser.add_argument("--max_depth", type=int, default=2,
                        help="Max click depth from base URL")
    args = parser.parse_args()

    out_dir = Path(args.out); out_dir.mkdir(exist_ok=True)
    projects = yaml.safe_load(open(args.config, encoding="utf-8"))

    loop = asyncio.get_event_loop()
    tasks = [
        crawl_project(p, u, out_dir, args.max_pages, args.max_depth)
        for p, u in projects.items()
    ]
    loop.run_until_complete(asyncio.gather(*tasks))

    aggregate(out_dir, out_dir / "summary.csv")

if __name__ == "__main__":
    main()
