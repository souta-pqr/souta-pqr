"""Render a year of GitHub contributions as an animated night-city skyline SVG.

Each week becomes a building: taller and brighter the more you committed.

Usage:
  GITHUB_TOKEN=... python scripts/skyline.py <user> <out_dir>
  python scripts/skyline.py <user> <out_dir> --demo   # random data, no network
"""
import json
import math
import os
import random
import sys
import urllib.request

W, H = 880, 300
GROUND = 220          # y of the street / water line
BW, GAP = 14, 2       # building width and gap
LEFT = (W - 53 * (BW + GAP) + GAP) // 2
MIN_H, MAX_H = 12, 135

PALETTES = {
    "dark": dict(sky1="#0b1026", sky2="#2b1d4e", sky3="#4a2a5e", star="#ffffff",
                 moon="#f4f1c9", bld1="#141a33", bld2="#1d2547", win="#ffd166",
                 win2="#7ae7ff", water="#0a0f22", text="#c9d1d9", sub="#8b949e"),
    "light": dict(sky1="#2d3a8c", sky2="#e86f8a", sky3="#ffb86b", star="#fff6e0",
                  moon="#fff3d6", bld1="#2b2346", bld2="#3d2f5c", win="#ffe08a",
                  win2="#ffc2d1", water="#3a2f63", text="#ffffff", sub="#ffe7d1"),
}

QUERY = """query($login:String!){user(login:$login){contributionsCollection{
contributionCalendar{totalContributions weeks{contributionDays{contributionCount date}}}}}}"""


def fetch(user):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        cal = json.load(r)["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [[d["contributionCount"] for d in w["contributionDays"]] for w in cal["weeks"]]
    return cal["totalContributions"], weeks[-53:]


def demo():
    rnd = random.Random(1)
    weeks = [[max(0, int(rnd.gauss(3, 4) * (1 + math.sin(i / 6)))) for _ in range(7)]
             for i in range(53)]
    return sum(map(sum, weeks)), weeks


def render(user, total, weeks, p):
    rnd = random.Random(user)  # stable layout between runs
    sums = [sum(w) for w in weeks]
    peak = max(max(sums), 1)
    best = sums.index(peak)
    out = []
    a = out.append

    a(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
      f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    a(f"""<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
 <stop offset="0" stop-color="{p['sky1']}"/><stop offset=".7" stop-color="{p['sky2']}"/>
 <stop offset="1" stop-color="{p['sky3']}"/></linearGradient>
<linearGradient id="bld" x1="0" y1="0" x2="0" y2="1">
 <stop offset="0" stop-color="{p['bld2']}"/><stop offset="1" stop-color="{p['bld1']}"/></linearGradient>
<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
 <stop offset="0" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<mask id="reflect"><rect x="0" y="{GROUND}" width="{W}" height="{H - GROUND}" fill="url(#fade)"/></mask>
<radialGradient id="glow"><stop offset="0" stop-color="{p['moon']}" stop-opacity=".5"/>
 <stop offset="1" stop-color="{p['moon']}" stop-opacity="0"/></radialGradient>
<clipPath id="frame"><rect width="{W}" height="{H}" rx="12"/></clipPath>
</defs>
<style>
.tw{{animation:tw 3s ease-in-out infinite alternate}}
@keyframes tw{{from{{opacity:.15}}to{{opacity:1}}}}
.b{{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(0);animation:up .9s cubic-bezier(.2,.9,.3,1.2) forwards}}
@keyframes up{{to{{transform:scaleY(1)}}}}
.w{{opacity:0;animation:on .4s forwards}}
@keyframes on{{to{{opacity:1}}}}
.f{{animation:on .4s forwards,fl 5s steps(1) infinite}}
@keyframes fl{{0%,100%{{opacity:1}}40%{{opacity:.2}}55%{{opacity:1}}}}
.beacon{{animation:bc 1.4s ease-in-out infinite}}
@keyframes bc{{0%,100%{{opacity:.2}}50%{{opacity:1}}}}
.shoot{{animation:sh 9s linear infinite;opacity:0}}
@keyframes sh{{0%{{transform:translate(0,0);opacity:0}}2%{{opacity:1}}10%{{transform:translate(-260px,110px);opacity:0}}100%{{opacity:0}}}}
.wave{{animation:wv 6s ease-in-out infinite alternate}}
@keyframes wv{{to{{transform:translateX(18px)}}}}
.label{{opacity:0;animation:on .6s 3.4s forwards}}
</style>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="url(#sky)"/>""")

    # stars
    for _ in range(90):
        x, y = rnd.uniform(0, W), rnd.uniform(0, GROUND - 60) ** 1.0
        r = rnd.choice([0.5, 0.7, 0.9, 1.2])
        a(f'<circle class="tw" cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{p["star"]}" '
          f'style="animation-delay:{rnd.uniform(0, 3):.2f}s;animation-duration:{rnd.uniform(2, 5):.1f}s"/>')

    # moon + shooting star
    a(f'<circle cx="{W - 90}" cy="58" r="46" fill="url(#glow)"/>'
      f'<circle cx="{W - 90}" cy="58" r="18" fill="{p["moon"]}"/>'
      f'<circle cx="{W - 83}" cy="53" r="16" fill="{p["sky1"]}" opacity=".9"/>')
    a(f'<g class="shoot" style="animation-delay:4s"><line x1="{W - 200}" y1="20" x2="{W - 160}" y2="4" '
      f'stroke="{p["star"]}" stroke-width="1.5" stroke-linecap="round"/></g>')

    # city
    a('<g id="city">')
    for i, s in enumerate(sums):
        x = LEFT + i * (BW + GAP)
        h = MIN_H + (MAX_H - MIN_H) * math.sqrt(s / peak)
        h = round(h / 5) * 5
        top = GROUND - h
        delay = i * 0.045
        a(f'<g class="b" style="animation-delay:{delay:.2f}s">'
          f'<rect x="{x}" y="{top}" width="{BW}" height="{h}" fill="url(#bld)"/>')
        if i % 7 == 3 and h > 40:  # rooftop water tank
            a(f'<rect x="{x + 4}" y="{top - 5}" width="6" height="5" fill="{p["bld2"]}"/>')
        lit = 0.1 + 0.7 * math.sqrt(s / peak)
        for row, wy in enumerate(range(int(top) + 5, GROUND - 4, 5)):
            for wx in (x + 2, x + 6, x + 10):
                if rnd.random() < lit:
                    col = p["win2"] if rnd.random() < 0.12 else p["win"]
                    cls = "f" if rnd.random() < 0.06 else "w"
                    d = delay + 0.9 + rnd.uniform(0, 1.6)
                    extra = f";animation-delay:{d:.2f}s,{d + rnd.uniform(0, 5):.2f}s" if cls == "f" \
                        else f";animation-delay:{d:.2f}s"
                    a(f'<rect class="{cls}" x="{wx}" y="{wy}" width="2" height="2" fill="{col}" style="{extra[1:]}"/>')
        if i == best:
            cx = x + BW / 2
            a(f'<line x1="{cx}" y1="{top}" x2="{cx}" y2="{top - 16}" stroke="{p["bld2"]}" stroke-width="1.5"/>'
              f'<circle class="beacon" cx="{cx}" cy="{top - 17}" r="2.2" fill="#ff4d4d"/>')
        a('</g>')
    a('</g>')

    # peak label
    bx = LEFT + best * (BW + GAP) + BW / 2
    btop = GROUND - round((MIN_H + (MAX_H - MIN_H)) / 5) * 5
    anchor = "end" if bx > W - 160 else "start"
    lx = bx - 6 if anchor == "end" else bx + 6
    a(f'<text class="label" x="{lx}" y="{btop - 20}" text-anchor="{anchor}" font-size="10" '
      f'font-family="ui-monospace,SFMono-Regular,Menlo,monospace" fill="{p["sub"]}">peak week · {peak}</text>')

    # water + reflection
    a(f'<rect x="0" y="{GROUND}" width="{W}" height="{H - GROUND}" fill="{p["water"]}"/>')
    a(f'<g mask="url(#reflect)"><use xlink:href="#city" href="#city" '
      f'transform="translate(0,{2 * GROUND}) scale(1,-1)" opacity=".6"/></g>')
    a(f'<rect x="0" y="{GROUND}" width="{W}" height="1.5" fill="{p["win"]}" opacity=".35"/>')
    for k in range(14):
        y = GROUND + 8 + k * 5.5
        x = rnd.uniform(-20, W - 80)
        a(f'<rect class="wave" x="{x:.0f}" y="{y:.0f}" width="{rnd.uniform(30, 90):.0f}" height="1" '
          f'fill="{p["star"]}" opacity=".12" style="animation-delay:-{rnd.uniform(0, 6):.1f}s"/>')

    # title
    a(f'<text x="24" y="34" font-size="18" font-weight="700" '
      f'font-family="ui-sans-serif,-apple-system,Segoe UI,Helvetica,Arial,sans-serif" fill="{p["text"]}">'
      f'{user}<tspan fill="{p["sub"]}" font-weight="400"> city</tspan></text>')
    a(f'<text x="24" y="54" font-size="11" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" '
      f'fill="{p["sub"]}">{total} contributions built in the last year</text>')
    a('</g></svg>')
    return "\n".join(out)


def main():
    user, out_dir = sys.argv[1], sys.argv[2]
    total, weeks = demo() if "--demo" in sys.argv else fetch(user)
    os.makedirs(out_dir, exist_ok=True)
    for name, pal in PALETTES.items():
        with open(os.path.join(out_dir, f"skyline-{name}.svg"), "w") as f:
            f.write(render(user, total, weeks, pal))


if __name__ == "__main__":
    main()
