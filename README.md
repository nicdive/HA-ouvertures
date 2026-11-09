# Gestion des ouvertures (Home Assistant)

Module Home Assistant pour centraliser baies vitrées, portes, portail coulissant, porte de garage sectionnelle et volet de piscine — avec les visuels inspirés de Jeedom.

## Fonctionnalités

| Type | Capteur ouverture | Capteur volet | Commandes |
|------|-------------------|---------------|-----------|
| **Baie vitrée** | Oui | Oui (cover / binary) | — (4 images d’état) |
| **Porte simple** | Oui | — | — |
| **Portail coulissant** | Oui | — | Ouvrir · Fermer · Impulsion |
| **Garage sectionnelle** | Oui | — | Impulsion |
| **Volet piscine** | Oui | — | — |

Chaque ouverture crée :

- un **capteur État** (texte + image + attributs pour la carte)
- un **binary_sensor Ouvert**
- des **boutons** de commande (portail / garage)

## Installation

### HACS (recommandé)

1. HACS → Intégrations → Menu → *Dépôts personnalisés*
2. Ajouter l’URL du dépôt en type **Integration**
3. Installer **Gestion des ouvertures**
4. Redémarrer Home Assistant

### Manuelle

1. Copier `custom_components/ouvertures` dans votre dossier `config/custom_components/`
2. Redémarrer Home Assistant

La carte Lovelace `custom:ouvertures-card` et les images SVG sont enregistrées automatiquement (`/ouvertures_static/...`).

## Configuration

1. **Paramètres → Appareils et services → Ajouter une intégration → Gestion des ouvertures**
2. Choisir le **type** et le **nom**
3. Sélectionner les entités demandées :
   - Baie : capteur baie + capteur/cover volet
   - Porte / piscine : capteur d’ouverture
   - Portail : capteur + action ouvrir + fermer + impulsion
   - Garage : capteur + bouton impulsionnel

Option **Inverser le capteur** si votre contact est à l’envers (`on` = fermé).

Vous pouvez ajouter **autant d’ouvertures** que nécessaire (une entrée par baie / porte / …).

## Tableau de bord

Exemple prêt à l’emploi : [`dashboards/ouvertures.yaml`](dashboards/ouvertures.yaml).

Carte seule :

```yaml
type: custom:ouvertures-card
entity: sensor.baie_salon_etat
```

Grille (dashboard dédié) :

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

Les boutons **Ouvrir / Fermer / Impulsion** apparaissent automatiquement sur portail et garage.

## Baie vitrée — 4 états

| État | Visuel |
|------|--------|
| Baie fermée · Volets ouverts | Vitres bleues, volets sur les côtés |
| Baie ouverte · Volets ouverts | Ouverture sombre + flèches |
| Baie fermée · Volets fermés | Lames blanches + cadenas |
| Baie ouverte · Volets fermés | Alerte « BAIE OUVERTE » |

## Structure

```
custom_components/ouvertures/
  __init__.py          # static + carte Lovelace
  config_flow.py       # UI de configuration
  sensor.py            # état combiné
  binary_sensor.py     # ouvert / fermé
  button.py            # commandes
  www/
    ouvertures-card.js
    img/               # SVG (baies, portes, portail, garage, piscine)
dashboards/ouvertures.yaml
```

## Notes

- Compatible `binary_sensor`, `cover`, `sensor`, `switch`, `button`, `script`…
- Le message d’origine mentionnait aussi « De plus, il me faudra… » (coupé) : précisez la suite pour l’ajouter (notifications, historique, alarme, etc.).
