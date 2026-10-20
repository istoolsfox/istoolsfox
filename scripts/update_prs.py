#!/usr/bin/env python3
"""Regenerate the merged-PR table between OSS-PRS markers in README.md.

Pulls every public merged PR authored by the repo owner via the search API
(is:public keeps private-repo activity out), newest first, and rewrites the
<details> block. Run in CI with GITHUB_TOKEN set.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

MARK_START = "<!-- OSS-PRS:START -->"
MARK_END = "<!-- OSS-PRS:END -->"
OWNER = os.environ.get("OWNER", "istoolsfox")
README = sys.argv[1] if len(sys.argv) > 1 else "README.md"

token = os.environ["GITHUB_TOKEN"]
query = f"is:pr is:merged author:{OWNER} is:public"
url = (
    "https://api.github.com/search/issues?"
    + urllib.parse.urlencode(
        {"q": query, "per_page": 100, "sort": "created", "order": "desc"}
    )
)
req = urllib.request.Request(
    url,
    headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-readme-update",
    },
)
data = json.load(urllib.request.urlopen(req, timeout=30))

items = sorted(data.get("items", []), key=lambda x: x.get("closed_at") or "", reverse=True)
rows = []
for it in items:
    owner_login, repo = it["repository_url"].rstrip("/").split("/")[-2:]
    if owner_login.lower() == OWNER.lower():
        continue  # PR 到自己仓库的不算"上游贡献"
    title = it["title"].replace("|", "\\|")
    rows.append(f"| {repo} | {title} | [#{it['number']}]({it['html_url']}) |")

count = data.get("total_count", len(rows))
block = (
    "<details open>\n"
    f"<summary><h3>🧩 开源贡献 · {count} 个 PR 已合并</h3></summary>\n"
    "\n"
    "| 上游项目 | 我的改动 | PR |\n"
    "|---|---|---|\n"
    + "\n".join(rows)
    + "\n\n</details>"
)

with open(README, encoding="utf-8") as f:
    text = f.read()
start = text.index(MARK_START) + len(MARK_START)
end = text.index(MARK_END)
text = text[:start] + "\n" + block + "\n" + text[end:]
with open(README, "w", encoding="utf-8") as f:
    f.write(text)

print(f"total_count={count}, rows={len(rows)}")
