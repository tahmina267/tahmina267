"""Builds card-dark.svg and card-light.svg, the info card on the profile README.

Run locally with `python generate.py`. The GitHub Action in .github/workflows/build.yml runs it
whenever this file changes.
"""
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent

THEMES = {
    "dark": dict(bg="#161b22", text="#e6edf3", key="#ffa657", value="#a5d6ff", cc="#3d444d", border="#30363d"),
    "light": dict(bg="#f6f8fa", text="#1f2328", key="#953800", value="#0a3069", cc="#d0d7de", border="#d0d7de"),
}

# (key, value) rows; a string is a section title, None is a blank line
CARD = [
    "tahmina@sultana",
    ("OS", "macOS, Linux, Windows"),
    ("Host", "Makebell Limited"),
    ("Role", "SQA Engineer & Project Manager"),
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


def svg(theme):
    c = THEMES[theme]
    fs, cw, pad = 16, 9.6, 34                     # font size, approx monospace char width, padding
    rows = [r for r in CARD if isinstance(r, tuple)]
    cols = max(len(k) + 1 + 3 + len(v) for k, v in rows)   # "key:" + gap + value, never overlapping
    width = int(pad * 2 + cols * cw)
    y, body = pad + 12, []
    for r in CARD:
        if r is None:
            y += 12
            continue
        if isinstance(r, str):
            if body:
                y += 6
            tw = len(r) * cw
            body.append(f'<text x="{pad}" y="{y}" fill="{c["text"]}" font-weight="700">{escape(r)}</text>')
            body.append(f'<line x1="{pad + tw + 12:.0f}" y1="{y - 5}" x2="{width - pad}" y2="{y - 5}" stroke="{c["cc"]}" stroke-dasharray="4 4"/>')
        else:
            k, v = r
            body.append(f'<text x="{pad}" y="{y}" fill="{c["key"]}">{escape(k)}:</text>')
            body.append(f'<text x="{width - pad}" y="{y}" fill="{c["value"]}" text-anchor="end">{escape(v)}</text>')
        y += 24
    height = y + pad - 18
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,\'Courier New\',monospace" font-size="{fs}px">',
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="14" fill="{c["bg"]}" stroke="{c["border"]}"/>',
        *body,
        "</svg>",
    ])


def main():
    for theme in THEMES:
        (ROOT / f"card-{theme}.svg").write_text(svg(theme))


if __name__ == "__main__":
    main()
