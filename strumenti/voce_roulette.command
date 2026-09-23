#!/bin/bash
# Golden Break - le frasi del croupier della roulette.
#
# Si lancia con due clic (o da Terminale). Usa la voce di sistema del
# Mac: "say". Per sentire che voci ci sono:   say -v '?'
# Per usarne un'altra:   ./voce_roulette.command Oliver
#
VOCE="${1:-Daniel}"
QUI="$(cd "$(dirname "$0")" && pwd)"
DOVE="$QUI/../audio/roulette/voce"
mkdir -p "$DOVE" || exit 1

frase() {
    nome="$1"; shift
    testo="$*"
    echo "  $nome  ->  $testo"
    say -v "$VOCE" -o "/tmp/gb_voce.aiff" "$testo" || exit 1
    afconvert -f WAVE -d LEI16@22050 "/tmp/gb_voce.aiff" "$DOVE/$nome.wav" || exit 1
    rm -f "/tmp/gb_voce.aiff"
}

echo "Voce: $VOCE"
frase n_000       "zero"
frase v_red       "red"
frase v_black     "black"
frase v_zero      "zero, green"
frase v_place     "place your bets"
frase v_nomore    "no more bets"
frase v_win       "winner"
frase v_nothing   "no winners"
echo
echo "Fatto: $DOVE"
