#!/usr/bin/env python3
import argparse
import math
import random
import re
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

SKIP = {"defs", "clipPath", "mask", "pattern", "filter", "marker", "symbol", "linearGradient", "radialGradient", "style", "title", "desc"}
NUM = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
TOK = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
ARGS = {"m": 2, "l": 2, "h": 1, "v": 1, "c": 6, "s": 4, "q": 4, "t": 2, "a": 7, "z": 0}


def tag(el):
    return el.tag.split("}")[-1]


def fnum(v, default=0.0):
    if v is None:
        return default
    m = NUM.search(str(v))
    return float(m.group()) if m else default


def style_get(el, key):
    st = el.get("style", "")
    m = re.search(rf"(?:^|;)\s*{key}\s*:\s*([^;]+)", st)
    return m.group(1).strip() if m else el.get(key)


def fmt(x):
    return f"{x:.2f}".rstrip("0").rstrip(".")


class Rougher:
    def __init__(self, amp, rng, filter_id, box):
        self.amp = amp
        self.rng = rng
        self.filter_id = filter_id
        self.box = box

    def j(self, scale=1.0):
        return self.rng.gauss(0, self.amp * scale)

    def jx(self, x, scale):
        x0, _, w, _ = self.box
        d = self.j(scale)
        if x <= x0 + 1:
            return x - abs(d) - 1
        if x >= x0 + w - 1:
            return x + abs(d) + 1
        return x + d

    def jy(self, y, scale):
        _, y0, _, h = self.box
        d = self.j(scale)
        if y <= y0 + 1:
            return y - abs(d) - 1
        if y >= y0 + h - 1:
            return y + abs(d) + 1
        return y + d

    def wobble(self, pts, closed):
        out = []
        seq = pts + ([pts[0]] if closed else [])
        for (x0, y0), (x1, y1) in zip(seq, seq[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / (self.amp * 18 + 1e-6)))
            for k in range(n):
                t = k / n
                out.append((self.jx(x0 + (x1 - x0) * t, 0.6), self.jy(y0 + (y1 - y0) * t, 0.6)))
        if not closed:
            ex, ey = seq[-1]
            out.append((self.jx(ex, 0.6), self.jy(ey, 0.6)))
        d = "M" + " L".join(f"{fmt(x)},{fmt(y)}" for x, y in out)
        return d + ("Z" if closed else "")

    def to_path(self, el, d):
        keep = {k: v for k, v in el.attrib.items() if k not in {"x", "y", "width", "height", "x1", "y1", "x2", "y2", "points", "cx", "cy", "r", "rx", "ry"}}
        el.clear()
        el.tag = f"{{{SVG_NS}}}path"
        for k, v in keep.items():
            el.set(k, v)
        el.set("d", d)

    def shift(self, el):
        dx, dy = self.j(0.8), self.j(0.8)
        tr = el.get("transform", "")
        el.set("transform", f"translate({fmt(dx)},{fmt(dy)}) {tr}".strip())

    def line(self, el):
        p = [(fnum(el.get("x1")), fnum(el.get("y1"))), (fnum(el.get("x2")), fnum(el.get("y2")))]
        self.to_path(el, self.wobble(p, False))
        self.shift(el)

    def rect(self, el):
        if fnum(el.get("rx")) or fnum(el.get("ry")):
            return
        x, y, w, h = (fnum(el.get(k)) for k in ("x", "y", "width", "height"))
        if w <= 0 or h <= 0 or str(el.get("width", "")).endswith("%"):
            return
        if w >= 0.9 * self.box[2] and h >= 0.9 * self.box[3]:
            return
        self.to_path(el, self.wobble([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], True))

    def poly(self, el, closed):
        nums = [float(n) for n in NUM.findall(el.get("points", ""))]
        pts = list(zip(nums[0::2], nums[1::2]))
        if len(pts) >= 2:
            self.to_path(el, self.wobble(pts, closed))

    def ellipse(self, el):
        cx, cy = fnum(el.get("cx")), fnum(el.get("cy"))
        if tag(el) == "circle":
            rx = ry = fnum(el.get("r"))
        else:
            rx, ry = fnum(el.get("rx")), fnum(el.get("ry"))
        if rx <= 0 or ry <= 0:
            return
        n = max(12, int(2 * math.pi * max(rx, ry) / (self.amp * 10 + 1e-6)))
        n = min(n, 160)
        drift = self.rng.uniform(0, math.tau)
        pts = []
        for k in range(n):
            a = math.tau * k / n
            r = 1 + 0.5 * self.j(1 / max(rx, ry)) + 0.015 * math.sin(3 * a + drift)
            pts.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
        d = "M" + " L".join(f"{fmt(x)},{fmt(y)}" for x, y in pts) + "Z"
        small = max(rx, ry) < self.amp * 6
        self.to_path(el, d)
        if small:
            self.shift(el)

    def path(self, el):
        toks = TOK.findall(el.get("d", ""))
        out, cmd, i, argi = [], None, 0, 0
        while i < len(toks):
            t = toks[i]
            if t.isalpha():
                cmd, argi = t, 0
                out.append(t)
                i += 1
                continue
            v = float(t)
            if cmd is None:
                out.append(t)
            else:
                c = cmd.lower()
                n = ARGS.get(c, 2) or 1
                pos = argi % n
                rel = cmd.islower()
                if c == "a" and pos < 5:
                    out.append(t)
                elif rel:
                    out.append(fmt(v + self.j(0.35)))
                elif c == "h" or (c != "v" and (pos % 2 == 0 if c != "a" else pos == 5)):
                    out.append(fmt(self.jx(v, 0.6)))
                else:
                    out.append(fmt(self.jy(v, 0.6)))
                argi += 1
            i += 1
        el.set("d", " ".join(out))

    def text(self, el, size):
        chars = "".join(el.itertext())
        if not chars or list(el):
            return
        k = 0.25 if size < 16 else (0.6 if size < 32 else 1.0)
        n = len(chars)
        rot = [fmt(self.rng.gauss(0, 2.2 * k)) for _ in range(n)]
        offs = [self.rng.gauss(0, self.amp * 0.5 * k) for _ in range(n)]
        dys = [offs[0]] + [offs[i] - offs[i - 1] for i in range(1, n)]
        if not el.get("rotate"):
            el.set("rotate", " ".join(rot))
        if not el.get("dy"):
            el.set("dy", " ".join(fmt(d) for d in dys))
        if size >= 28 and not el.get("filter"):
            el.set("filter", f"url(#{self.filter_id})")

    def walk(self, el, size):
        fs = style_get(el, "font-size")
        if fs:
            size = fnum(fs, size)
        for child in list(el):
            t = tag(child)
            if t in SKIP:
                continue
            if t == "text":
                cs = style_get(child, "font-size")
                self.text(child, fnum(cs, size) if cs else size)
                continue
            if t == "line":
                self.line(child)
            elif t == "rect":
                self.rect(child)
            elif t == "polyline":
                self.poly(child, False)
            elif t == "polygon":
                self.poly(child, True)
            elif t in ("circle", "ellipse"):
                self.ellipse(child)
            elif t == "path":
                self.path(child)
            self.walk(child, size)


def add_filter(root, fid, amp, seed):
    defs = next((c for c in root if tag(c) == "defs"), None)
    if defs is None:
        defs = ET.Element(f"{{{SVG_NS}}}defs")
        root.insert(0, defs)
    f = ET.SubElement(defs, f"{{{SVG_NS}}}filter", {"id": fid, "x": "-5%", "y": "-5%", "width": "110%", "height": "110%"})
    ET.SubElement(f, f"{{{SVG_NS}}}feTurbulence", {"type": "fractalNoise", "baseFrequency": "0.9", "numOctaves": "2", "seed": str(seed), "result": "n"})
    ET.SubElement(f, f"{{{SVG_NS}}}feDisplacementMap", {"in": "SourceGraphic", "in2": "n", "scale": fmt(amp * 2.2), "xChannelSelector": "R", "yChannelSelector": "G"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--amount", type=float, default=1.0)
    ap.add_argument("--seed", type=int)
    args = ap.parse_args()
    rng = random.Random(args.seed) if args.seed is not None else random.SystemRandom()
    tree = ET.parse(args.src)
    root = tree.getroot()
    vb = [float(n) for n in NUM.findall(root.get("viewBox", ""))]
    box = vb if len(vb) == 4 else [0.0, 0.0, fnum(root.get("width"), 600), fnum(root.get("height"), 600)]
    w, h = box[2], box[3]
    amp = args.amount * math.hypot(w, h) / 720 * 1.4
    fid = "rough-edge"
    add_filter(root, fid, amp, rng.randint(1, 9999))
    Rougher(amp, rng, fid, box).walk(root, 16.0)
    tree.write(args.dst, encoding="unicode", xml_declaration=False)
    print(f"wrote {args.dst} (amp {amp:.2f})")


if __name__ == "__main__":
    main()
