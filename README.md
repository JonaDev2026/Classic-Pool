# Golden Break

A casino game for Mac, Windows and Linux, written in Python with pygame.
Billiards with nine disciplines, tournaments and 55 cues, plus six card
games on a real card table. Roulette and slots are on the way.

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

### Billiards

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

### Card games

Six games, all one against one or against the house, on a card table with
its own cloth and real decks.

| Game | Cards | How it goes |
|---|---|---|
| Blackjack | French, two decks | Bets from your wallet, blackjack pays 3 to 2, double on the first two cards, the dealer draws to 17 |
| Sette e Mezzo | Italian 40 | Bets from your wallet, the King of Coins is wild, sette e mezzo reale pays double, a tie replays the hand |
| Scopa | Italian 40 | Up to 11 points: cards, coins, settebello, primiera and scope. When a card can be taken in more than one way you choose, and the cards light up |
| Briscola | Italian 40 | 120 points, the trump lies across under the deck |
| Rummy | French, two decks and four jokers | Opening at 50, laying off after you open, buying a joker with the card it stands for, stake of 50 and the "closed in one turn" rule |
| Texas Hold'em | French | Heads-up against the dealer, blinds, flop, turn and river, fixed limit betting |

**Decks**: 43 of them, Italian (Napoletane, Toscane) and French (Poker 98,
Texas, Jumbo, Bridge, Club, Golden Trophy, Bike Trophy). Each game
remembers its own deck; Rummy plays with two decks of the same design and
you pick which two colours, with the double box when the pack has one.

**Table**: the cloth is chosen in the Cards menu, from the same textures as
the billiards tables, or left on random.

**Controls in Rummy**: one cursor for everything, deck, discard, your hand
and the melds on the table. With the pad: A draws, discards or melds, Y
picks cards for melding, X moves a card in your hand or lays it off, RB
sorts your hand by the best combinations it can find. With mouse and
keyboard the same things are a click or ENTER, and the keys set in the
controls page (C, G and E by default); the help line at the bottom always
shows the keys you are actually using.

**Languages**

English, Italian, French and Spanish, switchable at any time, even during a
game.

## Folders

| Folder | Content |
|---|---|
| `golden_break.py` | Start the game from here |
| `giochi/biliardo` | Casino menu and billiards code, referee voice generator |
| `giochi/carte` | Card games code (table, cards, games) |
| `immagini/comune` | Fonts, controller icons, flags, background |
| `immagini/biliardo` | Tables, cloths, rails, crests, trophies, clock |
| `immagini/carte` | Card table, card faces and decks |
| `audio/comune` | Menu sounds |
| `audio/biliardo` | Music, sound effects, referee voice |
| `audio/carte` | Music and card sounds |

`giochi/biliardo/arbitro.py` regenerates the referee voice files (needs `edge-tts` and an
internet connection).

The card faces and decks under `immagini/carte/facce` and
`immagini/carte/mazzi` are not in the repository: put your own images
there, one folder per deck with `dorso.png`, `scatola.png` and, for a two
deck pack, `scatola_doppia.png`. A deck folder is named
`<type>_<design>_<colour>`, for example `francesi_texas_rosso` or
`napoletane_rosso_150`, and the type picks which set of faces it uses.

## Credits

The French card faces come from [xCards](https://github.com/Xadeck/xCards)
(LGPL 3).
