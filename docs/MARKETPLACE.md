# Publier sur le Marketplace Home Assistant

Checklist pour que **Gestion des ouvertures** soit installable via le Marketplace / HACS.

## Déjà en place dans le dépôt

- [x] `hacs.json` à la racine (`name`, `homeassistant`, `hide_default_branch`)
- [x] `custom_components/ouvertures/` (une seule intégration)
- [x] `manifest.json` avec `domain`, `name`, `version`, `documentation`, `issue_tracker`, `codeowners`
- [x] `brand/icon.png` (256×256) + `icon@2x.png` (512×512) + logos
- [x] `README.md` (section install masquée côté Marketplace via `ha-marketplace:exclude-*`)
- [x] `CHANGELOG.md` + workflows CI (`validate.yml`, `release.yml`)
- [x] Version `1.0.0` dans le manifest

## À faire sur GitHub (compte propriétaire)

Le token de l’agent n’a pas les droits d’écriture sur les réglages du dépôt.

1. **Description** du dépôt, par ex. :
   `Gestion des ouvertures Home Assistant (baies, portes, portail, garage, piscine)`
2. **Topics** : `home-assistant`, `hacs`, `marketplace`, `custom-component`, `integration`
3. **Issues** activées
4. Fusionner la PR sur `main`
5. Créer la **release** `1.0.0` (tag = version du manifest) :

```bash
git checkout main
git pull
git tag 1.0.0
git push origin 1.0.0
# le workflow Release publie la GitHub Release automatiquement
# ou manuellement :
gh release create 1.0.0 --title "1.0.0" --notes-file CHANGELOG.md
```

## Installation utilisateur (dès la release)

```
https://my.home-assistant.io/redirect/hacs_repository/?owner=nicdive&repository=HA-ouvertures&category=integration
```

Ou Marketplace / HACS → dépôt personnalisé → URL du dépôt → type Integration.

## Catalogue officiel

Pour apparaître dans le catalogue sans dépôt personnalisé, suivre les consignes du [Marketplace](https://contributors.home-assistant.io/marketplace/) / HACS default (soumission de dépôt). Les releases GitHub restent obligatoires.
