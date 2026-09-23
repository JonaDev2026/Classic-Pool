# -*- coding: utf-8 -*-
#
# Le frasi del croupier della roulette, con la stessa voce dell'arbitro
# del biliardo: en-GB-RyanNeural. Serve edge-tts e la rete:
#
#   python3 -m pip install --user edge-tts
#   python3 giochi/roulette/croupier.py
#
# I numeri da 1 a 36 sono gia' quelli dello snooker: qui ci sono lo zero
# e le frasi del tavolo. Il gioco legge i nomi dei file, non il testo,
# quindi i nomi qui sotto non si cambiano.

import asyncio
import os

import edge_tts

VOCE = "en-GB-RyanNeural"
QUI = os.path.dirname(os.path.abspath(__file__))
DOVE = os.path.join(QUI, "..", "..", "audio", "roulette", "voce")

FRASI = [
    ("v_zero", "Zero"),
    ("v_red", "Red"),
    ("v_black", "Black"),
    ("v_place", "Place your bets"),
    ("v_nomore", "No more bets"),
    ("v_win", "Winner"),
    ("v_nothing", "No winners"),
]


async def dillo(testo, dove):
    for tentativo in range(3):
        try:
            await edge_tts.Communicate(testo, VOCE).save(dove)
            return True
        except Exception as e:
            if tentativo == 2:
                print("   errore su %s: %s" % (os.path.basename(dove), e))
                return False
            await asyncio.sleep(1.5)


async def main():
    os.makedirs(DOVE, exist_ok=True)
    print("voce: %s" % VOCE)
    fatti = 0
    for nome, testo in FRASI:
        if await dillo(testo, os.path.join(DOVE, nome + ".mp3")):
            fatti += 1
    print("frasi: %d su %d" % (fatti, len(FRASI)))
    print("fatto")


if __name__ == "__main__":
    asyncio.run(main())
