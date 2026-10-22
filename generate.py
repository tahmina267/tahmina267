"""Builds profile-dark.svg and profile-light.svg, the profile card: a sky with one star per day of the
last year (brighter on busier days, joined into a constellation) next to a clean info panel.

Run locally with `GH_TOKEN=... python generate.py`. The GitHub Action in .github/workflows/build.yml
runs it daily so the sky follows your activity.
"""
import json
import os
import random
import urllib.request
from html import escape
from pathlib import Path

USER = "tahmina267"
ROOT = Path(__file__).parent

THEMES = {
    "dark": dict(bg="#161b22", text="#e6edf3", key="#ffa657", value="#a5d6ff", cc="#3d444d", muted="#7d8590", border="#30363d",
                 sky="#0b1026", star="#e8eeff", glow="#9db4ff", moon="#f3ead7"),
    "light": dict(bg="#f6f8fa", text="#1f2328", key="#953800", value="#0a3069", cc="#d0d7de", muted="#8c959f", border="#d0d7de",
                  sky="#1b2350", star="#f4f6ff", glow="#b9c8ff", moon="#f7efdc"),
}

# (key, value) rows; a string is a section title, None is a blank line
CARD = [
    "tahmina@sultana",
    ("OS", "macOS, Linux, Windows"),
    ("Role", "UI/UX Designer, SQA Engineer & Project Manager"),
    ("IDE", "VS Code, Claude Code, Figma"),
    None,
    ("Languages.Programming", "Python, JavaScript, TypeScript, SQL, C++"),
    ("Languages.Computer", "HTML, CSS, JSON, Markdown, YAML"),
    ("Languages.Real", "Bengali, English"),
    None,
    ("Stack.Design", "Figma, Framer, Protopie"),
    ("Stack.Frontend", "React, Next.js, Tailwind CSS, three.js"),
    ("Stack.Testing", "Playwright, Storybook, VoiceOver"),
    ("Stack.AI", "RAG, tool-calling agents, evals"),
    None,
    ("Education", "B.Sc. CSE, North South University (2025)"),
    None,
    "Contact",
    ("Email", "tahminasultana2609@gmail.com"),
    ("LinkedIn", "tahmina-sultana-188051247"),
    ("Portfolio", "portfolio-tahmina5.vercel.app"),
]


def contributions():
    """Daily contribution counts for the past year (GraphQL, needs a token)."""
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    q = {"query": 'query{user(login:"%s"){contributionsCollection{contributionCalendar{weeks{contributionDays{contributionCount}}}}}}' % USER}
    try:
        req = urllib.request.Request("https://api.github.com/graphql", json.dumps(q).encode(),
                                     {"Authorization": f"Bearer {token}", "User-Agent": USER})
        with urllib.request.urlopen(req, timeout=30) as r:
            weeks = json.load(r)["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        return [d["contributionCount"] for w in weeks for d in w["contributionDays"]]
    except Exception:
        return [0] * 365


def sky(c, counts, x0, y0, w, h):
    """One star per day of the last year. Brighter for busier days; the busiest twinkle."""
    rnd = random.Random(267)  # fixed seed: each day keeps its place in the sky
    top = max(counts) or 1
    out = [f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="10" fill="{c["sky"]}"/>']
    mx, my = x0 + w - 48, y0 + 44
    out.append(f'<circle cx="{mx}" cy="{my}" r="16" fill="{c["moon"]}"/>')
    out.append(f'<circle cx="{mx + 7}" cy="{my - 5}" r="14" fill="{c["sky"]}"/>')
    stars, path = [], []
    for n in counts:
        x = x0 + 14 + rnd.random() * (w - 28)
        y = y0 + 14 + rnd.random() * (h - 58)
        if (x - mx) ** 2 + (y - my) ** 2 < 30 ** 2:
            continue
        if n == 0:
            stars.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="0.7" fill="{c["star"]}" opacity="0.28"/>')
            continue
        path.append((x, y))
        t = n / top
        r = 1.1 + 2.2 * t
        if t > 0.45:  # bright day: glow, four-point sparkle, slow twinkle
            dur = 2.5 + rnd.random() * 3
            stars.append(f'<g><animate attributeName="opacity" values="1;0.45;1" dur="{dur:.1f}s" repeatCount="indefinite"/>'
                         f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * 3:.1f}" fill="{c["glow"]}" opacity="0.18"/>'
                         f'<path d="M{x:.1f} {y - r * 2.6:.1f}L{x + r * 0.45:.1f} {y:.1f}L{x:.1f} {y + r * 2.6:.1f}L{x - r * 0.45:.1f} {y:.1f}Z'
                         f'M{x - r * 2.6:.1f} {y:.1f}L{x:.1f} {y + r * 0.45:.1f}L{x + r * 2.6:.1f} {y:.1f}L{x:.1f} {y - r * 0.45:.1f}Z" fill="{c["star"]}"/></g>')
        else:
            stars.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{c["star"]}" opacity="{0.55 + 0.45 * t:.2f}"/>')
    if len(path) > 1:  # active days joined in date order: the year draws its own constellation
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in path)
        out.append(f'<path d="{d}" fill="none" stroke="{c["glow"]}" stroke-width="0.8" stroke-opacity="0.35" stroke-dasharray="2 3"/>')
    out += stars
    active = sum(1 for n in counts if n)
    out.append(f'<text x="{x0 + 14}" y="{y0 + h - 34}" font-size="13px" fill="{c["star"]}" opacity="0.9" font-style="italic">dreaming in code and stardust ✦</text>')
    out.append(f'<text x="{x0 + 14}" y="{y0 + h - 15}" font-size="11px" fill="{c["glow"]}" opacity="0.6">your year in stars · {active} bright days</text>')
    return out


def svg(theme, counts):
    c = THEMES[theme]
    fs, cw, pad, sky_w = 16, 9.6, 34, 300
    rows = [r for r in CARD if isinstance(r, tuple)]
    cols = max(len(k) + 1 + 3 + len(v) for k, v in rows)   # "key:" + gap + value, never overlapping
    x0 = pad + sky_w + 30
    width = int(x0 + cols * cw + pad)
    y, body = pad + 12, []
    for r in CARD:
        if r is None:
            y += 12
            continue
        if isinstance(r, str):
            if body:
                y += 6
            tw = len(r) * cw
            body.append(f'<text x="{x0}" y="{y}" fill="{c["text"]}" font-weight="700">{escape(r)}</text>')
            body.append(f'<line x1="{x0 + tw + 12:.0f}" y1="{y - 5}" x2="{width - pad}" y2="{y - 5}" stroke="{c["cc"]}" stroke-dasharray="4 4"/>')
        else:
            k, v = r
            body.append(f'<text x="{x0}" y="{y}" fill="{c["key"]}">{escape(k)}:</text>')
            body.append(f'<text x="{width - pad}" y="{y}" fill="{c["value"]}" text-anchor="end">{escape(v)}</text>')
        y += 24
    height = y + pad - 18
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,\'Courier New\',monospace" font-size="{fs}px">',
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="14" fill="{c["bg"]}" stroke="{c["border"]}"/>',
        *sky(c, counts, 22, 22, sky_w, height - 44),
        *body,
        "</svg>",
    ])


def main():
    counts = contributions()
    for theme in THEMES:
        (ROOT / f"profile-{theme}.svg").write_text(svg(theme, counts))


if __name__ == "__main__":
    main()
