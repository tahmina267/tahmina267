"""Builds dark_mode.svg and light_mode.svg, the profile card: a sky with one star per day of
the last year (brighter on busier days), next to a neofetch-style info panel.

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
                 cc="#616e7f", art="#c9d1d9", add="#3fb950", border="#30363d",
                 sky="#0b1026", star="#e8eeff", glow="#9db4ff", moon="#f3ead7"),
    "light": dict(bg="#f6f8fa", text="#24292f", key="#953800", value="#0a3069",
                  cc="#8c959f", art="#24292f", add="#1a7f37", border="#d0d7de",
                 sky="#1b2350", star="#f4f6ff", glow="#b9c8ff", moon="#f7efdc"),
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


def contributions():
    """Daily contribution counts for the past year (GraphQL, needs a token)."""
    q = {"query": 'query{user(login:"%s"){contributionsCollection{contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}' % USER}
    try:
        weeks = api("graphql", q)["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        return [d["contributionCount"] for w in weeks for d in w["contributionDays"]]
    except Exception:
        return [0] * 365


def sky(c, counts, x0, y0, w, h):
    """One star per day of the last year. Brighter for busier days; the busiest twinkle."""
    import random
    rnd = random.Random(267)  # fixed seed: each day keeps its place in the sky
    top = max(counts) or 1
    out = [f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="10" fill="{c["sky"]}"/>']
    # crescent moon
    mx, my = x0 + w - 52, y0 + 48
    out.append(f'<circle cx="{mx}" cy="{my}" r="17" fill="{c["moon"]}"/>')
    out.append(f'<circle cx="{mx + 7}" cy="{my - 5}" r="15" fill="{c["sky"]}"/>')
    stars, path = [], []
    for i, n in enumerate(counts):
        x = x0 + 14 + rnd.random() * (w - 28)
        y = y0 + 14 + rnd.random() * (h - 40)
        if (x - mx) ** 2 + (y - my) ** 2 < 30 ** 2:
            continue
        if n:
            path.append((x, y))
        if n == 0:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="0.7" fill="{c["star"]}" opacity="0.28"/>')
            continue
        t = n / top
        r = 1.1 + 2.2 * t
        if t > 0.45:  # bright day: a glow, a four-point sparkle, and a slow twinkle
            dur = 2.5 + rnd.random() * 3
            out.append(f'<g opacity="0.95"><animate attributeName="opacity" values="0.95;0.45;0.95" dur="{dur:.1f}s" repeatCount="indefinite"/>'
                       f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * 3:.1f}" fill="{c["glow"]}" opacity="0.18"/>'
                       f'<path d="M{x:.1f} {y - r * 2.6:.1f}L{x + r * 0.45:.1f} {y:.1f}L{x:.1f} {y + r * 2.6:.1f}L{x - r * 0.45:.1f} {y:.1f}Z'
                       f'M{x - r * 2.6:.1f} {y:.1f}L{x:.1f} {y + r * 0.45:.1f}L{x + r * 2.6:.1f} {y:.1f}L{x:.1f} {y - r * 0.45:.1f}Z" fill="{c["star"]}"/></g>')
        else:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{c["star"]}" opacity="{0.55 + 0.45 * t:.2f}"/>')
    # the active days, joined in date order: the year draws its own constellation
    if len(path) > 1:
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in path)
        out.insert(3, f'<path d="{d}" fill="none" stroke="{c["glow"]}" stroke-width="0.8" stroke-opacity="0.35" stroke-dasharray="2 3"/>')
    active = sum(1 for n in counts if n)
    out.append(f'<text x="{x0 + 14}" y="{y0 + h - 14}" font-size="12px" fill="{c["cc"]}">your year in stars · {active} bright days</text>')
    return out


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


def svg(theme, info, counts):
    c = THEMES[theme]
    lh, fs, cw = 20, 16, 9.6  # line height, font size, approx char width
    sky_w = 380
    x_info = 30 + sky_w + 30
    height = len(info) * lh + 50
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
    ]
    out += sky(c, counts, 24, 24, sky_w, height - 48)
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
    info = lines(stats(), datetime.date.today())
    counts = contributions()
    for theme in THEMES:
        (ROOT / f"{theme}_mode.svg").write_text(svg(theme, info, counts))


if __name__ == "__main__":
    main()
