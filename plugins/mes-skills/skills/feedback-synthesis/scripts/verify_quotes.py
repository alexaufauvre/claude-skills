#!/usr/bin/env python3
"""Vérifie que chaque verbatim du CSV existe bien dans sa source.

Usage:
    python verify_quotes.py coded.csv --sources ./sources/ [--report verify.md]

Le dossier --sources contient un fichier texte par source, nommé d'après source_id
(INT-07.md, TKT-4521.txt, APP-0312.csv...). Les docx/pdf doivent être convertis en
texte au préalable.

La comparaison ignore la casse, les différences d'espaces/retours à la ligne et
les variantes typographiques (guillemets, apostrophes, tirets, espaces insécables).
Les coupes signalées par […] ou [...] sont gérées : chaque fragment doit exister,
dans l'ordre.

Code de sortie : 0 si tout est retrouvé, 1 sinon.
"""
import argparse
import csv
import re
import sys
import unicodedata
from pathlib import Path

TEXT_EXT = {".txt", ".md", ".markdown", ".csv", ".tsv", ".json", ".html", ".htm", ".log", ""}

REPLACEMENTS = {
    "‘": "'", "’": "'", "‚": "'", "′": "'",
    "“": '"', "”": '"', "„": '"', "«": '"', "»": '"',
    "–": "-", "—": "-", "−": "-",
    " ": " ", " ": " ", " ": " ",
    "…": "...",
}


def norm(s):
    s = unicodedata.normalize("NFC", s)
    for a, b in REPLACEMENTS.items():
        s = s.replace(a, b)
    s = s.casefold()
    return re.sub(r"\s+", " ", s).strip()


def strip_wrapping_quotes(s):
    return re.sub(r'^[\s"\']+|[\s"\']+$', "", s)


def fragments(verbatim):
    """Découpe sur […] / [...] / ... ; ignore les [ajouts entre crochets] en les retirant."""
    v = re.sub(r"\[\s*(?:…|\.\.\.)\s*\]", "\u0000", verbatim)
    v = v.replace("…", "\u0000")
    v = re.sub(r"\[[^\]]*\]", "\u0000", v)  # contexte ajouté par l'analyste : coupe
    parts = [strip_wrapping_quotes(norm(p)) for p in v.split("\u0000")]
    return [p for p in parts if len(p) >= 3]


def find_source(sources_dir, source_id):
    sid = source_id.strip()
    cands = [p for p in sources_dir.iterdir() if p.is_file() and p.stem == sid]
    if not cands:
        cands = [p for p in sources_dir.rglob("*") if p.is_file() and p.stem == sid]
    return cands[0] if cands else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--sources", required=True)
    ap.add_argument("--report")
    args = ap.parse_args()

    sources_dir = Path(args.sources)
    if not sources_dir.is_dir():
        sys.exit(f"Dossier introuvable : {sources_dir}")

    with open(args.csv, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    cache = {}
    ok, bad, nofile, unreadable = [], [], [], []
    for r in rows:
        sid = r["source_id"].strip()
        if sid not in cache:
            p = find_source(sources_dir, sid)
            if p is None:
                cache[sid] = ("missing", None)
            elif p.suffix.lower() not in TEXT_EXT:
                cache[sid] = ("unreadable", p)
            else:
                cache[sid] = ("ok", norm(p.read_text(encoding="utf-8", errors="replace")))
        status, content = cache[sid]
        if status == "missing":
            nofile.append(r)
            continue
        if status == "unreadable":
            unreadable.append(r)
            continue
        frags = fragments(r["verbatim"])
        if not frags:
            bad.append((r, "verbatim vide ou trop court"))
            continue
        pos, found = 0, True
        for fr in frags:
            i = content.find(fr, pos)
            if i < 0:
                found = False
                break
            pos = i + len(fr)
        if found:
            ok.append(r)
        else:
            # même fragment présent mais pas dans l'ordre ?
            if all(fr in content for fr in frags):
                bad.append((r, "fragments présents mais dans un ordre différent de la source"))
            else:
                bad.append((r, "introuvable dans la source"))

    lines = [f"**Vérification des verbatims** : {len(ok)}/{len(rows)} retrouvés."]
    if bad:
        lines.append(f"\n### Introuvables ({len(bad)}) — à corriger ou retirer\n")
        for r, why in bad:
            lines.append(f"- `{r['unit_id']}` · `{r['source_id']}` — {why} : « {r['verbatim'][:120]} »")
    if nofile:
        ids = sorted({r["source_id"] for r in nofile})
        lines.append(f"\n### Source absente du dossier ({len(ids)} sources, {len(nofile)} unités)\n")
        lines.append("- " + ", ".join(f"`{i}`" for i in ids))
    if unreadable:
        ids = sorted({r["source_id"] for r in unreadable})
        lines.append(f"\n### Format non lisible ({len(ids)} sources) — convertir en texte\n")
        lines.append("- " + ", ".join(f"`{i}`" for i in ids))
    out = "\n".join(lines) + "\n"
    print(out)
    if args.report:
        Path(args.report).write_text(out, encoding="utf-8")
    sys.exit(0 if not (bad or nofile or unreadable) else 1)


if __name__ == "__main__":
    main()
