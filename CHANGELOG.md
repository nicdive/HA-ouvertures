## [1.5.0] - 2026-11-10

### Ajouté

- Type **Porte d'entrée** (arche pierre, battant asymétrique + vitre latérale)

### Changé

- Vignettes réalistes d’après photos : **portail coulissant**, **garage sectionnelle**
  (anthracite 3×4), **porte d'entrée**, **porte garage simple** (2 arcs + 2 panneaux)
- Libellé « Porte simple » → **Porte garage simple**

## 1.4.1

- Porte simple ouverte : battant charnière gauche, sans flèche/texte
- Garage sectionnelle ouverte : panneaux pleine largeur empilés en haut

# Changelog

Toutes les versions notables de **Gestion des ouvertures**.

Le format s’inspire de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
et le projet suit le [Semantic Versioning](https://semver.org/lang/fr/).

## [1.4.0] - 2026-11-10

### Changé

- Visuel **porte simple** ouverte : battant sur charnière, sans flèche / bandeau texte
- Visuel **garage sectionnelle** : fermée pleine ; ouverte = panneaux au plafond dans
  l’ouverture (plus de pyramide bizarre)

## [1.3.9] - 2026-11-10

### Changé

- (remplacé en 1.4.0) essai visuel garage sectionnelle

## [1.3.8] - 2026-11-10

### Changé

- Boutons **Ouvrir / Fermer / Impulsion** nettement plus gros (surtout iPhone)

## [1.3.7] - 2026-11-10

### Corrigé

- Portail coulissant : nouveaux fichiers SVG + `?v=` sur les images pour casser le
  cache navigateur (l’ancien double battant ne doit plus s’afficher)

## [1.3.6] - 2026-11-10

### Changé

- Visuel **portail coulissant** : un vantail large sur rail (plus de double battant),
  clairement décalé latéralement à l’ouverture

## [1.3.5] - 2026-11-10

### Changé

- Visuel **volet piscine** : bassin réaliste avec **volet roulant immergé**
  (banquette + axe, lamelles déployées / enroulées)

## [1.3.4] - 2026-11-10

### Corrigé

- Sensors numériques (`0.0` / `1.0`, xPL / remote HA) correctement lus
  (plus d’état « inconnu »)
- Si **0.0 = ouvert** : cocher **Inverser le capteur**

## [1.3.3] - 2026-11-10

### Clarifié

- Binary_sensor / contact `0`/`1` : par défaut `1`=ouvert ; si **0=ouvert**, cocher
  **Inverser le capteur**
- Libellés d’aide mis à jour dans le flux de config

## [1.3.2] - 2026-11-09

### Changé

- Visuel porte-fenêtre 3 battants : **plus large**, volet qui descend **depuis au-dessus
  de l’arrondi**, seul le **battant du milieu** s’ouvre

## [1.3.1] - 2026-11-09

### Changé

- Porte-fenêtre 3 battants : le volet roulant se lie à une **entité cover** uniquement
  (état / position du volet, pas un binary_sensor)

## [1.3.0] - 2026-11-09

### Ajouté

- Type **porte-fenêtre 3 battants** (haut arrondi + **volet roulant**), 4 états

## [1.2.1] - 2026-11-09

### Changé

- Visuel **fenêtre double battant** plus bas (moins « baie vitrée »)

## [1.2.0] - 2026-11-09

### Ajouté

- Types **fenêtre simple battant** et **fenêtre double battant**
- Variantes **avec volets** (4 états) ou **sans volets** (ouvert / fermé)
- Visuels SVG dédiés pour chaque combinaison

## [1.1.5] - 2026-11-09

### Changé

- Grille **dense 3×n sur mobile** (4 colonnes tablette/desktop) pour voir beaucoup
  plus d’ouvertures à l’écran
- Dashboard : une carte compacte par pièce (chaque ouverture = une petite tuile)

## [1.1.4] - 2026-11-09

### Changé

- Tableau de bord organisé **par pièce** (chaque ouverture séparée)

## [1.1.3] - 2026-11-09

### Ajouté

- (corrigé en 1.1.4) tentative de regroupement dans la carte

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

[1.4.0]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.4.0
[1.3.9]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.3.9
[1.3.8]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.3.8
[1.3.7]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.3.7
[1.3.6]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.3.6
[1.3.5]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.3.5
[1.3.4]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.3.4
[1.3.3]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.3.3
[1.3.2]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.3.2
[1.3.1]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.3.1
[1.3.0]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.3.0
[1.2.1]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.2.1
[1.2.0]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.2.0
[1.1.5]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.1.5
[1.1.4]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.1.4
[1.1.3]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.1.3
[1.1.2]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.1.2
[1.1.1]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.1.1
[1.1.0]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.1.0
[1.0.0]: https://github.com/nicdive/HA-ouvertures/releases/tag/1.0.0
