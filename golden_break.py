"""Golden Break: si parte da qui.

Il codice di ogni gioco sta in giochi/<gioco>, le immagini in
immagini/<gioco>, i suoni in audio/<gioco>. Il menu del casino' e il
biliardo sono in giochi/biliardo/biliardo.py, le carte in giochi/carte."""
import os
import sys

RADICE = os.path.dirname(os.path.abspath(__file__))
for sotto in ("biliardo", "carte"):
    p = os.path.join(RADICE, "giochi", sotto)
    if p not in sys.path:
        sys.path.insert(0, p)

import biliardo  # noqa: E402

if __name__ == "__main__":
    biliardo.main()
