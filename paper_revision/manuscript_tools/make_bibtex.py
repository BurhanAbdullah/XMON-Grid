#!/usr/bin/env python3
"""BibTeX export of the final reference list of the revised manuscript (parsed from the docx, then normalized).
Usage: python make_bibtex.py <revised.docx> <out.bib>"""
import sys, re, docx
d = docx.Document(sys.argv[1])
refs = [p.text for p in d.paragraphs if p.style.name == "Bibliography"]
out = []
def key(authors, year, n):
    fam = re.split(r",| and ", authors)[0].strip().split()[-1] if authors else f"ref{n}"
    fam = re.sub(r"[^A-Za-z]", "", fam)
    return f"{fam}{year}_{n}"
for r in refs:
    m = re.match(r"\[(\d+)\]\s*\t?(.*)", r.strip()); n, body = int(m.group(1)), m.group(2).strip()
    year = (re.findall(r"\b(19\d{2}|20\d{2})\b", re.split(r"doi:", body)[0]) or [""])[-1]
    doi = (re.findall(r"doi:\s*(\S+?)\.?$", body) or [""])[0]
    t = re.search(r"“(.+?)[,.]?”", body)
    authors = body[:t.start()].strip().rstrip(",") if t else body.split(",")[0]
    authors = authors.replace(", et al.", " and others").replace(" et al.", " and others")
    authors = re.sub(r",\s*and\s+", " and ", authors); authors = re.sub(r",\s+(?=[A-Z]\.)", " and ", authors)
    f = {"author": authors, "year": year}
    if doi: f["doi"] = doi
    if t:
        f["title"] = "{" + t.group(1) + "}"; rest = body[t.end():].strip(" ,")
        if rest.startswith("in "):
            typ = "inproceedings"; f["booktitle"] = rest[3:].split(", 20")[0].split(", 19")[0]
        elif "arXiv" in rest:
            typ = "misc"; f["eprint"] = re.findall(r"arXiv:(\S+?),", rest)[0]; f["archivePrefix"] = "arXiv"
        elif "Python package" in rest:
            typ = "software"; f["version"] = re.findall(r"version ([0-9.]+)", rest)[0].rstrip("."); f["url"] = re.findall(r"(https?://\S+)", rest)[0]
        else:
            typ = "article"; f["journal"] = rest.split(",")[0]
            for k, pat in [("volume", r"vol\. (\d+)"), ("number", r"no\. ([0-9–-]+)"), ("pages", r"pp\. ([0-9:–-]+)")]:
                mm = re.search(pat, rest)
                if mm: f[k] = mm.group(1).replace("–", "--")
            mm = re.search(r"Art\. no\. (\d+)", rest)
            if mm: f["pages"] = mm.group(1)
    else:
        typ = "book"; parts = body.split(", ", 1)[1] if ", " in body else body
        f["title"] = "{" + re.split(r"\. ", parts)[0].strip() + "}"
        pub = re.findall(r"\. ([^.]+), (?:19|20)\d{2}\.$", body); f["publisher"] = pub[0] if pub else ""
    out.append(f"@{typ}{{{key(authors, year, n)},\n" + ",\n".join(f"  {k} = {{{v}}}" for k, v in f.items() if v) + "\n}\n")
open(sys.argv[2], "w").write("\n".join(out)); print(len(out), "entries")
