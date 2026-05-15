#!/usr/bin/env python3
"""Patch STARRED_INDEX.md table descriptions to bilingual ZH / EN."""
import json
import re

from desc_i18n import _load_cache, _save_cache, format_bilingual, warm_cache_for_repos

INPUT = r"d:\AILAB\NING\TinyDay\Assets\starred_raw.json"
INDEX = r"d:\AILAB\NING\TinyDay\Assets\STARRED_INDEX.md"

def patch_row(line: str, desc: str) -> str:
    parts = line.rstrip("\n").split(" | ")
    # | stars | [repo](url) | desc | lang | tags |
    if len(parts) < 5 or not parts[1].startswith("["):
        return line.rstrip("\n")
    parts[2] = desc.replace("|", "\\|")
    return " | ".join(parts)


def main():
    with open(INPUT, "r", encoding="utf-8-sig") as f:
        repos = json.load(f)
    by_name = {r["full_name"]: r for r in repos if r.get("full_name")}

    print("Translating descriptions (uses cache)...")
    cache = warm_cache_for_repos(repos)
    _save_cache(cache)

    with open(INDEX, "r", encoding="utf-8") as f:
        lines = f.readlines()

    out = []
    updated = 0
    for line in lines:
        if "| 仓库 | 描述 |" in line:
            out.append(line.replace("| 描述 |", "| 描述（中 / EN） |"))
            continue
        m = re.match(r"^\| [^|]+ \| \[([^\]]+)\]\([^)]+\) \|", line)
        if m:
            full = m.group(1)
            repo = by_name.get(full)
            desc = format_bilingual(full, repo.get("description") if repo else None, cache=cache, persist=False)
            new_line = patch_row(line, desc)
            if new_line != line.rstrip("\n"):
                updated += 1
            out.append(new_line + "\n")
            continue
        out.append(line)

    _save_cache(cache)
    with open(INDEX, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(out)
    print(f"Patched {INDEX}: {updated} rows updated.")


if __name__ == "__main__":
    main()
