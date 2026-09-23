"""Golden Break - la roulette.

Ruota europea: trentasette caselle, un solo zero. Qui dentro c'e' la
ruota con la pallina, il tappeto delle puntate e i pagamenti.

Si appoggia a biliardo.py per finestra, caratteri, sfondo, suoni e
portafoglio, come le carte e la slot.
"""
import math
import os
import random
import sys

import pygame


def _base():
    m = sys.modules.get("__main__")
    if m is not None and hasattr(m, "tavolo_composto"):
        return m
    import biliardo
    return biliardo


B = _base()

CARTELLA = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(os.path.dirname(CARTELLA))
GFX = os.path.join(RADICE, "immagini", "roulette")

# l'ordine vero delle caselle sulla ruota europea, partendo dallo zero
RUOTA = (0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23,
         10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3,
         26)
ROSSI = (1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36)

VERDE_PANNO = (16, 88, 56)
VERDE_SCURO = (11, 64, 41)
ROSSO_N = (176, 32, 40)
NERO_N = (26, 26, 32)
ORO = (214, 178, 94)


def colore_numero(n):
    if n == 0:
        return VERDE_PANNO
    return ROSSO_N if n in ROSSI else NERO_N


# ------------------------------------------------------------ le puntate
# ogni puntata: che numeri copre e quanto paga (oltre alla puntata stessa)
def numeri_dozzina(i):
    return tuple(range(1 + i * 12, 13 + i * 12))


def numeri_colonna(i):
    return tuple(range(1 + i, 37, 3))


PUNTATE_FUORI = (
    ("rosso", lambda: tuple(ROSSI), 1),
    ("nero", lambda: tuple(n for n in range(1, 37) if n not in ROSSI), 1),
    ("pari", lambda: tuple(n for n in range(2, 37, 2)), 1),
    ("dispari", lambda: tuple(n for n in range(1, 36, 2)), 1),
    ("basso", lambda: tuple(range(1, 19)), 1),
    ("alto", lambda: tuple(range(19, 37)), 1),
    ("doz1", lambda: numeri_dozzina(0), 2),
    ("doz2", lambda: numeri_dozzina(1), 2),
    ("doz3", lambda: numeri_dozzina(2), 2),
    ("col1", lambda: numeri_colonna(0), 2),
    ("col2", lambda: numeri_colonna(1), 2),
    ("col3", lambda: numeri_colonna(2), 2),
)
PAGA_PIENO = 35             # il numero secco
FICHES = (5, 10, 25, 100, 500)


def copre(chiave):
    """I numeri coperti da una puntata."""
    if isinstance(chiave, int):
        return (chiave,)
    for nome, quali, _p in PUNTATE_FUORI:
        if nome == chiave:
            return quali()
    return ()


def quanto_paga(chiave):
    if isinstance(chiave, int):
        return PAGA_PIENO
    for nome, _q, p in PUNTATE_FUORI:
        if nome == chiave:
            return p
    return 0


def vincita(puntate, uscito):
    """Quanto rende il colpo: la puntata torna indietro piu' il premio."""
    tot = 0
    vinte = []
    for chiave, soldi in puntate.items():
        if uscito in copre(chiave):
            tot += soldi + soldi * quanto_paga(chiave)
            vinte.append(chiave)
    return tot, vinte


# -------------------------------------------------------------- i testi
TXT = {
    "en": {"roulette": "Roulette", "spin": "Spin", "chip": "Chip",
           "clear": "Clear", "back": "Back", "bet": "Bet",
           "win": "You win %s", "no_win": "Nothing", "broke": "Not enough money",
           "last": "Last numbers", "place": "Place your bets",
           "ball": "No more bets", "red": "Red", "black": "Black",
           "even": "Even", "odd": "Odd", "low": "1-18", "high": "19-36",
           "d1": "1st 12", "d2": "2nd 12", "d3": "3rd 12", "col": "2 to 1",
           "help": "arrows / mouse  move     click / ENTER  bet     %s  chip     %s  spin     ESC  back",
           "rl_move": "choose", "rl_bet": "bet", "rl_spin": "spin",
           "rl_chip": "chip"},
    "it": {"roulette": "Roulette", "spin": "Gira", "chip": "Fiche",
           "clear": "Pulisci", "back": "Indietro", "bet": "Puntata",
           "win": "Vinci %s", "no_win": "Niente", "broke": "Non hai abbastanza soldi",
           "last": "Ultimi numeri", "place": "Fate il vostro gioco",
           "ball": "Niente va piu'", "red": "Rosso", "black": "Nero",
           "even": "Pari", "odd": "Dispari", "low": "1-18", "high": "19-36",
           "d1": "1a dozzina", "d2": "2a dozzina", "d3": "3a dozzina",
           "col": "2 a 1",
           "help": "frecce / mouse  muovi     clic / INVIO  punta     %s  fiche     %s  gira     ESC  indietro",
           "rl_move": "scegli", "rl_bet": "punta", "rl_spin": "gira",
           "rl_chip": "fiche"},
    "fr": {"roulette": "Roulette", "spin": "Tourner", "chip": "Jeton",
           "clear": "Effacer", "back": "Retour", "bet": "Mise",
           "win": "Vous gagnez %s", "no_win": "Rien",
           "broke": "Pas assez d'argent", "last": "Derniers numeros",
           "place": "Faites vos jeux", "ball": "Rien ne va plus",
           "red": "Rouge", "black": "Noir", "even": "Pair", "odd": "Impair",
           "low": "1-18", "high": "19-36", "d1": "1re 12", "d2": "2e 12",
           "d3": "3e 12", "col": "2 pour 1",
           "help": "fleches / souris  deplacer     clic / ENTREE  miser     %s  jeton     %s  tourner     ECHAP  retour",
           "rl_move": "choisir", "rl_bet": "miser", "rl_spin": "tourner",
           "rl_chip": "jeton"},
    "es": {"roulette": "Ruleta", "spin": "Girar", "chip": "Ficha",
           "clear": "Limpiar", "back": "Atras", "bet": "Apuesta",
           "win": "Ganas %s", "no_win": "Nada",
           "broke": "No tienes bastante dinero", "last": "Ultimos numeros",
           "place": "Hagan juego", "ball": "No va mas", "red": "Rojo",
           "black": "Negro", "even": "Par", "odd": "Impar", "low": "1-18",
           "high": "19-36", "d1": "1a docena", "d2": "2a docena",
           "d3": "3a docena", "col": "2 a 1",
           "help": "flechas / raton  mover     clic / INTRO  apostar     %s  ficha     %s  girar     ESC  atras",
           "rl_move": "mover", "rl_bet": "apostar", "rl_spin": "girar",
           "rl_chip": "ficha"},
}
NOMI_FUORI = {"rosso": "red", "nero": "black", "pari": "even",
              "dispari": "odd", "basso": "low", "alto": "high",
              "doz1": "d1", "doz2": "d2", "doz3": "d3",
              "col1": "col", "col2": "col", "col3": "col"}


def T(k):
    d = TXT.get(B.CFG.get("lingua", "en"), TXT["en"])
    return d.get(k, TXT["en"].get(k, k))


def nome_puntata(chiave):
    if isinstance(chiave, int):
        return str(chiave)
    return T(NOMI_FUORI.get(chiave, chiave))


RIGA_PAD_ROULETTE = ((("croce",), "rl_move"), (("a",), "rl_bet"),
                     (("y",), "rl_chip"), (("x",), "rl_spin"),
                     (("b",), "pa_back"))
for _l, _d in (
        ("en", {"rl_move": "choose", "rl_bet": "bet", "rl_chip": "chip",
                "rl_spin": "spin"}),
        ("it", {"rl_move": "scegli", "rl_bet": "punta", "rl_chip": "fiche",
                "rl_spin": "gira"}),
        ("fr", {"rl_move": "choisir", "rl_bet": "miser", "rl_chip": "jeton",
                "rl_spin": "tourner"}),
        ("es", {"rl_move": "mover", "rl_bet": "apostar", "rl_chip": "ficha",
                "rl_spin": "girar"})):
    B.TESTI.setdefault(_l, {}).update(_d)


def aiuto_roulette():
    return T("help") % (B.nome_tasto(B.tasto("cambia")),
                        B.nome_tasto(B.tasto("gesso")))


# ------------------------------------------------------------ la ruota
RUOTA_GFX = [None]


def disegna_ruota(lato):
    """La ruota vista dall'alto: la corona di legno, le trentasette
    caselle coi numeri, il mozzo dorato in mezzo. Si disegna una volta
    sola e poi si gira."""
    if RUOTA_GFX[0] is not None and RUOTA_GFX[0].get_width() == lato:
        return RUOTA_GFX[0]
    q = pygame.Surface((lato, lato), pygame.SRCALPHA)
    c = lato // 2
    r_fuori = int(lato * 0.5)
    r_banda = int(lato * 0.455)      # dove comincia la corona dei numeri
    r_caselle = int(lato * 0.30)     # dove finisce, verso il centro
    r_mozzo = int(lato * 0.27)
    # la corona di legno
    pygame.draw.circle(q, (74, 46, 28), (c, c), r_fuori)
    pygame.draw.circle(q, (104, 68, 40), (c, c), r_fuori - max(1, lato // 80))
    pygame.draw.circle(q, (52, 34, 22), (c, c), r_banda + max(1, lato // 110))
    passo = 2 * math.pi / len(RUOTA)
    f = pygame.font.SysFont("dejavusans", max(9, int(lato * 0.042)), bold=True)
    for i, n in enumerate(RUOTA):
        a0 = -math.pi / 2 + (i - 0.5) * passo
        punti = []
        for k in range(7):
            a = a0 + passo * k / 6.0
            punti.append((c + math.cos(a) * r_banda,
                          c + math.sin(a) * r_banda))
        for k in range(6, -1, -1):
            a = a0 + passo * k / 6.0
            punti.append((c + math.cos(a) * r_caselle,
                          c + math.sin(a) * r_caselle))
        pygame.draw.polygon(q, colore_numero(n), punti)
        pygame.draw.line(q, (206, 200, 190),
                         (c + math.cos(a0) * r_caselle,
                          c + math.sin(a0) * r_caselle),
                         (c + math.cos(a0) * r_banda,
                          c + math.sin(a0) * r_banda), max(1, lato // 200))
        a = a0 + passo / 2
        t = f.render(str(n), True, (255, 255, 255))
        t = pygame.transform.rotate(t, -math.degrees(a) + 90)
        rr = int((r_banda + r_caselle) / 2)
        q.blit(t, t.get_rect(center=(c + math.cos(a) * rr,
                                     c + math.sin(a) * rr)))
    # il mozzo: ottone lucido con le razze
    pygame.draw.circle(q, (150, 118, 62), (c, c), r_mozzo)
    for k in range(8):
        a = k * math.pi / 4
        pygame.draw.line(q, (188, 154, 88), (c, c),
                         (c + math.cos(a) * r_mozzo * 0.92,
                          c + math.sin(a) * r_mozzo * 0.92),
                         max(2, lato // 90))
    pygame.draw.circle(q, (92, 70, 42), (c, c), r_mozzo, max(1, lato // 70))
    pygame.draw.circle(q, (196, 164, 96), (c, c), int(r_mozzo * 0.42))
    pygame.draw.circle(q, (120, 92, 50), (c, c), int(r_mozzo * 0.42),
                       max(1, lato // 110))
    RUOTA_GFX[0] = q
    return q


class Ruota:
    """La ruota che gira e la pallina che rallenta fino alla casella.

    La pallina si muove nel sistema della ruota: si tiene lo scarto fra
    la pallina e la casella dello zero, cosi' quando si ferma resta
    incollata al suo numero anche mentre la ruota continua a girare."""

    def __init__(self, centro, lato):
        self.centro = centro
        self.lato = lato
        self.ang = 0.0              # quanto e' girata la ruota
        self.gira = False
        self.t = 0.0
        self.durata = 0.0
        self.uscito = None
        self.off = 0.0              # dove sta la pallina, rispetto alla ruota
        self.off_da = 0.0
        self.off_a = 0.0

    def passo_casella(self):
        return 2 * math.pi / len(RUOTA)

    def lancia(self, numero, durata=5.0):
        """Butta la pallina: si sa gia' dove finisce, ci arriva girando."""
        self.uscito = numero
        self.gira = True
        self.t = 0.0
        self.durata = durata
        posto = RUOTA.index(numero)
        self.off_da = self.off
        # la pallina gira al contrario della ruota, sei giri buoni
        meta = posto * self.passo_casella()
        self.off_a = meta - 6 * 2 * math.pi

    def passo(self, dt):
        self.ang += dt * (1.6 if self.gira else 0.30)
        if not self.gira:
            return False
        self.t += dt
        k = min(1.0, self.t / self.durata)
        m = 1 - (1 - k) ** 3          # parte forte e rallenta
        self.off = self.off_da + (self.off_a - self.off_da) * m
        if k >= 1.0:
            self.gira = False
            self.off = RUOTA.index(self.uscito) * self.passo_casella()
            return True
        return False

    def dove_palla(self):
        """Il punto sullo schermo dove sta la pallina adesso."""
        k = min(1.0, self.t / self.durata) if self.gira else 1.0
        fuori, dentro = self.lato * 0.46, self.lato * 0.335
        r = fuori + (dentro - fuori) * (1 - (1 - k) ** 2)
        a = -math.pi / 2 + self.off + self.ang
        return (self.centro[0] + math.cos(a) * r,
                self.centro[1] + math.sin(a) * r)

    def disegna(self, sc):
        base = disegna_ruota(self.lato)
        girata = pygame.transform.rotozoom(base, -math.degrees(self.ang), 1.0)
        sc.blit(girata, girata.get_rect(center=self.centro))
        if self.uscito is None and not self.gira:
            return
        x, y = self.dove_palla()
        raggio = max(3, int(self.lato * 0.028))
        pygame.draw.circle(sc, (24, 24, 28), (int(x) + 2, int(y) + 2), raggio)
        pygame.draw.circle(sc, (245, 245, 240), (int(x), int(y)), raggio)


# ------------------------------------------------------------ il tappeto
class Tappeto:
    """Il panno delle puntate: lo zero, i trentasei numeri, le colonne,
    le dozzine e le puntate semplici. Ogni casella sa che puntata e'."""

    def __init__(self):
        self.celle = []             # (chiave, rettangolo, etichetta)
        self.fai()

    def fai(self):
        self.celle = []
        w, h = B.s(40), B.s(44)
        x0 = B.s(430)
        y0 = B.ALTO + B.s(80)
        # lo zero, alto quanto le tre righe
        self.celle.append((0, pygame.Rect(x0, y0, w, h * 3), "0"))
        for j in range(12):
            for i in range(3):
                n = j * 3 + (3 - i)
                r = pygame.Rect(x0 + w + j * w, y0 + i * h, w, h)
                self.celle.append((n, r, str(n)))
        # le tre colonne, a destra
        for i in range(3):
            r = pygame.Rect(x0 + w + 12 * w, y0 + i * h, w, h)
            self.celle.append(("col%d" % (3 - i), r, T("col")))
        # le dozzine
        for i in range(3):
            r = pygame.Rect(x0 + w + i * 4 * w, y0 + 3 * h, 4 * w, h)
            self.celle.append(("doz%d" % (i + 1), r, T("d%d" % (i + 1))))
        # le puntate semplici
        fuori = (("basso", T("low")), ("pari", T("even")),
                 ("rosso", T("red")), ("nero", T("black")),
                 ("dispari", T("odd")), ("alto", T("high")))
        for i, (chiave, testo) in enumerate(fuori):
            r = pygame.Rect(x0 + w + i * 2 * w, y0 + 4 * h, 2 * w, h)
            self.celle.append((chiave, r, testo))

    def zona(self):
        r = self.celle[0][1].unionall([c[1] for c in self.celle])
        return r

    def disegna(self, sc, puntate, cursore, uscito, lampo):
        f = B.FONTS["small"]
        f_n = B.FONTS["font"]
        zona = self.zona().inflate(B.s(16), B.s(16))
        pygame.draw.rect(sc, VERDE_SCURO, zona, border_radius=B.s(8))
        pygame.draw.rect(sc, ORO, zona, max(1, B.s(2)), border_radius=B.s(8))
        for chiave, r, testo in self.celle:
            dentro = VERDE_PANNO
            if isinstance(chiave, int):
                dentro = colore_numero(chiave)
            pygame.draw.rect(sc, dentro, r)
            pygame.draw.rect(sc, (228, 226, 220), r, 1)
            # il numero uscito lampeggia
            if uscito is not None and isinstance(chiave, int) \
                    and chiave == uscito:
                q = pygame.Surface(r.size, pygame.SRCALPHA)
                q.fill((255, 236, 150, int(70 + 120 * lampo)))
                sc.blit(q, r)
            usa = f_n if isinstance(chiave, int) else f
            t = usa.render(testo, True, (245, 245, 240))
            if t.get_width() > r.w - B.s(6):
                t = pygame.transform.smoothscale(
                    t, (r.w - B.s(6),
                        int(t.get_height() * (r.w - B.s(6)) / t.get_width())))
            sc.blit(t, t.get_rect(center=r.center))
            # la fiche appoggiata sopra
            if chiave in puntate:
                disegna_fiche(sc, r.center, puntate[chiave])
            if chiave == cursore:
                pygame.draw.rect(sc, (255, 255, 255), r.inflate(B.s(4), B.s(4)),
                                 max(2, B.s(2)))

    def sotto_mouse(self, pos):
        for chiave, r, _t in self.celle:
            if r.collidepoint(pos):
                return chiave
        return None

    def vicino(self, chiave, dx, dy):
        """La casella piu' vicina nella direzione data: serve alle frecce."""
        ora = next((r for k, r, _t in self.celle if k == chiave), None)
        if ora is None:
            return chiave
        meglio, dist = chiave, None
        for k, r, _t in self.celle:
            if k == chiave:
                continue
            vx, vy = r.centerx - ora.centerx, r.centery - ora.centery
            if dx and (vx * dx) <= 0:
                continue
            if dy and (vy * dy) <= 0:
                continue
            if dx and abs(vy) > B.s(60):
                continue
            if dy and abs(vx) > B.s(60):
                continue
            d = abs(vx) + abs(vy)
            if dist is None or d < dist:
                meglio, dist = k, d
        return meglio


FICHE_COL = ((5, (200, 200, 205)), (10, (70, 140, 220)),
             (25, (60, 170, 110)), (100, (190, 60, 70)),
             (500, (150, 110, 210)))


def colore_fiche(soldi):
    col = FICHE_COL[0][1]
    for v, c in FICHE_COL:
        if soldi >= v:
            col = c
    return col


def disegna_fiche(sc, centro, soldi):
    """Una fiche col suo valore sopra."""
    r = B.s(15)
    col = colore_fiche(soldi)
    pygame.draw.circle(sc, (20, 20, 24), (centro[0] + 1, centro[1] + 2), r)
    pygame.draw.circle(sc, col, centro, r)
    pygame.draw.circle(sc, (250, 250, 250), centro, r, max(1, B.s(2)))
    f = B.FONTS.get("mini") or B.FONTS["small"]
    t = f.render(str(soldi), True, (255, 255, 255))
    if t.get_width() > r * 1.8:
        t = pygame.transform.smoothscale(
            t, (int(r * 1.8), int(t.get_height() * r * 1.8 / t.get_width())))
    sc.blit(t, t.get_rect(center=centro))


# ------------------------------------------------------------- il gioco
def gioca_roulette(sc, clock, logo):
    """Si punta sul tappeto, si lancia la pallina, si paga."""
    tap = Tappeto()
    ruota = Ruota((B.s(215), B.ALTO + B.s(250)), B.s(380))
    puntate = {}
    usciti = []
    cursore = 0
    fiche = B.CFG.get("roul_fiche", FICHES[1])
    if fiche not in FICHES:
        fiche = FICHES[1]
    sel = 0
    msg, sotto, vinto = T("place"), "", 0
    lampo = 0.0
    voci = lambda: [T("spin"), "%s  %s" % (T("chip"), B.dollari(fiche)),
                    T("clear"), T("back")]
    rett = []

    def punta():
        nonlocal msg
        if ruota.gira:
            return
        if B.soldi() < fiche:
            msg = T("broke")
            B.suona_fx("menu_chiudi", 0.7)
            return
        B.soldi(-fiche)
        puntate[cursore] = puntate.get(cursore, 0) + fiche
        B.salva_config()
        B.suona_fx("menu_tic", 0.8)
        msg = "%s  %s" % (T("bet"), B.dollari(sum(puntate.values())))

    def pulisci():
        nonlocal msg
        if ruota.gira or not puntate:
            return
        B.soldi(sum(puntate.values()))
        puntate.clear()
        B.salva_config()
        msg = T("place")
        B.suona_fx("menu_chiudi", 0.7)

    def lancia():
        nonlocal msg, sotto, vinto
        if ruota.gira or not puntate:
            return
        ruota.lancia(random.choice(RUOTA))
        msg, sotto, vinto = T("ball"), "", 0
        B.suona_fx("menu_apri", 0.8)

    def cambia_fiche(verso):
        nonlocal fiche
        i = FICHES.index(fiche)
        fiche = FICHES[(i + verso) % len(FICHES)]
        B.CFG["roul_fiche"] = fiche
        B.salva_config()
        B.suona_fx("menu_tic", 0.6)

    while True:
        dt = min(0.05, clock.tick(60) / 1000.0)
        lampo = (lampo + dt) % 1.0
        mouse = B.mouse_gioco()
        for ev in B.eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pulisci()
                    return "su"
                if ev.key in (pygame.K_LEFT, pygame.K_a):
                    cursore = tap.vicino(cursore, -1, 0)
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    cursore = tap.vicino(cursore, 1, 0)
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    cursore = tap.vicino(cursore, 0, -1)
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    cursore = tap.vicino(cursore, 0, 1)
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                pygame.K_SPACE):
                    punta()
                elif ev.key == B.tasto("cambia"):
                    cambia_fiche(1)
                elif ev.key == B.tasto("gesso"):
                    lancia()
                elif ev.key == B.tasto("eff_via"):
                    pulisci()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (1, 3):
                dove = tap.sotto_mouse(mouse)
                if dove is not None and ev.button == 1:
                    cursore = dove
                    punta()
                for i, r in enumerate(rett):
                    if r.collidepoint(mouse):
                        sel = i
                        if i == 0:
                            lancia()
                        elif i == 1:
                            cambia_fiche(1)
                        elif i == 2:
                            pulisci()
                        else:
                            pulisci()
                            return "su"
        if B.MOUSE_VIVO[0]:
            dove = tap.sotto_mouse(mouse)
            if dove is not None:
                cursore = dove
            for i, r in enumerate(rett):
                if r.collidepoint(mouse):
                    sel = i
        if ruota.passo(dt):
            n = ruota.uscito
            usciti.insert(0, n)
            del usciti[8:]
            vinto, vinte = vincita(puntate, n)
            if vinto:
                B.soldi(vinto)
                msg = T("win") % B.dollari(vinto)
                sotto = "  ".join(nome_puntata(k) for k in vinte)
                B.suona_fx("menu_apri", 1.0)
            else:
                msg = T("no_win")
                sotto = ""
            puntate.clear()
            B.salva_config()

        # ---- il disegno
        sc.blit(B.fondo(), (0, 0))
        ruota.disegna(sc)
        tap.disegna(sc, puntate, cursore, ruota.uscito if not ruota.gira
                    else None, abs(math.sin(lampo * math.pi)))
        rett = disegna_colonna(sc, voci(), sel, fiche, puntate, msg, sotto,
                               vinto, usciti, tap)
        small = B.FONTS["small"]
        if B.modo_comandi() == "pad" and B.ICONE_TASTI_OK():
            r = B.riga_pad(small, RIGA_PAD_ROULETTE)
        else:
            r = small.render(aiuto_roulette(), True, (150, 156, 168))
        sc.blit(r, r.get_rect(center=(B.WIN_W // 2, B.WIN_H - B.s(30))))
        B.presenta()


def disegna_colonna(sc, voci, sel, fiche, puntate, msg, sotto, vinto,
                    usciti, tap):
    """La fascia a destra: i numeri usciti, la puntata, il messaggio e le
    scelte, nello stesso stile della slot e delle carte."""
    x0, x1 = B.s(1010), B.WIN_W - B.s(14)
    f = B.FONTS["small"]
    y = B.ALTO + B.s(24)
    t = f.render(T("last"), True, (150, 156, 168))
    sc.blit(t, (x0, y))
    y += t.get_height() + B.s(8)
    for i, n in enumerate(usciti[:8]):
        r = pygame.Rect(x0 + (i % 4) * B.s(48), y + (i // 4) * B.s(34),
                        B.s(40), B.s(28))
        pygame.draw.rect(sc, colore_numero(n), r, border_radius=B.s(4))
        pygame.draw.rect(sc, (90, 94, 104), r, 1, border_radius=B.s(4))
        q = f.render(str(n), True, (245, 245, 240))
        sc.blit(q, q.get_rect(center=r.center))
    y += B.s(80)
    righe = [(T("chip"), B.dollari(fiche), (235, 238, 245)),
             (T("bet"), B.dollari(sum(puntate.values())), (235, 238, 245))]
    if vinto:
        righe.append((T("win").split()[0], B.dollari(vinto), B.VERDE_SOLDI))
    for et, val, col in righe:
        t = f.render(et, True, (150, 156, 168))
        sc.blit(t, (x0, y))
        q = f.render(str(val), True, col)
        sc.blit(q, q.get_rect(topright=(x1, y)))
        y += f.get_height() + B.s(10)
    # le scelte, in stile menu
    rett = []
    f_v = B.FONTS["font"]
    B.tic_menu(tuple(voci), sel)
    passo = f_v.get_height() + B.s(14)
    y = max(y + B.s(30), B.ALTO + B.s(330))
    for i, testo in enumerate(voci):
        t = f_v.render(testo, True,
                       (255, 255, 255) if i == sel else (160, 166, 178))
        fondo = pygame.Rect(x0 - B.s(8), y - (passo - B.s(8)) // 2,
                            x1 - x0 + B.s(16), passo - B.s(8))
        if i == sel:
            q = pygame.Surface(fondo.size, pygame.SRCALPHA)
            q.fill((255, 255, 255, 16))
            sc.blit(q, fondo)
            pygame.draw.rect(sc, ORO, (fondo.x, fondo.y, max(1, B.s(3)),
                                       fondo.h))
        sc.blit(t, t.get_rect(midleft=(x0 + B.s(6), y)))
        rett.append(fondo)
        y += passo
    # il messaggio, sotto il tappeto
    zona = tap.zona()
    t = f_v.render(msg, True, (255, 226, 140) if vinto else (235, 238, 245))
    sc.blit(t, t.get_rect(center=(zona.centerx, zona.bottom + B.s(40))))
    if sotto:
        q = f.render(sotto, True, (180, 186, 198))
        sc.blit(q, q.get_rect(center=(zona.centerx, zona.bottom + B.s(66))))
    return rett


def schermata_roulette(sc, clock, logo):
    """Il menu della roulette: si gioca e basta, per ora."""
    return gioca_roulette(sc, clock, logo)
