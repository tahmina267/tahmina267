"""Builds dark_mode.svg and light_mode.svg, the neofetch-style card on the profile README.

Run locally with `python generate.py` (set GH_TOKEN for higher API limits).
The GitHub Action in .github/workflows/build.yml runs it daily to refresh the stats.
"""
import datetime
import json
import os
import urllib.request
from html import escape
from pathlib import Path

USER = "tahmina267"
JOINED = datetime.date(2021, 6, 9)  # GitHub account created
ROOT = Path(__file__).parent
WIDTH = 60  # characters in each info line

THEMES = {
    "dark": dict(bg="#161b22", text="#c9d1d9", key="#ffa657", value="#a5d6ff",
                 cc="#616e7f", art="#c9d1d9", add="#3fb950", border="#30363d"),
    "light": dict(bg="#f6f8fa", text="#24292f", key="#953800", value="#0a3069",
                  cc="#c2cfde", art="#24292f", add="#1a7f37", border="#d0d7de"),
}


def api(path, body=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USER}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(f"https://api.github.com/{path}", data, headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def stats():
    user = api(f"users/{USER}")
    repos = api(f"users/{USER}/repos?per_page=100&type=owner")
    commits = api(f"search/commits?q=author:{USER}&per_page=1")["total_count"]
    contributed = len({e["repo"]["name"] for e in api(f"users/{USER}/events/public?per_page=100")})
    return dict(
        repos=user["public_repos"],
        contributed=max(contributed, user["public_repos"]),
        stars=sum(r["stargazers_count"] for r in repos),
        followers=user["followers"],
        commits=commits,
    )


def uptime(today):
    years = today.year - JOINED.year
    months = today.month - JOINED.month
    days = today.day - JOINED.day
    if days < 0:
        months -= 1
        prev = today.replace(day=1) - datetime.timedelta(days=1)
        days += prev.day
    if months < 0:
        years -= 1
        months += 12
    plural = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    return f"{plural(years, 'year')}, {plural(months, 'month')}, {plural(days, 'day')}"


def row(key, value):
    """One `key: .... value` line; returns a list of (text, css class) spans."""
    dots = WIDTH - len(key) - 1 - len(value) - 2
    return [(key, "key"), (":", ""), (" " + "." * max(dots, 1) + " ", "cc"), (value, "value")]


def header(title):
    return [(title, ""), (" " + "-" * (WIDTH - len(title) - 1), "cc")]


def lines(s, today):
    return [
        header("tahmina@sultana"),
        row("OS", "macOS, Linux, Windows"),
        row("Uptime", uptime(today)),
        row("Host", "Makebell Limited"),
        row("Kernel", "SQA Engineer & Project Manager"),
        row("IDE", "VSCode, Claude Code, Figma"),
        row("Education", "B.Sc. CSE, North South University"),
        [],
        row("Languages.Programming", "Python, JavaScript, SQL, C++"),
        row("Languages.Computer", "HTML, CSS, JSON, Markdown, YAML"),
        row("Languages.Real", "Bengali, English"),
        [],
        row("Hobbies.Software", "AI agents, UI/UX, RAG systems"),
        row("Hobbies.Hardware", "Arduino, sensors"),
        [],
        header("Contact"),
        row("Email.Personal", "tahminasultana2609@gmail.com"),
        row("LinkedIn", "tahmina-sultana-188051247"),
        row("Portfolio", "portfolio-tahmina5.vercel.app"),
        [],
        header("GitHub Stats"),
        stat_line(
            [("Repos", f"{s['repos']}"), ("Contributed", f"{s['contributed']}"), ("Stars", f"{s['stars']}")]
        ),
        stat_line([("Commits", f"{s['commits']:,}"), ("Followers", f"{s['followers']}")]),
    ]


def stat_line(pairs):
    spans = []
    for i, (k, v) in enumerate(pairs):
        if i:
            spans.append((" | ", ""))
        spans += [(k, "key"), (": ", ""), (v, "value")]
    return spans


def svg(theme, art, info):
    c = THEMES[theme]
    lh, fs, cw = 20, 16, 9.6  # line height, font size, approx char width
    art_w = max(len(l) for l in art) * cw
    x_info = 30 + art_w + 30
    height = max(len(art), len(info)) * lh + 50
    width = int(x_info + WIDTH * cw + 30)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" font-family="ConsolasFallback,Consolas,\'Courier New\',monospace" '
        f'width="{width}px" height="{height}px" font-size="{fs}px">',
        "<style>",
        "@font-face{src:local('Consolas'),local('Consolas Bold');font-family:'ConsolasFallback';"
        "font-display:swap;-webkit-size-adjust:109%;size-adjust:109%;}",
        f".key{{fill:{c['key']};}}.value{{fill:{c['value']};}}.cc{{fill:{c['cc']};}}",
        "text,tspan{white-space:pre;}",
        "</style>",
        f'<rect width="{width}px" height="{height}px" fill="{c["bg"]}" rx="15" stroke="{c["border"]}"/>',
        f'<text x="30" y="40" fill="{c["art"]}" class="ascii">',
    ]
    for i, l in enumerate(art):
        out.append(f'<tspan x="30" y="{40 + i * lh}">{escape(l)}</tspan>')
    out.append("</text>")
    out.append(f'<text x="{x_info:.0f}" y="40" fill="{c["text"]}">')
    for i, spans in enumerate(info):
        y = 40 + i * lh
        parts = "".join(
            f'<tspan class="{cls}">{escape(t)}</tspan>' if cls else escape(t) for t, cls in spans
        )
        out.append(f'<tspan x="{x_info:.0f}" y="{y}">{parts}</tspan>')
    out.append("</text>")
    out.append("</svg>")
    return "\n".join(out)


def main():
    art = (ROOT / "ascii.txt").read_text().rstrip("\n").split("\n")
    info = lines(stats(), datetime.date.today())
    for theme in THEMES:
        (ROOT / f"{theme}_mode.svg").write_text(svg(theme, art, info))


if __name__ == "__main__":
    main()
