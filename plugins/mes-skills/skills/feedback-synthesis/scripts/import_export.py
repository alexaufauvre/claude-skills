#!/usr/bin/env python3
"""Importe des feedbacks vers le format de travail : un fichier texte par source + un index.

Deux entrées possibles :
  - un export CSV/TSV (Zendesk, Intercom, in-app, NPS...) : une ligne = un feedback
  - un dossier de fichiers .txt/.md (transcripts, comptes rendus) : un fichier = une source

Sortie dans --out-dir :
  sources/<source_id>.txt   le texte brut de chaque source (c'est là que les verbatims seront extraits)
  sources_index.csv         source_id, source_type, date, participant, segment, n_chars, origin
  participants_map.csv      (avec --pseudonymize) identifiant brut -> pseudonyme. LOCAL : ne pas partager.

À lancer une fois par canal, avec le même --out-dir : l'index et la table de pseudonymes sont
complétés, jamais écrasés. Un même client présent dans deux canaux reçoit le même pseudonyme,
ce qui permet de le compter une seule fois.

Exemples :
  python import_export.py tickets.csv --out-dir work --prefix TKT --source-type ticket \\
      --id-col "Ticket ID" --text-col Subject --text-col Description --date-col Created \\
      --user-col "Requester email" --segment-col Plan --pseudonymize --strip-html
  python import_export.py ./transcripts/ --out-dir work --prefix INT --source-type interview
"""
import argparse
import csv
import html
import re
import sys
from pathlib import Path

INDEX_COLS = ["source_id", "source_type", "date", "participant", "segment", "n_chars", "origin"]
TEXT_EXT = {".txt", ".md", ".markdown"}


def sanitize_id(v):
    return re.sub(r"[^\w.\-]+", "-", str(v).strip(), flags=re.U).strip("-")


def norm_date(v):
    v = (v or "").strip()
    if not v:
        return ""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", v)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.match(r"^(\d{1,2})[/.](\d{1,2})[/.](\d{4})", v)
    if m:  # jj/mm/aaaa (usage français)
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    return v


def strip_html(s):
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</(p|div|li|tr|h[1-6])>", "\n\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


class Pseudo:
    """Table identifiant brut -> pseudonyme stable, persistée entre les lancements."""

    def __init__(self, path, prefix):
        self.path, self.prefix, self.map, self.n = path, prefix, {}, 0
        if path.exists():
            with open(path, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.map[r["raw"]] = r["pseudo"]
                    m = re.search(r"(\d+)$", r["pseudo"])
                    if m:
                        self.n = max(self.n, int(m.group(1)))

    def get(self, raw):
        key = (raw or "").strip().lower()
        if not key:
            return ""
        if key not in self.map:
            self.n += 1
            self.map[key] = f"{self.prefix}{self.n:04d}"
        return self.map[key]

    def save(self):
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["raw", "pseudo"])
            for k, v in self.map.items():
                w.writerow([k, v])


def find_col(fieldnames, name):
    for fn in fieldnames:
        if fn == name:
            return fn
    for fn in fieldnames:
        if fn.strip().lower() == name.strip().lower():
            return fn
    sys.exit(f"Colonne « {name} » introuvable. Colonnes disponibles : {', '.join(fieldnames)}")


def read_csv(path, encoding, delimiter):
    csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
    with open(path, newline="", encoding=encoding) as f:
        sample = f.read(8192)
        f.seek(0)
        if delimiter:
            d = "\t" if delimiter == "\\t" else delimiter
        else:
            try:
                d = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
            except csv.Error:
                d = ","
        reader = csv.DictReader(f, delimiter=d)
        return reader.fieldnames or [], list(reader)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="export CSV/TSV ou dossier de .txt/.md")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--prefix", required=True, help="préfixe des source_id : INT, TKT, APP...")
    ap.add_argument("--source-type", required=True, help="interview, ticket, in-app...")
    ap.add_argument("--id-col", help="colonne de l'identifiant (sinon numéro de ligne). Les lignes de même id sont fusionnées")
    ap.add_argument("--text-col", action="append", default=[], help="colonne de texte, répétable (sujet, description...)")
    ap.add_argument("--date-col")
    ap.add_argument("--user-col", help="colonne client/utilisateur : sert à compter les voix distinctes")
    ap.add_argument("--segment-col", action="append", default=[], help="colonne de segment, répétable")
    ap.add_argument("--pseudonymize", action="store_true", help="remplace les identifiants clients par C0001, C0002...")
    ap.add_argument("--pseudo-prefix", default="C")
    ap.add_argument("--strip-html", action="store_true")
    ap.add_argument("--min-chars", type=int, default=1, help="ignore les sources plus courtes")
    ap.add_argument("--encoding", default="utf-8-sig")
    ap.add_argument("--delimiter", help="séparateur CSV (auto par défaut ; \\t pour tabulation)")
    args = ap.parse_args()

    src = Path(args.input)
    out = Path(args.out_dir)
    (out / "sources").mkdir(parents=True, exist_ok=True)
    pseudo = Pseudo(out / "participants_map.csv", args.pseudo_prefix) if args.pseudonymize else None

    records, merged, warnings = {}, 0, []

    if src.is_dir():
        files = sorted(p for p in src.iterdir() if p.is_file() and p.suffix.lower() in TEXT_EXT)
        if not files:
            sys.exit(f"Aucun .txt/.md dans {src}")
        w = max(2, len(str(len(files))))
        for i, p in enumerate(files, 1):
            sid = f"{args.prefix}-{i:0{w}d}"
            records[sid] = {"parts": [p.read_text(encoding="utf-8", errors="replace").strip()],
                            "date": "", "participant": "", "segment": "", "origin": p.name}
    elif src.is_file():
        if not args.text_col:
            sys.exit("--text-col est obligatoire pour un export CSV")
        fields, rows = read_csv(src, args.encoding, args.delimiter)
        id_col = find_col(fields, args.id_col) if args.id_col else None
        text_cols = [find_col(fields, c) for c in args.text_col]
        date_col = find_col(fields, args.date_col) if args.date_col else None
        user_col = find_col(fields, args.user_col) if args.user_col else None
        seg_cols = [find_col(fields, c) for c in args.segment_col]
        emails = 0
        for n, row in enumerate(rows, 1):
            raw_id = (row.get(id_col) or "").strip() if id_col else str(n)
            if not raw_id:
                raw_id = str(n)
            sid = f"{args.prefix}-{sanitize_id(raw_id)}"
            parts = []
            for c in text_cols:
                v = (row.get(c) or "").strip()
                if v:
                    parts.append(strip_html(v) if args.strip_html else v)
            parts = [p for p in parts if p]
            raw_user = (row.get(user_col) or "").strip() if user_col else ""
            if raw_user and "@" in raw_user and not pseudo:
                emails += 1
            participant = pseudo.get(raw_user) if pseudo else raw_user
            segment = " · ".join(v for v in ((row.get(c) or "").strip() for c in seg_cols) if v)
            date = norm_date(row.get(date_col)) if date_col else ""
            if sid in records:
                merged += 1
                rec = records[sid]
                for p in parts:  # un sujet répété d'une ligne à l'autre n'est gardé qu'une fois
                    if p not in rec["parts"]:
                        rec["parts"].append(p)
                rec["date"] = rec["date"] or date
                rec["participant"] = rec["participant"] or participant
                rec["segment"] = rec["segment"] or segment
            else:
                records[sid] = {"parts": parts, "date": date, "participant": participant,
                                "segment": segment, "origin": raw_id}
        if emails:
            warnings.append(f"{emails} lignes ont une adresse email comme identifiant client : "
                            "utiliser --pseudonymize avant de partager quoi que ce soit.")
    else:
        sys.exit(f"Entrée introuvable : {src}")

    # index existant (autres canaux déjà importés)
    index_path = out / "sources_index.csv"
    index = {}
    if index_path.exists():
        with open(index_path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                index[r["source_id"]] = r

    written = skipped = replaced = 0
    for sid, rec in records.items():
        text = "\n\n".join(rec["parts"]).strip()
        if len(text) < args.min_chars:
            skipped += 1
            continue
        if sid in index:
            replaced += 1
        (out / "sources" / f"{sid}.txt").write_text(text + "\n", encoding="utf-8")
        index[sid] = {"source_id": sid, "source_type": args.source_type, "date": rec["date"],
                      "participant": rec["participant"], "segment": rec["segment"],
                      "n_chars": str(len(text)), "origin": rec["origin"]}
        written += 1

    with open(index_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=INDEX_COLS)
        w.writeheader()
        for r in index.values():
            w.writerow({k: r.get(k, "") for k in INDEX_COLS})
    if pseudo:
        pseudo.save()

    voices = len({r["participant"] for r in index.values() if r.get("participant")})
    print(f"{written} sources écrites dans {out / 'sources'} ({args.source_type}, préfixe {args.prefix}).")
    if skipped:
        print(f"  {skipped} lignes ignorées (texte vide).")
    if merged:
        print(f"  {merged} lignes fusionnées dans une source de même identifiant.")
    if replaced:
        print(f"  {replaced} sources déjà présentes dans l'index ont été remplacées.")
    print(f"Index : {len(index)} sources au total, {voices} participants distincts.")
    if pseudo:
        print(f"Pseudonymes : {pseudo.path} contient les identifiants bruts. À garder en local.")
    for w_ in warnings:
        print("ATTENTION :", w_, file=sys.stderr)


if __name__ == "__main__":
    main()
