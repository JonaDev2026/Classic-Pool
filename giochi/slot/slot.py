"""Golden Break - la slot machine.

Sei colonne per cinque righe, i modi al posto delle linee, i rulli che
si fermano uno dopo l'altro. Qui c'e' il motore: le strisce dei rulli, il
conto delle vincite e il tabellone dei pagamenti. La grafica dei simboli
sta fuori, in immagini/slot/<tema>: finche' non c'e' si disegnano dei
segnaposto, cosi' la macchina si puo' provare lo stesso.

Si appoggia a biliardo.py per finestra, caratteri, sfondo, suoni e
portafoglio, come fanno le carte.
"""
import array
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

# ------------------------------------------------------------- il log
# Un giro per riga, nella cartella del gioco. Si svuota da solo alla
# prima scrittura di ogni avvio, cosi' i file non si accumulano e quello
# che leggi e' sempre la sessione di adesso.
LOG = os.path.join(RADICE, "slot_log.txt")
_LOG_PRONTO = [False, 0]


def log(riga):
    try:
        import datetime
        if not _LOG_PRONTO[0]:
            with open(LOG, "w") as f:
                f.write("Golden Break - slot - %s\n"
                        % datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))
            _LOG_PRONTO[0] = True
        _LOG_PRONTO[1] += 1
        with open(LOG, "a") as f:
            f.write("%4d  %s\n" % (_LOG_PRONTO[1], riga))
    except IOError:
        pass


# ----------------------------------------------------------- i simboli
# nome, colore di riserva, segno di riserva, e quanto paga con 2, 3, 4,
# 5 e 6 rulli di fila (per ogni unita' di puntata). Lo zero vuol dire che
# con quel numero di rulli non paga: su sei rulli due soli uguali non
# valgono niente, si comincia a vincere da tre in su.
SIMBOLI = (
    ("ciliegia",     (226,  80, 110), "C",      0,     40,    100,    250,    650),
    ("limone",       (232, 224,  90), "L",      0,     40,    100,    260,    680),
    ("arancia",      (240, 150,  60), "O",      0,     40,    110,    270,    700),
    ("prugna",       (150, 110, 200), "P",      0,     50,    110,    280,    720),
    ("mela",         (120, 200, 100), "M",      0,     50,    120,    290,    750),
    ("fragola",      (232,  90, 100), "F",      0,     50,    120,    300,    780),
    ("anguria",      (236, 120, 150), "A",      0,     80,    200,    500,   1300),
    ("uva",          (150, 110, 190), "U",      0,     80,    210,    520,   1350),
    ("cuori",        (230,  70,  90), "H",      0,     90,    220,    550,   1400),
    ("picche",       (150, 110, 230), "S",      0,     90,    220,    560,   1420),
    ("fiori",        ( 80, 120, 220), "K",      0,     90,    230,    580,   1450),
    ("quadri",       (226,  50,  90), "D",      0,    100,    240,    600,   1500),
    ("campana",      (240, 190,  70), "B",      0,    160,    450,   1150,   3000),
    ("ferro",        (200, 205, 215), "V",      0,    170,    460,   1180,   3050),
    ("quadrifoglio", ( 90, 200, 110), "Q",      0,    180,    480,   1200,   3100),
    ("carte",        (240, 240, 245), "T",      0,    450,   1150,   3000,   7900),
    ("roulette",     ( 90, 170, 190), "R",      0,    460,   1180,   3050,   8000),
    ("fiches",       (220, 100, 130), "G",      0,    470,   1200,   3100,   8200),
    ("dollaro",      (240, 190,  70), "$",      0,   1400,   3600,   9200,  24000),
    ("gemma",        (140, 210, 240), "^",      0,   1450,   3700,   9500,  24800),
    ("bar",          ( 60, 180, 220), "=",      0,   1480,   3800,   9700,  25300),
    ("sette",        (226,  60,  60), "7",      0,   1500,   3850,   9900,  25800),
    ("palla8",       ( 40,  44,  56), "8",      0,   1520,   3950,  10100,  26500),
    ("jolly",        (250, 250, 250), "W",      0,      0,      0,      0,      0),  # vale per tutti
    ("dadi",         (180, 186, 200), "?",      0,      0,      0,      0,      0),  # giri gratis
    ("regalo",       ( 90, 210, 220), "*",      0,      0,      0,      0,      0),  # premio a caso
    ("jackpot",      (255, 214,  92), "J",      0,      0,      0,      0,      0),  # il jackpot
)
PAGA = dict((s[0], (s[3], s[4], s[5], s[6], s[7]))
            for s in SIMBOLI)
COLORE = dict((s[0], s[1]) for s in SIMBOLI)
SEGNO = dict((s[0], s[2]) for s in SIMBOLI)
JOLLY = "jolly"
REGALO = "regalo"           # tre o piu': un premio a caso
DADI = "dadi"               # tre o piu': giri gratis
GIRI_GRATIS = 3             # quanti ne regalano i dadi
PREMIO_REGALO = {3: (2, 8), 4: (8, 25), 5: (30, 100)}   # in puntate


COLONNE, RIGHE = 6, 5

# la griglia paga a modi, non a linee: 5 righe per 6 rulli fanno 15625
# strade possibili, e la puntata si divide in unita' come prima
MODI = RIGHE ** COLONNE
MODI_UNITA = 20

# quante copie di ogni simbolo ci sono sulla striscia di ogni rullo: piu'
# un simbolo paga e piu' e' raro, in ordine dalla frutta alla palla otto.
# Il jolly non sta sul primo ne' sull'ultimo rullo
QUANTI = {
    "ciliegia":     (6, 6, 6, 6, 6, 6),
    "limone":       (6, 6, 6, 6, 6, 6),
    "arancia":      (6, 6, 6, 6, 6, 6),
    "prugna":       (6, 6, 6, 6, 6, 6),
    "mela":         (6, 6, 6, 6, 6, 6),
    "fragola":      (6, 6, 6, 6, 6, 6),
    "anguria":      (5, 5, 5, 5, 5, 5),
    "uva":          (5, 5, 5, 5, 5, 5),
    "cuori":        (5, 5, 5, 5, 5, 5),
    "picche":       (5, 5, 5, 5, 5, 5),
    "fiori":        (5, 5, 5, 5, 5, 5),
    "quadri":       (5, 5, 5, 5, 5, 5),
    "campana":      (4, 4, 4, 4, 4, 4),
    "ferro":        (4, 4, 4, 4, 4, 4),
    "quadrifoglio": (4, 4, 4, 4, 4, 4),
    "carte":        (3, 3, 3, 3, 3, 3),
    "roulette":     (3, 3, 3, 3, 3, 3),
    "fiches":       (3, 3, 3, 3, 3, 3),
    "dollaro":      (2, 2, 2, 2, 2, 2),
    "gemma":        (2, 2, 2, 2, 2, 2),
    "bar":          (2, 2, 2, 2, 2, 2),
    "sette":        (2, 2, 2, 2, 2, 2),
    "palla8":       (2, 2, 2, 2, 2, 2),
    "jolly":        (0, 3, 3, 3, 3, 0),
    "dadi":         (2, 2, 2, 2, 2, 2),
    "regalo":       (2, 2, 2, 2, 2, 2),
    "jackpot":      (5, 5, 5, 5, 5, 5),
}

# quanto si gioca a giro: di cinque in cinque, da cinque a cento. Con
# i salti grossi di prima (20, 50, 100, 250...) si arrivava subito a
# puntare mille dollari e la partita finiva li'
PUNTATE = tuple(range(5, 101, 5))

# il jackpot: parte da qui, cresce di una fetta di ogni puntata e si
# vince col suo simbolo su tutti e sei i rulli. Sta nel file del
# giocatore e cresce di partita in partita: si svuota solo quando
# qualcuno lo vince, nemmeno ricominciando la carriera.
# La fetta e' quanto della puntata ci finisce dentro: 1.0 vuol dire
# tutta, quindi un giro da venti dollari lo alza di venti.
JACKPOT_BASE = 1200
JACKPOT_FETTA = 1.0
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
    """Il jackpot vuole il suo simbolo su tutti e sei i rulli, e
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
    """Le strisce dei rulli, una per colonna."""
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
    """I modi: conta solo che lo stesso simbolo esca
    su rulli attaccati partendo da sinistra, dovunque stia nella colonna.
    Se su un rullo ce n'e' piu' d'uno le strade si moltiplicano. I
    Su sei rulli si paga da tre uguali in su.

    Torna il totale e l'elenco: (nome, quanti rulli, strade, quanto paga,
    le caselle da accendere)."""
    fuori = []
    for nome in paganti():
        conta, dove, veri = [], [], []
        for c in range(COLONNE):
            celle = [(c, r) for r in range(RIGHE)
                     if griglia[c][r] in (nome, JOLLY)]
            conta.append(len(celle))
            dove.append(celle)
            veri.append(any(griglia[c][r] == nome for r in range(RIGHE)))
        strade, lung = 1, 0
        for c in range(COLONNE):
            if not conta[c]:
                break
            strade *= conta[c]
            lung += 1
        if lung < 2:
            continue
        # il jolly aiuta, ma non fa tutto da solo: ci vogliono almeno due
        # rulli col simbolo vero
        if sum(1 for c in range(lung) if veri[c]) < 2:
            continue
        quanto = PAGA[nome][min(lung, COLONNE) - 2]
        if not quanto:
            continue
        paga = int(round(quanto * strade * unita))
        celle = [x for c in range(lung) for x in dove[c]]
        fuori.append((nome, lung, strade, paga, celle))
    return sum(v[3] for v in fuori), fuori


# ------------------------------------------------------------- i testi
TXT = {
    "en": {"slot": "Slots",
           "test": "Test", "pr_titolo": "All symbols, with their animations",
           "pr_aiuto": "any key  back", "spin": "Spin", "play": "Play",
           "m_prova": "Classic Slot", "m_nuova": "Space Slot",
           "bet": "Bet", "pays": "Paytable",
           "back": "Back", "win": "You win %s", "no_win": "No win",
           "broke": "Not enough money", "tot_bet": "Total bet",
           "per_line": "Per unit", "lines": "Ways",
           "free_spins": "Free spins", "win_row": "Win", "won_free": "%d free spins",
           "ways_win": "%d x %s  on %d ways", "credit": "Credit",
           "jackpot": "Jackpot", "won_jack": "JACKPOT!  %s",
           "st_spins": "Spins", "st_bet": "Bet", "st_won": "Won",
           "last_wins": "Last wins",
           "pt_jack": "One on each of the six reels wins the jackpot: %s",
           "pt_title": "Paytable", "pt_bet": "prizes at a bet of %s", "pt_wild": "Wild: stands for any symbol, but a win needs at least two real ones",
           "pt_gift": "Gift: three or more anywhere, with a random prize inside",
           "pt_dice": "Dice: three or more anywhere win %d free spins",
           "pt_bonus": "Bonus: pays anywhere, on the total bet",
           "pt_line": "Same symbol on touching reels from the left, in any position: %d ways. The numbers are per way, so a win on three ways pays three times.",
           "help": "click / ENTER  spin     < >  bet     %s  paytable     ESC  back",
           "sp_spin": "spin", "sp_bet": "bet", "sp_pays": "paytable", "help_pt": "ENTER / ESC  back"},
    "it": {"slot": "Slot",
           "test": "Prova", "pr_titolo": "Tutti i simboli, con le loro animazioni",
           "pr_aiuto": "un tasto qualsiasi  indietro", "spin": "Gira", "play": "Gioca",
           "m_prova": "Classic Slot", "m_nuova": "Space Slot",
           "bet": "Puntata",
           "pays": "Pagamenti", "back": "Indietro", "win": "Vinci %s",
           "no_win": "Niente", "broke": "Non hai abbastanza soldi",
           "tot_bet": "Puntata", "per_line": "Per unita", "lines": "Modi",
           "free_spins": "Giri gratis", "win_row": "Vincita", "won_free": "%d giri gratis",
           "ways_win": "%d x %s  su %d modi",
           "credit": "Credito", "jackpot": "Jackpot",
           "st_spins": "Giri", "st_bet": "Puntato", "st_won": "Vinto",
           "last_wins": "Ultime vincite",
           "won_jack": "JACKPOT!  %s",
           "pt_jack": "Uno su ognuno dei sei rulli vince il jackpot: %s",
           "pt_title": "Pagamenti", "pt_bet": "premi alla puntata di %s",
           "pt_wild": "Jolly: vale per tutti i simboli, ma servono almeno due simboli veri",
           "pt_gift": "Regalo: tre o piu' dovunque siano, e dentro c'e' un premio a caso",
           "pt_dice": "Dadi: tre o piu' dovunque siano vincono %d giri gratis",
           "pt_bonus": "Bonus: paga dovunque sia, sulla puntata intera",
           "pt_line": "Stesso simbolo su rulli attaccati da sinistra, in qualunque posizione: %d modi. I numeri sono per ogni modo, quindi una vincita su tre modi paga tre volte.",
           "help": "clic / INVIO  gira     < >  puntata     %s  pagamenti     ESC  indietro",
           "sp_spin": "gira", "sp_bet": "puntata", "sp_pays": "pagamenti", "help_pt": "INVIO / ESC  indietro"},
    "fr": {"slot": "Machine",
           "test": "Essai",
           "pr_titolo": "Tous les symboles, avec leurs animations",
           "pr_aiuto": "une touche  retour", "spin": "Tourner", "play": "Jouer",
           "m_prova": "Classic Slot", "m_nuova": "Space Slot",
           "bet": "Mise",
           "pays": "Gains", "back": "Retour", "win": "Vous gagnez %s",
           "no_win": "Rien", "broke": "Pas assez d'argent",
           "tot_bet": "Mise", "per_line": "Par unite", "lines": "Facons",
           "free_spins": "Tours gratuits", "win_row": "Gain", "won_free": "%d tours gratuits",
           "ways_win": "%d x %s  sur %d facons",
           "credit": "Credit", "jackpot": "Jackpot",
           "st_spins": "Tours", "st_bet": "Mise", "st_won": "Gagne",
           "last_wins": "Derniers gains",
           "won_jack": "JACKPOT !  %s",
           "pt_jack": "Un sur chacun des six rouleaux gagne le jackpot : %s",
           "pt_title": "Table des gains", "pt_bet": "gains pour une mise de %s",
           "pt_wild": "Joker : remplace tout, mais il faut au moins deux vrais symboles",
           "pt_gift": "Cadeau : trois ou plus n'importe ou, avec un prix au hasard",
           "pt_dice": "Des : trois ou plus n'importe ou gagnent %d tours gratuits",
           "pt_bonus": "Bonus : paie partout, sur la mise totale",
           "pt_line": "Meme symbole sur des rouleaux voisins depuis la gauche : %d facons. Les gains sont par facon.",
           "help": "clic / ENTREE  tourner     < >  mise     %s  gains     ECHAP  retour",
           "sp_spin": "tourner", "sp_bet": "mise", "sp_pays": "gains", "help_pt": "ENTREE / ECHAP  retour"},
    "es": {"slot": "Tragaperras",
           "test": "Prueba", "pr_titolo": "Todos los simbolos, con sus animaciones",
           "pr_aiuto": "una tecla  volver", "spin": "Girar", "play": "Jugar",
           "m_prova": "Classic Slot", "m_nuova": "Space Slot",
           "bet": "Apuesta",
           "pays": "Premios", "back": "Atras", "win": "Ganas %s",
           "no_win": "Nada", "broke": "No tienes bastante dinero",
           "tot_bet": "Apuesta", "per_line": "Por unidad", "lines": "Modos",
           "free_spins": "Giros gratis", "win_row": "Ganancia", "won_free": "%d giros gratis",
           "ways_win": "%d x %s  en %d modos",
           "credit": "Credito", "jackpot": "Jackpot",
           "st_spins": "Giros", "st_bet": "Apostado", "st_won": "Ganado",
           "last_wins": "Ultimos premios",
           "won_jack": "JACKPOT!  %s",
           "pt_jack": "Uno en cada uno de los seis rodillos gana el jackpot: %s",
           "pt_title": "Tabla de premios", "pt_bet": "premios con apuesta de %s",
           "pt_wild": "Comodin: vale por todos, pero hacen falta dos simbolos reales",
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
           "bar": "Bar", "sette": "Seven", "palla8": "Eight ball", "jolly": "Wild",
           "dadi": "Dice", "regalo": "Gift", "jackpot": "Jackpot"},
    "it": {"ciliegia": "Ciliegia", "limone": "Limone", "arancia": "Arancia",
           "prugna": "Prugna", "mela": "Mela", "fragola": "Fragola",
           "anguria": "Anguria", "uva": "Uva", "cuori": "Cuori",
           "picche": "Picche", "fiori": "Fiori", "quadri": "Quadri",
           "campana": "Campana", "ferro": "Ferro di cavallo",
           "quadrifoglio": "Quadrifoglio", "carte": "Carte",
           "roulette": "Roulette", "fiches": "Fiches", "dollaro": "Moneta",
           "gemma": "Gemma", "bar": "Bar", "sette": "Sette", "palla8": "Palla otto",
           "jolly": "Jolly", "dadi": "Dadi", "regalo": "Regalo",
           "jackpot": "Jackpot"},
    "fr": {"ciliegia": "Cerise", "limone": "Citron", "arancia": "Orange",
           "prugna": "Prune", "mela": "Pomme", "fragola": "Fraise",
           "anguria": "Pasteque", "uva": "Raisin", "cuori": "Coeur",
           "picche": "Pique", "fiori": "Trefle", "quadri": "Carreau",
           "campana": "Cloche", "ferro": "Fer a cheval",
           "quadrifoglio": "Trefle porte-bonheur", "carte": "Cartes",
           "roulette": "Roulette", "fiches": "Jetons", "dollaro": "Piece",
           "gemma": "Gemme", "bar": "Bar", "sette": "Sept", "palla8": "Boule huit",
           "jolly": "Joker", "dadi": "Des", "regalo": "Cadeau",
           "jackpot": "Jackpot"},
    "es": {"ciliegia": "Cereza", "limone": "Limon", "arancia": "Naranja",
           "prugna": "Ciruela", "mela": "Manzana", "fragola": "Fresa",
           "anguria": "Sandia", "uva": "Uvas", "cuori": "Corazon",
           "picche": "Pica", "fiori": "Trebol", "quadri": "Diamante",
           "campana": "Campana", "ferro": "Herradura",
           "quadrifoglio": "Trebol de cuatro", "carte": "Cartas",
           "roulette": "Ruleta", "fiches": "Fichas", "dollaro": "Moneda",
           "gemma": "Gema", "bar": "Bar", "sette": "Siete", "palla8": "Bola ocho",
           "jolly": "Comodin", "dadi": "Dados", "regalo": "Regalo",
           "jackpot": "Jackpot"},
}


def T(k):
    d = TXT.get(B.CFG.get("lingua", "en"), TXT["en"])
    return d.get(k, TXT["en"].get(k, k))


# Come si chiamano i simboli in una macchina che non e' la classica.
# I nomi dei file sono le CASELLE della tabella dei pagamenti, non i
# nomi dei disegni: "prugna" vuol dire "il quarto simbolo basso". Qui
# si dice come si chiama davvero quel disegno in quella macchina, cosi'
# il tabellone non scrive Prugna sotto un pianeta nano.
# I nomi propri (Eris, Cerere, Titano...) si scrivono una volta sola e
# valgono per tutte le lingue; quelli che si traducono hanno il loro
# dizionario per lingua.
NOMI_TEMA = {
    "nuova": {
        "ciliegia": "Asteroid", "limone": "Ceres", "arancia": "Makemake",
        "prugna": "Eris", "mela": "Pluto", "fragola": "Moon",
        "anguria": "Mercury", "uva": "Venus",
        "cuori": "Mars", "picche": "Kepler-22b", "fiori": "Uranus",
        "quadri": "Neptune",
        "campana": "TRAPPIST-1", "ferro": "Proxima", "quadrifoglio": "Jupiter",
        "carte": "Earth", "roulette": "Saturn", "fiches": "Planet X",
        "gemma": "Space Gun", "bar": "Rocket", "sette": "Sun",
        "regalo": "Alien",
        "dollaro": "Galaxy", "palla8": "Nebula",
        "jolly": "Wild", "dadi": "Comet",
    },
}
# le poche che cambiano da lingua a lingua
NOMI_TEMA_LINGUA = {
    "nuova": {
        "it": {"ciliegia": "Asteroide", "limone": "Cerere", "prugna": "Eride",
               "mela": "Plutone", "fragola": "Luna", "anguria": "Mercurio",
               "uva": "Venere", "cuori": "Marte",
               "fiori": "Urano", "quadri": "Nettuno", "quadrifoglio": "Giove",
               "carte": "Terra", "roulette": "Saturno", "fiches": "Pianeta X",
               "gemma": "Pistola Laser", "bar": "Razzo", "regalo": "Alieno", "sette": "Sole",
               "dollaro": "Galassia", "palla8": "Nebulosa",
               "jolly": "Wild", "dadi": "Cometa"},
        "fr": {"ciliegia": "Asteroide", "limone": "Ceres", "prugna": "Eris",
               "mela": "Pluton", "fragola": "Lune", "anguria": "Mercure",
               "uva": "Venus", "cuori": "Mars",
               "fiori": "Uranus", "quadri": "Neptune", "quadrifoglio": "Jupiter",
               "carte": "Terre", "roulette": "Saturne", "fiches": "Planete X",
               "gemma": "Pistolet Laser", "bar": "Fusee", "regalo": "Alien", "sette": "Soleil",
               "dollaro": "Galaxie", "palla8": "Nebuleuse",
               "jolly": "Wild", "dadi": "Comete"},
        "es": {"ciliegia": "Asteroide", "limone": "Ceres", "prugna": "Eris",
               "mela": "Pluton", "fragola": "Luna", "anguria": "Mercurio",
               "uva": "Venus", "cuori": "Marte",
               "fiori": "Urano", "quadri": "Neptuno", "quadrifoglio": "Jupiter",
               "carte": "Tierra", "roulette": "Saturno", "fiches": "Planeta X",
               "gemma": "Pistola Laser", "bar": "Cohete", "regalo": "Alien", "sette": "Sol",
               "dollaro": "Galaxia", "palla8": "Nebulosa",
               "jolly": "Wild", "dadi": "Cometa"},
    },
}


def nome_simbolo(s):
    """Come si chiama questo simbolo adesso. Se la macchina ha i suoi
    nomi si usano quelli, se no quelli della classica."""
    lg = B.CFG.get("lingua", "en")
    suoi = NOMI_TEMA.get(tema())
    if suoi and s in suoi:
        per_lingua = NOMI_TEMA_LINGUA.get(tema(), {}).get(lg, {})
        return per_lingua.get(s) or suoi[s]
    d = NOMI_SIM.get(lg, NOMI_SIM["en"])
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


SUONI_TEMA = [None]


def _carica_cartella(cartella, solo_nuovi=False):
    """I file di una cartella dentro SUONI. I file col trattino e un
    numero stanno insieme: vinci1-1, vinci1-2... sono tutti "vinci1", e
    a ogni vincita se ne sente uno a caso."""
    if not os.path.isdir(cartella):
        return
    for f in sorted(os.listdir(cartella)):
        if not f.lower().endswith((".ogg", ".wav", ".mp3")):
            continue
        nome = re.sub(r"-\d+$", "", os.path.splitext(f)[0].lower())
        if solo_nuovi and nome in SUONI:
            continue
        try:
            s = pygame.mixer.Sound(os.path.join(cartella, f))
            SUONI.setdefault(nome, []).append(s)
            DURATE[nome] = s.get_length()
        except pygame.error:
            pass


def carica_suoni():
    """I suoni della macchina di adesso: prima i suoi, in
    audio/slot/<tema>/fx, poi quelli della classica per tutto quello che
    lui non ha. Cosi' una macchina nuova suona fin dal primo giorno e i
    suoi suoni si mettono uno alla volta."""
    if not B.MUSICA_OK:
        return
    ora = tema()
    if SUONI and SUONI_TEMA[0] == ora:
        return
    SUONI.clear()
    DURATE.clear()
    SENTITO.clear()
    SUONI_TEMA[0] = ora
    _carica_cartella(os.path.join(B.SUONI_DIR, "slot", ora, "fx"))
    _carica_cartella(os.path.join(B.SUONI_DIR, "slot", TEMA_BASE, "fx"), True)
    # e la vecchia cartella senza tema, per non perdere niente
    _carica_cartella(os.path.join(B.SUONI_DIR, "slot", "fx"), True)


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


SENTITO = {}


def quanto_suona(nome, se_manca):
    """Quanto si SENTE quel suono, non quanto e' lungo il file: la coda
    di silenzio in fondo non conta. Il giro della slot finisce prima
    della fine di spin.ogg, e i rulli devono fermarsi con lui, non nel
    silenzio dopo. Si misura una volta sola e si tiene da parte."""
    if nome in SENTITO:
        return SENTITO[nome]
    gruppo = SUONI.get(nome)
    fine = quanto_dura(nome, se_manca)
    if gruppo:
        try:
            fine = _coda(gruppo[0], fine)
        except Exception:
            pass
    SENTITO[nome] = fine
    return fine


def _coda(suono, intero):
    """Dove muore davvero il suono: si torna indietro a blocchi di dieci
    millesimi finche' non si trova roba sopra l'uno e mezzo per cento."""
    init = pygame.mixer.get_init()
    if not init:
        return intero
    freq, misura, canali = init[0], init[1], init[2]
    tipo = {8: "B", -8: "b", 16: "H", -16: "h", 32: "l", -32: "l"}.get(misura)
    if tipo is None:
        return intero
    dati = array.array(tipo)
    grezzo = suono.get_raw()
    avanzo = len(grezzo) % dati.itemsize
    dati.frombytes(grezzo[:len(grezzo) - avanzo] if avanzo else grezzo)
    if not len(dati):
        return intero
    meta = 0 if misura < 0 else (1 << (abs(misura) - 1))
    picco = max(abs(x - meta) for x in dati[::97]) or 1
    soglia = picco * 0.015
    blocco = max(1, int(freq * 0.01)) * max(1, canali)
    i = len(dati)
    while i > blocco:
        pezzo = dati[i - blocco:i]
        if max(abs(x - meta) for x in pezzo) > soglia:
            break
        i -= blocco
    sentito = i / float(freq * max(1, canali))
    # un filo di aria in fondo, e mai meno di mezzo suono
    return max(intero * 0.5, min(intero, sentito + 0.05))


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


NUDE = {}


def fotogramma(fr, pos):
    """Il fotogramma alla posizione chiesta, che pero' non e' un numero
    intero: fra un fotogramma e quello dopo si sfuma. Senza questo un
    disegno che cambia due volte al secondo si vede scattare; sfumando,
    gli stessi identici fotogrammi scorrono lisci."""
    n = len(fr)
    if n < 2:
        return fr[0]
    pos = pos % n
    i = int(pos)
    k = pos - i
    if k < 0.02:
        return fr[i]
    try:
        import numpy as np
    except ImportError:
        return fr[i]
    a, b = fr[i], fr[(i + 1) % n]
    if a.get_size() != b.get_size():
        return fr[i]
    # si mescola tenendo conto della trasparenza, se no dove uno dei due
    # e' trasparente esce il nero che ci sta sotto
    aa = pygame.surfarray.array_alpha(a).astype("float32") / 255.0
    ab = pygame.surfarray.array_alpha(b).astype("float32") / 255.0
    al = aa * (1.0 - k) + ab * k
    pm = (pygame.surfarray.array3d(a).astype("float32") * aa[:, :, None] *
          (1.0 - k) +
          pygame.surfarray.array3d(b).astype("float32") * ab[:, :, None] * k)
    rgb = pm / np.maximum(al, 1e-4)[:, :, None]
    sup = pygame.Surface(a.get_size(), pygame.SRCALPHA)
    pygame.surfarray.blit_array(sup, np.clip(rgb, 0, 255).astype("uint8"))
    pygame.surfarray.pixels_alpha(sup)[:, :] = np.clip(
        al * 255, 0, 255).astype("uint8")
    return sup


def sposta_fine(img, fx, fy):
    """Sposta il disegno di una frazione di pixel. Serve a chi si muove
    piano: un galleggiamento di quattro pixel in sette secondi, potendosi
    posare solo su pixel interi, sta fermo mezzo secondo e poi salta.
    Spostandolo per meta' pixel scorre liscio come il tremolio dei dadi,
    che sembra fluido solo perche' e' veloce."""
    w, h = img.get_size()
    try:
        import numpy as np
    except ImportError:
        return img
    fx = min(max(fx, 0.0), 1.0)
    fy = min(max(fy, 0.0), 1.0)
    al = pygame.surfarray.array_alpha(img).astype("float32") / 255.0
    pm = pygame.surfarray.array3d(img).astype("float32") * al[:, :, None]
    # la tela e' sempre un pixel piu' grande, cosi' la cornice non cambia
    # di misura da un fotogramma all'altro
    gpm = np.zeros((w + 1, h + 1, 3), "float32")
    gal = np.zeros((w + 1, h + 1), "float32")
    for ox, oy, peso in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)),
                         (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        if peso <= 0.0:
            continue
        gpm[ox:ox + w, oy:oy + h] += pm * peso
        gal[ox:ox + w, oy:oy + h] += al * peso
    rgb = gpm / np.maximum(gal, 1e-4)[:, :, None]
    sup = pygame.Surface((w + 1, h + 1), pygame.SRCALPHA)
    pygame.surfarray.blit_array(sup, np.clip(rgb, 0, 255).astype("uint8"))
    pygame.surfarray.pixels_alpha(sup)[:, :] = np.clip(
        gal * 255, 0, 255).astype("uint8")
    return sup


def con_fiamma(img, forza, tt, fase=0.0):
    """La spinta dietro al razzo. Il pennacchio si disegna sotto, su una
    tela piu' alta, e si SOMMA alla luce invece di coprirla: il fuoco non
    ha un contorno, e' luce. La fiammata si allunga e si accorcia da se',
    con due ritmi diversi, cosi' non si sente il ciclo."""
    try:
        import numpy as np
    except ImportError:
        return img
    w, h = img.get_size()
    lungo = max(8, int(h * 0.78))
    su = int(lungo * 0.62)
    sfuria = (0.74 + 0.20 * math.sin(tt * 9.0 + fase) +
              0.10 * math.sin(tt * 15.7 + fase * 1.7))
    yy, xx = np.meshgrid(np.arange(h + lungo + su), np.arange(w),
                         indexing="ij")
    yy = yy.astype("float32")
    xx = xx.astype("float32")
    y0 = su + h * 0.90
    t = np.clip((yy - y0) / (lungo * sfuria), 0.0, 1.0)
    vivo = (yy >= y0) & (t < 1.0)
    # il getto ondeggia piano mentre scende
    cx = w * 0.5 + np.sin(t * 5.5 + tt * 6.0 + fase) * w * 0.025 * t
    largo = np.maximum(w * 0.035, w * 0.150 * (1.0 - t * 0.62))
    calore = np.exp(-((xx - cx) / largo) ** 2) * (1.0 - t) ** 1.15 * vivo
    calore *= forza * 1.25 * (0.85 + 0.15 * math.sin(tt * 21.0 + fase))
    rgb = np.zeros((w, h + lungo + su, 3), "float32")
    c = calore.T
    # dal bianco al giallo all'arancio: il cuore e' quasi bianco
    rgb += (c ** 2.6)[:, :, None] * np.array([255, 250, 225], "float32")
    rgb += (c ** 1.5)[:, :, None] * np.array([255, 186, 60], "float32") * 0.95
    rgb += c[:, :, None] * np.array([255, 92, 30], "float32") * 0.70
    alfa = np.clip(c * 1.35, 0, 1) * 255
    sup = pygame.Surface((w, h + lungo + su), pygame.SRCALPHA)
    pygame.surfarray.blit_array(sup, np.clip(rgb, 0, 255).astype("uint8"))
    pygame.surfarray.pixels_alpha(sup)[:, :] = alfa.astype("uint8")
    sup.blit(img, (0, su))
    return sup


def misura_simbolo(nome, misura):
    """Quanto va disegnato grande quel simbolo. Di suo ognuno occupa la
    stessa casella, ma certi disegni chiedono piu' spazio (la galassia)
    e certi ne vogliono meno (un sasso)."""
    an = ANIMAZIONI.get(tema(), {}).get(nome)
    k = (an or {}).get("misura", 1.0)
    if k == 1.0:
        return misura
    return (max(4, int(misura[0] * k)), max(4, int(misura[1] * k)))


def frames_disegnati(nome, misura):
    """I fotogrammi dei simboli che non sono una PNG ma li disegna il
    codice. Niente se questo simbolo non e' uno di quelli."""
    an = ANIMAZIONI.get(tema(), {}).get(nome)
    if not an:
        return None
    if an.get("galassia"):
        return frames_galassia(misura)
    if an.get("pleiadi"):
        return frames_pleiadi(misura)
    if an.get("nebbia"):
        return frames_nebbia(misura, an.get("colori"))
    if an.get("alieno"):
        return frames_alieno(nome, misura)
    if an.get("targa"):
        return frames_targa(nome, misura, an.get("colori"))
    return None


def figura(nome, misura):
    """Il disegno di un simbolo come si vede nel gioco: la palla con il
    suo anello, se ne ha uno."""
    chiave = (tema(), nome, misura)
    if chiave in NUDE:
        return NUDE[chiave]
    # i simboli che disegna il codice (galassia, nebulosa, Pleiadi) non
    # hanno una PNG: il loro primo fotogramma E' la loro faccia, se no
    # sui rulli si vedrebbe ancora il disegno vecchio
    misura = misura_simbolo(nome, misura)
    fr = frames_disegnati(nome, misura)
    if fr:
        NUDE[chiave] = fr[0]
        return fr[0]
    c = corona_di(nome)
    if c:
        palla = figura_nuda(nome, (max(4, int(misura[0] * c["palla"])),
                                   max(4, int(misura[1] * c["palla"]))))
        NUDE[chiave] = con_corona(nome, palla, misura)
        return NUDE[chiave]
    if not anello_di(nome):
        NUDE[chiave] = figura_nuda(nome, misura)
        return NUDE[chiave]
    palla = figura_nuda(nome, misura_palla(nome, misura))
    NUDE[chiave] = con_anello(nome, palla, misura_anello(nome, misura))
    return NUDE[chiave]


def figura_nuda(nome, misura):
    """La palla e basta, senza anello: e' da questa che si fanno i
    fotogrammi della rotazione, se no girerebbe anche l'anello.
    Se la PNG del tema non c'e' si disegna un segnaposto, cosi' la
    macchina si prova anche senza grafica."""
    chiave = (tema(), nome, misura)
    if chiave in FIGURE:
        return FIGURE[chiave]
    w, h = misura
    q = None
    f = os.path.join(GFX, tema(), nome + ".png")
    if not os.path.isfile(f):
        # il tema non ce l'ha ancora: si usa quello della classica
        f = os.path.join(GFX, TEMA_BASE, nome + ".png")
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


# i rulli: chiari come le macchine di una volta, o scuri come quelle
# moderne. Basta cambiare questa riga.
RULLI_CHIARI = False


CIELI = {}
STELLE = {}
# la slot dello spazio non ha le lampadine intorno alla cornice: al loro
# posto, dietro ai rulli, c'e' il cielo
SENZA_LUCI = ("nuova",)
COL_CIELO = ("nuova",)


def cielo_fondo(misura):
    """Il buio dietro ai rulli, e basta: niente nebbie, niente aloni.
    Le stelle si disegnano a parte, perche' si accendono."""
    if misura in CIELI:
        return CIELI[misura]
    sup = pygame.Surface(misura, pygame.SRCALPHA)
    sup.fill((6, 7, 15, 216))
    CIELI[misura] = sup
    return sup


def stelle_cielo(misura):
    """Dove stanno le stelle, di che colore sono e con che ritmo si
    accendono. Ognuna va per conto suo, se no battono tutte insieme."""
    if misura in STELLE:
        return STELLE[misura]
    w, h = misura
    rnd = random.Random(9)
    fuori = []
    for _ in range(max(50, (w * h) // 850)):
        x, y = rnd.randrange(w), rnd.randrange(h)
        k = rnd.random()
        if k > 0.965:
            col, lato = (255, 255, 255), max(2, int(B.s(2)))
        elif k > 0.80:
            col = rnd.choice(((214, 228, 255), (255, 238, 212)))
            lato = max(1, int(B.s(1.4)))
        else:
            col, lato = (150, 168, 210), max(1, int(B.s(1)))
        fuori.append((x, y, col, lato,
                      rnd.uniform(0.35, 0.95),      # quanto si spegne
                      rnd.uniform(0.6, 2.4),        # con che ritmo
                      rnd.uniform(0.0, 6.28)))
    STELLE[misura] = fuori
    return fuori


def disegna_cielo(sc, rett, tt):
    """Il cielo dietro ai rulli: il buio e la nebbia stanno fermi, le
    stelline si accendono e si spengono una per conto suo."""
    sc.blit(cielo_fondo(rett.size), rett)
    for x, y, col, lato, quanto, ritmo, fase in stelle_cielo(rett.size):
        k = 1.0 - quanto * (0.5 + 0.5 * math.sin(tt * ritmo + fase))
        sc.fill((int(col[0] * k), int(col[1] * k), int(col[2] * k)),
                (rett.x + x, rett.y + y, lato, lato))


SEPARATORE = [None]


def separatore(alta):
    """La riga fra un rullo e l'altro: appena accennata, e che si spegne
    verso le due punte invece di tagliare netto da cima a fondo."""
    if SEPARATORE[0] is not None and SEPARATORE[0].get_height() == alta:
        return SEPARATORE[0]
    largo = max(1, int(B.s(1)))
    col = (206, 198, 180) if RULLI_CHIARI else (108, 104, 136)
    q = pygame.Surface((largo, alta), pygame.SRCALPHA)
    sfuma = max(1.0, alta * 0.22)
    for y in range(alta):
        k = min(1.0, y / sfuma, (alta - 1 - y) / sfuma)
        q.fill(col + (int(58 * k),), (0, y, largo, 1))
    SEPARATORE[0] = q
    return q


def vetro_fondo(misura):
    """Il fondo dei rulli fatto come un cilindro vero: si scurisce verso
    l'alto e verso il basso, dove il rullo gira via, e in mezzo prende la
    luce, con un filo di riflesso sul vetro."""
    if VETRO[0] is None or VETRO[0].get_size() != misura:
        w, h = misura
        q = pygame.Surface(misura)
        if RULLI_CHIARI:
            mezzo, bordo = (250, 246, 236), (188, 180, 164)
        else:
            mezzo, bordo = (54, 50, 74), (10, 10, 16)
        for y in range(h):
            k = abs(y - h * 0.5) / (h * 0.5)
            k = k ** 1.6                       # il buio si stringe ai bordi
            q.fill(tuple(int(mezzo[i] + (bordo[i] - mezzo[i]) * k)
                         for i in range(3)), (0, y, w, 1))
        # il riflesso del vetro: una fascia chiara che taglia in alto
        luce = pygame.Surface(misura, pygame.SRCALPHA)
        alto = int(h * 0.30)
        for y in range(alto):
            a = int(26 * (1 - y / float(alto)))
            luce.fill((255, 255, 255, a), (0, y, w, 1))
        basso = int(h * 0.16)
        for y in range(basso):
            a = int(16 * (y / float(basso)))
            luce.fill((255, 255, 255, a), (0, h - basso + y, w, 1))
        q.blit(luce, (0, 0))
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


ALONI = {}
GRANELLI = {}
LED_PIENI = {}
LED = {}
LED_COLORI = 24          # quanti colori diversi sulla ruota
LED_LIVELLI = 10         # quanti gradini fra spenta e accesa


def _led_pieno(lato, ih):
    """Il LED acceso al massimo: il vetro quasi bianco in mezzo e
    l'alone del suo colore intorno, che sfuma fino a sparire."""
    chiave = (lato, ih)
    if chiave in LED_PIENI:
        return LED_PIENI[chiave]
    r, g, b = colorsys.hsv_to_rgb(ih / float(LED_COLORI), 0.75, 1.0)
    col = (r * 255.0, g * 255.0, b * 255.0)
    q = pygame.Surface((lato, lato), pygame.SRCALPHA)
    mezzo = lato / 2.0
    for y in range(lato):
        for x in range(lato):
            d = math.hypot(x - mezzo + 0.5, y - mezzo + 0.5) / mezzo
            if d >= 1.0:
                continue
            if d <= 0.20:
                k, bianco = 1.0, 0.92         # il filamento, quasi bianco
            elif d <= 0.42:
                p = (d - 0.20) / 0.22
                k = 1.0 - 0.22 * p            # il vetro, del suo colore
                bianco = 0.92 * (1.0 - p) ** 1.4
            else:
                p = (d - 0.42) / 0.58
                k = 0.78 * (1.0 - p) ** 2.5   # l'alone che sfuma
                bianco = 0.0
            q.set_at((x, y), tuple(
                min(255, int((col[j] + (255.0 - col[j]) * bianco) * k))
                for j in range(3)) + (255,))
    LED_PIENI[chiave] = q
    return q


def led(lato, giro, forza):
    """Una lucina LED, da sommare allo sfondo come fa la luce vera.
    Colore e accensione si arrotondano a gradini, cosi' le lucine gia'
    fatte si riusano invece di ridisegnarle sessanta volte al secondo."""
    ih = int((giro % 1.0) * LED_COLORI) % LED_COLORI
    i_f = max(0, min(LED_LIVELLI, int(forza * LED_LIVELLI + 0.5)))
    chiave = (lato, ih, i_f)
    if chiave in LED:
        return LED[chiave]
    q = _led_pieno(lato, ih)
    if i_f < LED_LIVELLI:
        v = int(255 * i_f / float(LED_LIVELLI))
        q = q.copy()
        q.fill((v, v, v, 255), special_flags=pygame.BLEND_RGB_MULT)
    LED[chiave] = q
    return q


def granello(lato, col, forza):
    """Un granello di polvere luminosa: il colore si spegne verso i
    bordi, cosi' sommandolo allo sfondo non si vede il quadrato. Si
    tengono da parte gia' fatti, per misura, colore e forza."""
    f = max(0, min(15, int(forza * 15)))
    chiave = (lato, tuple(col), f)
    if chiave in GRANELLI:
        return GRANELLI[chiave]
    q = pygame.Surface((lato, lato), pygame.SRCALPHA)
    mezzo = lato / 2.0
    k_f = f / 15.0
    for y in range(lato):
        for x in range(lato):
            d = math.hypot(x - mezzo + 0.5, y - mezzo + 0.5) / mezzo
            k = max(0.0, 1.0 - d) ** 2.2 * k_f
            q.set_at((x, y), (int(col[0] * k), int(col[1] * k),
                              int(col[2] * k), 255))
    GRANELLI[chiave] = q
    return q


def alone_radiale(lato, col):
    """Un alone tondo e sfumato, del colore del simbolo: si accende
    dietro le icone che stanno pagando."""
    chiave = (lato, tuple(col))
    if chiave in ALONI:
        return ALONI[chiave]
    q = pygame.Surface((lato, lato), pygame.SRCALPHA)
    passi = max(10, lato // 4)
    for i in range(passi):
        k = 1 - i / float(passi)          # 1 fuori, 0 dentro
        r = int(lato * 0.5 * k)
        a = int(230 * (1 - k) ** 1.7)
        if r > 0:
            pygame.draw.circle(q, tuple(col) + (a,),
                               (lato // 2, lato // 2), r)
    ALONI[chiave] = q
    return q


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
GRANDE = 0.52

# --------------------------------------------- i simboli che si animano
# Le animazioni si accendono SOLO quando quel simbolo sta pagando, e
# solo a rulli fermi. Il resto del tempo i simboli stanno fermi: se si
# muove tutto, non si capisce piu' cosa hai vinto.
# Per tema e per simbolo:
#   gira     giri al secondo: il pianeta ruota sul proprio asse
#   scia     quanti granelli al secondo si lascia dietro
#   verso    da che parte se ne va la scia
#   colore   di che colore sono i granelli
#   onda     di quanto ondeggia, in frazione di casella
# Chi non e' qui dentro fa quello di sempre: respira e basta.
# Quanto vanno veloci tutte le animazioni, tutte insieme. I numeri della
# tabella qui sotto restano i rapporti fra un simbolo e l'altro: questo
# li rallenta o li accelera tutti mantenendo le proporzioni.
VELOCITA = 0.5

ANIMAZIONI = {
    "nuova": {
        # Ogni pianeta gira alla SUA velocita', e l'ordine e' quello
        # vero: Giove e Cerere sono i piu' svelti (dieci ore di giornata),
        # Mercurio e la Luna quasi fermi, e Venere gira AL CONTRARIO,
        # perche' e' l'unico del sistema solare a farlo davvero.
        # I numeri sono giri al secondo, compressi: a tenere le
        # proporzioni vere Venere avrebbe impiegato mezz'ora a girare.
        # l'asteroide e' un sasso: galleggia, e sta piccolo
        "ciliegia": {"onda": 0.05, "misura": 0.67},
        "limone": {"gira": 0.80},                # Cerere, 9 ore
        "arancia": {"gira": 0.52},               # Makemake, 22 ore
        "prugna": {"gira": 0.47},                # Eris, 26 ore
        # Plutone e' un nano: gira, ma sta piccolo
        "mela": {"gira": 0.30, "misura": 0.68},  # Plutone, 6 giorni
        "fragola": {"gira": 0.22},               # Luna, 27 giorni
        "anguria": {"gira": 0.18},               # Mercurio, 59 giorni
        "uva": {"gira": -0.14},                  # Venere, al contrario
        "cuori": {"gira": 0.49},                 # Marte, 24 ore e mezza
        "picche": {"gira": 0.44},                # esopianeta
        "fiori": {"gira": 0.60},                 # Urano, 17 ore
        "quadri": {"gira": 0.62},                # Nettuno, 16 ore
        "campana": {"gira": 0.25},               # TRAPPIST-1, una stella
        "ferro": {"gira": 0.28},                 # Proxima, una stella
        "quadrifoglio": {"gira": 0.78},          # Giove, 9 ore e 55
        "carte": {"gira": 0.50},                 # Terra, 24 ore
        "roulette": {"gira": 0.74},           # Saturno, 10 ore e mezza
        "fiches": {"gira": 0.35},                # il pianeta X
        # la galassia a spirale: disegnata dal codice, gira su se stessa
        "dollaro": {"galassia": 0.06, "misura": 1.95},
        # la nebulosa non e' una PNG: la disegna il codice, tre veli di
        # nebbia che scorrono uno sull'altro e le stelle che brillano
        "palla8": {"nebbia": 0.18,
                   "colori": ((188, 92, 224), (236, 96, 168), (86, 150, 255))},
        # la pistola: sta ferma e butta qualche scintilla
        "gemma": {"scia": 20, "verso": (0.0, -0.20), "sparso": 0.40,
                  "colore": (130, 235, 200), "pixel": True},
        # il razzo: balla come i dadi, perche' si muove mentre va, e
        # dietro ha la fiammata che lo spinge
        "bar": {"trema": 0.030, "fiamma": 1.0, "misura": 0.86,
                "scia": 20, "verso": (0.0, 0.55), "sparso": 0.30,
                "colore": (255, 190, 110), "pixel": True},
        # l'astronauta non e' ancora di nessuno: sta in magazzino e
        # intanto capitombola piano
        "astronauta": {"rotola": 0.05, "misura": 0.80,
                       "scia": 20, "verso": (0.0, -0.20), "sparso": 0.40,
                       "colore": (210, 228, 255), "pixel": True},
        # le targhe: la scritta sta ferma, si muove solo la nebbia
        # che ci sta dietro
        "jolly": {"targa": 0.10, "scia": 26, "verso": (0.0, -0.22),
                  "sparso": 0.46, "colore": (170, 215, 255), "pixel": True,
                  "alone": False,
                  "colori": ((120, 90, 235), (90, 170, 255), (210, 120, 255))},
        # i giri gratis li porta la cometa: fluttua e lascia la scia
        "dadi": {"onda": 0.05, "scia": 60, "verso": (-1.0, 0.30),
                 "colore": (150, 200, 255), "misura": 0.67},
        # il bonus e' l'alieno: sta com'e' e galleggia piano
        "regalo": {"onda": 0.040,
                   "scia": 20, "verso": (0.0, -0.20), "sparso": 0.40,
                   "colore": (200, 170, 255), "pixel": True},
        # il jackpot:
        "jackpot": {"targa": 0.10, "misura": 1.35,
                    "scia": 26, "verso": (0.0, -0.22),
                    "sparso": 0.46, "colore": (255, 205, 120),
                    "pixel": True, "alone": False,
                    "colori": ((235, 120, 60), (255, 70, 120),
                               (180, 60, 210))},
    },
}


def animazione(nome):
    """Come si muove quel simbolo in questa macchina, o niente."""
    return ANIMAZIONI.get(tema(), {}).get(nome)


# ------------------------------------------------------------ gli anelli
# Saturno e Urano si scaricano come palle lisce e l'anello glielo
# disegniamo noi: se stesse dentro la PNG girerebbe insieme al pianeta,
# che e' sbagliato. Cosi' invece resta fermo mentre la palla ruota.
#   fuori/dentro  dove comincia e dove finisce, in raggi del pianeta
#   schiaccia     quanto e' di taglio (0 = visto di spigolo, 1 = di faccia)
#   inclina       di quanti gradi e' storto. Urano e' coricato su un
#                 fianco per davvero, quindi i suoi anelli sono verticali
#   divisione     dove passa la riga vuota dentro l'anello (0 = nessuna)
ANELLI = {
    "nuova": {
        "roulette": {"fuori": 1.95, "dentro": 1.26, "schiaccia": 0.44,
                     "inclina": -11, "colore": (228, 206, 158),
                     "opaco": 235, "divisione": 0.0},
        "fiori": {"fuori": 1.62, "dentro": 1.28, "schiaccia": 0.30,
                  "inclina": 80, "colore": (168, 202, 222),
                  "opaco": 165, "divisione": 0.0},
    },
}


def anello_di(nome):
    return ANELLI.get(tema(), {}).get(nome)


def centro_raggio(src):
    """Dove sta la palla dentro l'immagine e quanto e' grossa: si misura
    sul disegno, non sul bordo del file."""
    w, h = src.get_size()
    try:
        import numpy as np
        a = pygame.surfarray.array_alpha(src)
        col = np.where(a.max(axis=1) > 8)[0]
        rig = np.where(a.max(axis=0) > 8)[0]
        if len(col) and len(rig):
            return ((col[0] + col[-1]) / 2.0, (rig[0] + rig[-1]) / 2.0,
                    max(col[-1] - col[0], rig[-1] - rig[0]) / 2.0 + 0.5)
    except (ImportError, ValueError, pygame.error):
        pass
    return ((w - 1) / 2.0, (h - 1) / 2.0, min(w, h) / 2.0)


ANELLI_FATTI = {}


def anello_pezzi(nome, misura, R):
    """L'anello in due pezzi: quello che passa DIETRO al pianeta e quello
    che passa DAVANTI. E' la separazione che lo fa sembrare un anello e
    non un cerchio appiccicato sopra."""
    d = anello_di(nome)
    chiave = (tema(), nome, misura, int(R))
    if chiave in ANELLI_FATTI:
        return ANELLI_FATTI[chiave]
    if not d:
        ANELLI_FATTI[chiave] = None
        return None
    K = 3                                   # si disegna in grande
    L = int(max(misura) * K)
    m = L // 2
    a_f, a_d, sch = R * d["fuori"] * K, R * d["dentro"] * K, d["schiaccia"]
    col = tuple(d["colore"])
    piano = pygame.Surface((L, L), pygame.SRCALPHA)
    try:
        import numpy as np
    except ImportError:
        np = None
    if np is None:
        pygame.draw.ellipse(piano, col + (d.get("opaco", 235),),
                            pygame.Rect(m - a_f, m - a_f * sch,
                                        a_f * 2, a_f * sch * 2))
        pygame.draw.ellipse(piano, (0, 0, 0, 0),
                            pygame.Rect(m - a_d, m - a_d * sch,
                                        a_d * 2, a_d * sch * 2))
    else:
        # l'anello non e' una ciambella piena col bordo netto: sono
        # fasce, ognuna piu' accesa in mezzo e spenta ai lati, come i
        # bracci della galassia. Dentro e fuori si spegne piano, cosi'
        # non si vede dove comincia e dove finisce
        xx, yy = np.meshgrid(np.arange(L), np.arange(L), indexing="ij")
        X = xx - m
        Y = (yy - m) / max(0.05, sch)
        r = np.sqrt(X * X + Y * Y)
        u = (r - a_d) / max(1.0, a_f - a_d)
        fitto = np.zeros((L, L), np.float32)
        for dove, largo, forza in ((0.16, 0.20, 1.00), (0.50, 0.15, 0.78),
                                   (0.80, 0.12, 0.50)):
            fitto += forza * np.exp(-((u - dove) / largo) ** 2)
        fitto *= np.clip(u / 0.20, 0, 1) * np.clip((1.0 - u) / 0.32, 0, 1)
        fitto = np.clip(fitto, 0, 1)
        rgb = (np.array(col, np.float32)[None, None, :] *
               (0.72 + 0.38 * fitto)[:, :, None])
        pygame.surfarray.blit_array(piano, np.clip(rgb, 0, 255).astype(np.uint8))
        pygame.surfarray.pixels_alpha(piano)[:, :] = np.clip(
            fitto * d.get("opaco", 235), 0, 255).astype(np.uint8)
    pezzi = []
    # i due pezzi si accavallano di un pelo: tagliandoli netti a
    # meta' resta una riga scura in mezzo all'anello
    for alto, fondo in ((0, m + K * 5), (m, L)):
        mezzo = pygame.Surface((L, L), pygame.SRCALPHA)
        mezzo.blit(piano, (0, alto), pygame.Rect(0, alto, L, fondo - alto))
        mezzo = pygame.transform.rotozoom(mezzo, d.get("inclina", 0), 1.0)
        mezzo = pygame.transform.smoothscale(
            mezzo, (max(1, mezzo.get_width() // K),
                    max(1, mezzo.get_height() // K)))
        pezzi.append(mezzo)
    ANELLI_FATTI[chiave] = (pezzi[0], pezzi[1])
    return ANELLI_FATTI[chiave]


CORONE = {
    "nuova": {
        # il sole: la palla piccola in mezzo e tutta la luce intorno
        "sette": {"palla": 0.58, "fuori": 2.55,
                  "dentro": (255, 246, 190), "orlo": (255, 128, 20)},
        # la gigante rossa: stessa luce, ma rossa
        "redgiant": {"palla": 0.58, "fuori": 2.55,
                     "dentro": (255, 186, 146), "orlo": (206, 28, 14)},
    },
}
CORONE_FATTE = {}


def corona_di(nome):
    return CORONE.get(tema(), {}).get(nome)


def con_corona(nome, palla, misura):
    """La luce del sole intorno alla palla: si accende contro il disco e
    si spegne piano andando fuori, con i raggi che si allungano e si
    accorciano tutt'intorno. E' luce, quindi non ha un contorno."""
    d = corona_di(nome)
    if not d:
        return palla
    w, h = misura
    chiave = (tema(), nome, misura)
    if chiave not in CORONE_FATTE:
        try:
            import numpy as np
        except ImportError:
            CORONE_FATTE[chiave] = None
            return palla
        _cx, _cy, R = centro_raggio(palla)
        xx, yy = np.meshgrid(np.arange(w), np.arange(h), indexing="ij")
        X = xx - (w - 1) / 2.0
        Y = yy - (h - 1) / 2.0
        r = np.sqrt(X * X + Y * Y) / max(1.0, R)
        # la luce e' uguale tutt'intorno: un radiale e basta
        luce = np.exp(-((r - 0.96) / 0.70) ** 2)
        luce = np.where(r < 0.96, np.exp(-((r - 0.96) / 0.30) ** 2), luce)
        # deve spegnersi ESATTAMENTE dove finisce la casella, se no
        # resta il quadrato scuro intorno
        bordo = min(w, h) * 0.5 / max(1.0, R)
        luce = np.clip(luce * (1.0 - np.clip((r - 1.0) /
                                             max(0.2, bordo - 1.0), 0, 1))
                       ** 1.35, 0, 1)
        k = np.clip((r - 0.9) / 1.2, 0, 1)[:, :, None]
        rgb = (np.array(d["dentro"], np.float32)[None, None, :] * (1 - k) +
               np.array(d["orlo"], np.float32)[None, None, :] * k)
        sup = pygame.Surface(misura, pygame.SRCALPHA)
        pygame.surfarray.blit_array(
            sup, np.clip(rgb * (0.55 + 0.45 * luce[:, :, None]),
                         0, 255).astype(np.uint8))
        pygame.surfarray.pixels_alpha(sup)[:, :] = np.clip(
            luce * 235, 0, 255).astype(np.uint8)
        CORONE_FATTE[chiave] = sup
    fondo = CORONE_FATTE[chiave]
    if fondo is None:
        return palla
    fuori = pygame.Surface(misura, pygame.SRCALPHA)
    fuori.blit(fondo, (0, 0))
    fuori.blit(palla, palla.get_rect(center=(w // 2, h // 2)))
    return fuori


def con_anello(nome, palla, misura):
    """La palla con l'anello intorno, dentro una casella di quella
    misura: prima il pezzo di dietro, poi la palla, poi quello davanti."""
    _cx, _cy, R = centro_raggio(palla)
    pezzi = anello_pezzi(nome, misura, R)
    if not pezzi:
        return palla
    fuori = pygame.Surface(misura, pygame.SRCALPHA)
    mezzo = (misura[0] // 2, misura[1] // 2)
    fuori.blit(pezzi[0], pezzi[0].get_rect(center=mezzo))
    fuori.blit(palla, palla.get_rect(center=mezzo))
    fuori.blit(pezzi[1], pezzi[1].get_rect(center=mezzo))
    return fuori


PALLA_CON_ANELLO = 0.82     # quanto resta grossa la palla che ha l'anello


def misura_palla(nome, misura):
    """Quanto viene grande la palla quando ha un anello. Si stringe
    appena, non fino a farci stare l'anello: l'anello esce fuori dalla
    misura del simbolo, e va bene, perche' nella casella del rullo c'e'
    aria di avanzo."""
    if not anello_di(nome):
        return misura
    k = PALLA_CON_ANELLO
    return (max(4, int(misura[0] * k)), max(4, int(misura[1] * k)))


def misura_anello(nome, misura):
    """Quanto viene grande tutto insieme, palla piu' anello."""
    d = anello_di(nome)
    if not d:
        return misura
    p = misura_palla(nome, misura)
    k = d["fuori"] * 1.04
    return (max(4, int(p[0] * k)), max(4, int(p[1] * k)))


NEBBIE = {}
QUANTI_NEBBIA = 60


def frames_nebbia(misura, colori=None, quanti=None):
    """La nebulosa: non e' una PNG, si disegna. Tre veli di nebbia che
    scorrono uno sull'altro a velocita' diverse, piu' i punti di luce
    delle stelle dentro. Siccome i veli scorrono e si richiudono su se
    stessi, il giro e' continuo e non si vede dove ricomincia."""
    quanti = quanti or QUANTI_NEBBIA
    chiave = (misura, tuple(colori or ()), quanti)
    if chiave in NEBBIE:
        return NEBBIE[chiave]
    try:
        import numpy as np
    except ImportError:
        NEBBIE[chiave] = None
        return None
    w, h = misura
    colori = colori or ((188, 92, 224), (236, 96, 168), (86, 150, 255))
    rnd = np.random.RandomState(7)
    # ogni velo e' una nuvola di macchie morbide, che si ripete
    # Le macchie si fanno con onde a frequenza intera invece che con
    # chiazze sparse: cosi' il disegno si richiude esattamente su se
    # stesso, e facendolo scorrere non si vede la cucitura.
    yy, xx = np.meshgrid(np.arange(h), np.arange(w))
    veli = []
    for i, col in enumerate(colori):
        g = np.zeros((w, h), np.float32)
        for _ in range(5):
            fx, fy = rnd.randint(1, 4), rnd.randint(1, 4)
            fase = rnd.uniform(0, 2 * math.pi)
            g += rnd.uniform(0.5, 1.0) * np.sin(
                2 * math.pi * (fx * xx / float(w) + fy * yy / float(h)) + fase)
        g = (g - g.min()) / max(1e-6, g.max() - g.min())
        g = g ** 1.9                       # piu' buchi che nuvola
        veli.append((g, np.array(col, np.float32)))
    # la sagoma tonda, sfumata verso il bordo
    yy, xx = np.meshgrid(np.arange(h), np.arange(w))
    rr = np.sqrt(((xx - (w - 1) / 2.0) / (w / 2.0)) ** 2 +
                 ((yy - (h - 1) / 2.0) / (h / 2.0)) ** 2)
    sagoma = np.clip(1.0 - (rr - 0.45) / 0.55, 0.0, 1.0) ** 1.5
    # le stelle
    stelle = np.zeros((w, h), np.float32)
    for _ in range(max(8, w // 5)):
        sx, sy = rnd.randint(0, w), rnd.randint(0, h)
        stelle[sx, sy] = rnd.uniform(0.6, 1.0)
    fuori = []
    for f in range(quanti):
        k = f / float(quanti)
        rgb = np.zeros((w, h, 3), np.float32)
        alfa = np.zeros((w, h), np.float32)
        for i, (g, col) in enumerate(veli):
            sp = int(round(k * w * (1 + i)))          # ognuno a modo suo
            gg = np.roll(g, sp, axis=0)
            gg = np.roll(gg, int(round(k * h * (1 if i == 1 else -1))), axis=1)
            rgb += gg[:, :, None] * col[None, None, :]
            alfa = np.maximum(alfa, gg)
        rgb = np.clip(rgb * 0.85, 0, 255)
        luce = np.roll(stelle, int(round(k * w * 0.4)), axis=0)
        brilla = 0.5 + 0.5 * math.sin(2 * math.pi * (k * 3))
        rgb += (luce * 255 * brilla)[:, :, None]
        alfa = np.clip((alfa * 1.25 + luce) * sagoma, 0, 1) * 255
        sup = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.surfarray.blit_array(sup, np.clip(rgb, 0, 255).astype(np.uint8))
        pygame.surfarray.pixels_alpha(sup)[:, :] = alfa.astype(np.uint8)
        fuori.append(sup)
    NEBBIE[chiave] = fuori
    return fuori


GALASSIE = {}
QUANTI_GALASSIA = 72


def frames_galassia(misura, quanti=None):
    """Una galassia a spirale, tipo Andromeda: disegnata, non scaricata.

    Si lavora nel piano del disco e poi lo si schiaccia, come se lo si
    guardasse di sbieco. I bracci sono una spirale logaritmica: girando
    la spirale di mezzo giro la galassia torna identica a se stessa
    (i bracci sono due), quindi il ciclo si chiude senza salti.
    """
    quanti = quanti or QUANTI_GALASSIA
    chiave = (misura, quanti)
    if chiave in GALASSIE:
        return GALASSIE[chiave]
    try:
        import numpy as np
    except ImportError:
        GALASSIE[chiave] = None
        return None
    w, h = misura
    SCHIACCIA, INCLINA = 0.42, -0.42          # di quanto e' di sbieco
    yy, xx = np.meshgrid(np.arange(h), np.arange(w))
    X = (xx - (w - 1) / 2.0) / (w / 2.0)
    Y = (yy - (h - 1) / 2.0) / (h / 2.0)
    # si torna nel piano del disco: si raddrizza l'inclinazione e si
    # stira la direzione schiacciata
    xr = X * math.cos(-INCLINA) - Y * math.sin(-INCLINA)
    yr = X * math.sin(-INCLINA) + Y * math.cos(-INCLINA)
    u, v = xr, yr / SCHIACCIA
    r = np.sqrt(u * u + v * v) + 1e-4
    th = np.arctan2(v, u)
    dentro = r <= 1.0
    nucleo = np.exp(-(r / 0.10) ** 2)         # il cuore acceso
    bulbo = np.exp(-(r / 0.26) ** 2)          # il rigonfiamento giallo
    alone = np.exp(-(r / 0.40) ** 2) * 0.30
    # la granella di stelle sparse dentro al disco
    rnd = np.random.RandomState(11)
    grana = (rnd.rand(w, h) > 0.985).astype(np.float32) * rnd.rand(w, h)
    # le macchie rosa, a onde intere cosi' girano senza cuciture
    rosa = np.zeros((w, h), np.float32)
    for _ in range(4):
        fx, fy = rnd.randint(1, 4), rnd.randint(1, 4)
        rosa += rnd.uniform(0.4, 1.0) * np.sin(
            2 * math.pi * (fx * xx / float(w) + fy * yy / float(h)) +
            rnd.uniform(0, 6.28))
    rosa = np.clip((rosa - rosa.min()) / max(1e-6, rosa.max() - rosa.min()),
                   0, 1) ** 2.6
    fuori = []
    for f in range(quanti):
        fase = math.pi * f / float(quanti)    # mezzo giro: due bracci
        # spirale logaritmica: l'angolo cresce col logaritmo del raggio
        onda = np.cos(2.0 * (th - 3.3 * np.log(r) + fase))
        bracci = (np.clip(onda, 0, 1) ** 2.6 * np.exp(-r / 0.60) *
                  (r > 0.06))
        # la corsia di polvere: una seconda spirale sfasata che TOGLIE
        # luce invece di darne. E' quella che spezza i bracci e li fa
        # sembrare veri invece che due virgole disegnate
        buio = np.clip(np.cos(2.0 * (th - 3.3 * np.log(r) + fase - 0.40)),
                       0, 1) ** 2.4 * np.exp(-r / 0.58) * 0.80
        # il velo diffuso che riempie fra un braccio e l'altro
        velo = np.exp(-(r / 0.72) ** 2) * 0.20
        d = np.clip(bracci * 1.7 + alone + velo - buio, 0, 1)
        rgb = np.zeros((w, h, 3), np.float32)
        # i bracci azzurri con le stelle rosa dentro, il nucleo caldo
        rgb += (d * (1.0 - bulbo * 0.80))[:, :, None] * np.array(
            [104, 152, 250], np.float32) * 0.94
        # le nubi rosa lungo i bracci: nelle galassie vere sono le zone
        # dove nascono le stelle, ed e' quello che le fa colorate
        nubi = np.roll(rosa, int(round(fase / math.pi * w)), axis=0)
        fiore = np.clip(bracci * 2.2, 0, 1) * nubi
        rgb += fiore[:, :, None] * np.array([150, 224, 255],
                                            np.float32) * 1.70
        rgb += (d ** 3)[:, :, None] * np.array([190, 120, 255],
                                               np.float32) * 0.35
        # l'alone caldo che avvolge tutto il disco
        rgb += (velo * 1.6)[:, :, None] * np.array([120, 90, 190], np.float32)
        # la nebbiolina: un anello di foschia intorno al disco e una
        # velatura piu' stretta fra un braccio e l'altro. E' quella che
        # in Andromeda si vede oltre i bracci: senza, restano due
        # virgole e sembra un disegno
        foschia = (np.exp(-((r - 0.58) / 0.34) ** 2) *
                   (0.22 + 0.40 * np.clip(onda, 0, 1)))
        rgb += (foschia[:, :, None] *
                np.array([104, 170, 255], np.float32) * 0.70)
        celeste = (np.exp(-(r / 0.66) ** 2) *
                   np.clip(0.90 - bracci, 0, 1) * 0.42)
        rgb += celeste[:, :, None] * np.array([120, 205, 255], np.float32)
        # la granella di stelle, che gira insieme al disco
        gr = np.roll(grana, int(round(fase / math.pi * w)), axis=0)
        stelline = gr * np.clip(d * 1.6, 0, 1)
        rgb += stelline[:, :, None] * np.array([235, 245, 255], np.float32)
        rgb += (nucleo[:, :, None] *
                np.array([255, 224, 158], np.float32) * 0.90)
        rgb += (bulbo[:, :, None] *
                np.array([255, 202, 120], np.float32) * 0.86)
        alfa = np.clip(d * 1.7 + nucleo * 1.9 + bulbo * 1.15 +
                       stelline + fiore * 0.8 +
                       foschia * 0.58 + celeste * 0.50, 0, 1) * dentro
        # il bordo che sfuma, se no si vede il cerchio netto
        alfa *= np.clip((1.0 - r) / 0.28, 0, 1)
        sup = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.surfarray.blit_array(sup, np.clip(rgb, 0, 255).astype(np.uint8))
        pygame.surfarray.pixels_alpha(sup)[:, :] = (alfa * 255).astype(np.uint8)
        fuori.append(sup)
    GALASSIE[chiave] = fuori
    return fuori


TARGHE = {}
QUANTI_TARGA = 48


def frames_targa(nome, misura, colori=None, quanti=None):
    """Le scritte, SPACE e JACKPOT: la scritta sta ferma com'e', si
    muove soltanto la nebbia che le sta dietro."""
    quanti = quanti or QUANTI_TARGA
    chiave = (tema(), nome, misura, quanti)
    if chiave in TARGHE:
        return TARGHE[chiave]
    TARGHE[chiave] = None
    w, h = misura
    neb = frames_nebbia((max(4, int(w * 0.98)), max(4, int(h * 0.58))),
                        colori, quanti)
    if not neb:
        return None
    parola = figura_nuda(nome, misura)
    fuori = []
    for f in neb:
        sup = pygame.Surface((w, h), pygame.SRCALPHA)
        q = f.copy()
        q.fill((255, 255, 255, 165), special_flags=pygame.BLEND_RGBA_MULT)
        sup.blit(q, q.get_rect(center=(w // 2, h // 2)))
        sup.blit(parola, parola.get_rect(center=(w // 2, h // 2)))
        fuori.append(sup)
    TARGHE[chiave] = fuori
    return fuori


PEZZI = {}
ALIENI = {}
QUANTI_ALIENO = 48


def pezzi_faccia(nome):
    """Dove stanno le pupille e la bocca dentro al disegno, in frazione.
    Si guarda una volta sola. E' roba disegnata a tinte piatte: la tinta
    piu' usata e' il corpo, e le altre due sono l'occhio e la pupilla -
    ma non si sa quale delle due e' quale, dipende dal disegno. Allora si
    provano tutt'e due nei due versi e si tiene quella dove la pupilla
    sta DENTRO all'occhio. Se non torna, niente animazione."""
    if nome in PEZZI:
        return PEZZI[nome]
    PEZZI[nome] = None
    try:
        import numpy as np
    except ImportError:
        return None
    base = figura_nuda(nome, (512, 512))
    w, h = base.get_size()
    rgb = pygame.surfarray.array3d(base).astype("int16")
    alf = pygame.surfarray.array_alpha(base)
    pieno = alf > 100
    if pieno.sum() < 400:
        return None
    tinte, quante = np.unique(rgb[pieno].reshape(-1, 3), axis=0,
                              return_counts=True)
    ordine = np.argsort(-quante)[:3]
    if len(ordine) < 3:
        return None
    corpo = tinte[ordine[0]]
    due = [tinte[ordine[1]], tinte[ordine[2]]]

    def come(c, quanto=70):
        return (np.abs(rgb - c.astype("int16")).sum(2) < quanto) & pieno

    def riquadro(m):
        xs, ys = np.where(m)
        if len(xs) < 12:
            return None
        return pygame.Rect(int(xs.min()), int(ys.min()),
                           int(xs.max() - xs.min() + 1),
                           int(ys.max() - ys.min() + 1))

    def prova(c_occhio, c_pupilla):
        """Gli occhi sono due, uno per parte, e dentro ci sta la pupilla,
        che e' piu' piccola e non tocca i bordi."""
        m_o, m_p = come(c_occhio), come(c_pupilla)
        alto = np.zeros_like(m_o)
        alto[:, :int(h * 0.72)] = m_o[:, :int(h * 0.72)]
        fuori = []
        for lato in (slice(0, w // 2), slice(w // 2, w)):
            m = np.zeros_like(alto)
            m[lato] = alto[lato]
            occhio = riquadro(m)
            if occhio is None or occhio.w < w * 0.06:
                return None
            # un occhio e' un pezzo raccolto: se il riquadro e' mezza
            # faccia, quella tinta e' dell'altra roba (le corna, l'ombra)
            if occhio.w > w * 0.42 or occhio.h > h * 0.42:
                return None
            d = np.zeros_like(m_p)
            d[occhio.x:occhio.right, occhio.y:occhio.bottom] = \
                m_p[occhio.x:occhio.right, occhio.y:occhio.bottom]
            pup = riquadro(d)
            if pup is None:
                return None
            if pup.w >= occhio.w * 0.92 or pup.h >= occhio.h * 0.92:
                return None            # non e' dentro: e' lo stesso pezzo
            if pup.w * pup.h < occhio.w * occhio.h * 0.015:
                return None            # troppo piccola: e' un riflesso
            fuori.append((pup, occhio))
        # gli occhi sono due e stanno alla stessa altezza, uno per parte
        (p1, o1), (p2, o2) = fuori
        if abs(o1.centery - o2.centery) > h * 0.12:
            return None
        if min(o1.w, o2.w) < max(o1.w, o2.w) * 0.60:
            return None
        return fuori

    tondi = prova(due[0], due[1])
    scuro = due[1]
    if tondi is None:
        tondi = prova(due[1], due[0])
        scuro = due[0]
        due = [due[1], due[0]]
    if tondi is None:
        return None
    # la bocca: lo scuro che sta sotto, ma solo se e' un pezzo raccolto
    # in mezzo alla faccia. Un alieno senza bocca non ne ha bisogno
    m_s = come(scuro)
    giu = np.zeros_like(m_s)
    taglio = int(h * 0.45)
    giu[:, taglio:] = m_s[:, taglio:]
    for pup, occhio in tondi:
        giu[occhio.x:occhio.right, occhio.y:occhio.bottom] = False
    bocca = riquadro(giu)
    if bocca is not None:
        largo_ok = bocca.w < w * 0.50 and bocca.h < h * 0.30
        centro_ok = abs(bocca.centerx - w * 0.5) < w * 0.18
        if not (largo_ok and centro_ok):
            bocca = None

    def frazione(r):
        return (r.x / float(w), r.y / float(h),
                r.w / float(w), r.h / float(h))

    PEZZI[nome] = ([(frazione(p), frazione(o)) for p, o in tondi],
                   frazione(bocca) if bocca else None,
                   tuple(int(v) for v in due[0]),
                   tuple(int(v) for v in corpo),
                   tuple(int(v) for v in due[1]))
    return PEZZI[nome]


def sguardo(k):
    """Guarda da una parte, ci resta un momento buono, poi passa
    dall'altra. Le due punte sono addolcite, cosi' non parte di scatto."""
    fermo, passo = 0.34, 0.16
    if k < fermo:
        return 1.0
    if k < fermo + passo:
        u = (k - fermo) / passo
        return 1.0 - 2.0 * (u * u * (3.0 - 2.0 * u))
    if k < 2 * fermo + passo:
        return -1.0
    u = min(1.0, (k - 2 * fermo - passo) / passo)
    return -1.0 + 2.0 * (u * u * (3.0 - 2.0 * u))


def frames_alieno(nome, misura, quanti=None):
    """L'alieno che guarda a destra e a sinistra.

    La pupilla non si ritaglia e si riattacca: si lavora sulle maschere.
    Si sa quali pixel sono pupilla e quali sono il bianco dell'occhio; si
    ridipinge di bianco dove stava la pupilla e la si ridipinge spostata,
    ma SOLO dentro all'occhio. Cosi' l'occhio tiene la sua forma, anche
    storta o arrabbiata, e la pupilla non scappa mai sulla faccia: quando
    arriva al bordo si taglia da sola, come succede davvero."""
    p = pezzi_faccia(nome)
    if not p:
        return None
    try:
        import numpy as np
    except ImportError:
        return None
    quanti = quanti or QUANTI_ALIENO
    chiave = (tema(), nome, misura, quanti)
    if chiave in ALIENI:
        return ALIENI[chiave]
    occhi, bocca, c_occhio, c_corpo, c_pupilla = p
    base = figura_nuda(nome, misura)
    w, h = base.get_size()
    rgb = pygame.surfarray.array3d(base)

    def rett(fr):
        return pygame.Rect(int(fr[0] * w), int(fr[1] * h),
                           max(1, int(round(fr[2] * w))),
                           max(1, int(round(fr[3] * h))))

    zone = []
    for fr_p, fr_o in occhi:
        ro = rett(fr_o).inflate(2, 2).clip(base.get_rect())
        if ro.w < 3 or ro.h < 3:
            continue
        pezzo = rgb[ro.x:ro.right, ro.y:ro.bottom].astype("int16")
        m_pup = (np.abs(pezzo - np.array(c_pupilla, "int16")).sum(2) < 110)
        m_occ = (np.abs(pezzo - np.array(c_occhio, "int16")).sum(2) < 110)
        if m_pup.sum() < 4:
            continue
        fondo = pezzo.copy()
        fondo[m_pup] = np.array(c_occhio, "int16")
        zone.append((ro, m_pup, m_pup | m_occ, fondo))
    if not zone:
        ALIENI[chiave] = None
        return None
    fuori = []
    for f in range(quanti):
        k = f / float(quanti)
        sup = base.copy()
        sx = sguardo(k)
        vista = pygame.surfarray.pixels3d(sup)
        for ro, m_pup, dentro, fondo in zone:
            d = int(round(sx * max(1.0, ro.w * 0.17)))
            mossa = np.zeros_like(m_pup)
            if d == 0:
                mossa = m_pup.copy()
            elif d > 0:
                mossa[d:, :] = m_pup[:-d, :]
            else:
                mossa[:d, :] = m_pup[-d:, :]
            mossa &= dentro
            nuovo = fondo.copy()
            nuovo[mossa] = np.array(c_pupilla, "int16")
            vista[ro.x:ro.right, ro.y:ro.bottom] = nuovo.astype("uint8")
        del vista
        if bocca:
            rb = rett(bocca)
            if rb.w >= 2 and rb.h >= 1:
                apre = 1.0 + 0.55 * (0.5 - 0.5 * math.cos(6 * math.pi * k))
                pez = sup.subsurface(rb).copy()
                pygame.draw.ellipse(sup, c_corpo, rb.inflate(3, 3))
                pez = pygame.transform.smoothscale(
                    pez, (rb.w, max(1, int(round(rb.h * apre)))))
                sup.blit(pez, (rb.x, rb.y))
        fuori.append(sup)
    ALIENI[chiave] = fuori
    return fuori


PLEIADI = {}
QUANTI_PLEIADI = 60
# dove stanno le sette sorelle, piu' o meno come in cielo
SETTE = ((0.50, 0.26, 1.00), (0.34, 0.40, 0.82), (0.62, 0.44, 0.74),
         (0.24, 0.60, 0.66), (0.46, 0.62, 0.90), (0.70, 0.68, 0.58),
         (0.40, 0.80, 0.52))


def frames_pleiadi(misura, quanti=None):
    """Le Pleiadi: sette stelle azzurre dentro un velo di nebbia, che
    scintillano ognuna per conto suo. Anche questa e' disegnata."""
    quanti = quanti or QUANTI_PLEIADI
    chiave = (misura, quanti)
    if chiave in PLEIADI:
        return PLEIADI[chiave]
    try:
        import numpy as np
    except ImportError:
        PLEIADI[chiave] = None
        return None
    w, h = misura
    yy, xx = np.meshgrid(np.arange(h), np.arange(w))
    X = xx / float(w)
    Y = yy / float(h)
    rr = np.sqrt((X - 0.5) ** 2 + (Y - 0.5) ** 2) * 2.0
    sagoma = np.clip(1.0 - (rr - 0.5) / 0.5, 0, 1) ** 1.3
    # il velo di nebbia, a onde intere cosi' scorre senza cuciture
    rnd = np.random.RandomState(3)
    velo = np.zeros((w, h), np.float32)
    for _ in range(4):
        fx, fy = rnd.randint(1, 3), rnd.randint(1, 3)
        velo += rnd.uniform(0.5, 1.0) * np.sin(
            2 * math.pi * (fx * X + fy * Y) + rnd.uniform(0, 6.28))
    velo = (velo - velo.min()) / max(1e-6, velo.max() - velo.min())
    velo = velo ** 2.0
    fuori = []
    for f in range(quanti):
        k = f / float(quanti)
        rgb = np.zeros((w, h, 3), np.float32)
        alfa = np.zeros((w, h), np.float32)
        nb = np.roll(velo, int(round(k * w)), axis=0) * 0.5
        rgb += nb[:, :, None] * np.array([70, 120, 245], np.float32) * 1.8
        alfa = np.maximum(alfa, nb * 1.5)
        for i, (sx, sy, forza) in enumerate(SETTE):
            b = 0.55 + 0.45 * math.sin(2 * math.pi * (k * (2 + i % 3)) + i)
            d2 = ((X - sx) ** 2 + (Y - sy) ** 2)
            g = np.exp(-d2 / (0.0024 * forza)) * forza * b
            # le quattro punte
            croce = (np.exp(-((X - sx) ** 2) / 0.00018) *
                     np.exp(-((Y - sy) ** 2) / 0.010) +
                     np.exp(-((Y - sy) ** 2) / 0.00018) *
                     np.exp(-((X - sx) ** 2) / 0.010)) * forza * b * 0.7
            luce = g + croce
            rgb += luce[:, :, None] * np.array([190, 220, 255], np.float32)
            alfa = np.maximum(alfa, np.clip(luce, 0, 1))
        alfa = np.clip(alfa, 0, 1) * sagoma
        sup = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.surfarray.blit_array(sup, np.clip(rgb, 0, 255).astype(np.uint8))
        pygame.surfarray.pixels_alpha(sup)[:, :] = (alfa * 255).astype(np.uint8)
        fuori.append(sup)
    PLEIADI[chiave] = fuori
    return fuori


GIRI = {}
# Quanti fotogrammi fanno un giro completo. Tanti: il pianeta gira piano,
# e con pochi fotogrammi si vedrebbe scattare.
QUANTI_GIRO = 120
DENTRO = 0.84               # da quanto dentro il disco si pesca il colore


def frames_giro(nome, misura):
    """I fotogrammi di un pianeta che gira sul proprio asse.

    Il trucco sta nella geometria: ruotando attorno all'asse verticale
    un punto non cambia altezza, cambia solo la longitudine. Quindi ogni
    riga dell'immagine e' una fetta di pianeta a quella latitudine, che
    scorre, e le righe non si mescolano mai fra loro. Il lato nascosto
    non esiste nel disegno, quindi si specchia quello che si vede: su
    pianeti a fasce e a macchie non si nota.

    Si calcolano una volta sola per simbolo e misura, e si tengono da
    parte. Senza numpy si rinuncia e il simbolo respira come prima.
    """
    chiave = (tema(), nome, misura)
    if chiave in GIRI:
        return GIRI[chiave]
    try:
        import numpy as np
    except ImportError:
        GIRI[chiave] = None
        return None
    # se ha l'anello la palla e' piu' piccola della casella: si fanno i
    # fotogrammi della palla e l'anello si rimette sopra alla fine
    src = figura_nuda(nome, misura_palla(nome, misura))
    w, h = src.get_size()
    try:
        rgb = pygame.surfarray.array3d(src).astype(np.float32)
        alfa = pygame.surfarray.array_alpha(src).astype(np.float32)
    except (ValueError, pygame.error):
        GIRI[chiave] = None
        return None
    # centro e raggio si prendono dal DISEGNO, non dal bordo del file:
    # certe PNG hanno il pianeta piccolo in mezzo al vuoto, e pescando
    # fino al bordo si finiva fuori dalla palla -- il pianeta diventava
    # nero a meta' giro
    col = np.where(alfa.max(axis=1) > 8)[0]
    rig = np.where(alfa.max(axis=0) > 8)[0]
    if len(col) and len(rig):
        cx = (col[0] + col[-1]) / 2.0
        cy = (rig[0] + rig[-1]) / 2.0
        R = max(col[-1] - col[0], rig[-1] - rig[0]) / 2.0 + 0.5
    else:
        cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
        R = min(cx, cy) + 0.5
    xs = (np.arange(w) - cx) / R                 # -1..1 sullo schermo
    ys = (np.arange(h) - cy) / R
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    dentro = (X * X + Y * Y) <= 1.0
    cosphi = np.sqrt(np.clip(1.0 - Y * Y, 1e-6, 1.0))   # quanto e' larga
    lon = np.arcsin(np.clip(X / cosphi, -1.0, 1.0))     # la riga a quella
                                                        # latitudine

    # --- la striscia dei 360 gradi.
    # Il disegno mostra mezzo pianeta: il lato nascosto non esiste.
    # Prima lo specchiavo, e si vedeva -- meta' pianeta appariva
    # ribaltata, con una cucitura netta in mezzo. Adesso il disegno si
    # STENDE su tutto il giro, mezzo grado di disegno per ogni grado di
    # pianeta: niente specchio, niente meta' al rovescio, e il pianeta
    # gira sempre nello stesso verso. Si pesca dall'84% del raggio in
    # dentro, se no il contorno scuro della PNG finirebbe in mezzo.
    N_TEX = 2 * QUANTI_GIRO
    theta = (np.arange(N_TEX) / float(N_TEX) * 2.0 - 1.0) * math.pi
    cos_riga = np.sqrt(np.clip(1.0 - ys * ys, 1e-6, 1.0))        # (h,)
    sx = np.clip(np.rint(cx + R * DENTRO *
                         np.outer(np.sin(theta * 0.5), cos_riga)),
                 0, w - 1).astype(int)                           # (N_TEX,h)
    sy = np.clip(np.rint(cy + (np.arange(h) - cy) * DENTRO),
                 0, h - 1).astype(int)                           # (h,)
    tex = rgb[sx, sy[None, :]]                                   # (N_TEX,h,3)

    # La striscia si richiude su se stessa, e li' i due capi non
    # combaciano: passando da quel punto si vedeva uno scatto, come se
    # l'animazione ricominciasse da capo. Su una fetta di giro i due
    # capi si sfumano l'uno nell'altro, cosi' il giro e' continuo e la
    # giuntura passa come una velatura morbida invece che come un salto.
    banda = max(4, N_TEX // 7)
    peso = (0.5 - 0.5 * np.cos(np.pi * np.arange(banda) / (banda - 1.0)))
    peso = peso[:, None, None]
    coda = tex[N_TEX - banda:].copy()        # l'ultimo pezzo del giro
    testa = tex[:banda].copy()               # e il primo
    tex[N_TEX - banda:] = coda * (1.0 - peso * 0.5) + testa * (peso * 0.5)
    tex[:banda] = testa * (0.5 + peso * 0.5) + coda * (0.5 - peso * 0.5)

    # la luce sta ferma: viene da sopra a sinistra e non gira col pianeta
    Z = np.sqrt(np.clip(1.0 - X * X - Y * Y, 0.0, 1.0))
    luce = 0.58 + 0.52 * np.clip(-0.42 * X - 0.42 * Y + 0.76 * Z, 0.0, 1.0)
    luce = luce[:, :, None]
    # la sagoma resta quella del disegno originale: bordo netto
    maschera = (alfa * dentro).astype(np.uint8)
    righe = np.arange(h)[None, :]

    fuori = []
    for i in range(QUANTI_GIRO):
        fase = 2.0 * math.pi * i / QUANTI_GIRO
        lt = (lon + fase + math.pi) % (2.0 * math.pi) - math.pi
        j = np.mod(np.rint((lt / (2.0 * math.pi) + 0.5) * N_TEX
                           ).astype(int), N_TEX)
        q = np.clip(tex[j, righe] * luce, 0, 255)
        sup = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.surfarray.blit_array(sup, q.astype(np.uint8))
        pygame.surfarray.pixels_alpha(sup)[:, :] = maschera
        # l'anello si rimette sopra a giro fatto: sta fermo mentre la
        # palla ruota sotto, che e' il punto di tutta la faccenda
        if anello_di(nome):
            sup = con_anello(nome, sup, misura_anello(nome, misura))
        fuori.append(sup)
    GIRI[chiave] = fuori
    return fuori

# quanto e' grande la griglia rispetto allo spazio che avrebbe: 1.0 la
# riempie tutta, 0.5 la fa meta'. Un numero solo, si cambia qui.
MISURA = 0.75


class Macchina:
    """La slot sullo schermo: la cassa, i sei rulli e quello che
    succede a ogni giro."""

    def __init__(self, sc, clock):
        self.sc, self.clock = sc, clock
        self.dt = 0.0
        self.strisce = strisce()
        self.pos = [float(random.randrange(len(s))) for s in self.strisce]
        self.da, self.a, self.t, self.durata = None, None, None, None
        self.griglia = self.ferma()
        self.vinte, self.mostra, self.t_mostra = [], -1, 0.0
        self.storico = []       # le ultime vincite, a sinistra
        self.polvere = []       # la polvere sui simboli che pagano
        self.scia = []          # la scia dei simboli che si muovono
        self.t_vinta = 0.0      # per far respirare i simboli vincenti
        self.sotto = ""         # la riga piccola sotto il totale
        self.totale = 0         # quanto ha pagato tutto il giro
        self.gratis = 0         # i giri gratis che restano
        self.lampo = 0.0        # quanto dura il lampo del jackpot vinto
        self.t_neon = 0.0       # il colore che gira nella cornice
        self.t_luci = 0.0       # le lampadine, che corrono se si vince
        self.msg = ""
        self.vinto = 0
        self.gira = False
        # la cassa: a sinistra il vetro coi rulli, a destra la fascia
        # delle scelte, come al tavolo da carte
        largo = B.WIN_W - B.s(300)
        posto = pygame.Rect(B.s(40), B.ALTO + B.s(70),
                            largo - B.s(60),
                            B.WIN_H - B.ALTO - B.s(200))
        m = B.s(22)      # la fascia intorno al vetro, dove stanno i LED
        # le caselle restano quadrate: si prende il lato piu' grande che
        # ci sta sia in larghezza sia in altezza e il vetro si stringe
        # intorno ai rulli, cosi' con sei colonne non restano vuoti
        lato = int(min((posto.w - m * 2) // COLONNE,
                       (posto.h - m * 2) // RIGHE) * MISURA)
        self.cassa = pygame.Rect(0, 0, lato * COLONNE + m * 2,
                                 lato * RIGHE + m * 2)
        self.cassa.center = (B.WIN_W // 2, posto.centery)
        self.vetro = self.cassa.inflate(-m * 2, -m * 2)
        self.cella = (lato, lato)
        # la fascia delle scelte resta al suo posto a destra, non segue
        # la cassa quando la griglia si stringe
        self.fascia = posto.right

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
        del self.polvere[:]
        del self.scia[:]
        griglia, fermi = tira(self.strisce)
        self.griglia = griglia
        self.da = list(self.pos)
        self.a = []
        for c, p in enumerate(fermi):
            s = len(self.strisce[c])
            giri = 4 + c
            avanti = (p - self.da[c]) % s
            self.a.append(self.da[c] + giri * s + avanti)
        # l'ultimo rullo si ferma esattamente quando il suono del giro
        # smette di sentirsi, non quando finisce il file: in fondo a
        # spin.ogg c'e' quasi un secondo di silenzio, e fermarsi li'
        # dentro sembrava fuori tempo. Gli altri arrivano prima, a
        # distanza uguale fra loro
        giro = quanto_suona("spin", 2.0)
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
                    # l'ultimo rullo si ferma zitto: nello stesso
                    # istante parte il suono della vincita (o del
                    # niente), e i due insieme sembravano un colpo di
                    # troppo in fondo al giro
                    if c < COLONNE - 1:
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
        if tema() not in SENZA_LUCI:
            self.lampadine()
        self.disegna_jackpot()
        self.disegna_rulli()
        self.disegna_sotto()
        self.disegna_scelte(voci, sel)
        self.disegna_pannello(per_linea)
        self.disegna_ultime()
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
        # il cielo sta in mezzo: sopra al fondo dei rulli, sotto ai simboli
        if tema() in COL_CIELO:
            disegna_cielo(sc, vetro, self.t_neon)
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
            velo.fill((246, 241, 228, 170) if RULLI_CHIARI
                      else (14, 13, 20, 185))
            sc.blit(velo, vetro)
            # la scia va SOPRA al velo e sotto ai simboli: messa prima,
            # il velo se la mangiava e non si vedeva niente
            self.disegna_scia()
            respiro = 0.5 + 0.5 * math.sin(self.t_vinta * 7.0)
            k = 1.0 + 0.12 * respiro
            nome_v = self.vinte[self.mostra][0] if self.vinte else None
            col = tuple(colore_simbolo(nome_v)) if nome_v else \
                COLORI_VINTE[self.mostra % len(COLORI_VINTE)]
            for c, i in sorted(acceso):
                if not 0 <= i < RIGHE:
                    continue
                nome = self.griglia[c][i]
                r = pygame.Rect(vetro.x + c * cw, vetro.y + i * ch, cw, ch)
                # l'alone si misura sul simbolo, non sulla casella:
                # cosi' se le icone cambiano misura lui le segue
                an = animazione(nome)
                # chi ha un'animazione sua non pulsa e non sfuma: quella
                # animazione E' il suo modo di festeggiare, e pulsare in
                # piu' sarebbe due cose sopra la stessa casella
                suo = bool(an)
                # l'alone dietro: certi simboli non lo vogliono, perche'
                # sono gia' larghi e chiari di loro e lui li impasta
                if (an or {}).get("alone", True):
                    al = alone_radiale(int(min(cw, ch) * GRANDE * 1.73), col)
                    al = al.copy()
                    al.fill((255, 255, 255,
                             225 if suo else int(150 + 105 * respiro)),
                            special_flags=pygame.BLEND_RGBA_MULT)
                    sc.blit(al, al.get_rect(center=r.center))
                # l'alfa si moltiplica sui pixel: set_alpha su una
                # superficie trasparente farebbe un quadrato nero
                if suo:
                    img, (dx, dy) = self.icona_viva(
                        nome, (int(cw * GRANDE), int(ch * GRANDE)),
                        c * 1.7 + i * 2.3)
                else:
                    img = figura(nome, (int(cw * GRANDE * k),
                                        int(ch * GRANDE * k))).copy()
                    img.fill((255, 255, 255, int(165 + 90 * respiro)),
                             special_flags=pygame.BLEND_RGBA_MULT)
                    dx = dy = 0.0
                sc.blit(img, img.get_rect(
                    center=(int(r.centerx + dx), int(r.centery + dy))))
        if not (acceso and not self.gira):
            self.disegna_scia()
        self.disegna_polvere()
        sc.set_clip(vecchio)
        riga = separatore(vetro.h)
        for c in range(1, COLONNE):
            sc.blit(riga, (int(vetro.x + c * cw - riga.get_width() * 0.5),
                           vetro.y))

    def polvere_passo(self):
        """La polvere sui simboli che stanno pagando: nasce dalle
        caselle accese, sale svolazzando e si spegne da sola."""
        vive = []
        for p in self.polvere:
            p[4] += self.dt
            if p[4] >= p[5]:
                continue
            p[2] += math.sin(p[8] + p[4] * 3.4) * B.s(50) * self.dt
            p[2] *= 0.985
            p[3] += B.s(22) * self.dt      # sale e rallenta
            p[0] += p[2] * self.dt
            p[1] += p[3] * self.dt
            vive.append(p)
        self.polvere = vive
        # La polvere generica sui simboli vincenti non si fa piu': ogni
        # simbolo ha la sua animazione, e chi deve lasciare qualcosa
        # dietro (la cometa) ha la sua scia. Quella che e' gia' in aria
        # finisce di spegnersi da sola.
        return

    def scosta(self, nome, c, i):
        """Di quanto si e' spostato dal suo posto un simbolo vivo. Ogni
        casella ha la sua fase, se no si muovono tutti insieme come un
        banco di pesci."""
        an = animazione(nome)
        if not an or self.gira:
            return 0.0, 0.0
        cw, ch = self.cella
        fase = c * 1.7 + i * 2.3
        tt = self.t_neon * VELOCITA
        onda = an.get("onda", 0.0)
        largo, alto = cw * GRANDE, ch * GRANDE
        return (math.cos(tt * 1.15 + fase) * largo * onda,
                math.sin(tt * 1.70 + fase) * alto * onda)

    def semina(self, nome, centro, misura, fase=0.0):
        """Butta fuori qualche granello di scia da quel simbolo, se ne
        ha una. Vuole il centro sullo schermo e quanto e' grande, cosi'
        funziona dovunque il simbolo sia disegnato: sui rulli, nella
        lista a sinistra, nella pagina di prova."""
        an = animazione(nome)
        if not an or not an.get("scia") or len(self.scia) >= 260:
            return
        if random.random() > an["scia"] * self.dt:
            return
        vx, vy = an.get("verso", (-1.0, 0.0))
        v = misura[0] * random.uniform(0.6, 1.5)
        sp = an.get("sparso", 0.16)
        self.scia.append([
            centro[0] + random.uniform(-sp, sp) * misura[0],
            centro[1] + random.uniform(-sp, sp) * misura[1],
            vx * v + random.uniform(-0.2, 0.2) * misura[0],
            vy * v + random.uniform(-0.2, 0.2) * misura[1],
            0.0, random.uniform(0.5, 1.2),
            random.choice((0.45, 0.65, 0.9)) * misura[0] / float(B.s(41)),
            an.get("colore", (200, 220, 255)),
            random.uniform(0.0, 6.28),
            bool(an.get("pixel"))])

    def scia_passo(self):
        """La scia: si muove, rallenta e si spegne. I granelli nuovi li
        chiede semina(), da dove serve."""
        vive = []
        for p in self.scia:
            p[4] += self.dt
            if p[4] >= p[5]:
                continue
            p[0] += p[2] * self.dt
            p[1] += p[3] * self.dt
            p[2] *= 0.99
            p[3] *= 0.99
            vive.append(p)
        self.scia = vive
        # sui rulli nasce dalle caselle che stanno pagando, a rulli fermi
        if self.gira or not (0 <= self.mostra < len(self.vinte)):
            return
        cw, ch = self.cella
        for c, i in self.vinte[self.mostra][4]:
            if not 0 <= i < RIGHE:
                continue
            nome = self.griglia[c][i]
            dx, dy = self.scosta(nome, c, i)
            self.semina(nome,
                        (self.vetro.x + (c + 0.5) * cw + dx,
                         self.vetro.y + (i + 0.5) * ch + dy),
                        (cw * GRANDE, ch * GRANDE))

    def disegna_scia(self):
        """I granelli della scia, sotto ai simboli."""
        for x, y, _vx, _vy, vita, durata, grande, col, fase, fine \
                in self.scia:
            vivo = math.sin(math.pi * vita / durata) ** 0.8
            luce = 0.55 + 0.45 * math.sin(fase + vita * 9.0)
            forza = vivo * luce
            if forza < 0.05:
                continue
            if fine:
                # pixellini e basta: nessun alone, se no coprono tutto
                lato = max(1, int(B.s(1.7) * grande))
                self.sc.fill(tuple(int(c * forza) for c in col),
                             (int(x), int(y), lato, lato),
                             special_flags=pygame.BLEND_RGB_ADD)
                continue
            q = granello(max(3, int(B.s(12) * grande)), col, forza)
            self.sc.blit(q, q.get_rect(center=(int(x), int(y))),
                         special_flags=pygame.BLEND_RGB_ADD)

    def disegna_polvere(self):
        """I granelli, sommati alla luce di sotto: brillano perche' la
        forza va e viene mentre salgono."""
        for x, y, _vx, _vy, vita, durata, grande, col, fase in self.polvere:
            k = vita / durata
            vivo = math.sin(math.pi * k) ** 0.7
            luce = 0.5 + 0.5 * math.sin(fase + vita * 12.0)
            forza = vivo * (0.35 + 0.65 * luce)
            if forza < 0.06:
                continue
            lato = max(3, int(B.s(9) * grande))
            q = granello(lato, col, forza)
            self.sc.blit(q, q.get_rect(center=(int(x), int(y))),
                         special_flags=pygame.BLEND_RGB_ADD)

    def icona_viva(self, nome, misura, fase=0.0):
        """Il simbolo come si vede adesso, con la sua animazione gia'
        applicata, e di quanto si e' spostato dal suo posto. Vale
        dovunque: sui rulli, nella lista a sinistra, nella pagina di
        prova. Chi non ha un'animazione torna com'e'."""
        an = animazione(nome)
        if not an:
            return figura(nome, misura), (0.0, 0.0)
        tt = self.t_neon * VELOCITA
        img = None
        grande = misura_simbolo(nome, misura)
        fr = frames_disegnati(nome, grande)
        if fr:
            quanto = (an.get("galassia") or an.get("pleiadi")
                      or an.get("nebbia") or an.get("alieno")
                      or an.get("targa"))
            img = fotogramma(fr, tt * quanto * len(fr))
        elif an.get("gira"):
            fr = frames_giro(nome, grande)
            if fr:
                passo = tt * an["gira"] * len(fr)
                # chi gira svelto ha gia' piu' fotogrammi di quanti se ne
                # vedano: e' chi gira piano che va sfumato
                veloci = abs(an["gira"]) * len(fr) * VELOCITA
                img = (fr[int(passo) % len(fr)] if veloci >= 60.0
                       else fotogramma(fr, passo))
        if img is None:
            img = figura(nome, misura)
        # il capitombolo: gira nel suo piano, in senso antiorario,
        # come uno che galleggia e non ha niente a cui appoggiarsi
        if an.get("rotola"):
            img = pygame.transform.rotozoom(
                img, (tt * an["rotola"] * 360.0) % 360.0, 1.0)
        # la moneta gira di taglio: si schiaccia e si riapre
        if an.get("moneta"):
            k = abs(math.cos(tt * an["moneta"] * math.pi))
            larga = max(2, int(img.get_width() * max(0.10, k)))
            img = pygame.transform.smoothscale(img,
                                               (larga, img.get_height()))
        # il battito: si allarga e si stringe tutto insieme
        if an.get("batte"):
            k = 1.0 + an["batte"] * (0.5 + 0.5 * math.sin(tt * 5.0 + fase))
            img = pygame.transform.smoothscale(
                img, (max(2, int(img.get_width() * k)),
                      max(2, int(img.get_height() * k))))
        # il lampo: si accende e si spegne
        if an.get("lampo"):
            v = 1.0 - an["lampo"] * (0.5 + 0.5 * math.sin(tt * 6.0 + fase))
            q = int(max(0, min(255, 255 * v)))
            img = img.copy()
            img.fill((255, 255, 255, q), special_flags=pygame.BLEND_RGBA_MULT)
        # la fiamma del razzo: la spinta dietro
        if an.get("fiamma"):
            img = con_fiamma(img, an["fiamma"], tt, fase)
        dx = dy = 0.0
        onda = an.get("onda", 0.0)
        if onda:
            dx += math.cos(tt * 1.15 + fase) * misura[0] * onda
            dy += math.sin(tt * 1.70 + fase) * misura[1] * onda
        # il tremolio: scatti piccoli e veloci, come i dadi che ballano
        tr = an.get("trema", 0.0)
        if tr:
            dx += math.sin(tt * 23.0 + fase * 3) * misura[0] * tr
            dy += math.cos(tt * 19.0 + fase * 5) * misura[1] * tr
        # il mezzo pixel: lo spostamento intero va alla cornice, quello
        # che avanza si disegna dentro al simbolo. Senza, chi si muove
        # piano scatta da un pixel all'altro
        if dx or dy:
            ix, iy = math.floor(dx), math.floor(dy)
            img = sposta_fine(img, dx - ix, dy - iy)
            dx, dy = float(ix), float(iy)
        return img, (dx, dy)

    def disegna_ultime(self):
        """A sinistra, come alla roulette: le ultime vincite, ognuna col
        suo simbolo e col suo colore."""
        if not self.storico:
            return
        f, mini = B.FONTS["small"], B.FONTS.get("mini", B.FONTS["small"])
        x0 = B.s(28)
        # la colonna arriva fin sotto la cassa, ma senza toccarla
        largo = max(B.s(168), min(B.s(320), self.cassa.x - x0 - B.s(20)))
        y = B.ALTO + B.s(40)
        t = f.render(T("last_wins"), True, (150, 156, 168))
        self.sc.blit(t, (x0, y))
        y += t.get_height() + B.s(10)
        lato = B.s(26)
        for nome, lung, paga in self.storico[:10]:
            mezzo = y + lato // 2
            img, (dx, dy) = self.icona_viva(nome, (lato, lato), y * 0.03)
            self.sc.blit(img, img.get_rect(
                midleft=(int(x0 + dx), int(mezzo + dy))))
            soldi = f.render(B.dollari(paga), True, B.VERDE_SOLDI)
            self.sc.blit(soldi, soldi.get_rect(midright=(x0 + largo, mezzo)))
            # il nome e quanti rulli, fra l'icona e la cifra. Se il nome
            # e' lungo si accorcia, cosi' non va a finire sotto ai soldi
            x = x0 + lato + B.s(9)
            quanti = f.render(" x%d" % lung, True, tuple(colore_simbolo(nome)))
            sta = x0 + largo - soldi.get_width() - B.s(10) - quanti.get_width()
            testo = nome_simbolo(nome)
            q = f.render(testo, True, (206, 210, 220))
            while q.get_width() > sta - x and len(testo) > 3:
                testo = testo[:-1]
                q = f.render(testo + ".", True, (206, 210, 220))
            self.sc.blit(q, q.get_rect(midleft=(x, mezzo)))
            self.sc.blit(quanti, quanti.get_rect(
                midleft=(x + q.get_width(), mezzo)))
            y += lato + B.s(6)

    def disegna_scelte(self, voci, sel):
        """Le scelte nella fascia a destra, nello stesso stile dei menu."""
        self.rett = []
        x0, x1 = self.fascia + B.s(16), B.WIN_W - B.s(8)
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
        # il conto della sessione: giri, quanto hai puntato, quanto hai vinto
        conto = getattr(self, "conto", None)
        if conto:
            small = B.FONTS["small"]
            y += B.s(10)
            for et, val, col in conto:
                a = small.render(et, True, (150, 156, 168))
                b = small.render(val, True, col)
                self.sc.blit(a, a.get_rect(midleft=(x0 + B.s(14), y)))
                self.sc.blit(b, b.get_rect(midright=(x1 - B.s(14), y)))
                y += small.get_height() + B.s(6)

    def disegna_jackpot(self):
        """Il jackpot sopra la macchina, in una barra larga quanto lei,
        con la luce che gira e cambia colore."""
        sc = self.sc
        r = pygame.Rect(self.cassa.x, 0, self.cassa.w, B.s(44))
        r.bottom = self.cassa.top - B.s(12)
        pygame.draw.rect(sc, (13, 15, 21), r, border_radius=B.s(10))
        k = 0.5 + 0.5 * math.sin(self.t_vinta * 9.0)
        if self.lampo > 0:
            col = tuple(int(c * (0.45 + 0.55 * k)) for c in (255, 236, 150))
            pygame.draw.rect(sc, col, r, max(1, B.s(2)),
                             border_radius=B.s(10))
        else:
            cornice_neon(sc, r, self.t_neon + 0.5, B.s(10))
        if self.lampo > 0:
            col_t = tuple(int(c * (0.55 + 0.45 * k))
                          for c in (255, 236, 150))
        else:
            col_t = colore_neon(self.t_neon + 0.5)
        nome = B.FONTS["small"].render(T("jackpot").upper(), True, col_t)
        soldi = B.FONTS["font"].render(B.dollari(jackpot()), True, col_t)
        insieme = nome.get_width() + soldi.get_width() + B.s(16)
        x = r.centerx - insieme // 2
        sc.blit(nome, nome.get_rect(midleft=(x, r.centery)))
        sc.blit(soldi, soldi.get_rect(
            midleft=(x + nome.get_width() + B.s(16), r.centery)))

    def _giro_luci(self, r, passo, via=0):
        """I posti delle lampadine lungo la cornice, in fila. 'via'
        sposta tutta la fila, cosi' le piccole finiscono in mezzo alle
        grandi invece che sopra."""
        punti = []
        x = r.left + via
        while x < r.right:                      # sopra e sotto
            punti.append((x, r.top))
            punti.append((r.right - (x - r.left), r.bottom))
            x += passo
        y = r.top + passo + via
        while y < r.bottom - passo // 2:        # i due fianchi
            punti.append((r.right, y))
            punti.append((r.left, r.bottom - (y - r.top)))
            y += passo
        return punti

    def lampadine(self):
        """Le lucine intorno alla macchina, in mezzo alla fascia della
        cornice: una fila di LED piccoli e, fra uno e l'altro, uno ancora
        piu' piccolo. Il colore gira sulla ruota come il neon, ogni
        lucina un pezzetto piu' avanti della vicina, cosi' lungo il giro
        si vede passare tutto l'arcobaleno."""
        sc = self.sc
        dentro = B.s(11)                    # in mezzo alla fascia
        r = self.cassa.inflate(-dentro * 2, -dentro * 2)
        passo = B.s(34)
        for i, (px, py) in enumerate(self._giro_luci(r, passo)):
            f = 0.5 + 0.5 * math.sin(self.t_luci * 4.0 - i * 0.5)
            q = led(max(5, B.s(10)), (self.t_luci + i * 0.09) / 7.0,
                    0.4 + 0.6 * f)
            sc.blit(q, q.get_rect(center=(px, py)),
                    special_flags=pygame.BLEND_RGB_ADD)
        # quelle in mezzo: piu' piccole, piu' svelte, e mezzo giro di
        # colore indietro
        for i, (px, py) in enumerate(self._giro_luci(r, passo, passo // 2)):
            f = 0.5 + 0.5 * math.sin(self.t_luci * 5.5 + i * 0.6)
            q = led(max(3, B.s(6)), (self.t_luci + 3.5 + i * 0.09) / 7.0,
                    0.3 + 0.7 * f)
            sc.blit(q, q.get_rect(center=(px, py)),
                    special_flags=pygame.BLEND_RGB_ADD)

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
        x0, x1 = self.fascia + B.s(16), B.WIN_W - B.s(14)
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
        # da ferme le lampadine girano piano; quando i rulli si fermano
        # su una vincita partono, e col jackpot corrono
        if self.lampo > 0:
            corsa = 4.5
        elif not self.gira and any(v[3] for v in self.vinte):
            corsa = 2.5
        else:
            corsa = 0.45
        self.t_luci += self.dt * corsa
        self.polvere_passo()
        self.scia_passo()
        if self.lampo > 0:
            self.lampo = max(0.0, self.lampo - self.dt)


# le macchine: chiave, come si chiama, che tema usa. Il motore, i
# pagamenti e le regole sono gli stessi per tutte: cambiano solo i
# simboli (immagini/slot/<tema>/) e i suoni (audio/slot/<tema>/fx/).
# Quello che manca in un tema si prende da "classica", cosi' una
# macchina si puo' vestire un simbolo alla volta senza mai rompersi.
MACCHINE = (("prova", "m_prova", "classica"),
            ("nuova", "m_nuova", "nuova"))
TEMA_BASE = "classica"


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


def in_magazzino():
    """Le immagini che stanno nella cartella del tema ma che non sono
    (ancora) di nessun simbolo. Si fanno vedere in fondo alla pagina di
    prova, cosi' si guardano senza doverle mettere al posto di un altro."""
    usati = set(s[0] for s in SIMBOLI)
    d = os.path.join(GFX, tema())
    if not os.path.isdir(d):
        return []
    fuori = []
    for f in sorted(os.listdir(d)):
        n, e = os.path.splitext(f)
        if e.lower() == ".png" and n not in usati:
            fuori.append(n)
    return fuori


def pagina_prova(sc, clock, m):
    """La pagina di prova: tutti i simboli della macchina, ognuno con la
    sua animazione, tutti insieme. Serve a guardare le animazioni senza
    dover aspettare di vincere con quel simbolo."""
    elenco = [s[0] for s in SIMBOLI] + in_magazzino()
    while True:
        m.dt = min(0.05, clock.tick(60) / 1000.0)
        m.t_neon += m.dt
        for ev in B.eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return "su"
        sc.blit(fondo_slot(), (0, 0))
        m.scia_passo()
        m.disegna_scia()
        mini = B.FONTS.get("mini", B.FONTS["small"])
        t = B.FONTS["font"].render(T("pr_titolo"), True, B.ORO_SCELTA)
        sc.blit(t, t.get_rect(center=(B.WIN_W // 2, B.ALTO + B.s(18))))
        # quanti ce ne stanno: le righe si contano e i simboli si
        # stringono quanto serve, se no gli ultimi finiscono sotto il
        # bordo dello schermo e non si vedono
        per_riga = 7
        righe = (len(elenco) + per_riga - 1) // per_riga
        y0 = B.ALTO + B.s(52)
        spazio = B.WIN_H - B.s(52) - y0
        passo_y = min(B.s(108), spazio // max(1, righe))
        lato = max(B.s(28), passo_y - B.s(36))
        passo_x = (B.WIN_W - B.s(60)) // per_riga
        for i, nome in enumerate(elenco):
            cx = B.s(30) + passo_x * (i % per_riga) + passo_x // 2
            cy = y0 + passo_y * (i // per_riga) + lato // 2
            img, (dx, dy) = m.icona_viva(nome, (lato, lato), i * 0.7)
            m.semina(nome, (cx + dx, cy + dy), (lato, lato))
            sc.blit(img, img.get_rect(center=(int(cx + dx), int(cy + dy))))
            an = animazione(nome)
            q = mini.render(nome_simbolo(nome), True,
                            (150, 212, 255) if an else (138, 144, 156))
            sc.blit(q, q.get_rect(center=(cx, cy + lato // 2 + B.s(14))))
        r = mini.render(T("pr_aiuto"), True, (150, 156, 168))
        sc.blit(r, r.get_rect(center=(B.WIN_W // 2, B.WIN_H - B.s(24))))
        B.presenta()


def pagina_pagamenti(sc, clock):
    """Il tabellone: i simboli in due colonne, con quanto pagano da tre a
    sei rulli in soldi veri, alla puntata scelta."""
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
                p3, p4, p5, p6 = PAGA[nome][1:]
                # "3 = $18   4 = $38   5 = $95   6 = $209"
                x_val = x + largo
                cella = (largo - B.s(170)) // 4
                for k, v in enumerate((p3, p4, p5, p6)):
                    if not v:
                        continue
                    # "x2" in oro, il premio nel verde del portafoglio
                    per = small.render("x%d" % (k + 3), True, B.ORO_SCELTA)
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
    giri = [0]              # quanti tiri in questa sessione
    puntato = [0]           # quanto hai puntato in tutto
    vinto = [0]             # quanto hai vinto in tutto

    def voci():
        return [T("spin"), "%s  %s" % (T("bet"), B.dollari(punta)),
                T("pays"), T("test"), T("back")]

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
            puntato[0] += punta
            jackpot(max(1, int(punta * JACKPOT_FETTA)))
            B.salva_config()
        giri[0] += 1
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
                    sel = (sel + 1) % len(voci())
                    B.suona_fx("menu_tic", 0.6)
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % len(voci())
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
                    elif sel == 3:
                        if pagina_prova(sc, clock, m) == "quit":
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
                            elif i == 3:
                                if pagina_prova(sc, clock, m) == "quit":
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
            premio_jack = 0
            if jack:
                premio_jack = jackpot()
                azzera_jackpot()
                tot += premio_jack
                m.lampo = 8.0
            m.vinte, m.vinto = vinte, tot
            vinto[0] += tot
            if tot:
                B.soldi(tot)
            B.salva_config()
            m.totale = tot
            # le ultime vincite nella colonna di sinistra
            if premio_jack:
                m.storico.insert(0, (SIMBOLO_JACKPOT, COLONNE, premio_jack))
            for v in sorted((x for x in vinte if x[3]), key=lambda x: x[3]):
                m.storico.insert(0, (v[0], v[1], v[3]))
            del m.storico[10:]
            # il log del giro: puntata, cosa e' uscito, cosa ha pagato
            griglia_log = " | ".join(
                ",".join(m.griglia[c][r] for r in range(RIGHE))
                for c in range(COLONNE))
            dettaglio = "; ".join(
                "%s x%d su %d modi = %s" % (v[0], v[1], v[2], B.dollari(v[3]))
                for v in vinte) or "niente"
            log("punta %-6s  %s  ->  %-8s  [%s]  cassa %-8s  jackpot %s"
                % (B.dollari(punta), griglia_log, B.dollari(tot),
                   dettaglio, B.dollari(B.soldi()),
                   ("VINTO " + B.dollari(premio_jack)) if premio_jack
                   else B.dollari(jackpot())))
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
        m.conto = [(T("st_spins"), str(giri[0]), (230, 232, 238)),
                   (T("st_bet"), B.dollari(puntato[0]), (230, 232, 238)),
                   (T("st_won"), B.dollari(vinto[0]), B.VERDE_SOLDI)]
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
