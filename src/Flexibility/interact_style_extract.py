# Get interaction styles by processing log files
import json
import re
import sys

SEL_REGEX = {
    "Canvas": re.compile(r"(drag(?:AndDrop)?|canvas|svg|diagram|board)", re.I),
    "Table":  re.compile(r"(tbody|tr>|td>|grid|table|row|column|cell|openTable)", re.I),
    "Form":   re.compile(r"(type|fill|select|input|textarea|submit|login|\[type=)", re.I),
    "Navigation": re.compile(r"(menu|sidebar|btn-nav|href|goto|navigate|openPage|clickMenu)", re.I),
}
STYLE_ORDER = ["Canvas", "Table", "Form", "Navigation"]

FALLBACK_BY_ACTION = {
    "forward": "Navigation", "back": "Navigation",
    "switch_tab": "Navigation", "assert_url": "Navigation",
    "write": "Form", "submit": "Form", "select": "Form",
}

FUNC_PAT = re.compile(
    r'## Agent response part 2: function_call\s*{\s*name:\s*"(?P<name>\w+)"'
    r'(?P<body>[\s\S]+?)^\d{4}-\d{2}-\d{2}',  # 直到下一条日志时间戳
    re.M
)
CSS_SEL_PAT = re.compile(r'key:\s*"css_selector"[\s\S]*?string_value:\s*"([^"]+)"', re.S)
URL_PAT     = re.compile(r'key:\s*"url"[\s\S]*?string_value:\s*"([^"]+)"', re.S)

SUCCESS_FMT = r"✅\s*Action\s*'{act}'\s*was\s*done"
FAIL_FMT    = r"❌\s*Error while executing action\s*'{act}'"

def classify(selector: str | None, url: str | None, act: str) -> str:
    if selector:
        for style in STYLE_ORDER:
            if SEL_REGEX[style].search(selector):
                return style
    if url:
        return "Navigation"
    return FALLBACK_BY_ACTION.get(act, "Uncategorized")

def parse_one_log(log_txt: str) -> list[dict]:
    actions = []
    matches = list(FUNC_PAT.finditer(log_txt))
    for idx, m in enumerate(matches):
        start, end = m.span()
        body = m.group("body")
        act  = m.group("name")

        selector = CSS_SEL_PAT.search(body)
        url      = URL_PAT.search(body)
        selector = selector.group(1) if selector else None
        url      = url.group(1) if url else None

        next_start = matches[idx + 1].start() if idx + 1 < len(matches) else len(log_txt)
        window = log_txt[end:next_start]

        success_re = re.compile(SUCCESS_FMT.format(act=re.escape(act)))
        fail_re    = re.compile(FAIL_FMT.format(act=re.escape(act)))

        success = None
        if success_re.search(window):
            success = True
        elif fail_re.search(window):
            success = False

        actions.append({
            "name": act,
            "category": classify(selector, url, act),
            "success": success,
        })
    return actions


def main(src, dst):
    with open(dst, "w", encoding="utf-8") as fout:
        for n, log in sorted(src.items()):
            json.dump({"number": n, "actions": parse_one_log(log)}, fout, ensure_ascii=False)
            fout.write("\n")
    print(f"✅ output → {dst}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python parse_agent_logs.py <input.jsonl> <output.jsonl>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
