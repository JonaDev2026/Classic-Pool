# -*- coding: utf-8 -*-
#
# Le frasi dell'arbitro, con la voce di prima: en-GB-RyanNeural.
# Serve edge-tts e la rete:
#
#   python3 -m pip install --user edge-tts
#   python3 arbitro.py
#
# Le frasi finiscono in biliardo_voce/pool, i numeri delle serie dello
# snooker in biliardo_voce/snooker. Il gioco legge i nomi dei file, non
# il testo, quindi i nomi qui sotto non si cambiano.

import asyncio
import os

import edge_tts

VOCE = "en-GB-RyanNeural"
QUI = os.path.dirname(os.path.abspath(__file__))
POOL = os.path.join(QUI, "..", "..", "audio", "biliardo", "voce", "pool")
SNOOKER = os.path.join(QUI, "..", "..", "audio", "biliardo", "voce", "snooker")

FRASI = [
    ("break", "Break"),
    ("game", "Game"),
    ("frame", "Frame"),
    ("foul", "Foul"),
    ("foul_and_a_miss", "Foul, and a miss"),
    ("ball_in_hand", "Ball in hand"),
    ("free_ball", "Free ball"),
    ("eight_ball", "Eight ball"),
    ("time", "Time"),
    ("solids", "Solids"),
    ("stripes", "Stripes"),
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
    os.makedirs(POOL, exist_ok=True)
    os.makedirs(SNOOKER, exist_ok=True)

    print("voce: %s" % VOCE)
    fatti = 0
    for nome, testo in FRASI:
        if await dillo(testo, os.path.join(POOL, nome + ".mp3")):
            fatti += 1
    print("frasi: %d su %d" % (fatti, len(FRASI)))

    fatti = 0
    for n in range(1, 148):
        f = os.path.join(SNOOKER, "n_%03d.mp3" % n)
        if await dillo(str(n), f):
            fatti += 1
        if n % 25 == 0:
            print("   numeri: %d" % n)
    print("numeri: %d su 147" % fatti)
    print("fatto")


if __name__ == "__main__":
    asyncio.run(main())
