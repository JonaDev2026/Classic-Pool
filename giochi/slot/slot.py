"""Golden Break - la slot machine.

Cinque colonne per quattro righe, venti linee fisse, i rulli che si
fermano uno dopo l'altro. Qui c'e' il motore: le strisce dei rulli, il
conto delle vincite e il tabellone dei pagamenti. La grafica dei simboli
sta fuori, in immagini/slot/<tema>: finche' non c'e' si disegnano dei
segnaposto, cosi' la macchina si puo' provare lo stesso.

Si appoggia a biliardo.py per finestra, caratteri, sfondo, suoni e
portafoglio, come fanno le carte.
"""
import colorsys
import math
import os
import random
import re
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
GFX = os.path.join(RADICE, "immagini", "slot")

# ----------------------------------------------------------- i simboli
# id, colore del segnaposto, segno, e quanto paga con 3, 4 e 5 uguali
# (per ogni dollaro puntato sulla linea)
# nome, colore di riserva, segno di riserva, e quanto paga con 2, 3, 4 e
# 5 rulli di fila (per ogni unita' di puntata). Lo zero vuol dire che con
# quel numero di rulli non paga.
SIMBOLI = (
    ("ciliegia",     (226,  80, 110), "C",   8,  18,  38,   95),
    ("limone",       (232, 224,  90), "L",   9,  19,  39,   98),
    ("arancia",      (240, 150,  60), "O",  10,  20,  40,  100),
    ("prugna",       (150, 110, 200), "P",  11,  21,  41,  102),
    ("mela",         (120, 200, 100), "M",  12,  22,  42,  105),
    ("fragola",      (232,  90, 100), "F",  13,  23,  44,  108),
    ("anguria",      (236, 120, 150), "A",  14,  24,  46,  112),
    ("uva",          (150, 110, 190), "U",  15,  25,  48,  115),
    ("cuori",        (230,  70,  90), "H",   0,  28,  58,  145),
    ("picche",       (150, 110, 230), "S",   0,  29,  59,  148),
    ("fiori",        ( 80, 120, 220), "K",   0,  30,  60,  150),
    ("quadri",       (226,  50,  90), "D",   0,  31,  61,  152),
    ("campana",      (240, 190,  70), "B",   0,  32,  62,  155),
    ("ferro",        (200, 205, 215), "V",   0,  34,  64,  158),
    ("quadrifoglio", ( 90, 200, 110), "Q",   0,  35,  66,  162),
    ("carte",        (240, 240, 245), "T",   0,  58, 145,  390),
    ("roulette",     ( 90, 170, 190), "R",   0,  60, 150,  400),
    ("fiches",       (220, 100, 130), "G",   0,  62, 155,  410),
    ("dollaro",      (240, 190,  70), "$",   0,  65, 160,  420),
    ("gemma",        (140, 210, 240), "^",   0, 140, 480, 1900),
    ("bar",          ( 60, 180, 220), "=",   0, 150, 500, 2000),
    ("sette",        (226,  60,  60), "7",   0, 160, 550, 2200),
    ("jolly",        (250, 250, 250), "W", 0,   0,   0,    0),  # vale per tutti
    ("dadi",         (180, 186, 200), "?", 0,   0,   0,    0),  # giri gratis
    ("regalo",       ( 90, 210, 220), "*", 0,   0,   0,    0),  # premio a caso
    ("jackpot",      (255, 214,  92), "J", 0,   0,   0,    0),  # il jackpot
)
PAGA = dict((s[0], (s[3], s[4], s[5], s[6])) for s in SIMBOLI)
COLORE = dict((s[0], s[1]) for s in SIMBOLI)
SEGNO = dict((s[0], s[2]) for s in SIMBOLI)
JOLLY = "jolly"
REGALO = "regalo"           # tre o piu': un premio a caso
DADI = "dadi"               # tre o piu': giri gratis
GIRI_GRATIS = 3             # quanti ne regalano i dadi
PREMIO_REGALO = {3: (2, 8), 4: (8, 25), 5: (30, 100)}   # in puntate


COLONNE, RIGHE = 5, 4

# la griglia paga a modi, non a linee: 4 righe per 5 rulli fanno 1024
# strade possibili, e la puntata si divide in venti unita' come prima
MODI = RIGHE ** COLONNE
MODI_UNITA = 20

# quante copie di ogni simbolo ci sono sulla striscia di ogni rullo: i
# simboli che pagano tanto sono rari, il jolly e il mistero non stanno
# sul primo e sull'ultimo rullo
QUANTI = {
    "ciliegia":     (5, 5, 5, 5, 5),
    "limone":       (5, 5, 5, 5, 5),
    "arancia":      (5, 5, 5, 5, 5),
    "prugna":       (5, 5, 5, 5, 5),
    "mela":         (5, 5, 5, 5, 5),
    "fragola":      (5, 5, 5, 5, 5),
    "anguria":      (4, 4, 4, 4, 4),
    "uva":          (4, 4, 4, 4, 4),
    "cuori":        (9, 9, 9, 9, 9),
    "picche":       (9, 9, 9, 9, 9),
    "fiori":        (9, 9, 9, 9, 9),
    "quadri":       (9, 9, 9, 9, 9),
    "campana":      (4, 4, 4, 4, 4),
    "ferro":        (4, 4, 4, 4, 4),
    "quadrifoglio": (4, 4, 4, 4, 4),
    "carte":        (3, 3, 3, 3, 3),
    "roulette":     (3, 3, 3, 3, 3),
    "fiches":       (3, 3, 3, 3, 3),
    "dollaro":      (2, 2, 2, 2, 2),
    "gemma":        (2, 2, 2, 2, 2),
    "bar":          (2, 2, 2, 2, 2),
    "sette":        (2, 2, 2, 2, 2),
    "jolly":        (0, 3, 3, 3, 0),
    "dadi":         (2, 2, 2, 2, 2),
    "regalo":       (2, 2, 2, 2, 2),
    "jackpot":      (5, 5, 5, 5, 5),
}

PUNTATE = (20, 50, 100, 250, 500, 1000)   # quanto si gioca a giro

# il jackpot: parte da qui, cresce di una fetta di ogni puntata e si
# vince con cinque simboli del jackpot in fila su una linea. Sta nel
# file del giocatore, quindi cresce di partita in partita finche' non si
# vince o non si ricomincia la carriera.
JACKPOT_BASE = 500
JACKPOT_FETTA = 0.02
SIMBOLO_JACKPOT = "jackpot"


def jackpot(agg=None):
    """Quanto vale adesso il jackpot, o ce ne mette dentro dell'altro."""
    ora = int(B.CFG.get("slot_jackpot", JACKPOT_BASE) or JACKPOT_BASE)
    if agg:
        ora = max(JACKPOT_BASE, ora + int(agg))
        B.CFG["slot_jackpot"] = ora
    return ora


def azzera_jackpot():
    B.CFG["slot_jackpot"] = JACKPOT_BASE
    return JACKPOT_BASE


def fa_jackpot(griglia):
    """Il jackpot vuole il suo simbolo su tutti e cinque i rulli, e
    quelli veri: il jolly non lo fa."""
    for c in range(COLONNE):
        if not any(griglia[c][r] == SIMBOLO_JACKPOT for r in range(RIGHE)):
            return False
    return True


def _buona(s):
    """Una striscia va bene se non ha due simboli uguali attaccati e se i
    bonus stanno lontani fra loro almeno quanto e' alta la finestra: cosi'
    un rullo non ne mostra mai due insieme e i conti dei pagamenti
    tornano sempre uguali."""
    n = len(s)
    if any(s[i] == s[i - 1] for i in range(n)):
        return False
    dove = [i for i, x in enumerate(s) if x == REGALO]
    for a in range(len(dove)):
        for b in range(a + 1, len(dove)):
            d = abs(dove[a] - dove[b])
            if min(d, n - d) < RIGHE:
                return False
    return True


def strisce():
    """Le cinque strisce dei rulli, una per colonna."""
    fuori = []
    for r in range(COLONNE):
        s = []
        for nome, quanti in QUANTI.items():
            s += [nome] * quanti[r]
        for _ in range(4000):
            random.shuffle(s)
            if _buona(s):
                break
        fuori.append(list(s))
    return fuori


def tira(strisce_ora):
    """Un giro: da ogni striscia si prende una finestra di quattro
    simboli. Torna la griglia [colonna][riga] e dove si e' fermata."""
    griglia, fermi = [], []
    for s in strisce_ora:
        p = random.randrange(len(s))
        fermi.append(p)
        griglia.append([s[(p + i) % len(s)] for i in range(RIGHE)])
    return griglia, fermi


def paganti():
    return [x[0] for x in SIMBOLI if any(PAGA[x[0]])]


def quanti_ce_ne(griglia, nome):
    """Le caselle con quel simbolo, dovunque stiano."""
    return [(c, r) for c in range(COLONNE) for r in range(RIGHE)
            if griglia[c][r] == nome]


def premio_regalo(quanti, punta):
    """Il pacchetto regalo: tre o piu' dovunque siano, e dentro c'e' un
    premio a caso, tanto piu' grosso quanti pacchetti sono."""
    da, a = PREMIO_REGALO[min(5, quanti)]
    return int(round(random.uniform(da, a) * punta))


def vincite(griglia, unita):
    """I mille e ventiquattro modi: conta solo che lo stesso simbolo esca
    su rulli attaccati partendo da sinistra, dovunque stia nella colonna.
    Se su un rullo ce n'e' piu' d'uno le strade si moltiplicano. I
    simboli comuni pagano gia' con due rulli, gli altri da tre in su.

    Torna il totale e l'elenco: (nome, quanti rulli, strade, quanto paga,
    le caselle da accendere)."""
    fuori = []
    for nome in paganti():
        conta, dove = [], []
        for c in range(COLONNE):
            celle = [(c, r) for r in range(RIGHE)
                     if griglia[c][r] in (nome, JOLLY)]
            conta.append(len(celle))
            dove.append(celle)
        strade, lung = 1, 0
        for c in range(COLONNE):
            if not conta[c]:
                break
            strade *= conta[c]
            lung += 1
        if lung < 2:
            continue
        quanto = PAGA[nome][min(lung, 5) - 2]
        if not quanto:
            continue
        paga = int(round(quanto * strade * unita))
        celle = [x for c in range(lung) for x in dove[c]]
        fuori.append((nome, lung, strade, paga, celle))
    return sum(v[3] for v in fuori), fuori


# ------------------------------------------------------------- i testi
TXT = {
    "en": {"slot": "Slots", "spin": "Spin", "play": "Play",
           "m_prova": "Test machine", "bet": "Bet", "pays": "Paytable",
           "back": "Back", "win": "You win %s", "no_win": "No win",
           "broke": "Not enough money", "tot_bet": "Total bet",
           "per_line": "Per unit", "lines": "Ways",
           "free_spins": "Free spins", "win_row": "Win", "won_free": "%d free spins",
           "ways_win": "%d x %s  on %d ways", "credit": "Credit",
           "jackpot": "Jackpot", "won_jack": "JACKPOT!  %s",
           "pt_jack": "One on each of the five reels wins the jackpot: %s",
           "pt_title": "Paytable", "pt_bet": "prizes at a bet of %s", "pt_wild": "Wild: stands for any symbol",
           "pt_gift": "Gift: three or more anywhere, with a random prize inside",
           "pt_dice": "Dice: three or more anywhere win %d free spins",
           "pt_bonus": "Bonus: pays anywhere, on the total bet",
           "pt_line": "Same symbol on touching reels from the left, in any position: %d ways. The numbers are per way, so a win on three ways pays three times.",
           "help": "click / ENTER  spin     < >  bet     %s  paytable     ESC  back",
           "sp_spin": "spin", "sp_bet": "bet", "sp_pays": "paytable", "help_pt": "ENTER / ESC  back"},
    "it": {"slot": "Slot", "spin": "Gira", "play": "Gioca",
           "m_prova": "Slot di prova", "bet": "Puntata",
           "pays": "Pagamenti", "back": "Indietro", "win": "Vinci %s",
           "no_win": "Niente", "broke": "Non hai abbastanza soldi",
           "tot_bet": "Puntata", "per_line": "Per unita", "lines": "Modi",
           "free_spins": "Giri gratis", "win_row": "Vincita", "won_free": "%d giri gratis",
           "ways_win": "%d x %s  su %d modi",
           "credit": "Credito", "jackpot": "Jackpot",
           "won_jack": "JACKPOT!  %s",
           "pt_jack": "Uno su ognuno dei cinque rulli vince il jackpot: %s",
           "pt_title": "Pagamenti", "pt_bet": "premi alla puntata di %s",
           "pt_wild": "Jolly: vale per tutti i simboli",
           "pt_gift": "Regalo: tre o piu' dovunque siano, e dentro c'e' un premio a caso",
           "pt_dice": "Dadi: tre o piu' dovunque siano vincono %d giri gratis",
           "pt_bonus": "Bonus: paga dovunque sia, sulla puntata intera",
           "pt_line": "Stesso simbolo su rulli attaccati da sinistra, in qualunque posizione: %d modi. I numeri sono per ogni modo, quindi una vincita su tre modi paga tre volte.",
           "help": "clic / INVIO  gira     < >  puntata     %s  pagamenti     ESC  indietro",
           "sp_spin": "gira", "sp_bet": "puntata", "sp_pays": "pagamenti", "help_pt": "INVIO / ESC  indietro"},
    "fr": {"slot": "Machine", "spin": "Tourner", "play": "Jouer",
           "m_prova": "Machine d'essai", "bet": "Mise",
           "pays": "Gains", "back": "Retour", "win": "Vous gagnez %s",
           "no_win": "Rien", "broke": "Pas assez d'argent",
           "tot_bet": "Mise", "per_line": "Par unite", "lines": "Facons",
           "free_spins": "Tours gratuits", "win_row": "Gain", "won_free": "%d tours gratuits",
           "ways_win": "%d x %s  sur %d facons",
           "credit": "Credit", "jackpot": "Jackpot",
           "won_jack": "JACKPOT !  %s",
           "pt_jack": "Un sur chacun des cinq rouleaux gagne le jackpot : %s",
           "pt_title": "Table des gains", "pt_bet": "gains pour une mise de %s",
           "pt_wild": "Joker : remplace tous les symboles",
           "pt_gift": "Cadeau : trois ou plus n'importe ou, avec un prix au hasard",
           "pt_dice": "Des : trois ou plus n'importe ou gagnent %d tours gratuits",
           "pt_bonus": "Bonus : paie partout, sur la mise totale",
           "pt_line": "Meme symbole sur des rouleaux voisins depuis la gauche : %d facons. Les gains sont par facon.",
           "help": "clic / ENTREE  tourner     < >  mise     %s  gains     ECHAP  retour",
           "sp_spin": "tourner", "sp_bet": "mise", "sp_pays": "gains", "help_pt": "ENTREE / ECHAP  retour"},
    "es": {"slot": "Tragaperras", "spin": "Girar", "play": "Jugar",
           "m_prova": "Tragaperras de prueba", "bet": "Apuesta",
           "pays": "Premios", "back": "Atras", "win": "Ganas %s",
           "no_win": "Nada", "broke": "No tienes bastante dinero",
           "tot_bet": "Apuesta", "per_line": "Por unidad", "lines": "Modos",
           "free_spins": "Giros gratis", "win_row": "Ganancia", "won_free": "%d giros gratis",
           "ways_win": "%d x %s  en %d modos",
           "credit": "Credito", "jackpot": "Jackpot",
           "won_jack": "JACKPOT!  %s",
           "pt_jack": "Uno en cada uno de los cinco rodillos gana el jackpot: %s",
           "pt_title": "Tabla de premios", "pt_bet": "premios con apuesta de %s",
           "pt_wild": "Comodin: vale por todos los simbolos",
           "pt_gift": "Regalo: tres o mas donde sea, con un premio al azar",
           "pt_dice": "Dados: tres o mas donde sea ganan %d giros gratis",
           "pt_bonus": "Bonus: paga donde sea, sobre la apuesta total",
           "pt_line": "Mismo simbolo en rodillos seguidos desde la izquierda: %d modos. Los premios son por modo.",
           "help": "clic / INTRO  girar     < >  apuesta     %s  premios     ESC  atras",
           "sp_spin": "girar", "sp_bet": "apuesta", "sp_pays": "premios", "help_pt": "INTRO / ESC  atras"},
}
NOMI_SIM = {
    "en": {"ciliegia": "Cherry", "limone": "Lemon", "arancia": "Orange",
           "prugna": "Plum", "mela": "Apple", "fragola": "Strawberry",
           "anguria": "Melon", "uva": "Grapes", "cuori": "Heart",
           "picche": "Spade", "fiori": "Club", "quadri": "Diamond",
           "campana": "Bell", "ferro": "Horseshoe",
           "quadrifoglio": "Clover", "carte": "Cards", "roulette": "Wheel",
           "fiches": "Chips", "dollaro": "Coin", "gemma": "Gem",
           "bar": "Bar", "sette": "Seven", "jolly": "Wild",
           "dadi": "Dice", "regalo": "Gift", "jackpot": "Jackpot"},
    "it": {"ciliegia": "Ciliegia", "limone": "Limone", "arancia": "Arancia",
           "prugna": "Prugna", "mela": "Mela", "fragola": "Fragola",
           "anguria": "Anguria", "uva": "Uva", "cuori": "Cuori",
           "picche": "Picche", "fiori": "Fiori", "quadri": "Quadri",
           "campana": "Campana", "ferro": "Ferro di cavallo",
           "quadrifoglio": "Quadrifoglio", "carte": "Carte",
           "roulette": "Roulette", "fiches": "Fiches", "dollaro": "Moneta",
           "gemma": "Gemma", "bar": "Bar", "sette": "Sette",
           "jolly": "Jolly", "dadi": "Dadi", "regalo": "Regalo",
           "jackpot": "Jackpot"},
    "fr": {"ciliegia": "Cerise", "limone": "Citron", "arancia": "Orange",
           "prugna": "Prune", "mela": "Pomme", "fragola": "Fraise",
           "anguria": "Pasteque", "uva": "Raisin", "cuori": "Coeur",
           "picche": "Pique", "fiori": "Trefle", "quadri": "Carreau",
           "campana": "Cloche", "ferro": "Fer a cheval",
           "quadrifoglio": "Trefle porte-bonheur", "carte": "Cartes",
           "roulette": "Roulette", "fiches": "Jetons", "dollaro": "Piece",
           "gemma": "Gemme", "bar": "Bar", "sette": "Sept",
           "jolly": "Joker", "dadi": "Des", "regalo": "Cadeau",
           "jackpot": "Jackpot"},
    "es": {"ciliegia": "Cereza", "limone": "Limon", "arancia": "Naranja",
           "prugna": "Ciruela", "mela": "Manzana", "fragola": "Fresa",
           "anguria": "Sandia", "uva": "Uvas", "cuori": "Corazon",
           "picche": "Pica", "fiori": "Trebol", "quadri": "Diamante",
           "campana": "Campana", "ferro": "Herradura",
           "quadrifoglio": "Trebol de cuatro", "carte": "Cartas",
           "roulette": "Ruleta", "fiches": "Fichas", "dollaro": "Moneda",
           "gemma": "Gema", "bar": "Bar", "sette": "Siete",
           "jolly": "Comodin", "dadi": "Dados", "regalo": "Regalo",
           "jackpot": "Jackpot"},
}


def T(k):
    d = TXT.get(B.CFG.get("lingua", "en"), TXT["en"])
    return d.get(k, TXT["en"].get(k, k))


def nome_simbolo(s):
    d = NOMI_SIM.get(B.CFG.get("lingua", "en"), NOMI_SIM["en"])
    return d.get(s, s)


# la riga dei comandi col joystick, con le icone come nel resto del gioco
RIGA_PAD_SLOT = ((("croce",), "sl_move"), (("a",), "sl_ok"),
                 (("b",), "pa_back"))
for _l, _d in (
        ("en", {"sl_move": "choose", "sl_ok": "ok"}),
        ("it", {"sl_move": "scegli", "sl_ok": "ok"}),
        ("fr", {"sl_move": "choisir", "sl_ok": "ok"}),
        ("es", {"sl_move": "elegir", "sl_ok": "ok"})):
    B.TESTI.setdefault(_l, {}).update(_d)

SUONI = {}
DURATE = {}


def carica_suoni():
    """I suoni della slot, da audio/slot/fx. I file col trattino e un
    numero stanno insieme: vinci1-1, vinci1-2... sono tutti "vinci1", e
    a ogni vincita se ne sente uno a caso."""
    if SUONI or not B.MUSICA_OK:
        return
    cartella = os.path.join(B.SUONI_DIR, "slot", "fx")
    if not os.path.isdir(cartella):
        return
    for f in sorted(os.listdir(cartella)):
        if not f.lower().endswith((".ogg", ".wav", ".mp3")):
            continue
        nome = re.sub(r"-\d+$", "", os.path.splitext(f)[0].lower())
        try:
            s = pygame.mixer.Sound(os.path.join(cartella, f))
            SUONI.setdefault(nome, []).append(s)
            DURATE[nome] = s.get_length()
        except pygame.error:
            pass


# a chi tocca quale suono: il regalo usa "bonus", il jolly dentro una
# vincita usa "transform", la vincita piccola "gift". Vinci2 e vinci3
# arrivano quando ci saranno i file, per ora suona quello piccolo.
RIPIEGO = {"regalo": "bonus", "jolly": "transform", "dadi": "transform",
           "vinci2": "vinci1", "vinci3": "vinci2"}


def suona(nome, quanto=0.9):
    gruppo = SUONI.get(nome) or SUONI.get(RIPIEGO.get(nome, ""))
    v = B.CFG.get("effetti", 100) / 100.0
    if not gruppo or v <= 0:
        return None
    s = random.choice(gruppo)
    s.stop()                # se stava ancora suonando, ricomincia
    s.set_volume(min(1.0, v * quanto))
    s.play()
    return s


def ferma_suono(nome):
    for s in SUONI.get(nome, []):
        s.stop()


def quanto_dura(nome, se_manca):
    """Quanto dura quel suono; se non c'e', il tempo di riserva."""
    return DURATE.get(nome, se_manca)


_FONT = {}


def font_slot(misura):
    if misura not in _FONT:
        _FONT[misura] = B.carattere_elegante(B.s(misura)) or B.FONTS["small"]
    return _FONT[misura]


def aiuto_slot():
    """La riga d'aiuto con mouse e tastiera: i tasti veri."""
    return T("help") % B.nome_tasto(B.tasto("gesso"))


# ---------------------------------------------------------- la grafica
FIGURE = {}


def tema():
    return B.CFG.get("slot_tema", "classica")


def figura(nome, misura):
    """Il disegno di un simbolo, della misura voluta. Se la PNG del tema
    non c'e' si disegna un segnaposto: cosi' la macchina si prova anche
    senza grafica."""
    chiave = (tema(), nome, misura)
    if chiave in FIGURE:
        return FIGURE[chiave]
    w, h = misura
    q = None
    f = os.path.join(GFX, tema(), nome + ".png")
    if os.path.isfile(f):
        try:
            img = pygame.image.load(f).convert_alpha()
            k = min(w / float(img.get_width()), h / float(img.get_height()))
            q = pygame.transform.smoothscale(
                img, (max(1, int(img.get_width() * k)),
                      max(1, int(img.get_height() * k))))
        except (pygame.error, OSError):
            q = None
    if q is None:
        q = pygame.Surface((w, h), pygame.SRCALPHA)
        col = COLORE[nome]
        r = pygame.Rect(w // 10, h // 10, w - w // 5, h - h // 5)
        pygame.draw.rect(q, col + (230,), r, border_radius=int(h * 0.18))
        pygame.draw.rect(q, (14, 14, 18, 220), r, max(1, B.s(2)),
                         border_radius=int(h * 0.18))
        f_s = B.FONTS["grande"]
        t = f_s.render(SEGNO[nome], True, (18, 18, 22))
        if t.get_width() > r.w * 0.7:
            k = r.w * 0.7 / float(t.get_width())
            t = pygame.transform.smoothscale(
                t, (int(t.get_width() * k), int(t.get_height() * k)))
        q.blit(t, t.get_rect(center=r.center))
    FIGURE[chiave] = q
    return q


FONDO_SLOT = [None]


def fondo_slot():
    """Il fondo della slot: scuro e tutto suo, non quello del casino'.
    Cosi' la macchina non e' semitrasparente sopra la sala."""
    if FONDO_SLOT[0] is None or FONDO_SLOT[0].get_size() != (B.WIN_W,
                                                             B.WIN_H):
        q = pygame.Surface((B.WIN_W, B.WIN_H))
        for y in range(B.WIN_H):
            k = y / float(max(1, B.WIN_H - 1))
            q.fill((int(9 + 8 * k), int(10 + 10 * k), int(16 + 14 * k)),
                   (0, y, B.WIN_W, 1))
        FONDO_SLOT[0] = q
    return FONDO_SLOT[0]


def colore_neon(t, giro=7.0):
    """Un colore che gira piano su tutta la ruota: serve alla cornice."""
    h = (t / giro) % 1.0
    r, g, b = colorsys.hsv_to_rgb(h, 0.75, 1.0)
    return (int(r * 255), int(g * 255), int(b * 255))


def cornice_neon(sc, r, t, raggio=None):
    """La cornice luminosa attorno alla macchina: tre tratti uno dentro
    l'altro, col colore che scorre."""
    raggio = raggio if raggio is not None else B.s(14)
    for i, (allarga, spesso, alfa) in enumerate((
            (B.s(7), max(1, B.s(7)), 40), (B.s(3), max(1, B.s(4)), 90),
            (0, max(1, B.s(2)), 255))):
        col = colore_neon(t + i * 0.35)
        rr = r.inflate(allarga * 2, allarga * 2)
        q = pygame.Surface(rr.size, pygame.SRCALPHA)
        pygame.draw.rect(q, col + (alfa,), q.get_rect(), spesso,
                         border_radius=raggio + allarga)
        sc.blit(q, rr)


VETRO = [None]


def vetro_fondo(misura):
    """Il fondo dei rulli: crema, come i rulli veri delle macchine di una
    volta, con un'ombra leggera in alto e in basso."""
    if VETRO[0] is None or VETRO[0].get_size() != misura:
        w, h = misura
        q = pygame.Surface(misura)
        for y in range(h):
            k = abs(y - h * 0.5) / (h * 0.5)      # 0 in mezzo, 1 ai bordi
            v = 1.0 - 0.18 * k * k
            q.fill((int(246 * v), int(241 * v), int(228 * v)),
                   (0, y, w, 1))
        VETRO[0] = q
    return VETRO[0]


COL_SIMBOLO = {}


def colore_simbolo(nome):
    """Il colore del simbolo, preso dal suo disegno: la media dei pixel
    pieni, tirata su di vivacita' cosi' si stacca sul crema del rullo."""
    if nome in COL_SIMBOLO:
        return COL_SIMBOLO[nome]
    img = figura(nome, (B.s(40), B.s(40)))
    r = g = b = n = 0
    w, h = img.get_size()
    for x in range(0, w, 2):
        for y in range(0, h, 2):
            c = img.get_at((x, y))
            if c.a < 140 or (c.r > 235 and c.g > 235 and c.b > 235):
                continue
            r += c.r
            g += c.g
            b += c.b
            n += 1
    if not n:
        col = COLORE.get(nome, (255, 255, 255))
    else:
        col = [r // n, g // n, b // n]
        m = max(col)
        if m:
            k = 235.0 / m
            col = [min(255, int(v * k)) for v in col]
        med = sum(col) / 3.0
        col = tuple(max(0, min(255, int(med + (v - med) * 1.5)))
                    for v in col)
    COL_SIMBOLO[nome] = col
    return col


NEON = {}


def neon(misura, col, spesso=None):
    """Un alone morbido attorno a una casella: tanti riquadri arrotondati
    uno dentro l'altro, sempre piu' accesi. Sul nero fa il neon."""
    w, h = misura
    m = spesso or max(B.s(14), h // 6)
    chiave = (w, h, col, m)
    if chiave in NEON:
        return NEON[chiave]
    q = pygame.Surface((w + m * 2, h + m * 2), pygame.SRCALPHA)
    passi = max(4, m // max(1, B.s(2)))
    for i in range(passi):
        k = i / float(passi - 1)            # 0 fuori, 1 dentro
        d = int(m * (1 - k))
        r = pygame.Rect(d, d, w + (m - d) * 2, h + (m - d) * 2)
        a = int(12 + 70 * k * k)
        pygame.draw.rect(q, col + (a,), r, max(1, B.s(3)),
                         border_radius=int(h * 0.22) + d // 2)
    NEON[chiave] = q
    return q


# ogni combinazione che lampeggia ha il suo colore, a turno
COLORI_VINTE = ((120, 230, 255), (255, 170, 205), (160, 245, 170),
                (255, 214, 130), (200, 170, 255), (255, 150, 120))


# quanto della casella riempie il simbolo: piu' piccolo respira meglio
GRANDE = 0.66


class Macchina:
    """La slot sullo schermo: la cassa, i cinque rulli e quello che
    succede a ogni giro."""

    def __init__(self, sc, clock):
        self.sc, self.clock = sc, clock
        self.dt = 0.0
        self.strisce = strisce()
        self.pos = [float(random.randrange(len(s))) for s in self.strisce]
        self.da, self.a, self.t, self.durata = None, None, None, None
        self.griglia = self.ferma()
        self.vinte, self.mostra, self.t_mostra = [], -1, 0.0
        self.t_vinta = 0.0      # per far respirare i simboli vincenti
        self.sotto = ""         # la riga piccola sotto il totale
        self.totale = 0         # quanto ha pagato tutto il giro
        self.gratis = 0         # i giri gratis che restano
        self.lampo = 0.0        # quanto dura il lampo del jackpot vinto
        self.t_neon = 0.0       # il colore che gira nella cornice
        self.msg = ""
        self.vinto = 0
        self.gira = False
        # la cassa: a sinistra il vetro coi rulli, a destra la fascia
        # delle scelte, come al tavolo da carte
        largo = B.WIN_W - B.s(300)
        self.cassa = pygame.Rect(B.s(40), B.ALTO + B.s(70),
                                 largo - B.s(60),
                                 B.WIN_H - B.ALTO - B.s(200))
        m = B.s(16)
        self.vetro = self.cassa.inflate(-m * 2, -m * 2)
        self.cella = (self.vetro.w // COLONNE, self.vetro.h // RIGHE)

    # ---- i rulli
    def ferma(self):
        """I simboli fermi adesso, dalla posizione di ogni rullo."""
        g = []
        for c, s in enumerate(self.strisce):
            p = int(self.pos[c]) % len(s)
            g.append([s[(p + i) % len(s)] for i in range(RIGHE)])
        return g

    def parti(self):
        """Lancia i rulli: si sa gia' dove si fermano, e ognuno ci arriva
        rallentando, uno dopo l'altro."""
        griglia, fermi = tira(self.strisce)
        self.griglia = griglia
        self.da = list(self.pos)
        self.a = []
        for c, p in enumerate(fermi):
            s = len(self.strisce[c])
            giri = 4 + c
            avanti = (p - self.da[c]) % s
            self.a.append(self.da[c] + giri * s + avanti)
        # l'ultimo rullo si ferma esattamente quando finisce il suono del
        # giro; gli altri arrivano prima, a distanza uguale
        giro = quanto_dura("spin", 2.0)
        primo = giro * 0.45
        passo = (giro - primo) / max(1, COLONNE - 1)
        self.durata = [primo + c * passo for c in range(COLONNE)]
        self.t = 0.0
        self.gira = True
        self.vinte, self.mostra, self.vinto = [], -1, 0
        self.msg = ""

    def passo(self):
        if not self.gira:
            return
        self.t += self.dt
        finiti = 0
        for c in range(COLONNE):
            d = self.durata[c]
            if self.t >= d:
                if self.pos[c] != self.a[c]:
                    self.pos[c] = self.a[c]
                    suona("stop", 0.7)
                finiti += 1
            else:
                k = self.t / d
                k = 1 - (1 - k) ** 3          # parte forte e rallenta
                self.pos[c] = self.da[c] + (self.a[c] - self.da[c]) * k
        if finiti == COLONNE:
            self.gira = False
            return True
        return False

    # ---- il disegno
    def disegna(self, voci, sel, per_linea):
        sc = self.sc
        sc.blit(B.fondo(), (0, 0))
        # la cassa: un pannello scuro pieno, con la luce che gira intorno
        pygame.draw.rect(sc, (13, 15, 21), self.cassa,
                         border_radius=B.s(14))
        cornice_neon(sc, self.cassa, self.t_neon)
        self.disegna_jackpot()
        self.disegna_rulli()
        self.disegna_sotto()
        self.disegna_scelte(voci, sel)
        self.disegna_pannello(per_linea)
        small = B.FONTS["small"]
        if B.modo_comandi() == "pad" and B.ICONE_TASTI_OK():
            r = B.riga_pad(small, RIGA_PAD_SLOT)
        else:
            r = small.render(aiuto_slot(), True, (150, 156, 168))
        sc.blit(r, r.get_rect(center=(B.WIN_W // 2, B.WIN_H - B.s(40))))

    def nome_gioco(self):
        f = B.FONTS.get("elegante_voce") or B.FONTS["font"]
        t = f.render(B.tit_el(T("slot")), True, B.ORO_SCELTA)
        self.sc.blit(t, (B.s(18), B.ALTO + B.s(10)))

    def disegna_rulli(self):
        sc = self.sc
        vetro = self.vetro
        sc.blit(vetro_fondo(vetro.size), vetro)
        cw, ch = self.cella
        vecchio = sc.get_clip()
        sc.set_clip(vetro)
        acceso = set()
        if 0 <= self.mostra < len(self.vinte):
            acceso = set(self.vinte[self.mostra][4])
        for c in range(COLONNE):
            s = self.strisce[c]
            p = self.pos[c]
            base = int(p)
            sotto = (p - base) * ch
            for i in range(-1, RIGHE + 1):
                nome = s[(base + i) % len(s)]
                r = pygame.Rect(vetro.x + c * cw,
                                int(vetro.y + i * ch - sotto), cw, ch)
                img = figura(nome, (int(cw * GRANDE), int(ch * GRANDE)))
                sc.blit(img, img.get_rect(center=r.center))
        if acceso and not self.gira:
            # le caselle che non c'entrano si spengono, cosi' si vede
            # bene la combinazione che sta pagando
            velo = pygame.Surface(vetro.size, pygame.SRCALPHA)
            velo.fill((246, 241, 228, 170))
            sc.blit(velo, vetro)
            respiro = 0.5 + 0.5 * math.sin(self.t_vinta * 7.0)
            k = 1.0 + 0.12 * respiro
            nome_v = self.vinte[self.mostra][0] if self.vinte else None
            col = tuple(colore_simbolo(nome_v)) if nome_v else \
                COLORI_VINTE[self.mostra % len(COLORI_VINTE)]
            # i fili che legano i simboli della combinazione, da un rullo
            # al successivo, nel colore di questa vincita
            per_col = {}
            for c, i in acceso:
                if 0 <= i < RIGHE:
                    per_col.setdefault(c, []).append(i)
            fili = pygame.Surface(vetro.size, pygame.SRCALPHA)
            for c in sorted(per_col):
                if c + 1 not in per_col:
                    continue
                for i in per_col[c]:
                    for j in per_col[c + 1]:
                        a_x = c * cw + cw // 2
                        a_y = i * ch + ch // 2
                        b_x = (c + 1) * cw + cw // 2
                        b_y = j * ch + ch // 2
                        pygame.draw.line(fili,
                                         col + (int(130 + 125 * respiro),),
                                         (a_x, a_y), (b_x, b_y),
                                         max(2, B.s(4)))
            sc.blit(fili, vetro)
            for c, i in sorted(acceso):
                if not 0 <= i < RIGHE:
                    continue
                nome = self.griglia[c][i]
                r = pygame.Rect(vetro.x + c * cw, vetro.y + i * ch, cw, ch)
                img = figura(nome, (int(cw * GRANDE * k),
                                    int(ch * GRANDE * k))).copy()
                # l'alfa si moltiplica sui pixel: set_alpha su una
                # superficie trasparente farebbe un quadrato nero
                img.fill((255, 255, 255, int(165 + 90 * respiro)),
                         special_flags=pygame.BLEND_RGBA_MULT)
                sc.blit(img, img.get_rect(center=r.center))
        sc.set_clip(vecchio)
        for c in range(1, COLONNE):
            x = vetro.x + c * cw
            pygame.draw.line(sc, (206, 198, 180), (x, vetro.y),
                             (x, vetro.bottom), max(1, B.s(1)))

    def disegna_scelte(self, voci, sel):
        """Le scelte nella fascia a destra, nello stesso stile dei menu."""
        self.rett = []
        x0, x1 = self.cassa.right + B.s(16), B.WIN_W - B.s(8)
        f = B.FONTS["font"]
        B.tic_menu(tuple(voci), sel)
        passo = f.get_height() + B.s(14)
        y = self.cassa.centery - (len(voci) - 1) * passo // 2 + B.s(52)
        for i, testo in enumerate(voci):
            t = f.render(testo, True,
                         (255, 255, 255) if i == sel else (160, 166, 178))
            fondo = pygame.Rect(x0, y - (passo - B.s(8)) // 2, x1 - x0,
                                passo - B.s(8))
            if i == sel:
                q = pygame.Surface(fondo.size, pygame.SRCALPHA)
                q.fill((255, 255, 255, 16))
                self.sc.blit(q, fondo)
                pygame.draw.rect(self.sc, colore_neon(self.t_neon),
                                 (fondo.x, fondo.y, max(1, B.s(3)), fondo.h))
            self.sc.blit(t, t.get_rect(midleft=(x0 + B.s(14), y)))
            self.rett.append(fondo)
            y += passo

    def disegna_jackpot(self):
        """Il jackpot sopra la macchina, in una barra larga quanto lei,
        con la luce che gira e cambia colore."""
        sc = self.sc
        r = pygame.Rect(self.cassa.x, 0, self.cassa.w, B.s(44))
        r.bottom = self.cassa.top - B.s(12)
        pygame.draw.rect(sc, (13, 15, 21), r, border_radius=B.s(10))
        if self.lampo > 0:
            k = 0.5 + 0.5 * math.sin(self.t_vinta * 9.0)
            col = tuple(int(c * (0.45 + 0.55 * k)) for c in (255, 236, 150))
            pygame.draw.rect(sc, col, r, max(1, B.s(2)),
                             border_radius=B.s(10))
        else:
            cornice_neon(sc, r, self.t_neon + 0.5, B.s(10))
        nome = B.FONTS["small"].render(T("jackpot").upper(), True,
                                       (190, 196, 208))
        soldi = B.FONTS["font"].render(B.dollari(jackpot()), True,
                                       (255, 255, 255))
        insieme = nome.get_width() + soldi.get_width() + B.s(16)
        x = r.centerx - insieme // 2
        sc.blit(nome, nome.get_rect(midleft=(x, r.centery)))
        sc.blit(soldi, soldi.get_rect(
            midleft=(x + nome.get_width() + B.s(16), r.centery)))

    def disegna_sotto(self):
        """La barra sotto la macchina: qui va la combinazione che sta
        lampeggiando, nel suo colore."""
        sc = self.sc
        r = pygame.Rect(self.cassa.x, self.cassa.bottom + B.s(12),
                        self.cassa.w, B.s(48))
        pygame.draw.rect(sc, (13, 15, 21), r, border_radius=B.s(10))
        cornice_neon(sc, r, self.t_neon + 1.2, B.s(10))
        if not self.sotto:
            return
        nome = self.vinte[self.mostra][0] if (self.vinte and
                                              self.mostra >= 0) else None
        col = colore_simbolo(nome) if nome else (170, 176, 188)
        t = B.FONTS["font"].render(self.sotto, True, col)
        sc.blit(t, t.get_rect(center=r.center))

    def disegna_pannello(self, per_linea):
        """La colonna a destra: in cima il jackpot, che e' della casa e
        vale per tutte le macchine, poi la puntata."""
        sc = self.sc
        x0, x1 = self.cassa.right + B.s(16), B.WIN_W - B.s(14)
        f = B.FONTS["small"]
        passo = f.get_height() + B.s(10)
        y = self.cassa.top + B.s(16)
        righe = [(T("tot_bet"), B.dollari(round(per_linea * MODI_UNITA)),
                  (235, 238, 245))]
        if self.gratis:
            righe.append((T("free_spins"), str(self.gratis), (235, 238, 245)))
        if self.msg:
            righe.append((T("win_row"),
                          B.dollari(self.totale) if self.totale
                          else T("no_win"),
                          B.VERDE_SOLDI if self.totale else (180, 186, 198)))
        for et, val, col in righe:
            t = f.render(et, True, (150, 156, 168))
            sc.blit(t, (x0, y - t.get_height() // 2))
            v = f.render(str(val), True, col)
            sc.blit(v, v.get_rect(midright=(x1, y)))
            y += passo

    def frame(self):
        self.dt = min(0.05, self.clock.tick(60) / 1000.0)
        self.t_vinta += self.dt
        self.t_neon += self.dt
        if self.lampo > 0:
            self.lampo = max(0.0, self.lampo - self.dt)


# le macchine: chiave, come si chiama, che tema usa. Ognuna avra' i suoi
# simboli e i suoi pagamenti; per ora c'e' solo quella di prova
MACCHINE = (("prova", "m_prova", "classica"),)


def gruppi_pagamenti():
    """I simboli che pagano uguale vanno insieme su una riga sola: con
    ventidue simboli l'elenco uno per uno non ci starebbe."""
    fuori = []
    for nome in paganti():
        for g in fuori:
            if PAGA[g[0][0]] == PAGA[nome]:
                g[0].append(nome)
                break
        else:
            fuori.append(([nome], PAGA[nome]))
    return fuori


def pagina_pagamenti(sc, clock):
    """Il tabellone: i ventidue simboli in due colonne, con quanto pagano
    da due a cinque rulli in soldi veri, alla puntata scelta."""
    while True:
        clock.tick(60)
        for ev in B.eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_RETURN,
                              pygame.K_KP_ENTER, pygame.K_SPACE,
                              pygame.K_BACKSPACE):
                    return "su"
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (1, 3):
                return "su"
        sc.blit(fondo_slot(), (0, 0))
        small, mini = B.FONTS["small"], B.FONTS.get("mini", B.FONTS["small"])
        punta = B.CFG.get("slot_punta", PUNTATE[0])
        if punta not in PUNTATE:
            punta = PUNTATE[0]
        unita = punta / float(MODI_UNITA)
        t = small.render("%s  -  %s" % (T("pt_title"),
                                        T("pt_bet") % B.dollari(punta)),
                         True, B.ORO_SCELTA)
        sc.blit(t, t.get_rect(center=(B.WIN_W // 2, B.ALTO + B.s(12))))

        elenco = paganti()
        meta = (len(elenco) + 1) // 2
        lato = B.s(30)
        passo = lato + B.s(12)
        y0 = B.ALTO + B.s(46)
        bordo, spazio = B.s(28), B.s(70)      # aria fra le due colonne
        largo = (B.WIN_W - bordo * 2 - spazio) // 2
        for col in range(2):
            gruppo = elenco[col * meta:(col + 1) * meta]
            x = bordo + col * (largo + spazio)
            for i, nome in enumerate(gruppo):
                y = y0 + i * passo
                img = figura(nome, (lato, lato))
                sc.blit(img, img.get_rect(midleft=(x, y)))
                t = small.render(nome_simbolo(nome), True, (215, 218, 226))
                sc.blit(t, t.get_rect(midleft=(x + lato + B.s(8), y)))
                p2, p3, p4, p5 = PAGA[nome]
                # "2 = $8   3 = $18   4 = $38   5 = $95"
                x_val = x + largo
                cella = (largo - B.s(170)) // 4
                for k, v in enumerate((p2, p3, p4, p5)):
                    if not v:
                        continue
                    # "x2" in oro, il premio nel verde del portafoglio
                    per = small.render("x%d" % (k + 2), True, B.ORO_SCELTA)
                    soldi = small.render(B.dollari(round(v * unita)), True,
                                         B.VERDE_SOLDI)
                    destra = x_val - (3 - k) * cella
                    sc.blit(soldi, soldi.get_rect(midright=(destra, y)))
                    sc.blit(per, per.get_rect(
                        midright=(destra - soldi.get_width() - B.s(6), y)))

        # i quattro speciali, in fondo, due per riga
        y = y0 + meta * passo + B.s(6)
        speciali = ((JOLLY, T("pt_wild")), (REGALO, T("pt_gift")),
                    (DADI, T("pt_dice") % GIRI_GRATIS),
                    (SIMBOLO_JACKPOT, T("pt_jack") % B.dollari(jackpot())))
        for i, (nome, testo) in enumerate(speciali):
            x = B.s(30) + (i % 2) * largo
            yy = y + (i // 2) * (lato + B.s(8))
            img = figura(nome, (lato, lato))
            sc.blit(img, img.get_rect(midleft=(x, yy)))
            q = mini.render(testo, True, (200, 206, 216))
            sc.blit(q, q.get_rect(midleft=(x + lato + B.s(8), yy)))
        y += 2 * (lato + B.s(8)) + B.s(4)
        t = mini.render(T("pt_line") % MODI, True, B.ORO_SOTTO)
        sc.blit(t, t.get_rect(center=(B.WIN_W // 2, y)))
        if B.modo_comandi() == "pad" and B.ICONE_TASTI_OK():
            r = B.riga_pad(small, B.RIGA_MENU)
        else:
            r = mini.render(T("help_pt"), True, (150, 156, 168))
        sc.blit(r, r.get_rect(center=(B.WIN_W // 2, B.WIN_H - B.s(24))))
        B.presenta()


def gioca_slot(sc, clock, logo):
    """La macchina: si punta, si gira, si paga."""
    carica_suoni()
    m = Macchina(sc, clock)
    punta = B.CFG.get("slot_punta", PUNTATE[0])
    if punta not in PUNTATE:
        punta = PUNTATE[0]
    sel = 0
    aspetta = [0.0]         # quanto resta da far vedere della vincita
    gratis = [0]            # i giri gratis ancora da giocare

    def voci():
        return [T("spin"), "%s  %s" % (T("bet"), B.dollari(punta)),
                T("pays"), T("back")]

    def per_linea():
        """L'unita': i premi del tabellone sono per unita', e la puntata
        vale venti unita'."""
        return punta / float(MODI_UNITA)

    def cambia_punta(verso):
        nonlocal punta
        i = PUNTATE.index(punta)
        punta = PUNTATE[(i + verso) % len(PUNTATE)]
        B.CFG["slot_punta"] = punta
        B.salva_config()
        B.suona_fx("menu_tic", 0.6)

    def parti():
        if gratis[0] > 0:
            # un giro gratis: non si paga, e il jackpot non cresce
            gratis[0] -= 1
        else:
            if B.soldi() < punta:
                m.msg = T("broke")
                B.suona_fx("menu_chiudi", 0.7)
                return
            B.soldi(-punta)
            jackpot(max(1, int(punta * JACKPOT_FETTA)))
            B.salva_config()
        m.gratis = gratis[0]
        m.parti()
        suona("bottone", 0.9)
        suona("spin", 0.9)

    while True:
        m.frame()
        mouse = B.mouse_gioco()
        for ev in B.eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    for n in ("spin", "jackpot", "bonus", "level", "gift"):
                        ferma_suono(n)
                    return "su"
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    sel = (sel + 1) % 4
                    B.suona_fx("menu_tic", 0.6)
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % 4
                    B.suona_fx("menu_tic", 0.6)
                elif ev.key in (pygame.K_LEFT, pygame.K_a) and sel == 1:
                    cambia_punta(-1)
                elif ev.key in (pygame.K_RIGHT, pygame.K_d) and sel == 1:
                    cambia_punta(1)
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                pygame.K_SPACE):
                    if m.gira:
                        pass
                    elif sel == 0:
                        parti()
                    elif sel == 1:
                        cambia_punta(1)
                    elif sel == 2:
                        if pagina_pagamenti(sc, clock) == "quit":
                            return "quit"
                    else:
                        return "su"
                elif ev.key == B.tasto("gesso") and not m.gira:
                    if pagina_pagamenti(sc, clock) == "quit":
                        return "quit"
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(getattr(m, "rett", [])):
                    if r.collidepoint(mouse):
                        sel = i
                        if not m.gira:
                            if i == 0:
                                parti()
                            elif i == 1:
                                cambia_punta(1)
                            elif i == 2:
                                if pagina_pagamenti(sc, clock) == "quit":
                                    return "quit"
                            else:
                                return "su"
        if B.MOUSE_VIVO[0]:
            for i, r in enumerate(getattr(m, "rett", [])):
                if r.collidepoint(mouse):
                    sel = i
        if m.passo():
            # i rulli si sono fermati: prima i simboli che pagano a modi
            tot, vinte = vincite(m.griglia, per_linea())
            # il pacchetto regalo: tre o piu' dovunque siano
            pacchi = quanti_ce_ne(m.griglia, REGALO)
            if len(pacchi) >= 3:
                premio = premio_regalo(len(pacchi), punta)
                tot += premio
                vinte.append((REGALO, len(pacchi), 0, premio, pacchi))
            # i dadi: tre o piu' e si vincono i giri gratis
            dadi = quanti_ce_ne(m.griglia, DADI)
            vinti_gratis = GIRI_GRATIS if len(dadi) >= 3 else 0
            if vinti_gratis:
                gratis[0] += vinti_gratis
                vinte.append((DADI, len(dadi), 0, 0, dadi))
            jack = fa_jackpot(m.griglia)
            if jack:
                premio = jackpot()
                azzera_jackpot()
                tot += premio
                m.lampo = 8.0
            m.vinte, m.vinto = vinte, tot
            if tot:
                B.soldi(tot)
            B.salva_config()
            m.totale = tot
            m.mostra, aspetta[0], m.t_vinta = (0 if vinte else -1), 1.4, 0.0
            # il jolly che ha aiutato una vincita ha il suo suono
            con_jolly = any(m.griglia[c][r] == JOLLY
                            for _n, _l, _s, pa, celle in vinte if pa
                            for c, r in celle)
            if jack:
                suona("jackpot", 1.0)
            elif vinti_gratis:
                suona("dadi", 0.9)
            elif len(pacchi) >= 3:
                suona("regalo", 0.9)
            elif tot >= punta * 20:
                suona("vinci3", 0.9)
            elif tot >= punta * 5:
                suona("vinci2", 0.9)
            elif con_jolly:
                suona("jolly", 0.9)
            elif tot:
                suona("vinci1", 0.9)
            m.msg = (T("win") % B.dollari(tot)) if tot else (
                T("won_free") % vinti_gratis if vinti_gratis else T("no_win"))
        if m.vinte and m.mostra >= 0:
            aspetta[0] -= m.dt
            if aspetta[0] <= 0:
                m.mostra = (m.mostra + 1) % len(m.vinte)
                aspetta[0] = 1.2
                m.t_vinta = 0.0
            nome, lung, strade, paga, _celle = m.vinte[m.mostra]
            if nome == REGALO:
                m.sotto = "%d x %s  -  %s" % (lung, nome_simbolo(nome),
                                              B.dollari(paga))
            elif nome == DADI:
                m.sotto = "%d x %s  -  %s" % (lung, nome_simbolo(nome),
                                              T("won_free") % GIRI_GRATIS)
            else:
                testo = ("%d x %s" % (lung, nome_simbolo(nome))
                         if strade <= 1 else
                         T("ways_win") % (lung, nome_simbolo(nome), strade))
                m.sotto = "%s  -  %s" % (testo, B.dollari(paga))
        else:
            m.sotto = ""
        m.gratis = gratis[0]
        m.disegna(voci(), sel, per_linea())
        B.presenta()


def menu_macchina(sc, clock, logo, quale):
    """Il menu di una macchina: si gioca, si guardano i suoi pagamenti.
    Ogni macchina ha i suoi, per questo stanno qui dentro e non fuori."""
    chiave, nome, tema_suo = quale
    sel = 0
    rett = []
    while True:
        clock.tick(60)
        voci = [(T("play"), None), (T("pays"), None), (T("back"), None)]
        mouse = B.mouse_gioco()

        def fai(i):
            """Torna "quit" se si chiude il gioco, "su" se si torna
            indietro, None se si resta qui."""
            if i == 2:
                return "su"
            B.CFG["slot_tema"] = tema_suo
            fine = (gioca_slot(sc, clock, logo) if i == 0
                    else pagina_pagamenti(sc, clock))
            return "quit" if fine == "quit" else None

        for ev in B.eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    sel = (sel + 1) % len(voci)
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % len(voci)
                elif ev.key == pygame.K_ESCAPE:
                    return "su"
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                pygame.K_SPACE):
                    fine = fai(sel)
                    if fine:
                        return fine
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(rett):
                    if r.collidepoint(mouse):
                        sel = i
                        fine = fai(i)
                        if fine:
                            return fine
        B.sfondo_menu(sc, logo)
        t = (B.FONTS.get("elegante") or B.FONTS["grande"]).render(
            B.tit_el(T(nome)), True, (240, 240, 244))
        sc.blit(t, t.get_rect(center=(B.WIN_W // 2, B.s(326))))
        rett = B.disegna_voci(sc, voci, sel, B.FONTS["font"],
                              B.FONTS["small"], B.s(436), B.s(44))
        for i, r in enumerate(rett):
            if B.MOUSE_VIVO[0] and r.collidepoint(mouse):
                sel = i
        B.presenta()


def schermata_slot(sc, clock, logo):
    """L'elenco delle macchine."""
    sel = 0
    rett = []
    while True:
        clock.tick(60)
        voci = [(T(m[1]), None) for m in MACCHINE] + [(T("back"), None)]
        mouse = B.mouse_gioco()
        for ev in B.eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    sel = (sel + 1) % len(voci)
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % len(voci)
                elif ev.key == pygame.K_ESCAPE:
                    return "menu"
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                pygame.K_SPACE):
                    if sel >= len(MACCHINE):
                        return "menu"
                    if menu_macchina(sc, clock, logo,
                                     MACCHINE[sel]) == "quit":
                        return "quit"
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(rett):
                    if r.collidepoint(mouse):
                        sel = i
                        if i >= len(MACCHINE):
                            return "menu"
                        if menu_macchina(sc, clock, logo,
                                         MACCHINE[i]) == "quit":
                            return "quit"
        B.sfondo_menu(sc, logo)
        t = (B.FONTS.get("elegante") or B.FONTS["grande"]).render(
            B.tit_el(T("slot")), True, (240, 240, 244))
        sc.blit(t, t.get_rect(center=(B.WIN_W // 2, B.s(326))))
        rett = B.disegna_voci(sc, voci, sel, B.FONTS["font"],
                              B.FONTS["small"], B.s(436), B.s(44))
        for i, r in enumerate(rett):
            if B.MOUSE_VIVO[0] and r.collidepoint(mouse):
                sel = i
        B.presenta()
