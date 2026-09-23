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

# la ruota americana: trentotto caselle, c'e' anche lo zero doppio, e
# i numeri stanno in un ordine tutto suo
ZERO2 = 37                  # dentro al programma lo zero doppio e' 37
RUOTA_US = (0, 28, 9, 26, 30, 11, 7, 20, 32, 17, 5, 22, 34, 15, 3, 24, 36,
            13, 1, ZERO2, 27, 10, 25, 29, 12, 8, 19, 31, 18, 6, 21, 33, 16,
            4, 23, 35, 14, 2)

# nome, come si chiama, che ruota, zero doppio, meta' indietro sullo zero
TAVOLI = (("europea", "t_eu", RUOTA, False, False),
          ("francese", "t_fr", RUOTA, False, True),
          ("americana", "t_us", RUOTA_US, True, False))

ORDINE = [RUOTA]            # la ruota in uso adesso
DOPPIO = [False]
PARTAGE = [False]
TIPO = ["europea"]


def scegli_tavolo(nome):
    """Cambia tavolo: ruota, zeri e regola della meta'."""
    for n, _t, ordine, doppio, partage in TAVOLI:
        if n != nome:
            continue
        TIPO[0], ORDINE[0] = n, ordine
        DOPPIO[0], PARTAGE[0] = doppio, partage
        SCODELLA[0] = None
        ROTORE[0] = None
        return


def scritto(n):
    """Come si scrive un numero: lo zero doppio e' "00"."""
    return "00" if n == ZERO2 else str(n)

VERDE_PANNO = (16, 88, 56)
VERDE_SCURO = (11, 64, 41)
ROSSO_N = (176, 32, 40)
NERO_N = (26, 26, 32)
ORO = (214, 178, 94)


def colore_numero(n):
    if n in (0, ZERO2):
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


PAGA_QUANTI = {1: 35, 2: 17, 3: 11, 4: 8, 5: 6, 6: 5}


def copre(chiave):
    """I numeri coperti da una puntata."""
    if isinstance(chiave, tuple):
        return chiave
    if isinstance(chiave, int):
        return (chiave,)
    for nome, quali, _p in PUNTATE_FUORI:
        if nome == chiave:
            return quali()
    return ()


def quanto_paga(chiave):
    if isinstance(chiave, tuple):
        return PAGA_QUANTI.get(len(chiave), 0)
    if isinstance(chiave, int):
        return PAGA_PIENO
    for nome, _q, p in PUNTATE_FUORI:
        if nome == chiave:
            return p
    return 0


def vincita(puntate, uscito):
    """Quanto rende il colpo: la puntata torna indietro piu' il premio.
    Torna il totale e l'elenco di cosa ha vinto, con quanto ha reso."""
    tot = 0
    vinte = []
    meta = ("rosso", "nero", "pari", "dispari", "basso", "alto")
    for chiave, soldi in puntate.items():
        if uscito in copre(chiave):
            reso = soldi + soldi * quanto_paga(chiave)
            tot += reso
            vinte.append((chiave, reso))
        elif PARTAGE[0] and uscito == 0 and chiave in meta:
            # tavolo francese: sullo zero le puntate semplici tornano
            # indietro a meta'
            tot += soldi // 2
    return tot, vinte


# -------------------------------------------------------------- i testi
TXT = {
    "en": {"t_eu": "European", "t_fr": "French", "t_us": "American",
           "t_eu_d": "37  single zero", "t_fr_d": "37  la partage",
           "t_us_d": "38  double zero", "table": "Choose the table",
           "roulette": "Roulette", "spin": "Spin", "chip": "Chip",
           "clear": "Clear", "back": "Back", "bet": "Bet",
           "win": "You win %s", "no_win": "Nothing", "broke": "Not enough money",
           "last": "Last numbers", "place": "Place your bets",
           "ball": "No more bets", "red": "Red", "black": "Black",
           "even": "Even", "odd": "Odd", "low": "1-18", "high": "19-36",
           "d1": "1st 12", "d2": "2nd 12", "d3": "3rd 12", "col": "2 to 1",
           "help": "arrows / mouse  move     click / ENTER  bet     %s  chip     %s  spin     ESC  back",
           "rl_move": "choose", "rl_bet": "bet", "rl_spin": "spin",
           "rl_chip": "chip"},
    "it": {"t_eu": "Europea", "t_fr": "Francese", "t_us": "Americana",
           "t_eu_d": "37  uno zero", "t_fr_d": "37  la partage",
           "t_us_d": "38  due zeri", "table": "Scegli il tavolo",
           "roulette": "Roulette", "spin": "Gira", "chip": "Fiche",
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
    "fr": {"t_eu": "Europeenne", "t_fr": "Francaise", "t_us": "Americaine",
           "t_eu_d": "37  un seul zero", "t_fr_d": "37  la partage",
           "t_us_d": "38  double zero", "table": "Choisissez la table",
           "roulette": "Roulette", "spin": "Tourner", "chip": "Jeton",
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
    "es": {"t_eu": "Europea", "t_fr": "Francesa", "t_us": "Americana",
           "t_eu_d": "37  un cero", "t_fr_d": "37  la partage",
           "t_us_d": "38  doble cero", "table": "Elige la mesa",
           "roulette": "Ruleta", "spin": "Girar", "chip": "Ficha",
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
    if isinstance(chiave, tuple):
        if len(chiave) == 2:
            return "%s-%s" % (scritto(chiave[0]), scritto(chiave[1]))
        return "%s-%s (%d)" % (scritto(chiave[0]), scritto(chiave[-1]),
                               len(chiave))
    if isinstance(chiave, int):
        return scritto(chiave)
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


# ------------------------------------------------------------- i suoni
SUONI = {}
DURATE = {}


def carica_suoni():
    """I suoni della roulette, da audio/roulette/fx."""
    if SUONI or not B.MUSICA_OK:
        return
    cartella = os.path.join(B.SUONI_DIR, "roulette", "fx")
    if not os.path.isdir(cartella):
        return
    for f in sorted(os.listdir(cartella)):
        if not f.lower().endswith((".ogg", ".wav", ".mp3")):
            continue
        try:
            s = pygame.mixer.Sound(os.path.join(cartella, f))
            SUONI[os.path.splitext(f)[0].lower()] = s
            DURATE[os.path.splitext(f)[0].lower()] = s.get_length()
        except pygame.error:
            pass


def carica_voce():
    """Le frasi del croupier, da audio/roulette/voce: si infilano fra
    quelle dell'arbitro, cosi' le dice la stessa coda. I numeri da 1 a
    36 sono gia' quelli del biliardo; qui c'e' lo zero e il resto."""
    if not B.MUSICA_OK:
        return
    cartella = os.path.join(B.SUONI_DIR, "roulette", "voce")
    if not os.path.isdir(cartella):
        return
    for f in sorted(os.listdir(cartella)):
        if not f.lower().endswith((".ogg", ".wav", ".mp3")):
            continue
        nome = os.path.splitext(f)[0].lower()
        if nome in B.VOCI:
            continue
        try:
            B.VOCI[nome] = pygame.mixer.Sound(os.path.join(cartella, f))
        except pygame.error:
            pass


def suona(nome, quanto=0.9):
    s = SUONI.get(nome)
    if s is None:
        return None
    v = B.CFG.get("effetti", 100) / 100.0
    if v <= 0.0:
        return s
    s.set_volume(min(1.0, v * quanto))
    s.play()
    return s


def voce(*codici):
    """Mette in coda una frase del croupier, se c'e'."""
    try:
        B.dice(*codici)
    except AttributeError:
        pass


def croupier(n):
    """Il numero uscito, detto con la voce dell'arbitro del biliardo:
    sono le stesse registrazioni, da n_001 a n_036. Lo zero e i colori
    li fa croupier.py, stessa voce, in audio/roulette/voce."""
    if n in (0, ZERO2):
        voce("v_zero")
    else:
        voce("n_%03d" % n, "v_red" if n in ROSSI else "v_black")


def dura_pallina():
    """Il giro dura esattamente quanto l'audio della pallina."""
    return DURATE.get("pallina", 11.0)


# ------------------------------------------------------------ la ruota
RUOTA_GFX = [None]


# sulla ruota fotografica lo zero non sta esattamente in cima: misurato,
# e' spostato di cinque gradi, e la pallina deve tenerne conto
SCARTO_PNG = math.radians(-4.9)


def ruota_png(lato):
    """La ruota fotografica, se c'e' il file: immagini/roulette/ruota.png,
    con lo zero in cima e i numeri in senso orario."""
    f = os.path.join(GFX, "ruota.png")
    if not os.path.isfile(f):
        return None
    if RUOTA_GFX[0] is not None and RUOTA_GFX[0].get_width() == lato:
        return RUOTA_GFX[0]
    try:
        img = pygame.image.load(f).convert_alpha()
    except (pygame.error, OSError):
        return None
    RUOTA_GFX[0] = pygame.transform.smoothscale(img, (lato, lato))
    return RUOTA_GFX[0]


def _anello(q, c, r1, r2, col1, col2, passi=26):
    """Un anello sfumato da r1 a r2: serve per dare il tondo al legno."""
    for i in range(passi):
        k = i / float(passi - 1)
        r = int(r1 + (r2 - r1) * k)
        col = tuple(int(col1[j] + (col2[j] - col1[j]) * k) for j in range(3))
        pygame.draw.circle(q, col, (c, c), r,
                           max(1, int(abs(r2 - r1) / passi) + 2))


# la ruota sta in due pezzi: la scodella non gira mai (cosi' resta tonda
# davvero) e dentro ci gira solo la corona dei numeri, come quelle vere
SCODELLA = [None]
ROTORE = [None]

# ogni tavolo ha il suo legno: fuori, dentro, la pista, il fondo della
# corona, e il metallo di diamanti, righe e croce
LEGNI = {
    "europea": ((56, 33, 20), (28, 16, 10), (46, 27, 17), (30, 18, 11),
                (34, 20, 13), (216, 178, 98)),
    "francese": ((74, 26, 26), (34, 13, 13), (58, 22, 22), (36, 14, 14),
                 (40, 16, 16), (226, 190, 110)),
    "americana": ((40, 40, 46), (18, 18, 22), (34, 34, 40), (20, 20, 25),
                  (24, 24, 29), (198, 204, 214)),
}


def legno():
    return LEGNI.get(TIPO[0], LEGNI["europea"])


# il legno vero della cornice: sono le stesse texture dei bordi del
# biliardo. L'americana resta in metallo, niente legno.
LEGNI_TEX = {"europea": "ciliegio", "francese": "palissandro"}
TEX = {}


def tex_legno(nome, lato):
    """La texture del legno, portata alla misura della ruota."""
    if not nome:
        return None
    if (nome, lato) in TEX:
        return TEX[(nome, lato)]
    f = os.path.join(RADICE, "immagini", "biliardo", "bordi", nome + ".png")
    if not os.path.isfile(f):
        return None
    try:
        img = pygame.image.load(f).convert()
    except (pygame.error, OSError):
        return None
    img = pygame.transform.smoothscale(img, (lato, lato))
    TEX[(nome, lato)] = img
    return img


def anello_legno(q, c, lato, r_fuori, r_dentro):
    """La cornice col legno vero: la texture ritagliata ad anello e un
    velo scuro verso l'interno, se no sembra un adesivo."""
    t = tex_legno(LEGNI_TEX.get(TIPO[0]), lato)
    if t is None:
        return
    anello = pygame.Surface((lato, lato), pygame.SRCALPHA)
    anello.blit(t, (0, 0))
    anello.fill((176, 164, 158, 255), special_flags=pygame.BLEND_RGBA_MULT)
    m = pygame.Surface((lato, lato), pygame.SRCALPHA)
    pygame.draw.circle(m, (255, 255, 255, 255), (c, c), r_fuori)
    pygame.draw.circle(m, (0, 0, 0, 0), (c, c), r_dentro)
    anello.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    q.blit(anello, (0, 0))
    om = pygame.Surface((lato, lato), pygame.SRCALPHA)
    spesso = max(2, (r_fuori - r_dentro) // 14)
    for i in range(20):
        k = i / 19.0
        r = int(r_dentro + (r_fuori - r_dentro) * k)
        a = int(120 * (1 - k) ** 1.5)
        if a > 0:
            pygame.draw.circle(om, (0, 0, 0, a), (c, c), r, spesso)
    q.blit(om, (0, 0))


def scodella(lato):
    """La parte ferma: la cornice di legno scuro e la pista larga dove
    corre la pallina, coi diamantini che la fanno ballare."""
    if SCODELLA[0] is not None and SCODELLA[0][0] == (lato, TIPO[0]):
        return SCODELLA[0][1]
    q = pygame.Surface((lato, lato), pygame.SRCALPHA)
    c = lato // 2
    R = lato * 0.5
    r_bordo = int(R * 0.995)
    r_pista_f = int(R * 0.86)       # dove comincia la pista
    r_pista_d = int(R * 0.68)       # dove finisce, verso i numeri
    fuori, dentro, pista1, pista2, _fondo, oro = legno()
    pygame.draw.circle(q, dentro, (c, c), r_bordo)
    _anello(q, c, r_bordo, r_pista_f, fuori, dentro, 34)
    # la pista: liscia e scura, un filo piu' chiara sul fondo
    _anello(q, c, r_pista_f, r_pista_d, pista1, pista2, 34)
    anello_legno(q, c, lato, r_bordo, r_pista_f)
    pygame.draw.circle(q, oro, (c, c), r_pista_f, max(1, lato // 240))
    pygame.draw.circle(q, (28, 16, 10), (c, c), r_pista_d, max(1, lato // 280))
    for k in range(8):
        a = -math.pi / 2 + k * math.pi / 4 + math.pi / 8
        rr = (r_pista_f + r_pista_d) / 2
        x, y = c + math.cos(a) * rr, c + math.sin(a) * rr
        d = lato * 0.022
        punti = [(x, y - d), (x + d * 0.62, y), (x, y + d), (x - d * 0.62, y)]
        pygame.draw.polygon(q, tuple(min(255, v + 26) for v in oro), punti)
        pygame.draw.polygon(q, tuple(int(v * 0.62) for v in oro), punti,
                            max(1, lato // 300))
    SCODELLA[0] = ((lato, TIPO[0]), q)
    return q


def rotore(lato):
    """La parte che gira: la corona dei numeri e la torretta in mezzo."""
    if ROTORE[0] is not None and ROTORE[0][0] == (lato, TIPO[0]):
        return ROTORE[0][1]
    R = lato * 0.5
    r_num_f = int(R * 0.66)
    r_num_d = int(R * 0.45)
    r_mozzo = int(R * 0.43)
    l2 = r_num_f * 2 + 4
    q = pygame.Surface((l2, l2), pygame.SRCALPHA)
    c = l2 // 2
    _f1, _f2, _p1, _p2, fondo, oro = legno()
    pygame.draw.circle(q, fondo, (c, c), r_num_f)
    quante = len(ORDINE[0])
    passo = 2 * math.pi / quante
    f = pygame.font.SysFont("dejavusans",
                            max(8, int(lato * (0.036 if quante < 38 else
                                               0.032))), bold=True)
    for i, n in enumerate(ORDINE[0]):
        a0 = -math.pi / 2 + (i - 0.5) * passo
        punti = []
        for k in range(7):
            a = a0 + passo * k / 6.0
            punti.append((c + math.cos(a) * (r_num_f - lato * 0.004),
                          c + math.sin(a) * (r_num_f - lato * 0.004)))
        for k in range(6, -1, -1):
            a = a0 + passo * k / 6.0
            punti.append((c + math.cos(a) * r_num_d,
                          c + math.sin(a) * r_num_d))
        pygame.draw.polygon(q, colore_numero(n), punti)
        pygame.draw.line(q, oro,
                         (c + math.cos(a0) * r_num_d,
                          c + math.sin(a0) * r_num_d),
                         (c + math.cos(a0) * r_num_f,
                          c + math.sin(a0) * r_num_f),
                         max(1, lato // 300))
        a = a0 + passo / 2
        t = f.render(scritto(n), True, (250, 248, 244))
        t = pygame.transform.rotate(t, -math.degrees(a) + 90)
        rr = int(r_num_f * 0.82 + r_num_d * 0.18)
        q.blit(t, t.get_rect(center=(c + math.cos(a) * rr,
                                     c + math.sin(a) * rr)))
    pygame.draw.circle(q, oro, (c, c), r_num_f, max(1, lato // 220))
    # il cono di mezzo e la torretta
    _anello(q, c, r_mozzo, int(r_mozzo * 0.30), _f1, _f2, 30)
    pygame.draw.circle(q, _f2, (c, c), r_mozzo, max(1, lato // 260))
    for k in range(4):
        a = k * math.pi / 2
        lung = r_mozzo * 0.86
        largo = lato * 0.018
        dx, dy = math.cos(a), math.sin(a)
        px, py = -dy, dx
        punti = [(c + dx * lung, c + dy * lung),
                 (c + px * largo, c + py * largo),
                 (c - px * largo, c - py * largo)]
        pygame.draw.polygon(q, oro, punti)
        pygame.draw.polygon(q, tuple(int(v * 0.6) for v in oro), punti,
                            max(1, lato // 340))
        pygame.draw.circle(q, tuple(min(255, v + 30) for v in oro),
                           (int(c + dx * lung), int(c + dy * lung)),
                           max(2, int(lato * 0.012)))
    pygame.draw.circle(q, tuple(int(v * 0.92) for v in oro), (c, c),
                       int(lato * 0.055))
    pygame.draw.circle(q, tuple(int(v * 0.6) for v in oro), (c, c),
                       int(lato * 0.055), max(1, lato // 300))
    pygame.draw.circle(q, tuple(min(255, v + 34) for v in oro), (c, c),
                       int(lato * 0.022))
    ROTORE[0] = ((lato, TIPO[0]), q)
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
        return 2 * math.pi / len(ORDINE[0])

    def lancia(self, numero, durata=None):
        """Butta la pallina: si sa gia' dove finisce, ci arriva girando."""
        self.uscito = numero
        self.gira = True
        self.t = 0.0
        self.durata = dura_pallina() if durata is None else durata
        posto = ORDINE[0].index(numero)
        self.off_da = self.off
        # la pallina gira al contrario della ruota: tanti giri quanto
        # basta per restare svelta per tutta la durata del suono
        meta = posto * self.passo_casella()
        giri = max(12, int(self.durata * 2.4))
        self.off_a = meta - giri * 2 * math.pi

    def passo(self, dt):
        if self.gira:
            k = min(1.0, self.t / self.durata)
            # anche la ruota rallenta, non gira sempre uguale
            self.ang += dt * (1.2 + 4.2 * (1 - k) ** 1.4)
        else:
            self.ang += dt * 1.2
        if not self.gira:
            return False
        self.t += dt
        k = min(1.0, self.t / self.durata)
        m = 1 - (1 - k) ** 2          # parte fortissima e cala piano piano
        self.off = self.off_da + (self.off_a - self.off_da) * m
        if k >= 1.0:
            self.gira = False
            self.off = ORDINE[0].index(self.uscito) * self.passo_casella()
            return True
        return False

    def dove_palla(self):
        """Il punto sullo schermo dove sta la pallina adesso. Prima gira
        sulla pista esterna, poi molla e scende sui numeri saltellando,
        e si posa piano."""
        k = min(1.0, self.t / self.durata) if self.gira else 1.0
        if ruota_png(self.lato) is not None:
            fuori, dentro = self.lato * 0.468, self.lato * 0.385
        else:
            # la pista larga e la corona dei numeri della ruota disegnata
            fuori, dentro = self.lato * 0.385, self.lato * 0.277
        cade = 0.72                     # fin qui corre sulla pista
        if k < cade:
            r = fuori
        else:
            t = (k - cade) / (1 - cade)
            # scende, poi saltella sulle caselle smorzandosi fino a fermarsi
            m = 1 - (1 - t) ** 2.2
            salti = abs(math.sin(t * math.pi * 3.2)) * (1 - t) ** 2.2
            r = fuori + (dentro - fuori) * m + salti * self.lato * 0.045
        a = -math.pi / 2 + self.off + self.ang
        if ruota_png(self.lato) is not None:
            a += SCARTO_PNG
        return (self.centro[0] + math.cos(a) * r,
                self.centro[1] + math.sin(a) * r)

    def disegna(self, sc):
        png = ruota_png(self.lato)
        if png is not None:
            girata = pygame.transform.rotozoom(png, -math.degrees(self.ang),
                                               1.0)
            sc.blit(girata, girata.get_rect(center=self.centro))
        else:
            # la scodella non si gira mai: cosi' resta tonda davvero
            base = scodella(self.lato)
            sc.blit(base, base.get_rect(center=self.centro))
            gir = pygame.transform.rotozoom(rotore(self.lato),
                                            -math.degrees(self.ang), 1.0)
            sc.blit(gir, gir.get_rect(center=self.centro))
        if self.uscito is None and not self.gira:
            return
        x, y = self.dove_palla()
        raggio = max(2, int(self.lato * 0.0125))
        pygame.draw.circle(sc, (18, 18, 22), (int(x) + 2, int(y) + 2), raggio)
        pygame.draw.circle(sc, (245, 245, 240), (int(x), int(y)), raggio)


# ------------------------------------------------------------ il tappeto
class Tappeto:
    """Il panno delle puntate. Le caselle servono a disegnare; la puntata
    vera la decide il punto dove appoggi la fiche, cosi' si punta anche
    sulle linee: a cavallo di due numeri, sull'incrocio di quattro, in
    fondo a una terzina o fra due terzine."""

    def __init__(self):
        # il tappeto sta sotto, largo e centrato: quattordici colonne
        # (lo zero, i dodici, il "2 a 1") e cinque righe
        self.w, self.h = B.s(56), B.s(52)
        self.x0 = (B.WIN_W - 14 * self.w) // 2
        self.y0 = B.ALTO + B.s(356)
        self.celle = []
        self.fai()

    # ---- geometria
    def cella_numero(self, n):
        j = (n - 1) // 3
        i = 2 - (n - 1) % 3
        return pygame.Rect(self.x0 + self.w + j * self.w,
                           self.y0 + i * self.h, self.w, self.h)

    def numero_di(self, j, i):
        """Il numero nella colonna j (0..11), riga i (0 in alto)."""
        return j * 3 + (3 - i)

    def fai(self):
        w, h, x0, y0 = self.w, self.h, self.x0, self.y0
        if DOPPIO[0]:
            # tavolo americano: lo zero e lo zero doppio, uno sull'altro
            mezzo = h * 3 // 2
            self.celle = [(0, pygame.Rect(x0, y0, w, mezzo), "0"),
                          (ZERO2, pygame.Rect(x0, y0 + mezzo, w,
                                              h * 3 - mezzo), "00")]
        else:
            self.celle = [(0, pygame.Rect(x0, y0, w, h * 3), "0")]
        for n in range(1, 37):
            self.celle.append((n, self.cella_numero(n), str(n)))
        for i in range(3):
            r = pygame.Rect(x0 + w + 12 * w, y0 + i * h, w, h)
            self.celle.append(("col%d" % (3 - i), r, T("col")))
        for i in range(3):
            r = pygame.Rect(x0 + w + i * 4 * w, y0 + 3 * h, 4 * w, h)
            self.celle.append(("doz%d" % (i + 1), r, T("d%d" % (i + 1))))
        fuori = (("basso", T("low")), ("pari", T("even")),
                 ("rosso", T("red")), ("nero", T("black")),
                 ("dispari", T("odd")), ("alto", T("high")))
        for i, (chiave, testo) in enumerate(fuori):
            r = pygame.Rect(x0 + w + i * 2 * w, y0 + 4 * h, 2 * w, h)
            self.celle.append((chiave, r, testo))

    def cella_di(self, n):
        """Il rettangolo di un numero, zeri compresi."""
        if n in (0, ZERO2):
            for k, r, _t in self.celle:
                if k == n:
                    return r
            return self.celle[0][1]
        return self.cella_numero(n)

    def zona(self):
        return self.celle[0][1].unionall([c[1] for c in self.celle])

    # ---- che puntata c'e' sotto la fiche
    def puntata_qui(self, pos):
        """Guarda dove sta la fiche e dice che puntata e': numero secco,
        cavallo, quartina, terzina, sestina, o una delle puntate fuori."""
        x, y = pos
        w, h, x0, y0 = self.w, self.h, self.x0, self.y0
        xg, yg = x0 + w, y0
        soglia = 0.22                 # quanto conta "vicino alla linea"
        dentro_grid = (xg - w * 0.3 <= x <= xg + 12 * w + w * 0.3 and
                       yg - h * 0.3 <= y <= yg + 3 * h + h * 0.3)
        if dentro_grid:
            fx = (x - xg) / float(w)
            fy = (y - yg) / float(h)
            j = max(0, min(11, int(fx)))
            i = max(0, min(2, int(fy)))
            dx = fx - j - 0.5
            dy = fy - i - 0.5
            su_x = abs(dx) > 0.5 - soglia
            su_y = abs(dy) > 0.5 - soglia
            j2 = j + (1 if dx > 0 else -1)
            i2 = i + (1 if dy > 0 else -1)
            fuori_y = i2 < 0 or i2 > 2
            fuori_x = j2 < 0 or j2 > 11
            if su_x and su_y:
                if fuori_y and not fuori_x:
                    # in fondo, fra due terzine: sestina
                    a, b = min(j, j2), max(j, j2)
                    return tuple(sorted([self.numero_di(a, k) for k in range(3)] +
                                        [self.numero_di(b, k) for k in range(3)]))
                if not fuori_x and not fuori_y:
                    return tuple(sorted((self.numero_di(j, i),
                                         self.numero_di(j2, i),
                                         self.numero_di(j, i2),
                                         self.numero_di(j2, i2))))
            if su_y and fuori_y:
                # in fondo alla colonna: terzina
                return tuple(sorted(self.numero_di(j, k) for k in range(3)))
            if su_x and not fuori_x:
                return tuple(sorted((self.numero_di(j, i),
                                     self.numero_di(j2, i))))
            if su_y and not fuori_y:
                return tuple(sorted((self.numero_di(j, i),
                                     self.numero_di(j, i2))))
            if su_x and fuori_x and j2 < 0:
                if DOPPIO[0]:
                    # il cesto: zero, zero doppio e i primi tre
                    return (0, 1, 2, 3, ZERO2)
                # fra lo zero e la prima colonna
                return tuple(sorted((0, self.numero_di(j, i))))
            return self.numero_di(j, i)
        for chiave, r, _t in self.celle:
            if r.collidepoint(pos):
                return chiave
        return None

    def dove_sta(self, chiave):
        """Il punto dove appoggiare la fiche di quella puntata."""
        if isinstance(chiave, tuple):
            punti = [self.cella_di(n).center for n in chiave]
            return (sum(p[0] for p in punti) // len(punti),
                    sum(p[1] for p in punti) // len(punti))
        for k, r, _t in self.celle:
            if k == chiave:
                return r.center
        return (0, 0)

    # ---- il disegno
    def disegna(self, sc, puntate, uscito, lampo, vinte=()):
        f = B.FONTS["small"]
        f_n = B.FONTS["font"]
        zona = self.zona().inflate(B.s(18), B.s(18))
        pygame.draw.rect(sc, VERDE_SCURO, zona, border_radius=B.s(8))
        pygame.draw.rect(sc, ORO, zona, max(1, B.s(2)), border_radius=B.s(8))
        for chiave, r, testo in self.celle:
            dentro = colore_numero(chiave) if isinstance(chiave, int) \
                else VERDE_PANNO
            pygame.draw.rect(sc, dentro, r)
            pygame.draw.rect(sc, (228, 226, 220), r, 1)
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
        for chiave, soldi in puntate.items():
            p = self.dove_sta(chiave)
            if chiave in vinte:
                raggio = B.s(16) + int(B.s(5) * lampo)
                q = pygame.Surface((raggio * 2, raggio * 2), pygame.SRCALPHA)
                pygame.draw.circle(q, (255, 226, 140, 90), (raggio, raggio),
                                   raggio)
                pygame.draw.circle(q, (255, 236, 170, 230), (raggio, raggio),
                                   raggio, max(1, B.s(3)))
                sc.blit(q, q.get_rect(center=p))
            disegna_pila(sc, p, soldi)


FICHE_COL = ((5, (178, 42, 48)), (10, (40, 86, 168)),
             (25, (30, 128, 74)), (100, (30, 30, 36)),
             (500, (108, 54, 150)))
FICHE_GFX = {}


def colore_fiche(soldi):
    col = FICHE_COL[0][1]
    for v, c in FICHE_COL:
        if soldi >= v:
            col = c
    return col


def _fiche_gfx(soldi, r):
    """La fiche disegnata come quelle vere: il bordo coi tacchetti
    bianchi e il tondo chiaro in mezzo per il valore. Si disegna in
    grande e si rimpicciolisce, cosi' i bordi vengono lisci."""
    chiave = (soldi, r)
    if chiave in FICHE_GFX:
        return FICHE_GFX[chiave]
    S = 4
    lato = (r + 1) * 2 * S
    q = pygame.Surface((lato, lato), pygame.SRCALPHA)
    c = lato // 2
    R = r * S
    col = colore_fiche(soldi)
    scuro = tuple(int(v * 0.52) for v in col)
    chiaro = tuple(int(v * 0.88) for v in col)
    pygame.draw.circle(q, scuro, (c, c), R)
    pygame.draw.circle(q, col, (c, c), int(R * 0.955))
    for k in range(8):
        a0 = k * math.pi / 4 - math.radians(11)
        a1 = a0 + math.radians(22)
        punti = []
        for i in range(7):
            a = a0 + (a1 - a0) * i / 6.0
            punti.append((c + math.cos(a) * R * 0.99,
                          c + math.sin(a) * R * 0.99))
        for i in range(6, -1, -1):
            a = a0 + (a1 - a0) * i / 6.0
            punti.append((c + math.cos(a) * R * 0.70,
                          c + math.sin(a) * R * 0.70))
        pygame.draw.polygon(q, (240, 240, 236), punti)
    pygame.draw.circle(q, (248, 248, 244), (c, c), int(R * 0.70),
                       max(1, int(R * 0.06)))
    pygame.draw.circle(q, chiaro, (c, c), int(R * 0.62))
    pygame.draw.circle(q, scuro, (c, c), int(R * 0.62), max(1, int(R * 0.05)))
    q = pygame.transform.smoothscale(q, ((r + 1) * 2, (r + 1) * 2))
    FICHE_GFX[chiave] = q
    return q


def disegna_fiche(sc, centro, soldi, grande=False):
    """Una fiche col suo valore sopra."""
    r = B.s(13) if grande else B.s(10)
    img = _fiche_gfx(soldi, r)
    om = pygame.Surface(img.get_size(), pygame.SRCALPHA)
    om.fill((0, 0, 0, 110))
    om.blit(img, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    sc.blit(om, om.get_rect(center=(centro[0] + B.s(2), centro[1] + B.s(3))))
    sc.blit(img, img.get_rect(center=centro))
    f = B.FONTS.get("mini") or B.FONTS["small"]
    t = f.render(str(soldi), True, (255, 255, 255))
    if t.get_width() > r * 1.1:
        t = pygame.transform.smoothscale(
            t, (int(r * 1.1), int(t.get_height() * r * 1.1 / t.get_width())))
    sc.blit(t, t.get_rect(center=centro))


def taglia(soldi):
    """Spezza la puntata nelle fiches vere: 500, 100, 25, 10, 5. Una
    puntata da 15 sono una da 10 e una da 5, non una fiche da 15."""
    pila = []
    resto = soldi
    for v, _c in reversed(FICHE_COL):
        while resto >= v:
            pila.append(v)
            resto -= v
    return pila


def disegna_pila(sc, centro, soldi):
    """La puntata sul tappeto: le fiches una sopra l'altra, con sotto
    quanto fa in tutto."""
    pila = taglia(soldi)
    if not pila:
        return
    r = B.s(10)
    troppe = len(pila) > 6
    mostra = pila[:6] if troppe else pila
    alt = B.s(4)
    x, y = centro[0], centro[1] + (len(mostra) - 1) * alt // 2
    for i, v in enumerate(reversed(mostra)):
        disegna_fiche(sc, (x, y - i * alt), v)
    f = B.FONTS.get("mini") or B.FONTS["small"]
    t = f.render(B.dollari(soldi), True, (255, 255, 255))
    p = t.get_rect(center=(x, y + r + B.s(7)))
    q = pygame.Surface(p.inflate(B.s(8), B.s(3)).size, pygame.SRCALPHA)
    q.fill((12, 14, 20, 200))
    sc.blit(q, p.inflate(B.s(8), B.s(3)))
    sc.blit(t, p)


# ------------------------------------------------------------- il gioco
def gioca_roulette(sc, clock, logo):
    """Si muove la fiche sul tappeto, si appoggia dove si vuole - anche
    sulle linee - poi si lancia la pallina."""
    carica_suoni()
    carica_voce()
    voce("v_place")
    tap = Tappeto()
    ruota = Ruota((B.WIN_W // 2, B.ALTO + B.s(176)), B.s(320))
    puntate = {}
    usciti = []
    fiche = B.CFG.get("roul_fiche", FICHES[1])
    if fiche not in FICHES:
        fiche = FICHES[1]
    zona = tap.zona()
    mano = [zona.centerx, zona.centery]     # dove sta la fiche in mano
    sel = 0
    msg, sotto, vinto = T("place"), "", 0
    lampo = 0.0
    attesa = 0.0                # quanto restano su le fiches dopo il colpo
    vinte_k = ()
    rett = []

    def voci():
        return [T("spin"), "%s  %s" % (T("chip"), B.dollari(fiche)),
                T("clear"), T("back")]

    def punta():
        nonlocal msg
        if ruota.gira or attesa > 0:
            return
        dove = tap.puntata_qui(mano)
        if dove is None:
            return
        if B.soldi() < fiche:
            msg = T("broke")
            B.suona_fx("menu_chiudi", 0.7)
            return
        B.soldi(-fiche)
        puntate[dove] = puntate.get(dove, 0) + fiche
        B.salva_config()
        B.suona_fx("menu_tic", 0.8)

    def togli():
        """Toglie la puntata che sta sotto la fiche."""
        dove = tap.puntata_qui(mano)
        if ruota.gira or attesa > 0 or dove not in puntate:
            return
        B.soldi(puntate.pop(dove))
        B.salva_config()
        B.suona_fx("menu_chiudi", 0.6)

    def pulisci():
        nonlocal msg
        if ruota.gira or attesa > 0 or not puntate:
            return
        B.soldi(sum(puntate.values()))
        puntate.clear()
        B.salva_config()
        msg = T("place")
        B.suona_fx("menu_chiudi", 0.7)

    def lancia():
        nonlocal msg, sotto, vinto
        if ruota.gira or attesa > 0 or not puntate:
            return
        ruota.lancia(random.choice(ORDINE[0]))
        msg, sotto, vinto = T("ball"), "", 0
        voce("v_nomore")
        if suona("pallina", 0.85) is None:
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
        B.aggiorna_voce()
        mouse = B.mouse_gioco()
        tasti = pygame.key.get_pressed()
        # con le frecce, con la levetta o con la croce la fiche scivola;
        # col mouse la segue
        passo = B.s(420) * dt
        vx = vy = 0.0
        if tasti[pygame.K_LEFT] or tasti[pygame.K_a]:
            vx -= 1
        if tasti[pygame.K_RIGHT] or tasti[pygame.K_d]:
            vx += 1
        if tasti[pygame.K_UP] or tasti[pygame.K_w]:
            vy -= 1
        if tasti[pygame.K_DOWN] or tasti[pygame.K_s]:
            vy += 1
        c = B.pad()
        if c is not None:
            lx = B.pad_asse(c, pygame.CONTROLLER_AXIS_LEFTX)
            ly = B.pad_asse(c, pygame.CONTROLLER_AXIS_LEFTY)
            if abs(lx) > 0.15 or abs(ly) > 0.15:
                vx += lx
                vy += ly
            if B.pad_tasto(c, pygame.CONTROLLER_BUTTON_DPAD_LEFT):
                vx -= 1
            if B.pad_tasto(c, pygame.CONTROLLER_BUTTON_DPAD_RIGHT):
                vx += 1
            if B.pad_tasto(c, pygame.CONTROLLER_BUTTON_DPAD_UP):
                vy -= 1
            if B.pad_tasto(c, pygame.CONTROLLER_BUTTON_DPAD_DOWN):
                vy += 1
        mano[0] += vx * passo
        mano[1] += vy * passo
        if B.MOUSE_VIVO[0]:
            largo = zona.inflate(B.s(60), B.s(60))
            if largo.collidepoint(mouse):
                mano[0], mano[1] = mouse
        largo = zona.inflate(B.s(40), B.s(40))
        mano[0] = max(largo.left, min(largo.right, mano[0]))
        mano[1] = max(largo.top, min(largo.bottom, mano[1]))
        for ev in B.eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pulisci()
                    B.zittisci()
                    return "su"
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                              pygame.K_SPACE):
                    punta()
                elif ev.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP,
                                pygame.K_DOWN) and getattr(ev, "dal_pad",
                                                           False):
                    # uno scatto di mezza casella, per chi va a scatti
                    mano[0] += (tap.w // 2) * (1 if ev.key == pygame.K_RIGHT
                                               else -1 if ev.key == pygame.K_LEFT
                                               else 0)
                    mano[1] += (tap.h // 2) * (1 if ev.key == pygame.K_DOWN
                                               else -1 if ev.key == pygame.K_UP
                                               else 0)
                elif ev.key == B.tasto("cambia"):
                    cambia_fiche(1)
                elif ev.key == B.tasto("gesso"):
                    lancia()
                elif ev.key == B.tasto("eff_via"):
                    togli()
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    preso = False
                    for i, r in enumerate(rett):
                        if r.collidepoint(mouse):
                            sel, preso = i, True
                            if i == 0:
                                lancia()
                            elif i == 1:
                                cambia_fiche(1)
                            elif i == 2:
                                pulisci()
                            else:
                                pulisci()
                                B.zittisci()
                                return "su"
                    if not preso:
                        punta()
                elif ev.button == 3:
                    togli()
                elif ev.button in (4, 5):
                    cambia_fiche(1 if ev.button == 4 else -1)
        if B.MOUSE_VIVO[0]:
            for i, r in enumerate(rett):
                if r.collidepoint(mouse):
                    sel = i
        if ruota.passo(dt):
            n = ruota.uscito
            usciti.insert(0, n)
            del usciti[10:]
            croupier(n)
            vinto, vinte = vincita(puntate, n)
            voce("v_win" if vinto else "v_nothing", "v_place")
            vinte_k = tuple(k for k, _r in vinte)
            if vinto:
                B.soldi(vinto)
                msg = T("win") % B.dollari(vinto)
                # cosa ha azzeccato e quanto ha reso, una per una
                sotto = "    ".join("%s  %s" % (nome_puntata(k), B.dollari(r))
                                    for k, r in vinte)
                B.suona_fx("menu_apri", 1.0)
            else:
                msg = T("no_win")
                sotto = ""
            # le fiches restano un po' sul tappeto, per vedere dov'erano
            attesa = 4.5
            B.salva_config()
        if attesa > 0:
            attesa -= dt
            if attesa <= 0:
                puntate.clear()
                vinte_k = ()

        # ---- il disegno
        sc.blit(B.fondo(), (0, 0))
        ruota.disegna(sc)
        tap.disegna(sc, puntate, ruota.uscito if not ruota.gira else None,
                    abs(math.sin(lampo * math.pi)), vinte_k)
        if not ruota.gira and attesa <= 0:
            fiche_in_mano(sc, mano, fiche, tap)
        colonna_usciti(sc, usciti)
        rett = disegna_colonna(sc, voci(), sel, fiche, puntate, msg, sotto,
                               vinto, tap)
        small = B.FONTS["small"]
        if B.modo_comandi() == "pad" and B.ICONE_TASTI_OK():
            r = B.riga_pad(small, RIGA_PAD_ROULETTE)
        else:
            r = small.render(aiuto_roulette(), True, (150, 156, 168))
        sc.blit(r, r.get_rect(center=(B.WIN_W // 2, B.WIN_H - B.s(30))))
        B.presenta()


def fiche_in_mano(sc, mano, fiche, tap):
    """La fiche che tieni in mano, con sotto scritto che puntata e' e
    quanto paga."""
    dove = tap.puntata_qui(mano)
    x, y = int(mano[0]), int(mano[1])
    if dove is not None:
        # il posto dove finirebbe, segnato in chiaro
        p = tap.dove_sta(dove)
        pygame.draw.circle(sc, (255, 255, 255), p, B.s(12), max(1, B.s(2)))
    disegna_fiche(sc, (x, y), fiche, grande=True)
    if dove is None:
        return
    paga = quanto_paga(dove)
    testo = "%s   %d:1" % (nome_puntata(dove), paga)
    f = B.FONTS["small"]
    t = f.render(testo, True, (245, 245, 240))
    r = t.get_rect(center=(x, y - B.s(30)))
    q = pygame.Surface(r.inflate(B.s(12), B.s(8)).size, pygame.SRCALPHA)
    q.fill((12, 14, 20, 210))
    sc.blit(q, r.inflate(B.s(12), B.s(8)))
    sc.blit(t, r)


def colonna_usciti(sc, usciti):
    """A sinistra, in verticale, gli ultimi numeri usciti."""
    f = B.FONTS["small"]
    x = B.s(40)
    y = B.ALTO + B.s(40)
    t = f.render(T("last"), True, (150, 156, 168))
    sc.blit(t, (x, y))
    y += t.get_height() + B.s(8)
    for n in usciti[:8]:
        r = pygame.Rect(x, y, B.s(44), B.s(26))
        pygame.draw.rect(sc, colore_numero(n), r, border_radius=B.s(4))
        pygame.draw.rect(sc, (90, 94, 104), r, 1, border_radius=B.s(4))
        q = f.render(str(n), True, (245, 245, 240))
        sc.blit(q, q.get_rect(center=r.center))
        y += B.s(30)


def disegna_colonna(sc, voci, sel, fiche, puntate, msg, sotto, vinto, tap):
    """La fascia stretta a destra: fiche, puntata, vincita e le scelte."""
    x1 = B.WIN_W - B.s(14)
    x0 = x1 - B.s(150)
    f = B.FONTS["small"]
    y = B.ALTO + B.s(30)
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
    rett = []
    f_v = B.FONTS["font"]
    B.tic_menu(tuple(voci), sel)
    passo = f_v.get_height() + B.s(14)
    y = B.ALTO + B.s(200)
    for i, testo in enumerate(voci):
        t = f_v.render(testo, True,
                       (255, 255, 255) if i == sel else (160, 166, 178))
        if t.get_width() > x1 - x0 - B.s(12):
            k = (x1 - x0 - B.s(12)) / float(t.get_width())
            t = pygame.transform.smoothscale(
                t, (int(t.get_width() * k), int(t.get_height() * k)))
        fondo = pygame.Rect(x0 - B.s(8), y - (passo - B.s(8)) // 2,
                            x1 - x0 + B.s(16), passo - B.s(8))
        if i == sel:
            q = pygame.Surface(fondo.size, pygame.SRCALPHA)
            q.fill((255, 255, 255, 16))
            sc.blit(q, fondo)
            pygame.draw.rect(sc, ORO, (fondo.x, fondo.y, max(1, B.s(3)),
                                       fondo.h))
        sc.blit(t, t.get_rect(midleft=(x0, y)))
        rett.append(fondo)
        y += passo
    zona = tap.zona()
    t = f_v.render(msg, True, (255, 226, 140) if vinto else (235, 238, 245))
    sc.blit(t, t.get_rect(center=(zona.centerx, zona.bottom + B.s(46))))
    if sotto:
        q = f.render(sotto, True, (255, 226, 140))
        largo = B.WIN_W - B.s(360)
        if q.get_width() > largo:
            k = largo / float(q.get_width())
            q = pygame.transform.smoothscale(
                q, (largo, int(q.get_height() * k)))
        sc.blit(q, q.get_rect(center=(zona.centerx, zona.bottom + B.s(74))))
    return rett


def schermata_roulette(sc, clock, logo):
    """Il menu della roulette: si sceglie a che tavolo giocare. Stesso
    vestito degli altri menu: sfondo, carattere elegante, valori in oro."""
    nomi = [t[0] for t in TAVOLI]
    scelto = B.CFG.get("roul_tavolo", "europea")
    sel = nomi.index(scelto) if scelto in nomi else 0
    rett = []

    def scelta(i):
        if i >= len(TAVOLI):
            return "su"
        scegli_tavolo(nomi[i])
        B.CFG["roul_tavolo"] = nomi[i]
        B.salva_config()
        B.suona_fx("menu_apri", 0.8)
        return gioca_roulette(sc, clock, logo)

    while True:
        clock.tick(60)
        mouse = B.mouse_gioco()
        n = len(TAVOLI) + 1
        for ev in B.eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    sel = (sel + 1) % n
                if ev.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % n
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                              pygame.K_SPACE):
                    q = scelta(sel)
                    if q in ("quit", "su"):
                        return q
                    break
                if ev.key == pygame.K_ESCAPE:
                    return "su"
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(rett):
                    if r.collidepoint(mouse):
                        q = scelta(i)
                        if q in ("quit", "su"):
                            return q
                        break
        font, small = B.FONTS["font"], B.FONTS["small"]
        B.sfondo_menu(sc, logo)
        t = small.render(T("roulette"), True, B.ORO_SOTTO)
        sc.blit(t, t.get_rect(center=(B.WIN_W // 2, B.s(270))))
        voci = [(T(et), T(et + "_d")) for _n, et, _o, _d, _p in TAVOLI]
        voci.append((T("back"), None))
        rett = B.disegna_voci(sc, voci, sel, font, small, B.s(360), B.s(56))
        for i, r in enumerate(rett):
            if B.MOUSE_VIVO[0] and r.collidepoint(mouse):
                sel = i
        B.presenta()
