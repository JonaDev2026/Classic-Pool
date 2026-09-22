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
    ("ciliegia",     (226,  80, 110), "C", 1,  15,  60,  250),
    ("limone",       (232, 224,  90), "L", 1,  15,  60,  250),
    ("arancia",      (240, 150,  60), "O", 1,  18,  70,  300),
    ("prugna",       (150, 110, 200), "P", 1,  18,  70,  300),
    ("mela",         (120, 200, 100), "M", 1,  18,  70,  300),
    ("fragola",      (232,  90, 100), "F", 1,  20,  80,  360),
    ("anguria",      (236, 120, 150), "A", 0,  20,  80,  360),
    ("uva",          (150, 110, 190), "U", 0,  20,  80,  360),
    ("cuori",        (230,  70,  90), "H", 0,  22,  90,  400),
    ("picche",       (150, 110, 230), "S", 0,  25, 100,  450),
    ("fiori",        ( 80, 120, 220), "K", 0,  25, 100,  450),
    ("quadri",       (226,  50,  90), "D", 0,  25, 100,  450),
    ("campana",      (240, 190,  70), "B", 0,  32, 130,  580),
    ("ferro",        (200, 205, 215), "V", 0,  32, 130,  580),
    ("quadrifoglio", ( 90, 200, 110), "Q", 0,  32, 130,  580),
    ("carte",        (240, 240, 245), "T", 0,  44, 175,  800),
    ("roulette",     ( 90, 170, 190), "R", 0,  44, 175,  800),
    ("fiches",       (220, 100, 130), "G", 0,  44, 175,  800),
    ("dollaro",      (240, 190,  70), "$", 0,  65, 260, 1150),
    ("gemma",        (140, 210, 240), "^", 0,  65, 260, 1150),
    ("bar",          ( 60, 180, 220), "=", 0,  65, 260, 1150),
    ("sette",        (226,  60,  60), "7", 0, 110, 450, 2000),
    ("jolly",        (250, 250, 250), "W", 0,   0,   0,    0),  # vale per tutti
    ("mistero",      (180, 186, 200), "?", 0,   0,   0,    0),  # si trasforma
    ("bonus",        ( 90, 210, 220), "*", 0,   0,   0,    0),  # paga sparso
    ("jackpot",      (255, 214,  92), "J", 0,   0,   0,    0),  # il jackpot
)
PAGA = dict((s[0], (s[3], s[4], s[5], s[6])) for s in SIMBOLI)
COLORE = dict((s[0], s[1]) for s in SIMBOLI)
SEGNO = dict((s[0], s[2]) for s in SIMBOLI)
JOLLY = "jolly"
BONUS = "bonus"
MISTERO = "mistero"
# il bonus paga sul totale puntato, non sulla linea
PAGA_BONUS = {3: 2, 4: 10, 5: 50}

COLONNE, RIGHE = 5, 4

# la griglia paga a modi, non a linee: 4 righe per 5 rulli fanno 1024
# strade possibili, e la puntata si divide in venti unita' come prima
MODI = RIGHE ** COLONNE
MODI_UNITA = 20

# quante copie di ogni simbolo ci sono sulla striscia di ogni rullo: i
# simboli che pagano tanto sono rari, il jolly e il mistero non stanno
# sul primo e sull'ultimo rullo
QUANTI = {
    "ciliegia":     (9, 9, 9, 9, 9),
    "limone":       (9, 9, 9, 9, 9),
    "arancia":      (8, 8, 8, 8, 8),
    "prugna":       (8, 8, 8, 8, 8),
    "mela":         (8, 8, 8, 8, 8),
    "fragola":      (7, 7, 7, 7, 7),
    "anguria":      (7, 7, 7, 7, 7),
    "uva":          (7, 7, 7, 7, 7),
    "cuori":        (7, 7, 7, 7, 7),
    "picche":       (6, 6, 6, 6, 6),
    "fiori":        (6, 6, 6, 6, 6),
    "quadri":       (6, 6, 6, 6, 6),
    "campana":      (5, 5, 5, 5, 5),
    "ferro":        (5, 5, 5, 5, 5),
    "quadrifoglio": (5, 5, 5, 5, 5),
    "carte":        (4, 4, 4, 4, 4),
    "roulette":     (4, 4, 4, 4, 4),
    "fiches":       (4, 4, 4, 4, 4),
    "dollaro":      (3, 3, 3, 3, 3),
    "gemma":        (3, 3, 3, 3, 3),
    "bar":          (3, 3, 3, 3, 3),
    "sette":        (2, 2, 2, 2, 2),
    "jolly":        (0, 3, 3, 3, 0),
    "mistero":      (0, 3, 3, 3, 0),
    "bonus":        (2, 2, 2, 2, 2),
    "jackpot":      (5, 5, 5, 5, 5),
}

PUNTATE = (20, 40, 100, 200, 400)   # per giro, divisi sulle venti linee

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
    dove = [i for i, x in enumerate(s) if x == BONUS]
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


def apri_mistero(griglia):
    """I simboli mistero si girano tutti insieme e diventano tutti lo
    stesso simbolo, scelto a caso fra quelli che pagano. Torna il
    simbolo uscito e le caselle che si sono girate, o (None, [])."""
    celle = [(c, r) for c in range(COLONNE) for r in range(RIGHE)
             if griglia[c][r] == MISTERO]
    if not celle:
        return None, []
    pesi = [sum(QUANTI[n]) for n in paganti()]
    quale = random.choices(paganti(), pesi)[0]
    for c, r in celle:
        griglia[c][r] = quale
    return quale, celle


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
        paga = quanto * strade * unita
        celle = [x for c in range(lung) for x in dove[c]]
        fuori.append((nome, lung, strade, paga, celle))
    # il bonus paga dovunque sia, sulla puntata intera
    celle = [(c, r) for c in range(COLONNE) for r in range(RIGHE)
             if griglia[c][r] == BONUS]
    if len(celle) >= 3:
        quanti = min(5, len(celle))
        paga = PAGA_BONUS[quanti] * unita * MODI_UNITA
        fuori.append((BONUS, quanti, 1, paga, celle))
    return sum(v[3] for v in fuori), fuori


# ------------------------------------------------------------- i testi
TXT = {
    "en": {"slot": "Slots", "spin": "Spin", "play": "Play",
           "m_prova": "Test machine", "bet": "Bet", "pays": "Paytable",
           "back": "Back", "win": "You win %s", "no_win": "No win",
           "broke": "Not enough money", "tot_bet": "Total bet",
           "per_line": "Per unit", "lines": "Ways",
           "mystery": "Mystery:  %s",
           "ways_win": "%d x %s  on %d ways", "credit": "Credit",
           "jackpot": "Jackpot", "won_jack": "JACKPOT!  %s",
           "pt_jack": "One on each of the five reels wins the jackpot: %s",
           "pt_title": "Paytable", "pt_wild": "Wild: stands for any symbol",
           "pt_mystery": "Mystery: they all flip to the same random symbol",
           "pt_bonus": "Bonus: pays anywhere, on the total bet",
           "pt_line": "Same symbol on touching reels from the left: %d ways, the commonest symbols already pay on two reels",
           "help": "click / ENTER  spin     < >  bet     %s  paytable     ESC  back",
           "sp_spin": "spin", "sp_bet": "bet", "sp_pays": "paytable", "help_pt": "ENTER / ESC  back"},
    "it": {"slot": "Slot", "spin": "Gira", "play": "Gioca",
           "m_prova": "Slot di prova", "bet": "Puntata",
           "pays": "Pagamenti", "back": "Indietro", "win": "Vinci %s",
           "no_win": "Niente", "broke": "Non hai abbastanza soldi",
           "tot_bet": "Puntata", "per_line": "Per unita", "lines": "Modi",
           "mystery": "Mistero:  %s",
           "ways_win": "%d x %s  su %d modi",
           "credit": "Credito", "jackpot": "Jackpot",
           "won_jack": "JACKPOT!  %s",
           "pt_jack": "Uno su ognuno dei cinque rulli vince il jackpot: %s",
           "pt_title": "Pagamenti",
           "pt_wild": "Jolly: vale per tutti i simboli",
           "pt_mystery": "Mistero: si girano tutti insieme nello stesso simbolo",
           "pt_bonus": "Bonus: paga dovunque sia, sulla puntata intera",
           "pt_line": "Stesso simbolo su rulli attaccati da sinistra: %d modi, i simboli comuni pagano gia con due rulli",
           "help": "clic / INVIO  gira     < >  puntata     %s  pagamenti     ESC  indietro",
           "sp_spin": "gira", "sp_bet": "puntata", "sp_pays": "pagamenti", "help_pt": "INVIO / ESC  indietro"},
    "fr": {"slot": "Machine", "spin": "Tourner", "play": "Jouer",
           "m_prova": "Machine d'essai", "bet": "Mise",
           "pays": "Gains", "back": "Retour", "win": "Vous gagnez %s",
           "no_win": "Rien", "broke": "Pas assez d'argent",
           "tot_bet": "Mise", "per_line": "Par unite", "lines": "Facons",
           "mystery": "Mystere :  %s",
           "ways_win": "%d x %s  sur %d facons",
           "credit": "Credit", "jackpot": "Jackpot",
           "won_jack": "JACKPOT !  %s",
           "pt_jack": "Un sur chacun des cinq rouleaux gagne le jackpot : %s",
           "pt_title": "Table des gains",
           "pt_wild": "Joker : remplace tous les symboles",
           "pt_mystery": "Mystere : ils se retournent tous sur le meme symbole",
           "pt_bonus": "Bonus : paie partout, sur la mise totale",
           "pt_line": "Meme symbole sur des rouleaux voisins depuis la gauche : %d facons",
           "help": "clic / ENTREE  tourner     < >  mise     %s  gains     ECHAP  retour",
           "sp_spin": "tourner", "sp_bet": "mise", "sp_pays": "gains", "help_pt": "ENTREE / ECHAP  retour"},
    "es": {"slot": "Tragaperras", "spin": "Girar", "play": "Jugar",
           "m_prova": "Tragaperras de prueba", "bet": "Apuesta",
           "pays": "Premios", "back": "Atras", "win": "Ganas %s",
           "no_win": "Nada", "broke": "No tienes bastante dinero",
           "tot_bet": "Apuesta", "per_line": "Por unidad", "lines": "Modos",
           "mystery": "Misterio:  %s",
           "ways_win": "%d x %s  en %d modos",
           "credit": "Credito", "jackpot": "Jackpot",
           "won_jack": "JACKPOT!  %s",
           "pt_jack": "Uno en cada uno de los cinco rodillos gana el jackpot: %s",
           "pt_title": "Tabla de premios",
           "pt_wild": "Comodin: vale por todos los simbolos",
           "pt_mystery": "Misterio: se giran todos en el mismo simbolo",
           "pt_bonus": "Bonus: paga donde sea, sobre la apuesta total",
           "pt_line": "Mismo simbolo en rodillos seguidos desde la izquierda: %d modos",
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
           "mistero": "Mystery", "bonus": "Bonus", "jackpot": "Jackpot"},
    "it": {"ciliegia": "Ciliegia", "limone": "Limone", "arancia": "Arancia",
           "prugna": "Prugna", "mela": "Mela", "fragola": "Fragola",
           "anguria": "Anguria", "uva": "Uva", "cuori": "Cuori",
           "picche": "Picche", "fiori": "Fiori", "quadri": "Quadri",
           "campana": "Campana", "ferro": "Ferro di cavallo",
           "quadrifoglio": "Quadrifoglio", "carte": "Carte",
           "roulette": "Roulette", "fiches": "Fiches", "dollaro": "Moneta",
           "gemma": "Gemma", "bar": "Bar", "sette": "Sette",
           "jolly": "Jolly", "mistero": "Mistero", "bonus": "Bonus",
           "jackpot": "Jackpot"},
    "fr": {"ciliegia": "Cerise", "limone": "Citron", "arancia": "Orange",
           "prugna": "Prune", "mela": "Pomme", "fragola": "Fraise",
           "anguria": "Pasteque", "uva": "Raisin", "cuori": "Coeur",
           "picche": "Pique", "fiori": "Trefle", "quadri": "Carreau",
           "campana": "Cloche", "ferro": "Fer a cheval",
           "quadrifoglio": "Trefle porte-bonheur", "carte": "Cartes",
           "roulette": "Roulette", "fiches": "Jetons", "dollaro": "Piece",
           "gemma": "Gemme", "bar": "Bar", "sette": "Sept",
           "jolly": "Joker", "mistero": "Mystere", "bonus": "Bonus",
           "jackpot": "Jackpot"},
    "es": {"ciliegia": "Cereza", "limone": "Limon", "arancia": "Naranja",
           "prugna": "Ciruela", "mela": "Manzana", "fragola": "Fresa",
           "anguria": "Sandia", "uva": "Uvas", "cuori": "Corazon",
           "picche": "Pica", "fiori": "Trebol", "quadri": "Diamante",
           "campana": "Campana", "ferro": "Herradura",
           "quadrifoglio": "Trebol de cuatro", "carte": "Cartas",
           "roulette": "Ruleta", "fiches": "Fichas", "dollaro": "Moneda",
           "gemma": "Gema", "bar": "Bar", "sette": "Siete",
           "jolly": "Comodin", "mistero": "Misterio", "bonus": "Bonus",
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
    """I suoni della slot, da audio/slot/fx."""
    if SUONI or not B.MUSICA_OK:
        return
    cartella = os.path.join(B.SUONI_DIR, "slot", "fx")
    if not os.path.isdir(cartella):
        return
    for f in sorted(os.listdir(cartella)):
        if not f.lower().endswith((".ogg", ".wav", ".mp3")):
            continue
        nome = os.path.splitext(f)[0].lower()
        try:
            s = pygame.mixer.Sound(os.path.join(cartella, f))
            SUONI[nome] = s
            DURATE[nome] = s.get_length()
        except pygame.error:
            pass


def suona(nome, quanto=0.9):
    s = SUONI.get(nome)
    v = B.CFG.get("effetti", 100) / 100.0
    if not s or v <= 0:
        return None
    s.stop()                # se stava ancora suonando, ricomincia
    s.set_volume(min(1.0, v * quanto))
    s.play()
    return s


def ferma_suono(nome):
    s = SUONI.get(nome)
    if s:
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
    """Il fondo dei rulli: quasi nero, con una luce morbida al centro che
    stacca i simboli senza rubare la scena."""
    if VETRO[0] is None or VETRO[0].get_size() != misura:
        w, h = misura
        q = pygame.Surface(misura)
        q.fill((10, 11, 15))
        luce = pygame.Surface(misura, pygame.SRCALPHA)
        for i in range(24):
            k = i / 23.0
            r = pygame.Rect(0, int(h * 0.5 - h * 0.5 * (1 - k * 0.8)),
                            w, max(1, int(h * (1 - k * 0.8))))
            pygame.draw.rect(luce, (40, 48, 68, 5), r)
        q.blit(luce, (0, 0))
        VETRO[0] = q
    return VETRO[0]


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
        self.lampo = 0.0        # quanto dura il lampo del jackpot vinto
        self.t_neon = 0.0       # il colore che gira nella cornice
        self.msg = ""
        self.vinto = 0
        self.gira = False
        # la cassa: a sinistra il vetro coi rulli, a destra la fascia
        # delle scelte, come al tavolo da carte
        largo = B.WIN_W - B.s(300)
        self.cassa = pygame.Rect(B.s(40), B.ALTO + B.s(56),
                                 largo - B.s(60), B.WIN_H - B.ALTO - B.s(170))
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
                    # il rullo si ferma in silenzio: c'e' solo lo spin
                    self.pos[c] = self.a[c]
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
        sc.blit(fondo_slot(), (0, 0))
        self.nome_gioco()
        # la cassa: un pannello scuro pieno, con la luce che gira intorno
        pygame.draw.rect(sc, (13, 15, 21), self.cassa,
                         border_radius=B.s(14))
        cornice_neon(sc, self.cassa, self.t_neon)
        self.disegna_rulli()
        self.disegna_scelte(voci, sel)
        self.disegna_pannello(per_linea)
        self.disegna_messaggio()
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
            velo.fill((6, 7, 10, 165))
            sc.blit(velo, vetro)
            respiro = 0.5 + 0.5 * math.sin(self.t_vinta * 7.0)
            k = 1.0 + 0.12 * respiro
            for c, i in sorted(acceso):
                if not 0 <= i < RIGHE:
                    continue
                nome = self.griglia[c][i]
                r = pygame.Rect(vetro.x + c * cw, vetro.y + i * ch, cw, ch)
                # niente cornici ne' aloni: il simbolo lampeggia e basta
                img = figura(nome, (int(cw * GRANDE * k),
                                    int(ch * GRANDE * k))).copy()
                # l'alfa si moltiplica sui pixel: set_alpha su una
                # superficie trasparente farebbe un quadrato nero
                img.fill((255, 255, 255, int(150 + 105 * respiro)),
                         special_flags=pygame.BLEND_RGBA_MULT)
                sc.blit(img, img.get_rect(center=r.center))
        sc.set_clip(vecchio)
        for c in range(1, COLONNE):
            x = vetro.x + c * cw
            pygame.draw.line(sc, (26, 29, 38), (x, vetro.y),
                             (x, vetro.bottom), max(1, B.s(1)))

    def disegna_scelte(self, voci, sel):
        """Le scelte nella fascia a destra, nello stesso stile dei menu."""
        self.rett = []
        x0, x1 = self.cassa.right + B.s(16), B.WIN_W - B.s(8)
        f = B.FONTS["font"]
        B.tic_menu(tuple(voci), sel)
        passo = f.get_height() + B.s(14)
        y = self.cassa.centery - (len(voci) - 1) * passo // 2 + B.s(30)
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

    def disegna_pannello(self, per_linea):
        """La colonna a destra: in cima il jackpot, che e' della casa e
        vale per tutte le macchine, poi la puntata."""
        sc = self.sc
        x0, x1 = self.cassa.right + B.s(16), B.WIN_W - B.s(14)
        y = self.cassa.top + B.s(6)
        # il riquadro del jackpot, col suo filo di luce
        r = pygame.Rect(x0 - B.s(6), y, x1 - x0 + B.s(12), B.s(62))
        pygame.draw.rect(sc, (13, 15, 21), r, border_radius=B.s(8))
        col = colore_neon(self.t_neon + 0.5)
        if self.lampo > 0:
            k = 0.5 + 0.5 * math.sin(self.t_vinta * 9.0)
            col = tuple(int(c * (0.45 + 0.55 * k)) for c in (255, 236, 150))
        pygame.draw.rect(sc, col, r, max(1, B.s(2)), border_radius=B.s(8))
        f = B.FONTS["small"]
        t = f.render(T("jackpot").upper(), True, (170, 176, 188))
        sc.blit(t, t.get_rect(midtop=(r.centerx, r.top + B.s(8))))
        f = B.FONTS["font"]
        t = f.render(B.dollari(jackpot()), True, (255, 255, 255))
        sc.blit(t, t.get_rect(midbottom=(r.centerx, r.bottom - B.s(8))))
        # i dati della puntata, in carattere normale
        f = B.FONTS["small"]
        passo = f.get_height() + B.s(10)
        y = r.bottom + B.s(24)
        righe = [(T("tot_bet"), B.dollari(per_linea * MODI_UNITA)),
                 (T("per_line"), B.dollari(per_linea))]
        for et, val in righe:
            t = f.render(et, True, (150, 156, 168))
            sc.blit(t, (x0, y - t.get_height() // 2))
            v = f.render(str(val), True, (235, 238, 245))
            sc.blit(v, v.get_rect(midright=(x1, y)))
            y += passo

    def disegna_messaggio(self):
        if not self.msg:
            return
        t = B.FONTS["font"].render(self.msg, True, (235, 238, 245))
        self.sc.blit(t, t.get_rect(center=(self.cassa.centerx,
                                           self.cassa.bottom + B.s(34))))

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
    """Il tabellone: i simboli in gruppi, con quanto pagano da due a
    cinque rulli per ogni unita' di puntata."""
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
        f_t = B.FONTS.get("elegante") or B.FONTS["grande"]
        t = f_t.render(B.tit_el(T("pt_title")), True, (240, 240, 244))
        sc.blit(t, t.get_rect(center=(B.WIN_W // 2, B.ALTO + B.s(40))))
        small, font = B.FONTS["small"], B.FONTS["font"]
        gruppi = gruppi_pagamenti()
        lato = B.s(38)
        y = B.ALTO + B.s(84)
        passo = lato + B.s(6)
        x0 = B.s(90)
        for nomi, (p2, p3, p4, p5) in gruppi:
            x = x0
            for nome in nomi:
                img = figura(nome, (lato, lato))
                sc.blit(img, img.get_rect(midleft=(x, y)))
                x += lato + B.s(5)
            pezzi = []
            if p2:
                pezzi.append("2 - %d" % p2)
            pezzi += ["3 - %d" % p3, "4 - %d" % p4, "5 - %d" % p5]
            t = font.render("      ".join(pezzi), True, (230, 232, 238))
            sc.blit(t, t.get_rect(midright=(B.WIN_W - B.s(90), y)))
            y += passo
        # i simboli speciali, in fondo
        y += B.s(10)
        for nome, testo in ((JOLLY, T("pt_wild")), (MISTERO, T("pt_mystery")),
                            (BONUS, T("pt_bonus")),
                            (SIMBOLO_JACKPOT,
                             T("pt_jack") % B.dollari(jackpot()))):
            img = figura(nome, (lato, lato))
            sc.blit(img, img.get_rect(midleft=(x0, y)))
            t = small.render(testo, True, (230, 232, 238))
            sc.blit(t, t.get_rect(midleft=(x0 + lato + B.s(12), y)))
            if nome == BONUS:
                t = small.render("3 - %dx    4 - %dx    5 - %dx"
                                 % (PAGA_BONUS[3], PAGA_BONUS[4],
                                    PAGA_BONUS[5]), True, B.ORO_SOTTO)
                sc.blit(t, t.get_rect(midright=(B.WIN_W - B.s(90), y)))
            y += lato + B.s(4)
        t = small.render(T("pt_line") % MODI, True, B.ORO_SOTTO)
        sc.blit(t, t.get_rect(center=(B.WIN_W // 2, B.WIN_H - B.s(66))))
        if B.modo_comandi() == "pad" and B.ICONE_TASTI_OK():
            r = B.riga_pad(small, B.RIGA_MENU)
        else:
            r = small.render(T("help_pt"), True, (150, 156, 168))
        sc.blit(r, r.get_rect(center=(B.WIN_W // 2, B.WIN_H - B.s(34))))
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
    conta = [0.0]           # la pausa per far vedere il mistero aperto
    da_contare = [False]

    def voci():
        return [T("spin"), "%s  %s" % (T("bet"), B.dollari(punta)),
                T("pays"), T("back")]

    def per_linea():
        return max(1, punta // MODI_UNITA)

    def cambia_punta(verso):
        nonlocal punta
        i = PUNTATE.index(punta)
        punta = PUNTATE[(i + verso) % len(PUNTATE)]
        B.CFG["slot_punta"] = punta
        B.salva_config()
        B.suona_fx("menu_tic", 0.6)

    def parti():
        if B.soldi() < punta:
            m.msg = T("broke")
            B.suona_fx("menu_chiudi", 0.7)
            return
        B.soldi(-punta)
        jackpot(max(1, int(punta * JACKPOT_FETTA)))
        B.salva_config()
        m.parti()
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
            # i rulli si sono fermati: prima si girano i misteri
            quale, celle = apri_mistero(m.griglia)
            if quale:
                m.msg = T("mystery") % nome_simbolo(quale)
                m.vinte, m.mostra = [(quale, 0, 0, 0, celle)], 0
                m.t_vinta = 0.0
                suona("transform", 0.9)
                conta[0] = 1.1
            else:
                conta[0] = 0.0
            da_contare[0] = True
        if da_contare[0]:
            conta[0] -= m.dt
            if conta[0] > 0:
                m.disegna(voci(), sel, per_linea())
                B.presenta()
                continue
            da_contare[0] = False
            tot, vinte = vincite(m.griglia, per_linea())
            m.vinte, m.vinto = vinte, tot
            jack = fa_jackpot(m.griglia)
            if jack:
                premio = jackpot()
                azzera_jackpot()
                tot += premio
                m.vinto = tot
                m.lampo = 8.0
                B.soldi(premio)
                B.salva_config()
            if tot:
                B.soldi(tot)
                B.salva_config()
                m.msg = T("win") % B.dollari(tot)
                m.mostra, aspetta[0], m.t_vinta = 0, 1.2, 0.0
                if jack:
                    suona("jackpot", 1.0)
                elif any(v[1] == BONUS for v in vinte):
                    suona("bonus", 0.9)
                elif tot >= punta * 10:
                    suona("level", 0.9)
                else:
                    suona("gift", 0.9)
            else:
                m.msg = T("no_win")
                m.mostra = -1
        if m.vinte and m.mostra >= 0:
            aspetta[0] -= m.dt
            if aspetta[0] <= 0:
                m.mostra = (m.mostra + 1) % len(m.vinte)
                aspetta[0] = 1.0
                m.t_vinta = 0.0
            nome, lung, strade, paga, _celle = m.vinte[m.mostra]
            if nome == BONUS:
                m.msg = "%d x %s  -  %s" % (lung, nome_simbolo(nome),
                                            B.dollari(paga))
            else:
                m.msg = "%s  -  %s" % (
                    T("ways_win") % (lung, nome_simbolo(nome), strade),
                    B.dollari(paga))
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
