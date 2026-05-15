#!/usr/bin/env python3
"""Generate categorized Markdown index from GitHub starred repos."""
import json
import re
from collections import defaultdict
from datetime import datetime, timezone

INPUT = r"d:\AILAB\NING\TinyDay\Assets\starred_raw.json"
OUTPUT = r"d:\AILAB\NING\TinyDay\Assets\StarIndex\README.md"
# (id, name, emoji, priority, topic_exact, keywords)
CATEGORIES = [
    ("unreal-engine", "Unreal Engine / UE4·UE5", "🎯", 5, [
        "ue4", "ue5", "unreal-engine", "unrealengine", "unreal",
    ], [
        "unreal engine", "unreal-engine", "ue4", "ue5", "blueprint",
    ]),
    ("ai-ml", "AI / 机器学习 / LLM", "🤖", 10, [
        "ai", "machine-learning", "deep-learning", "llm", "gpt", "chatgpt",
        "pytorch", "tensorflow", "langchain", "stable-diffusion", "comfyui",
        "huggingface", "openai", "generative-ai", "computer-vision",
        "neural-network", "nlp", "transformers", "yolo", "llama",
    ], [
        "large language model", "diffusion", "transformer", "fine-tun",
        "segment anything", "whisper", "ollama", "vllm", "rag", "copilot",
        "autogpt", "agent", "inference", "embedding",
    ]),
    ("3d-vision", "3D / 视觉 / 图形学", "🎨", 20, [
        "3d", "computer-vision", "opencv", "nerf", "gaussian-splatting",
        "point-cloud", "slam", "webgl", "threejs", "blender",
    ], [
        "gaussian", "splat", "3dgs", "4dgs", "nerf", "mesh", "render",
        "reconstruction", "photogrammetry", "equirect", "cubemap", "panorama",
        "depth", "colmap", "radiance", "voxel", "lidar", "heatmap",
        "spacetime", "gsplat", "stereo", "pose estimation",
    ]),
    ("video-media", "视频 / 音频 / 媒体", "🎬", 30, [
        "video", "ffmpeg", "audio", "speech", "tts",
    ], [
        "ffmpeg", "subtitle", "transcode", "demucs", "lip-sync", "codec",
    ]),
    ("web-frontend", "Web / 前端", "🌐", 40, [
        "react", "vue", "frontend", "webgl", "typescript", "javascript",
        "nextjs", "tailwind", "vite", "electron",
    ], [
        "react", "vue", "next.js", "nextjs", "svelte", "angular",
        "tailwind", "webpack", "dashboard", "mini-program", "wechat",
    ]),
    ("backend-devops", "后端 / DevOps / 基础设施", "⚙️", 50, [
        "docker", "kubernetes", "devops", "redis", "fastapi", "django",
    ], [
        "kubernetes", "microservice", "terraform", "ansible", "nginx",
        "postgres", "mongodb", "kafka", "rabbitmq", "prometheus", "celery",
        "flask", "grpc", "github-actions",
    ]),
    ("data-db", "数据 / 数据库 / 分析", "📊", 55, [
        "data-science", "database", "analytics", "jupyter", "pandas",
    ], [
        "dataset", "etl", "spark", "clickhouse", "duckdb", "parquet",
        "visualization", "notebook", "warehouse",
    ]),
    ("game-unity", "Unity / 游戏引擎", "🎮", 58, [
        "unity", "godot", "game-development",
    ], [
        "unity3d", "godot", "game engine", "game development",
    ]),
    ("mobile", "移动开发", "📱", 62, [
        "android", "ios", "flutter", "react-native",
    ], [
        "flutter", "react-native", "swift", "kotlin",
    ]),
    ("robot-iot", "机器人 / IoT / 硬件", "🔧", 70, [
        "robotics", "iot", "embedded", "arduino", "esp32", "ros",
    ], [
        "raspberry", "mqtt", "firmware", "drone", "sensor",
    ]),
    ("security", "安全 / 隐私", "🔒", 80, [
        "security", "cryptography", "privacy",
    ], [
        "pentest", "vulnerability", "oauth", "encrypt", "malware",
    ]),
    ("tools-cli", "工具 / CLI / 自动化", "🛠️", 90, [
        "cli", "automation", "productivity", "vscode", "neovim",
    ], [
        "command-line", "scraper", "workflow", "dotfiles", "plugin",
    ]),
    ("edu-awesome", "教程 / 文档 / Awesome", "📚", 100, [
        "awesome-list", "tutorial", "roadmap", "learning-resources",
    ], [
        "awesome-", "cheatsheet", "interview", "course", "roadmap",
    ]),
]

TOPIC_TO_CAT = {}
for cat_id, _, _, _, topics, _ in CATEGORIES:
    for t in topics:
        TOPIC_TO_CAT[t.lower()] = cat_id

AUTO_TAGS = [
    ("star:popular", lambda r: (r.get("stargazers_count") or 0) >= 1000),
    ("star:notable", lambda r: 100 <= (r.get("stargazers_count") or 0) < 1000),
    ("fork", lambda r: r.get("fork") is True),
    ("archived", lambda r: r.get("archived") is True),
]

SHORT_KW = frozenset({"ai", "ml", "3d", "vr", "ui", "go", "ar", "api", "rag"})


def load_repos():
    with open(INPUT, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def text_blob(repo, include_topics=True):
    parts = [
        repo.get("full_name") or "",
        repo.get("name") or "",
        repo.get("description") or "",
    ]
    if include_topics:
        parts.extend(repo.get("topics") or [])
    return " ".join(parts).lower()


def kw_match(blob, kw):
    kw = kw.lower().strip()
    if not kw:
        return False
    if len(kw) <= 3 or kw in SHORT_KW:
        return bool(re.search(r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])", blob))
    return kw in blob


def score_category(repo, cat_id, topic_exact, keywords):
    score = 0
    topics = [t.lower() for t in (repo.get("topics") or [])]
    blob = text_blob(repo)
    name_desc = text_blob(repo, include_topics=False)

    for t in topics:
        if t in topic_exact:
            score += 5
        if t in TOPIC_TO_CAT and TOPIC_TO_CAT[t] == cat_id:
            score += 3

    for kw in keywords:
        if kw_match(blob, kw):
            score += 2 if kw in name_desc else 1

    return score


def classify(repo):
    best_cat, best_score, best_pri = "other", 0, 9999
    for cat_id, _, _, priority, topic_exact, keywords in CATEGORIES:
        s = score_category(repo, cat_id, set(topic_exact), keywords)
        if s > best_score or (s == best_score and s > 0 and priority < best_pri):
            best_cat, best_score, best_pri = cat_id, s, priority

    if best_cat != "other":
        return best_cat

    lang = repo.get("language") or ""
    topics = [t.lower() for t in (repo.get("topics") or [])]
    if any(t in TOPIC_TO_CAT for t in topics):
        return TOPIC_TO_CAT[topics[0]]
    if lang in ("Python", "Jupyter Notebook"):
        return "ai-ml"
    if lang in ("JavaScript", "TypeScript", "HTML", "CSS"):
        return "web-frontend"
    if lang in ("C++", "C", "GLSL", "HLSL"):
        return "3d-vision"
    if lang == "C#":
        return "game-unity"
    if lang in ("Go", "Rust", "Shell", "Dockerfile"):
        return "backend-devops"
    return "other"


def derive_tags(repo, primary_cat):
    tags = []
    tags.append(f"cat:{primary_cat}")

    for t in (repo.get("topics") or [])[:5]:
        tags.append(f"topic:{t}")

    if repo.get("language"):
        tags.append(f"lang:{repo['language'].lower().replace(' ', '-')}")

    for tag_id, fn in AUTO_TAGS:
        if fn(repo):
            tags.append(tag_id)

    # README proxy: first line of description as hint tag
    desc = (repo.get("description") or "").strip()
    if desc:
        words = re.findall(r"[a-zA-Z][a-zA-Z0-9+.#-]{2,}", desc.lower())
        stop = {"the", "and", "for", "with", "this", "that", "from", "your", "are", "you"}
        for w in words[:3]:
            if w not in stop and len(tags) < 10:
                tags.append(w)

    return tags[:10]


def esc(s):
    if not s:
        return ""
    return s.replace("|", "\\|").replace("\n", " ")


def repo_desc(repo, i18n_cache):
    from desc_i18n import format_bilingual

    full = repo.get("full_name") or ""
    return esc(format_bilingual(full, repo.get("description"), cache=i18n_cache, persist=False))


def main():
    from desc_i18n import _load_cache, _save_cache, warm_cache_for_repos

    repos = load_repos()
    repos.sort(key=lambda r: (-(r.get("stargazers_count") or 0), r.get("full_name") or ""))

    print("Building bilingual descriptions (cached where possible)...")
    i18n_cache = warm_cache_for_repos(
        repos,
        on_progress=lambda n, t, name: print(f"  [{n}/{t}] {name}") if n % 20 == 0 or n == t else None,
    )
    _save_cache(i18n_cache)

    cat_map = {c[0]: (c[1], c[2]) for c in CATEGORIES}
    cat_map["other"] = ("其他 / 未分类", "📦")

    by_cat = defaultdict(list)
    all_tags = defaultdict(int)

    for repo in repos:
        cat = classify(repo)
        repo["_category"] = cat
        repo["_tags"] = derive_tags(repo, cat)
        by_cat[cat].append(repo)
        for t in repo["_tags"]:
            all_tags[t] += 1

    order = [c[0] for c in CATEGORIES] + ["other"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# ⭐ GitHub Stars 索引",
        "",
        "<p align=\"center\">",
        "  <strong>个人 GitHub Star 收藏目录</strong><br/>",
        f"  <sub>@{ 'o0pk2008' } · {len(repos)} repos · 自动生成</sub>",
        "</p>",
        "",
        "> 基于 **Topics / Description / Language** 自动分类与打标。",
        f"> 数据源：[o0pk2008 starred](https://github.com/o0pk2008?tab=stars) · 更新 **{now}**",
        "",
        "## 📑 目录",
        "",
    ]

    for cat_id in order:
        if cat_id not in by_cat:
            continue
        name, emoji = cat_map[cat_id]
        lines.append(f"- [{emoji} {name}](#{cat_id}) — **{len(by_cat[cat_id])}**")

    lang_counts = defaultdict(int)
    topic_counts = defaultdict(int)
    for r in repos:
        lang_counts[r.get("language") or "Unknown"] += 1
        for t in r.get("topics") or []:
            topic_counts[t] += 1

    lines.extend([
        "",
        "## 📈 统计",
        "",
        "| 指标 | 值 |",
        "|------|-----|",
        f"| 收藏总数 | {len(repos)} |",
        f"| 分类数 | {len(by_cat)} |",
        f"| 含 Topics | {sum(1 for r in repos if r.get('topics'))} |",
        "",
        "<details>",
        "<summary><strong>语言分布</strong></summary>",
        "",
        "| 语言 | 数量 |",
        "|------|------|",
    ])
    for lang, cnt in sorted(lang_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {lang} | {cnt} |")
    lines.append("")
    lines.append("</details>")
    lines.append("")

    if topic_counts:
        lines.extend([
            "<details>",
            "<summary><strong>热门 Topics</strong></summary>",
            "",
            "| Topic | 数量 |",
            "|-------|------|",
        ])
        for topic, cnt in sorted(topic_counts.items(), key=lambda x: -x[1])[:20]:
            lines.append(f"| `{topic}` | {cnt} |")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    lines.extend([
        "## 🏷️ 标签体系",
        "",
        "| 标签 | 说明 |",
        "|------|------|",
        "| `cat:*` | 主分类（互斥） |",
        "| `topic:*` | GitHub 官方 Topics |",
        "| `lang:*` | 主语言 |",
        "| `star:popular` | Star ≥ 1k |",
        "| `star:notable` | Star 100–999 |",
        "",
        "---",
        "",
    ])

    for cat_id in order:
        if cat_id not in by_cat:
            continue
        name, emoji = cat_map[cat_id]
        items = by_cat[cat_id]
        lines.append(f'<a id="{cat_id}"></a>')
        lines.append("")
        lines.append(f"## {emoji} {name}")
        lines.append("")
        lines.append(f"<!-- {len(items)} repositories -->")
        lines.append("")
        lines.append("<details open>")
        lines.append(f"<summary><strong>展开列表（{len(items)}）</strong></summary>")
        lines.append("")
        lines.append("| ⭐ | 仓库 | 描述（中 / EN） | 语言 | 标签 |")
        lines.append("|:---:|:-----|:-----|:----:|:-----|")

        for r in items:
            stars = r.get("stargazers_count") or 0
            star_str = f"**{stars:,}**" if stars >= 1000 else str(stars)
            full = r.get("full_name") or ""
            url = r.get("html_url") or f"https://github.com/{full}"
            desc = repo_desc(r, i18n_cache) or "—"
            lang = r.get("language") or "—"
            tag_str = " ".join(f"`{t}`" for t in r.get("_tags", [])[:8])
            lines.append(f"| {star_str} | [{full}]({url}) | {desc} | {lang} | {tag_str} |")

        lines.append("")
        lines.append("</details>")
        lines.append("")

    # Flat A-Z index
    lines.extend([
        "---",
        "",
        "## 🔤 字母索引（A→Z）",
        "",
    ])
    by_letter = defaultdict(list)
    for r in repos:
        letter = (r.get("full_name") or "?")[0].upper()
        if not letter.isalnum():
            letter = "#"
        by_letter[letter].append(r)

    for letter in sorted(by_letter.keys()):
        items = sorted(by_letter[letter], key=lambda r: r.get("full_name", "").lower())
        links = " · ".join(
            f"[{r['full_name'].split('/')[-1]}]({r.get('html_url')})"
            for r in items
        )
        lines.append(f"### {letter}")
        lines.append("")
        lines.append(links)
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 🔄 更新方式",
        "",
        "```bash",
        "# 1. 拉取最新 Star 列表（PowerShell）",
        "$page=1; $all=@(); do {",
        "  $r = Invoke-RestMethod \"https://api.github.com/users/o0pk2008/starred?per_page=100&page=$page\"",
        "  $all += $r; $page++",
        "} while ($r.Count -eq 100)",
        "$all | ConvertTo-Json -Depth 6 | Out-File starred_raw.json -Encoding utf8",
        "",
        "# 2. 重新生成本 README",
        "py -3 generate_star_index.py",
        "```",
        "",
        "---",
        "",
        "*Generated by [`generate_star_index.py`](../generate_star_index.py)*",
        "",
    ])

    import os
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote {OUTPUT} ({len(lines)} lines)")
    for cat_id in order:
        if cat_id in by_cat:
            print(f"  {cat_id}: {len(by_cat[cat_id])}")


if __name__ == "__main__":
    main()
