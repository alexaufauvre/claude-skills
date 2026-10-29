---
name: "feedback-synthesis"
description: "Agrège des comptes rendus d'interviews, tickets support et feedbacks in-app (ou toute autre voix client) pour détecter les patterns, quantifier leur récurrence et produire une synthèse orientée opportunités avec verbatims sourcés. À utiliser dès que l'utilisateur colle, joint ou pointe vers des verbatims, notes d'interviews, exports de tickets (Zendesk, Intercom, Crisp...), NPS/feedbacks in-app, ou demande \"qu'est-ce qui ressort\", \"quels sont les pain points\", \"synthèse des retours\", \"voice of customer\", \"analyse des tickets\", \"thèmes récurrents\", \"opportunités produit à partir des retours\" — même s'il ne prononce pas le mot \"synthèse\"."
---

# Synthèse de feedbacks : problèmes priorisés et sourcés

Transformer un tas de retours bruts (interviews, tickets, in-app) en une liste de **problèmes utilisateur** priorisés, où chaque affirmation est **comptée** et **sourcée**. Un PM doit pouvoir défendre n'importe quelle ligne devant un dev sceptique : « combien de gens ? », « montre-moi la phrase ».

Le workflow du PM : extraire des insights, les regrouper en thèmes, formuler le problème sous-jacent, prioriser, puis (autre étape, autre skill) explorer les solutions. Cette skill s'arrête à la liste priorisée des problèmes. Elle ne propose pas d'idées de solution sauf demande explicite.

Trois règles qui gouvernent tout le reste :

1. **Compter des sources distinctes, pas des mentions.** Un utilisateur qui râle 8 fois dans 8 tickets = 1 voix. Sinon la synthèse récompense les plus bavards.
2. **Un verbatim est une citation exacte ou n'est pas un verbatim.** Pas de reformulation entre guillemets. Chaque citation porte sa source.
3. **Un thème est un problème vécu, pas une catégorie ni une solution.** « Impossible de savoir pourquoi une campagne a chuté », pas « Reporting » ni « Ajouter un dashboard ».

## Workflow

### 1. Cadrer (2 minutes, pas plus)

Établir, depuis la demande ou en le déduisant des fichiers (ne poser une question que si la réponse change l'analyse) :
- **Question directrice** : sur quoi doit éclairer la synthèse ? (une feature, un parcours, un segment, « tout »). Sans question, la synthèse devient un inventaire.
- **Périmètre** : période, produit, segments.
- **Inventaire des sources** : combien de documents par canal, quelles dates. Annoncer le volume (« 12 interviews, 340 tickets, 85 feedbacks in-app ») avant de plonger.
- **Destination du livrable** : si l'utilisateur nomme une page Notion, un doc ou un dossier, c'est là que la synthèse est créée (voir Livrable).

Si les données sont dans Notion, Drive, un CRM ou un outil de support connecté, aller les chercher plutôt que demander un copier-coller. Pour une base Notion : récupérer le schéma, puis lire les lignes et le contenu de chaque page.

### 2. Ingérer : un fichier texte par source

Tout part du même format de travail : `sources/<source_id>.txt` + `sources_index.csv`. Ne jamais retaper une source ni un verbatim.

- **Export CSV** (Zendesk, Intercom, in-app, NPS…) : `scripts/import_export.py` (une fois par canal, même `--out-dir`).
- **Dossier de transcripts/comptes rendus** (.txt/.md) : même script, sur le dossier. Pour une interview, ne garder dans la source que la parole de l'interviewé (les notes de l'intervieweur peuvent alimenter un thème mais ne sont jamais des verbatims).
- **Notion, Drive, autre outil connecté** : récupérer le texte, l'écrire tel quel dans un fichier, importer le dossier. Les propriétés utiles (segment, participant, date, nombre de biens…) ne sont pas lues par le script : les reporter dans `sources_index.csv` (colonnes `participant`, `segment`, `date`).

```bash
python scripts/import_export.py tickets.csv --out-dir work --prefix TKT --source-type ticket \
    --id-col "Ticket ID" --text-col Subject --text-col Description --date-col Created \
    --user-col "Requester email" --segment-col Plan --pseudonymize --strip-html
python scripts/import_export.py inapp.csv --out-dir work --prefix APP --source-type in-app --id-col id \
    --text-col comment --date-col date --user-col user --pseudonymize
python scripts/import_export.py ./transcripts/ --out-dir work --prefix INT --source-type interview
```

Ce que fait le script : fusionne les lignes de même id (plusieurs messages d'un ticket), normalise les dates, nettoie le HTML, et avec `--pseudonymize` remplace les identifiants clients par `C0001`… de façon stable entre canaux (`participants_map.csv`, **local, à ne pas partager**). Un même client qui écrit dans deux canaux compte donc pour une seule voix. Sans `--pseudonymize`, il avertit si les identifiants sont des emails.

### 3. Coder par lots, codebook figé après le lot 1

```bash
python scripts/batches.py work/sources_index.csv --out work/batch_plan.csv
```

Le plan mélange les canaux à tour de rôle : chaque lot, surtout le premier, représente tous les canaux. Le lot 1 est plus petit (≈30 sources) : il sert à construire le codebook.

**Lot 1 : construire le codebook** (induction, pas de liste préfabriquée) :
- 8 à 15 thèmes. Nom orienté problème vécu et définition d'une ligne (ce qui entre / n'entre pas). Écrire `codebook.csv` (colonnes `theme,definition`).
- Une unité peut porter 2 thèmes (séparés par `;`), rarement plus.
- Ne pas forcer un thème. Une unité qui contredit le pattern dominant est un **contre-signal** : le noter.

**Lots suivants : codebook figé.** Si un passage ne rentre dans aucun thème, coder `autre: <proposition de thème>` au lieu d'en créer un. À la fin de chaque lot le script liste ces propositions ; arbitrer alors (créer le thème, ou le rattacher à un existant). Si un thème est créé ou renommé après coup, ne pas recoder : l'ajouter au codebook et utiliser `--theme-map` (`old,new`) pour renommer/fusionner. Si `autre` dépasse ~15 % des unités, le codebook est faux : le revoir.

**Coder = désigner des passages, pas les copier.** Lire les sources du lot et écrire `units_NN.csv`, une ligne par unité (un besoin, une douleur, une demande, un bug ou un compliment ; une phrase qui mélange deux sujets = deux unités) :

`source_id, start, end, theme, type, intensite`

- `start` : les premiers mots du passage, tels qu'ils sont dans la source (assez pour être unique dans cette source). `end` : les derniers mots ; vide si le passage tient dans `start`. Le passage choisi est le plus court qui porte le sens.
- `type` : `douleur`, `besoin`, `demande-feature`, `bug`, `question`, `compliment`.
- `intensite` : 1 (gêne), 2 (frein), 3 (bloquant / risque de churn), seulement si le texte le justifie (« j'ai failli annuler »). Sinon vide.
- Colonnes facultatives : `unit_id`, `occurrence` (si le début apparaît plusieurs fois), `participant`/`segment`/`date` pour surcharger l'index, et toute colonne utile qui sera conservée. Pour des interviews, ajouter une colonne `ouverture` (`ouverte` = la personne a abordé le sujet à une question ouverte, `guidée` = l'intervieweur a choisi le sujet) : elle sert à juger la solidité de la preuve à l'étape 4.

Puis extraire les verbatims exacts :

```bash
python scripts/extract_verbatims.py work/units_01.csv work/units_02.csv --sources work/sources \
    --index work/sources_index.csv --codebook work/codebook.csv [--theme-map themes_map.csv] \
    [--redact redactions.csv] --out work/coded.csv
```

Le script refuse plutôt que de deviner : début introuvable ou ambigu, fin introuvable, passage qui traverse un saut de paragraphe (changement d'interlocuteur), passage trop long, thème hors codebook (avec suggestion du plus proche). Les refus vont dans `coded.csv.rejected.csv` avec la raison ; corriger les repères et relancer. `--redact` (colonnes `pattern,replacement`) anonymise les noms restants dans les verbatims, le remplacement est mis entre `[crochets]`.

Ne jamais échantillonner en silence : si on échantillonne, l'écrire dans les limites.

### 4. Quantifier

Lancer le script pour ne pas compter à la main :

```bash
python scripts/aggregate.py coded.csv --out themes.md
```

Il produit, par thème : unités, **voix distinctes**, répartition par canal, part du corpus, période couverte, intensité moyenne.

Pour des interviews, ajouter le croisement ouverte / guidée par thème (comptage de voix distinctes sur la colonne `ouverture`). Définir la **solidité de la preuve** : forte = au moins 2 voix en interview ouverte, moyenne = 1, faible = 0 (thème peut-être induit par le guide d'entretien).

Lire les chiffres avec ces garde-fous :
- **Toujours compter en effectifs** (« 7 sur 12 ») ; quand n < 10, jamais de pourcentages.
- **Trianguler les canaux.** Un thème présent dans les trois canaux est solide. Un thème présent dans un seul est une piste, pas un pattern : le dire en tête du livrable. Les tickets sur-représentent bugs et irritants ; les interviews sur-représentent ce que les gens ont envie de raconter ; l'in-app sur-représente les mécontents rapides.
- **Pas de statistiques déguisées.** Ces corpus ne sont pas des échantillons représentatifs. Écrire « récurrent dans notre corpus », pas « X % des utilisateurs ».
- **Récurrence ≠ importance.** Un thème rare mais très intense peut peser plus qu'un thème fréquent mais mineur. Montrer les colonnes séparément, ne pas les fusionner dans un score opaque.

### 5. Formuler les problèmes et prioriser

Pour chaque thème, formuler le **problème sous-jacent** du point de vue de l'utilisateur, en une phrase, sans solution embarquée (« une petite défaillance se paie en avis négatif », pas « il faut des alertes »).

Prioriser avec des critères visibles, une colonne par critère, pas de note sur 100 :
- **Portée** : utilisateurs concernés (effectif sur n).
- **Douleur** : intensité moyenne sur 3.
- **Impact attendu** (user et business) : jugement qualitatif (fort / moyen / faible) avec une demi-phrase de justification, **toujours marqué comme hypothèse** sauf si le corpus ou l'utilisateur fournit des données (revenu par client, churn…). Les demander si elles existent.
- **Preuve** : solidité (forte / moyenne / faible, étape 4).
- **Risque et effort** : ne pas les noter par défaut, ils dépendent des solutions. Les ajouter si l'utilisateur donne le contexte ou explore déjà des solutions.

Rang par défaut : portée d'abord (P1 = au moins la moitié du corpus, P2 = un tiers à la moitié, P3 = le reste, à adapter à la taille du corpus), puis douleur. Écrire la règle sous le tableau. Signaler explicitement les exceptions : un thème intense mais porté par une seule voix reste P3 avec la mention « à creuser ».

**Garder la liste large** : tous les thèmes retenus apparaissent, pas seulement les 2-3 premiers. L'utilisateur choisit selon sa stratégie et son contexte, pas forcément dans l'ordre.

Chaque problème a aussi une ligne « à creuser » quand une question non résolue changerait sa priorité.

### 6. Sourcer les verbatims

Pour chaque problème, retenir **2 à 3 verbatims** : choisir les plus **nets** et **variés** (canaux et participants différents), pas trois fois la même plainte.

Format de citation :

> « Je passe 20 minutes à refaire l'export à la main chaque lundi. » — `INT-07`

Règles :
- Citation **copiée telle quelle** depuis le champ `verbatim`. Coupe avec `[…]`, ajout de contexte entre `[crochets]`, jamais de réécriture.
- Traduction d'un verbatim : l'indiquer (`traduit de l'anglais`) et garder l'original dans l'annexe. Si le corpus est dans une langue, citer dans cette langue.
- Une citation par participant par problème, sauf pour montrer une nuance.

Avant de livrer, **vérifier mécaniquement** que chaque citation du livrable existe dans sa source. Les verbatims de `coded.csv` sont exacts par construction ; le risque est la citation retapée dans le livrable. Mettre les citations du livrable dans un petit CSV (`source_id,verbatim`) et lancer :

```bash
python scripts/verify_quotes.py doc_quotes.csv --sources work/sources
```

(le script comprend `[…]` et `[crochets]`). Toute citation introuvable est corrigée ou retirée. Ne jamais livrer une synthèse dont cette vérification n'a pas été passée, ou dire explicitement qu'elle n'a pas pu l'être.

## Livrable

Le lecteur veut voir d'un coup d'œil la liste priorisée des problèmes, et creuser seulement s'il en a besoin. Structure, dans cet ordre :

1. **Un encadré d'une ou deux lignes** : source(s) et mise en garde principale (par exemple « un seul canal : à confirmer »). Pas de paragraphe d'introduction.
2. **Tableau des thèmes priorisé**, en tête de page : priorité (colorée), problème sous-jacent, portée (x/n), douleur (x/3), impact attendu (hyp.), preuve. Les chiffres vivent dans ce tableau, pas dans des phrases. Règle de rang en une ligne dessous.
3. **Fiches par problème, dépliantes** (une par ligne du tableau) : la phrase de problème, 2 à 3 verbatims sourcés, et « à creuser » si pertinent. Pas de solutions.
4. **Annexes, dépliantes** : périmètre et limites (sources, volumes, biais, interviews ouvertes vs guidées, langue), détail des voix par thème (par canal ou ouvert/guidé), méthode (voix distinctes, extraction automatique des verbatims, définition de la preuve et de la douleur).

**Écrire court.** Phrases courtes, zéro jargon creux (« insights actionnables », « pain points majeurs »). Pas de stats ni de pourcentages répétés dans les phrases : un chiffre apparaît dans le tableau, éventuellement dans l'annexe, et nulle part ailleurs. Si une formulation pourrait s'écrire sans avoir lu les données, la supprimer. Une phrase de texte ne doit pas répéter ce que le tableau dit déjà.

**Où créer le livrable :**
- Si l'utilisateur nomme une page Notion : créer une sous-page dans cette page (lire d'abord la spécification Notion-flavored markdown). Tableau en `<table>` avec lignes colorées par priorité (rouge P1, orange P2, sans couleur P3), fiches et annexes en `<toggle heading="h3">`. Pas de ligne vide juste après la balise ouvrante ni juste avant la fermante.
- Sinon : un doc à garder et partager (type Docs si disponible), avec la même structure. Le tableau des thèmes est un tableau natif.
- Dans tous les cas, joindre le CSV codé (`coded.csv`) : c'est la traçabilité qui permet à quelqu'un d'autre de refaire le décompte.

## Cas particuliers

- **Très gros volume (centaines de feedbacks)** : c'est le cas nominal de l'étape 3 (import, lots, codebook figé). Ne rien retaper, ne jamais échantillonner en silence.
- **Un seul canal fourni** : produire la synthèse quand même, mais dire en tête qu'il n'y a pas de triangulation et que les thèmes sont des pistes.
- **Données en deux langues** : coder dans la langue de la synthèse, conserver le verbatim dans sa langue d'origine.
- **Mise à jour d'une synthèse existante** : réutiliser le codebook précédent, marquer les thèmes nouveaux / en hausse / en baisse plutôt que repartir de zéro.
- **Demande de pourcentage « sur tous les utilisateurs »** : expliquer pourquoi le corpus ne le permet pas et proposer ce qu'il faudrait (enquête quantitative, analytics produit) pour le mesurer.
- **L'utilisateur demande des idées de solution ou des opportunités** : les proposer comme hypothèses à tester, une ou deux directions par problème choisi, avec ce que chacune parie. Hors demande, rester sur les problèmes.