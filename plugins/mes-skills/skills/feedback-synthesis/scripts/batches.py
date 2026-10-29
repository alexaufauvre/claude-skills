#!/usr/bin/env python3
"""Découpe les sources en lots de codage.

Usage:
    python batches.py sources_index.csv [--first-size 30] [--max-sources 50] [--max-chars 80000]
                                        [--out batch_plan.csv]

Pourquoi des lots : un seul passage sur des centaines de sources dépasse ce qu'on peut lire d'un
coup avec soin. Les sources sont mélangées canal par canal (une de chaque canal à tour de rôle),
donc chaque lot, et surtout le premier, représente tous les canaux. Le lot 1 est plus petit : il
sert à construire le codebook, qui est ensuite figé pour les lots suivants.
"""
import argparse
import csv
import sys
from collections import Counter, defaultdict


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("index")
    ap.add_argument("--first-size", type=int, default=30, help="nombre de sources du lot 1 (codebook)")
    ap.add_argument("--max-sources", type=int, default=50)
    ap.add_argument("--max-chars", type=int, default=80000, help="volume de texte max par lot")
    ap.add_argument("--out", default="batch_plan.csv")
    args = ap.parse_args()

    with open(args.index, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit("Index vide.")

    queues = defaultdict(list)
    for r in rows:
        queues[r["source_type"] or "?"].append(r)
    order = []
    while any(queues.values()):
        for t in sorted(queues):
            if queues[t]:
                order.append(queues[t].pop(0))

    batches, cur, cur_chars = [], [], 0
    limit = min(args.first_size, args.max_sources)
    for r in order:
        n = int(r.get("n_chars") or 0)
        if cur and (len(cur) >= limit or cur_chars + n > args.max_chars):
            batches.append(cur)
            cur, cur_chars = [], 0
            limit = args.max_sources
        cur.append(r)
        cur_chars += n
    if cur:
        batches.append(cur)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source_id", "source_type", "n_chars", "batch"])
        for i, b in enumerate(batches, 1):
            for r in b:
                w.writerow([r["source_id"], r["source_type"], r.get("n_chars", ""), i])

    print(f"{len(rows)} sources -> {len(batches)} lots (plan : {args.out})\n")
    print("| Lot | Sources | Caractères | Répartition par canal |")
    print("|---|---|---|---|")
    for i, b in enumerate(batches, 1):
        c = Counter(r["source_type"] for r in b)
        chars = sum(int(r.get("n_chars") or 0) for r in b)
        label = " (codebook)" if i == 1 and len(batches) > 1 else ""
        print(f"| {i}{label} | {len(b)} | {chars} | " + ", ".join(f"{k} {v}" for k, v in sorted(c.items())) + " |")


if __name__ == "__main__":
    main()
