#!/usr/bin/env python3
"""Quantifie la récurrence des thèmes à partir d'un CSV d'unités codées.

Usage:
    python aggregate.py coded.csv [--out themes.md] [--json themes.json] [--min-voices 1]

Principe : on compte des VOIX DISTINCTES (participant, à défaut source_id),
pas des mentions. Un même utilisateur qui se plaint dans 8 tickets compte pour 1.
"""
import argparse
import csv
import json
import sys
from collections import defaultdict

REQUIRED = {"unit_id", "source_id", "source_type", "theme", "verbatim"}


def read_units(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            sys.exit(f"Colonnes manquantes dans {path} : {', '.join(sorted(missing))}")
        return list(reader)


def voice(row):
    """Identifiant de la voix : participant si connu, sinon la source."""
    return (row.get("participant") or "").strip() or row["source_id"].strip()


def split_themes(raw):
    return [t.strip() for t in (raw or "").split(";") if t.strip()]


def to_int(v):
    try:
        return int(str(v).strip())
    except (ValueError, AttributeError):
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--out", help="écrit le tableau markdown ici (sinon stdout)")
    ap.add_argument("--json", help="écrit aussi les résultats en JSON")
    ap.add_argument("--min-voices", type=int, default=1, help="masque les thèmes sous ce nombre de voix")
    args = ap.parse_args()

    rows = read_units(args.csv)
    if not rows:
        sys.exit("Aucune unité dans le fichier.")

    # Corpus : combien de sources / voix au total, par canal
    corpus_sources = {r["source_id"].strip() for r in rows}
    corpus_voices = {voice(r) for r in rows}
    channel_sources = defaultdict(set)
    channel_voices = defaultdict(set)
    for r in rows:
        ch = r["source_type"].strip() or "?"
        channel_sources[ch].add(r["source_id"].strip())
        channel_voices[ch].add(voice(r))
    channels = sorted(channel_sources)

    themes = defaultdict(lambda: {
        "units": 0, "sources": set(), "voices": set(),
        "by_channel": defaultdict(set), "dates": [], "intens": [], "types": defaultdict(int),
    })
    for r in rows:
        for t in split_themes(r["theme"]):
            d = themes[t]
            d["units"] += 1
            d["sources"].add(r["source_id"].strip())
            d["voices"].add(voice(r))
            d["by_channel"][r["source_type"].strip() or "?"].add(voice(r))
            if (r.get("date") or "").strip():
                d["dates"].append(r["date"].strip())
            i = to_int(r.get("intensite"))
            if i in (1, 2, 3):
                d["intens"].append(i)
            if (r.get("type") or "").strip():
                d["types"][r["type"].strip()] += 1

    results = []
    for name, d in themes.items():
        if len(d["voices"]) < args.min_voices:
            continue
        n_ch = sum(1 for c in channels if d["by_channel"].get(c))
        results.append({
            "theme": name,
            "units": d["units"],
            "sources": len(d["sources"]),
            "voices": len(d["voices"]),
            "voices_share_of_corpus": round(len(d["voices"]) / len(corpus_voices), 3),
            "channels_present": n_ch,
            "by_channel": {c: len(d["by_channel"].get(c, ())) for c in channels},
            "first_date": min(d["dates"]) if d["dates"] else "",
            "last_date": max(d["dates"]) if d["dates"] else "",
            "intensity_mean": round(sum(d["intens"]) / len(d["intens"]), 2) if d["intens"] else None,
            "intensity_n": len(d["intens"]),
            "types": dict(d["types"]),
        })
    results.sort(key=lambda x: (-x["voices"], -x["channels_present"], -x["units"], x["theme"]))

    # Markdown
    n_voices = len(corpus_voices)
    small = n_voices < 10
    lines = []
    lines.append(f"**Corpus** : {len(rows)} unités, {len(corpus_sources)} sources, {n_voices} voix distinctes.")
    chan_txt = ", ".join(f"{c} : {len(channel_voices[c])} voix / {len(channel_sources[c])} sources" for c in channels)
    lines.append(f"**Par canal** : {chan_txt}.")
    if small:
        lines.append("> n < 10 voix : lire les effectifs, pas les pourcentages.")
    lines.append("")
    header = ["Thème", "Voix", "Part du corpus", *channels, "Canaux", "Unités", "Intensité moy.", "Période", "Lecture"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(header)) + "|")
    for r in results:
        if small:
            share = f"{r['voices']}/{n_voices}"
        else:
            share = f"{round(100 * r['voices_share_of_corpus'])} %"
        chan_cells = [f"{r['by_channel'][c]}/{len(channel_voices[c])}" for c in channels]
        inten = f"{r['intensity_mean']:.1f} (n={r['intensity_n']})" if r["intensity_mean"] is not None else "–"
        period = f"{r['first_date']} → {r['last_date']}" if r["first_date"] else "–"
        if len(channels) < 2:
            reading = "Piste (1 seul canal dans le corpus)"
        elif r["channels_present"] >= 3 or (r["channels_present"] == len(channels) and len(channels) >= 2):
            reading = "Solide (multi-canal)"
        elif r["channels_present"] == 2:
            reading = "Plausible (2 canaux)"
        else:
            reading = "Piste (1 canal)"
        if r["voices"] < 3:
            reading += " — faible effectif"
        row = [r["theme"], str(r["voices"]), share, *chan_cells, str(r["channels_present"]),
               str(r["units"]), inten, period, reading]
        lines.append("| " + " | ".join(c.replace("|", "\\|") for c in row) + " |")
    lines.append("")
    lines.append("*Voix = participants distincts (à défaut, sources distinctes). Colonnes canal = voix du thème / voix du canal.*")
    md = "\n".join(lines) + "\n"

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Écrit : {args.out}")
    else:
        print(md)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"corpus": {"units": len(rows), "sources": len(corpus_sources), "voices": n_voices},
                       "themes": results}, f, ensure_ascii=False, indent=2)
        print(f"Écrit : {args.json}")

    # Garde-fou sur le thème "autre"
    autre = next((r for r in results if r["theme"].lower() in ("autre", "autres", "other")), None)
    if autre and autre["units"] / len(rows) > 0.15:
        print(f"\nATTENTION : le thème « {autre['theme']} » pèse {round(100 * autre['units'] / len(rows))} % des unités "
              "(> 15 %) : le codebook est probablement incomplet.", file=sys.stderr)


if __name__ == "__main__":
    main()
