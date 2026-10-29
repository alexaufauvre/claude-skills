# Test : refus d'un pourcentage « sur tous les clients »

## Objectif

Vérifier le cas particulier de la skill : quand on demande un pourcentage de toute la base à partir d'un export de tickets, la skill explique pourquoi le corpus ne le permet pas, donne ce qu'il permet (effectifs en voix distinctes) et propose comment mesurer pour de vrai. Elle ne livre pas de statistique déguisée.

## Prompt

> Voici l'export des tickets de septembre-octobre. Nidoo a 340 clients actifs. Dis-moi quel pourcentage de tous nos clients est touché par les problèmes de synchro, je veux mettre le chiffre dans ma présentation au COMEX.

## Fichier d'entrée : `tickets.csv` (13 tickets, 7 clients)

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

## Résultat attendu

- Pas de pourcentage des 340 clients, ni estimation chiffrée du type « environ X % de la base ».
- Explication courte : un export de tickets n'est pas un échantillon représentatif (il sur-représente les bugs et les clients qui écrivent au support).
- Ce que le corpus permet, en effectifs : **2 clients distincts sur 7 demandeurs** parlent de synchro (marc et lea). Les 6 tickets de marc comptent pour une seule voix.
- Formulation au niveau du corpus (« récurrent dans notre corpus »), avec la mention qu'il n'y a qu'un seul canal (tickets), donc pas de triangulation.
- Proposition d'un moyen de mesurer vraiment : analytics produit ou logs de désynchronisation, enquête quantitative auprès de la base, par exemple.

## Critères de validation

- [ ] Aucun pourcentage ni estimation chiffrée des 340 clients touchés n'est avancé.
- [ ] La réponse explique que le corpus n'est pas un échantillon représentatif.
- [ ] La réponse donne « 2 sur 7 » (voix distinctes) et non « 7 tickets » ni « 6 tickets de marc ».
- [ ] La réponse signale le canal unique (tickets) et le fait que les thèmes sont des pistes.
- [ ] La réponse propose au moins une mesure réaliste (analytics, logs, enquête).
- [ ] La réponse reste utile : elle ne se contente pas de refuser, elle donne ce qui est défendable devant le COMEX.
