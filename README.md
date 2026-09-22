# Classic Pool

A billiards game for Mac, Windows and Linux, written in Python with pygame.
Nine disciplines, a computer opponent with six levels, tournaments, 55 cues
and a full set of tables, cloths and ball sets.

## Requirements

- Python 3
- [pygame](https://www.pygame.org) 2
- [numpy](https://numpy.org) (recommended: ball rendering and sound need it)

## Install

```
git clone https://github.com/JonaDev2026/Classic-Pool.git
cd Classic-Pool
python3 -m pip install pygame numpy
```

On Windows use `py` instead of `python3`.

## Play

```
python3 golden_break.py
```

Your settings, wallet, cues and the tournament in progress are saved in
your user data folder, not in the game folder:

- Windows: `%APPDATA%\ClassicPool`
- macOS: `~/Library/Application Support/ClassicPool`
- Linux: `~/.local/share/ClassicPool`

## Controls

You can play with the mouse, the keyboard or a controller (Settings >
Controls). Keyboard keys can be remapped.

**Mouse**

- Aim: move the mouse
- Shoot: hold the left button and drag back to build power, release to shoot
- Ball in hand: move and click to place the cue ball
- Russian Pyramid: right click to choose the striking ball

**Keyboard (default keys)**

| Action | Key |
|---|---|
| Aim left / right | Left / Right |
| Fine aim (hold) | Left Shift |
| Shoot (hold to build power) | Space |
| Ball in hand up / down | Up / Down |
| Spin top / back / left / right | W / S / A / D |
| Clear spin | E |
| Change ball (Pyramid) | C |

**Controller**

Left stick to aim, LB for fine aim, A or RT held to shoot, right stick for
spin, Y to clear spin, X to change ball in the Pyramid, START to pause.
Menus work with the D-pad, A to select and B to go back.

**Always**

- ESC: pause at the table, exit from the menu
- F11: fullscreen

## What's in the game

**Disciplines**, grouped by category:

- Pool: 8-Ball, 9-Ball, 10-Ball, Blackball, Russian Pyramid
- Snooker: Snooker, 6-Red Snooker
- Pins: 5-Pins, Goriziana

Each one follows its own rules: fouls, ball in hand, free ball and miss in
snooker, colour respotting, pins and scores. The Rules menu explains every
discipline.

**Game modes**

- Multiplayer: two players on the same computer
- Vs Computer: six levels, from Beginner to Champion. The computer
  simulates its shots, plays combinations and knows the rules of each
  discipline
- Tournament: one tournament per discipline, 64 players, best of 3 frames,
  with bracket, crest and trophy. The tournament is saved after every frame

**Table and graphics**

- 55 cues, from plain wood to carbon, metal and legendary designs
- Ball sets for every type of game (pool, snooker, pins, blackball, pyramid)
- Different cloths and rails, classic or modern crests, player flags
- Resolution and fullscreen / window

**Sound**

- Impact sounds graded by strength: cue, balls, rails, pockets
- Referee voice, applause for good shots and at the end of the frame
- Background music in the menu and during play
- Shot clock with countdown ticks in the last ten seconds

**Languages**

English, Italian, French and Spanish, switchable at any time, even during a
game.

## Folders

| Folder | Content |
|---|---|
| `golden_break.py` | Start the game from here |
| `giochi/biliardo` | Casino menu and billiards code, referee voice generator |
| `giochi/carte` | Card games code |
| `immagini/comune` | Fonts, controller icons, flags, background |
| `immagini/biliardo` | Tables, cloths, rails, crests, trophies, clock |
| `immagini/carte` | Card table, card faces and decks |
| `audio/comune` | Menu sounds |
| `audio/biliardo` | Music, sound effects, referee voice |
| `audio/carte` | Music and card sounds |

`giochi/biliardo/arbitro.py` regenerates the referee voice files (needs `edge-tts` and an
internet connection).
