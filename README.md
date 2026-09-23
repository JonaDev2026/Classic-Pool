# Golden Break

A casino game for Mac, Windows and Linux, written in Python with pygame.
Billiards with nine disciplines, tournaments and 55 cues, six card games
on a real card table, three roulette tables and a slot machine.

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
| Rummy | French, two decks and four jokers | Opening at 50, laying off, buying jokers, stake of 50 and the "closed in one turn" rule. See the rules below |
| Texas Hold'em | French | Heads-up against the dealer, blinds, flop, turn and river, fixed limit betting |

**Stakes**: Scopa, Briscola and Rummy are played for money. You choose
the stake before the match starts, from 10 to 1000, and the winner takes
the pot; in Rummy the losing hand also pays the 50 point stake. Blackjack,
Sette e Mezzo and Texas Hold'em take their bets hand by hand.

**Decks**: 43 of them, Italian (Napoletane, Toscane) and French (Poker 98,
Texas, Jumbo, Bridge, Club, Golden Trophy, Bike Trophy). Each game
remembers its own deck; Rummy plays with two decks of the same design and
you pick which two colours, with the double box when the pack has one.

**Table**: the cloth is chosen in the Cards menu, from the same textures as
the billiards tables, or left on random.

**Rummy rules the game enforces**

- You open at 50 points. Before you open you can still take the discard,
  lay off and buy jokers, but only if you reach 50 in that same turn: if
  you don't, everything goes back when you discard - your melds return to
  your hand, your lay-offs are pulled out and a joker you bought goes back
  to its place in the meld.
- Anything you take from the table has to go back down. The card you take
  from the discard pile and every joker you buy must end up on the table,
  melded or laid off. While one of them is still in your hand the only
  card you are allowed to discard is that same card - and there goes your
  turn.
- A joker is worth the slot it sits in, recounted every time it moves: a
  joker in a run of tens is worth 10, the same joker next to a 2 is worth
  2. Left in your hand at the end of the hand it costs you 25.
- To buy a joker from a run you play the exact card it stands for. To buy
  one from a set you have to close the set: with two kings and a joker on
  the table you need both missing kings, not one. With three kings and a
  joker the last king is enough.
- Before you open, a meld you laid this turn can be taken back: hold Y on
  it for three seconds, or press Y with the cursor on it.

**Controls in Rummy**: one cursor for everything, deck, discard, your hand
and the melds on the table. With the pad: A draws, discards or melds, Y
picks cards for melding, X moves a card in your hand or lays it off, RB
sorts your hand by the best combinations it can find. With mouse and
keyboard the same things are a click or ENTER, and the keys set in the
controls page (C, G and E by default); the help line at the bottom always
shows the keys you are actually using.

### Roulette

Three tables, chosen from the roulette menu:

| Table | Wheel | Rule |
|---|---|---|
| European | 37 numbers, a single zero | House edge 2.70% |
| French | 37 numbers, a single zero | La partage: on the zero, even money bets get half back, house edge 1.35% |
| American | 38 numbers, zero and double zero | Its own number order, the basket bet (0-00-1-2-3) pays 6 to 1, house edge 5.26% |

Each table has its own wheel, drawn from scratch: cherry wood on the
European, rosewood on the French, black and chrome on the American, with
the wide ball track, the diamonds and the gold cross of the turret. The
bowl stays still and only the number ring turns, the way a real wheel
does.

The chip moves freely over the layout with the mouse, the arrows or the
stick, so you bet on a number or on a line: straight, split, street,
corner, six line, the dozens, the columns and the even money bets. Chips
come in 5, 10, 25, 100 and 500 and stack in real denominations - two
fives stay two fives. The ball runs on the outer track for as long as the
sound lasts, then drops in and bounces its way onto the numbers, and the
croupier calls the number and the colour with the same voice as the
billiards referee. After every spin the chips stay on the layout for a
few seconds, winners with a gold halo, and under the table you read what
each bet paid.

`giochi/roulette/croupier.py` regenerates the croupier phrases (needs
`edge-tts` and an internet connection). The numbers themselves are the
snooker ones, already in the game.

### Slots

Five reels by four rows and 1024 ways to win, paid left to right: no
lines to pick, any symbol on any row counts. Twenty-three paying symbols,
from the fruit that pays from two up to the eight ball, plus a wild that
stands for all of them, the dice that give three free spins, the gift box
that drops a random prize and the jackpot symbol. The wild never pays on
its own: at least two real symbols have to be there.

You pick the bet per spin (20, 50, 100, 250, 500 or 1000) and the
paytable inside the machine shows what every symbol pays in real money at
the bet you chose. Every spin feeds a progressive jackpot that lives in
your profile and keeps growing until someone fills all five reels with
the jackpot symbol, or until you restart your career.

Winning symbols pulse with a glow taken from their own colours while the
rest fade, the neon frame cycles, the marquee bulbs run around the
cabinet, and the reels stop exactly when the spin sound ends. There is
one machine for now, Classic Slot, with its 26 symbols in
`immagini/slot/classica`; a new machine is a folder of PNGs plus its own
paytable. Sounds live in `audio/slot/fx`.

### Wallet

Billiards is free, everything else is played with the wallet. A new
career starts with 1000 and the money is saved in your profile, together
with the progressive jackpot. If you run dry, Settings > Restart career
wipes the profile and deals you a fresh 1000: it is a free game and the
money is imaginary.

**Languages**

English, Italian, French and Spanish, switchable at any time, even during a
game.

## Folders

| Folder | Content |
|---|---|
| `golden_break.py` | Start the game from here |
| `giochi/biliardo` | Casino menu and billiards code, referee voice generator |
| `giochi/carte` | Card games code (table, cards, games) |
| `giochi/roulette` | Roulette code and croupier voice generator |
| `giochi/slot` | Slot machine code |
| `immagini/comune` | Fonts, controller icons, flags, background |
| `immagini/biliardo` | Tables, cloths, rails, crests, trophies, clock |
| `immagini/carte` | Card table, card faces and decks |
| `immagini/slot` | Slot symbols, one folder per machine |
| `audio/comune` | Menu sounds |
| `audio/biliardo` | Music, sound effects, referee voice |
| `audio/carte` | Music and card sounds |
| `audio/roulette` | Ball sound and croupier phrases |
| `audio/slot` | Spin, wins, bonus and jackpot |

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
