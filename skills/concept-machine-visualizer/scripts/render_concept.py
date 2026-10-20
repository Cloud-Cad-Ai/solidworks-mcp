#!/usr/bin/env python3
"""
render_concept.py  --  concept.json  ->  single-file HTML concept sheet

Usage:
    python render_concept.py concept.json [-o concept_sheet.html] [--svg-dir views/]

Produces one self-contained HTML page (inline SVG, no external deps) with:
  * third-angle orthographic views (top / front / right) at a common scale,
    overall dimensions and the max-envelope constraint drawn dashed
  * an isometric view with BOM balloons and motion arrows
  * requirements, assumptions, concept decision matrix (weighted totals
    computed here), sizing table, BOM, risks, next steps

It also prints validation warnings (unlinked parts, envelope violation,
selected concept != best score, missing units ...). Exit code 0 even with
warnings; exit 1 only on unreadable input.

Coordinate system (mm):  +X = length (left->right in front view)
                         +Y = depth  (front -> back)
                         +Z = height (up)
Stdlib only.
"""
import argparse, html, json, math, os, sys

# ---------------------------------------------------------------- palette
GROUP_COLORS = {
    "frame":      "#8a96a3",
    "structure":  "#8a96a3",
    "drive":      "#d9822b",
    "motor":      "#d9822b",
    "transmission": "#c9a227",
    "motion":     "#3b82c4",
    "guide":      "#3b82c4",
    "tooling":    "#7c5cc4",
    "end_effector": "#7c5cc4",
    "payload":    "#3aa476",
    "workpiece":  "#3aa476",
    "electrical": "#c44b4b",
    "sensor":     "#c44b4b",
    "pneumatic":  "#2aa3a3",
    "hydraulic":  "#2aa3a3",
    "guarding":   "#b8c4cf",
    "other":      "#9aa0a6",
}
DEFAULT_COLOR = "#9aa0a6"


def color_of(p):
    return p.get("color") or GROUP_COLORS.get(str(p.get("group", "other")).lower(), DEFAULT_COLOR)


def shade(hex_color, f):
    """f<1 darker, f>1 lighter."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    if f <= 1:
        r, g, b = (int(c * f) for c in (r, g, b))
    else:
        t = f - 1
        r, g, b = (int(c + (255 - c) * t) for c in (r, g, b))
    return "#%02x%02x%02x" % (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


def esc(s):
    return html.escape(str(s), quote=True)


# ---------------------------------------------------------------- geometry
AX = {"x": 0, "y": 1, "z": 2}


def cyl_basis(axis):
    a = AX[axis]
    others = [i for i in range(3) if i != a]
    return a, others


def prim_faces(p, segs=28):
    """Return list of (polygon_points_3d, outward_normal) for a primitive."""
    t = p.get("type", "box")
    faces = []
    if t == "box":
        x, y, z = p["pos"]
        dx, dy, dz = p["size"]
        X0, X1, Y0, Y1, Z0, Z1 = x, x + dx, y, y + dy, z, z + dz
        faces = [
            ([(X0, Y0, Z0), (X1, Y0, Z0), (X1, Y0, Z1), (X0, Y0, Z1)], (0, -1, 0)),
            ([(X0, Y1, Z0), (X1, Y1, Z0), (X1, Y1, Z1), (X0, Y1, Z1)], (0, 1, 0)),
            ([(X0, Y0, Z0), (X0, Y1, Z0), (X0, Y1, Z1), (X0, Y0, Z1)], (-1, 0, 0)),
            ([(X1, Y0, Z0), (X1, Y1, Z0), (X1, Y1, Z1), (X1, Y0, Z1)], (1, 0, 0)),
            ([(X0, Y0, Z0), (X1, Y0, Z0), (X1, Y1, Z0), (X0, Y1, Z0)], (0, 0, -1)),
            ([(X0, Y0, Z1), (X1, Y0, Z1), (X1, Y1, Z1), (X0, Y1, Z1)], (0, 0, 1)),
        ]
    elif t in ("cyl", "cylinder"):
        a, (i, j) = cyl_basis(p.get("axis", "z"))
        c = list(p["pos"])          # centre of the base end
        r = p["r"]
        L = p["length"]
        ring0, ring1 = [], []
        for k in range(segs):
            th = 2 * math.pi * k / segs
            q = [0.0, 0.0, 0.0]
            q[a] = c[a]
            q[i] = c[i] + r * math.cos(th)
            q[j] = c[j] + r * math.sin(th)
            q1 = list(q)
            q1[a] = c[a] + L
            ring0.append(tuple(q))
            ring1.append(tuple(q1))
        for k in range(segs):
            k2 = (k + 1) % segs
            th = 2 * math.pi * (k + 0.5) / segs
            n = [0.0, 0.0, 0.0]
            n[i] = math.cos(th)
            n[j] = math.sin(th)
            faces.append(([ring0[k], ring0[k2], ring1[k2], ring1[k]], tuple(n)))
        n0 = [0.0, 0.0, 0.0]; n0[a] = -1
        n1 = [0.0, 0.0, 0.0]; n1[a] = 1
        faces.append((ring0, tuple(n0)))
        faces.append((ring1, tuple(n1)))
    return faces


def prim_bounds(p):
    t = p.get("type", "box")
    if t == "box":
        lo = list(p["pos"])
        hi = [lo[k] + p["size"][k] for k in range(3)]
        return lo, hi
    a, (i, j) = cyl_basis(p.get("axis", "z"))
    c = p["pos"]; r = p["r"]; L = p["length"]
    lo = [0, 0, 0]; hi = [0, 0, 0]
    lo[a], hi[a] = min(c[a], c[a] + L), max(c[a], c[a] + L)
    lo[i], hi[i] = c[i] - r, c[i] + r
    lo[j], hi[j] = c[j] - r, c[j] + r
    return lo, hi


def prim_center(p):
    lo, hi = prim_bounds(p)
    return [(lo[k] + hi[k]) / 2 for k in range(3)]


# ---------------------------------------------------------------- projections
S6, S2, S3 = math.sqrt(6), math.sqrt(2), math.sqrt(3)
ISO_D = (-1 / S3, 1 / S3, -1 / S3)   # view direction: from front-right-top into scene


def iso_proj(pt):
    x, y, z = pt
    return ((x + y) / S2, (x - y - 2 * z) / S6)


def iso_depth(pt):
    x, y, z = pt
    return (-x + y - z) / S3          # larger = further away


# Ortho views: (horizontal axis index, sign), (vertical-up axis index, sign), depth (axis, sign: larger value = nearer)
ORTHO = {
    "front": {"h": (0, 1), "v": (2, 1), "near": (1, -1), "look": 1},
    "top":   {"h": (0, 1), "v": (1, 1), "near": (2, 1), "look": 2},
    "right": {"h": (1, 1), "v": (2, 1), "near": (0, 1), "look": 0},
}


def ortho_rect(p, view):
    """Projected 2D shape of primitive in an ortho view -> ('rect', x0,y0,x1,y1) or ('circle', cx,cy,r) in model units (v up)."""
    cfg = ORTHO[view]
    hi_, hs = cfg["h"]; vi, vs = cfg["v"]
    t = p.get("type", "box")
    if t in ("cyl", "cylinder") and AX[p.get("axis", "z")] == cfg["look"]:
        c = p["pos"]
        return ("circle", hs * c[hi_], vs * c[vi], p["r"])
    lo, hi = prim_bounds(p)
    a0, a1 = sorted((hs * lo[hi_], hs * hi[hi_]))
    b0, b1 = sorted((vs * lo[vi], vs * hi[vi]))
    return ("rect", a0, b0, a1, b1)


def ortho_depth(p, view):
    ai, s = ORTHO[view]["near"]
    lo, hi = prim_bounds(p)
    return s * (hi[ai] if s > 0 else lo[ai])     # nearest face value, larger = nearer


def ortho_pt(pt, view):
    cfg = ORTHO[view]
    return (cfg["h"][1] * pt[cfg["h"][0]], cfg["v"][1] * pt[cfg["v"][0]])


# ---------------------------------------------------------------- SVG builders
def fmt(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")


def arrow_defs():
    return ('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            '<path d="M0,0 L10,5 L0,10 z" fill="var(--ink)"/></marker>'
            '<marker id="mh" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
            '<path d="M0,0 L10,5 L0,10 z" fill="var(--motion)"/></marker></defs>')


def svg_ortho(prims, view, scale, W, H, envelope=None, motions=()):
    """Return SVG string for one ortho view, fitted around content center at given scale (px per mm)."""
    shapes = [(ortho_depth(p, view), p, ortho_rect(p, view)) for p in prims]
    # bounds of drawing (model units)
    xs, ys = [], []
    for _, _, s in shapes:
        if s[0] == "rect":
            xs += [s[1], s[3]]; ys += [s[2], s[4]]
        else:
            xs += [s[1] - s[3], s[1] + s[3]]; ys += [s[2] - s[3], s[2] + s[3]]
    if not xs:
        return ""
    bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)
    if envelope:   # centre on geometry + envelope so a larger envelope stays in frame
        lo_e = list(envelope.get("origin", [0, 0, 0]))
        hi_e = [lo_e[k] + envelope["size"][k] for k in range(3)]
        ea, eb = ortho_pt(lo_e, view), ortho_pt(hi_e, view)
        xs += [ea[0], eb[0]]; ys += [ea[1], eb[1]]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2

    def T(u, v):
        return (W / 2 + (u - cx) * scale, H / 2 - (v - cy) * scale)

    out = ['<svg class="view" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg">' % (W, H), arrow_defs()]
    out.append('<text x="8" y="16" class="vlabel">%s VIEW</text>' % view.upper())
    for _, p, s in sorted(shapes, key=lambda q: q[0]):
        col = color_of(p)
        tip = esc(p.get("name", p.get("id", "")))
        if s[0] == "rect":
            x0, y0 = T(s[1], s[4]); x1, y1 = T(s[3], s[2])
            out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="%s" fill-opacity="0.85" stroke="var(--ink)" stroke-width="0.8"><title>%s</title></rect>'
                       % (fmt(x0), fmt(y0), fmt(max(x1 - x0, 0.6)), fmt(max(y1 - y0, 0.6)), col, tip))
        else:
            px, py = T(s[1], s[2])
            out.append('<circle cx="%s" cy="%s" r="%s" fill="%s" fill-opacity="0.85" stroke="var(--ink)" stroke-width="0.8"><title>%s</title></circle>'
                       % (fmt(px), fmt(py), fmt(max(s[3] * scale, 0.8)), col, tip))
            out.append('<path d="M%s %sh%sM%s %sv%s" stroke="var(--ink)" stroke-width="0.4" stroke-dasharray="4 2 1 2"/>' % (
                fmt(px - s[3] * scale - 4), fmt(py), fmt(2 * s[3] * scale + 8), fmt(px), fmt(py - s[3] * scale - 4), fmt(2 * s[3] * scale + 8)))
    # envelope
    if envelope:
        L, Wd, Hh = envelope["size"]
        lo = list(envelope.get("origin", [0, 0, 0])); hi = [lo[0] + L, lo[1] + Wd, lo[2] + Hh]
        a = ortho_pt(lo, view); b = ortho_pt(hi, view)
        x0, y0 = T(min(a[0], b[0]), max(a[1], b[1])); x1, y1 = T(max(a[0], b[0]), min(a[1], b[1]))
        out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="none" stroke="var(--env)" stroke-width="1" stroke-dasharray="6 4"/>'
                   % (fmt(x0), fmt(y0), fmt(x1 - x0), fmt(y1 - y0)))
    # motions
    for m in motions:
        if m.get("type", "linear") != "linear":
            continue
        a = ortho_pt(m["from"], view); b = ortho_pt(m["to"], view)
        if math.hypot(b[0] - a[0], b[1] - a[1]) * scale < 6:
            continue
        p0 = T(*a); p1 = T(*b)
        out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="var(--motion)" stroke-width="1.6" marker-start="url(#mh)" marker-end="url(#mh)"/>'
                   % (fmt(p0[0]), fmt(p0[1]), fmt(p1[0]), fmt(p1[1])))
    # overall dims
    X0, Y0 = T(bx0, by0); X1, Y1 = T(bx1, by1)   # Y0 is bottom (larger px)
    dy = Y0 + 18
    out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" class="dim" marker-start="url(#ah)" marker-end="url(#ah)"/>' % (fmt(X0), fmt(dy), fmt(X1), fmt(dy)))
    out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" class="ext"/><line x1="%s" y1="%s" x2="%s" y2="%s" class="ext"/>'
               % (fmt(X0), fmt(Y0 + 3), fmt(X0), fmt(dy + 4), fmt(X1), fmt(Y0 + 3), fmt(X1), fmt(dy + 4)))
    out.append('<text x="%s" y="%s" class="dimt" text-anchor="middle">%s</text>' % (fmt((X0 + X1) / 2), fmt(dy - 4), fmt(bx1 - bx0)))
    dx = X1 + 18
    out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" class="dim" marker-start="url(#ah)" marker-end="url(#ah)"/>' % (fmt(dx), fmt(Y0), fmt(dx), fmt(Y1)))
    out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" class="ext"/><line x1="%s" y1="%s" x2="%s" y2="%s" class="ext"/>'
               % (fmt(X1 + 3), fmt(Y0), fmt(dx + 4), fmt(Y0), fmt(X1 + 3), fmt(Y1), fmt(dx + 4), fmt(Y1)))
    out.append('<text x="%s" y="%s" class="dimt" text-anchor="middle" transform="rotate(-90 %s %s)">%s</text>'
               % (fmt(dx - 4), fmt((Y0 + Y1) / 2), fmt(dx - 4), fmt((Y0 + Y1) / 2), fmt(by1 - by0)))
    out.append("</svg>")
    return "\n".join(out)


def svg_iso(prims, W, H, motions=(), item_numbers=None):
    faces = []
    for p in prims:
        col = color_of(p)
        for poly, n in prim_faces(p):
            ndot = n[0] * ISO_D[0] + n[1] * ISO_D[1] + n[2] * ISO_D[2]
            if ndot >= -1e-9:
                continue                                      # back-face
            cen = [sum(q[k] for q in poly) / len(poly) for k in range(3)]
            # simple fixed-light shading: top lightest, front mid, right side darkest
            light = 0.92 + 0.28 * n[2] + 0.08 * (-n[1]) - 0.14 * n[0]
            light = max(0.6, min(1.3, light))
            faces.append((iso_depth(cen), poly, shade(col, light), p))
    if not faces:
        return ""
    pts2 = [iso_proj(q) for _, poly, _, _ in faces for q in poly]
    u0, u1 = min(a for a, _ in pts2), max(a for a, _ in pts2)
    v0, v1 = min(b for _, b in pts2), max(b for _, b in pts2)
    pad = 60
    sc = min((W - 2 * pad) / max(u1 - u0, 1), (H - 2 * pad) / max(v1 - v0, 1))
    ox = W / 2 - (u0 + u1) / 2 * sc
    oy = H / 2 - (v0 + v1) / 2 * sc

    def T(pt):
        u, v = iso_proj(pt)
        return (ox + u * sc, oy + v * sc)

    out = ['<svg class="view" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg">' % (W, H), arrow_defs()]
    out.append('<text x="8" y="16" class="vlabel">ISOMETRIC (not to scale)</text>')
    for _, poly, fill, p in sorted(faces, key=lambda f: -f[0]):
        d = " ".join("%s,%s" % (fmt(a), fmt(b)) for a, b in (T(q) for q in poly))
        sw = "0.6" if len(poly) == 4 and p.get("type", "box") != "box" else "0.8"
        stroke = fill if (len(poly) == 4 and p.get("type", "box") != "box") else "var(--ink)"
        out.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round"><title>%s</title></polygon>'
                   % (d, fill, stroke, sw, esc(p.get("name", p.get("id", "")))))
    for m in motions:
        if m.get("type", "linear") == "linear":
            a = T(m["from"]); b = T(m["to"])
            out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="var(--motion)" stroke-width="2" marker-start="url(#mh)" marker-end="url(#mh)"/>'
                       % (fmt(a[0]), fmt(a[1]), fmt(b[0]), fmt(b[1])))
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        else:  # rotary: arc of 270deg around axis
            c = m["center"]; r = m.get("r", 40)
            ai, (i, j) = cyl_basis(m.get("axis", "z"))
            ptsr = []
            for k in range(0, 28):
                th = math.radians(20 + 270 * k / 27)
                q = list(c); q[i] += r * math.cos(th); q[j] += r * math.sin(th)
                ptsr.append(T(q))
            d = "M" + " L".join("%s %s" % (fmt(a), fmt(b)) for a, b in ptsr)
            out.append('<path d="%s" fill="none" stroke="var(--motion)" stroke-width="2" marker-end="url(#mh)"/>' % d)
            mid = ptsr[0]
        if m.get("label"):
            out.append('<text x="%s" y="%s" class="mlabel">%s</text>' % (fmt(mid[0] + 6), fmt(mid[1] - 6), esc(m["label"])))
    # balloons
    if item_numbers:
        # one balloon per BOM item, anchored on its largest primitive, pushed radially
        # outward from the drawing centre with a leader line, nudged apart if crowded
        best = {}
        for p in prims:
            it = p.get("item")
            if it is None:
                continue
            lo, hi = prim_bounds(p)
            vol = (hi[0] - lo[0]) * (hi[1] - lo[1]) * (hi[2] - lo[2])
            if it not in best or vol > best[it][0]:
                best[it] = (vol, p)
        gx, gy = W / 2, H / 2
        placed = []
        for it, (_, p) in sorted(best.items(), key=lambda kv: str(kv[0])):
            ax_, ay_ = T(prim_center(p))
            dx, dy = ax_ - gx, ay_ - gy
            d = math.hypot(dx, dy) or 1.0
            ux, uy = dx / d, dy / d
            dist = 34
            for _ in range(40):
                bx, by = ax_ + ux * dist, ay_ + uy * dist
                bx = min(max(bx, 12), W - 12); by = min(max(by, 24), H - 12)
                if all(math.hypot(bx - qx, by - qy) >= 20 for qx, qy in placed):
                    break
                dist += 8
                ux, uy = ux * math.cos(0.35) - uy * math.sin(0.35), ux * math.sin(0.35) + uy * math.cos(0.35)
            placed.append((bx, by))
            out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="var(--ink)" stroke-width="0.6"/><circle cx="%s" cy="%s" r="1.8" fill="var(--ink)"/>'
                       % (fmt(ax_), fmt(ay_), fmt(bx), fmt(by), fmt(ax_), fmt(ay_)))
            out.append('<circle cx="%s" cy="%s" r="8.5" class="balloon"/><text x="%s" y="%s" class="btext" text-anchor="middle">%s</text>'
                       % (fmt(bx), fmt(by), fmt(bx), fmt(by + 3.5), esc(it)))
    out.append("</svg>")
    return "\n".join(out)


# ---------------------------------------------------------------- validation
def validate(c):
    w = []
    prims = c.get("geometry", [])
    bom = c.get("bom", [])
    bom_items = {str(b.get("item")) for b in bom}
    for p in prims:
        t = p.get("type", "box")
        if t == "box" and not ("pos" in p and "size" in p):
            w.append("geometry '%s': box needs pos and size" % p.get("id"))
        if t in ("cyl", "cylinder") and not all(k in p for k in ("pos", "r", "length")):
            w.append("geometry '%s': cylinder needs pos, r, length (+axis)" % p.get("id"))
        if p.get("item") is not None and str(p["item"]) not in bom_items:
            w.append("geometry '%s' references BOM item %s which is not in the BOM" % (p.get("id"), p["item"]))
        if p.get("item") is None:
            w.append("geometry '%s' has no BOM item link" % p.get("id"))
    used = {str(p.get("item")) for p in prims}
    for b in bom:
        if str(b.get("item")) not in used and not b.get("not_drawn"):
            w.append("BOM item %s (%s) is not drawn; set \"not_drawn\": true if intentional" % (b.get("item"), b.get("name")))
    # envelope
    env = c.get("envelope")
    if env and prims:
        lo = [min(prim_bounds(p)[0][k] for p in prims) for k in range(3)]
        hi = [max(prim_bounds(p)[1][k] for p in prims) for k in range(3)]
        o = env.get("origin", [0, 0, 0])
        for k, ax in enumerate("XYZ"):
            if lo[k] < o[k] - 1e-6 or hi[k] > o[k] + env["size"][k] + 1e-6:
                w.append("ENVELOPE VIOLATION along %s: geometry %s..%s mm, allowed %s..%s mm"
                         % (ax, fmt(lo[k]), fmt(hi[k]), fmt(o[k]), fmt(o[k] + env["size"][k])))
    # decision
    dm = c.get("decision")
    if dm:
        tot = decision_totals(dm)
        if tot:
            best = max(tot, key=tot.get)
            sel = c.get("selected_concept")
            if sel and sel != best:
                w.append("selected_concept '%s' is not the top weighted score ('%s'); justify in selection_rationale" % (sel, best))
            wsum = sum(cr.get("weight", 0) for cr in dm.get("criteria", []))
            if wsum and abs(wsum - 1) > 0.01 and abs(wsum - 100) > 0.5:
                w.append("decision weights sum to %s (expected 1.0 or 100)" % fmt(wsum))
    for s in c.get("sizing", []):
        if not s.get("result"):
            w.append("sizing row '%s' has no result" % s.get("item"))
    if not c.get("assumptions"):
        w.append("no assumptions listed -- every back-of-envelope number rests on some")
    return w


def decision_totals(dm):
    crit = dm.get("criteria", [])
    scores = dm.get("scores", {})
    tot = {}
    for concept, row in scores.items():
        tot[concept] = sum(cr.get("weight", 0) * row.get(cr["name"], 0) for cr in crit)
    return tot


# ---------------------------------------------------------------- HTML
CSS = """
:root{--bg:#f6f7f9;--paper:#ffffff;--ink:#1d2329;--muted:#5f6b76;--rule:#d5dbe1;--env:#c0392b;--motion:#1f6fd1;--accent:#0f5e9c;--good:#1e7f4f}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#14181c;--paper:#1c2127;--ink:#e5e9ee;--muted:#9aa5b1;--rule:#33404c;--env:#ff6b5b;--motion:#5aa9ff;--accent:#6cb4ff;--good:#4cc38a}}
:root[data-theme="dark"]{--bg:#14181c;--paper:#1c2127;--ink:#e5e9ee;--muted:#9aa5b1;--rule:#33404c;--env:#ff6b5b;--motion:#5aa9ff;--accent:#6cb4ff;--good:#4cc38a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.sheet{max-width:1280px;margin:0 auto;padding:16px}
header{display:flex;flex-wrap:wrap;gap:8px 24px;align-items:baseline;border-bottom:2px solid var(--ink);padding-bottom:8px;margin-bottom:14px}
header h1{font-size:22px;margin:0;letter-spacing:.2px}
header .meta{color:var(--muted);font-size:12.5px}
.summary{margin:0 0 14px;max-width:900px}
.views{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.cell{background:var(--paper);border:1px solid var(--rule);border-radius:6px;overflow:hidden}
.view{width:100%;height:auto;display:block}
.vlabel{font:600 11px ui-monospace,Menlo,Consolas,monospace;fill:var(--muted);letter-spacing:.6px}
.dim{stroke:var(--ink);stroke-width:.7}.ext{stroke:var(--ink);stroke-width:.4}
.dimt{font:11px ui-monospace,Menlo,Consolas,monospace;fill:var(--ink)}
.mlabel{font:600 11px ui-sans-serif,system-ui,sans-serif;fill:var(--motion);paint-order:stroke;stroke:var(--paper);stroke-width:3px}
.balloon{fill:var(--paper);stroke:var(--ink);stroke-width:1}
.btext{font:700 10px ui-sans-serif,system-ui,sans-serif;fill:var(--ink)}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:12px;color:var(--muted);margin:8px 0 18px}
.legend i{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:5px;vertical-align:-1px;border:1px solid var(--rule)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
section{background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:12px 14px;margin-bottom:14px;overflow-x:auto}
section h2{font-size:14px;text-transform:uppercase;letter-spacing:.8px;margin:0 0 8px;color:var(--accent)}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{text-align:left;padding:5px 7px;border-bottom:1px solid var(--rule);vertical-align:top}
th{font-weight:600;color:var(--muted);font-size:12px}
td.num{text-align:right;font-variant-numeric:tabular-nums}
tr.win td{background:color-mix(in srgb,var(--good) 14%,transparent);font-weight:600}
ul{margin:4px 0;padding-left:18px}
.warn{border-color:var(--env)}.warn h2{color:var(--env)}
code{font:12px ui-monospace,Menlo,Consolas,monospace}
.concepts{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px}
.concept{border:1px solid var(--rule);border-radius:6px;padding:10px}
.concept.sel{border:2px solid var(--good)}
.concept h3{margin:0 0 4px;font-size:14px}
.tag{font-size:11px;color:var(--good);font-weight:700;margin-left:6px}
@media (max-width:760px){.views,.grid2{grid-template-columns:1fr}.sheet{padding:16px}}
@media print{body{background:#fff}.sheet{max-width:none}section,.cell{break-inside:avoid}}
"""


def table(headers, rows, num_cols=(), row_class=None):
    h = "<table><thead><tr>%s</tr></thead><tbody>" % "".join(
        "<th%s>%s</th>" % (' style="text-align:right"' if ci in num_cols else "", esc(x)) for ci, x in enumerate(headers))
    for ri, r in enumerate(rows):
        cls = (' class="%s"' % row_class(ri)) if row_class and row_class(ri) else ""
        h += "<tr%s>%s</tr>" % (cls, "".join(
            '<td%s>%s</td>' % (' class="num"' if ci in num_cols else "", esc(v if v is not None else "")) for ci, v in enumerate(r)))
    return h + "</tbody></table>"


def build_html(c, warnings):
    prims = c.get("geometry", [])
    motions = c.get("motions", [])
    env = c.get("envelope")
    W, H = 600, 420
    # common ortho scale
    if prims:
        lo = [min(prim_bounds(p)[0][k] for p in prims) for k in range(3)]
        hi = [max(prim_bounds(p)[1][k] for p in prims) for k in range(3)]
        if env:
            eo = env.get("origin", [0, 0, 0])
            lo = [min(lo[k], eo[k]) for k in range(3)]
            hi = [max(hi[k], eo[k] + env["size"][k]) for k in range(3)]
        ext = [hi[k] - lo[k] for k in range(3)]
        margin = 70
        scale = min((W - margin) / max(ext[0], ext[1], 1), (H - margin) / max(ext[2], ext[1], 1),
                    (W - margin) / max(ext[0], 1), (H - margin) / max(ext[1], 1))
    else:
        scale = 1
    top = svg_ortho(prims, "top", scale, W, H, env, motions)
    front = svg_ortho(prims, "front", scale, W, H, env, motions)
    right = svg_ortho(prims, "right", scale, W, H, env, motions)
    iso = svg_iso(prims, W, H, motions, item_numbers=True)

    title = c.get("title", "Machine concept")
    meta = " · ".join(esc(x) for x in [c.get("concept_id", ""), "Rev " + str(c.get("rev", "A")), c.get("date", ""),
                                         c.get("author", ""), "Units: mm, kg, N, s" + (", " + c["units_note"] if c.get("units_note") else "")] if x)
    parts = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
             "<title>%s</title><style>%s</style></head><body><div class='sheet'>" % (esc(title), CSS),
             "<header><h1>%s</h1><span class='meta'>%s</span></header>" % (esc(title), meta)]
    if c.get("summary"):
        parts.append("<p class='summary'>%s</p>" % esc(c["summary"]))

    parts.append("<div class='views'><div class='cell'>%s</div><div class='cell'>%s</div><div class='cell'>%s</div><div class='cell'>%s</div></div>"
                 % (top, iso, front, right))
    groups = sorted({str(p.get("group", "other")).lower() for p in prims})
    parts.append("<div class='legend'>" + "".join("<span><i style='background:%s'></i>%s</span>" % (GROUP_COLORS.get(g, DEFAULT_COLOR), esc(g)) for g in groups)
                 + "<span><i style='background:var(--motion)'></i>motion / stroke</span>"
                 + ("<span><i style='background:transparent;border:1px dashed var(--env)'></i>max envelope %s</span>" % esc(" × ".join(fmt(v) for v in env["size"])) if env else "")
                 + "<span>Third-angle projection · ortho views share one scale</span></div>")

    if warnings:
        parts.append("<section class='warn'><h2>Validation flags</h2><ul>%s</ul></section>" % "".join("<li>%s</li>" % esc(w) for w in warnings))

    # requirements + assumptions
    req = c.get("requirements", [])
    rq_rows = [(r.get("id", ""), r.get("text", ""), r.get("value", ""), r.get("source", "spec")) for r in req]
    parts.append("<div class='grid2'><section><h2>Requirements</h2>%s</section><section><h2>Assumptions</h2><ul>%s</ul></section></div>"
                 % (table(["ID", "Requirement", "Target", "Source"], rq_rows),
                    "".join("<li>%s</li>" % esc(a) for a in c.get("assumptions", []))))

    # concepts + decision
    concepts = c.get("concepts", [])
    sel = c.get("selected_concept")
    if concepts:
        cards = ""
        for k in concepts:
            is_sel = k.get("name") == sel
            cards += "<div class='concept%s'><h3>%s%s</h3><p>%s</p>%s%s</div>" % (
                " sel" if is_sel else "", esc(k.get("name")), "<span class='tag'>SELECTED</span>" if is_sel else "",
                esc(k.get("description", "")),
                ("<b>+</b><ul>%s</ul>" % "".join("<li>%s</li>" % esc(x) for x in k.get("pros", []))) if k.get("pros") else "",
                ("<b>−</b><ul>%s</ul>" % "".join("<li>%s</li>" % esc(x) for x in k.get("cons", []))) if k.get("cons") else "")
        parts.append("<section><h2>Concept alternatives</h2><div class='concepts'>%s</div></section>" % cards)
    dm = c.get("decision")
    if dm and dm.get("criteria"):
        tot = decision_totals(dm)
        names = list(dm.get("scores", {}).keys())
        best = max(tot, key=tot.get) if tot else None
        hdr = ["Criterion", "Weight"] + names
        rows = [[cr["name"], fmt(cr.get("weight", 0))] + [fmt(dm["scores"][n].get(cr["name"], 0)) for n in names] for cr in dm["criteria"]]
        rows.append(["Weighted total", ""] + [fmt(tot[n]) for n in names])
        parts.append("<section><h2>Decision matrix (score 1–5)</h2>%s%s</section>" % (
            table(hdr, rows, num_cols=set(range(1, len(hdr))), row_class=lambda i: "win" if i == len(rows) - 1 else None),
            ("<p><b>Selected:</b> %s. %s</p>" % (esc(sel or best), esc(c.get("selection_rationale", "")))) ))

    if c.get("morphology"):
        mrows = [(m.get("function", ""), " | ".join(m.get("options", [])), m.get("chosen", "")) for m in c["morphology"]]
        parts.append("<section><h2>Function → solution (morphological chart)</h2>%s</section>" % table(["Function", "Options considered", "Chosen"], mrows))

    if c.get("sizing"):
        srows = [(s.get("item", ""), s.get("formula", ""), s.get("inputs", ""), s.get("result", ""), s.get("selection", ""), s.get("margin", "")) for s in c["sizing"]]
        parts.append("<section><h2>Back-of-envelope sizing</h2>%s</section>" % table(["Item", "Formula", "Inputs", "Result", "Selection", "Margin / SF"], srows))

    if c.get("bom"):
        brows = [(b.get("item", ""), b.get("name", ""), b.get("qty", 1), b.get("spec", ""), b.get("make_buy", ""), b.get("mass_kg", ""), b.get("notes", "")) for b in c["bom"]]
        mass = sum((b.get("mass_kg") or 0) * (b.get("qty") or 1) for b in c["bom"] if isinstance(b.get("mass_kg"), (int, float)))
        parts.append("<section><h2>Concept BOM</h2>%s%s</section>" % (
            table(["#", "Part", "Qty", "Spec / size", "Make/Buy", "kg ea", "Notes"], brows, num_cols={0, 2, 5}),
            ("<p>Estimated mass of listed items: <b>≈ %.0f kg</b></p>" % mass) if mass else ""))

    if c.get("interfaces"):
        irows = [(i.get("name", ""), i.get("type", ""), i.get("detail", "")) for i in c["interfaces"]]
        parts.append("<section><h2>Interfaces</h2>%s</section>" % table(["Interface", "Type", "Detail"], irows))

    tail = ""
    if c.get("risks"):
        tail += "<section><h2>Risks &amp; open questions</h2><ul>%s</ul></section>" % "".join(
            "<li>%s</li>" % esc(r if isinstance(r, str) else "%s — %s" % (r.get("risk", ""), r.get("mitigation", ""))) for r in c["risks"])
    if c.get("next_steps"):
        tail += "<section><h2>Next steps</h2><ul>%s</ul></section>" % "".join("<li>%s</li>" % esc(s) for s in c["next_steps"])
    if tail:
        parts.append("<div class='grid2'>%s</div>" % tail)
    parts.append("<p style='color:var(--muted);font-size:12px'>Concept-level geometry from primitives; not for manufacture. Source data: <code>%s</code></p>"
                 % esc(c.get("_source", "concept.json")))
    parts.append("</div></body></html>")
    return "\n".join(parts), {"top": top, "front": front, "right": right, "iso": iso}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("concept")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--svg-dir", default=None, help="also write each view as a standalone SVG")
    a = ap.parse_args()
    try:
        with open(a.concept, encoding="utf-8") as f:
            c = json.load(f)
    except Exception as e:
        print("ERROR reading %s: %s" % (a.concept, e), file=sys.stderr)
        sys.exit(1)
    c["_source"] = os.path.basename(a.concept)
    warnings = validate(c)
    page, views = build_html(c, warnings)
    out = a.out or os.path.splitext(a.concept)[0] + "_sheet.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    if a.svg_dir:
        os.makedirs(a.svg_dir, exist_ok=True)
        style = "<style>" + CSS.split("*{")[0].replace(":root", "svg") + ".vlabel{font:600 11px monospace;fill:#5f6b76}.dim{stroke:#1d2329;stroke-width:.7}.ext{stroke:#1d2329;stroke-width:.4}.dimt{font:11px monospace;fill:#1d2329}.mlabel{font:600 11px sans-serif;fill:#1f6fd1}.balloon{fill:#fff;stroke:#1d2329}.btext{font:700 10px sans-serif;fill:#1d2329}</style>"
        for k, v in views.items():
            if v:
                with open(os.path.join(a.svg_dir, "%s.svg" % k), "w", encoding="utf-8") as f:
                    f.write(v.replace("<defs>", style + "<defs>", 1))
    print("wrote", out)
    if warnings:
        print("\nVALIDATION FLAGS (%d):" % len(warnings))
        for w in warnings:
            print("  -", w)
    else:
        print("validation: clean")


if __name__ == "__main__":
    main()
