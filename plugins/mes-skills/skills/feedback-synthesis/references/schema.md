# Schéma des fichiers de travail

Tous les CSV sont en UTF-8. Les scripts lisent ces en-têtes exacts.

## Fichiers produits par `import_export.py`

- `sources/<source_id>.txt` : texte brut de chaque source, là où les verbatims sont extraits.
- `sources_index.csv` : `source_id, source_type, date, participant, segment, n_chars, origin`.
- `participants_map.csv` : `raw, pseudo`. Identifiants bruts vers pseudonymes. **Local, ne jamais partager.**

## Unités codées par repères (`units_NN.csv`, un fichier par lot)

| Colonne | Obligatoire | Contenu |
|---|---|---|
| `source_id` | oui | `INT-07`, `TKT-4521`… doit exister dans `sources/` |
| `start` | oui | Premiers mots du passage, tels que dans la source. Unique dans la source, sinon allonger ou donner `occurrence` |
| `end` | non | Derniers mots (première occurrence après `start`). Vide = tout le passage tient dans `start` |
| `theme` | oui | Un ou deux thèmes du codebook séparés par `;`, ou `autre: proposition` |
| `type`, `intensite` | non | voir plus bas |
| `unit_id`, `occurrence` | non | identifiant imposé ; n° d'occurrence de `start` |
| `participant`, `segment`, `date`, `source_type` | non | surchargent `sources_index.csv` |

Toute autre colonne est conservée dans `coded.csv`.

## `codebook.csv` (figé après le lot 1)

`theme,definition`. Avec `--codebook`, un thème absent est refusé (avec le plus proche en suggestion). `autre: …` est accepté et listé en fin de lot pour arbitrage.

## `themes_map.csv` (renommer ou fusionner sans recoder)

`old,new`. `new` peut contenir deux thèmes séparés par `;`.

## `redactions.csv` (anonymisation)

`pattern,replacement`. Insensible à la casse ; mettre le remplacement entre crochets (`[quartier]`).

## Table finale des unités (`coded.csv`, produite par `extract_verbatims.py`)

Une ligne par unité de feedback. Lue par `aggregate.py` et `verify_quotes.py` :

| Colonne | Obligatoire | Contenu |
|---|---|---|
| `unit_id` | oui | Identifiant unique de l'unité (`U001`, `U002`…) |
| `source_id` | oui | Identifiant lisible du document source : `INT-07`, `TKT-4521`, `APP-0312`. Sert de référence dans les citations |
| `source_type` | oui | `interview`, `ticket`, `in-app` (ou autre canal, valeurs cohérentes dans tout le fichier) |
| `date` | non | `AAAA-MM-JJ` (ou `AAAA-MM`) |
| `participant` | non | ID de la personne ou du compte (`P07`, `ACC-112`). Vide si inconnu : ne jamais inventer. Sert à dédupliquer |
| `segment` | non | Segment utile à la question directrice (plan, taille, rôle, ancienneté…) |
| `type` | non | `douleur`, `besoin`, `demande-feature`, `bug`, `question`, `compliment` |
| `theme` | oui | Un ou deux thèmes du codebook, séparés par `;` |
| `verbatim` | oui | Extrait exact de la source (jamais retapé) |
| `intensite` | non | `1`, `2` ou `3` (voir SKILL.md). Vide si le texte ne le justifie pas |

Si `participant` est vide, les scripts retombent sur `source_id` pour compter les voix distinctes. Pour les tickets où un même client ouvre plusieurs tickets, renseigner `participant` est ce qui évite de surcompter.

Mettre le verbatim entre guillemets CSV standard (`"..."`), et doubler les guillemets internes.

## Codebook lisible (`codebook.md`, pour l'annexe)

Un tableau, une ligne par thème :

| Thème | Définition (ce qui entre / ce qui n'entre pas) | Exemple de verbatim | Statut |
|---|---|---|---|
| Impossible de savoir pourquoi une campagne a échoué | Manque de visibilité sur les causes d'un résultat. Hors bugs d'affichage des stats | « Je vois que ça a chuté mais pas pourquoi. » — `INT-03` | stable |

`Statut` : `stable`, `nouveau`, `fusionné avec X`, `à surveiller` (peu de données).

Nommer les thèmes comme un problème vécu (« Je ne retrouve pas… », « Impossible de… »), pas comme une catégorie de produit (« Reporting », « UX »). Le nom doit rester compréhensible sans la définition.
