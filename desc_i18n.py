"""Bilingual (ZH / EN) GitHub repo descriptions with disk cache."""
from __future__ import annotations

import json
import os
import re
import time

CACHE_PATH = os.path.join(os.path.dirname(__file__), "starred_desc_i18n.json")

CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")
LATIN_WORD_RE = re.compile(r"[a-zA-Z]{2,}")


def has_cjk(text: str) -> bool:
    return bool(CJK_RE.search(text))


def has_latin_words(text: str) -> bool:
    return bool(LATIN_WORD_RE.search(text))


def _load_cache() -> dict:
    if os.path.isfile(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict) -> None:
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _translate(text: str, source: str, target: str) -> str:
    from deep_translator import GoogleTranslator

    return GoogleTranslator(source=source, target=target).translate(text)


def _split_zh_en(text: str) -> tuple[str, str]:
    """Best-effort split when description already mixes languages."""
    parts = re.split(r"\s*[/|｜]\s*|\s*——\s*|\s*--\s*", text, maxsplit=1)
    if len(parts) == 2:
        a, b = parts[0].strip(), parts[1].strip()
        if has_cjk(a) and has_latin_words(b):
            return a, b
        if has_cjk(b) and has_latin_words(a):
            return b, a
    return "", ""


def bilingual_pair(full_name: str, description: str | None, cache: dict | None = None) -> tuple[str, str]:
    """Return (zh, en) for a repo description."""
    if cache is None:
        cache = _load_cache()

    if full_name in cache:
        entry = cache[full_name]
        return entry["zh"], entry["en"]

    desc = (description or "").strip()
    if not desc:
        return "", ""

    zh, en = _split_zh_en(desc)
    if zh and en:
        cache[full_name] = {"zh": zh, "en": en}
        return zh, en

    try:
        if has_cjk(desc) and not has_latin_words(desc):
            zh, en = desc, _translate(desc, "zh-CN", "en")
        elif has_latin_words(desc) and not has_cjk(desc):
            en, zh = desc, _translate(desc, "en", "zh-CN")
        elif has_cjk(desc) and has_latin_words(desc):
            zh, en = desc, _translate(desc, "auto", "en")
            if has_cjk(en):
                en = _translate(desc, "auto", "en")
            if not has_cjk(zh) or len(zh) < len(desc) * 0.3:
                zh = _translate(desc, "auto", "zh-CN")
        else:
            zh, en = desc, desc
    except Exception:
        zh, en = desc, desc

    cache[full_name] = {"zh": zh, "en": en}
    time.sleep(0.15)
    return zh, en


def format_bilingual(
    full_name: str,
    description: str | None,
    *,
    max_each: int = 90,
    cache: dict | None = None,
    persist: bool = True,
) -> str:
    desc = (description or "").strip()
    if not desc:
        return "—"

    if cache is None:
        cache = _load_cache()

    zh, en = bilingual_pair(full_name, desc, cache)

    if zh and en and zh.strip() == en.strip():
        text = zh[: max_each * 2]
    elif zh and en:
        z = zh if len(zh) <= max_each else zh[: max_each - 1] + "…"
        e = en if len(en) <= max_each else en[: max_each - 1] + "…"
        text = f"{z} / {e}"
    elif zh:
        text = zh[:max_each]
    else:
        text = en[:max_each]

    if persist:
        _save_cache(cache)
    return text


def warm_cache_for_repos(repos: list, on_progress=None) -> dict:
    cache = _load_cache()
    total = len(repos)
    for i, repo in enumerate(repos):
        full = repo.get("full_name") or ""
        desc = repo.get("description")
        if desc and full and full not in cache:
            format_bilingual(full, desc, cache=cache, persist=False)
            if on_progress:
                on_progress(i + 1, total, full)
    _save_cache(cache)
    return cache
