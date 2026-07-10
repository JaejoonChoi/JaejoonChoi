#!/usr/bin/env python3

from __future__ import annotations

import html
import math
import random
import re
import urllib.request
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


URLS = [
    "https://jaejoonchoi.github.io/",
    "https://jaejoonchoi.github.io/publications/",
    "https://jaejoonchoi.github.io/project/",
    "https://jaejoonchoi.github.io/portfolio/",
]

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "using",
    "from",
    "into",
    "that",
    "this",
    "your",
    "have",
    "has",
    "had",
    "are",
    "was",
    "were",
    "been",
    "being",
    "its",
    "their",
    "our",
    "you",
    "can",
    "will",
    "through",
    "based",
    "study",
    "book",
    "chapter",
    "published",
    "publication",
    "project",
    "projects",
    "portfolio",
    "lists",
    "experiences",
    "home",
    "homepage",
    "guide",
    "follow",
    "student",
    "students",
    "university",
    "lab",
    "data",
    "model",
    "models",
    "system",
    "systems",
    "analysis",
    "research",
    "paper",
    "poster",
    "conference",
    "journal",
    "classification",
    "classification",
    "detection",
    "management",
    "industrial",
    "engineering",
    "choi",
    "jaejoon",
    "jaejun",
    "korea",
    "kyung",
    "hee",
    "kumoh",
    "institute",
    "technology",
    "click",
    "expand",
    "contents",
    "role",
    "period",
    "present",
    "download",
    "article",
    "articles",
    "profile",
    "google",
    "scholar",
    "github",
    "linkedin",
    "email",
    "introduction",
    "welcome",
    "side",
    "work",
    "works",
    "based",
    "case",
    "used",
    "also",
    "than",
    "which",
    "into",
    "under",
    "within",
    "more",
    "most",
    "such",
    "only",
    "over",
    "both",
    "each",
    "within",
    "about",
    "after",
    "before",
    "where",
    "while",
    "during",
    "there",
    "these",
    "those",
    "them",
    "they",
    "their",
    "ours",
    "mine",
    "from",
    "2023",
    "2024",
    "2025",
    "2026",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
    "최재준",
}

KOREAN_STOPWORDS = {
    "그리고",
    "통해",
    "기반",
    "활용",
    "개발",
    "구축",
    "연구",
    "프로젝트",
    "데이터",
    "시스템",
    "분석",
    "모델",
    "학생",
    "경희대학교",
    "금오공과대학교",
    "최재준",
    "재준",
    "내용",
    "기간",
    "역할",
    "발표",
    "포스터",
    "학술대회",
    "논문",
    "대회",
    "클릭",
    "확장",
}

PALETTE = ["#0f4c81", "#2f80ed", "#27ae60", "#f2994a", "#eb5757", "#6c5ce7"]


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        return " ".join(self.parts)


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=20) as response:
        return response.read().decode("utf-8", errors="ignore")


def normalize_token(token: str) -> str | None:
    token = token.strip().lower()
    if not token:
        return None

    if re.fullmatch(r"[a-z][a-z0-9\-\+]{2,}", token):
        if token in STOPWORDS:
            return None
        return token

    if re.fullmatch(r"[가-힣]{2,}", token):
        if token in KOREAN_STOPWORDS:
            return None
        return token

    return None


def collect_tokens(text: str) -> Counter[str]:
    raw_tokens = re.findall(r"[A-Za-z][A-Za-z0-9\-\+]+|[가-힣]{2,}", text)
    counter: Counter[str] = Counter()
    for raw in raw_tokens:
        token = normalize_token(raw)
        if token:
            counter[token] += 1
    return counter


def estimate_box(word: str, font_size: int) -> tuple[float, float]:
    korean_chars = len(re.findall(r"[가-힣]", word))
    latin_chars = len(word) - korean_chars
    width = font_size * (korean_chars * 0.95 + latin_chars * 0.58)
    height = font_size * 1.15
    return width, height


def overlaps(box, placed) -> bool:
    x1, y1, x2, y2 = box
    for ox1, oy1, ox2, oy2 in placed:
        if not (x2 < ox1 or ox2 < x1 or y2 < oy1 or oy2 < y1):
            return True
    return False


def build_svg(words: list[tuple[str, int]], output_path: Path) -> None:
    width = 1200
    height = 700
    cx = width / 2
    cy = height / 2
    max_count = words[0][1]
    min_count = words[-1][1]
    rng = random.Random(42)
    placed_boxes = []
    elements = []

    for idx, (word, count) in enumerate(words):
        if max_count == min_count:
            scale = 0.5
        else:
            scale = (count - min_count) / (max_count - min_count)
        font_size = int(22 + scale * 46)
        box_w, box_h = estimate_box(word, font_size)
        angle_offset = rng.random() * math.pi * 2
        placed = False

        for step in range(1200):
            radius = 6 + step * 2.8
            theta = angle_offset + step * 0.42
            x = cx + math.cos(theta) * radius
            y = cy + math.sin(theta) * radius
            x1 = x - box_w / 2
            y1 = y - box_h / 2
            x2 = x + box_w / 2
            y2 = y + box_h / 2

            if x1 < 24 or y1 < 24 or x2 > width - 24 or y2 > height - 24:
                continue
            box = (x1, y1, x2, y2)
            if overlaps(box, placed_boxes):
                continue

            color = PALETTE[idx % len(PALETTE)]
            weight = 700 if font_size >= 48 else 600
            elements.append(
                f'<text x="{x:.1f}" y="{y:.1f}" '
                f'font-size="{font_size}" font-weight="{weight}" '
                f'fill="{color}" text-anchor="middle" dominant-baseline="middle">'
                f"{html.escape(word)}</text>"
            )
            placed_boxes.append(box)
            placed = True
            break

        if not placed:
            continue

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Word cloud from Jaejoon Choi portfolio">
  <rect width="100%" height="100%" fill="#f8fbff" rx="24" ry="24" />
  <text x="50%" y="56" text-anchor="middle" font-size="28" font-weight="700" fill="#12324a">Portfolio Word Cloud</text>
  <text x="50%" y="88" text-anchor="middle" font-size="15" fill="#4f6b81">Generated from jaejoonchoi.github.io content</text>
  {"".join(elements)}
</svg>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")


def main() -> None:
    combined = Counter()
    for url in URLS:
        extractor = TextExtractor()
        extractor.feed(fetch(url))
        combined.update(collect_tokens(extractor.text()))

    top_words = combined.most_common(55)
    output = Path("assets/portfolio-wordcloud.svg")
    build_svg(top_words, output)

    print("Top words:")
    for word, count in top_words[:20]:
        print(f"{word}: {count}")
    print(f"Saved to {output}")


if __name__ == "__main__":
    main()
