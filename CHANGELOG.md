# Changelog

Toutes les versions notables de **Gestion des ouvertures**.

Le format s’inspire de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
et le projet suit le [Semantic Versioning](https://semver.org/lang/fr/).

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

[1.1.0]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.1.0
[1.0.0]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.0.0
