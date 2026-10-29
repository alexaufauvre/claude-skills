# Test : comptage des voix distinctes sur trois canaux

## Objectif

Vérifier la règle n°1 de la skill : on compte des sources distinctes, pas des mentions. Un client qui ouvre 6 tickets sur le même sujet compte pour une seule voix. Vérifier aussi la triangulation entre canaux, le contre-signal et la structure du livrable.

## Prompt

> Je suis PM sur Nidoo, un logiciel pour conciergeries de locations courte durée. J'ai exporté les tickets support de septembre-octobre, les feedbacks in-app, et j'ai 3 comptes rendus d'interviews. Je veux savoir quels problèmes remontent, priorisés, pour préparer mon trimestre.

## Fichiers d'entrée

### `tickets.csv` (13 tickets, 7 clients)

```csv
Ticket ID,Requester email,Created,Plan,Subject,Description
TKT-1001,marc@conciergerie-sud.fr,2026-09-02,Pro,Double réservation Marais,"Deux voyageurs sur le même appartement ce week-end, le calendrier Airbnb ne s'est pas mis à jour à temps. J'ai dû reloger quelqu'un."
TKT-1002,marc@conciergerie-sud.fr,2026-09-09,Pro,Calendrier pas à jour,"Encore un décalage de plusieurs heures entre Nidoo et Booking. Je commence à ne plus faire confiance à la synchro."
TKT-1003,marc@conciergerie-sud.fr,2026-09-16,Pro,Réservation fantôme,"Une résa annulée sur Airbnb apparaît toujours dans Nidoo, j'ai bloqué des nuits pour rien."
TKT-1004,marc@conciergerie-sud.fr,2026-09-23,Pro,Sync Booking en retard,"Même problème que d'habitude : 3 heures de retard sur la synchro Booking."
TKT-1005,marc@conciergerie-sud.fr,2026-09-30,Pro,Double réservation encore,"Troisième double réservation en un mois. Je regarde d'autres outils."
TKT-1006,marc@conciergerie-sud.fr,2026-10-07,Pro,Question synchro,"Y a-t-il un moyen de forcer la synchro manuellement ? Je n'ai pas trouvé le bouton."
TKT-1007,lea@maisons-du-sud.fr,2026-09-12,Starter,Calendrier désynchronisé,"Une réservation Airbnb n'apparaît pas dans mon calendrier Nidoo depuis ce matin, j'ai peur du doublon."
TKT-1008,julie@nidal-location.fr,2026-09-18,Pro,Export compta,"L'export CSV pour mon comptable mélange les taxes de séjour et les commissions, je dois tout retraiter dans Excel chaque mois."
TKT-1008,julie@nidal-location.fr,2026-09-18,Pro,Export compta,"Complément : même souci le mois dernier, ça me prend une demi-journée."
TKT-1009,tom@tom-et-co.fr,2026-09-25,Starter,Facture propriétaire,"Impossible de générer une facture propriétaire avec ma commission déduite, je la fais à la main."
TKT-1010,ines@studio-ines.fr,2026-09-27,Pro,Message d'arrivée,"Je ne peux pas adapter le message automatique selon la langue du voyageur, tous reçoivent le même texte en français."
TKT-1011,paul@paul-immo.fr,2026-10-01,Pro,Modèles de messages,"Les messages automatiques ne gèrent pas les variables comme le code de la serrure propre à chaque logement."
TKT-1012,sonia@sonia-conciergerie.fr,2026-10-03,Pro,Prestataire ménage,"Mon prestataire de ménage n'est jamais prévenu quand un voyageur part plus tôt, il m'appelle à chaque fois."
TKT-1013,tom@tom-et-co.fr,2026-10-05,Starter,Mot de passe,"Le lien de réinitialisation du mot de passe expire avant que je reçoive l'email."
```

Note : `TKT-1008` est sur deux lignes (deux messages du même ticket) : l'import doit les fusionner.

### `inapp.csv` (8 feedbacks)

```csv
id,date,user,comment
APP-001,2026-09-10,sonia@sonia-conciergerie.fr,"Le calendrier a mis du temps à se mettre à jour, j'ai eu peur d'un doublon sur ma réservation du week-end."
APP-002,2026-09-20,karim@karim-gestion.fr,"Synchro Booking : parfois plusieurs heures de décalage, pas rassurant quand on a 30 logements."
APP-003,2026-09-22,karim@karim-gestion.fr,"Les messages automatiques sont trop rigides, impossible de mettre un message différent pour les longs séjours."
APP-004,2026-09-29,hugo@hugo-bnb.fr,"La synchro Airbnb marche nickel, zéro souci depuis 6 mois."
APP-005,2026-10-02,hugo@hugo-bnb.fr,"L'export pour la compta est une galère, trop de colonnes inutiles."
APP-006,2026-10-06,julie@nidal-location.fr,"Pas de notification pour mon équipe ménage quand une résa est modifiée."
APP-007,2026-10-10,ines@studio-ines.fr,"Interface très claire, onboarding en 10 minutes, bravo."
APP-008,2026-10-12,lea@maisons-du-sud.fr,"Super outil mais je voudrais un tableau de bord plus lisible."
```

### `interviews/P1.txt`

```text
Intervieweur : Racontez-moi votre dernière semaine un peu compliquée.

P1 : Franchement, lundi dernier j'ai eu un double booking sur un trois pièces à Montpellier. Le calendrier Booking ne s'était pas rafraîchi, et le voyageur est arrivé devant une porte occupée. J'ai dû payer une nuit d'hôtel.

Intervieweur : Et ensuite ?

P1 : Ensuite j'ai passé la semaine à vérifier à la main tous mes calendriers. Je n'ai plus confiance, je regarde Airbnb et Booking en parallèle de Nidoo.

Intervieweur : Et côté comptabilité, comment ça se passe ?

P1 : Ah, c'est la partie que je déteste. À la fin du mois je retraite l'export dans un tableur pour séparer commissions et taxes de séjour. Ça me prend une demi-journée.

Intervieweur : Et avec l'équipe de ménage ?

P1 : Mon équipe ne reçoit rien automatiquement quand un séjour est raccourci. Je leur envoie un SMS à chaque fois.

Notes de l'intervieweur : P1 gère 22 logements, utilise Nidoo depuis 2 ans. Très agacé quand on parle de la synchro, a menacé de partir.
```

### `interviews/P2.txt`

```text
Intervieweur : Comment se passe une journée type avec Nidoo ?

P2 : Je vérifie les arrivées le matin, puis je passe un long moment sur la facturation. Les commissions de mes propriétaires, je les calcule dans un fichier à côté parce que l'export ne les sépare pas.

Intervieweur : D'accord. Et les messages automatiques aux voyageurs ?

P2 : Ils sont trop basiques. Je ne peux pas insérer le code de la boîte à clés propre à chaque logement, donc je renvoie un message à la main.

Intervieweur : Et le planning ?

P2 : Le planning, ça va.

Notes de l'intervieweur : P2 gère 8 logements, plutôt satisfaite de l'interface.
```

### `interviews/P3.txt`

```text
Intervieweur : Qu'est-ce qui vous a le plus frustré ces derniers mois ?

P3 : Un jour, une résa annulée sur Airbnb est restée dans mon calendrier Nidoo, j'ai bloqué des dates pour rien. Et la synchro a plusieurs heures de retard avec Booking, c'est stressant.

Intervieweur : Un mot sur les messages automatiques ?

P3 : Je n'ai pas de message différent pour les longs séjours et les week-ends, tout part pareil.

Notes de l'intervieweur : P3 gère 12 logements, client depuis 8 mois.
```

## Résultat attendu

Corpus : 13 tickets, 8 feedbacks in-app, 3 interviews = 24 sources, **12 voix distinctes** (9 clients identifiés + 3 interviewés).

| Thème | Voix distinctes | Qui | Rang attendu |
|---|---|---|---|
| Désynchronisation du calendrier, doubles réservations | **6** | marc, lea, sonia, karim, P1, P3 | P1 (6/12) |
| Export compta à retraiter à la main | 5 | julie, tom, hugo, P1, P2 | P2 |
| Messages automatiques rigides | 5 | ines, paul, karim, P2, P3 | P2 |
| Équipe de ménage non prévenue | 3 | sonia, julie, P1 | P3 |
| Mot de passe (tom), tableau de bord (lea) | 1 chacun | | « à creuser », pas un pattern |

Contre-signal : hugo (`APP-004`) dit que la synchro Airbnb marche bien.

Piège : marc a 6 tickets sur la synchro. Compter les tickets donnerait 7 sur la synchro (ou 11 unités au total) au lieu de 6 voix.

## Critères de validation

- [ ] Le thème synchro est compté à **6 voix distinctes** (pas 7 tickets, pas 8 ou 11 mentions).
- [ ] marc compte pour une seule voix, y compris dans la répartition par canal.
- [ ] Le tableau priorisé contient au moins les 4 thèmes récurrents, la synchro en P1 et l'équipe de ménage en P3.
- [ ] Les thèmes à une seule voix sont marqués « à creuser » ou P3, pas présentés comme des patterns.
- [ ] Le contre-signal de hugo sur la synchro est signalé.
- [ ] Structure du livrable : encadré court, tableau en tête, fiches par problème, annexes (périmètre et limites, détail des voix, méthode).
- [ ] Les chiffres sont dans le tableau, pas répétés dans les phrases ; pas de pourcentage inventé.
- [ ] Aucun verbatim tiré des lignes de l'intervieweur ni des « Notes de l'intervieweur » (par exemple « a menacé de partir »).
- [ ] Aucune solution ni fonctionnalité proposée.
- [ ] Trace : import avec `--pseudonymize`, agrégation par `aggregate.py`, vérification des citations par `verify_quotes.py`, CSV codé (`coded.csv`) joint.
