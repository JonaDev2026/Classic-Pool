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
LEGNO_FUORI = pygame.Rect(95, 88, 1327, 720)    # il bordo esterno del legno
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
    diamanti_posti(base)
    base.blit(vero, (0, 0))
    if len(COMPOSTO) > 3:
        COMPOSTO.clear()
    COMPOSTO[chiave] = pygame.transform.smoothscale(
        base, (int(B.TAV_W * B.SCALA), int(B.TAV_H * B.SCALA)))
    return COMPOSTO[chiave]


def scelta_tavolo():
    """Il tavolo standard delle carte: panno verde e cornice di ciliegio,
    il tavolo di casa. Non segue quello scelto per il biliardo."""
    return (B._quale(B.PANNI, B.TAVOLO_CASA[0]),
            B._quale(B.BORDI, B.TAVOLO_CASA[1]))


# ------------------------------------------------------------ le carte
#
# Per ora solo la sagoma: carta bianca davanti, dorso grigio chiaro con
# una cornicetta. Serve a provare come entrano, escono e si muovono sul
# tavolo; la grafica vera arriva dopo, sopra le stesse misure.

import math
import random

CARTA_W, CARTA_H = 61, 88       # alla misura del disegno, poi s()
TEMPO_VOLO = 0.32               # secondi per andare da un posto all'altro
TEMPO_GIRO = 0.22               # secondi per girarla
FACCIA = {}


def faccia_carta(scoperta):
    """La superficie della carta, dritta, con la sua ombra."""
    if scoperta in FACCIA:
        return FACCIA[scoperta]
    w, h = B.s(CARTA_W), B.s(CARTA_H)
    r = max(3, B.s(9))
    sup = pygame.Surface((w + B.s(6), h + B.s(6)), pygame.SRCALPHA)
    # l'ombra, spostata in basso a destra
    pygame.draw.rect(sup, (0, 0, 0, 60), pygame.Rect(B.s(4), B.s(5), w, h),
                     border_radius=r)
    corpo = pygame.Rect(0, 0, w, h)
    if scoperta:
        pygame.draw.rect(sup, (250, 250, 246), corpo, border_radius=r)
        pygame.draw.rect(sup, (170, 170, 176), corpo, 1, border_radius=r)
    else:
        pygame.draw.rect(sup, (214, 216, 222), corpo, border_radius=r)
        dentro = corpo.inflate(-B.s(14), -B.s(14))
        pygame.draw.rect(sup, (186, 190, 200), dentro, max(1, B.s(2)),
                         border_radius=max(2, r - B.s(4)))
        pygame.draw.rect(sup, (150, 152, 160), corpo, 1, border_radius=r)
    FACCIA[scoperta] = sup
    return sup


def morbido(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


class Carta:
    """Una carta sul tavolo: dove sta, dove va, com'e' girata."""

    def __init__(self, pos, angolo=0.0, scoperta=False):
        self.pos = pygame.Vector2(pos)
        self.da = pygame.Vector2(pos)
        self.a = pygame.Vector2(pos)
        self.ang, self.ang_da, self.ang_a = angolo, angolo, angolo
        self.scoperta = scoperta
        self.gira_a = scoperta          # come deve finire
        self.t = 1.0                    # 1 = arrivata
        self.ritardo = 0.0
        self.su = 0.0                   # quanto si alza sotto il mouse

    def vai(self, dove, angolo=None, scoperta=None, ritardo=0.0):
        self.da = pygame.Vector2(self.pos)
        self.a = pygame.Vector2(dove)
        self.ang_da = self.ang
        self.ang_a = self.ang if angolo is None else angolo
        if scoperta is not None:
            self.gira_a = scoperta
        self.t = 0.0
        self.ritardo = ritardo

    def passo(self, dt):
        if self.ritardo > 0:
            self.ritardo -= dt
            return
        if self.t < 1.0:
            self.t = min(1.0, self.t + dt / TEMPO_VOLO)
            k = morbido(self.t)
            self.pos = self.da.lerp(self.a, k)
            self.ang = self.ang_da + (self.ang_a - self.ang_da) * k

    def disegna(self, sc):
        # la girata: a meta' volo si stringe fino a sparire e rinasce
        # dall'altra parte, come una carta che ruota
        k = 1.0
        scoperta = self.scoperta
        if self.gira_a != self.scoperta:
            if self.t >= 1.0 and self.ritardo <= 0:
                self.scoperta = self.gira_a
                scoperta = self.scoperta
            else:
                k = abs(math.cos(math.pi * max(0.0, self.t)))
                scoperta = self.gira_a if self.t > 0.5 else self.scoperta
        img = faccia_carta(scoperta)
        if k < 0.999:
            img = pygame.transform.smoothscale(
                img, (max(1, int(img.get_width() * k)), img.get_height()))
        if abs(self.ang) > 0.1:
            img = pygame.transform.rotozoom(img, self.ang, 1.0)
        sc.blit(img, img.get_rect(center=(int(self.pos.x),
                                          int(self.pos.y - self.su))))


def zona_panno():
    """Il panno sullo schermo."""
    k = B.SCALA
    x, y = B.TAV_POS
    return pygame.Rect(int(x + PANNO_CARTE.x * k), int(y + PANNO_CARTE.y * k),
                       int(PANNO_CARTE.w * k), int(PANNO_CARTE.h * k))


def posti(n_mano):
    """Dove vanno le carte di ognuno: tu in basso a ventaglio, uno sopra,
    uno a sinistra e uno a destra, girati verso il centro."""
    z = zona_panno()
    passo = B.s(CARTA_W) * 0.62
    out = {0: [], 1: [], 2: [], 3: []}
    for i in range(n_mano):
        off = (i - (n_mano - 1) / 2.0)
        out[0].append(((z.centerx + off * passo * 1.25,
                        z.bottom - B.s(CARTA_H) * 0.62 + abs(off) * B.s(3)),
                       -off * 3.0))
        out[1].append(((z.centerx + off * passo * 0.7,
                        z.top + B.s(CARTA_H) * 0.55), 180.0))
        out[2].append(((z.left + B.s(CARTA_H) * 0.6,
                        z.centery + off * passo * 0.7), -90.0))
        out[3].append(((z.right - B.s(CARTA_H) * 0.6,
                        z.centery + off * passo * 0.7), 90.0))
    return out


# i colori dei quattro posti: il pallino sul legno e quello nella
# targhetta sono dello stesso colore, cosi' si capisce chi e' chi
COL_POSTI = ((236, 186, 64), (72, 142, 232), (222, 72, 72), (86, 190, 112))


def rombo(sc, centro, col, rx, ry):
    """Un diamantino piatto, intarsiato: niente luci, solo il colore."""
    x, y = centro
    pygame.draw.polygon(sc, col, [(x, y - ry), (x + rx, y), (x, y + ry),
                                  (x - rx, y)])


def targhetta(sc, nome, punti, centro, col, attivo=False):
    """Pallino, nome e punteggio di un giocatore, in una targhetta scura.
    Ritorna quanto e' larga, per metterle in fila."""
    f = B.FONTS["small"]
    tn = f.render(nome, True, (240, 240, 244))
    tp = f.render(str(punti), True, B.ORO_SCELTA)
    pad, gap, rp = B.s(12), B.s(14), B.s(7)
    w = pad + rp * 2 + B.s(10) + tn.get_width() + gap + tp.get_width() + pad
    h = max(tn.get_height(), tp.get_height()) + B.s(8)
    r = pygame.Rect(0, 0, w, h)
    r.center = (int(centro[0]), int(centro[1]))
    q = pygame.Surface(r.size, pygame.SRCALPHA)
    pygame.draw.rect(q, (0, 0, 0, 150), q.get_rect(),
                     border_radius=h // 2)
    sc.blit(q, r)
    if attivo:
        pygame.draw.rect(sc, B.ORO_SCELTA, r, max(1, B.s(2)),
                         border_radius=h // 2)
    rombo(sc, (r.x + pad + rp, r.centery), col, rp * 0.7, rp)
    x = r.x + pad + rp * 2 + B.s(10)
    sc.blit(tn, tn.get_rect(midleft=(x, r.centery)))
    sc.blit(tp, tp.get_rect(midright=(r.right - pad, r.centery)))
    return w


def larga_targhetta(nome, punti):
    f = B.FONTS["small"]
    return (B.s(12) * 2 + B.s(14) * 2 + B.s(10) + f.size(nome)[0] +
            B.s(14) + f.size(str(punti))[0])


def diamanti_posti(base):
    """Un diamantino colorato a meta' di ogni lato, intarsiato nel legno
    come i segni del biliardo: di chi e' quel posto. Si disegna sulla PNG
    a misura piena, prima di ridurre."""
    p, e = PANNO_CARTE, LEGNO_FUORI
    a, b = B.DIAMANTE_LARGO * 0.8, B.DIAMANTE_LUNGO * 0.8
    dove = {0: (p.centerx, (p.bottom + e.bottom) / 2.0, True),
            1: (p.centerx, (e.top + p.top) / 2.0, True),
            2: ((e.left + p.left) / 2.0, p.centery, False),
            3: ((p.right + e.right) / 2.0, p.centery, False)}
    for chi, (x, y, in_piedi) in dove.items():
        rx, ry = (a, b) if in_piedi else (b, a)
        rombo(base, (x, y), COL_POSTI[chi], rx, ry)


def fila_targhette(sc, nomi, punti, attivo=0):
    """La fascia del punteggio come nel biliardo, larga quanto la
    finestra e divisa in quattro: per ognuno il diamantino del suo posto,
    il nome in avorio e il riquadro verde col punteggio. Fra un posto e
    l'altro un filo d'oro; davanti a chi gioca la freccia d'oro."""
    r = B.BANDA_PUNTI
    carattere = B.FONTS.get("nomi_hud") or B.FONTS["font"]
    font = B.FONTS["font"]
    n = len(nomi)
    largo = r.w // n
    alto = r.h - B.s(8)
    for chi in range(n):
        cella = pygame.Rect(r.x + chi * largo, r.y, largo, r.h)
        # il punteggio: riquadro verde a destra della cella
        box = pygame.Rect(0, 0, B.s(64), alto)
        box.midright = (cella.right - B.s(14), cella.centery)
        pygame.draw.rect(sc, B.VERDONE, box)
        t = font.render(str(punti[chi]), True, (255, 255, 255))
        sc.blit(t, t.get_rect(center=box.center))
        # diamantino e nome a sinistra
        x = cella.left + B.s(26)
        if chi == attivo:
            m = B.s(7)
            pygame.draw.polygon(sc, B.ORO_LUCE,
                                [(x - B.s(12), cella.centery - m),
                                 (x - B.s(12) + B.s(9), cella.centery),
                                 (x - B.s(12), cella.centery + m)])
        rombo(sc, (x + B.s(8), cella.centery), COL_POSTI[chi],
              B.s(6), B.s(10))
        x += B.s(24)
        spazio = box.left - B.s(12) - x
        testo = nomi[chi]
        while testo and carattere.size(testo)[0] > spazio:
            testo = testo[:-1]
        if testo != nomi[chi]:
            testo = testo[:-1] + "."
        t = carattere.render(testo, True, B.AVORIO)
        sc.blit(t, t.get_rect(midleft=(x, cella.centery)))
        # il filo d'oro che separa i posti
        if chi > 0:
            pygame.draw.line(sc, B.ORO_LOGO, (cella.left, cella.top + B.s(8)),
                             (cella.left, cella.bottom - B.s(8)),
                             max(1, B.s(1)))


def schermata_carte(sc, clock, logo):
    """La prova delle carte: D distribuisce, clic su una tua carta la
    gioca al centro, R raccoglie tutto nel mazzo e lo rimescola. ESC
    torna al menu."""
    ip, ib = scelta_tavolo()
    z = zona_panno()
    # il mazzo fuori dal tavolo, a sinistra: dove nel biliardo ci sono
    # potenza e precisione
    x_lato = max(B.s(30), int((B.TAV_POS[0] + B.TAV_VISTA[0] * B.SCALA)
                              / 2.0))
    mazzo_pos = (x_lato, z.centery)
    carte = []
    mani = {0: [], 1: [], 2: [], 3: []}
    centro = []

    def nuovo_mazzo():
        del carte[:]
        for k in range(40):
            c = Carta((mazzo_pos[0] - k * 0.25, mazzo_pos[1] - k * 0.35))
            carte.append(c)
        for m in mani.values():
            del m[:]
        del centro[:]

    def distribuisci(n=5):
        pos = posti(n)
        rit = 0.0
        for i in range(n):
            for chi in (0, 1, 2, 3):
                if not carte:
                    return
                c = carte.pop()
                mani[chi].append(c)
                dove, ang = pos[chi][i]
                c.vai(dove, ang, scoperta=(chi == 0), ritardo=rit)
                rit += 0.07

    def rimetti_mano():
        """Dopo una giocata la mano si richiude al centro."""
        pos = posti(len(mani[0]))
        for i, c in enumerate(mani[0]):
            c.vai(pos[0][i][0], pos[0][i][1])

    def gioca(c):
        mani[0].remove(c)
        centro.append(c)
        n = len(centro)
        c.su = 0.0
        c.vai((z.centerx + (n - 1) * B.s(18) - B.s(20),
               z.centery + random.uniform(-4, 4)),
              random.uniform(-8, 8), scoperta=True)
        rimetti_mano()

    def raccogli():
        rit = 0.0
        tutte = centro + mani[0] + mani[1] + mani[2] + mani[3]
        for c in tutte:
            c.vai(mazzo_pos, 0.0, scoperta=False, ritardo=rit)
            rit += 0.02
            carte.insert(0, c)
        for m in mani.values():
            del m[:]
        del centro[:]
        random.shuffle(carte)

    nomi = [B.NOMI[0] or "Player 1"] + random.sample(B.AVVERSARI, 3)
    punti = [0, 0, 0, 0]
    nuovo_mazzo()
    while True:
        dt = clock.tick(60) / 1000.0
        mouse = B.mouse_gioco()
        sopra = None
        for c in reversed(mani[0]):
            w, h = B.s(CARTA_W), B.s(CARTA_H)
            if pygame.Rect(c.pos.x - w / 2, c.pos.y - h / 2 - c.su, w,
                           h).collidepoint(mouse) and c.t >= 1.0:
                sopra = c
                break
        for ev in B.eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return "menu"
                if ev.key == pygame.K_d and not any(mani.values()):
                    distribuisci()
                if ev.key == pygame.K_r:
                    raccogli()
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 3:
                    return "menu"
                if ev.button == 1 and sopra is not None:
                    gioca(sopra)
        for c in mani[0]:
            voglio = B.s(18) if c is sopra else 0.0
            c.su += (voglio - c.su) * min(1.0, dt * 14)
        for c in carte + centro + sum(mani.values(), []):
            c.passo(dt)

        sc.blit(B.fondo(), (0, 0))
        tav = tavolo_carte(ip, ib)
        if tav is not None:
            sc.blit(tav, B.TAV_POS)
        # prima quelle ferme nel mazzo, poi il centro, poi le mani: e fra
        # quelle in volo, prima chi e' partito prima
        for c in carte:
            c.disegna(sc)
        for c in centro:
            c.disegna(sc)
        for chi in (1, 2, 3, 0):
            for c in mani[chi]:
                c.disegna(sc)
        fila_targhette(sc, nomi, punti)
        aiuto = FONT_AIUTO()
        if aiuto is not None:
            t = aiuto.render("D  deal     click  play a card     R  collect"
                             "     ESC  back", True, (190, 196, 208))
            sc.blit(t, t.get_rect(center=(B.WIN_W // 2,
                                          B.WIN_H - B.s(40))))
        B.presenta()


def FONT_AIUTO():
    return B.FONTS.get("small")
