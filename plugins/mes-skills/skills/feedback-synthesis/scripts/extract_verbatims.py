#!/usr/bin/env python3
"""Transforme des unités codées PAR REPÈRES en table finale avec verbatims exacts.

On ne retape pas les citations : pour chaque unité on indique la source, le début et la fin du
passage (quelques mots chacun), et le script en extrait le texte exact depuis la source.

Usage:
    python extract_verbatims.py units_01.csv [units_02.csv ...] --sources sources/ \\
        [--index sources_index.csv] [--codebook codebook.csv] [--theme-map themes_map.csv] \\
        [--redact redactions.csv] --out coded.csv

units_*.csv (une ligne par unité) :
    source_id   obligatoire. Ex. INT-07, TKT-4521
    start       obligatoire. Les premiers mots du passage, tels qu'ils sont dans la source
    end         les derniers mots du passage. Vide = le passage tient tout entier dans `start`
    theme       obligatoire. Un ou deux thèmes du codebook séparés par « ; », ou « autre: proposition »
    type, intensite, unit_id, occurrence   facultatifs
    participant, segment, date, source_type   facultatifs : surchargent l'index
    toute autre colonne est conservée

Règles de repérage (le script refuse les cas douteux plutôt que de deviner) :
  - le début doit être unique dans la source ; sinon allonger le repère ou donner `occurrence` (1, 2...)
  - la fin = première occurrence après le début
  - un passage ne peut pas traverser un saut de paragraphe (souvent un changement d'interlocuteur)
  - un passage plus long que --max-chars (700) est refusé : repère de fin probablement faux
La casse, les espaces et les variantes typographiques (guillemets, apostrophes, tirets) sont ignorés
pour trouver le passage ; le texte renvoyé est celui de la source.

Sortie : coded.csv (unit_id, source_id, source_type, date, participant, segment, type, theme,
verbatim, intensite + colonnes en plus). Les unités refusées vont dans <out>.rejected.csv avec la
raison ; code de sortie 1 s'il y en a.
"""
import argparse
import csv
import difflib
import re
import sys
import unicodedata
from pathlib import Path

# À garder aligné avec verify_quotes.py (pas d'import croisé : les scripts tournent avec python -I)
REPL = {
    "‘": "'", "’": "'", "‚": "'", "′": "'",
    "“": '"', "”": '"', "„": '"', "«": '"', "»": '"',
    "–": "-", "—": "-", "−": "-",
    " ": " ", " ": " ", " ": " ",
    "…": "...",
}

BASE_COLS = ["unit_id", "source_id", "source_type", "date", "participant", "segment", "type",
             "theme", "verbatim", "intensite"]
UNIT_ONLY = {"start", "end", "occurrence"}


def norm_map(text):
    """Texte normalisé + position d'origine de chaque caractère normalisé."""
    chars, idx, last_space = [], [], True
    for i, c in enumerate(text):
        for ch in REPL.get(c, c):
            if ch.isspace():
                if not last_space:
                    chars.append(" ")
                    idx.append(i)
                    last_space = True
            else:
                for cf in ch.casefold():
                    chars.append(cf)
                    idx.append(i)
                last_space = False
    return "".join(chars), idx


def norm(text):
    return norm_map(unicodedata.normalize("NFC", text))[0].strip()


class Src:
    def __init__(self, path):
        self.text = unicodedata.normalize("NFC", Path(path).read_text(encoding="utf-8", errors="replace"))
        self.ntext, self.idx = norm_map(self.text)


def find_all(hay, needle):
    out, i = [], hay.find(needle)
    while i >= 0:
        out.append(i)
        i = hay.find(needle, i + 1)
    return out


def locate(src, start, end, occurrence, max_chars, allow_multi):
    s = norm(start)
    if len(s) < 3:
        raise ValueError("repère de début vide ou trop court")
    pos = find_all(src.ntext, s)
    if not pos:
        raise ValueError(f"repère de début introuvable : « {start[:60]} »")
    if occurrence is None:
        if len(pos) > 1:
            raise ValueError(f"repère de début ambigu ({len(pos)} occurrences de « {start[:40]} ») : "
                             "allonger le repère ou donner `occurrence`")
        k = 0
    else:
        k = occurrence - 1
        if k < 0 or k >= len(pos):
            raise ValueError(f"occurrence {occurrence} demandée, {len(pos)} trouvée(s)")
    s0 = pos[k]
    s1 = s0 + len(s)
    e1 = s1
    if end and end.strip():
        e = norm(end)
        if len(e) < 3:
            raise ValueError("repère de fin trop court")
        j = src.ntext.find(e, s1)
        if j < 0:
            raise ValueError(f"repère de fin introuvable après le début : « {end[:60]} »")
        e1 = j + len(e)
    o0, o1 = src.idx[s0], src.idx[e1 - 1] + 1
    raw = src.text[o0:o1]
    if not allow_multi and re.search(r"\n[ \t]*\n", raw):
        raise ValueError("le passage traverse un saut de paragraphe (changement d'interlocuteur ?) : "
                         "le couper en deux unités ou resserrer les repères")
    verbatim = re.sub(r"\s+", " ", raw).strip()
    if len(verbatim) > max_chars:
        raise ValueError(f"passage de {len(verbatim)} caractères (> {max_chars}) : repère de fin à revoir")
    return verbatim


def split_themes(s):
    return [t.strip() for t in (s or "").split(";") if t.strip()]


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        return list(r.fieldnames or []), [{(k or "").strip(): (v or "").strip() for k, v in row.items()} for row in r]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("units", nargs="+")
    ap.add_argument("--sources", required=True)
    ap.add_argument("--index")
    ap.add_argument("--codebook", help="CSV avec une colonne `theme` : codebook figé, refuse les autres thèmes")
    ap.add_argument("--theme-map", help="CSV old,new : renomme ou fusionne des thèmes sans recoder")
    ap.add_argument("--redact", help="CSV pattern,replacement : anonymise (remplacement entre [crochets])")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-chars", type=int, default=700)
    ap.add_argument("--allow-multi-paragraph", action="store_true")
    args = ap.parse_args()

    sdir = Path(args.sources)
    files = {p.stem: p for p in sdir.rglob("*") if p.is_file()}
    index = {}
    if args.index:
        _, rows = read_csv(args.index)
        index = {r["source_id"]: r for r in rows}
    allowed = None
    if args.codebook:
        _, rows = read_csv(args.codebook)
        allowed = {r["theme"] for r in rows if r.get("theme")}
        if not allowed:
            sys.exit("Codebook vide ou sans colonne `theme`.")
    tmap = {}
    if args.theme_map:
        _, rows = read_csv(args.theme_map)
        tmap = {r["old"]: r["new"] for r in rows if r.get("old")}
    redactions = []
    if args.redact:
        _, rows = read_csv(args.redact)
        redactions = [(r["pattern"], r["replacement"]) for r in rows if r.get("pattern")]

    cache, out_rows, rejected, extra_cols = {}, [], [], []
    seen_ids, n_in, n_redacted, autre = set(), 0, 0, {}
    no_type_warned = False

    for upath in args.units:
        _, urows = read_csv(upath)
        for row in urows:
            if not any(row.values()):
                continue
            n_in += 1
            uid = row.get("unit_id") or f"U{n_in:04d}"
            reason = None
            verbatim = ""
            try:
                if uid in seen_ids:
                    raise ValueError(f"unit_id en double : {uid}")
                sid = row.get("source_id", "")
                if not sid:
                    raise ValueError("source_id manquant")
                if sid not in files:
                    raise ValueError(f"source {sid} absente de {sdir}")
                if sid not in cache:
                    cache[sid] = Src(files[sid])
                occ = int(row["occurrence"]) if row.get("occurrence") else None
                verbatim = locate(cache[sid], row.get("start", ""), row.get("end", ""), occ,
                                  args.max_chars, args.allow_multi_paragraph)

                themes = []
                for t in split_themes(row.get("theme")):
                    for m in split_themes(tmap.get(t, t)):
                        if m not in themes:
                            themes.append(m)
                if not themes:
                    raise ValueError("thème manquant")
                for t in themes:
                    if t.lower().startswith("autre"):
                        autre.setdefault(t, []).append(uid)
                    elif allowed is not None and t not in allowed:
                        hint = difflib.get_close_matches(t, sorted(allowed), n=1, cutoff=0.6)
                        raise ValueError(f"thème hors codebook : « {t} »" +
                                         (f" (proche de « {hint[0]} »)" if hint else "") +
                                         ". Utiliser « autre: proposition » pour suggérer un thème")
            except ValueError as e:
                reason = str(e)
            if reason:
                rejected.append({**row, "reason": reason, "_file": Path(upath).name})
                continue
            seen_ids.add(uid)
            for pat, rep in redactions:
                new, k = re.subn(re.escape(pat), rep, verbatim, flags=re.I)
                if k:
                    n_redacted += k
                    verbatim = new

            ix = index.get(sid, {})
            rec = {
                "unit_id": uid, "source_id": sid,
                "source_type": row.get("source_type") or ix.get("source_type", ""),
                "date": row.get("date") or ix.get("date", ""),
                "participant": row.get("participant") or ix.get("participant", ""),
                "segment": row.get("segment") or ix.get("segment", ""),
                "type": row.get("type", ""), "theme": ";".join(themes),
                "verbatim": verbatim, "intensite": row.get("intensite", ""),
            }
            if not rec["source_type"] and not no_type_warned:
                print("ATTENTION : pas de source_type (fournir --index ou une colonne source_type).", file=sys.stderr)
                no_type_warned = True
            for k, v in row.items():
                if k and k not in BASE_COLS and k not in UNIT_ONLY and k != "reason":
                    if k not in extra_cols:
                        extra_cols.append(k)
                    rec[k] = v
            out_rows.append(rec)

    cols = BASE_COLS + extra_cols
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in out_rows:
            w.writerow({c: r.get(c, "") for c in cols})

    rej_path = Path(args.out + ".rejected.csv")
    if rejected:
        rcols = []
        for r in rejected:
            for k in r:
                if k not in rcols:
                    rcols.append(k)
        with open(rej_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=rcols)
            w.writeheader()
            w.writerows(rejected)
    elif rej_path.exists():
        rej_path.unlink()

    print(f"{len(out_rows)}/{n_in} unités extraites -> {args.out}")
    if n_redacted:
        print(f"  {n_redacted} remplacement(s) d'anonymisation appliqué(s).")
    if autre:
        print("\nThèmes proposés (« autre ») à arbitrer en fin de lot :")
        for t, ids in sorted(autre.items(), key=lambda x: -len(x[1])):
            print(f"  {t}  ({len(ids)} unité(s) : {', '.join(ids[:6])}{'…' if len(ids) > 6 else ''})")
    if rejected:
        print(f"\n{len(rejected)} unité(s) refusée(s) -> {rej_path}", file=sys.stderr)
        for r in rejected[:15]:
            print(f"  [{r['_file']}] {r.get('source_id', '?')} « {r.get('start', '')[:40]} » : {r['reason']}", file=sys.stderr)
        if len(rejected) > 15:
            print(f"  … et {len(rejected) - 15} autre(s), voir le fichier.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
