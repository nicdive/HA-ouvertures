# Gestion des ouvertures

Module Home Assistant pour centraliser baies vitrées, portes-fenêtres (3 battants, haut arrondi + volet roulant), fenêtres (simple / double battant, avec ou sans volets), portes, portail coulissant, porte de garage sectionnelle et volet de piscine — avec les visuels inspirés de Jeedom.

![Version](https://img.shields.io/github/v/release/nicdive/HA-ouvertures?style=flat-square)
![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)
![HA](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg?style=flat-square)

<!-- ha-marketplace:exclude-start -->

## Installation

### Marketplace / HACS (recommandé)

[![Ouvrir dans Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=nicdive&repository=HA-ouvertures&category=integration)

1. HACS / Marketplace → menu → **Dépôts personnalisés**
2. Ajouter `https://github.com/nicdive/HA-ouvertures` en type **Integration**
3. Rechercher **Gestion des ouvertures** → **Télécharger**
4. Redémarrer Home Assistant
5. Paramètres → Appareils et services → **Ajouter une intégration** → *Gestion des ouvertures*

[![Configurer l’intégration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ouvertures)

> Après publication d’une release GitHub (`1.0.0`, …), le Marketplace propose les mises à jour automatiquement.

Voir aussi [`docs/MARKETPLACE.md`](docs/MARKETPLACE.md) pour la checklist de publication.

### Manuelle

1. Télécharger la [dernière release](https://github.com/nicdive/HA-ouvertures/releases/latest)
2. Copier `custom_components/ouvertures` dans `config/custom_components/`
3. Redémarrer Home Assistant

La carte Lovelace `custom:ouvertures-card` et les images SVG sont enregistrées automatiquement (`/ouvertures_static/...`).

<!-- ha-marketplace:exclude-end -->

## Fonctionnalités

| Type | Capteur ouverture | Capteur volet | Commandes |
|------|-------------------|---------------|-----------|
| **Baie vitrée** | Oui | Oui (cover / binary) | — (4 images d’état) |
| **Fenêtre simple battant** | Oui | — | — |
| **Fenêtre simple + volets** | Oui | Oui | — (4 images d’état) |
| **Fenêtre double battant** | Oui | — | — |
| **Fenêtre double + volets** | Oui | Oui | — (4 images d’état) |
| **Porte-fenêtre 3 battants** | Oui | Oui (**cover** volet roulant) | — (haut arrondi, 4 états) |
| **Porte simple** | Oui | — | — |
| **Portail coulissant** | Oui | — | Ouvrir · Fermer · Impulsion |
| **Garage sectionnelle** | Oui | — | Impulsion |
| **Volet piscine** | Oui | — | — |

Chaque ouverture crée :

- un **capteur État** (texte + image + attributs pour la carte)
- un **binary_sensor Ouvert**
- des **boutons** de commande (portail / garage)

## Configuration

1. **Paramètres → Appareils et services → Ajouter une intégration → Gestion des ouvertures**
2. Choisir le **type** et le **nom**
3. Sélectionner les entités demandées :
   - Baie / fenêtre + volets : capteur ouverture + capteur/cover volet
   - Porte-fenêtre 3 battants : capteur ouverture + **entité cover** du volet roulant
   - Fenêtre sans volets / porte / piscine : capteur d’ouverture
   - Portail : capteur + action ouvrir + fermer + impulsion
   - Garage : capteur + bouton impulsionnel

Les **binary_sensor** sont supportés. Convention par défaut : `on` / `1` = ouvert, `off` / `0` = fermé.

Si ton contact est inversé (**0 = ouvert**, **1 = fermé**), coche **Inverser le capteur** à la config (ou dans les options de l’entrée).

Vous pouvez ajouter **autant d’ouvertures** que nécessaire (une entrée par baie / porte / …).

Assignez une **pièce** (area) à chaque capteur/appareil
(**Paramètres → Appareils → Pièce**). Le tableau de bord auto se structure alors :

- section **Salon** → grille dense des ouvertures de cette pièce  
- section **Cuisine** → …  
- chaque ouverture reste une **tuile séparée** (≈ 3 colonnes sur iPhone)

## Tableau de bord

Un tableau de bord **Ouvertures** est créé **automatiquement** dans la barre latérale (`/ha-ouvertures`) dès qu’au moins un ouvrant est configuré. Il se met à jour quand vous ajoutez ou supprimez une ouverture.

Vous pouvez aussi utiliser la carte manuellement :

```yaml
type: custom:ouvertures-card
title: Ouvertures
entities:
  - sensor.baie_salon_etat
  - sensor.porte_entree_etat
  - sensor.portail_etat
  - sensor.garage_etat
  - sensor.volet_piscine_etat
```

> Les modifications manuelles de ce dashboard peuvent être écrasées lors d’un ajout/suppression d’ouvrant (dashboard géré par l’intégration).

### Carte absente du sélecteur ?

1. Vérifier **Paramètres → Tableaux de bord → Ressources** :  
   `/ouvertures_static/ouvertures-card.js` (type **JavaScript module**)
2. Recharger le frontend (Ctrl+F5) ou redémarrer HA
3. Chercher **Ouvertures** dans « Parcourir » / custom cards

## Baie vitrée — 4 états

| État | Visuel |
|------|--------|
| Baie fermée · Volets ouverts | Vitres bleues, volets sur les côtés |
| Baie ouverte · Volets ouverts | Ouverture sombre + flèches |
| Baie fermée · Volets fermés | Lames blanches + cadenas |
| Baie ouverte · Volets fermés | Alerte « BAIE OUVERTE » |

## Versioning

- Semantic Versioning (`MAJOR.MINOR.PATCH`)
- La version dans `custom_components/ouvertures/manifest.json` **doit** correspondre au tag de release GitHub (ex. `1.0.0`)
- Historique : [`CHANGELOG.md`](CHANGELOG.md)

## Structure

```
custom_components/ouvertures/
  brand/                 # icônes Marketplace (icon 256 / 512)
  manifest.json          # version + métadonnées HA
  www/                   # carte Lovelace + SVG
hacs.json
CHANGELOG.md
```

## Licence

Usage personnel / partage via le dépôt GitHub `nicdive/HA-ouvertures`.
