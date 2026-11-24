"""Run-level python-docx helpers that preserve the manuscript's styles.
Markup in new text: _{sub}  ^{sup}  **bold**  //italic//"""
import re, copy
import docx
from docx.oxml.ns import qn
from docx.shared import Emu
from docx.text.paragraph import Paragraph
from docx.table import Table

XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
MARK = re.compile(r"_\{([^}]*)\}|\^\{([^}]*)\}|\*\*([^*]*)\*\*|//([^/]*)//")

def base_rpr(p):
    for r in p._p.iter(qn("w:r")):
        if r.find(qn("w:t")) is None:
            continue
        rp = r.find(qn("w:rPr"))
        rp = copy.deepcopy(rp) if rp is not None else None
        if rp is not None:
            for tag in ("w:vertAlign", "w:b", "w:bCs", "w:i", "w:iCs"):
                for e in rp.findall(qn(tag)):
                    rp.remove(e)
        return rp
    return None

def add_run(p_el, text, rpr, sub=False, sup=False, bold=False, ital=False):
    r = p_el.makeelement(qn("w:r"), {})
    rp = copy.deepcopy(rpr) if rpr is not None else r.makeelement(qn("w:rPr"), {})
    if bold: rp.append(rp.makeelement(qn("w:b"), {}))
    if ital: rp.append(rp.makeelement(qn("w:i"), {}))
    if sub or sup:
        rp.append(rp.makeelement(qn("w:vertAlign"), {qn("w:val"): "subscript" if sub else "superscript"}))
    if len(rp): r.append(rp)
    t = r.makeelement(qn("w:t"), {}); t.text = text; t.set(XML_SPACE, "preserve"); r.append(t)
    p_el.append(r)

def set_text(p, markup, allow_math=False, rpr=None):
    if not allow_math:
        assert not p._p.findall(".//{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath"), "paragraph holds OMML"
    rpr = base_rpr(p) if rpr is None else rpr
    for ch in list(p._p):
        if ch.tag != qn("w:pPr"):
            p._p.remove(ch)
    pos = 0
    for m in MARK.finditer(markup):
        if m.start() > pos: add_run(p._p, markup[pos:m.start()], rpr)
        if m.group(1) is not None: add_run(p._p, m.group(1), rpr, sub=True)
        elif m.group(2) is not None: add_run(p._p, m.group(2), rpr, sup=True)
        elif m.group(3) is not None: add_run(p._p, m.group(3), rpr, bold=True)
        else: add_run(p._p, m.group(4), rpr, ital=True)
        pos = m.end()
    if pos < len(markup): add_run(p._p, markup[pos:], rpr)
    return p

def replace_in(p, old, new, count=1):
    """Replace text across runs; replacement keeps the format of the first run touched."""
    for _ in range(count):
        runs = [t for t in p._p.iter(qn("w:t"))]
        full = "".join(t.text or "" for t in runs)
        i = full.find(old)
        assert i >= 0, (old, full[:150])
        j = i + len(old); pos = 0; done = False
        for t in runs:
            s = t.text or ""; a, b = pos, pos + len(s); pos = b
            if b <= i or a >= j: continue
            lo, hi = max(i, a) - a, min(j, b) - a
            t.text = (s[:lo] + new + s[hi:]) if not done else (s[:lo] + s[hi:]); done = True
            t.set(XML_SPACE, "preserve")

def para_after(anchor_el, template_p, markup, style=None):
    el = copy.deepcopy(template_p._p)
    anchor_el.addnext(el)
    p = Paragraph(el, template_p._parent)
    for ch in list(el):
        if ch.tag != qn("w:pPr"): el.remove(ch)
    if style is not None: p.style = style
    set_text(p, markup, rpr=base_rpr(template_p))
    return p

def delete(el):
    el.getparent().remove(el)

def move_before(target_el, els):
    for e in els:
        target_el.addprevious(e)

def tbl_end(tbl):
    return tbl._tbl

def set_widths(tbl, widths_in):
    tp = tbl._tbl.tblPr
    for e in tp.findall(qn("w:tblW")) + tp.findall(qn("w:tblLayout")) + tp.findall(qn("w:tblInd")) + tp.findall(qn("w:jc")):
        tp.remove(e)
    tw = tp.makeelement(qn("w:tblW"), {qn("w:w"): str(int(sum(widths_in) * 1440)), qn("w:type"): "dxa"})
    style = tp.find(qn("w:tblStyle"))
    (style.addnext(tw) if style is not None else tp.insert(0, tw))
    tw.addnext(tp.makeelement(qn("w:jc"), {qn("w:val"): "center"}))
    tp.append(tp.makeelement(qn("w:tblLayout"), {qn("w:type"): "fixed"}))
    grid = tbl._tbl.find(qn("w:tblGrid"))
    for gc in list(grid): grid.remove(gc)
    for w in widths_in: grid.append(grid.makeelement(qn("w:gridCol"), {qn("w:w"): str(int(w * 1440))}))
    for tr in tbl._tbl.findall(qn("w:tr")):
        tcs = tr.findall(qn("w:tc"))
        if len(tcs) == len(widths_in):
            for tc, w in zip(tcs, widths_in):
                tcpr = tc.find(qn("w:tcPr")); tcw = tcpr.find(qn("w:tcW")) if tcpr is not None else None
                if tcw is not None: tcw.set(qn("w:w"), str(int(w * 1440))); tcw.set(qn("w:type"), "dxa")

def _fit_cells(tr, n):
    tcs = tr.findall(qn("w:tc"))
    while len(tcs) < n:
        tcs[-1].addnext(copy.deepcopy(tcs[-1])); tcs = tr.findall(qn("w:tc"))
    while len(tcs) > n:
        tr.remove(tcs[-1]); tcs = tr.findall(qn("w:tc"))
    return tcs

def _cell_text(tc, parent, markup):
    ps = tc.findall(qn("w:p"))
    for extra in ps[1:]: tc.remove(extra)
    set_text(Paragraph(ps[0], parent), markup)

def make_table(template, rows, widths_in, anchor_el, note=None, note_template_tr=None):
    """Copy template table (header row 0, body row 1, last row for the bottom border); fill rows (first row = header)."""
    t = copy.deepcopy(template._tbl)
    trs = [tr for tr in t.findall(qn("w:tr"))]
    has_note = note_template_tr is not None
    hdr, body = trs[0], trs[1]
    last = trs[-2] if (len(trs) > 2 and _is_note(trs[-1])) else trs[-1]
    for tr in trs: t.remove(tr)
    n = len(rows[0]); tbl = Table(t, template._parent)
    new = []
    for i, r in enumerate(rows):
        src = hdr if i == 0 else (last if i == len(rows) - 1 else body)
        tr = copy.deepcopy(src); tcs = _fit_cells(tr, n)
        for tc, v in zip(tcs, r): _cell_text(tc, tbl, v)
        t.append(tr); new.append(tr)
    if note is not None and note_template_tr is not None:
        tr = copy.deepcopy(note_template_tr); tcs = tr.findall(qn("w:tc"))
        for e in tcs[0].iter(qn("w:gridSpan")): e.set(qn("w:val"), str(n))
        for extra in tcs[1:]: tr.remove(extra)
        _cell_text(tcs[0], tbl, note); t.append(tr)
    anchor_el.addnext(t)
    set_widths(tbl, widths_in)
    return tbl

def _is_note(tr):
    return tr.find(".//" + qn("w:gridSpan")) is not None

def figure_after(anchor_el, template_fig_p, png, width_emu):
    el = copy.deepcopy(template_fig_p._p); anchor_el.addnext(el)
    p = Paragraph(el, template_fig_p._parent)
    for ch in list(el):
        if ch.tag != qn("w:pPr"): el.remove(ch)
    p.add_run().add_picture(png, width=Emu(width_emu))
    return p

def swap_image(fig_p, png, width_emu=None):
    from PIL import Image
    blip = fig_p._p.find(".//" + qn("a:blip")); rid = blip.get(qn("r:embed"))
    part = fig_p.part.related_parts[rid]; part._blob = open(png, "rb").read()
    ext = fig_p._p.find(".//" + qn("wp:extent")); w, h = Image.open(png).size
    cx = int(width_emu) if width_emu else int(ext.get("cx")); cy = int(cx * h / w)
    ext.set("cx", str(cx)); ext.set("cy", str(cy))
    for e in fig_p._p.iter(qn("a:ext")):
        e.set("cx", str(cx)); e.set("cy", str(cy))

ROMAN = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
def to_roman(n):
    s = ""
    for v, r in ROMAN:
        while n >= v: s += r; n -= v
    return s
def from_roman(s):
    m = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}; v = 0
    for a, b in zip(s, s[1:] + " "):
        v += -m[a] if b != " " and m[a] < m[b] else m[a]
    return v

def renumber(doc, tmap, fmap):
    """One regex pass over every w:t: 'Table <roman>' and 'Fig. <n>' mapped old->new simultaneously."""
    pat = re.compile(r"\b(Table|Fig\.)([  ]+)([IVXLC]+|\d+)\b")
    def rep(m):
        kind, sp, num = m.groups()
        if kind == "Table" and num.isalpha(): return f"{kind}{sp}{to_roman(tmap.get(from_roman(num), from_roman(num)))}"
        if kind == "Fig." and num.isdigit(): return f"{kind}{sp}{fmap.get(int(num), int(num))}"
        return m.group(0)
    body = doc.element.body
    for t in body.iter(qn("w:t")):
        if t.text and ("Table" in t.text or "Fig." in t.text):
            t.text = pat.sub(rep, t.text)
