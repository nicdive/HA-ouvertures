# Changelog

Toutes les versions notables de **Gestion des ouvertures**.

Le format s’inspire de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
et le projet suit le [Semantic Versioning](https://semver.org/lang/fr/).

## [1.1.3] - 2026-11-09

### Ajouté

- La carte range automatiquement les tuiles **par pièce** (titres de groupe)

## [1.1.2] - 2026-11-09

### Ajouté

- Affichage de la **pièce** (area HA) en titre sur chaque tuile
- Dashboard regroupé par pièce quand les areas sont renseignées

## [1.1.1] - 2026-11-09

### Corrigé

- Plus de clignotement du visuel baie : la carte ne reconstruit le DOM / l’image
  que si l’état utile change ; debounce côté capteur (updates cover)

## [1.1.0] - 2026-11-09

### Ajouté

- Tableau de bord Lovelace **Ouvertures** créé automatiquement (`/ha-ouvertures`)
- Mise à jour auto à l’ajout / suppression / modification d’un ouvrant
- Suppression du dashboard quand plus aucune ouverture n’est configurée
- Enregistrement de la carte comme **ressource Lovelace** (module)

### Corrigé

- La carte `custom:ouvertures-card` apparaît dans le sélecteur de cartes
  (ne plante plus sur la config stub vide)

## [1.0.0] - 2026-11-09

### Ajouté

- Intégration Home Assistant avec config flow (UI)
- Types : baie vitrée, porte simple, portail coulissant, garage sectionnelle, volet piscine
- Capteur d’état combiné + binary_sensor « Ouvert »
- Boutons Ouvrir / Fermer / Impulsion (portail) et Impulsion (garage)
- Carte Lovelace `custom:ouvertures-card` (enregistrement automatique)
- Visuels SVG (baies Jeedom + porte / portail / garage / piscine)
- Assets brand (`brand/icon.png`, logo) pour le Marketplace
- Exemple de tableau de bord (`dashboards/ouvertures.yaml`)

[1.1.3]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.1.3
[1.1.2]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.1.2
[1.1.1]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.1.1
[1.1.0]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.1.0
[1.0.0]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.0.0
