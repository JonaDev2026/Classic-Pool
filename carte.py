"""Golden Break - le carte.

Il tavolo da carte, uguale per tutti i giochi di carte: la stessa misura
del tavolo da biliardo, cosi' i fianchi e la barra in basso restano
liberi. Sotto il legno scelto, dentro il panno scelto, sopra la PNG
table_cards.png con la linea che divide il panno dal legno. Niente
sponde e niente buche: al posto delle ombre della sponda, quella morbida
di un tavolo normale.

Si appoggia a biliardo.py per tutto il resto: finestra, caratteri,
sfondo, menu, texture di panni e cornici.
"""
import sys

import pygame


def _base():
    """Il modulo del biliardo gia' aperto: se il gioco e' partito da
    biliardo.py e' __main__, e non va importato una seconda volta (avrebbe
    impostazioni e finestra sue)."""
    m = sys.modules.get("__main__")
    if m is not None and hasattr(m, "tavolo_composto"):
        return m
    import biliardo
    return biliardo


B = _base()

TAVOLO_CARTE = "table_cards.png"
# il panno: dentro la linea della PNG, fin dove arriva il legno
PANNO_CARTE = pygame.Rect(120, 117, 1277, 662)
OMBRA_LEGNO = 14        # quanto si allarga l'ombra del panno sul legno
OMBRA_SUL_LEGNO = 120   # quanto scurisce il legno contro il panno (0-255)
LUCE_MEZZO = 26         # quanto schiarisce il centro del panno

COMPOSTO = {}


def ombra_tavolo(base, r):
    """Il panno qualche millimetro piu' alto del legno, come sui tavoli da
    carte: niente ombra dentro il panno (quella fa sembrare una sponda),
    ma un'ombra morbida che il panno butta sul legno tutto intorno, piu'
    forte in basso a destra, e sul bordo del panno un filo di luce in
    alto e un filo di scuro in basso. Al centro un filo di luce."""
    # l'ombra sul legno, fuori dal panno
    om = pygame.Surface(base.get_size(), pygame.SRCALPHA)
    for i in range(OMBRA_LEGNO, 0, -1):
        a = int(OMBRA_SUL_LEGNO * (1.0 - i / float(OMBRA_LEGNO + 1)) ** 1.6)
        q = r.inflate(i * 2, i * 2).move(i // 3, i // 2)
        pygame.draw.rect(om, (0, 0, 0, a), q, border_radius=i)
    om.fill((0, 0, 0, 0), r)        # solo sul legno, non sotto il panno
    base.blit(om, (0, 0))
    campo = base.subsurface(r)
    w, h = campo.get_size()
    # il bordo del panno, alzato: luce sopra e a sinistra, scuro sotto
    bordo = pygame.Surface((w, h), pygame.SRCALPHA)
    for k in range(3):
        a_l, a_s = 55 - k * 18, 45 - k * 15
        pygame.draw.line(bordo, (255, 255, 255, a_l), (k, k), (w - 1 - k, k))
        pygame.draw.line(bordo, (255, 255, 255, a_l), (k, k), (k, h - 1 - k))
        pygame.draw.line(bordo, (0, 0, 0, a_s), (k, h - 1 - k),
                         (w - 1 - k, h - 1 - k))
        pygame.draw.line(bordo, (0, 0, 0, a_s), (w - 1 - k, k),
                         (w - 1 - k, h - 1 - k))
    campo.blit(bordo, (0, 0))
    luce = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(12):
        k = 1.0 - i / 12.0
        q = pygame.Rect(0, 0, int(w * (0.35 + 0.6 * k)),
                        int(h * (0.35 + 0.6 * k)))
        q.center = (w // 2, h // 2)
        pygame.draw.ellipse(luce, (255, 255, 255, max(1, LUCE_MEZZO // 12)),
                            q)
    campo.blit(luce, (0, 0))


def tavolo_carte(i_panno, i_bordo):
    """Il tavolo montato a strati e ridotto alla misura del biliardo."""
    chiave = (i_panno, i_bordo)
    if chiave in COMPOSTO:
        return COMPOSTO[chiave]
    vero = B.tavolo_vero(TAVOLO_CARTE)
    if not vero:
        return None
    base = pygame.Surface(vero.get_size(), pygame.SRCALPHA)
    if B.BORDI and 0 <= i_bordo < len(B.BORDI):
        l = B.texture(B.BORDI[i_bordo][1], (B.LATO_LEGNO, B.LATO_LEGNO))
        if l is not None:
            legno = pygame.Surface(base.get_size(), pygame.SRCALPHA)
            for x in range(0, legno.get_width(), B.LATO_LEGNO):
                for y in range(0, legno.get_height(), B.LATO_LEGNO):
                    legno.blit(l, (x, y))
            legno.blit(B.sagoma_legno(base.get_size()), (0, 0),
                       special_flags=pygame.BLEND_RGBA_MULT)
            base.blit(legno, (0, 0))
    if B.PANNI and 0 <= i_panno < len(B.PANNI):
        q = B.texture(B.PANNI[i_panno][1], (B.LATO_PANNO, B.LATO_PANNO))
        if q is not None:
            campo = base.subsurface(PANNO_CARTE)
            for x in range(0, campo.get_width(), B.LATO_PANNO):
                for y in range(0, campo.get_height(), B.LATO_PANNO):
                    campo.blit(q, (x, y))
    ombra_tavolo(base, PANNO_CARTE)
    base.blit(vero, (0, 0))
    if len(COMPOSTO) > 3:
        COMPOSTO.clear()
    COMPOSTO[chiave] = pygame.transform.smoothscale(
        base, (int(B.TAV_W * B.SCALA), int(B.TAV_H * B.SCALA)))
    return COMPOSTO[chiave]


def scelta_tavolo():
    """Panno e cornice: per ora quelli scelti per il biliardo, o quelli
    di casa se non ce n'e' uno."""
    ip = B.CFG.get("panno", -1)
    ib = B.CFG.get("bordo", -1)
    if not 0 <= ip < len(B.PANNI):
        ip = B._quale(B.PANNI, B.TAVOLO_CASA[0])
    if not 0 <= ib < len(B.BORDI):
        ib = B._quale(B.BORDI, B.TAVOLO_CASA[1])
    return ip, ib


def schermata_carte(sc, clock, logo):
    """Per ora il tavolo vuoto, per vederlo. ESC torna al menu."""
    ip, ib = scelta_tavolo()
    while True:
        clock.tick(60)
        for ev in B.eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return "menu"
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 3:
                return "menu"
        sc.blit(B.fondo(), (0, 0))
        tav = tavolo_carte(ip, ib)
        if tav is not None:
            sc.blit(tav, B.TAV_POS)
        B.presenta()
