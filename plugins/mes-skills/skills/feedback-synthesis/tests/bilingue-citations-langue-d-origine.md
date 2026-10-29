# Test : corpus bilingue, citations dans la langue d'origine

## Objectif

Vérifier que la skill regroupe des feedbacks français et anglais dans les mêmes thèmes, rédige la synthèse en français, et cite chaque verbatim dans sa langue d'origine, sans le traduire.

## Prompt

> Voici les feedbacks in-app d'octobre, certains en anglais, d'autres en français. Fais-moi la synthèse des problèmes, en français.

## Fichier d'entrée : `mixed.csv`

```csv
id,date,user,comment
APP-M01,2026-10-01,u01@example.com,"Le calendrier ne se met pas à jour assez vite, j'ai eu un doublon ce week-end."
APP-M02,2026-10-02,u02@example.com,"Calendar sync is hours behind Booking.com, I almost double booked a guest."
APP-M03,2026-10-03,u03@example.com,"Sync with Airbnb drops reservations sometimes. I no longer trust it."
APP-M04,2026-10-04,u04@example.com,"La synchro Booking a plusieurs heures de retard."
APP-M05,2026-10-05,u05@example.com,"The accounting export mixes tourist tax and commissions, I fix it in Excel every month."
APP-M06,2026-10-06,u06@example.com,"Export compta inutilisable tel quel, il faut tout retraiter."
APP-M07,2026-10-07,u07@example.com,"Automatic messages can't use per-property variables like the lockbox code."
APP-M08,2026-10-08,u08@example.com,"Impossible de personnaliser les messages automatiques selon la langue du voyageur."
APP-M09,2026-10-09,u09@example.com,"Love the clean interface, onboarding took ten minutes."
APP-M10,2026-10-10,u10@example.com,"Vraiment content de l'outil, rien à redire sur l'interface."
```

## Résultat attendu

10 feedbacks, 10 utilisateurs distincts, 4 en anglais et 6 en français. Un seul canal (in-app).

| Thème (en français) | Voix distinctes | Dont EN | Dont FR |
|---|---|---|---|
| Synchro en retard ou qui perd des réservations | 4 | 2 (u02, u03) | 2 (u01, u04) |
| Export compta à retraiter à la main | 2 | 1 (u05) | 1 (u06) |
| Messages automatiques non personnalisables | 2 | 1 (u07) | 1 (u08) |
| Compliments sur l'interface (u09, u10) | hors problèmes | | |

## Critères de validation

- [ ] Les voix anglaises et françaises sont regroupées dans les mêmes thèmes (pas de thème « EN » séparé).
- [ ] Les comptes sont : synchro 4, export compta 2, messages automatiques 2.
- [ ] Les noms de thèmes, phrases de problème, tableau et annexes sont en français.
- [ ] Les verbatims issus des feedbacks anglais sont cités en anglais, identiques à `mixed.csv`, sans traduction entre guillemets.
- [ ] Les verbatims français restent en français, copiés tels quels, avec leur source (`APP-M01`…).
- [ ] Les deux compliments ne sont pas présentés comme un problème prioritaire.
- [ ] Le livrable signale qu'il n'y a qu'un seul canal (pas de triangulation, thèmes = pistes).
- [ ] La vérification des citations (`verify_quotes.py`) a été faite, ou son absence est dite explicitement.
