# claude-skills

Marketplace de plugins Claude Code personnelle : elle versionne mes skills Claude et les rend installables sur n'importe quelle machine.

## Installation sur une autre machine

Dans Claude Code :

```
/plugin marketplace add alexaufauvre/claude-skills
/plugin install mes-skills@claude-skills
```

(Le repo est privé : `gh auth login` ou un accès git configuré est nécessaire sur la machine.)

## Ajouter une nouvelle skill

1. Créer `plugins/mes-skills/skills/<nom>/SKILL.md` (nom en kebab-case, identique au dossier, avec un frontmatter `name:` et `description:`).
2. Bumper la version dans `plugins/mes-skills/.claude-plugin/plugin.json` **et** dans `.claude-plugin/marketplace.json`.
3. Ajouter la skill au tableau ci-dessous.
4. `git commit` + `git push`.
5. Sur chaque machine : `/plugin marketplace update claude-skills`.

## Skills du plugin `mes-skills`

| Skill | Description |
|-------|-------------|
| `exemple-skill` | Skill d'exemple à remplacer. |
