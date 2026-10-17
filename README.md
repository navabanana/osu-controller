# DualSense pour osu!

Utilise le pavé tactile de ta manette **PS5 (DualSense)** comme une **tablette graphique** pour jouer à osu! sur Windows.

- Le pavé tactile déplace le curseur en position absolue, comme une tablette.
- Les boutons de la manette envoient les touches Z et X.
- Un petit programme avec fenêtre, qu'on peut compiler en `.exe`.

## Commandes

| Action sur la manette | Effet |
|---|---|
| Pavé tactile (un doigt) | Position du curseur |
| Clic du pavé tactile | Clic gauche |
| L1, Croix ou L2 | Touche **Z** |
| R1, Rond ou R2 | Touche **X** |
| Options | Active / désactive le contrôle |

La fenêtre propose un curseur « Zone du pavé utilisée » (30 à 100 %, 60 % par défaut). Plus la zone est petite, plus le curseur va vite pour un même geste.

## Installation

### Option 1 : créer le .exe

1. Installe [Python 3](https://www.python.org/downloads/) en cochant **Add python.exe to PATH**.
2. Double-clique sur `creer_exe.bat`.
3. Récupère `dist\DualSenseOsu.exe`.

### Option 2 : lancer avec Python

```bat
pip install -r requirements.txt
python dualsense_osu.py
```

## Réglages dans osu!

- **Options > Input > Raw input : désactivé**, sinon le jeu ignore le curseur contrôlé par le programme.
- **Confine mouse cursor** : « Jamais » (ou « Plein écran seulement »).
- Ferme **DS4Windows** et **Steam Input** s'ils sont ouverts, car ils peuvent prendre la manette avant le programme.

## Connexion

La manette fonctionne en **USB** et en **Bluetooth**. Le Bluetooth est moins testé : en cas de souci, essaie en USB.

## Limites

- Windows uniquement.
- Le pavé fait 1920 × 1080 points : c'est jouable, mais moins précis qu'une vraie tablette.
- Il n'y a pas de détection de pression sur le pavé tactile de la DualSense.
- Seul le premier doigt est pris en compte.

## Comment ça marche

Le programme lit les rapports HID de la manette avec `hidapi` : position des doigts, boutons et gâchettes. Il envoie ensuite des événements souris (position absolue) et clavier (codes de touche matériels) à Windows avec `SendInput`.

