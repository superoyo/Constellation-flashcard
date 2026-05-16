#!/usr/bin/env python3
"""Generate printable, double-sided cut-out flashcards for all 88 IAU
constellations. Front of each card = star-dot diagram; back = the name."""
import json
import math
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

# IAU abbreviation -> full name (88 constellations)
NAMES = {
    "And": "Andromeda", "Ant": "Antlia", "Aps": "Apus", "Aqr": "Aquarius",
    "Aql": "Aquila", "Ara": "Ara", "Ari": "Aries", "Aur": "Auriga",
    "Boo": "Bootes", "Cae": "Caelum", "Cam": "Camelopardalis", "Cnc": "Cancer",
    "CVn": "Canes Venatici", "CMa": "Canis Major", "CMi": "Canis Minor",
    "Cap": "Capricornus", "Car": "Carina", "Cas": "Cassiopeia",
    "Cen": "Centaurus", "Cep": "Cepheus", "Cet": "Cetus", "Cha": "Chamaeleon",
    "Cir": "Circinus", "Col": "Columba", "Com": "Coma Berenices",
    "CrA": "Corona Australis", "CrB": "Corona Borealis", "Crv": "Corvus",
    "Crt": "Crater", "Cru": "Crux", "Cyg": "Cygnus", "Del": "Delphinus",
    "Dor": "Dorado", "Dra": "Draco", "Equ": "Equuleus", "Eri": "Eridanus",
    "For": "Fornax", "Gem": "Gemini", "Gru": "Grus", "Her": "Hercules",
    "Hor": "Horologium", "Hya": "Hydra", "Hyi": "Hydrus", "Ind": "Indus",
    "Lac": "Lacerta", "Leo": "Leo", "LMi": "Leo Minor", "Lep": "Lepus",
    "Lib": "Libra", "Lup": "Lupus", "Lyn": "Lynx", "Lyr": "Lyra",
    "Men": "Mensa", "Mic": "Microscopium", "Mon": "Monoceros", "Mus": "Musca",
    "Nor": "Norma", "Oct": "Octans", "Oph": "Ophiuchus", "Ori": "Orion",
    "Pav": "Pavo", "Peg": "Pegasus", "Per": "Perseus", "Phe": "Phoenix",
    "Pic": "Pictor", "Psc": "Pisces", "PsA": "Piscis Austrinus",
    "Pup": "Puppis", "Pyx": "Pyxis", "Ret": "Reticulum", "Sge": "Sagitta",
    "Sgr": "Sagittarius", "Sco": "Scorpius", "Scl": "Sculptor", "Sct": "Scutum",
    "Ser": "Serpens", "Sex": "Sextans", "Tau": "Taurus", "Tel": "Telescopium",
    "Tri": "Triangulum", "TrA": "Triangulum Australe", "Tuc": "Tucana",
    "UMa": "Ursa Major", "UMi": "Ursa Minor", "Vel": "Vela", "Vir": "Virgo",
    "Vol": "Volans", "Vul": "Vulpecula",
}

with open("lines.json") as fh:
    data = json.load(fh)

# Merge features by id (Serpens appears twice -> one constellation).
segs_by_id = {}
for feat in data["features"]:
    cid = feat["id"]
    segs_by_id.setdefault(cid, []).extend(feat["geometry"]["coordinates"])

constellations = sorted(segs_by_id.keys(), key=lambda c: NAMES[c])
assert len(constellations) == 88, len(constellations)


def unwrap(segments):
    """Unwrap RA so a constellation crossing the 0/360 line stays contiguous."""
    ref = segments[0][0][0]
    out = []
    for seg in segments:
        pts = []
        for ra, dec in seg:
            while ra - ref > 180:
                ra -= 360
            while ra - ref < -180:
                ra += 360
            pts.append((ra, dec))
        out.append(pts)
    return out


def draw_diagram(c, segs, x0, y0, w, h):
    """Draw a star-dot diagram fitted into the box (x0, y0, w, h)."""
    segs = unwrap(segs)
    pts = [p for seg in segs for p in seg]
    mean_dec = sum(d for _, d in pts) / len(pts)
    k = math.cos(math.radians(mean_dec))
    # Sky view: RA increases to the left.
    proj = [[(-ra * k, dec) for ra, dec in seg] for seg in segs]
    xs = [p[0] for seg in proj for p in seg]
    ys = [p[1] for seg in proj for p in seg]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    spanx = (maxx - minx) or 1.0
    spany = (maxy - miny) or 1.0
    pad = 0.16
    scale = min(w * (1 - 2 * pad) / spanx, h * (1 - 2 * pad) / spany)
    cx = x0 + w / 2
    cy = y0 + h / 2
    mx = (minx + maxx) / 2
    my = (miny + maxy) / 2

    def tx(px, py):
        return (cx + (px - mx) * scale, cy + (py - my) * scale)

    c.setStrokeColorRGB(0.55, 0.6, 0.78)
    c.setLineWidth(0.8)
    for seg in proj:
        path = c.beginPath()
        sx, sy = tx(*seg[0])
        path.moveTo(sx, sy)
        for px, py in seg[1:]:
            path.lineTo(*tx(px, py))
        c.drawPath(path)

    c.setFillColorRGB(0.04, 0.05, 0.13)
    seen = set()
    for px, py in [p for seg in proj for p in seg]:
        key = (round(px, 4), round(py, 4))
        if key in seen:
            continue
        seen.add(key)
        gx, gy = tx(px, py)
        c.circle(gx, gy, 2.1, stroke=0, fill=1)


PAGE_W, PAGE_H = letter
COLS, ROWS = 2, 3
PER_PAGE = COLS * ROWS
MARGIN = 12 * mm
CARD_W = (PAGE_W - 2 * MARGIN) / COLS
CARD_H = (PAGE_H - 2 * MARGIN) / ROWS


def card_box(col, row):
    x = MARGIN + col * CARD_W
    y = PAGE_H - MARGIN - (row + 1) * CARD_H
    return x, y, CARD_W, CARD_H


def cut_border(c, x, y, w, h):
    c.setStrokeColorRGB(0.78, 0.78, 0.78)
    c.setLineWidth(0.5)
    c.setDash(2, 2)
    c.rect(x, y, w, h, stroke=1, fill=0)
    c.setDash()


c = canvas.Canvas("constellation_flashcards.pdf", pagesize=letter)
pages = [constellations[i:i + PER_PAGE]
         for i in range(0, len(constellations), PER_PAGE)]

for group in pages:
    # FRONT: star diagrams
    for idx, cid in enumerate(group):
        col, row = idx % COLS, idx // COLS
        x, y, w, h = card_box(col, row)
        cut_border(c, x, y, w, h)
        draw_diagram(c, segs_by_id[cid], x, y, w, h)
        c.setFont("Helvetica-Oblique", 7)
        c.setFillColorRGB(0.6, 0.6, 0.6)
        c.drawCentredString(x + w / 2, y + 6, "What constellation is this?")
    c.showPage()

    # BACK: names, columns mirrored for long-edge duplex printing
    for idx, cid in enumerate(group):
        col, row = idx % COLS, idx // COLS
        bcol = COLS - 1 - col
        x, y, w, h = card_box(bcol, row)
        cut_border(c, x, y, w, h)
        c.setFillColorRGB(0.04, 0.05, 0.13)
        name = NAMES[cid]
        size = 30 if len(name) <= 11 else (22 if len(name) <= 16 else 17)
        c.setFont("Helvetica-Bold", size)
        c.drawCentredString(x + w / 2, y + h / 2 + 4, name)
        c.setFont("Helvetica", 11)
        c.setFillColorRGB(0.45, 0.45, 0.5)
        c.drawCentredString(x + w / 2, y + h / 2 - 18, f"({cid})")
    c.showPage()

c.save()
print("Wrote constellation_flashcards.pdf  ("
      f"{len(constellations)} cards, {len(pages) * 2} pages)")
