"""Render a year of GitHub contributions as an animated night-city skyline SVG.

The real contribution grid sits on the waterfront; directly above each week's
column stands a building whose height and lit windows follow that week's total.

Usage:
  GITHUB_TOKEN=... python scripts/skyline.py <user> <out_dir>
  python scripts/skyline.py <user> <out_dir> --demo   # random data, no network
"""
import datetime
import json
import math
import os
import random
import sys
import urllib.request

CELL, GAP = 12, 4             # grid cell and gap; building width = CELL + 2
PITCH = CELL + GAP
LEFT = 44                     # room for weekday labels
W = LEFT + 53 * PITCH + 20
GROUND = 200                  # y of the waterline
GRID_Y = GROUND + 24          # top of the contribution grid
H = GRID_Y + 7 * PITCH + 30
MIN_H, MAX_H = 10, 130
LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
MONO = "ui-monospace,SFMono-Regular,Menlo,monospace"

PALETTES = {
    "dark": dict(sky1="#0b1026", sky2="#2b1d4e", sky3="#4a2a5e", star="#ffffff",
                 moon="#f4f1c9", bld1="#141a33", bld2="#1d2547", win="#ffd166",
                 win2="#7ae7ff", water="#0a0f22", sub="#8b949e",
                 grass=["#161b2e", "#0e4429", "#006d32", "#26a641", "#39d353"]),
    "light": dict(sky1="#2d3a8c", sky2="#e86f8a", sky3="#ffb86b", star="#fff6e0",
                  moon="#fff3d6", bld1="#2b2346", bld2="#3d2f5c", win="#ffe08a",
                  win2="#ffc2d1", water="#3a2f63", sub="#ffe7d1",
                  grass=["#4a3f75", "#216e39", "#30a14e", "#40c463", "#9be9a8"]),
}

QUERY = """query($login:String!){user(login:$login){contributionsCollection{
contributionCalendar{totalContributions weeks{contributionDays{
contributionCount contributionLevel date weekday}}}}
repositories(first:100,ownerAffiliations:OWNER,isFork:false){nodes{
languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}}}"""


def fetch(user):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        u = json.load(r)["data"]["user"]
    cal = u["contributionsCollection"]["contributionCalendar"]
    langs = {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            n = e["node"]
            size, _ = langs.get(n["name"], (0, None))
            langs[n["name"]] = (size + e["size"], n["color"] or "#8b949e")
    weeks = [[(d["contributionCount"], LEVELS.index(d["contributionLevel"]), d["weekday"], d["date"])
              for d in w["contributionDays"]] for w in cal["weeks"]]
    return cal["totalContributions"], weeks[-53:], langs


def demo():
    rnd = random.Random(1)
    start = datetime.date(2025, 11, 30)
    weeks = []
    for i in range(53):
        days = []
        for wd in range(7 if i < 52 else 6):
            c = max(0, int(rnd.gauss(3, 4) * (1 + math.sin(i / 6))))
            lv = 0 if c == 0 else min(4, 1 + c // 4)
            days.append((c, lv, wd, str(start + datetime.timedelta(i * 7 + wd))))
        weeks.append(days)
    langs = {"Python": (500, "#3572A5"), "Jupyter Notebook": (300, "#DA5B0B"),
             "JavaScript": (120, "#f1e05a"), "HTML": (60, "#e34c26"), "C#": (30, "#178600")}
    return sum(d[0] for w in weeks for d in w), weeks, langs


def render(user, total, weeks, p):
    rnd = random.Random(user)  # stable layout between runs
    sums = [sum(d[0] for d in w) for w in weeks]
    peak = max(max(sums), 1)
    best = sums.index(peak)
    out = []
    a = out.append

    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    a(f"""<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
 <stop offset="0" stop-color="{p['sky1']}"/><stop offset=".7" stop-color="{p['sky2']}"/>
 <stop offset="1" stop-color="{p['sky3']}"/></linearGradient>
<linearGradient id="bld" x1="0" y1="0" x2="0" y2="1">
 <stop offset="0" stop-color="{p['bld2']}"/><stop offset="1" stop-color="{p['bld1']}"/></linearGradient>
<linearGradient id="beam" x1="0" y1="1" x2="0" y2="0">
 <stop offset="0" stop-color="{p['grass'][4]}" stop-opacity=".5"/>
 <stop offset="1" stop-color="{p['grass'][4]}" stop-opacity="0"/></linearGradient>
<radialGradient id="glow"><stop offset="0" stop-color="{p['moon']}" stop-opacity=".5"/>
 <stop offset="1" stop-color="{p['moon']}" stop-opacity="0"/></radialGradient>
<clipPath id="frame"><rect width="{W}" height="{H}" rx="12"/></clipPath>
</defs>
<style>
.tw{{animation:tw 3s ease-in-out infinite alternate}}
@keyframes tw{{from{{opacity:.15}}to{{opacity:1}}}}
.c{{opacity:0;transform-box:fill-box;transform-origin:center;transform:scale(.3);animation:pop .35s ease-out forwards}}
@keyframes pop{{to{{opacity:1;transform:scale(1)}}}}
.b{{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(0);animation:up .9s cubic-bezier(.2,.9,.3,1.2) forwards}}
@keyframes up{{to{{transform:scaleY(1)}}}}
.w{{opacity:0;animation:on .4s forwards}}
@keyframes on{{to{{opacity:1}}}}
.f{{animation:on .4s forwards,fl 5s steps(1) infinite}}
@keyframes fl{{0%,100%{{opacity:1}}40%{{opacity:.2}}55%{{opacity:1}}}}
.beacon{{animation:bc 1.4s ease-in-out infinite}}
@keyframes bc{{0%,100%{{opacity:.2}}50%{{opacity:1}}}}
.scan{{opacity:0;animation:scan 14s linear 5s infinite}}
@keyframes scan{{0%{{opacity:0;transform:translateX(0)}}3%{{opacity:1}}60%{{opacity:1}}63%,100%{{opacity:0;transform:translateX({52 * PITCH}px)}}}}
.today{{animation:td 1.6s ease-in-out infinite}}
@keyframes td{{0%,100%{{stroke-opacity:.15}}50%{{stroke-opacity:1}}}}
.shoot{{animation:sh 9s linear infinite;opacity:0}}
@keyframes sh{{0%{{transform:translate(0,0);opacity:0}}2%{{opacity:1}}10%{{transform:translate(-260px,110px);opacity:0}}100%{{opacity:0}}}}
.late{{opacity:0;animation:on .6s 3.6s forwards}}
</style>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="url(#sky)"/>""")

    # stars, moon, shooting star
    for _ in range(90):
        x, y = rnd.uniform(0, W), rnd.uniform(0, GROUND - 70)
        a(f'<circle class="tw" cx="{x:.1f}" cy="{y:.1f}" r="{rnd.choice([0.5, 0.7, 0.9, 1.2])}" '
          f'fill="{p["star"]}" style="animation-delay:{rnd.uniform(0, 3):.2f}s;'
          f'animation-duration:{rnd.uniform(2, 5):.1f}s"/>')
    a(f'<circle cx="{W - 70}" cy="48" r="44" fill="url(#glow)"/>'
      f'<circle cx="{W - 70}" cy="48" r="17" fill="{p["moon"]}"/>'
      f'<circle cx="{W - 63}" cy="43" r="15" fill="{p["sky1"]}" opacity=".9"/>')
    a(f'<g class="shoot" style="animation-delay:4s"><line x1="{W - 200}" y1="20" x2="{W - 160}" y2="4" '
      f'stroke="{p["star"]}" stroke-width="1.5" stroke-linecap="round"/></g>')

    # water
    a(f'<rect x="0" y="{GROUND}" width="{W}" height="{H - GROUND}" fill="{p["water"]}"/>')

    # buildings: one per week, standing right above that week's grid column
    for i, s in enumerate(sums):
        x = LEFT + i * PITCH - 1
        bw = CELL + 2
        h = round((MIN_H + (MAX_H - MIN_H) * math.sqrt(s / peak)) / 5) * 5
        top = GROUND - h
        delay = i * 0.045 + 0.35   # rises just after its grass column lights up
        a(f'<g class="b" style="animation-delay:{delay:.2f}s">'
          f'<rect x="{x}" y="{top}" width="{bw}" height="{h}" fill="url(#bld)"/>')
        if i % 7 == 3 and h > 40:
            a(f'<rect x="{x + 4}" y="{top - 5}" width="6" height="5" fill="{p["bld2"]}"/>')
        lit = 0.06 + 0.6 * math.sqrt(s / peak)
        for wy in range(top + 5, GROUND - 4, 5):
            for wx in (x + 2, x + 6, x + 10):
                if rnd.random() < lit:
                    col = p["win2"] if rnd.random() < 0.12 else p["win"]
                    d = delay + 0.9 + rnd.uniform(0, 1.6)
                    if rnd.random() < 0.06:
                        style = f"animation-delay:{d:.2f}s,{d + rnd.uniform(0, 5):.2f}s"
                        cls = "f"
                    else:
                        style, cls = f"animation-delay:{d:.2f}s", "w"
                    a(f'<rect class="{cls}" x="{wx}" y="{wy}" width="2" height="2" fill="{col}" style="{style}"/>')
        if i == best:
            cx = x + bw / 2
            a(f'<line x1="{cx}" y1="{top}" x2="{cx}" y2="{top - 16}" stroke="{p["bld2"]}" stroke-width="1.5"/>'
              f'<circle class="beacon" cx="{cx}" cy="{top - 17}" r="2.2" fill="#ff4d4d"/>')
        a('</g>')

    # peak label
    bx = LEFT + best * PITCH + CELL / 2
    ptop = GROUND - round(MAX_H / 5) * 5
    anchor = "end" if bx > W - 160 else "start"
    a(f'<text class="late" x="{bx - 8 if anchor == "end" else bx + 8}" y="{ptop - 20}" text-anchor="{anchor}" '
      f'font-size="10" font-family="{MONO}" fill="{p["sub"]}">peak week · {peak}</text>')

    # waterline
    a(f'<rect x="0" y="{GROUND}" width="{W}" height="1.5" fill="{p["win"]}" opacity=".35"/>')

    # month labels
    prev = None
    for i, w in enumerate(weeks):
        m = int(w[0][3][5:7])
        first_cut = i == 0 and int(weeks[2][0][3][5:7]) != m  # avoid overlapping labels
        if m != prev and i < 51 and not first_cut:
            name = datetime.date(2000, m, 1).strftime("%b")
            a(f'<text x="{LEFT + i * PITCH}" y="{GRID_Y - 8}" font-size="9" font-family="{MONO}" '
              f'fill="{p["sub"]}">{name}</text>')
        prev = m
    for wd, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        a(f'<text x="{LEFT - 8}" y="{GRID_Y + wd * PITCH + CELL - 2}" text-anchor="end" font-size="9" '
          f'font-family="{MONO}" fill="{p["sub"]}">{name}</text>')

    # contribution grid (the real "grass")
    for i, w in enumerate(weeks):
        for c, lv, wd, date in w:
            x, y = LEFT + i * PITCH, GRID_Y + wd * PITCH
            a(f'<rect class="c" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
              f'fill="{p["grass"][lv]}" style="animation-delay:{i * 0.045 + wd * 0.02:.2f}s">'
              f'<title>{date}: {c}</title></rect>')
    # today's cell pulses
    c, lv, wd, _ = weeks[-1][-1]
    a(f'<rect class="today" x="{LEFT + 52 * PITCH - 1.5}" y="{GRID_Y + wd * PITCH - 1.5}" '
      f'width="{CELL + 3}" height="{CELL + 3}" rx="3.5" fill="none" stroke="{p["grass"][4]}" stroke-width="1.2"/>')

    # a light beam that sweeps the weeks, linking each grass column to its building
    a(f'<g class="scan"><rect x="{LEFT - 1}" y="{GROUND - MAX_H}" width="{CELL + 2}" '
      f'height="{GRID_Y + 7 * PITCH - (GROUND - MAX_H)}" fill="url(#beam)" opacity=".35"/>'
      f'<rect x="{LEFT - 2}" y="{GRID_Y - 2}" width="{CELL + 4}" height="{7 * PITCH}" rx="3" '
      f'fill="none" stroke="{p["grass"][4]}" stroke-opacity=".7"/></g>')

    # footer: total + legend
    fy = H - 10
    a(f'<text class="late" x="{LEFT}" y="{fy}" font-size="10" font-family="{MONO}" fill="{p["sub"]}">'
      f'{total:,} contributions in the last year</text>')
    lx = LEFT + 53 * PITCH - GAP - 5 * (CELL - 2 + 3) - 30
    a(f'<g class="late"><text x="{lx - 6}" y="{fy}" text-anchor="end" font-size="10" '
      f'font-family="{MONO}" fill="{p["sub"]}">Less</text>')
    for k in range(5):
        a(f'<rect x="{lx + k * (CELL + 1)}" y="{fy - 9}" width="{CELL - 2}" height="{CELL - 2}" rx="2" '
          f'fill="{p["grass"][k]}"/>')
    a(f'<text x="{lx + 5 * (CELL + 1) + 3}" y="{fy}" font-size="10" font-family="{MONO}" '
      f'fill="{p["sub"]}">More</text></g>')
    a('</g></svg>')
    return "\n".join(out)


def render_stats(total, weeks, langs, p):
    days = [d for w in weeks for d in w]
    longest = run = 0
    for c, *_ in days:
        run = run + 1 if c else 0
        longest = max(longest, run)
    current = 0
    for c, *_ in reversed(days[:-1] if days[-1][0] == 0 else days):  # today may still be empty
        if not c:
            break
        current += 1
    best = max(days, key=lambda d: d[0])
    best_date = datetime.date.fromisoformat(best[3]).strftime("%b %-d")

    h = 128
    stats = [(f"{total:,}", "contributions"), (f"{current}d", "current streak"),
             (f"{longest}d", "longest streak"), (str(best[0]), f"best day · {best_date}")]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}">',
           f"""<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="{p['sky1']}"/><stop offset="1" stop-color="{p['sky2']}"/></linearGradient>
<clipPath id="bar"><rect x="{LEFT}" y="96" width="{W - 2 * LEFT}" height="6" rx="3"/></clipPath></defs>
<style>.in{{opacity:0;animation:in .6s ease-out forwards}}
@keyframes in{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
.grow{{transform-box:fill-box;transform:scaleX(0);animation:grow 1.2s .5s cubic-bezier(.2,.8,.2,1) forwards}}
@keyframes grow{{to{{transform:scaleX(1)}}}}</style>
<rect width="{W}" height="{h}" rx="12" fill="url(#bg)"/>"""]
    a = out.append
    col = (W - 2 * LEFT) / 4
    for k, (num, label) in enumerate(stats):
        x = LEFT + k * col
        a(f'<g class="in" style="animation-delay:{k * 0.12:.2f}s">'
          f'<text x="{x}" y="46" font-size="26" font-weight="700" '
          f'font-family="ui-sans-serif,-apple-system,Segoe UI,Helvetica,Arial,sans-serif" fill="{p["star"]}">{num}</text>'
          f'<text x="{x}" y="64" font-size="10" font-family="{MONO}" fill="{p["sub"]}">{label}</text></g>')
        if k:
            a(f'<rect x="{x - 16}" y="26" width="1" height="40" fill="{p["sub"]}" opacity=".25"/>')

    top = sorted(langs.items(), key=lambda kv: -kv[1][0])[:5]
    whole = sum(v[0] for v in langs.values()) or 1
    bar_w, x = W - 2 * LEFT, LEFT
    a('<g clip-path="url(#bar)"><g class="grow">')
    a(f'<rect x="{LEFT}" y="96" width="{bar_w}" height="6" fill="{p["sub"]}" opacity=".3"/>')
    for name, (size, color) in top:
        w = bar_w * size / whole
        a(f'<rect x="{x:.1f}" y="96" width="{w:.1f}" height="6" fill="{color}"/>')
        x += w
    a('</g></g>')
    lx = LEFT
    for k, (name, (size, color)) in enumerate(top):
        label = f"{name} {100 * size / whole:.0f}%"
        a(f'<g class="in" style="animation-delay:{1.2 + k * 0.1:.2f}s">'
          f'<circle cx="{lx + 4}" cy="{86 - 3.5}" r="3.5" fill="{color}"/>'
          f'<text x="{lx + 12}" y="86" font-size="10" font-family="{MONO}" fill="{p["sub"]}">{label}</text></g>')
        lx += 12 + len(label) * 6.1 + 18
    a('</svg>')
    return "\n".join(out)


def main():
    user, out_dir = sys.argv[1], sys.argv[2]
    total, weeks, langs = demo() if "--demo" in sys.argv else fetch(user)
    os.makedirs(out_dir, exist_ok=True)
    for name, pal in PALETTES.items():
        with open(os.path.join(out_dir, f"skyline-{name}.svg"), "w") as f:
            f.write(render(user, total, weeks, pal))
        with open(os.path.join(out_dir, f"stats-{name}.svg"), "w") as f:
            f.write(render_stats(total, weeks, langs, pal))


if __name__ == "__main__":
    main()
